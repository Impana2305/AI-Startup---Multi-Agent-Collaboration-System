/* ------------------------------------------------------------------ */
/*  TypeScript types for the AI Startup Boardroom                      */
/* ------------------------------------------------------------------ */

export interface StartupIdea {
  startup_idea: string;
  problem_statement: string;
  solution: string;
  target_customers: string;
  revenue_model: string;
  industry: string;
  funding_stage: string;
  pitch_deck_text?: string;
  business_plan_text?: string;
  website_url?: string;
}

export interface MeetingStatus {
  meeting_id: string;
  status: "pending" | "running" | "completed" | "failed";
  current_phase: number;
  phase_name: string;
}

/* ---- Agent types ---- */

export type AgentStatus = "waiting" | "thinking" | "speaking" | "done";

export interface AgentState {
  name: string;
  role: string;
  status: AgentStatus;
  avatar: string;
}

export interface AgentAnalysis {
  agent_name: string;
  agent_role: string;
  summary: string;
  pros: string[];
  cons: string[];
  risks: string[];
  score: number;
  recommendation: string;
  details: Record<string, unknown>;
}

export interface DebateMessage {
  speaker: string;
  speaker_role: string;
  target: string | null;
  message_type: "challenge" | "question" | "defense" | "agreement" | "revision" | "comment";
  content: string;
  round_number: number;
}

export interface AgentVote {
  agent_name: string;
  agent_role: string;
  vote: "YES" | "NO" | "CONDITIONAL YES";
  confidence: number;
  reasoning: string;
  conditions: string[];
}

/* ---- Board messages (for the discussion feed) ---- */

export interface BoardMessage {
  id: string;
  agent_name: string;
  agent_role: string;
  content: string;
  message_type: string;
  timestamp: number;
}

/* ---- Report types ---- */

export interface SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface RiskHeatmapItem {
  category: string;
  risk_name: string;
  likelihood: number;
  impact: number;
  severity: "Low" | "Medium" | "High" | "Critical";
}

export interface DepartmentScore {
  department: string;
  score: number;
  summary: string;
}

export interface FundingBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

export interface HiringPlanRole {
  role: string;
  count: number;
  priority: string;
  estimated_salary: string;
  timeline: string;
}

export interface TimelinePhase {
  phase: string;
  duration: string;
  milestones: string[];
  key_deliverables: string[];
}

export interface BoardReport {
  meeting_id: string;
  startup_name: string;
  executive_summary: string;
  overall_recommendation: "Proceed" | "Pivot" | "Reject" | "Delay" | string;
  final_confidence_score: number;
  department_analyses: AgentAnalysis[];
  department_scores: DepartmentScore[];
  debate_highlights: DebateMessage[];
  conflict_resolutions: Array<{
    conflict_topic: string;
    agents_involved: string[];
    original_positions: Record<string, string>;
    resolution: string;
  }>;
  votes: AgentVote[];
  voting_summary: {
    yes: number;
    no: number;
    conditional_yes: number;
    total: number;
    average_confidence: number;
  };
  swot_analysis: SWOTAnalysis | null;
  risk_heatmap: RiskHeatmapItem[];
  key_risks: string[];
  trade_offs: string[];
  estimated_budget: string | null;
  funding_recommendation: string | null;
  funding_breakdown: FundingBreakdown[];
  suggested_timeline: TimelinePhase[];
  hiring_plan: HiringPlanRole[];
  next_steps: string[];
}

/* ---- SSE event types ---- */

export type SSEEventType =
  | "phase_change"
  | "agent_status"
  | "agent_speaking"
  | "debate_message"
  | "debate_round"
  | "vote_cast"
  | "report_ready"
  | "error"
  | "stream_end";

/* ---- Phase constants ---- */

export const PHASES = [
  { id: 1, name: "Receiving Proposal", icon: "📥" },
  { id: 2, name: "Summarizing", icon: "📝" },
  { id: 3, name: "Delegating", icon: "📋" },
  { id: 4, name: "Analysis", icon: "🔍" },
  { id: 5, name: "Gathering", icon: "📊" },
  { id: 6, name: "Debate", icon: "💬" },
  { id: 7, name: "Resolving", icon: "⚖️" },
  { id: 8, name: "Voting", icon: "🗳️" },
  { id: 9, name: "Decision", icon: "✅" },
] as const;

/* ---- Agent config (avatars & colors) ---- */

export const AGENT_CONFIG: Record<string, { avatar: string; color: string; gradient: string }> = {
  Founder:           { avatar: "👔", color: "#8b5cf6", gradient: "from-violet-500 to-purple-600" },
  CTO:               { avatar: "💻", color: "#06b6d4", gradient: "from-cyan-500 to-blue-600" },
  CFO:               { avatar: "💰", color: "#10b981", gradient: "from-emerald-500 to-green-600" },
  COO:               { avatar: "⚙️", color: "#f59e0b", gradient: "from-amber-500 to-orange-600" },
  CMO:               { avatar: "📣", color: "#ec4899", gradient: "from-pink-500 to-rose-600" },
  CHRO:              { avatar: "👥", color: "#6366f1", gradient: "from-indigo-500 to-violet-600" },
  Legal:             { avatar: "⚖️", color: "#64748b", gradient: "from-slate-500 to-gray-600" },
  "Product Manager": { avatar: "📦", color: "#14b8a6", gradient: "from-teal-500 to-cyan-600" },
  Investor:          { avatar: "🏦", color: "#a855f7", gradient: "from-purple-500 to-fuchsia-600" },
  System:            { avatar: "🏛️", color: "#475569", gradient: "from-slate-600 to-slate-700" },
};
