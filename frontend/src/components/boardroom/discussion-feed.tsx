/* ------------------------------------------------------------------ */
/*  Live Discussion Feed — real-time board meeting messages             */
/* ------------------------------------------------------------------ */

"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { BoardMessage } from "@/lib/types";
import { AGENT_CONFIG } from "@/lib/types";

interface DiscussionFeedProps {
  messages: BoardMessage[];
}

export default function DiscussionFeed({ messages }: DiscussionFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const getMessageStyle = (type: string) => {
    if (type.startsWith("debate_challenge")) return "msg-challenge";
    if (type.startsWith("debate_question")) return "msg-question";
    if (type.startsWith("debate_defense")) return "msg-defense";
    if (type.startsWith("debate_agreement")) return "msg-agreement";
    return "";
  };

  return (
    <ScrollArea className="h-full">
      <div className="space-y-3 p-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <span className="text-4xl mb-3">🏛️</span>
            <p className="text-sm">Waiting for the board meeting to begin…</p>
          </div>
        )}

        {messages.map((msg, idx) => {
          const config = AGENT_CONFIG[msg.agent_name] || AGENT_CONFIG.System;
          const isSystem =
            msg.agent_name === "System" || msg.message_type === "phase";

          if (isSystem) {
            return (
              <div
                key={msg.id}
                className="text-center animate-fade-in-up"
                style={{ animationDelay: `${Math.min(idx * 0.02, 0.3)}s` }}
              >
                <span className="text-[11px] text-muted-foreground bg-secondary/50 px-3 py-1 rounded-full">
                  {msg.content}
                </span>
              </div>
            );
          }

          const isVote = msg.message_type === "vote";
          const isFounder = msg.agent_name === "Founder";

          return (
            <div
              key={msg.id}
              className={`animate-fade-in-up ${getMessageStyle(msg.message_type)}`}
              style={{ animationDelay: `${Math.min(idx * 0.02, 0.3)}s` }}
            >
              <div
                className={`glass-subtle rounded-xl p-3 transition-all hover:bg-secondary/20 ${
                  isFounder ? "border-l-2" : ""
                }`}
                style={isFounder ? { borderLeftColor: config.color } : {}}
              >
                {/* Header */}
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className="w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0"
                    style={{ background: `${config.color}20` }}
                  >
                    {config.avatar}
                  </span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: config.color }}
                  >
                    {msg.agent_name}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {msg.agent_role}
                  </span>
                  {isVote && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full badge-yes">
                      🗳️ Vote
                    </span>
                  )}
                  {msg.message_type.startsWith("debate_") && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                      💬 {msg.message_type.replace("debate_", "")}
                    </span>
                  )}
                </div>

                {/* Content */}
                <div className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap pl-9">
                  {msg.content}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
