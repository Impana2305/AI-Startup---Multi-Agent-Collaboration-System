"""Executive agent base class and factory.

All executive agents share the same interface: they can analyze a proposal,
participate in debate, cast a vote, and revise their position.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
import httpx
from google import genai

from config import settings

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    """Return a Gemini client configured with the API key."""
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


def _build_model_candidates(model: str | None) -> list[str]:
    """Build a preferred model list with safe fallbacks for unavailable models."""
    configured_model = (model or settings.executive_model or "gemini-3.5-flash").strip()
    candidates = [configured_model]

    for fallback_model in (
        "gemini-3.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ):
        if fallback_model not in candidates:
            candidates.append(fallback_model)

    return candidates


def _is_retryable_error(error: Exception) -> bool:
    """Identify transient server-side or quota issues that should be retried."""
    error_str = str(error).lower()
    return any(
        keyword in error_str
        for keyword in (
            "resource_exhausted",
            "429",
            "rate",
            "quota",
            "too many",
            "temporarily unavailable",
            "service unavailable",
            "503",
            "timeout",
        )
    )


def _is_model_unavailable_error(error: Exception) -> bool:
    """Detect a model selection problem that should trigger a fallback model."""
    error_str = str(error).lower()
    return any(
        keyword in error_str
        for keyword in (
            "404",
            "not_found",
            "not found",
            "unsupported",
            "unsupported model",
            "invalid model",
            "does not support",
        )
    )


async def _call_groq_endpoint(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    max_retries: int = 4,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return json.loads(data["choices"][0]["message"]["content"])
        except Exception as exc:
            last_error = exc
            if _is_retryable_error(exc) and attempt < max_retries - 1:
                wait_time = 2 ** attempt + 1
                logger.warning(
                    "Groq request failed (attempt %d/%d). Retrying in %ds: %s",
                    attempt + 1,
                    max_retries,
                    wait_time,
                    exc,
                )
                await asyncio.sleep(wait_time)
                continue
            raise

    raise last_error or RuntimeError("Groq request failed")


async def call_gemini(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_retries: int = 5,
) -> dict[str, Any]:
    """Call the configured LLM (Groq or Gemini) and parse the JSON response.

    If LLM_PROVIDER is 'auto', Groq is used when GROQ_API_KEY is set,
    otherwise Gemini. If provider is explicitly 'groq', Groq is used.
    On Groq failure, a structured error fallback is returned.
    For Gemini, automatic retries with exponential backoff are applied.
    """
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    if provider == "auto":
        provider = "groq" if settings.GROQ_API_KEY else "gemini"

    if provider == "groq":
        try:
            return await _call_groq_endpoint(
                prompt,
                system_prompt,
                model or settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                temperature,
                max_retries=max_retries,
            )
        except Exception as exc:
            logger.warning("Groq failed, falling back safely: %s", exc)
            return {
                "summary": f"Agent encountered an error: {exc}",
                "score": 5.0,
                "pros": [],
                "cons": [],
                "risks": [str(exc)],
                "recommendation": "Retry required",
                "details": {},
                "vote": "CONDITIONAL YES",
                "confidence": 0.5,
                "reasoning": f"Fallback due to API error: {exc}",
                "conditions": ["Resolve API error"],
                "overall_recommendation": "Retry required",
                "final_confidence_score": 0.0,
                "executive_summary": "The board meeting could not be completed successfully due to an API provider error.",
            }

    # --- Existing Gemini code below ---
    client = _get_client()
    model_candidates = _build_model_candidates(model)

    last_exception: Exception | None = None
    response_text = ""

    for attempt in range(max_retries):
        for candidate_model in model_candidates:
            try:
                response = await client.aio.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        response_mime_type="application/json",
                    ),
                )

                response_text = getattr(response, "text", "") or ""
                text = response_text.strip()

                # Strip markdown code fences if present
                if text.startswith("```"):
                    lines = text.split("\n")
                    # Remove first and last lines (```json and ```)
                    lines = [line for line in lines if not line.strip().startswith("```")]
                    text = "\n".join(lines)

                return json.loads(text)

            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON from Gemini response: %s", e)
                logger.error("Raw response: %s", response_text[:500])
                # Return a minimal fallback — no point retrying a parse error
                return {
                    "summary": "Analysis could not be parsed. Raw response available.",
                    "raw_response": response_text[:2000],
                    "score": 5.0,
                    "pros": [],
                    "cons": [],
                    "risks": ["Response parsing failed"],
                    "recommendation": "Manual review required",
                    "details": {},
                }
            except Exception as e:
                last_exception = e
                if _is_model_unavailable_error(e):
                    logger.warning(
                        "Gemini model %s is unavailable, trying the next fallback: %s",
                        candidate_model,
                        e,
                    )
                    continue

                if _is_retryable_error(e) and attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32 seconds
                    logger.warning(
                        "Gemini request failed for %s (attempt %d/%d). Retrying in %ds: %s",
                        candidate_model,
                        attempt + 1,
                        max_retries,
                        wait_time,
                        e,
                    )
                    await asyncio.sleep(wait_time)
                    break

                return {
                    "summary": f"Agent encountered an error: {str(e)}",
                    "score": 5.0,
                    "pros": [],
                    "cons": [],
                    "risks": [str(e)],
                    "recommendation": "Retry required",
                    "details": {},
                    "vote": "CONDITIONAL YES",
                    "confidence": 0.5,
                    "reasoning": f"Fallback due to API error: {str(e)}",
                    "conditions": ["Resolve API error"],
                    "overall_recommendation": "Retry required",
                    "final_confidence_score": 0.0,
                    "executive_summary": "The board meeting could not be completed successfully due to an API quota or rate limit error.",
                }

        if last_exception and _is_retryable_error(last_exception) and attempt < max_retries - 1:
            continue

        break

    logger.error("All retries exhausted for Gemini API call: %s", last_exception)
    return {
        "summary": f"Agent encountered an error after {max_retries} retries: {last_exception}",
        "score": 5.0,
        "pros": [],
        "cons": [],
        "risks": [str(last_exception)],
        "recommendation": "Retry required",
        "details": {},
        "vote": "CONDITIONAL YES",
        "confidence": 0.5,
        "reasoning": f"Fallback due to API error: {str(last_exception)}",
        "conditions": ["Resolve API error"],
        "overall_recommendation": "Retry required",
        "final_confidence_score": 0.0,
        "executive_summary": "The board meeting could not be completed successfully due to an API quota or rate limit error.",
    }