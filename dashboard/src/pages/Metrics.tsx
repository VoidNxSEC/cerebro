import { useMemo, useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, BarChart3, ChevronDown, ChevronUp, FileCode, Radio, RefreshCw, Shield } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { useMetrics, useWatcherStatus, useScanMetrics } from '@/hooks/useApi'
import { useWebSocketStore } from '@/stores/dashboard'
import { cn, getHealthColor } from '@/lib/utils'
import type { RepoMetrics } from '@/types'

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export function Metrics() {
  const { data: snapshot, isLoading } = useMetrics()
  const { data: watcher } = useWatcherStatus()
  const scanMutation = useScanMetrics()

  const [sortField, setSortField] = useState('health_score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filterStatus, setFilterStatus] = useState('all')
  const [search, setSearch] = useState('')
  const [flash, setFlash] = useState(false)

  // real-time flash on WebSocket update
  const { lastMessage } = useWebSocketStore()
  useEffect(() => {
    if ((lastMessage as any)?.type === 'repo_update' || (lastMessage as any)?.type === 'metrics_scan_complete') {
      setFlash(true)
      const t = setTimeout(() => setFlash(false), 2500)
      return () => clearTimeout(t)
    }
  }, [lastMessage])

  const repos: RepoMetrics[] = snapshot?.repos ?? []

  // ---------- aggregates ----------
  const stats = useMemo(() => {
    const totalLoc = repos.reduce((s, r) => s + r.total_loc, 0)
    const avgHealth = repos.length ? repos.reduce((s, r) => s + r.health_score, 0) / repos.length : 0
    const active = repos.filter((r) => r.status === 'active').length

    const langMap: Record<string, { files: number; lines: number }> = {}
    repos.forEach((r) => {
      Object.entries(r.languages).forEach(([lang, ls]) => {
        if (!langMap[lang]) langMap[lang] = { files: 0, lines: 0 }
        langMap[lang].files += ls.files
        langMap[lang].lines += ls.lines
      })
    })
    const topLangs = Object.entries(langMap).sort((a, b) => b[1].lines - a[1].lines).slice(0, 8)
    return { totalLoc, avgHealth, active, topLangs }
  }, [repos])

  // ---------- filter + sort ----------
  const filtered = useMemo(() => {
    return repos
      .filter((r) => {
        if (filterStatus !== 'all' && r.status !== filterStatus) return false
        if (search && !r.name.toLowerCase().includes(search.toLowerCase())) return false
        return true
      })
      .sort((a, b) => {
        let va: any = sortField === 'git_commits' ? (a.git?.total_commits ?? 0) : (a as any)[sortField]
        let vb: any = sortField === 'git_commits' ? (b.git?.total_commits ?? 0) : (b as any)[sortField]
        if (typeof va === 'string') va = va.toLowerCase()
        if (typeof vb === 'string') vb = vb.toLowerCase()
        const cmp = va < vb ? -1 : va > vb ? 1 : 0
        return sortDir === 'asc' ? cmp : -cmp
      })
  }, [repos, sortField, sortDir, filterStatus, search])

  const handleSort = (field: string) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('desc') }
  }

  // ---------------------------------------------------------------------------
  // JSX
  // ---------------------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <BarChart3 className="h-8 w-8" /> Metrics
          </h1>
          <p className="text-muted-foreground">Zero-token analysis · {repos.length} repositories</p>
        </div>
        <div className="flex items-center gap-3">
          {/* live badge */}
          <div className={cn('flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium',
            watcher?.running ? 'border-green-500/40 bg-green-500/10 text-green-700' : 'border-muted text-muted-foreground')}>
            <span className={cn('h-2 w-2 rounded-full', watcher?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400')} />
            {watcher?.running ? 'Live' : 'Offline'}
          </div>
          {flash && <Badge variant="secondary" className="animate-pulse">↻ update</Badge>}
          <Button size="sm" onClick={() => scanMutation.mutate()} disabled={scanMutation.isPending}>
            <RefreshCw className={cn('h-4 w-4 mr-2', scanMutation.isPending && 'animate-spin')} />
            Scan All
          </Button>
        </div>
      </div>

      {/* stat cards */}
      <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
        <MiniCard title="Repositories" value={repos.length} icon={FileCode} sub={`${stats.active} active`} />
        <MiniCard title="Total LoC" value={stats.totalLoc.toLocaleString()} icon={Activity} sub="all repos" />
        <MiniCard title="Avg Health" value={`${stats.avgHealth.toFixed(1)}%`} icon={Shield} sub="ecosystem" valCls={getHealthColor(stats.avgHealth)} />
        <MiniCard
          title="Watcher Changes"
          value={watcher?.changes_detected ?? 0}
          icon={Radio}
          sub={watcher?.last_update ? `@ ${new Date(watcher.last_update).toLocaleTimeString()}` : 'none yet'}
        />
      </div>

      {/* language bar chart */}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Language Distribution (LoC)</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {stats.topLangs.map(([lang, ls]) => {
              const max = stats.topLangs[0]?.[1]?.lines || 1
              return (
                <div key={lang} className="flex items-center gap-3">
                  <span className="w-24 text-sm text-right text-muted-foreground">{lang}</span>
                  <div className="flex-1 h-2.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full bg-primary/75 transition-all" style={{ width: `${(ls.lines / max) * 100}%` }} />
                  </div>
                  <span className="w-20 text-xs text-muted-foreground text-right">{ls.lines.toLocaleString()}</span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Input placeholder="Search repos…" className="w-56" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="flex gap-1">
          {['all', 'active', 'maintenance', 'archived'].map((s) => (
            <Button key={s} variant={filterStatus === s ? 'default' : 'outline'} size="sm" onClick={() => setFilterStatus(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* main table */}
      <Card>
        <CardContent className="p-0 overflow-x-auto">
          {isLoading ? (
            <div className="text-center py-14 text-muted-foreground">Loading metrics…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  {COLUMNS.map((c) => (
                    <th key={c.key} className="px-4 py-3 text-left font-semibold text-muted-foreground cursor-pointer hover:text-foreground" onClick={() => handleSort(c.key)}>
                      <div className="flex items-center gap-1">
                        {c.label}
                        {sortField === c.key && (sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((repo, i) => (
                  <RepoRow key={repo.name} repo={repo} idx={i} />
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* watcher card */}
      {watcher && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Radio className={cn('h-4 w-4', watcher.running ? 'text-green-500' : 'text-muted-foreground')} />
              Real-Time Watcher
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div><div className="text-muted-foreground">Status</div><div className={cn('font-semibold', watcher.running ? 'text-green-600' : 'text-red-600')}>{watcher.running ? 'Running' : 'Stopped'}</div></div>
              <div><div className="text-muted-foreground">Tracking</div><div className="font-semibold">{watcher.tracked_repos} repos</div></div>
              <div><div className="text-muted-foreground">Changes</div><div className="font-semibold">{watcher.changes_detected}</div></div>
              <div><div className="text-muted-foreground">Interval</div><div className="font-semibold">{watcher.poll_interval} s</div></div>
            </div>
          </CardContent>
        </Card>
      )}

      {snapshot?.generated_at && (
        <p className="text-xs text-center text-muted-foreground">
          Snapshot · {new Date(snapshot.generated_at).toLocaleString()} · {snapshot.repo_count} repos
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------
const COLUMNS = [
  { key: 'name', label: 'Repository' },
  { key: 'status', label: 'Status' },
  { key: 'health_score', label: 'Health' },
  { key: 'total_loc', label: 'LoC' },
  { key: 'total_files', label: 'Files' },
  { key: 'git_commits', label: 'Commits' },
  { key: 'primary_language', label: 'Lang' },
  { key: 'dep_count', label: 'Deps' },
  { key: 'security_score', label: 'Security' },
]

function RepoRow({ repo, idx }: { repo: RepoMetrics; idx: number }) {
  const hc = getHealthColor(repo.health_score)
  const statusCls =
    repo.status === 'active' ? 'bg-green-500/10 text-green-700 border-green-300' :
    repo.status === 'maintenance' ? 'bg-yellow-500/10 text-yellow-700 border-yellow-300' :
    'bg-muted text-muted-foreground'
  const secCls = repo.security_score >= 70 ? 'text-green-600' : repo.security_score >= 40 ? 'text-yellow-600' : 'text-red-600'

  return (
    <motion.tr
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: idx * 0.018 }}
      className="border-b last:border-0 hover:bg-muted/30 transition-colors"
    >
      <td className="px-4 py-3">
        <div className="font-medium text-primary">{repo.name}</div>
        <div className="text-xs text-muted-foreground truncate max-w-[160px]">{repo.path}</div>
      </td>
      <td className="px-4 py-3"><Badge variant="outline" className={cn('text-xs', statusCls)}>{repo.status}</Badge></td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span className={cn('font-bold', hc)}>{repo.health_score.toFixed(0)}%</span>
          <Progress value={repo.health_score} className="w-16 h-1.5" />
        </div>
      </td>
      <td className="px-4 py-3 text-right text-muted-foreground">{repo.total_loc.toLocaleString()}</td>
      <td className="px-4 py-3 text-right text-muted-foreground">{repo.total_files.toLocaleString()}</td>
      <td className="px-4 py-3 text-right text-muted-foreground">{repo.git?.total_commits?.toLocaleString() ?? '—'}</td>
      <td className="px-4 py-3">{repo.primary_language && <Badge variant="secondary" className="text-xs">{repo.primary_language}</Badge>}</td>
      <td className="px-4 py-3 text-right text-muted-foreground">{repo.dep_count}</td>
      <td className="px-4 py-3"><span className={cn('font-semibold', secCls)}>{repo.security_score.toFixed(0)}%</span></td>
    </motion.tr>
  )
}

function MiniCard({ title, value, icon: Icon, sub, valCls }: { title: string; value: string | number; icon: React.ElementType; sub: string; valCls?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-muted-foreground uppercase tracking-wide">{title}</div>
            <div className={cn('text-2xl font-bold mt-1', valCls)}>{value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{sub}</div>
          </div>
          <div className="p-2 rounded-lg bg-muted"><Icon className="h-5 w-5 text-primary" /></div>
        </div>
      </CardContent>
    </Card>
  )
}
