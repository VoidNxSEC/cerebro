import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  Calendar,
  AlertTriangle,
  TrendingUp,
  Download,
  RefreshCw,
  Volume2,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useDailyBriefing, useExecutiveBriefing } from '@/hooks/useApi'
import { formatDate, getHealthColor, cn } from '@/lib/utils'
import api from '@/lib/api'

export function Briefing() {
  const [activeTab, setActiveTab] = useState<'daily' | 'executive'>('daily')
  const [isReading, setIsReading] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const { data: dailyBriefing, isLoading: dailyLoading, refetch: refetchDaily } = useDailyBriefing()
  const { data: executiveBriefing, isLoading: execLoading, refetch: refetchExec } = useExecutiveBriefing()

  const briefing = activeTab === 'daily' ? dailyBriefing : executiveBriefing
  const isLoading = activeTab === 'daily' ? dailyLoading : execLoading

  const handleReadAloud = () => {
    if ('speechSynthesis' in window) {
      if (isReading) {
        window.speechSynthesis.cancel()
        setIsReading(false)
      } else {
        const text = briefing?.summary || briefing?.headline || 'No briefing available'
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.onend = () => setIsReading(false)
        window.speechSynthesis.speak(utterance)
        setIsReading(true)
      }
    }
  }

  const handleRefresh = () => {
    if (activeTab === 'daily') {
      refetchDaily()
    } else {
      refetchExec()
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const result = await api.getBriefingMarkdown(activeTab)
      const blob = new Blob([result.markdown], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cerebro-${activeTab}-briefing-${new Date().toISOString().split('T')[0]}.md`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // silently fail — backend may not support markdown format
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Intelligence Briefing</h1>
          <p className="text-muted-foreground">
            Automated intelligence reports for ~/master ecosystem
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReadAloud}>
            <Volume2 className={cn('h-4 w-4 mr-2', isReading && 'text-green-500')} />
            {isReading ? 'Stop' : 'Read Aloud'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Export
          </Button>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-2">
        <Button
          variant={activeTab === 'daily' ? 'default' : 'outline'}
          onClick={() => setActiveTab('daily')}
        >
          <Calendar className="h-4 w-4 mr-2" />
          Daily Briefing
        </Button>
        <Button
          variant={activeTab === 'executive' ? 'default' : 'outline'}
          onClick={() => setActiveTab('executive')}
        >
          <TrendingUp className="h-4 w-4 mr-2" />
          Executive Summary
        </Button>
      </div>

      {/* Briefing Content */}
      {isLoading ? (
        <Card>
          <CardContent className="p-12 text-center">
            <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-muted-foreground" />
            <p className="text-muted-foreground">Generating briefing...</p>
          </CardContent>
        </Card>
      ) : briefing ? (
        <div className="space-y-6">
          {/* Header Card */}
          <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-6 w-6 text-primary" />
                  <div>
                    <CardTitle className="text-xl">
                      {briefing.headline || `${briefing.type?.toUpperCase()} BRIEFING`}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Generated: {formatDate(briefing.timestamp)}
                    </p>
                  </div>
                </div>
                <Badge variant="outline">{briefing.classification}</Badge>
              </div>
            </CardHeader>
            {briefing.summary && (
              <CardContent>
                <p className="text-lg">{briefing.summary}</p>
              </CardContent>
            )}
          </Card>

          {/* Ecosystem Status */}
          {briefing.ecosystem_status && (
            <Card>
              <CardHeader>
                <CardTitle>Ecosystem Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-lg bg-muted/50 p-4 text-center">
                    <div className="text-3xl font-bold">
                      {briefing.ecosystem_status.total_projects}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Projects</div>
                  </div>
                  <div className="rounded-lg bg-muted/50 p-4 text-center">
                    <div className="text-3xl font-bold">
                      {briefing.ecosystem_status.active_projects}
                    </div>
                    <div className="text-sm text-muted-foreground">Active Projects</div>
                  </div>
                  <div className="rounded-lg bg-muted/50 p-4 text-center">
                    <div className={cn(
                      'text-3xl font-bold',
                      getHealthColor(briefing.ecosystem_status.health_score)
                    )}>
                      {briefing.ecosystem_status.health_score.toFixed(0)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Ecosystem Health</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Key Developments */}
          {briefing.key_developments && briefing.key_developments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Key Developments</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {briefing.key_developments.map((dev, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center gap-4 rounded-lg border p-3"
                    >
                      <Badge variant={dev.threat_level as any}>{dev.type}</Badge>
                      <div className="flex-1">
                        <p className="font-medium">{dev.title}</p>
                        <p className="text-sm text-muted-foreground">{dev.source}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Alerts */}
          {briefing.alerts && briefing.alerts.length > 0 && (
            <Card className="border-red-500/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-500">
                  <AlertTriangle className="h-5 w-5" />
                  Alerts ({briefing.alerts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {briefing.alerts.map((alert, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-red-500/20 bg-red-500/5 p-3"
                    >
                      <p>{alert.message}</p>
                      {alert.project && (
                        <p className="mt-1 text-sm text-muted-foreground">
                          Project: {alert.project}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Project Summaries (Weekly) */}
          {briefing.project_summaries && briefing.project_summaries.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Project Summaries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {briefing.project_summaries.map((proj, i) => (
                    <div key={i} className="rounded-lg border p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">{proj.name}</h4>
                        <div className="flex items-center gap-2">
                          <Badge variant={proj.status as any}>{proj.status}</Badge>
                          <span className={cn('font-bold', getHealthColor(proj.health_score))}>
                            {proj.health_score.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      {proj.insights && proj.insights.length > 0 && (
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {proj.insights.map((insight, j) => (
                            <li key={j}>• {insight}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            No briefing data available
          </CardContent>
        </Card>
      )}
    </div>
  )
}
