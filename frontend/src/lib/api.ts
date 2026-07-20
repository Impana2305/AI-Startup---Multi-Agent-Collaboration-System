/* ------------------------------------------------------------------ */
/*  API client for the FastAPI backend                                 */
/* ------------------------------------------------------------------ */

import type { StartupIdea, MeetingStatus } from "@/lib/types";

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
    return "http://localhost:8000";
  }
  return "";
}

async function parseError(res: Response, defaultMessage: string): Promise<string> {
  try {
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await res.json();
      return data.detail || data.message || defaultMessage;
    }
    const text = await res.text();
    if (res.status === 500 || res.status === 502 || res.status === 503 || res.status === 504) {
      if (text.includes("ECONNREFUSED") || text.includes("Failed to proxy")) {
        return "Cannot connect to backend server. Please make sure FastAPI backend is running on port 8000.";
      }
    }
    return text || defaultMessage;
  } catch {
    return defaultMessage;
  }
}

export async function startMeeting(startup: StartupIdea): Promise<MeetingStatus> {
  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}/api/meetings/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ startup }),
  });

  if (!res.ok) {
    const errorMsg = await parseError(res, "Failed to start meeting");
    throw new Error(errorMsg);
  }

  return res.json();
}

export async function getMeetingStatus(meetingId: string): Promise<MeetingStatus> {
  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}/api/meetings/status/${meetingId}`);
  if (!res.ok) {
    const errorMsg = await parseError(res, "Failed to get meeting status");
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function getReport(meetingId: string) {
  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}/api/meetings/report/${meetingId}`);
  if (!res.ok) {
    const errorMsg = await parseError(res, "Report not available yet");
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function uploadPDF(file: File): Promise<{ extracted_text: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}/api/documents/upload-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorMsg = await parseError(res, "Failed to upload PDF");
    throw new Error(errorMsg);
  }

  return res.json();
}
