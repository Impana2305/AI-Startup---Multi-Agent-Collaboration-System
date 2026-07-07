/* ------------------------------------------------------------------ */
/*  Board Report — comprehensive final report display                  */
/* ------------------------------------------------------------------ */

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { BoardReport } from "@/lib/types";
import { AGENT_CONFIG } from "@/lib/types";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface BoardReportViewProps {
  report: BoardReport;
}

export default function BoardReportView({ report }: BoardReportViewProps) {
  const recColor =
    report.overall_recommendation === "Proceed"
      ? "text-emerald-400"
      : report.overall_recommendation === "Reject"
        ? "text-red-400"
        : report.overall_recommendation === "Pivot"
          ? "text-amber-400"
          : "text-blue-400";

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-6">
      {/* ── Header ───────────────────────────────────────────────── */}
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          Board Meeting Report
        </h1>
        <p className="text-xl font-semibold">{report.startup_name}</p>
        <div className="flex items-center justify-center gap-4">
          <Badge className={`text-lg px-4 py-1 ${
            report.overall_recommendation === "Proceed"
              ? "badge-yes"
              : report.overall_recommendation === "Reject"
                ? "badge-no"
                : "badge-conditional"
          }`}>
            {report.overall_recommendation}
          </Badge>
          <span className="text-muted-foreground">
            Confidence: <span className="font-bold text-foreground">{(report.final_confidence_score * 100).toFixed(0)}%</span>
          </span>
        </div>
      </div>

      {/* ── Executive Summary ────────────────────────────────────── */}
      <Card className="glass border-0 glow-cyan">
        <CardHeader>
          <CardTitle className="text-cyan-400">📋 Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-foreground/90">
            {report.executive_summary}
          </p>
        </CardContent>
      </Card>

      {/* ── Department Scores ────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">📊 Department Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={report.department_scores.map((s) => ({ dept: s.department, score: s.score }))}>
                <PolarGrid stroke="hsl(217, 32%, 20%)" />
                <PolarAngleAxis dataKey="dept" tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 10 }} />
                <PolarRadiusAxis domain={[0, 10]} tick={{ fill: "hsl(215, 20%, 40%)", fontSize: 9 }} />
                <Radar dataKey="score" stroke="hsl(192, 91%, 43%)" fill="hsl(192, 91%, 43%)" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Voting Summary */}
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">🗳️ Voting Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center mb-4">
              <ResponsiveContainer width={180} height={180}>
                <PieChart>
                  <Pie
                    data={[
                      { name: "Yes", value: report.voting_summary.yes, color: "hsl(160, 60%, 45%)" },
                      { name: "No", value: report.voting_summary.no, color: "hsl(0, 63%, 51%)" },
                      { name: "Conditional", value: report.voting_summary.conditional_yes, color: "hsl(45, 93%, 47%)" },
                    ].filter((d) => d.value > 0)}
                    innerRadius={40}
                    outerRadius={70}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {[
                      { name: "Yes", value: report.voting_summary.yes, color: "hsl(160, 60%, 45%)" },
                      { name: "No", value: report.voting_summary.no, color: "hsl(0, 63%, 51%)" },
                      { name: "Conditional", value: report.voting_summary.conditional_yes, color: "hsl(45, 93%, 47%)" },
                    ].filter((d) => d.value > 0).map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {report.votes.map((v) => {
                const config = AGENT_CONFIG[v.agent_name];
                return (
                  <div key={v.agent_name} className="flex items-center gap-2 p-2 rounded-lg glass-subtle">
                    <span>{config?.avatar || "👤"}</span>
                    <span className="text-xs font-medium flex-1">{v.agent_name}</span>
                    <Badge className={`text-[10px] ${v.vote === "YES" ? "badge-yes" : v.vote === "NO" ? "badge-no" : "badge-conditional"}`}>
                      {v.vote}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">{(v.confidence * 100).toFixed(0)}%</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── SWOT Analysis ────────────────────────────────────────── */}
      {report.swot_analysis && (
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">🎯 SWOT Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <SWOTQuadrant title="Strengths" items={report.swot_analysis.strengths} color="emerald" icon="💪" />
              <SWOTQuadrant title="Weaknesses" items={report.swot_analysis.weaknesses} color="red" icon="⚠️" />
              <SWOTQuadrant title="Opportunities" items={report.swot_analysis.opportunities} color="cyan" icon="🚀" />
              <SWOTQuadrant title="Threats" items={report.swot_analysis.threats} color="amber" icon="🔥" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Funding Breakdown ────────────────────────────────────── */}
      {report.funding_breakdown.length > 0 && (
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">💰 Funding Breakdown</CardTitle>
            {report.estimated_budget && (
              <p className="text-xs text-muted-foreground">
                Estimated Budget: <span className="text-cyan-400 font-medium">{report.estimated_budget}</span>
              </p>
            )}
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={report.funding_breakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(217, 32%, 15%)" />
                <XAxis dataKey="category" tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 10 }} />
                <YAxis tick={{ fill: "hsl(215, 20%, 55%)", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(222, 84%, 7%)",
                    border: "1px solid hsl(217, 33%, 20%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="percentage" fill="hsl(192, 91%, 43%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* ── Timeline ─────────────────────────────────────────────── */}
      {report.suggested_timeline.length > 0 && (
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">📅 Suggested Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {report.suggested_timeline.map((phase, i) => (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center text-sm font-bold text-cyan-400">
                      {i + 1}
                    </div>
                    {i < report.suggested_timeline.length - 1 && (
                      <div className="w-[2px] flex-1 bg-border/30 mt-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className="text-sm font-semibold">{phase.phase}</p>
                    <p className="text-xs text-muted-foreground mb-2">{phase.duration}</p>
                    <div className="space-y-1">
                      {phase.milestones.map((m, j) => (
                        <p key={j} className="text-xs text-foreground/80">• {m}</p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Hiring Plan ──────────────────────────────────────────── */}
      {report.hiring_plan.length > 0 && (
        <Card className="glass border-0">
          <CardHeader>
            <CardTitle className="text-sm">👥 Hiring Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {report.hiring_plan.map((role, i) => (
                <div key={i} className="p-2.5 rounded-lg glass-subtle flex items-center gap-3">
                  <div className="text-center">
                    <p className="text-lg font-bold text-cyan-400">{role.count}</p>
                    <p className="text-[9px] text-muted-foreground">people</p>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{role.role}</p>
                    <p className="text-[10px] text-muted-foreground">{role.estimated_salary} · {role.timeline}</p>
                  </div>
                  <Badge className={`text-[9px] ${
                    role.priority === "Critical" ? "badge-no" :
                    role.priority === "High" ? "badge-conditional" : "badge-yes"
                  }`}>
                    {role.priority}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Key Risks & Next Steps ───────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {report.key_risks.length > 0 && (
          <Card className="glass border-0">
            <CardHeader>
              <CardTitle className="text-sm">⚠️ Key Risks</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {report.key_risks.map((risk, i) => (
                  <li key={i} className="text-xs text-foreground/80 flex gap-2">
                    <span className="text-red-400">•</span> {risk}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {report.next_steps.length > 0 && (
          <Card className="glass border-0">
            <CardHeader>
              <CardTitle className="text-sm">🚀 Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-1.5">
                {report.next_steps.map((step, i) => (
                  <li key={i} className="text-xs text-foreground/80 flex gap-2">
                    <span className="text-cyan-400 font-bold">{i + 1}.</span> {step}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

/* ── SWOT Quadrant ──────────────────────────────────────────────── */

function SWOTQuadrant({
  title,
  items,
  color,
  icon,
}: {
  title: string;
  items: string[];
  color: string;
  icon: string;
}) {
  const bgMap: Record<string, string> = {
    emerald: "bg-emerald-500/10 border-emerald-500/20",
    red: "bg-red-500/10 border-red-500/20",
    cyan: "bg-cyan-500/10 border-cyan-500/20",
    amber: "bg-amber-500/10 border-amber-500/20",
  };

  return (
    <div className={`p-3 rounded-lg border ${bgMap[color] || ""}`}>
      <p className="text-xs font-semibold mb-2">
        {icon} {title}
      </p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-[11px] text-foreground/80">
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
