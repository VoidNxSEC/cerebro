import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ScanEye, FileSearch2, BarChart2,
  BrainCircuit, CheckCircle2,
  XCircle, Loader2, Clock, Trash2, Activity,
  ChevronDown, ChevronUp, Database, ShieldCheck,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  useScanMutation, useScanMetrics,
  useAiHealth, useProjects, useRagAction, useKnowledgeAction, useOpsHealth
} from '@/hooks/useApi'
import { useAgentStore } from '@/stores/dashboard'
import type { AgentRun } from '@/stores/dashboard'
import { cn, formatRelativeTime } from '@/lib/utils'

// ─── Action definitions ──────────────────────────────────────────────────────

interface ActionDef {
  id: string
  name: string
  description: string
  longDesc: string
  icon: React.ElementType
  category: 'Ecosystem' | 'Knowledge' | 'RAG Runtime' | 'System'
  color: string
  gradient: string
}

const ACTIONS: ActionDef[] = [
  // Ecosystem Dispatchers
  {
    id: 'ecosystem-scan',
    name: 'Ecosystem Scanner',
    description: 'Deep-scan all projects and collect intelligence',
    longDesc: 'Traverses every repository in ~/master, extracts intelligence items (SIGINT, HUMINT, OSINT, TECHINT), updates health scores and project metadata.',
    icon: ScanEye,
    category: 'Ecosystem',
    color: 'text-cyan-500',
    gradient: 'from-cyan-500/20 to-cyan-500/5',
  },
  {
    id: 'metrics-scan',
    name: 'Metrics Collector',
    description: 'Collect code metrics, LOC, git activity for all repos',
    longDesc: 'Zero-token analysis: counts files, lines of code, git commits, contributors, security patterns, test coverage, and CI presence.',
    icon: BarChart2,
    category: 'Ecosystem',
    color: 'text-violet-500',
    gradient: 'from-violet-500/20 to-violet-500/5',
  },
  // Knowledge Base Dispatchers
  {
    id: 'knowledge-analyze',
    name: 'Repo Analyzer',
    description: 'Deep AST analysis of a specific repository',
    longDesc: 'Extracts classes, functions, and metadata using Hermetic Analyzer. Generates artifacts for RAG ingestion.',
    icon: FileSearch2,
    category: 'Knowledge',
    color: 'text-amber-500',
    gradient: 'from-amber-500/20 to-amber-500/5',
  },
  {
    id: 'knowledge-index',
    name: 'Repository Indexer',
    description: 'Index collected intelligence into the vector store',
    longDesc: 'Processes generated artifacts and updates the semantic search index.',
    icon: BrainCircuit,
    category: 'Knowledge',
    color: 'text-blue-500',
    gradient: 'from-blue-500/20 to-blue-500/5',
  },
  // RAG Runtime Dispatchers
  {
    id: 'rag-ingest',
    name: 'RAG Ingestor',
    description: 'Ingest artifacts into the active RAG backend',
    longDesc: 'Loads analyzed code and intelligence into the production retrieval engine.',
    icon: Database,
    category: 'RAG Runtime',
    color: 'text-indigo-500',
    gradient: 'from-indigo-500/20 to-indigo-500/5',
  },
  {
    id: 'rag-smoke',
    name: 'RAG Smoke Tester',
    description: 'Validate retrieval backend health and performance',
    longDesc: 'Runs a write/read/delete cycle to ensure the vector store is fully operational.',
    icon: ShieldCheck,
    category: 'RAG Runtime',
    color: 'text-emerald-500',
    gradient: 'from-emerald-500/20 to-emerald-500/5',
  },
  {
    id: 'ops-health',
    name: 'System Diagnostics',
    description: 'Full system health and credential check',
    longDesc: 'Verifies file system access, LLM availability, and vector store connectivity.',
    icon: Activity,
    category: 'System',
    color: 'text-rose-500',
    gradient: 'from-rose-500/20 to-rose-500/5',
  },
]

// ─── Page ────────────────────────────────────────────────────────────────────

