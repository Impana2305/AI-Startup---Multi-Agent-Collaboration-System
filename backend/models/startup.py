"""Pydantic models for startup idea input data."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class StartupIdea(BaseModel):
    """The user-submitted startup proposal."""

    startup_idea: str = Field(..., description="The core startup idea")
    problem_statement: str = Field(..., description="What problem does it solve?")
    solution: str = Field(..., description="How does it solve the problem?")
    target_customers: str = Field(..., description="Who are the target customers?")
    revenue_model: str = Field(..., description="How will it make money?")
    industry: str = Field(..., description="Which industry does it operate in?")
    funding_stage: str = Field(
        ...,
        description="Current funding stage (Pre-seed, Seed, Series A, etc.)",
    )

    # Optional fields
    pitch_deck_text: Optional[str] = Field(
        None, description="Extracted text from pitch deck PDF"
    )
    business_plan_text: Optional[str] = Field(
        None, description="Extracted text from business plan PDF"
    )
    website_url: Optional[str] = Field(None, description="Company website URL")


class MeetingRequest(BaseModel):
    """API request to start a new board meeting."""

    startup: StartupIdea


class MeetingStatus(BaseModel):
    """Current status of a board meeting."""

    meeting_id: str
    status: str = Field(
        default="pending",
        description="pending | running | completed | failed",
    )
    current_phase: int = Field(default=0, description="Current step (1-9)")
    phase_name: str = Field(default="", description="Human-readable phase name")
