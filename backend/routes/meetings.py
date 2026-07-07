"""Meeting API routes — start a meeting, get status, stream events."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.startup import StartupIdea, MeetingRequest, MeetingStatus
from orchestrator.board_meeting import run_board_meeting, meetings
from utils.streaming import event_bus

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("/start", response_model=MeetingStatus)
async def start_meeting(request: MeetingRequest):
    """Start a new board meeting with the given startup proposal."""
    try:
        meeting_id = await run_board_meeting(request.startup.model_dump())
        return MeetingStatus(
            meeting_id=meeting_id,
            status="running",
            current_phase=1,
            phase_name="Receiving Proposal",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{meeting_id}")
async def stream_meeting(meeting_id: str):
    """SSE endpoint — streams real-time board meeting events."""
    if meeting_id not in meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return StreamingResponse(
        event_bus.subscribe(meeting_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status/{meeting_id}", response_model=MeetingStatus)
async def get_meeting_status(meeting_id: str):
    """Get the current status of a board meeting."""
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    phase = meeting.get("current_phase", 0)
    from orchestrator.board_meeting import PHASE_NAMES

    return MeetingStatus(
        meeting_id=meeting_id,
        status=meeting.get("status", "unknown"),
        current_phase=phase,
        phase_name=PHASE_NAMES.get(phase, "Unknown"),
    )


@router.get("/report/{meeting_id}")
async def get_report(meeting_id: str):
    """Get the final board report for a completed meeting."""
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    report = meeting.get("report")
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")

    return report