export function ControlPlane() {
  const { data: aiHealth } = useAiHealth()
  const { runs, clearRuns } = useAgentStore()
  const [logOpen, setLogOpen] = useState(false)

  const runningCount = runs.filter((r) => r.status === 'running').length

  const categories = ['Ecosystem', 'Knowledge', 'RAG Runtime', 'System'] as const

  return (
    <div className="space-y-8 pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
            <Zap className="h-9 w-9 text-primary animate-pulse-glow" />
            Control Plane
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Centralized command & control for the CEREBRO ecosystem
          </p>
        </motion.div>
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={aiHealth?.available ? 'default' : 'destructive'} className="gap-1.5 py-1.5 px-3 glass shadow-sm">
            <span className={cn('h-2 w-2 rounded-full', aiHealth?.available ? 'bg-green-400 animate-pulse' : 'bg-red-400')} />
            LLM {aiHealth?.available ? `Online · ${aiHealth.model ?? 'local'}` : 'Offline'}
          </Badge>
          {runningCount > 0 && (
            <Badge variant="secondary" className="gap-1.5 py-1.5 px-3 animate-pulse glass border-primary/20">
              <Activity className="h-3.5 w-3.5 text-primary" />
              {runningCount} ACTIVE
            </Badge>
          )}
        </div>
      </div>

      {/* Action Categories */}
      {categories.map((cat, idx) => (
        <motion.div
          key={cat}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="space-y-4"
        >
          <div className="flex items-center gap-4">
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground/70 pl-1">
              {cat} Dispatchers
            </h2>
            <div className="h-px flex-1 bg-border/50" />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {ACTIONS.filter(a => a.category === cat).map((action) => (
              <ActionCard key={action.id} action={action} />
            ))}
          </div>
        </motion.div>
      ))}

      {/* Activity Log */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="rounded-2xl border bg-card/50 backdrop-blur-xl overflow-hidden glass shadow-xl"
      >
        <button
          onClick={() => setLogOpen((v) => !v)}
          className="flex w-full items-center justify-between px-6 py-5 hover:bg-muted/50 transition-all group"
        >
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-muted p-2 group-hover:bg-primary/10 transition-colors">
              <Activity className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="text-left">
              <span className="font-bold text-sm block">Operation Registry</span>
              <span className="text-xs text-muted-foreground">Historical execution data</span>
            </div>
            {runs.length > 0 && (
              <Badge variant="secondary" className="ml-2 font-mono">{runs.length}</Badge>
            )}
          </div>
          <div className="flex items-center gap-4">
            {runs.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-xs hover:text-red-500 hover:bg-red-500/10"
                onClick={(e) => { e.stopPropagation(); clearRuns() }}
              >
                <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                Purge
              </Button>
            )}
            {logOpen ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
          </div>
        </button>

        <AnimatePresence>
          {logOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-t"
            >
              {runs.length === 0 ? (
                <div className="px-6 py-12 text-center text-sm text-muted-foreground italic">
                  Registry is currently empty. Dispatch an operation to begin tracking.
                </div>
              ) : (
                <div className="divide-y max-h-80 overflow-y-auto">
                  {runs.map((run) => (
                    <ActivityRow key={run.id} run={run} />
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

// ─── ActionCard ───────────────────────────────────────────────────────────────

function ActionCard({ action }: { action: ActionDef }) {
  const { runs, addRun, updateRun } = useAgentStore()
  const { data: projects } = useProjects()

  const scanMutation = useScanMutation()
  const metricsMutation = useScanMetrics()
  const ragMutation = useRagAction()
  const knowledgeMutation = useKnowledgeAction()
  const healthMutation = useOpsHealth()

  const [selectedProject, setSelectedProject] = useState('')

  const latestRun = runs.find((r) => r.agentId === action.id)
  const isRunning = latestRun?.status === 'running'

  const startRun = () => {
    const id = crypto.randomUUID()
    addRun({
      id,
      agentId: action.id,
      agentName: action.name,
      startedAt: new Date().toISOString(),
      status: 'running',
    })
    return id
  }

  const handleRun = () => {
    switch (action.id) {
      case 'ecosystem-scan': {
        const id = startRun()
        scanMutation.mutate(undefined, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `${data?.projects_found ?? 0} projects, ${data?.indexed_items ?? 0} indexed` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'metrics-scan': {
        const id = startRun()
        metricsMutation.mutate(undefined, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `${data?.repo_count ?? 0} repos scanned` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'knowledge-analyze': {
        if (!selectedProject) return
        const id = startRun()
        knowledgeMutation.mutate({ action: 'analyze', params: { repo_path: selectedProject } }, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `Analyzed ${data?.repo}. LoC: ${data?.metrics?.loc}` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'knowledge-index': {
        const id = startRun()
        knowledgeMutation.mutate({ action: 'index' }, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `Indexed ${data?.indexed_items} items` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'rag-ingest': {
        const id = startRun()
        ragMutation.mutate({ action: 'ingest' }, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: data?.detail }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'rag-smoke': {
        const id = startRun()
        ragMutation.mutate({ action: 'smoke' }, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `Backend: ${data?.backend}, Healthy: ${data?.healthy}` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
      case 'ops-health': {
        const id = startRun()
        healthMutation.mutate(undefined, {
          onSuccess: (data) => updateRun(id, { status: 'success', completedAt: new Date().toISOString(), detail: `${data?.results?.length} checks completed` }),
          onError: (e) => updateRun(id, { status: 'error', completedAt: new Date().toISOString(), detail: String(e) }),
        })
        break
      }
    }
  }

  const statusColor = latestRun?.status === 'success'
    ? 'text-green-500' : latestRun?.status === 'error'
    ? 'text-red-500' : latestRun?.status === 'running'
    ? 'text-yellow-500' : 'text-muted-foreground'

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.2 }}
    >
      <Card className={cn(
        'group h-full flex flex-col overflow-hidden border-border/50 transition-all duration-300 glass hover:shadow-2xl hover:border-primary/30',
        isRunning && 'border-primary/50 shadow-primary/20 glow-primary'
      )}>
        {/* Shimmer loading bar when running */}
        {isRunning && <div className="h-1.5 w-full shimmer bg-primary/30" />}
        {!isRunning && <div className={cn('h-1 w-full', action.color.replace('text-', 'bg-'))} />}

        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-2">
            <div className={cn(
              'flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br shadow-md transition-transform group-hover:scale-110 duration-300',
              action.gradient
            )}>
              <action.icon className={cn('h-6 w-6', action.color)} />
            </div>
            <div className="flex items-center gap-1.5">
              {latestRun && (
                <Badge variant="outline" className={cn('flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider glass', statusColor)}>
                  {latestRun.status === 'running' && <Loader2 className="h-3 w-3 animate-spin" />}
                  {latestRun.status === 'success' && <CheckCircle2 className="h-3 w-3" />}
                  {latestRun.status === 'error' && <XCircle className="h-3 w-3" />}
                  {latestRun.status}
                </Badge>
              )}
            </div>
          </div>
          <CardTitle className="text-lg mt-4 font-bold tracking-tight">{action.name}</CardTitle>
          <CardDescription className="text-sm leading-relaxed text-muted-foreground/80">{action.longDesc}</CardDescription>
        </CardHeader>

        <CardContent className="mt-auto pt-2 space-y-4">
          {/* Project selector for repo-specific actions */}
          {action.id === 'knowledge-analyze' && (
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/60 ml-1">Target Repository</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full rounded-lg border border-border/50 bg-background/50 backdrop-blur-sm px-3 py-2 text-xs focus:ring-1 ring-primary/30 outline-none transition-all"
              >
                <option value="">Select a project…</option>
                {projects?.map((p) => (
                  <option key={p.name} value={p.path}>{p.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Last run info */}
          {latestRun?.completedAt && (
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground/70 bg-muted/30 p-2 rounded-lg border border-border/20">
              <Clock className="h-3 w-3 shrink-0" />
              <span className="truncate">
                {formatRelativeTime(latestRun.completedAt)}
                {latestRun.detail && ` · ${latestRun.detail}`}
              </span>
            </div>
          )}

          <Button
            onClick={handleRun}
            disabled={isRunning || (action.id === 'knowledge-analyze' && !selectedProject)}
            size="sm"
            className={cn(
              "w-full h-10 font-bold tracking-wide transition-all duration-300 shadow-sm",
              isRunning ? "bg-primary/20" : "hover:shadow-lg active:scale-[0.98]"
            )}
            variant={isRunning ? "outline" : "default"}
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Executing Operation…
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 mr-2" />
                Dispatch Operation
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}

// ─── ActivityRow ─────────────────────────────────────────────────────────────

function ActivityRow({ run }: { run: AgentRun }) {
  const icon = run.status === 'running'
    ? <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />
    : run.status === 'success'
    ? <CheckCircle2 className="h-4 w-4 text-green-500" />
    : <XCircle className="h-4 w-4 text-red-500" />

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-4 px-6 py-4 text-sm hover:bg-primary/[0.02] transition-colors"
    >
      <div className="shrink-0">{icon}</div>
      <div className="flex flex-col min-w-0">
        <span className="font-bold tracking-tight text-foreground/90">{run.agentName}</span>
        {run.detail && <span className="text-xs text-muted-foreground truncate max-w-md">{run.detail}</span>}
      </div>
      <div className="ml-auto flex flex-col items-end gap-1 shrink-0">
        <span className="text-[10px] font-mono text-muted-foreground/60 uppercase">
          {formatRelativeTime(run.completedAt ?? run.startedAt)}
        </span>
        <Badge variant="outline" className="text-[8px] h-4 py-0 px-1.5 font-bold glass">
          ID: {run.id.slice(0, 8)}
        </Badge>
      </div>
    </motion.div>
  )
}
