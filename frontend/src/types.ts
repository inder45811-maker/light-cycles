/* ⏣ Light Cycles — Shared Types */

export interface Battle {
  id: string
  title: string
  description: string
  status: 'waiting' | 'coding' | 'judging' | 'complete' | 'error'
  winner: string | null
  agents: AgentSubmission[]
  scores: ScoreEntry[]
  created_at: number
  completed_at: number | null
}

export interface AgentSubmission {
  name: string
  model: string
  status: string
  code?: string
  error?: string | null
  score: AgentScore | null
}

export interface AgentScore {
  score: number
  tests_passed: number
  tests_total: number
  duration_ms: number
  errors: string[]
}

export interface ScoreEntry {
  agent: string
  score: number
  passed: number
  total: number
  duration_ms: number
}

export interface Tournament {
  id: string
  title: string
  description: string
  problem_statement: string
  entry_fee_display: string
  prize_pool_display: string
  platform_fee_display: string
  player_cap: number
  player_count: number
  paid_count: number
  status: string
  winner_name: string | null
  current_round: number
  total_rounds: number
  round_name: string
  players: PlayerEntry[]
  matches: MatchEntry[]
  scheduled_at: number | null
  created_at: number
}

export interface PlayerEntry {
  id: string
  name: string
  paid: boolean
  eliminated: boolean
  seed: number
}

export interface MatchEntry {
  id: string
  round: number
  round_name: string
  player1: string
  player2: string
  status: string
  winner: string | null
  battle_id: string | null
}

export interface Debate {
  id: string
  topic: string
  position_for: string
  position_against: string
  rounds: DebateRound[]
  status: string
  winner: string | null
  final_scores: Record<string, number>
  created_at: number
}

export interface DebateRound {
  round: number
  speaker: string
  content: string
  judge_score: number | null
  judge_feedback: string
}

export interface LeaderboardEntry {
  name: string
  battles: number
  wins: number
  total_score: number
  avg_score: number
}

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  text: string
}

export type View = 'dashboard' | 'battles' | 'leaderboard' | 'create' | 'tournaments' | 'create-tournament' | 'debates' | 'pits'
