import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot, ScanEye, FileSearch2, Newspaper, BarChart2,
  BrainCircuit, MessageSquareDiff, CheckCircle2,
  XCircle, Loader2, Clock, Trash2, Activity,
  ChevronDown, ChevronUp,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  useScanMutation, useScanMetrics,
  useAiHealth, useProjects,
} from '@/hooks/useApi'
import { useAgentStore } from '@/stores/dashboard'
import type { AgentRun } from '@/stores/dashboard'
import { cn, formatRelativeTime } from '@/lib/utils'

// ─── Agent definitions ───────────────────────────────────────────────────────

interface AgentDef {
  id: string
  name: string
  description: string
  longDesc: string
  icon: React.ElementType
  color: string
  gradient: string
}

const AGENTS: AgentDef[] = [
  {
    id: 'ecosystem-scan',
    name: 'Ecosystem Scanner',
    description: 'Deep-scan all projects and collect intelligence',
    longDesc: 'Traverses every repository in ~/master, extracts intelligence items (SIGINT, HUMINT, OSINT, TECHINT), updates health scores and project metadata.',
    icon: ScanEye,
    color: 'text-cyan-500',
    gradient: 'from-cyan-500/20 to-cyan-500/5',
  },
  {
    id: 'metrics-scan',
    name: 'Metrics Collector',
    description: 'Collect code metrics, LOC, git activity for all repos',
    longDesc: 'Zero-token analysis: counts files, lines of code, git commits, contributors, security patterns, test coverage, and CI presence.',
    icon: BarChart2,
    color: 'text-violet-500',
    gradient: 'from-violet-500/20 to-violet-500/5',
  },
  {
    id: 'project-summarizer',
    name: 'Project Summarizer',
    description: 'Generate AI summaries for individual projects',
    longDesc: 'Uses the local LLM to synthesize project intelligence into concise technical summaries with health insights and recommendations.',
    icon: FileSearch2,
    color: 'text-amber-500',
    gradient: 'from-amber-500/20 to-amber-500/5',
  },
  {
    id: 'daily-briefing',
    name: 'Briefing Generator',
    description: 'Generate daily and executive intelligence briefings',
    longDesc: 'Synthesizes ecosystem activity into structured reports: key developments, active alerts, health trends, and recommended actions.',
    icon: Newspaper,
    color: 'text-green-500',
    gradient: 'from-green-500/20 to-green-500/5',
  },
  {
    id: 'rag-query',
    name: 'Knowledge Query',
    description: 'Semantic search across the indexed knowledge base',
    longDesc: 'Embeds your query using local sentence-transformers (Jina code-aware, 8192 ctx), retrieves semantically similar intelligence items.',
    icon: BrainCircuit,
    color: 'text-blue-500',
    gradient: 'from-blue-500/20 to-blue-500/5',
  },
  {
    id: 'ai-chat',
    name: 'AI Assistant',
    description: 'Multi-turn conversation with RAG context',
    longDesc: 'Connects to the local LLM (llama.cpp) with automatic RAG context injection from your knowledge base. Full conversation history.',
    icon: MessageSquareDiff,
    color: 'text-primary',
    gradient: 'from-primary/20 to-primary/5',
  },
]

// ─── Page ────────────────────────────────────────────────────────────────────

