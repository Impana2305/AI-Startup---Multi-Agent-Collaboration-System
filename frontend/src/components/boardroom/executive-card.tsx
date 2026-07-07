/* ------------------------------------------------------------------ */
/*  Executive Card — shows each board member's status                  */
/* ------------------------------------------------------------------ */

"use client";

import type { AgentState } from "@/lib/types";
import { AGENT_CONFIG } from "@/lib/types";

interface ExecutiveCardProps {
  agent: AgentState;
  compact?: boolean;
}

export default function ExecutiveCard({ agent, compact }: ExecutiveCardProps) {
  const config = AGENT_CONFIG[agent.name] || AGENT_CONFIG.System;

  const statusStyles: Record<string, string> = {
    waiting: "bg-slate-500/20 text-slate-400",
    thinking: "bg-amber-500/20 text-amber-400 animate-pulse-thinking",
    speaking: "bg-cyan-500/20 text-cyan-400",
    done: "bg-emerald-500/20 text-emerald-400",
  };

  const statusLabels: Record<string, string> = {
    waiting: "Waiting",
    thinking: "Analyzing…",
    speaking: "Speaking",
    done: "Done",
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg glass-subtle transition-all hover:bg-secondary/30">
        <span className="text-lg">{config.avatar}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{agent.name}</p>
        </div>
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${statusStyles[agent.status]}`}
        >
          {statusLabels[agent.status]}
        </span>
      </div>
    );
  }

  return (
    <div
      className="group relative glass rounded-xl p-3 transition-all duration-300 hover:scale-[1.02]"
      style={{
        borderColor: `${config.color}22`,
        boxShadow:
          agent.status === "speaking"
            ? `0 0 20px ${config.color}15, 0 0 40px ${config.color}08`
            : "none",
      }}
    >
      {/* Speaking indicator glow */}
      {agent.status === "speaking" && (
        <div
          className="absolute inset-0 rounded-xl opacity-20 animate-gradient"
          style={{
            background: `linear-gradient(135deg, ${config.color}10, transparent, ${config.color}10)`,
            backgroundSize: "200% 200%",
          }}
        />
      )}

      <div className="relative flex items-center gap-3">
        {/* Avatar */}
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-lg shrink-0"
          style={{ background: `${config.color}20` }}
        >
          {config.avatar}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate">{agent.name}</p>
          <p className="text-[11px] text-muted-foreground truncate">
            {agent.role}
          </p>
        </div>

        {/* Status badge */}
        <div className="flex flex-col items-end gap-1">
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${statusStyles[agent.status]}`}
          >
            {statusLabels[agent.status]}
          </span>
          {/* Speaking wave animation */}
          {agent.status === "speaking" && (
            <div className="flex gap-[2px] items-end h-3">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="w-[2px] bg-cyan-400 rounded-full"
                  style={{
                    animation: `speaking-wave 0.6s ease-in-out infinite`,
                    animationDelay: `${i * 0.1}s`,
                    height: "6px",
                  }}
                />
              ))}
            </div>
          )}
          {/* Thinking dots */}
          {agent.status === "thinking" && (
            <div className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-amber-400"
                  style={{
                    animation: "pulse-thinking 1.2s ease-in-out infinite",
                    animationDelay: `${i * 0.2}s`,
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
