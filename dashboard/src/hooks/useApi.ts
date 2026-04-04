import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDashboardStore } from '@/stores/dashboard'
import api from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import type { IntelligenceType, QueryResult, AiHealth, ChatRequest } from '@/types'

// Query keys
export const queryKeys = {
  status: ['status'] as const,
  projects: (params?: object) => ['projects', params] as const,
  project: (name: string) => ['project', name] as const,
  intelligence: (query: string, params?: object) => ['intelligence', query, params] as const,
  intelligenceStats: ['intelligence', 'stats'] as const,
  briefing: (type: string) => ['briefing', type] as const,
  alerts: ['alerts'] as const,
  graph: ['graph'] as const,
  metrics: ['metrics'] as const,
  watcherStatus: ['metrics', 'watcher'] as const,
  aiHealth: ['ai', 'health'] as const,
}

// Status
export function useStatus() {
  const { autoRefresh, refreshInterval } = useDashboardStore()

  return useQuery({
    queryKey: queryKeys.status,
    queryFn: api.getStatus,
    refetchInterval: autoRefresh ? refreshInterval : false,
  })
}

// Projects
export function useProjects(params?: {
  status?: string
  language?: string
  sort_by?: string
  order?: 'asc' | 'desc'
}) {
  return useQuery({
    queryKey: queryKeys.projects(params),
    queryFn: () => api.getProjects(params),
  })
}

export function useProject(name: string) {
  return useQuery({
    queryKey: queryKeys.project(name),
    queryFn: () => api.getProject(name),
    enabled: !!name,
  })
}

// Intelligence
export function useIntelligenceQuery(
  query: string,
  options?: {
    types?: IntelligenceType[]
    projects?: string[]
    limit?: number
    semantic?: boolean
  }
) {
  return useQuery<QueryResult>({
    queryKey: queryKeys.intelligence(query, options),
    queryFn: () =>
      api.queryIntelligence({
        query,
        ...options,
      }),
    enabled: query.length > 0,
  })
}

export function useIntelligenceStats() {
  return useQuery({
    queryKey: queryKeys.intelligenceStats,
    queryFn: api.getIntelligenceStats,
  })
}

// Briefings
export function useDailyBriefing() {
  return useQuery({
    queryKey: queryKeys.briefing('daily'),
    queryFn: api.getDailyBriefing,
  })
}

export function useExecutiveBriefing() {
  return useQuery({
    queryKey: queryKeys.briefing('executive'),
    queryFn: api.getExecutiveBriefing,
  })
}

// Alerts
export function useAlerts() {
  const { autoRefresh, refreshInterval } = useDashboardStore()

  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: api.getAlerts,
    refetchInterval: autoRefresh ? refreshInterval : false,
  })
}

// Graph
export function useDependencyGraph() {
  return useQuery({
    queryKey: queryKeys.graph,
    queryFn: api.getDependencyGraph,
  })
}

// Mutations
export function useScanMutation() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: () => api.triggerScan(),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['status'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['intelligence'] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      toast({ title: 'Scan complete', description: `${data?.projects_found ?? 0} projects found` })
    },
    onError: (err: Error) => {
      toast({ variant: 'destructive', title: 'Scan failed', description: err.message })
    },
  })
}

export function useSummarizeProject() {
  const { toast } = useToast()
  return useMutation({
    mutationFn: (name: string) => api.summarizeProject(name),
    onError: (err: Error) => {
      toast({ variant: 'destructive', title: 'Summary failed', description: err.message })
    },
  })
}

// Metrics
export function useMetrics() {
  const { autoRefresh, refreshInterval } = useDashboardStore()
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: api.getMetrics,
    refetchInterval: autoRefresh ? refreshInterval : false,
  })
}

export function useWatcherStatus() {
  const { autoRefresh, refreshInterval } = useDashboardStore()
  return useQuery({
    queryKey: queryKeys.watcherStatus,
    queryFn: api.getWatcherStatus,
    refetchInterval: autoRefresh ? refreshInterval : false,
  })
}

export function useScanMetrics() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  return useMutation({
    mutationFn: () => api.triggerMetricsScan(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
      toast({ title: 'Metrics collected', description: `${data.repo_count} repos scanned` })
    },
    onError: (err: Error) => {
      toast({ variant: 'destructive', title: 'Metrics scan failed', description: err.message })
    },
  })
}

export function useChatMutation() {
  return useMutation({
    mutationFn: (request: ChatRequest) => api.chat(request),
  })
}

// AI / Local LLM
export function useAiHealth() {
  const { autoRefresh, refreshInterval } = useDashboardStore()
  return useQuery<AiHealth>({
    queryKey: queryKeys.aiHealth,
    queryFn: api.getAiHealth,
    refetchInterval: autoRefresh ? refreshInterval : false,
  })
}
