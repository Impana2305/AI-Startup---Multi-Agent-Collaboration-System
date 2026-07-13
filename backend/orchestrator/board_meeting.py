"""Board Meeting Orchestrator — the 9-step workflow engine.

This is the heart of the multi-agent collaboration system.  It drives
the full board-meeting lifecycle from proposal intake through the final
report, streaming every event to the frontend in real time via SSE.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from agents.founder import FounderAgent
from agents.executives import ExecutiveAgent, create_all_executives
from utils.streaming import event_bus

logger = logging.getLogger(__name__)

from config import settings

def get_concurrency_settings() -> tuple[int, float]:
    """Determine the semaphore limit and stagger delay based on the number of keys."""
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    if provider == "auto":
        provider = "groq" if getattr(settings, "groq_api_keys", []) else "gemini"

    if provider == "groq":
        keys = getattr(settings, "groq_api_keys", [])
    else:
        keys = getattr(settings, "google_api_keys", [])

    num_keys = len(keys)
    if num_keys <= 1:
        return 1, 6.0
    elif num_keys == 2:
        return 2, 3.0
    elif num_keys <= 4:
        return 3, 1.5
    else:
        return 4, 1.0


def _get_compact_analyses(analyses_dict: dict) -> str:
    """Formats raw agent analyses into a compact text block to save token quota."""
    compact = []
    for name, analysis in analyses_dict.items():
        score = analysis.get("score", "N/A")
        rec = analysis.get("recommendation", "N/A")
        summary = analysis.get("summary", "")
        truncated_summary = summary[:300] + "..." if len(summary) > 300 else summary

        pros = ", ".join(analysis.get("pros", []))
        cons = ", ".join(analysis.get("cons", []))
        risks = ", ".join(analysis.get("risks", []))

        compact.append(
            f"- **{name} ({analysis.get('agent_role', 'Executive')})** [Score: {score}/10, Rec: {rec}]\n"
            f"  Summary: {truncated_summary}\n"
            f"  Pros: {pros}\n"
            f"  Cons: {cons}\n"
            f"  Risks: {risks}"
        )
    return "\n\n".join(compact)


def _get_compact_debate_history(messages: list) -> str:
    """Formats debate message history into a compact, space-efficient list."""
    if not messages:
        return "No previous messages yet."
    compact = []
    for msg in messages:
        compact.append(
            f"Round {msg.get('round_number', 1)}: {msg.get('speaker')} ({msg.get('speaker_role')}) to {msg.get('target', 'All')}: \"{msg.get('content')}\""
        )
    return "\n".join(compact)


# In-memory store for meeting state
meetings: dict[str, dict[str, Any]] = {}


PHASE_NAMES = {
    1: "Receiving Proposal",
    2: "Summarizing Proposal",
    3: "Delegating Tasks",
    4: "Independent Analysis",
    5: "Gathering Reports",
    6: "Board Debate",
    7: "Conflict Resolution",
    8: "Voting",
    9: "Final Decision",
}


async def run_board_meeting(startup_data: dict) -> str:
    """Launch a full board meeting.  Returns the meeting_id.

    The meeting runs as a background task so the SSE stream can push
    events to the client as they happen.
    """
    meeting_id = str(uuid.uuid4())[:8]

    meetings[meeting_id] = {
        "id": meeting_id,
        "status": "running",
        "current_phase": 0,
        "startup": startup_data,
        "summary": None,
        "analyses": {},
        "debate_messages": [],
        "conflicts": [],
        "votes": [],
        "report": None,
    }

    event_bus.create_meeting(meeting_id)

    # Run the meeting in the background while keeping a reference to the task.
    task = asyncio.create_task(_execute_meeting(meeting_id), name=f"board-meeting-{meeting_id}")
    meetings[meeting_id]["task"] = task
    task.add_done_callback(lambda completed_task: meetings.get(meeting_id, {}).pop("task", None))

    return meeting_id


async def _execute_meeting(meeting_id: str) -> None:
    """Execute the full 9-step board meeting workflow."""
    meeting = meetings[meeting_id]
    founder = FounderAgent()
    executives = create_all_executives()

    try:
        # ── Step 1: Receive Proposal ────────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 1, PHASE_NAMES[1])
        meeting["current_phase"] = 1

        proposal = meeting["startup"]
        proposal_text = _format_proposal(proposal)

        await event_bus.emit_agent_speaking(
            meeting_id, "System", "Board Secretary",
            f"New startup proposal received. Convening the board...",
            "system",
        )
        await asyncio.sleep(0.5)

        # ── Step 2: Summarize Proposal ──────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 2, PHASE_NAMES[2])
        meeting["current_phase"] = 2

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "thinking")

        summary_result = await founder.summarize_proposal(proposal)
        meeting["summary"] = summary_result

        startup_name = summary_result.get("startup_name", "This Startup")
        exec_summary = summary_result.get("executive_summary", "")

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "speaking")
        await event_bus.emit_agent_speaking(
            meeting_id, "Founder", "CEO",
            f"Good morning, board. Today we're evaluating **{startup_name}**.\n\n{exec_summary}\n\nLet me assign each of you your evaluation tasks.",
            "summary",
        )
        await asyncio.sleep(0.3)

        # ── Step 3: Delegate Tasks ──────────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 3, PHASE_NAMES[3])
        meeting["current_phase"] = 3

        for agent in executives:
            await event_bus.emit_agent_speaking(
                meeting_id, "Founder", "CEO",
                f"**{agent.name}**, please evaluate this from a {agent.role} perspective.",
                "delegation",
            )
            await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "waiting")
            await asyncio.sleep(0.15)

        # ── Step 4: Independent Analysis (parallel) ─────────────────
        await event_bus.emit_phase_change(meeting_id, 4, PHASE_NAMES[4])
        meeting["current_phase"] = 4

        # Mark all agents as thinking
        for agent in executives:
            await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "thinking")

        summary_text = json.dumps(summary_result, indent=2)

        # Run analyses with rate limiting to avoid RESOURCE_EXHAUSTED
        analyses = await _run_with_rate_limit(
            [
                _run_agent_analysis(meeting_id, agent, summary_text, proposal_text)
                for agent in executives
            ]
        )

        # Store results
        for agent, result in zip(executives, analyses):
            if isinstance(result, Exception):
                logger.error("Agent %s failed: %s", agent.name, result)
                result = {
                    "agent_name": agent.name,
                    "agent_role": agent.role,
                    "summary": f"Analysis failed: {result}",
                    "score": 5.0,
                    "pros": [],
                    "cons": [],
                    "risks": [str(result)],
                    "recommendation": "Retry required",
                    "details": {},
                }
            meeting["analyses"][agent.name] = result

        # ── Step 5: Gather Reports ──────────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 5, PHASE_NAMES[5])
        meeting["current_phase"] = 5

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "speaking")
        await event_bus.emit_agent_speaking(
            meeting_id, "Founder", "CEO",
            "Thank you all for your analyses. I've reviewed all reports. Now let's open the floor for discussion. Challenge each other's assumptions — that's what this board is for.",
            "transition",
        )
        await asyncio.sleep(0.3)

        # ── Step 6: Debate Round (3 rounds) ─────────────────────────
        await event_bus.emit_phase_change(meeting_id, 6, PHASE_NAMES[6])
        meeting["current_phase"] = 6

        all_analyses_text = json.dumps(meeting["analyses"], indent=2)
        compact_analyses_text = _get_compact_analyses(meeting["analyses"])

        for round_num in range(1, 4):  # 3 debate rounds
            await event_bus.emit(meeting_id, "debate_round", {
                "round": round_num,
                "message": f"Debate Round {round_num} of 3",
            })

            previous_msgs = _get_compact_debate_history(meeting["debate_messages"])

            # Run debates with rate limiting to avoid RESOURCE_EXHAUSTED
            debate_results = await _run_with_rate_limit(
                [
                    _run_agent_debate(
                        meeting_id, agent,
                        json.dumps(meeting["analyses"].get(agent.name, {})),
                        compact_analyses_text,
                        previous_msgs,
                        round_num,
                    )
                    for agent in executives
                ]
            )

            # Process debate messages
            for agent, result in zip(executives, debate_results):
                if isinstance(result, Exception):
                    logger.error("Debate failed for %s: %s", agent.name, result)
                    continue

                messages = result.get("messages", [])
                for msg in messages:
                    debate_msg = {
                        "speaker": agent.name,
                        "speaker_role": agent.role,
                        "target": msg.get("target", "All"),
                        "message_type": msg.get("message_type", "comment"),
                        "content": msg.get("content", ""),
                        "round_number": round_num,
                    }
                    meeting["debate_messages"].append(debate_msg)

                    await event_bus.emit_debate_message(
                        meeting_id,
                        agent.name,
                        agent.role,
                        msg.get("target"),
                        msg.get("message_type", "comment"),
                        msg.get("content", ""),
                        round_num,
                    )
                    await asyncio.sleep(0.1)

        # ── Step 7: Conflict Resolution ─────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 7, PHASE_NAMES[7])
        meeting["current_phase"] = 7

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "thinking")

        debate_transcript = json.dumps(meeting["debate_messages"], indent=2)
        compact_debate = _get_compact_debate_history(meeting["debate_messages"])
        compact_analyses = _get_compact_analyses(meeting["analyses"])
        conflict_result = await founder.resolve_conflicts(
            compact_debate, compact_analyses
        )

        meeting["conflicts"] = conflict_result.get("conflicts", [])

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "speaking")

        # Announce conflicts
        for conflict in meeting["conflicts"]:
            await event_bus.emit_agent_speaking(
                meeting_id, "Founder", "CEO",
                f"I've identified a conflict regarding **{conflict.get('conflict_topic', 'N/A')}** "
                f"between {', '.join(conflict.get('agents_involved', []))}. "
                f"My resolution: {conflict.get('resolution', 'N/A')}",
                "conflict_resolution",
            )
            await asyncio.sleep(0.2)

        # Ask for revisions
        revision_requests = conflict_result.get("revision_requests", [])
        revision_agent_map = {a.name: a for a in executives}

        for req in revision_requests:
            target_name = req.get("target_agent", "")
            agent = revision_agent_map.get(target_name)
            if agent:
                await event_bus.emit_agent_speaking(
                    meeting_id, "Founder", "CEO",
                    f"**{target_name}**, I'd like you to reconsider: {req.get('request', '')}",
                    "revision_request",
                )

                await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "thinking")

                revision = await agent.revise(
                    revision_request=req.get("request", ""),
                    original_position=json.dumps(meeting["analyses"].get(agent.name, {})),
                    debate_context=compact_debate[:3000],
                )

                status = "revised their position" if revision.get("revised") else "maintained their position"
                await event_bus.emit_agent_speaking(
                    meeting_id, agent.name, agent.role,
                    f"I've {status}. {revision.get('reasoning', '')}",
                    "revision_response",
                )
                await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "done")
                await asyncio.sleep(0.15)

        # ── Step 8: Voting ──────────────────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 8, PHASE_NAMES[8])
        meeting["current_phase"] = 8

        await event_bus.emit_agent_speaking(
            meeting_id, "Founder", "CEO",
            "The debate is concluded. Each board member will now cast their vote. Please vote YES, NO, or CONDITIONAL YES with your reasoning.",
            "voting_start",
        )
        await asyncio.sleep(0.3)

        compact_debate_summary = _get_compact_debate_history(meeting["debate_messages"])
        conflicts_text = json.dumps(meeting["conflicts"], indent=2)

        # Run votes with rate limiting to avoid RESOURCE_EXHAUSTED
        vote_results = await _run_with_rate_limit(
            [
                _run_agent_vote(
                    meeting_id, agent,
                    json.dumps(meeting["analyses"].get(agent.name, {})),
                    compact_debate_summary,
                    conflicts_text,
                )
                for agent in executives
            ]
        )

        for agent, result in zip(executives, vote_results):
            if isinstance(result, Exception):
                logger.error("Vote failed for %s: %s", agent.name, result)
                result = {
                    "agent_name": agent.name,
                    "agent_role": agent.role,
                    "vote": "CONDITIONAL YES",
                    "confidence": 0.5,
                    "reasoning": f"Vote processing failed: {result}",
                    "conditions": ["Technical issues during voting"],
                }

            meeting["votes"].append(result)
            await event_bus.emit_vote(
                meeting_id,
                result.get("agent_name", agent.name),
                result.get("agent_role", agent.role),
                result.get("vote", "CONDITIONAL YES"),
                result.get("confidence", 0.5),
                result.get("reasoning", ""),
            )
            await asyncio.sleep(0.2)

        # ── Step 9: Final Decision ──────────────────────────────────
        await event_bus.emit_phase_change(meeting_id, 9, PHASE_NAMES[9])
        meeting["current_phase"] = 9

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "thinking")

        final_decision = await founder.make_final_decision(
            summary=json.dumps(meeting["summary"]),
            analyses=compact_analyses_text,
            debate=compact_debate[:4000],
            conflicts=conflicts_text,
            votes=json.dumps(meeting["votes"], indent=2),
        )

        # Build the complete board report
        report = _build_report(meeting_id, meeting, final_decision)
        meeting["report"] = report
        meeting["status"] = "completed"

        await event_bus.emit_agent_status(meeting_id, "Founder", "CEO", "speaking")
        await event_bus.emit_agent_speaking(
            meeting_id, "Founder", "CEO",
            f"The board has reached its decision. Our recommendation is: **{final_decision.get('overall_recommendation', 'Pending')}** "
            f"with a confidence score of **{final_decision.get('final_confidence_score', 0):.0%}**.\n\n"
            f"{final_decision.get('executive_summary', '')}",
            "final_decision",
        )

        await event_bus.emit_report_ready(meeting_id, report)

    except asyncio.CancelledError:
        meeting["status"] = "cancelled"
        logger.info("Board meeting %s was cancelled", meeting_id)
        raise
    except Exception as e:
        logger.exception("Board meeting %s failed: %s", meeting_id, e)
        meeting["status"] = "failed"
        await event_bus.emit(meeting_id, "error", {
            "message": f"Meeting failed: {str(e)}"
        })
        await event_bus.emit(meeting_id, "stream_end", {
            "message": "Meeting ended due to error"
        })


# ---------------------------------------------------------------------------
# Rate-limited execution helper
# ---------------------------------------------------------------------------

async def _run_with_rate_limit(
    coroutines: list,
) -> list[Any]:
    """Run coroutines with concurrency limiting and staggered delays.

    Uses a semaphore to cap concurrent API calls and adds a small
    delay between launches so we don't burst past the rate limits.
    """
    concurrency_limit, stagger_delay = get_concurrency_settings()
    sem = asyncio.Semaphore(concurrency_limit)
    results: list[Any] = [None] * len(coroutines)

    async def _wrapped(index: int, coro):
        # Sleep first to stagger the launches (before acquiring semaphore)
        if stagger_delay > 0:
            await asyncio.sleep(index * stagger_delay)
        async with sem:
            try:
                results[index] = await coro
            except Exception as exc:
                results[index] = exc

    tasks = [
        asyncio.create_task(_wrapped(i, coro), name=f"rate-limited-agent-{i}")
        for i, coro in enumerate(coroutines)
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    return results


# ---------------------------------------------------------------------------
# Helper coroutines for agent execution
# ---------------------------------------------------------------------------

async def _run_agent_analysis(
    meeting_id: str,
    agent: ExecutiveAgent,
    summary: str,
    proposal: str,
) -> dict[str, Any]:
    """Run a single agent's analysis and emit events."""
    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "thinking")

    result = await agent.analyze(summary, proposal)

    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "speaking")
    await event_bus.emit_agent_speaking(
        meeting_id, agent.name, agent.role,
        f"**{agent.name} Assessment** (Score: {result.get('score', 'N/A')}/10)\n\n"
        f"{result.get('summary', 'Analysis complete.')}\n\n"
        f"**Recommendation**: {result.get('recommendation', 'N/A')}",
        "analysis",
    )
    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "done")

    return result


