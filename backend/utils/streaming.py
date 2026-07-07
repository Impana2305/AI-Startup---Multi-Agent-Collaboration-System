"""SSE streaming helpers for real-time board meeting updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MeetingEventBus:
    """In-memory event bus that streams board meeting events via SSE.

    Each meeting gets its own queue. The SSE endpoint reads from the queue
    and forwards events to the connected frontend client.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue] = {}

    def create_meeting(self, meeting_id: str) -> None:
        """Register a new meeting's event queue."""
        self._queues[meeting_id] = asyncio.Queue()

    def remove_meeting(self, meeting_id: str) -> None:
        """Clean up a meeting's event queue."""
        self._queues.pop(meeting_id, None)

    async def emit(self, meeting_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Push an event into the meeting's queue."""
        queue = self._queues.get(meeting_id)
        if queue is None:
            logger.warning("No queue for meeting %s", meeting_id)
            return

        event = {
            "type": event_type,
            "data": data,
        }
        await queue.put(event)
        logger.info("[%s] Event: %s — %s", meeting_id, event_type, data.get("message", "")[:80])

    async def subscribe(self, meeting_id: str):
        """Async generator that yields SSE-formatted events."""
        queue = self._queues.get(meeting_id)
        if queue is None:
            return

        while True:
            event = await queue.get()

            # Sentinel to end the stream
            if event.get("type") == "stream_end":
                yield f"event: stream_end\ndata: {json.dumps(event['data'])}\n\n"
                break

            yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"

    async def emit_phase_change(
        self, meeting_id: str, phase: int, phase_name: str
    ) -> None:
        """Emit a phase transition event."""
        await self.emit(meeting_id, "phase_change", {
            "phase": phase,
            "phase_name": phase_name,
            "message": f"Phase {phase}: {phase_name}",
        })

    async def emit_agent_status(
        self,
        meeting_id: str,
        agent_name: str,
        agent_role: str,
        status: str,
    ) -> None:
        """Emit an agent status change (thinking/speaking/waiting/done)."""
        await self.emit(meeting_id, "agent_status", {
            "agent_name": agent_name,
            "agent_role": agent_role,
            "status": status,
        })

    async def emit_agent_speaking(
        self,
        meeting_id: str,
        agent_name: str,
        agent_role: str,
        content: str,
        message_type: str = "analysis",
    ) -> None:
        """Emit agent speech/analysis content."""
        await self.emit(meeting_id, "agent_speaking", {
            "agent_name": agent_name,
            "agent_role": agent_role,
            "content": content,
            "message_type": message_type,
        })

    async def emit_debate_message(
        self,
        meeting_id: str,
        speaker: str,
        speaker_role: str,
        target: str | None,
        message_type: str,
        content: str,
        round_number: int,
    ) -> None:
        """Emit a debate message."""
        await self.emit(meeting_id, "debate_message", {
            "speaker": speaker,
            "speaker_role": speaker_role,
            "target": target,
            "message_type": message_type,
            "content": content,
            "round_number": round_number,
        })

    async def emit_vote(
        self,
        meeting_id: str,
        agent_name: str,
        agent_role: str,
        vote: str,
        confidence: float,
        reasoning: str,
    ) -> None:
        """Emit a vote event."""
        await self.emit(meeting_id, "vote_cast", {
            "agent_name": agent_name,
            "agent_role": agent_role,
            "vote": vote,
            "confidence": confidence,
            "reasoning": reasoning,
        })

    async def emit_report_ready(
        self, meeting_id: str, report: dict[str, Any]
    ) -> None:
        """Emit the final report and end the stream."""
        await self.emit(meeting_id, "report_ready", {
            "message": "Board report is ready",
            "report": report,
        })
        # End the SSE stream
        await self.emit(meeting_id, "stream_end", {
            "message": "Meeting concluded",
        })


# Global singleton
event_bus = MeetingEventBus()
