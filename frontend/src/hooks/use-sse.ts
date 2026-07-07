/* ------------------------------------------------------------------ */
/*  SSE hook — connects to the meeting event stream                    */
/* ------------------------------------------------------------------ */

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useMeetingStore } from "@/stores/meeting-store";

export function useSSE(meetingId: string | null) {
  const sourceRef = useRef<EventSource | null>(null);
  const {
    setPhase,
    updateAgentStatus,
    addMessage,
    addDebateMessage,
    setDebateRound,
    addVote,
    setReport,
    setStatus,
  } = useMeetingStore();

  const connect = useCallback(() => {
    if (!meetingId) return;

    // Close any existing connection
    if (sourceRef.current) {
      sourceRef.current.close();
    }

    const url = `/api/meetings/stream/${meetingId}`;
    const es = new EventSource(url);
    sourceRef.current = es;

    /* ── Phase changes ─────────────────────────────────────────── */
    es.addEventListener("phase_change", (e) => {
      const data = JSON.parse(e.data);
      setPhase(data.phase, data.phase_name);
      addMessage({
        agent_name: "System",
        agent_role: "Board Secretary",
        content: data.message,
        message_type: "phase",
      });
    });

    /* ── Agent status ──────────────────────────────────────────── */
    es.addEventListener("agent_status", (e) => {
      const data = JSON.parse(e.data);
      updateAgentStatus(data.agent_name, data.agent_role, data.status);
    });

    /* ── Agent speaking ────────────────────────────────────────── */
    es.addEventListener("agent_speaking", (e) => {
      const data = JSON.parse(e.data);
      addMessage({
        agent_name: data.agent_name,
        agent_role: data.agent_role,
        content: data.content,
        message_type: data.message_type,
      });
    });

    /* ── Debate messages ───────────────────────────────────────── */
    es.addEventListener("debate_message", (e) => {
      const data = JSON.parse(e.data);
      addDebateMessage(data);
      addMessage({
        agent_name: data.speaker,
        agent_role: data.speaker_role,
        content: `${data.target ? `@${data.target}: ` : ""}${data.content}`,
        message_type: `debate_${data.message_type}`,
      });
    });

    /* ── Debate round ──────────────────────────────────────────── */
    es.addEventListener("debate_round", (e) => {
      const data = JSON.parse(e.data);
      setDebateRound(data.round);
      addMessage({
        agent_name: "System",
        agent_role: "Board Secretary",
        content: data.message,
        message_type: "round",
      });
    });

    /* ── Votes ─────────────────────────────────────────────────── */
    es.addEventListener("vote_cast", (e) => {
      const data = JSON.parse(e.data);
      addVote(data);
      addMessage({
        agent_name: data.agent_name,
        agent_role: data.agent_role,
        content: `**Vote: ${data.vote}** (Confidence: ${(data.confidence * 100).toFixed(0)}%)\n${data.reasoning}`,
        message_type: "vote",
      });
    });

    /* ── Report ready ──────────────────────────────────────────── */
    es.addEventListener("report_ready", (e) => {
      const data = JSON.parse(e.data);
      setReport(data.report);
    });

    /* ── Error ─────────────────────────────────────────────────── */
    es.addEventListener("error", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        addMessage({
          agent_name: "System",
          agent_role: "Board Secretary",
          content: `Error: ${data.message}`,
          message_type: "error",
        });
      } catch {
        // Generic SSE error
      }
      setStatus("failed");
    });

    /* ── Stream end ────────────────────────────────────────────── */
    es.addEventListener("stream_end", () => {
      es.close();
      sourceRef.current = null;
    });

    es.onerror = () => {
      // EventSource auto-reconnects; we just log it
      console.warn("SSE connection error, will retry...");
    };
  }, [meetingId, setPhase, updateAgentStatus, addMessage, addDebateMessage, setDebateRound, addVote, setReport, setStatus]);

  useEffect(() => {
    connect();
    return () => {
      if (sourceRef.current) {
        sourceRef.current.close();
        sourceRef.current = null;
      }
    };
  }, [connect]);
}
