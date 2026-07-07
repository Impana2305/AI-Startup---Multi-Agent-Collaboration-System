/* ------------------------------------------------------------------ */
/*  Zustand store for board meeting state                              */
/* ------------------------------------------------------------------ */

import { create } from "zustand";
import type {
  AgentState,
  AgentVote,
  BoardMessage,
  BoardReport,
  DepartmentScore,
  DebateMessage,
} from "@/lib/types";
import { AGENT_CONFIG } from "@/lib/types";

interface MeetingStore {
  // ── Connection state ───────────────────────────────────────────
  meetingId: string | null;
  status: "idle" | "running" | "completed" | "failed";

  // ── Phase tracking ─────────────────────────────────────────────
  currentPhase: number;
  phaseName: string;

  // ── Agents ─────────────────────────────────────────────────────
  agents: Record<string, AgentState>;

  // ── Discussion feed ────────────────────────────────────────────
  messages: BoardMessage[];

  // ── Debate ─────────────────────────────────────────────────────
  debateRound: number;
  debateMessages: DebateMessage[];

  // ── Voting ─────────────────────────────────────────────────────
  votes: AgentVote[];

  // ── Scores ─────────────────────────────────────────────────────
  departmentScores: DepartmentScore[];

  // ── Final report ───────────────────────────────────────────────
  report: BoardReport | null;

  // ── Actions ────────────────────────────────────────────────────
  startMeeting: (meetingId: string) => void;
  setPhase: (phase: number, phaseName: string) => void;
  updateAgentStatus: (name: string, role: string, status: AgentState["status"]) => void;
  addMessage: (msg: Omit<BoardMessage, "id" | "timestamp">) => void;
  addDebateMessage: (msg: DebateMessage) => void;
  setDebateRound: (round: number) => void;
  addVote: (vote: AgentVote) => void;
  setReport: (report: BoardReport) => void;
  setStatus: (status: MeetingStore["status"]) => void;
  reset: () => void;
}

const initialAgents: Record<string, AgentState> = Object.fromEntries(
  Object.entries(AGENT_CONFIG)
    .filter(([name]) => name !== "System")
    .map(([name, config]) => [
      name,
      { name, role: "", status: "waiting" as const, avatar: config.avatar },
    ]),
);

// Set roles
const roleMap: Record<string, string> = {
  Founder: "CEO",
  CTO: "Chief Technology Officer",
  CFO: "Chief Financial Officer",
  COO: "Chief Operating Officer",
  CMO: "Chief Marketing Officer",
  CHRO: "Chief Human Resources Officer",
  Legal: "Legal Advisor",
  "Product Manager": "Head of Product",
  Investor: "Venture Capital Advisor",
};
Object.entries(roleMap).forEach(([name, role]) => {
  if (initialAgents[name]) initialAgents[name].role = role;
});

const initialState = {
  meetingId: null as string | null,
  status: "idle" as const,
  currentPhase: 0,
  phaseName: "",
  agents: { ...initialAgents },
  messages: [] as BoardMessage[],
  debateRound: 0,
  debateMessages: [] as DebateMessage[],
  votes: [] as AgentVote[],
  departmentScores: [] as DepartmentScore[],
  report: null as BoardReport | null,
};

export const useMeetingStore = create<MeetingStore>((set) => ({
  ...initialState,

  startMeeting: (meetingId) =>
    set({
      meetingId,
      status: "running",
      currentPhase: 1,
      phaseName: "Receiving Proposal",
    }),

  setPhase: (phase, phaseName) =>
    set({ currentPhase: phase, phaseName }),

  updateAgentStatus: (name, role, status) =>
    set((state) => {
      const agent = state.agents[name];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [name]: { ...agent, role: role || agent.role, status },
        },
      };
    }),

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...msg,
          id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          timestamp: Date.now(),
        },
      ],
    })),

  addDebateMessage: (msg) =>
    set((state) => ({
      debateMessages: [...state.debateMessages, msg],
    })),

  setDebateRound: (round) => set({ debateRound: round }),

  addVote: (vote) =>
    set((state) => ({
      votes: [...state.votes, vote],
    })),

  setReport: (report) =>
    set({
      report,
      status: "completed",
      departmentScores: report.department_scores || [],
    }),

  setStatus: (status) => set({ status }),

  reset: () => set({ ...initialState, agents: { ...initialAgents } }),
}));
