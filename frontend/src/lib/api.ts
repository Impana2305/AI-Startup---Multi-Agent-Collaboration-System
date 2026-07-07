/* ------------------------------------------------------------------ */
/*  API client for the FastAPI backend                                 */
/* ------------------------------------------------------------------ */

import type { StartupIdea, MeetingStatus } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function startMeeting(startup: StartupIdea): Promise<MeetingStatus> {
  const res = await fetch(`${API_BASE}/api/meetings/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ startup }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to start meeting");
  }

  return res.json();
}

export async function getMeetingStatus(meetingId: string): Promise<MeetingStatus> {
  const res = await fetch(`${API_BASE}/api/meetings/status/${meetingId}`);
  if (!res.ok) throw new Error("Failed to get meeting status");
  return res.json();
}

export async function getReport(meetingId: string) {
  const res = await fetch(`${API_BASE}/api/meetings/report/${meetingId}`);
  if (!res.ok) throw new Error("Report not available yet");
  return res.json();
}

export async function uploadPDF(file: File): Promise<{ extracted_text: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/documents/upload-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload PDF");
  }

  return res.json();
}