async def _run_agent_debate(
    meeting_id: str,
    agent: ExecutiveAgent,
    own_analysis: str,
    other_analyses: str,
    previous_messages: str,
    round_number: int,
) -> dict[str, Any]:
    """Run a single agent's debate contribution."""
    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "thinking")

    result = await agent.debate(own_analysis, other_analyses, previous_messages, round_number)

    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "done")
    return result


async def _run_agent_vote(
    meeting_id: str,
    agent: ExecutiveAgent,
    own_analysis: str,
    debate_summary: str,
    conflicts: str,
) -> dict[str, Any]:
    """Run a single agent's vote."""
    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "thinking")

    result = await agent.vote(own_analysis, debate_summary, conflicts)

    await event_bus.emit_agent_status(meeting_id, agent.name, agent.role, "done")
    return result


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _format_proposal(proposal: dict) -> str:
    """Format the startup proposal into a readable text block."""
    parts = [
        f"**Startup Idea**: {proposal.get('startup_idea', 'N/A')}",
        f"**Problem Statement**: {proposal.get('problem_statement', 'N/A')}",
        f"**Solution**: {proposal.get('solution', 'N/A')}",
        f"**Target Customers**: {proposal.get('target_customers', 'N/A')}",
        f"**Revenue Model**: {proposal.get('revenue_model', 'N/A')}",
        f"**Industry**: {proposal.get('industry', 'N/A')}",
        f"**Funding Stage**: {proposal.get('funding_stage', 'N/A')}",
    ]

    if proposal.get("pitch_deck_text"):
        parts.append(f"\n**Pitch Deck Content**:\n{proposal['pitch_deck_text'][:3000]}")

    if proposal.get("business_plan_text"):
        parts.append(f"\n**Business Plan Content**:\n{proposal['business_plan_text'][:3000]}")

    if proposal.get("website_url"):
        parts.append(f"**Website**: {proposal['website_url']}")

    return "\n\n".join(parts)


