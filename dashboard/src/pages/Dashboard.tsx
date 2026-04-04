import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity,
  FolderKanban,
  Brain,
  AlertTriangle,
  TrendingUp,
  Search,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { useStatus, useProjects, useAlerts, useDailyBriefing } from '@/hooks/useApi'
import { getHealthColor, formatRelativeTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus()
  const { data: projects, isLoading: projectsLoading } = useProjects({ sort_by: 'health_score', order: 'asc' })
  const { data: alerts } = useAlerts()
  const { data: briefing } = useDailyBriefing()

  const topProjects = projects?.slice(0, 5) || []
  const recentAlerts = alerts?.slice(0, 5) || []

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
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
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

      {/* Main Content Grid */}
      <div className="grid gap-4 lg:gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Projects Needing Attention */}
        <Card className="border-0 shadow-md hover:shadow-lg transition-shadow duration-300">
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
                <div className="text-center text-muted-foreground">Loading...</div>
              ) : topProjects.length === 0 ? (
                <div className="text-center text-muted-foreground">
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
                    className="group relative flex items-center justify-between rounded-lg border border-border/50 bg-card/50 backdrop-blur-sm p-4 hover:border-primary/30 hover:bg-card/80 transition-all duration-200 cursor-pointer"
                  >
                    {/* Left accent bar */}
                    <div
                      className={cn(
                        'absolute left-0 top-0 bottom-0 w-1 rounded-l-lg transition-all duration-300',
                        project.health_score >= 70
                          ? 'bg-green-500 group-hover:w-1.5'
                          : project.health_score >= 50
                          ? 'bg-yellow-500 group-hover:w-1.5'
                          : 'bg-red-500 group-hover:w-1.5'
                      )}
                    />

                    <div className="flex-1 ml-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground group-hover:text-primary transition-colors">
                          {project.name}
                        </span>
                        <Badge variant={project.status as any} className="shadow-sm">
                          {project.status}
                        </Badge>
                      </div>
                      <div className="mt-1.5 flex items-center gap-4 text-xs text-muted-foreground">
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
                            'text-2xl font-bold tabular-nums tracking-tight',
                            getHealthColor(project.health_score)
                          )}
                        >
                          {project.health_score.toFixed(0)}
                        </div>
                        <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
                          Health
                        </div>
                      </div>
                      <div className="w-24">
                        <Progress
                          value={project.health_score}
                          className="h-2"
                          indicatorClassName={cn(
                            'transition-all duration-300',
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
        <Card className="border-0 shadow-md hover:shadow-lg transition-shadow duration-300">
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
            <Badge variant="outline" className="shadow-sm">
              {alerts?.length || 0} total
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentAlerts.length === 0 ? (
                <div className="text-center text-muted-foreground py-4">
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
                    className="group relative flex items-start gap-3 rounded-lg border border-red-500/20 bg-gradient-to-r from-red-500/10 via-red-500/5 to-transparent p-4 hover:border-red-500/30 transition-all duration-200"
                  >
                    {/* Pulse indicator */}
                    <div className="absolute -left-1 top-1/2 -translate-y-1/2 h-2 w-2 rounded-full bg-red-500 animate-pulse" />

                    <div className="rounded-lg bg-red-500/10 p-2 group-hover:bg-red-500/20 transition-colors">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-red-500" />
                    </div>
                    <div className="flex-1 text-sm">
                      <p className="font-medium text-foreground">{alert.message}</p>
                      {alert.project && (
                        <p className="mt-1.5 text-xs text-muted-foreground flex items-center gap-1">
                          <span className="text-red-500">•</span>
                          Project: <span className="font-medium">{alert.project}</span>
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
        <Card className="lg:col-span-2 border-0 shadow-md hover:shadow-lg transition-shadow duration-300">
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
            <Button variant="outline" size="sm" asChild className="hover:bg-primary/10">
              <Link to="/briefing">Full Briefing</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {briefing ? (
              <div className="space-y-4">
                <div className="rounded-lg bg-muted/50 p-4">
                  <p className="text-sm">{briefing.summary}</p>
                </div>

                {briefing.key_developments && briefing.key_developments.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium">Key Developments</h4>
                    <div className="grid gap-2 md:grid-cols-2">
                      {briefing.key_developments.slice(0, 4).map((dev, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 rounded border p-2 text-sm"
                        >
                          <Badge variant={dev.threat_level as any} className="shrink-0">
                            {dev.type}
                          </Badge>
                          <span className="truncate">{dev.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                Loading briefing...
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
        <Card className="border-0 shadow-md hover:shadow-lg transition-shadow duration-300">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Quick Actions
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Common tasks and navigation shortcuts
            </p>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button variant="outline" asChild className="w-full h-auto py-4 hover:bg-primary/5 hover:border-primary/30 transition-all group">
                  <Link to="/intelligence" className="flex flex-col items-center gap-2">
                    <Search className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-semibold">Search Intelligence</span>
                    <span className="text-xs text-muted-foreground">Query knowledge base</span>
                  </Link>
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button variant="outline" asChild className="w-full h-auto py-4 hover:bg-primary/5 hover:border-primary/30 transition-all group">
                  <Link to="/briefing" className="flex flex-col items-center gap-2">
                    <TrendingUp className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-semibold">Executive Summary</span>
                    <span className="text-xs text-muted-foreground">View insights</span>
                  </Link>
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button variant="outline" asChild className="w-full h-auto py-4 hover:bg-primary/5 hover:border-primary/30 transition-all group">
                  <Link to="/projects" className="flex flex-col items-center gap-2">
                    <FolderKanban className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-semibold">Browse Projects</span>
                    <span className="text-xs text-muted-foreground">Explore ecosystem</span>
                  </Link>
                </Button>
              </motion.div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
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
      <Card className="relative overflow-hidden border-0 shadow-md hover:shadow-xl transition-shadow duration-300">
        {/* Gradient background accent */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />

        <CardContent className="p-6 relative">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                {title}
              </p>
              <p className={cn('text-4xl font-bold tracking-tight', valueClassName)}>
                {loading ? (
                  <span className="inline-block animate-pulse">...</span>
                ) : value}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            </div>
            <motion.div
              className="rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 p-4"
              whileHover={{ rotate: 5, scale: 1.1 }}
              transition={{ duration: 0.2 }}
            >
              <Icon className="h-7 w-7 text-primary" />
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
