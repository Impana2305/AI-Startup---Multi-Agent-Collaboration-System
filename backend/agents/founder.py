"""Founder / CEO Agent — orchestrates the board meeting."""

from __future__ import annotations

from typing import Any

from agents.base import call_gemini
from agents.prompts import (
    FOUNDER_SYSTEM_PROMPT,
    FOUNDER_SUMMARIZE_PROMPT,
    FOUNDER_CONFLICT_RESOLUTION_PROMPT,
    FOUNDER_FINAL_DECISION_PROMPT,
)
from config import settings


class FounderAgent:
    """The CEO who orchestrates the entire board meeting."""

    NAME = "Founder"
    ROLE = "CEO"

    async def summarize_proposal(self, proposal: dict) -> dict[str, Any]:
        """Step 2: Create an executive summary of the startup proposal."""
        import json
        prompt = FOUNDER_SUMMARIZE_PROMPT.format(proposal=json.dumps(proposal, indent=2))
        return await call_gemini(
            prompt=prompt,
            system_prompt=FOUNDER_SYSTEM_PROMPT,
            model=settings.founder_model,
        )

    async def resolve_conflicts(
        self,
        debate_transcript: str,
        analyses: str,
    ) -> dict[str, Any]:
        """Step 7: Identify and resolve conflicts from the debate."""
        prompt = FOUNDER_CONFLICT_RESOLUTION_PROMPT.format(
            debate_transcript=debate_transcript,
            analyses=analyses,
        )
        return await call_gemini(
            prompt=prompt,
            system_prompt=FOUNDER_SYSTEM_PROMPT,
            model=settings.founder_model,
        )

    async def make_final_decision(
        self,
        summary: str,
        analyses: str,
        debate: str,
        conflicts: str,
        votes: str,
    ) -> dict[str, Any]:
        """Step 9: Generate the final board decision and report."""
        prompt = FOUNDER_FINAL_DECISION_PROMPT.format(
            summary=summary,
            analyses=analyses,
            debate=debate,
            conflicts=conflicts,
            votes=votes,
        )
        return await call_gemini(
            prompt=prompt,
            system_prompt=FOUNDER_SYSTEM_PROMPT,
            model=settings.founder_model,
            temperature=0.5,  # More deterministic for final decision
        )