def _build_report(
    meeting_id: str,
    meeting: dict,
    final_decision: dict,
) -> dict[str, Any]:
    """Compile the complete board report from all meeting data."""
    summary = meeting.get("summary", {})

    # Build department scores from analyses
    department_scores = []
    for name, analysis in meeting.get("analyses", {}).items():
        department_scores.append({
            "department": name,
            "score": analysis.get("score", 5.0),
            "summary": analysis.get("summary", ""),
        })

    # Build voting summary
    votes = meeting.get("votes", [])
    yes_count = sum(1 for v in votes if v.get("vote") == "YES")
    no_count = sum(1 for v in votes if v.get("vote") == "NO")
    conditional_count = sum(1 for v in votes if v.get("vote") == "CONDITIONAL YES")
    avg_confidence = (
        sum(v.get("confidence", 0.5) for v in votes) / len(votes)
        if votes
        else 0.5
    )

    return {
        "meeting_id": meeting_id,
        "startup_name": summary.get("startup_name", "Unnamed Startup"),
        "executive_summary": final_decision.get("executive_summary", ""),
        "overall_recommendation": final_decision.get("overall_recommendation", "Pending"),
        "final_confidence_score": final_decision.get("final_confidence_score", 0.5),

        "department_analyses": list(meeting.get("analyses", {}).values()),
        "department_scores": department_scores,

        "debate_highlights": meeting.get("debate_messages", [])[:15],
        "conflict_resolutions": meeting.get("conflicts", []),
        "votes": votes,
        "voting_summary": {
            "yes": yes_count,
            "no": no_count,
            "conditional_yes": conditional_count,
            "total": len(votes),
            "average_confidence": round(avg_confidence, 2),
        },

        "swot_analysis": final_decision.get("swot_analysis"),
        "risk_heatmap": final_decision.get("risk_heatmap", []),
        "key_risks": final_decision.get("key_risks", []),
        "trade_offs": final_decision.get("trade_offs", []),

        "estimated_budget": final_decision.get("estimated_budget"),
        "funding_recommendation": final_decision.get("funding_recommendation"),
        "funding_breakdown": final_decision.get("funding_breakdown", []),

        "suggested_timeline": final_decision.get("suggested_timeline", []),
        "hiring_plan": final_decision.get("hiring_plan", []),
        "next_steps": final_decision.get("next_steps", []),
    }
