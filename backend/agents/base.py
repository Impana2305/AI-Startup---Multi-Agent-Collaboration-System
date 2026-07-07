"""Executive agent base class and factory.

All executive agents share the same interface: they can analyze a proposal,
participate in debate, cast a vote, and revise their position.
"""

from __future__ import annotations

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
) -> dict[str, Any]:
    """Call Gemini and parse the JSON response.

    Falls back to extracting JSON from markdown code fences if the model
    wraps its output that way.
    """
    client = _get_client()
    model = model or settings.executive_model

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
        # Return a minimal fallback
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
        logger.error("Gemini API call failed: %s", e)
        return {
            "summary": f"Agent encountered an error: {str(e)}",
            "score": 5.0,
            "pros": [],
            "cons": [],
            "risks": [str(e)],
            "recommendation": "Retry required",
            "details": {},
        }
