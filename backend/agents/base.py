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


from utils.key_manager import KeyManager

_GROQ_KEY_MANAGER: KeyManager | None = None
_GOOGLE_KEY_MANAGER: KeyManager | None = None
_OPENROUTER_KEY_MANAGER: KeyManager | None = None
_SAMBANOVA_KEY_MANAGER: KeyManager | None = None
_TOGETHER_KEY_MANAGER: KeyManager | None = None


def _get_groq_key_manager() -> KeyManager:
    global _GROQ_KEY_MANAGER
    keys = getattr(settings, "groq_api_keys", [])
    if not keys:
        single_key = getattr(settings, "GROQ_API_KEY", "")
        keys = [single_key] if single_key else ["dummy-groq-key"]

    if _GROQ_KEY_MANAGER is None:
        _GROQ_KEY_MANAGER = KeyManager("groq", keys)
    else:
        # Sync keys in case settings changed dynamically (e.g. mock settings in tests)
        if set(_GROQ_KEY_MANAGER.keys) != set(keys):
            _GROQ_KEY_MANAGER.update_keys(keys)
    return _GROQ_KEY_MANAGER


def _get_google_key_manager() -> KeyManager:
    global _GOOGLE_KEY_MANAGER
    keys = getattr(settings, "google_api_keys", [])
    if not keys:
        single_key = getattr(settings, "GOOGLE_API_KEY", "")
        keys = [single_key] if single_key else ["dummy-google-key"]

    if _GOOGLE_KEY_MANAGER is None:
        _GOOGLE_KEY_MANAGER = KeyManager("google", keys)
    else:
        # Sync keys in case settings changed dynamically
        if set(_GOOGLE_KEY_MANAGER.keys) != set(keys):
            _GOOGLE_KEY_MANAGER.update_keys(keys)
    return _GOOGLE_KEY_MANAGER


def _get_openrouter_key_manager() -> KeyManager:
    global _OPENROUTER_KEY_MANAGER
    keys = getattr(settings, "openrouter_api_keys", [])
    if not keys:
        single_key = getattr(settings, "OPENROUTER_API_KEY", "")
        keys = [single_key] if single_key else ["dummy-openrouter-key"]

    if _OPENROUTER_KEY_MANAGER is None:
        _OPENROUTER_KEY_MANAGER = KeyManager("openrouter", keys)
    else:
        if set(_OPENROUTER_KEY_MANAGER.keys) != set(keys):
            _OPENROUTER_KEY_MANAGER.update_keys(keys)
    return _OPENROUTER_KEY_MANAGER


def _get_sambanova_key_manager() -> KeyManager:
    global _SAMBANOVA_KEY_MANAGER
    keys = getattr(settings, "sambanova_api_keys", [])
    if not keys:
        single_key = getattr(settings, "SAMBANOVA_API_KEY", "")
        keys = [single_key] if single_key else ["dummy-sambanova-key"]

    if _SAMBANOVA_KEY_MANAGER is None:
        _SAMBANOVA_KEY_MANAGER = KeyManager("sambanova", keys)
    else:
        if set(_SAMBANOVA_KEY_MANAGER.keys) != set(keys):
            _SAMBANOVA_KEY_MANAGER.update_keys(keys)
    return _SAMBANOVA_KEY_MANAGER


def _get_together_key_manager() -> KeyManager:
    global _TOGETHER_KEY_MANAGER
    keys = getattr(settings, "together_api_keys", [])
    if not keys:
        single_key = getattr(settings, "TOGETHER_API_KEY", "")
        keys = [single_key] if single_key else ["dummy-together-key"]

    if _TOGETHER_KEY_MANAGER is None:
        _TOGETHER_KEY_MANAGER = KeyManager("together", keys)
    else:
        if set(_TOGETHER_KEY_MANAGER.keys) != set(keys):
            _TOGETHER_KEY_MANAGER.update_keys(keys)
    return _TOGETHER_KEY_MANAGER


def _get_client(api_key: str) -> genai.Client:
    """Return a Gemini client configured with the given API key."""
    return genai.Client(api_key=api_key)


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


def _build_groq_model_candidates(model: str | None) -> list[str]:
    """Build a preferred model list for Groq with free-tier fallbacks."""
    configured_model = (model or settings.GROQ_MODEL or "llama-3.3-70b-versatile").strip()
    candidates = [configured_model]

    for fallback_model in (
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ):
        if fallback_model not in candidates:
            candidates.append(fallback_model)

    return candidates