export function Agents() {
  const { data: aiHealth } = useAiHealth()
  const { runs, clearRuns } = useAgentStore()
  const [logOpen, setLogOpen] = useState(false)

  const runningCount = runs.filter((r) => r.status === 'running').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Bot className="h-8 w-8 text-primary" />
            AI Agents
          </h1>
          <p className="text-muted-foreground mt-1">
            Autonomous operations for your ecosystem — dispatch, monitor, iterate
          </p>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <Badge variant={aiHealth?.available ? 'default' : 'destructive'} className="gap-1.5">
            <span className={cn('h-1.5 w-1.5 rounded-full', aiHealth?.available ? 'bg-green-300 animate-pulse' : 'bg-red-300')} />
            LLM {aiHealth?.available ? `Online · ${aiHealth.model ?? 'local'}` : 'Offline'}
          </Badge>
          {runningCount > 0 && (
            <Badge variant="secondary" className="gap-1.5 animate-pulse">
              <Activity className="h-3 w-3" />
              {runningCount} running
            </Badge>
          )}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {AGENTS.map((agent, i) => (
          <AgentCard key={agent.id} agent={agent} index={i} />
        ))}
      </div>

      {/* Activity Log */}
      <div className="rounded-xl border bg-card overflow-hidden">
        <button
          onClick={() => setLogOpen((v) => !v)}
          className="flex w-full items-center justify-between px-5 py-4 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-sm">Activity Log</span>
            {runs.length > 0 && (
              <Badge variant="secondary" className="text-xs">{runs.length}</Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {runs.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={(e) => { e.stopPropagation(); clearRuns() }}
              >
                <Trash2 className="h-3 w-3 mr-1" />
                Clear
              </Button>
            )}
            {logOpen ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </div>
        </button>

        <AnimatePresence>
          {logOpen && (
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: 'auto' }}
              exit={{ height: 0 }}
              className="overflow-hidden border-t"
            >
              {runs.length === 0 ? (
                <div className="px-5 py-8 text-center text-sm text-muted-foreground">
                  No activity yet — dispatch an agent to get started
                </div>
              ) : (
                <div className="divide-y max-h-64 overflow-y-auto">
                  {runs.map((run) => (
                    <ActivityRow key={run.id} run={run} />
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ─── AgentCard ───────────────────────────────────────────────────────────────

function AgentCard({ agent, index }: { agent: AgentDef; index: number }) {
  const navigate = useNavigate()
  const { runs, addRun, updateRun } = useAgentStore()
  const { data: projects } = useProjects()

  const scanMutation = useScanMutation()
  const metricsMutation = useScanMetrics()

  const [selectedProject, setSelectedProject] = useState('')

  const latestRun = runs.find((r) => r.agentId === agent.id)
  const isRunning = latestRun?.status === 'running'

  const startRun = () => {
    const id = crypto.randomUUID()
    addRun({
      id,
      agentId: agent.id,
      agentName: agent.name,
      startedAt: new Date().toISOString(),
      status: 'running',
    })
    return id
  }

  const handleRun = () => {
    switch (agent.id) {
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
      case 'daily-briefing':
        navigate('/briefing')
        break
      case 'project-summarizer':
        navigate(selectedProject ? `/projects/${selectedProject}` : '/projects')
        break
      case 'rag-query':
        navigate('/intelligence')
        break
      case 'ai-chat':
        navigate('/chat')
        break
    }
  }

  const statusColor = latestRun?.status === 'success'
    ? 'text-green-500' : latestRun?.status === 'error'
    ? 'text-red-500' : latestRun?.status === 'running'
    ? 'text-yellow-500' : 'text-muted-foreground'

  const isLaunchOnly = ['daily-briefing', 'project-summarizer', 'rag-query', 'ai-chat'].includes(agent.id)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, type: 'spring', stiffness: 200 }}
    >
      <Card className={cn(
        'group h-full flex flex-col overflow-hidden border transition-all duration-300 hover:shadow-lg',
        isRunning && 'border-primary/40 shadow-[0_0_0_1px_hsl(var(--primary)/0.15)]'
      )}>
        {/* Color bar */}
        <div className={cn(
          'h-1 w-full transition-all duration-500',
          isRunning ? 'animate-pulse bg-gradient-to-r from-primary to-primary/60' : `bg-gradient-to-r ${agent.gradient.replace('/20', '/40').replace('/5', '/10')}`
        )} />

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className={cn(
              'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm',
              agent.gradient
            )}>
              <agent.icon className={cn('h-5 w-5', agent.color)} />
            </div>
            <div className="flex items-center gap-1.5">
              {latestRun && (
                <div className={cn('flex items-center gap-1 text-xs font-medium', statusColor)}>
                  {latestRun.status === 'running' && <Loader2 className="h-3 w-3 animate-spin" />}
                  {latestRun.status === 'success' && <CheckCircle2 className="h-3 w-3" />}
                  {latestRun.status === 'error' && <XCircle className="h-3 w-3" />}
                  {latestRun.status === 'running' ? 'Running' : latestRun.status === 'success' ? 'Done' : 'Error'}
                </div>
              )}
            </div>
          </div>
          <CardTitle className="text-base mt-2">{agent.name}</CardTitle>
          <CardDescription className="text-xs leading-relaxed">{agent.longDesc}</CardDescription>
        </CardHeader>

        <CardContent className="mt-auto pt-0 space-y-3">
          {/* Project selector for summarizer */}
          {agent.id === 'project-summarizer' && (
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full rounded-md border bg-background px-2 py-1.5 text-xs"
            >
              <option value="">All projects…</option>
              {projects?.map((p) => (
                <option key={p.name} value={p.name}>{p.name}</option>
              ))}
            </select>
          )}

          {/* Last run info */}
          {latestRun?.completedAt && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(latestRun.completedAt)}</span>
              {latestRun.detail && <span className="truncate">· {latestRun.detail}</span>}
            </div>
          )}

          <Button
            onClick={handleRun}
            disabled={isRunning}
            size="sm"
            className="w-full"
            variant={isLaunchOnly ? 'outline' : 'default'}
          >
            {isRunning ? (
              <>
                <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                Running…
              </>
            ) : isLaunchOnly ? (
              <>
                <agent.icon className="h-3.5 w-3.5 mr-2" />
                Open
              </>
            ) : (
              <>
                <agent.icon className="h-3.5 w-3.5 mr-2" />
                Run
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
    <div className="flex items-center gap-3 px-5 py-3 text-sm hover:bg-muted/30 transition-colors">
      {icon}
      <span className="font-medium">{run.agentName}</span>
      {run.detail && <span className="text-muted-foreground truncate">· {run.detail}</span>}
      <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
        {formatRelativeTime(run.completedAt ?? run.startedAt)}
      </span>
    </div>
  )
}
