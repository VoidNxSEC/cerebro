/**
 * API Client for Cerebro Backend
 * Connects to Cerebro API (FastAPI) on localhost:8009
 * Local LLM (llama.cpp) on localhost:8081 — checked via /ai/health
 */

import type {
    EcosystemStatus,
    Project,
    IntelligenceStats,
    QueryResult,
    Briefing,
    Alert,
    DependencyGraph,
    IntelligenceType,
    MetricsSnapshot,
    RepoMetrics,
    WatcherStatus,
    AiHealth,
    RagRuntimeStatus,
    RagBackendCapabilities,
    ChatRequest,
    ChatResponse,
} from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

class ApiClient {
    private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
            ...options,
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`)
        }

        return response.json()
    }

    // Status & Health
    async getStatus(): Promise<EcosystemStatus> {
        return this.fetch<EcosystemStatus>('/status')
    }

    async getHealth(): Promise<{ status: string; timestamp: string }> {
        return this.fetch('/health')
    }

    // Projects
    async getProjects(params?: {
        status?: string
        language?: string
        sort_by?: string
        order?: 'asc' | 'desc'
    }): Promise<Project[]> {
        const query = new URLSearchParams(params as any).toString()
        return this.fetch<Project[]>(`/projects${query ? `?${query}` : ''}`)
    }

    async getProject(name: string): Promise<{ project: Project; analysis: any }> {
        return this.fetch<{ project: Project; analysis: any }>(`/projects/${encodeURIComponent(name)}`)
    }

    async summarizeProject(projectName: string): Promise<{ summary: string; source: string }> {
        return this.fetch(`/actions/summarize/${encodeURIComponent(projectName)}`, {
            method: 'POST',
        })
    }

    // Intelligence
    async queryIntelligence(params: {
        query: string
        types?: IntelligenceType[]
        projects?: string[]
        limit?: number
        semantic?: boolean
    }): Promise<QueryResult> {
        return this.fetch<QueryResult>('/intelligence/query', {
            method: 'POST',
            body: JSON.stringify(params),
        })
    }

    async getIntelligenceStats(): Promise<IntelligenceStats> {
        return this.fetch<IntelligenceStats>('/intelligence/stats')
    }

    // Briefings
    async getDailyBriefing(): Promise<Briefing> {
        return this.fetch<Briefing>('/briefing/daily')
    }

    async getExecutiveBriefing(): Promise<Briefing> {
        return this.fetch<Briefing>('/briefing/executive')
    }

    // Alerts
    async getAlerts(): Promise<Alert[]> {
        return this.fetch<Alert[]>('/alerts')
    }

    // Dependency Graph
    async getDependencyGraph(): Promise<DependencyGraph> {
        return this.fetch<DependencyGraph>('/graph/dependencies')
    }

    // Actions
    async triggerScan(fullScan: boolean = false): Promise<any> {
        return this.fetch('/actions/scan', {
            method: 'POST',
            body: JSON.stringify({ full_scan: fullScan, collect_intelligence: true }),
        })
    }

    // Control Plane Actions
    async ragAction(action: string, params: Record<string, any> = {}): Promise<any> {
        return this.fetch(`/actions/rag/${action}`, {
            method: 'POST',
            body: JSON.stringify({ action, params }),
        })
    }

    async knowledgeAction(action: string, params: Record<string, any> = {}): Promise<any> {
        return this.fetch(`/actions/knowledge/${action}`, {
            method: 'POST',
            body: JSON.stringify({ action, params }),
        })
    }

    async opsHealth(): Promise<any> {
        return this.fetch('/actions/ops/health', { method: 'POST' })
    }

    // Metrics
    async getMetrics(): Promise<MetricsSnapshot> {
        return this.fetch<MetricsSnapshot>('/metrics')
    }

    async getRepoMetrics(name: string): Promise<RepoMetrics> {
        return this.fetch<RepoMetrics>(`/metrics/${encodeURIComponent(name)}`)
    }

    async triggerMetricsScan(): Promise<{ status: string; repo_count: number }> {
        return this.fetch('/metrics/scan', { method: 'POST' })
    }

    async getWatcherStatus(): Promise<WatcherStatus> {
        return this.fetch<WatcherStatus>('/metrics/watcher')
    }

    // AI / Local LLM
    async getAiHealth(): Promise<AiHealth> {
        return this.fetch<AiHealth>('/ai/health')
    }

    async getRagStatus(): Promise<RagRuntimeStatus> {
        return this.fetch<RagRuntimeStatus>('/rag/status')
    }

    async getRagBackends(): Promise<RagBackendCapabilities[]> {
        return this.fetch<RagBackendCapabilities[]>('/rag/backends')
    }

    async chat(request: ChatRequest): Promise<ChatResponse> {
        return this.fetch<ChatResponse>('/chat', {
            method: 'POST',
            body: JSON.stringify(request),
        })
    }

    async getBriefingMarkdown(type: string): Promise<{ markdown: string }> {
        return this.fetch('/briefing', {
            method: 'POST',
            body: JSON.stringify({ type, format: 'markdown' }),
        })
    }
}

const api = new ApiClient()
export default api
