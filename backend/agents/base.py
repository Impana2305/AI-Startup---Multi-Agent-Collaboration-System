"""Executive agent base class and factory.

All executive agents share the same interface: they can analyze a proposal,
participate in debate, cast a vote, and revise their position.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from google import genai

from config import settings

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    """Return a Gemini client configured with the API key."""
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


async def call_gemini(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_retries: int = 5,
) -> dict[str, Any]:
    """Call Gemini and parse the JSON response.

    Includes automatic retry with exponential backoff for rate-limit
    errors (RESOURCE_EXHAUSTED).  Falls back to extracting JSON from
    markdown code fences if the model wraps its output that way.
    """
    client = _get_client()
    model = model or settings.executive_model

    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first and last lines (```json and ```)
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Gemini response: %s", e)
            logger.error("Raw response: %s", response.text[:500])
            # Return a minimal fallback — no point retrying a parse error
            return {
                "summary": "Analysis could not be parsed. Raw response available.",
                "raw_response": response.text[:2000],
                "score": 5.0,
                "pros": [],
                "cons": [],
                "risks": ["Response parsing failed"],
                "recommendation": "Manual review required",
                "details": {},
            }
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()

            # Check if this is a rate-limit / quota error worth retrying
            is_retryable = any(
                keyword in error_str
                for keyword in ("resource_exhausted", "429", "rate", "quota", "too many")
            )

            if is_retryable and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32 seconds
                logger.warning(
                    "Gemini rate-limited (attempt %d/%d). Retrying in %ds: %s",
                    attempt + 1, max_retries, wait_time, e,
                )
                await asyncio.sleep(wait_time)
                continue

            # Non-retryable error or out of retries
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

    # Should not reach here, but just in case
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
