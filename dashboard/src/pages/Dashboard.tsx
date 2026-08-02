import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity,
  FolderKanban,
  Brain,
  AlertTriangle,
  TrendingUp,
  Search,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { useStatus, useProjects, useAlerts, useDailyBriefing, useRagStatus } from '@/hooks/useApi'
import { getHealthColor, formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus()
  const { data: projects, isLoading: projectsLoading } = useProjects({ sort_by: 'health_score', order: 'asc' })
  const { data: alerts } = useAlerts()
  const { data: briefing } = useDailyBriefing()
  const { data: ragStatus } = useRagStatus()

  const topProjects = projects?.slice(0, 5) || []
  const recentAlerts = alerts?.slice(0, 5) || []
  const ragBadgeVariant: 'default' | 'outline' | 'destructive' =
    !ragStatus ? 'outline' : ragStatus.healthy ? 'default' : 'destructive'
  const ragBadgeLabel = !ragStatus ? 'Loading' : ragStatus.healthy ? 'Healthy' : 'Unavailable'

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-1"
      >
        <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
          Dashboard
        </h1>
        <p className="text-muted-foreground text-lg">
          Central intelligence overview for{' '}
          <span className="font-mono text-primary">~/master</span> ecosystem
        </p>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Projects"
          value={status?.total_projects || 0}
          icon={FolderKanban}
          description={`${status?.active_projects || 0} active`}
          loading={statusLoading}
        />
        <StatCard
          title="Intelligence Items"
          value={status?.total_intelligence || 0}
          icon={Brain}
          description="Indexed artifacts"
          loading={statusLoading}
        />
        <StatCard
          title="Ecosystem Health"
          value={`${status?.health_score?.toFixed(0) || 0}%`}
          icon={Activity}
          description="Overall score"
          loading={statusLoading}
          valueClassName={getHealthColor(status?.health_score || 0)}
        />
        <StatCard
          title="Active Alerts"
          value={status?.alerts_count || 0}
          icon={AlertTriangle}
          description="Requires attention"
          loading={statusLoading}
          valueClassName={
            (status?.alerts_count || 0) > 0 ? 'text-red-500' : 'text-green-500'
          }
        />
      </div>

      <Card className="border-border/50 shadow-lg glass overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 relative">
          {/* Subtle glow background */}
          <div className="absolute top-0 right-0 -mt-10 -mr-10 h-32 w-32 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="space-y-1">
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              RAG Runtime
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Production retrieval backend configured for the new provider layer
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={ragBadgeVariant} className="glass">
              {ragBadgeLabel}
            </Badge>
            <Button variant="outline" size="sm" asChild className="hover:bg-primary/10 glass">
              <Link to="/settings">Details</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <RuntimeMetric
              label="Backend"
              value={ragStatus?.backend ?? 'loading'}
            />
            <RuntimeMetric
              label="Mode"
              value={ragStatus?.mode ?? 'loading'}
            />
            <RuntimeMetric
              label="Documents"
              value={ragStatus?.document_count != null ? String(ragStatus.document_count) : '—'}
            />
            <RuntimeMetric
              label="Namespace"
              value={ragStatus?.namespace ?? 'default'}
            />
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground/80">LLM:</span>
            <Badge variant="outline" className="glass">{ragStatus?.llm_provider ?? 'loading'}</Badge>
            {ragStatus?.collection_name && (
              <>
                <span className="font-medium text-foreground/80 ml-2">Collection:</span>
                <span className="font-mono bg-muted/50 px-1.5 py-0.5 rounded">{ragStatus.collection_name}</span>
              </>
            )}
            {ragStatus?.error && (
              <span className="text-red-500 ml-auto flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                {ragStatus.error}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Projects Needing Attention */}
        <Card className="border-border/50 shadow-lg glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div className="space-y-1">
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <FolderKanban className="h-5 w-5 text-primary" />
                Projects Needing Attention
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Focus areas requiring your review
              </p>
            </div>
            <Button variant="ghost" size="sm" asChild className="hover:bg-primary/10">
              <Link to="/projects">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {projectsLoading ? (
                <div className="text-center text-muted-foreground py-8 shimmer rounded-lg">Loading...</div>
              ) : topProjects.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  All projects are healthy!
                </div>
              ) : (
                topProjects.map((project, index) => (
                  <motion.div
                    key={project.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ x: 4, scale: 1.01 }}
                    className="group relative flex items-center justify-between rounded-xl border border-border/50 bg-card/30 backdrop-blur-sm p-4 hover:border-primary/30 hover:bg-card/50 transition-all duration-300 cursor-pointer"
                  >
                    {/* Left accent bar */}
                    <div
                      className={cn(
                        'absolute left-0 top-0 bottom-0 w-1 rounded-l-xl transition-all duration-300',
                        project.health_score >= 70
                          ? 'bg-green-500 group-hover:w-1.5 glow-success'
                          : project.health_score >= 50
                          ? 'bg-yellow-500 group-hover:w-1.5 glow-warning'
                          : 'bg-red-500 group-hover:w-1.5 glow-danger'
                      )}
                    />

                    <div className="flex-1 ml-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-foreground group-hover:text-primary transition-colors">
                          {project.name}
                        </span>
                        <Badge variant={project.status as any} className="shadow-sm glass text-[10px] uppercase font-bold tracking-wider">
                          {project.status}
                        </Badge>
                      </div>
                      <div className="mt-1.5 flex items-center gap-4 text-xs text-muted-foreground font-medium">
                        <span className="flex items-center gap-1">
                          {project.languages.slice(0, 2).join(', ')}
                        </span>
                        <span className="flex items-center gap-1">
                          {formatRelativeTime(project.last_commit ?? '')}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div
                          className={cn(
                            'text-2xl font-black tabular-nums tracking-tighter',
                            getHealthColor(project.health_score)
                          )}
                        >
                          {project.health_score.toFixed(0)}
                        </div>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">
                          Health
                        </div>
                      </div>
                      <div className="w-24">
                        <Progress
                          value={project.health_score}
                          className="h-2 glass"
                          indicatorClassName={cn(
                            'transition-all duration-500',
                            project.health_score >= 70
                              ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                              : project.health_score >= 50
                              ? 'bg-gradient-to-r from-yellow-500 to-amber-500'
                              : 'bg-gradient-to-r from-red-500 to-rose-500'
                          )}
                        />
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card className="border-border/50 shadow-lg glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div className="space-y-1">
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                Recent Alerts
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                System notifications and warnings
              </p>
            </div>
            <Badge variant="outline" className="shadow-sm glass">
              {alerts?.length || 0} total
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentAlerts.length === 0 ? (
                <div className="text-center text-muted-foreground py-8 italic">
                  No alerts - system is healthy
                </div>
              ) : (
                recentAlerts.map((alert, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: 10, scale: 0.95 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    transition={{ delay: i * 0.05, type: "spring", stiffness: 200 }}
                    whileHover={{ scale: 1.02, x: 4 }}
                    className="group relative flex items-start gap-4 rounded-xl border border-red-500/20 bg-gradient-to-r from-red-500/10 via-red-500/5 to-transparent p-4 hover:border-red-500/40 transition-all duration-300"
                  >
                    <div className="rounded-lg bg-red-500/10 p-2 group-hover:bg-red-500/20 transition-colors shadow-inner">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-red-500" />
                    </div>
                    <div className="flex-1 text-sm">
                      <p className="font-bold text-foreground leading-tight">{alert.message}</p>
                      {alert.project && (
                        <p className="mt-2 text-[10px] text-muted-foreground flex items-center gap-1 uppercase tracking-widest font-bold">
                          <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
                          Project: <span className="text-foreground">{alert.project}</span>
                        </p>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Daily Briefing Summary */}
        <Card className="lg:col-span-2 border-border/50 shadow-lg glass">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div className="space-y-1">
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Daily Briefing
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Today's key insights and developments
              </p>
            </div>
            <Button variant="outline" size="sm" asChild className="hover:bg-primary/10 glass">
              <Link to="/briefing">Full Briefing</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {briefing ? (
              <div className="space-y-4">
                <div className="rounded-xl bg-card/50 p-6 border border-border/30 shadow-inner">
                  <p className="text-sm leading-relaxed text-foreground/90">{briefing.summary}</p>
                </div>

                {briefing.key_developments && briefing.key_developments.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-xs font-bold uppercase tracking-widest text-muted-foreground/70">Key Developments</h4>
                    <div className="grid gap-3 md:grid-cols-2">
                      {briefing.key_developments.slice(0, 4).map((dev, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-3 rounded-lg border border-border/50 bg-background/40 p-3 text-sm hover:border-primary/20 transition-all cursor-default"
                        >
                          <Badge variant={dev.threat_level as any} className="shrink-0 glass text-[10px] h-5">
                            {dev.type}
                          </Badge>
                          <span className="truncate font-medium">{dev.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-12 shimmer rounded-xl">
                Synthesizing briefing data...
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border-border/50 shadow-xl glass overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Rapid Access
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Direct dispatchers and system navigation
            </p>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <QuickActionLink
                to="/intelligence"
                icon={Search}
                title="Search Intel"
                description="Query knowledge base"
              />
              <QuickActionLink
                to="/control-plane"
                icon={Zap}
                title="Control Plane"
                description="Dispatch operations"
              />
              <QuickActionLink
                to="/projects"
                icon={FolderKanban}
                title="Browse Projects"
                description="Explore ecosystem"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

function QuickActionLink({ to, icon: Icon, title, description }: { to: string, icon: any, title: string, description: string }) {
  return (
    <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
      <Button variant="outline" asChild className="w-full h-auto py-5 glass hover:bg-primary/5 hover:border-primary/30 transition-all group border-border/50 shadow-sm">
        <Link to={to} className="flex flex-col items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2 group-hover:bg-primary/20 transition-colors">
            <Icon className="h-6 w-6 text-primary group-hover:scale-110 transition-transform duration-300" />
          </div>
          <div className="text-center">
            <span className="font-bold block text-sm">{title}</span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">{description}</span>
          </div>
        </Link>
      </Button>
    </motion.div>
  )
}

function RuntimeMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 p-4 shadow-inner">
      <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">{label}</p>
      <p className="mt-1 font-mono text-sm font-bold truncate">{value}</p>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  description: string
  loading?: boolean
  valueClassName?: string
}

function StatCard({
  title,
  value,
  icon: Icon,
  description,
  loading,
  valueClassName,
}: StatCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="relative overflow-hidden border-border/50 shadow-lg glass hover:shadow-2xl transition-all duration-300">
        <CardContent className="p-6 relative">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-[10px] font-black text-muted-foreground/70 uppercase tracking-[0.2em]">
                {title}
              </p>
              <p className={cn('text-4xl font-black tracking-tighter tabular-nums', valueClassName)}>
                {loading ? (
                  <span className="inline-block animate-pulse">...</span>
                ) : value}
              </p>
              <p className="text-[10px] text-muted-foreground mt-1 font-medium">{description}</p>
            </div>
            <motion.div
              className="rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 p-4 shadow-inner border border-primary/10"
              whileHover={{ rotate: 5, scale: 1.1 }}
              transition={{ duration: 0.2 }}
            >
              <Icon className="h-8 w-8 text-primary glow-primary rounded-full" />
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
