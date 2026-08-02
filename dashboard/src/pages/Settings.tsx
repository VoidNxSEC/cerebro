import { motion } from 'framer-motion'
import {
  RefreshCw,
  Moon,
  Sun,
  Database,
  Search,
  Scan,
  Trash2,
  Cpu,
  Loader2,
} from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useDashboardStore } from '@/stores/dashboard'
import { useIntelligenceStats, useScanMutation, useAiHealth, useRagStatus } from '@/hooks/useApi'
import { TIME_RANGES } from '@/types'
import type { IntelligenceStats } from '@/types'

export function Settings() {
  const {
    autoRefresh,
    setAutoRefresh,
    refreshInterval,
    setRefreshInterval,
    theme,
    setTheme,
    timeRange,
    setTimeRange,
  } = useDashboardStore()

  const { data: stats } = useIntelligenceStats()
  const { data: aiHealth } = useAiHealth()
  const { data: ragStatus } = useRagStatus()
  const scanMutation = useScanMutation()
  const ragBadgeVariant: 'default' | 'outline' | 'destructive' =
    !ragStatus ? 'outline' : ragStatus.healthy ? 'default' : 'destructive'
  const ragBadgeLabel = !ragStatus ? 'Loading' : ragStatus.healthy ? 'Healthy' : 'Unavailable'

  const handleFullScan = () => {
    scanMutation.mutate(undefined)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
          <Database className="h-9 w-9 text-primary" />
          System Settings
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Configure and maintain your CEREBRO intelligence environment
        </p>
      </motion.div>

      <div className="grid gap-8">
        {/* Display & Experience */}
        <Card className="glass border-border/50 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5 text-primary" />
              Appearance & Experience
            </CardTitle>
            <CardDescription>
              Configure how you interact with the CEREBRO interface
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-muted/30 border border-border/20">
              <div>
                <p className="font-bold text-sm">Visual Theme</p>
                <p className="text-xs text-muted-foreground italic">
                  Switch between light and high-contrast dark modes
                </p>
              </div>
              <div className="flex items-center gap-1 bg-background/50 p-1 rounded-lg border border-border/30 glass">
                <Button
                  variant={theme === 'light' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setTheme('light')}
                  className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider"
                >
                  <Sun className="h-3.5 w-3.5 mr-2" />
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setTheme('dark')}
                  className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider"
                >
                  <Moon className="h-3.5 w-3.5 mr-2" />
                  Dark
                </Button>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="flex flex-col justify-between p-4 rounded-xl bg-muted/30 border border-border/20">
                <div className="mb-3">
                  <p className="font-bold text-sm">Default Time Range</p>
                  <p className="text-xs text-muted-foreground italic">Filter dashboards by time</p>
                </div>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value as any)}
                  className="w-full rounded-lg border border-border/30 bg-background/50 px-3 py-2 text-xs font-bold outline-none glass"
                >
                  {TIME_RANGES.map((range) => (
                    <option key={range.value} value={range.value}>
                      {range.label.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col justify-between p-4 rounded-xl bg-muted/30 border border-border/20">
                <div className="mb-3">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-sm">Auto Refresh</p>
                    <Switch
                      checked={autoRefresh}
                      onCheckedChange={setAutoRefresh}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground italic">Sync data in the background</p>
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={refreshInterval / 1000}
                    onChange={(e) => setRefreshInterval(Number(e.target.value) * 1000)}
                    disabled={!autoRefresh}
                    className="h-8 glass bg-background/50 font-mono text-xs font-bold"
                    min={5}
                  />
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Seconds</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Intelligence Index */}
        <Card className="glass border-border/50 shadow-lg overflow-hidden relative">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 h-32 w-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Database className="h-5 w-5" />
              Intelligence Index
            </CardTitle>
            <CardDescription>
              Semantic storage and embedding statistics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-xl bg-card/30 p-6 border border-border/30 glass">
              {stats?.indexer_stats ? (
                <IndexerStatsPanel stats={stats} />
              ) : (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary/50" />
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-muted/30 border border-border/20">
              <div className="space-y-1">
                <p className="font-bold text-sm">Maintenance Operations</p>
                <p className="text-xs text-muted-foreground italic">Trigger re-scans or purge the entire semantic base</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleFullScan}
                  disabled={scanMutation.isPending}
                  className="glass hover:bg-primary/10 font-bold text-[10px] tracking-wider h-9"
                  variant="outline"
                >
                  {scanMutation.isPending ? (
                    <RefreshCw className="h-3.5 w-3.5 mr-2 animate-spin" />
                  ) : (
                    <Scan className="h-3.5 w-3.5 mr-2" />
                  )}
                  FULL ECOSYSTEM SCAN
                </Button>
                <Button variant="destructive" size="sm" className="font-bold text-[10px] tracking-wider h-9">
                  <Trash2 className="h-3.5 w-3.5 mr-2" />
                  PURGE INDEX
                </Button>
              </div>
            </div>

            {scanMutation.data && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="rounded-xl bg-primary/5 p-4 border border-primary/20 text-xs"
              >
                <p className="font-black mb-2 uppercase tracking-[0.2em] text-primary/70 text-[10px]">Registry Results</p>
                <div className="grid grid-cols-2 gap-y-2 font-medium">
                  <div className="text-muted-foreground">Projects Identified:</div>
                  <div className="text-right tabular-nums">{scanMutation.data.projects_found}</div>
                  <div className="text-muted-foreground">Intelligence Harvested:</div>
                  <div className="text-right tabular-nums">{scanMutation.data.intelligence_collected}</div>
                  <div className="text-muted-foreground">Semantic Mappings:</div>
                  <div className="text-right tabular-nums">{scanMutation.data.indexed_items}</div>
                  <div className="text-muted-foreground">Dispatch Duration:</div>
                  <div className="text-right tabular-nums">{scanMutation.data.duration_seconds?.toFixed(1)}s</div>
                </div>
              </motion.div>
            )}
          </CardContent>
        </Card>

        {/* System Health */}
        <div className="grid md:grid-cols-2 gap-8">
          <Card className="glass border-border/50 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-primary" />
                Local LLM Health
              </CardTitle>
              <CardDescription>Status of the inference engine (llama.cpp)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border/20">
                <div className="space-y-1">
                  <p className="font-bold text-xs uppercase tracking-widest text-muted-foreground">Endpoint</p>
                  <p className="font-mono text-sm">{aiHealth?.url ?? 'http://localhost:8081'}</p>
                </div>
                <Badge variant={aiHealth?.available ? 'default' : 'destructive'} className="glass py-1">
                  {aiHealth?.available ? 'ONLINE' : 'OFFLINE'}
                </Badge>
              </div>
              {aiHealth?.available && aiHealth.model && (
                <div className="rounded-xl bg-primary/5 p-4 border border-primary/10">
                  <p className="text-[10px] font-bold text-primary/70 uppercase tracking-widest mb-1">Loaded Model</p>
                  <p className="font-mono text-sm font-bold truncate">{aiHealth.model}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="glass border-border/50 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-primary" />
                RAG Persistence
              </CardTitle>
              <CardDescription>Vector store runtime configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-muted/30 border border-border/20">
                <div className="space-y-1">
                  <p className="font-bold text-xs uppercase tracking-widest text-muted-foreground">Backend</p>
                  <p className="font-mono text-sm">{ragStatus?.backend ?? 'loading'}</p>
                </div>
                <Badge variant={ragBadgeVariant} className="glass py-1">
                  {ragBadgeLabel.toUpperCase()}
                </Badge>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-background/50 p-3 border border-border/30 text-center">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Documents</p>
                  <p className="text-lg font-black">{ragStatus?.document_count ?? '—'}</p>
                </div>
                <div className="rounded-xl bg-background/50 p-3 border border-border/30 text-center">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Provider</p>
                  <p className="text-sm font-bold truncate">{ragStatus?.llm_provider ?? '—'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="pt-6 text-center">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground/40">
            CEREBRO Intelligence System v1.0.0 · ~/master
          </p>
        </div>
      </div>
    </div>
  )
}

function IndexerStatsPanel({ stats }: { stats: IntelligenceStats }) {
  const idx = stats.indexer_stats
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatsBadge label="Model" value={String(idx.model ?? '—')} />
        <StatsBadge label="Dimensions" value={String(idx.embedding_dim ?? '—')} />
        <StatsBadge label="Indexed" value={String(idx.indexed_items ?? '—')} />
        <StatsBadge label="Index Size" value={idx.index_size_mb != null ? `${(idx.index_size_mb as number).toFixed(1)} MB` : '—'} />
      </div>

      <div>
        <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 mb-3 ml-1">Composition by Intelligence Type</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.by_type || {}).map(([type, count]) => (
            <Badge key={type} variant={type as any} className="glass py-1 px-3 border-border/30">
              <span className="opacity-70 mr-1">{type.toUpperCase()}:</span> {count}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatsBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">{label}</span>
      <span className="text-sm font-black tracking-tight truncate">{value}</span>
    </div>
  )
}
