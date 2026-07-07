/* ------------------------------------------------------------------ */
/*  Score Panel — right sidebar with department scores & charts        */
/* ------------------------------------------------------------------ */

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AgentVote, DepartmentScore, BoardReport } from "@/lib/types";
import { AGENT_CONFIG } from "@/lib/types";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface ScorePanelProps {
  scores: DepartmentScore[];
  votes: AgentVote[];
  report: BoardReport | null;
  currentPhase: number;
}

export default function ScorePanel({
  scores,
  votes,
  report,
  currentPhase,
}: ScorePanelProps) {
  const hasScores = scores.length > 0;
  const hasVotes = votes.length > 0;

  return (
    <div className="space-y-4 p-3 h-full overflow-y-auto">
      {/* ── Meeting Status ───────────────────────────────────────── */}
      {report && (
        <Card className="glass border-0 glow-cyan">
          <CardContent className="pt-4 pb-3 text-center">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
              Board Decision
            </p>
            <p
              className={`text-xl font-bold ${
                report.overall_recommendation === "Proceed"
                  ? "text-emerald-400"
                  : report.overall_recommendation === "Reject"
                    ? "text-red-400"
                    : report.overall_recommendation === "Pivot"
                      ? "text-amber-400"
                      : "text-blue-400"
              }`}
            >
              {report.overall_recommendation}
            </p>
            <div className="mt-2">
              <ConfidenceMeter value={report.final_confidence_score} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Department Radar Chart ───────────────────────────────── */}
      {hasScores && (
        <Card className="glass border-0">
          <CardHeader className="pb-1 pt-3 px-3">
            <CardTitle className="text-xs text-muted-foreground">
              Department Scores
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-3 px-1">
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart
                data={scores.map((s) => ({
                  dept: s.department,
                  score: s.score,
                }))}
              >
                <PolarGrid stroke="hsl(217, 32%, 20%)" />
                <PolarAngleAxis
                  dataKey="dept"
                  tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 9 }}
                />
                <PolarRadiusAxis
                  domain={[0, 10]}
                  tick={{ fill: "hsl(215, 20%, 40%)", fontSize: 8 }}
                />
                <Radar
                  dataKey="score"
                  stroke="hsl(192, 91%, 43%)"
                  fill="hsl(192, 91%, 43%)"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>

            {/* Score list */}
            <div className="space-y-1.5 px-2 mt-1">
              {scores.map((s) => {
                const config = AGENT_CONFIG[s.department];
                return (
                  <div key={s.department} className="flex items-center gap-2">
                    <span className="text-xs">{config?.avatar || "📊"}</span>
                    <span className="text-[11px] flex-1 truncate">
                      {s.department}
                    </span>
                    <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-1000"
                        style={{
                          width: `${(s.score / 10) * 100}%`,
                          background: config?.color || "#06b6d4",
                        }}
                      />
                    </div>
                    <span className="text-[11px] font-mono text-muted-foreground w-6 text-right">
                      {s.score.toFixed(1)}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Voting Results ───────────────────────────────────────── */}
      {hasVotes && (
        <Card className="glass border-0">
          <CardHeader className="pb-1 pt-3 px-3">
            <CardTitle className="text-xs text-muted-foreground">
              Voting Results
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-3 px-3">
            <VotingChart votes={votes} />
            <div className="space-y-1.5 mt-3">
              {votes.map((v) => {
                const config = AGENT_CONFIG[v.agent_name];
                return (
                  <div
                    key={v.agent_name}
                    className="flex items-center gap-2"
                  >
                    <span className="text-xs">{config?.avatar || "👤"}</span>
                    <span className="text-[11px] flex-1 truncate">
                      {v.agent_name}
                    </span>
                    <Badge
                      className={`text-[9px] px-1.5 py-0 h-4 ${
                        v.vote === "YES"
                          ? "badge-yes"
                          : v.vote === "NO"
                            ? "badge-no"
                            : "badge-conditional"
                      }`}
                    >
                      {v.vote}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Risk Heatmap ─────────────────────────────────────────── */}
      {report?.risk_heatmap && report.risk_heatmap.length > 0 && (
        <Card className="glass border-0">
          <CardHeader className="pb-1 pt-3 px-3">
            <CardTitle className="text-xs text-muted-foreground">
              Risk Heatmap
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-3 px-3">
            <div className="space-y-1.5">
              {report.risk_heatmap.map((risk, i) => {
                const severityColor = {
                  Low: "bg-emerald-500/20 text-emerald-400",
                  Medium: "bg-amber-500/20 text-amber-400",
                  High: "bg-orange-500/20 text-orange-400",
                  Critical: "bg-red-500/20 text-red-400",
                }[risk.severity] || "bg-slate-500/20 text-slate-400";

                return (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-1.5 rounded-md glass-subtle"
                  >
                    <span className="text-[10px] text-muted-foreground w-14 truncate">
                      {risk.category}
                    </span>
                    <span className="text-[10px] flex-1 truncate">
                      {risk.risk_name}
                    </span>
                    <Badge className={`text-[8px] px-1 py-0 h-3.5 ${severityColor}`}>
                      {risk.severity}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── No data placeholder ──────────────────────────────────── */}
      {!hasScores && !hasVotes && currentPhase < 5 && (
        <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
          <span className="text-3xl mb-2">📊</span>
          <p className="text-xs text-center">
            Scores and charts will appear
            <br />
            after executives complete their analyses
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────────────── */

function ConfidenceMeter({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const circumference = 2 * Math.PI * 32;
  const offset = circumference - (value * circumference);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="80" height="80" className="-rotate-90">
        <circle cx="40" cy="40" r="32" fill="none" stroke="hsl(217, 32%, 15%)" strokeWidth="6" />
        <circle
          cx="40"
          cy="40"
          r="32"
          fill="none"
          stroke={value >= 0.7 ? "hsl(160, 60%, 45%)" : value >= 0.4 ? "hsl(45, 93%, 47%)" : "hsl(0, 63%, 51%)"}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000"
        />
      </svg>
      <span className="absolute text-lg font-bold">{percent}%</span>
    </div>
  );
}

function VotingChart({ votes }: { votes: AgentVote[] }) {
  const yes = votes.filter((v) => v.vote === "YES").length;
  const no = votes.filter((v) => v.vote === "NO").length;
  const conditional = votes.filter((v) => v.vote === "CONDITIONAL YES").length;

  const data = [
    { name: "Yes", value: yes, color: "hsl(160, 60%, 45%)" },
    { name: "No", value: no, color: "hsl(0, 63%, 51%)" },
    { name: "Conditional", value: conditional, color: "hsl(45, 93%, 47%)" },
  ].filter((d) => d.value > 0);

  if (data.length === 0) return null;

  return (
    <div className="flex items-center justify-center gap-4">
      <ResponsiveContainer width={80} height={80}>
        <PieChart>
          <Pie
            data={data}
            innerRadius={20}
            outerRadius={35}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="space-y-1">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: d.color }}
            />
            <span className="text-[10px]">
              {d.name}: {d.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
