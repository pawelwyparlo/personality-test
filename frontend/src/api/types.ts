export type Form = 'full' | 'quick'
export type Sex = 'male' | 'female'
export type RunStatus = 'in_progress' | 'completed' | 'abandoned'

export interface Item {
  id: number
  text: string
  domain: string
}

export interface FormItems {
  form: Form
  count: number
  items: Item[]
}

export interface ProfileCreated {
  id: string
}

export interface TestRunCreated {
  id: string
  item_count: number
}

export interface AnswerCreate {
  item_id: number
  value: number
}

export interface FacetScore {
  domain?: string
  number: number
  name: string
  raw: number
  t_score: number
  percentile: number
  level: string
}

export interface DomainScore {
  domain: string
  name: string
  raw: number
  t_score: number
  percentile: number
  level: string
  facets: FacetScore[]
}

export interface ScoreResult {
  run_id: string
  age: number
  sex: string
  domains: DomainScore[]
  facets: FacetScore[]
}

export interface TestRunStatus {
  id: string
  status: RunStatus
  form: Form
  item_count: number
  answered_count: number
  scores: ScoreResult | null
}

export interface Narrative {
  pull_quote: string
  paragraphs: string[]
  strengths: string[]
  watch_outs: string[]
  source: 'llm' | 'textbank'
}

export interface Report {
  run_id: string
  form: Form
  completed_at: string
  domains: DomainScore[]
  facets: FacetScore[]
  narrative: Narrative
}

// --- Coach ----------------------------------------------------------------- //

export type CoachRole = 'user' | 'coach'

export interface CoachMessage {
  id: string
  role: CoachRole
  content: string
  created_at: string
}

export interface TraitContext {
  run_id: string
  /** Domain percentiles keyed by letter (O/C/E/A/N). */
  percentiles: Record<string, number>
}

export interface Coach {
  id: string
  name: string
  messages: CoachMessage[]
  trait_context: TraitContext
}

export interface CoachCreated {
  id: string
  name: string
}
