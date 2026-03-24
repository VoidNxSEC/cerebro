/**
 * API Client for Cerebro Backend
 * Connects to Cerebro API (FastAPI) on localhost:8000
 */

import type {
    EcosystemStatus,
    Project,
    IntelligenceItem,
    IntelligenceStats,
    Briefing,
    Alert,
    DependencyGraph,
    IntelligenceType,
    MetricsSnapshot,
    RepoMetrics,
    WatcherStatus,
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

    async getProject(name: string): Promise<Project> {
        return this.fetch<Project>(`/projects/${encodeURIComponent(name)}`)
    }

    // Intelligence
    async queryIntelligence(params: {
        query: string
        types?: IntelligenceType[]
        projects?: string[]
        limit?: number
        semantic?: boolean
    }): Promise<IntelligenceItem[]> {
        const result = await this.fetch<{ results: IntelligenceItem[] }>('/intelligence/query', {
            method: 'POST',
            body: JSON.stringify(params),
        })
        return result.results
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

    async summarizeProject(projectName: string): Promise<{ summary: string }> {
        return this.fetch(`/actions/summarize/${encodeURIComponent(projectName)}`, {
            method: 'POST',
        })
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
}

const api = new ApiClient()
export default api
