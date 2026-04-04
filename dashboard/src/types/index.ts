// Intelligence Types
export type IntelligenceType = 'sigint' | 'humint' | 'osint' | 'techint'
export type ThreatLevel = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type ProjectStatus = 'active' | 'maintenance' | 'deprecated' | 'archived' | 'unknown'

export interface Project {
  name: string
  path: string
  description: string
  languages: string[]
  status: ProjectStatus
  health_score: number
  last_commit: string | null
  last_indexed: string | null
  metadata: Record<string, unknown>
}

export interface ProjectAnalysis {
  project: string
  timestamp: string
  health_score: number
  status: ProjectStatus
  insights: string[]
  recommendations: string[]
  metrics: {
    health_factors: Record<string, number>
  }
}

export interface IntelligenceItem {
  id: string
  type: IntelligenceType
  source: string
  title: string
  content: string
  threat_level: ThreatLevel
  timestamp: string
  tags: string[]
  related_projects: string[]
  score?: number
}

export interface EcosystemStatus {
  total_projects: number
  active_projects: number
  health_score: number
  total_intelligence: number
  alerts_count: number
  last_scan: string | null
}

export interface Alert {
  type: string
  project?: string
  message: string
  score?: number
  id?: string
  title?: string
}

export interface Briefing {
  type: string
  classification: string
  timestamp: string
  summary?: string
  headline?: string
  ecosystem_status?: {
    total_projects: number
    active_projects: number
    health_score: number
  }
  key_developments?: Array<{
    type: string
    title: string
    source: string
    threat_level: ThreatLevel
  }>
  alerts?: Alert[]
  project_summaries?: Array<{
    name: string
    health_score: number
    status: ProjectStatus
    insights: string[]
  }>
}

export interface IntelligenceStats {
  total: number
  by_type: Record<string, number>
  by_threat_level: Record<string, number>
  indexer_stats: Record<string, unknown>
}

export interface QueryResult {
  query: string
  results: IntelligenceItem[]
  total: number
  search_type: 'semantic' | 'keyword'
}

export interface DependencyGraph {
  nodes: Array<{ id: string; label: string }>
  edges: Array<{ source: string; target: string }>
}

// Metrics Types
export interface LanguageStats {
  files: number
  lines: number
}

export interface GitMetrics {
  total_commits: number
  commits_30d: number
  commits_90d: number
  contributors: number
  branches: number
  tags: number
  last_commit_hash?: string
  last_commit_author?: string
  last_commit_date?: string
  last_commit_message?: string
  top_contributors?: Array<{ name: string; commits: number }>
  error?: string
}

export interface RepoMetrics {
  name: string
  path: string
  collected_at: string
  total_files: number
  total_loc: number
  languages: Record<string, LanguageStats>
  primary_language: string
  git: GitMetrics
  dependencies: string[]
  dep_count: number
  security_findings: Array<{ type: string; file: string; line: number }>
  security_score: number
  has_tests: boolean
  test_files: number
  has_ci: boolean
  has_readme: boolean
  has_docs: boolean
  has_flake: boolean
  health_score: number
  status: string
}

export interface MetricsSnapshot {
  generated_at: string
  repo_count: number
  repos: RepoMetrics[]
}

export interface WatcherStatus {
  running: boolean
  tracked_repos: number
  last_update: string | null
  changes_detected: number
  poll_interval: number
}

export interface AiHealth {
  available: boolean
  url: string | null
  model: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  messages: ChatMessage[]
  project?: string
  use_rag?: boolean
  max_context_items?: number
}

export interface ChatResponse {
  message: ChatMessage
  sources: Array<{
    title: string
    type: string
    source: string
    score?: number
  }>
  model: string | null
  rag_used: boolean
}

// Store Types
export interface DashboardState {
  timeRange: TimeRange
  environment: string
  selectedServices: string[]
  autoRefresh: boolean
  refreshInterval: number
  setTimeRange: (range: TimeRange) => void
  setEnvironment: (env: string) => void
  setSelectedServices: (services: string[]) => void
  setAutoRefresh: (enabled: boolean) => void
  setRefreshInterval: (interval: number) => void
}

export type TimeRange = '1h' | '6h' | '24h' | '7d' | '30d' | 'custom'

export interface TimeRangeValue {
  label: string
  value: TimeRange
  hours: number
}

export const TIME_RANGES: TimeRangeValue[] = [
  { label: 'Last Hour', value: '1h', hours: 1 },
  { label: 'Last 6 Hours', value: '6h', hours: 6 },
  { label: 'Last 24 Hours', value: '24h', hours: 24 },
  { label: 'Last 7 Days', value: '7d', hours: 168 },
  { label: 'Last 30 Days', value: '30d', hours: 720 },
]

export const ENVIRONMENTS = ['production', 'staging', 'development', 'all']

export const INTEL_TYPE_CONFIG: Record<IntelligenceType, { label: string; color: string; icon: string }> = {
  sigint: { label: 'Signals', color: 'intel-sigint', icon: 'radio' },
  humint: { label: 'Human', color: 'intel-humint', icon: 'users' },
  osint: { label: 'Open Source', color: 'intel-osint', icon: 'globe' },
  techint: { label: 'Technical', color: 'intel-techint', icon: 'code' },
}

export const THREAT_LEVEL_CONFIG: Record<ThreatLevel, { label: string; color: string }> = {
  critical: { label: 'Critical', color: 'threat-critical' },
  high: { label: 'High', color: 'threat-high' },
  medium: { label: 'Medium', color: 'threat-medium' },
  low: { label: 'Low', color: 'threat-low' },
  info: { label: 'Info', color: 'threat-info' },
}
