"""Pydantic models for agent responses, votes, and debate messages."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AgentAnalysis(BaseModel):
    """Structured analysis output from an executive agent."""

    agent_name: str
    agent_role: str
    summary: str = Field(..., description="Executive summary of the analysis")
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    score: float = Field(..., ge=0, le=10, description="Score out of 10")
    recommendation: str = Field(
        ..., description="Brief recommendation statement"
    )
    details: dict = Field(
        default_factory=dict,
        description="Agent-specific detailed analysis data",
    )


class DebateMessage(BaseModel):
    """A single message in the debate round."""

    speaker: str = Field(..., description="Agent name who is speaking")
    speaker_role: str = Field(..., description="Agent role (CTO, CFO, etc.)")
    target: Optional[str] = Field(
        None, description="Agent being addressed (if any)"
    )
    message_type: str = Field(
        ...,
        description="challenge | question | defense | agreement | revision",
    )
    content: str = Field(..., description="The actual message text")
    round_number: int = Field(..., description="Debate round (1-3)")


class AgentVote(BaseModel):
    """Structured vote from an executive agent."""

    agent_name: str
    agent_role: str
    vote: str = Field(..., description="YES | NO | CONDITIONAL YES")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the vote (0-1)"
    )
    reasoning: str = Field(..., description="Why they voted this way")
    conditions: list[str] = Field(
        default_factory=list,
        description="Conditions for CONDITIONAL YES votes",
    )


class ConflictResolution(BaseModel):
    """A conflict identified and resolved by the Founder."""

    conflict_topic: str
    agents_involved: list[str]
    original_positions: dict[str, str]
    resolution: str
    revised_positions: dict[str, str]
