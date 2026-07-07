/* ------------------------------------------------------------------ */
/*  Main Page — Startup Input → Board Meeting                          */
/* ------------------------------------------------------------------ */

"use client";

import { useState } from "react";
import StartupForm from "@/components/startup-form";
import BoardroomDashboard from "@/components/boardroom/boardroom-dashboard";
import { startMeeting } from "@/lib/api";
import { useMeetingStore } from "@/stores/meeting-store";
import type { StartupIdea } from "@/lib/types";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const { meetingId, status, startMeeting: storeStart, reset } = useMeetingStore();

  const handleSubmit = async (data: StartupIdea) => {
    setIsLoading(true);
    try {
      const result = await startMeeting(data);
      storeStart(result.meeting_id);
    } catch (err) {
      console.error("Failed to start meeting:", err);
      alert("Failed to start board meeting. Make sure the backend is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewMeeting = () => {
    reset();
  };

  // Show the boardroom dashboard once a meeting is started
  if (meetingId) {
    return (
      <BoardroomDashboard
        meetingId={meetingId}
        onNewMeeting={handleNewMeeting}
      />
    );
  }

  // Show the startup input form
  return <StartupForm onSubmit={handleSubmit} isLoading={isLoading} />;
}
