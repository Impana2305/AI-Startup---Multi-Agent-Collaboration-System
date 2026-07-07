/* ------------------------------------------------------------------ */
/*  Phase Timeline — bottom bar showing meeting progress               */
/* ------------------------------------------------------------------ */

"use client";

import { PHASES } from "@/lib/types";

interface PhaseTimelineProps {
  currentPhase: number;
}

export default function PhaseTimeline({ currentPhase }: PhaseTimelineProps) {
  return (
    <div className="glass-strong border-t border-border/50 px-4 py-3">
      <div className="flex items-center gap-1 overflow-x-auto">
        {PHASES.map((phase, idx) => {
          const isActive = currentPhase === phase.id;
          const isCompleted = currentPhase > phase.id;
          const isPending = currentPhase < phase.id;

          return (
            <div key={phase.id} className="flex items-center">
              {/* Phase node */}
              <div className="flex flex-col items-center min-w-[70px]">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-500 ${
                    isActive
                      ? "bg-cyan-500/20 ring-2 ring-cyan-400 scale-110"
                      : isCompleted
                        ? "bg-emerald-500/20 ring-1 ring-emerald-500/50"
                        : "bg-secondary/30 ring-1 ring-border/30"
                  }`}
                >
                  {isCompleted ? "✓" : phase.icon}
                </div>
                <span
                  className={`text-[9px] mt-1 text-center leading-tight ${
                    isActive
                      ? "text-cyan-400 font-semibold"
                      : isCompleted
                        ? "text-emerald-400/70"
                        : "text-muted-foreground/50"
                  }`}
                >
                  {phase.name}
                </span>
              </div>

              {/* Connector */}
              {idx < PHASES.length - 1 && (
                <div
                  className={`h-[2px] w-4 mx-0.5 rounded transition-all duration-500 ${
                    isCompleted
                      ? "bg-emerald-500/50"
                      : isActive
                        ? "bg-cyan-500/30"
                        : "bg-border/20"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
