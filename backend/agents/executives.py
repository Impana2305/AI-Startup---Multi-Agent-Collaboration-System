"""Executive agent implementations — CTO, CFO, COO, CMO, CHRO, Legal, PM, Investor.

All executives share the same interface: analyze, debate, vote, revise.
They differ only in their system prompts and analysis prompts.
"""

from __future__ import annotations

import json
from typing import Any

from agents.base import call_gemini
from agents.prompts import (
    # System prompts
    CTO_SYSTEM_PROMPT,
    CFO_SYSTEM_PROMPT,
    COO_SYSTEM_PROMPT,
    CMO_SYSTEM_PROMPT,
    CHRO_SYSTEM_PROMPT,
    LEGAL_SYSTEM_PROMPT,
    PM_SYSTEM_PROMPT,
    INVESTOR_SYSTEM_PROMPT,
    # Analysis prompts
    CTO_ANALYSIS_PROMPT,
    CFO_ANALYSIS_PROMPT,
    COO_ANALYSIS_PROMPT,
    CMO_ANALYSIS_PROMPT,
    CHRO_ANALYSIS_PROMPT,
    LEGAL_ANALYSIS_PROMPT,
    PM_ANALYSIS_PROMPT,
    INVESTOR_ANALYSIS_PROMPT,
    # Shared prompts
    DEBATE_PROMPT,
    VOTING_PROMPT,
    REVISION_PROMPT,
)


class ExecutiveAgent:
    """Generic executive agent that can be specialized via prompts."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        analysis_prompt: str,
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.analysis_prompt = analysis_prompt

    async def analyze(self, summary: str, proposal: str) -> dict[str, Any]:
        """Step 4: Perform independent analysis of the startup proposal."""
        prompt = self.analysis_prompt.format(summary=summary, proposal=proposal)
        result = await call_gemini(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )
        result["agent_name"] = self.name
        result["agent_role"] = self.role
        return result

    async def debate(
        self,
        own_analysis: str,
        other_analyses: str,
        previous_messages: str,
        round_number: int,
    ) -> dict[str, Any]:
        """Step 6: Participate in debate round."""
        prompt = DEBATE_PROMPT.format(
            agent_name=self.name,
            agent_role=self.role,
            own_analysis=own_analysis,
            other_analyses=other_analyses,
            previous_messages=previous_messages or "No previous messages yet.",
            round_number=round_number,
        )
        return await call_gemini(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

    async def vote(
        self,
        own_analysis: str,
        debate_summary: str,
        conflicts: str,
    ) -> dict[str, Any]:
        """Step 8: Cast a vote on the startup proposal."""
        prompt = VOTING_PROMPT.format(
            agent_name=self.name,
            agent_role=self.role,
            own_analysis=own_analysis,
            debate_summary=debate_summary,
            conflicts=conflicts,
        )
        result = await call_gemini(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )
        result["agent_name"] = self.name
        result["agent_role"] = self.role
        return result

    async def revise(
        self,
        revision_request: str,
        original_position: str,
        debate_context: str,
    ) -> dict[str, Any]:
        """Step 7: Revise position based on CEO's conflict resolution."""
        prompt = REVISION_PROMPT.format(
            agent_name=self.name,
            agent_role=self.role,
            revision_request=revision_request,
            original_position=original_position,
            debate_context=debate_context,
        )
        return await call_gemini(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )


# ---------------------------------------------------------------------------
# Agent Factory — create all 8 executive agents
# ---------------------------------------------------------------------------

def create_cto() -> ExecutiveAgent:
    return ExecutiveAgent("CTO", "Chief Technology Officer", CTO_SYSTEM_PROMPT, CTO_ANALYSIS_PROMPT)

def create_cfo() -> ExecutiveAgent:
    return ExecutiveAgent("CFO", "Chief Financial Officer", CFO_SYSTEM_PROMPT, CFO_ANALYSIS_PROMPT)

def create_coo() -> ExecutiveAgent:
    return ExecutiveAgent("COO", "Chief Operating Officer", COO_SYSTEM_PROMPT, COO_ANALYSIS_PROMPT)

def create_cmo() -> ExecutiveAgent:
    return ExecutiveAgent("CMO", "Chief Marketing Officer", CMO_SYSTEM_PROMPT, CMO_ANALYSIS_PROMPT)

def create_chro() -> ExecutiveAgent:
    return ExecutiveAgent("CHRO", "Chief Human Resources Officer", CHRO_SYSTEM_PROMPT, CHRO_ANALYSIS_PROMPT)

def create_legal() -> ExecutiveAgent:
    return ExecutiveAgent("Legal", "Legal Advisor", LEGAL_SYSTEM_PROMPT, LEGAL_ANALYSIS_PROMPT)

def create_pm() -> ExecutiveAgent:
    return ExecutiveAgent("Product Manager", "Head of Product", PM_SYSTEM_PROMPT, PM_ANALYSIS_PROMPT)

def create_investor() -> ExecutiveAgent:
    return ExecutiveAgent("Investor", "Venture Capital Advisor", INVESTOR_SYSTEM_PROMPT, INVESTOR_ANALYSIS_PROMPT)


def create_all_executives() -> list[ExecutiveAgent]:
    """Create all 8 executive agents."""
    return [
        create_cto(),
        create_cfo(),
        create_coo(),
        create_cmo(),
        create_chro(),
        create_legal(),
        create_pm(),
        create_investor(),
    ]