def _build_openrouter_model_candidates(model: str | None) -> list[str]:
    """Build a preferred model list for OpenRouter with free-tier fallbacks."""
    configured_model = (model or settings.OPENROUTER_MODEL or "meta-llama/llama-3.3-70b-instruct:free").strip()
    candidates = [configured_model]

    for fallback_model in (
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
    ):
        if fallback_model not in candidates:
            candidates.append(fallback_model)

    return candidates


def _build_sambanova_model_candidates(model: str | None) -> list[str]:
    """Build a preferred model list for SambaNova with free-tier fallbacks."""
    configured_model = (model or settings.SAMBANOVA_MODEL or "Meta-Llama-3.3-70B-Instruct").strip()
    candidates = [configured_model]

    for fallback_model in (
        "Meta-Llama-3.3-70B-Instruct",
        "Meta-Llama-3.1-8B-Instruct",
    ):
        if fallback_model not in candidates:
            candidates.append(fallback_model)

    return candidates


def _build_together_model_candidates(model: str | None) -> list[str]:
    """Build a preferred model list for Together AI with free-tier fallbacks."""
    configured_model = (model or settings.TOGETHER_MODEL or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo").strip()
    candidates = [configured_model]

    for fallback_model in (
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
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
            "410",
            "gone",
        )
    )


def _make_fallback_response(exc: Exception) -> dict[str, Any]:
    """Generate a consistent fallback JSON response on critical API failures."""
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


async def _call_openai_compatible_endpoint(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    base_url: str,
    key_manager: KeyManager,
    max_retries: int = 8,
) -> dict[str, Any]:
    """Call an OpenAI-compatible endpoint with key rotation, cooldowns, and retries."""
    last_error = None

    for attempt in range(max_retries):
        key = key_manager.get_key()
        if not key:
            raise RuntimeError(f"No API keys available for {key_manager.provider}")

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if "openrouter" in base_url.lower():
            headers["HTTP-Referer"] = "https://localhost:8000"
            headers["X-Title"] = "AI Boardroom"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if "openrouter" not in base_url.lower():
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    base_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Cleanup potential markdown json codeblocks from LLM responses
                content_clean = content.strip()
                if content_clean.startswith("```json"):
                    content_clean = content_clean[7:]
                    if content_clean.endswith("```"):
                        content_clean = content_clean[:-3]
                elif content_clean.startswith("```"):
                    content_clean = content_clean[3:]
                    if content_clean.endswith("```"):
                        content_clean = content_clean[:-3]
                        
                return json.loads(content_clean.strip())
        except Exception as exc:
            last_error = exc
            if _is_retryable_error(exc):
                key_manager.report_rate_limit(key)
                if attempt < max_retries - 1:
                    import time
                    now = time.time()
                    available_keys = [k for k in key_manager.keys if key_manager.cooldowns[k] <= now]
                    if available_keys:
                        wait_time = 0.5
                        logger.info("%s rate limit hit. Retrying immediately using another available key.", key_manager.provider.capitalize())
                    else:
                        retry_after = None
                        if isinstance(exc, httpx.HTTPStatusError):
                            retry_after_val = exc.response.headers.get("retry-after") or exc.response.headers.get("x-ratelimit-reset")
                            if retry_after_val:
                                try:
                                    retry_after = float(retry_after_val)
                                except ValueError:
                                    import re
                                    m = re.match(r'^([\d.]+)\s*s$', retry_after_val.strip().lower())
                                    if m:
                                        retry_after = float(m.group(1))

                        if retry_after is not None:
                            if retry_after > 100.0:
                                retry_after = retry_after / 1000.0
                            wait_time = min(max(retry_after, 0.5), 60.0)
                            logger.info("%s rate limit header detected. Sleeping for %.2f seconds.", key_manager.provider.capitalize(), wait_time)
                        else:
                            earliest_expiry = min(key_manager.cooldowns.values())
                            sleep_needed = earliest_expiry - now
                            if sleep_needed > 0:
                                wait_time = min(sleep_needed + 0.5, 60.0)
                                logger.info("All %s keys on cooldown. Sleeping for %.2f seconds to let the earliest key clear.", key_manager.provider.capitalize(), wait_time)
                            else:
                                wait_time = 2 ** attempt + 3
                                logger.warning(
                                    "%s request failed (attempt %d/%d). All keys on cooldown. Retrying in %ds: %s",
                                    key_manager.provider.capitalize(),
                                    attempt + 1,
                                    max_retries,
                                    wait_time,
                                    exc,
                                )
                    await asyncio.sleep(wait_time)
                    continue
            raise

    raise last_error or RuntimeError(f"{key_manager.provider.capitalize()} request failed")


