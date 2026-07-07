"""Pydantic models for the final board report."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from .agent_response import AgentAnalysis, AgentVote, DebateMessage, ConflictResolution


class SWOTAnalysis(BaseModel):
    """SWOT analysis for the startup."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class RiskHeatmapItem(BaseModel):
    """A single item in the risk heatmap."""

    category: str
    risk_name: str
    likelihood: float = Field(..., ge=0, le=5, description="1-5 scale")
    impact: float = Field(..., ge=0, le=5, description="1-5 scale")
    severity: str = Field(..., description="Low | Medium | High | Critical")


class DepartmentScore(BaseModel):
    """Score for a single department."""

    department: str
    score: float = Field(..., ge=0, le=10)
    summary: str


class FundingBreakdown(BaseModel):
    """Estimated funding allocation."""

    category: str
    amount: float
    percentage: float


class HiringPlanRole(BaseModel):
    """A single role in the hiring plan."""

    role: str
    count: int
    priority: str = Field(..., description="Critical | High | Medium | Low")
    estimated_salary: str
    timeline: str


class TimelinePhase(BaseModel):
    """A phase in the suggested timeline."""

    phase: str
    duration: str
    milestones: list[str]
    key_deliverables: list[str]


class BoardReport(BaseModel):
    """The complete final board report — the primary output."""

    # Meta
    meeting_id: str
    startup_name: str

    # Executive Summary
    executive_summary: str
    overall_recommendation: str = Field(
        ..., description="Proceed | Pivot | Reject | Delay"
    )
    final_confidence_score: float = Field(
        ..., ge=0, le=1, description="Overall confidence (0-1)"
    )

    # Department Analyses
    department_analyses: list[AgentAnalysis] = Field(default_factory=list)
    department_scores: list[DepartmentScore] = Field(default_factory=list)

    # Debate & Voting
    debate_highlights: list[DebateMessage] = Field(default_factory=list)
    conflict_resolutions: list[ConflictResolution] = Field(default_factory=list)
    votes: list[AgentVote] = Field(default_factory=list)
    voting_summary: dict = Field(default_factory=dict)

    # Strategic Analysis
    swot_analysis: Optional[SWOTAnalysis] = None
    risk_heatmap: list[RiskHeatmapItem] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)

    # Financial
    estimated_budget: Optional[str] = None
    funding_recommendation: Optional[str] = None
    funding_breakdown: list[FundingBreakdown] = Field(default_factory=list)

    # Roadmap
    suggested_timeline: list[TimelinePhase] = Field(default_factory=list)
    hiring_plan: list[HiringPlanRole] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
