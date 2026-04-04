import {
  RefreshCw,
  Moon,
  Sun,
  Database,
  Scan,
  Trash2,
  Cpu,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useDashboardStore } from '@/stores/dashboard'
import { useIntelligenceStats, useScanMutation, useAiHealth } from '@/hooks/useApi'
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
  const scanMutation = useScanMutation()

  const handleFullScan = () => {
    scanMutation.mutate(undefined)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your Cerebro Intelligence Dashboard
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Display Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5" />
              Display
            </CardTitle>
            <CardDescription>
              Configure appearance and display preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Theme</p>
                <p className="text-sm text-muted-foreground">
                  Choose light or dark mode
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme('light')}
                >
                  <Sun className="h-4 w-4 mr-2" />
                  Light
                </Button>
                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTheme('dark')}
                >
                  <Moon className="h-4 w-4 mr-2" />
                  Dark
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Default Time Range</p>
                <p className="text-sm text-muted-foreground">
                  Default filter for dashboards
                </p>
              </div>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="rounded-md border bg-background px-3 py-2"
              >
                {TIME_RANGES.map((range) => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Auto Refresh Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5" />
              Auto Refresh
            </CardTitle>
            <CardDescription>
              Configure automatic data refresh
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Enable Auto Refresh</p>
                <p className="text-sm text-muted-foreground">
                  Automatically update data
                </p>
              </div>
              <Button
                variant={autoRefresh ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Enabled' : 'Disabled'}
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Refresh Interval</p>
                <p className="text-sm text-muted-foreground">
                  Time between updates (seconds)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={refreshInterval / 1000}
                  onChange={(e) => setRefreshInterval(Number(e.target.value) * 1000)}
                  className="w-20"
                  min={5}
                  max={300}
                />
                <span className="text-sm text-muted-foreground">sec</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Indexer Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Intelligence Index
            </CardTitle>
            <CardDescription>
              Vector store and embedding statistics
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats?.indexer_stats ? (
              <IndexerStatsPanel stats={stats} />
            ) : (
              <p className="text-muted-foreground">Loading stats...</p>
            )}
          </CardContent>
        </Card>

        {/* Local LLM Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Local LLM
            </CardTitle>
            <CardDescription>
              llama.cpp status (port 8081)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Status</p>
                <p className="text-sm text-muted-foreground font-mono">
                  {aiHealth?.url ?? 'http://localhost:8081'}
                </p>
              </div>
              <Badge variant={aiHealth?.available ? 'default' : 'destructive'}>
                {aiHealth?.available ? 'Online' : 'Offline'}
              </Badge>
            </div>
            {aiHealth?.available && aiHealth.model && (
              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-sm text-muted-foreground">Model</p>
                <p className="font-mono text-sm">{aiHealth.model}</p>
              </div>
            )}
            {!aiHealth?.available && (
              <p className="text-sm text-muted-foreground">
                Start with: <span className="font-mono">llama-server --embeddings --port 8081</span>
              </p>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scan className="h-5 w-5" />
              Actions
            </CardTitle>
            <CardDescription>
              Manage ecosystem scanning and indexing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Full Ecosystem Scan</p>
                <p className="text-sm text-muted-foreground">
                  Re-scan all projects and collect intelligence
                </p>
              </div>
              <Button
                onClick={handleFullScan}
                disabled={scanMutation.isPending}
              >
                {scanMutation.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <Scan className="h-4 w-4 mr-2" />
                    Start Scan
                  </>
                )}
              </Button>
            </div>

            {scanMutation.data && (
              <div className="rounded-lg bg-muted/50 p-3 text-sm">
                <p className="font-medium mb-1">Last Scan Results</p>
                <ul className="space-y-1 text-muted-foreground">
                  <li>Projects found: {scanMutation.data.projects_found}</li>
                  <li>Intelligence collected: {scanMutation.data.intelligence_collected}</li>
                  <li>Items indexed: {scanMutation.data.indexed_items}</li>
                  <li>Duration: {scanMutation.data.duration_seconds?.toFixed(1)}s</li>
                </ul>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-red-500">Clear Index</p>
                <p className="text-sm text-muted-foreground">
                  Remove all indexed intelligence (requires re-scan)
                </p>
              </div>
              <Button variant="destructive" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle>About CEREBRO</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <p>
              <strong>CEREBRO Intelligence System</strong> is the central brain of the ~/master ecosystem.
              It provides unified intelligence gathering, analysis, and dissemination across all your projects.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Version 1.0.0 | Built with React, TypeScript, and FastAPI
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function IndexerStatsPanel({ stats }: { stats: IntelligenceStats }) {
  const idx = stats.indexer_stats
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">Model</p>
          <p className="font-mono text-sm">{idx.model ?? '—'}</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">Dimensions</p>
          <p className="font-semibold">{idx.embedding_dim ?? '—'}</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">Indexed Items</p>
          <p className="font-semibold">{idx.indexed_items ?? '—'}</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-sm text-muted-foreground">Index Size</p>
          <p className="font-semibold">
            {idx.index_size_mb != null ? `${(idx.index_size_mb as number).toFixed(2)} MB` : '—'}
          </p>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium mb-2">Intelligence by Type</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.by_type || {}).map(([type, count]) => (
            <Badge key={type} variant={type as any}>
              {type}: {count}
            </Badge>
          ))}
        </div>
      </div>
    </>
  )
}