async def _call_groq_endpoint(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    max_retries: int = 8,
) -> dict[str, Any]:
    last_error: Exception | None = None
    key_manager = _get_groq_key_manager()

    for attempt in range(max_retries):
        key = key_manager.get_key()
        if not key:
            raise RuntimeError("No Groq API keys available")

        headers = {
            "Authorization": f"Bearer {key}",
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
            if _is_retryable_error(exc):
                key_manager.report_rate_limit(key)
                if attempt < max_retries - 1:
                    import time
                    now = time.time()
                    available_keys = [k for k in key_manager.keys if key_manager.cooldowns[k] <= now]
                    if available_keys:
                        wait_time = 0.5
                        logger.info("Groq API rate limit hit. Retrying immediately using another available key.")
                    else:
                        retry_after = None
                        if isinstance(exc, httpx.HTTPStatusError):
                            retry_after_val = exc.response.headers.get("retry-after") or exc.response.headers.get("x-ratelimit-reset")
                            if retry_after_val:
                                try:
                                    retry_after = float(retry_after_val)
                                except ValueError:
                                    import re
                                    m = re.match(r'^([\d.]+)\s*s$', retry_after_val.strip().lower())
                                    if m:
                                        retry_after = float(m.group(1))
                                    else:
                                        m = re.match(r'^(?:(\d+)m)?\s*([\d.]+)s$', retry_after_val.strip().lower())
                                        if m:
                                            minutes = int(m.group(1)) if m.group(1) else 0
                                            seconds = float(m.group(2))
                                            retry_after = minutes * 60 + seconds

                        if retry_after is not None:
                            # If it's very large, it's probably in milliseconds (e.g. 2428 ms = 2.428s)
                            if retry_after > 100.0:
                                retry_after = retry_after / 1000.0
                            # Cap the sleep to 60 seconds maximum (since TPM resets every minute)
                            wait_time = min(max(retry_after, 0.5), 60.0)
                            logger.info("Groq rate limit header detected. Sleeping for %.2f seconds.", wait_time)
                        else:
                            earliest_expiry = min(key_manager.cooldowns.values())
                            sleep_needed = earliest_expiry - now
                            if sleep_needed > 0:
                                wait_time = min(sleep_needed + 0.5, 60.0)
                                logger.info("All Groq keys on cooldown. Sleeping for %.2f seconds to let the earliest key clear.", wait_time)
                            else:
                                wait_time = 2 ** attempt + 3
                                logger.warning(
                                    "Groq request failed (attempt %d/%d). All keys on cooldown. Retrying in %ds: %s",
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
    max_retries: int = 8,
) -> dict[str, Any]:
    """Call the configured LLM (Groq or Gemini) and parse the JSON response.

    If LLM_PROVIDER is 'auto', Groq is used when GROQ_API_KEY is set,
    otherwise Gemini. If provider is explicitly 'groq', Groq is used.
    On Groq failure, a structured error fallback is returned.
    For Gemini, automatic retries with exponential backoff are applied.
    """
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    if provider == "auto":
        if getattr(settings, "groq_api_keys", []):
            provider = "groq"
        elif getattr(settings, "openrouter_api_keys", []):
            provider = "openrouter"
        elif getattr(settings, "sambanova_api_keys", []):
            provider = "sambanova"
        elif getattr(settings, "together_api_keys", []):
            provider = "together"
        else:
            provider = "gemini"

    # Cross-provider model override logic
    target_model = model
    if provider == "groq":
        groq_model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        if target_model and "gemini" in target_model.lower():
            target_model = groq_model
        if not target_model:
            target_model = groq_model
    elif provider == "openrouter":
        openrouter_model = settings.OPENROUTER_MODEL or "meta-llama/llama-3.1-8b-instruct:free"
        if target_model and any(kw in target_model.lower() for kw in ("gemini", "llama-3.3-70b-versatile")):
            target_model = openrouter_model
        if not target_model:
            target_model = openrouter_model
    elif provider == "sambanova":
        sambanova_model = settings.SAMBANOVA_MODEL or "Meta-Llama-3.1-70B-Instruct"
        if target_model and any(kw in target_model.lower() for kw in ("gemini", "llama-3.3-70b-versatile")):
            target_model = sambanova_model
        if not target_model:
            target_model = sambanova_model
    elif provider == "together":
        together_model = settings.TOGETHER_MODEL or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        if target_model and any(kw in target_model.lower() for kw in ("gemini", "llama-3.3-70b-versatile")):
            target_model = together_model
        if not target_model:
            target_model = together_model
    else:
        if target_model and any(kw in target_model.lower() for kw in ("llama", "mixtral", "gemma", "deepseek")):
            target_model = None

    if provider == "groq":
        model_candidates = _build_groq_model_candidates(target_model)
        last_error = None
        for candidate_model in model_candidates:
            try:
                return await _call_groq_endpoint(
                    prompt,
                    system_prompt,
                    candidate_model,
                    temperature,
                    max_retries=max_retries,
                )
            except Exception as exc:
                last_error = exc
                if _is_model_unavailable_error(exc) or _is_retryable_error(exc):
                    logger.warning(
                        "Groq model %s failed, trying the next fallback: %s",
                        candidate_model,
                        exc,
                    )
                    continue
                raise

        logger.error("All Groq model candidates failed: %s", last_error)
        return _make_fallback_response(last_error)

    elif provider == "openrouter":
        key_manager = _get_openrouter_key_manager()
        model_candidates = _build_openrouter_model_candidates(target_model)
        last_error = None
        for candidate_model in model_candidates:
            try:
                return await _call_openai_compatible_endpoint(
                    prompt,
                    system_prompt,
                    candidate_model,
                    temperature,
                    "https://openrouter.ai/api/v1/chat/completions",
                    key_manager,
                    max_retries=max_retries,
                )
            except Exception as exc:
                last_error = exc
                if _is_model_unavailable_error(exc) or _is_retryable_error(exc):
                    logger.warning(
                        "OpenRouter model %s failed, trying the next fallback: %s",
                        candidate_model,
                        exc,
                    )
                    continue
                raise
        logger.error("All OpenRouter model candidates failed: %s", last_error)
        return _make_fallback_response(last_error)

    elif provider == "sambanova":
        key_manager = _get_sambanova_key_manager()
        model_candidates = _build_sambanova_model_candidates(target_model)
        last_error = None
        for candidate_model in model_candidates:
            try:
                return await _call_openai_compatible_endpoint(
                    prompt,
                    system_prompt,
                    candidate_model,
                    temperature,
                    "https://api.sambanova.ai/v1/chat/completions",
                    key_manager,
                    max_retries=max_retries,
                )
            except Exception as exc:
                last_error = exc
                if _is_model_unavailable_error(exc) or _is_retryable_error(exc):
                    logger.warning(
                        "SambaNova model %s failed, trying the next fallback: %s",
                        candidate_model,
                        exc,
                    )
                    continue
                raise
        logger.error("All SambaNova model candidates failed: %s", last_error)
        return _make_fallback_response(last_error)

    elif provider == "together":
        key_manager = _get_together_key_manager()
        model_candidates = _build_together_model_candidates(target_model)
        last_error = None
        for candidate_model in model_candidates:
            try:
                return await _call_openai_compatible_endpoint(
                    prompt,
                    system_prompt,
                    candidate_model,
                    temperature,
                    "https://api.together.xyz/v1/chat/completions",
                    key_manager,
                    max_retries=max_retries,
                )
            except Exception as exc:
                last_error = exc
                if _is_model_unavailable_error(exc) or _is_retryable_error(exc):
                    logger.warning(
                        "Together model %s failed, trying the next fallback: %s",
                        candidate_model,
                        exc,
                    )
                    continue
                raise
        logger.error("All Together model candidates failed: %s", last_error)
        return _make_fallback_response(last_error)

    # --- Existing Gemini code below ---
    key_manager = _get_google_key_manager()
    model_candidates = _build_model_candidates(target_model)

    last_exception: Exception | None = None
    response_text = ""

    for attempt in range(max_retries):
        for candidate_model in model_candidates:
            key = key_manager.get_key()
            if not key:
                raise RuntimeError("No Google API keys available")

            client = _get_client(key)
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

                if _is_retryable_error(e):
                    key_manager.report_rate_limit(key)
                    if attempt < max_retries - 1:
                        import time
                        now = time.time()
                        available_keys = [k for k in key_manager.keys if key_manager.cooldowns[k] <= now]
                        if available_keys:
                            wait_time = 0.5
                            logger.info("Gemini API rate limit hit. Retrying immediately using another available key.")
                        else:
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