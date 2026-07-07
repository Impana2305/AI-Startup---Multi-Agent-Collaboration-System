/* ------------------------------------------------------------------ */
/*  Boardroom Dashboard — the main 3-column meeting view               */
/* ------------------------------------------------------------------ */

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMeetingStore } from "@/stores/meeting-store";
import { useSSE } from "@/hooks/use-sse";
import ExecutiveCard from "./executive-card";
import DiscussionFeed from "./discussion-feed";
import PhaseTimeline from "./phase-timeline";
import ScorePanel from "./score-panel";
import BoardReportView from "@/components/report/board-report";

interface BoardroomDashboardProps {
  meetingId: string;
  onNewMeeting: () => void;
}

export default function BoardroomDashboard({
  meetingId,
  onNewMeeting,
}: BoardroomDashboardProps) {
  const [activeTab, setActiveTab] = useState("meeting");

  // Connect to SSE stream
  useSSE(meetingId);

  const {
    agents,
    messages,
    votes,
    departmentScores,
    report,
    currentPhase,
    phaseName,
    status,
  } = useMeetingStore();

  const agentList = Object.values(agents);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* ── Background effects ───────────────────────────────────── */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-[hsl(222,84%,5%)] via-[hsl(240,60%,6%)] to-[hsl(222,84%,5%)]" />
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/3 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/3 rounded-full blur-3xl" />
      </div>

      {/* ── Header ───────────────────────────────────────────────── */}
      <header className="glass-strong border-b border-border/50 px-4 py-2.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🏛️</span>
          <div>
            <h1 className="text-sm font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              AI Startup Boardroom
            </h1>
            <p className="text-[10px] text-muted-foreground">
              Meeting #{meetingId} · {phaseName || "Initializing…"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {status === "completed" && (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="h-7 bg-secondary/50">
                <TabsTrigger value="meeting" className="text-xs h-5 px-2">
                  💬 Meeting
                </TabsTrigger>
                <TabsTrigger value="report" className="text-xs h-5 px-2">
                  📋 Report
                </TabsTrigger>
              </TabsList>
            </Tabs>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onNewMeeting}
            className="text-xs h-7 border-border/50 hover:bg-secondary/50"
          >
            ✨ New Meeting
          </Button>
        </div>
      </header>

      {/* ── Main content ─────────────────────────────────────────── */}
      {activeTab === "report" && report ? (
        <div className="flex-1 overflow-y-auto">
          <BoardReportView report={report} />
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* ── Left Sidebar — Executives ────────────────────────── */}
          <aside className="w-[240px] shrink-0 glass-strong border-r border-border/50 flex flex-col">
            <div className="p-3 border-b border-border/30">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Executive Board
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
              {agentList.map((agent) => (
                <ExecutiveCard key={agent.name} agent={agent} />
              ))}
            </div>

            {/* Meeting info */}
            <div className="p-3 border-t border-border/30">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    status === "running"
                      ? "bg-cyan-400 animate-pulse"
                      : status === "completed"
                        ? "bg-emerald-400"
                        : status === "failed"
                          ? "bg-red-400"
                          : "bg-slate-400"
                  }`}
                />
                <span className="text-[10px] text-muted-foreground capitalize">
                  {status === "running" ? "Meeting in progress…" : status}
                </span>
              </div>
            </div>
          </aside>

          {/* ── Center — Discussion Feed ─────────────────────────── */}
          <main className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-hidden">
              <DiscussionFeed messages={messages} />
            </div>
          </main>

          {/* ── Right Panel — Scores & Charts ────────────────────── */}
          <aside className="w-[280px] shrink-0 glass-strong border-l border-border/50 overflow-hidden">
            <div className="p-3 border-b border-border/30">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Analytics & Scores
              </p>
            </div>
            <ScorePanel
              scores={departmentScores}
              votes={votes}
              report={report}
              currentPhase={currentPhase}
            />
          </aside>
        </div>
      )}

      {/* ── Bottom — Phase Timeline ──────────────────────────────── */}
      <PhaseTimeline currentPhase={currentPhase} />
    </div>
  );
}
