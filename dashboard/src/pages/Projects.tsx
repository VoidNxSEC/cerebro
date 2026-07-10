import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FolderKanban,
  Search,
  Grid,
  List,
  ExternalLink,
  Clock,
  Sparkles,
  Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { useProjects, useProject, useSummarizeProject } from '@/hooks/useApi'
import { getHealthColor, formatRelativeTime, cn } from '@/lib/utils'
import type { Project } from '@/types'

export function Projects() {
  const { projectName } = useParams()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: projects, isLoading } = useProjects()
  const { data: projectDetail } = useProject(projectName || '')

  // Filter projects
  const filteredProjects = projects?.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter
    return matchesSearch && matchesStatus
  })

  if (projectName && projectDetail) {
    return <ProjectDetail project={projectDetail.project} analysis={projectDetail.analysis} />
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-1">
            {projects?.length || 0} autonomous projects in <span className="font-mono text-primary font-bold">~/master</span>
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 glass p-4 rounded-2xl border-border/50 shadow-md">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            className="pl-10 glass bg-background/50 border-border/30"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {['all', 'active', 'maintenance', 'deprecated', 'archived'].map((status) => (
            <Button
              key={status}
              variant={statusFilter === status ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter(status)}
              className={cn(
                "h-9 px-4 text-[10px] font-bold uppercase tracking-widest transition-all",
                statusFilter === status ? "shadow-lg glow-primary" : "glass border-border/30"
              )}
            >
              {status}
            </Button>
          ))}
        </div>

        <div className="flex items-center gap-1 ml-auto border border-border/30 rounded-lg p-1 glass">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="icon"
            className="h-8 w-8"
            onClick={() => setViewMode('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="icon"
            className="h-8 w-8"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Projects Grid/List */}
      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 rounded-2xl shimmer border border-border/30 glass" />
          ))}
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects?.map((project, i) => (
            <ProjectCard key={project.name} project={project} index={i} />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredProjects?.map((project, i) => (
            <ProjectRow key={project.name} project={project} index={i} />
          ))}
        </div>
      )}

      {filteredProjects?.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No projects found matching your criteria
        </div>
      )}
    </div>
  )
}

function ProjectCard({ project, index }: { project: Project; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4, scale: 1.02 }}
    >
      <Card className="hover:border-primary/50 transition-all duration-300 glass group h-full flex flex-col shadow-lg">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
                <FolderKanban className="h-5 w-5" />
              </div>
              <CardTitle className="text-lg font-bold tracking-tight group-hover:text-primary transition-colors">
                {project.name}
              </CardTitle>
            </div>
            <Badge variant={project.status as any} className="glass text-[10px] font-bold uppercase tracking-wider">
              {project.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col">
          <p className="text-sm text-muted-foreground/80 line-clamp-2 mb-4 italic min-h-[40px]">
            {project.description || 'System metadata extraction in progress...'}
          </p>

          <div className="flex flex-wrap gap-1.5 mb-6">
            {project.languages.slice(0, 3).map((lang) => (
              <Badge key={lang} variant="secondary" className="text-[10px] font-mono bg-muted/50">
                {lang}
              </Badge>
            ))}
            {project.languages.length > 3 && (
              <Badge variant="secondary" className="text-[10px] font-mono bg-muted/50">
                +{project.languages.length - 3}
              </Badge>
            )}
          </div>

          <div className="mt-auto space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest flex items-center gap-1.5">
                  <Clock className="h-3 w-3" />
                  Last Updated
                </span>
                <span className="text-xs font-medium">{formatRelativeTime(project.last_commit ?? '')}</span>
              </div>
              <div className="text-right">
                <span className={cn('text-2xl font-black tracking-tighter tabular-nums', getHealthColor(project.health_score))}>
                  {project.health_score.toFixed(0)}%
                </span>
                <Progress
                  value={project.health_score}
                  className="w-20 h-1.5 mt-1 glass"
                  indicatorClassName={cn(
                    'transition-all duration-500',
                    project.health_score >= 70
                      ? 'bg-green-500 glow-success'
                      : project.health_score >= 50
                      ? 'bg-yellow-500 glow-warning'
                      : 'bg-red-500 glow-danger'
                  )}
                />
              </div>
            </div>

            <Button variant="outline" size="sm" className="w-full glass hover:bg-primary/10 group-hover:border-primary/50 transition-all font-bold tracking-wide" asChild>
              <Link to={`/projects/${project.name}`}>
                VIEW DETAILS
                <ExternalLink className="ml-2 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function ProjectRow({ project, index }: { project: Project; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      whileHover={{ x: 4 }}
    >
      <Card className="hover:border-primary/50 transition-all duration-300 glass group shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center gap-6">
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary/20 transition-colors shrink-0">
              <FolderKanban className="h-6 w-6" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-bold tracking-tight text-lg group-hover:text-primary transition-colors truncate">{project.name}</h3>
                <Badge variant={project.status as any} className="glass text-[10px] font-bold uppercase tracking-wider">{project.status}</Badge>
              </div>
              <p className="text-sm text-muted-foreground/80 truncate italic">
                {project.description || 'No description available'}
              </p>
            </div>

            <div className="hidden lg:flex flex-wrap gap-1.5 max-w-[200px] justify-center">
              {project.languages.slice(0, 2).map((lang) => (
                <Badge key={lang} variant="secondary" className="text-[10px] font-mono bg-muted/50">
                  {lang}
                </Badge>
              ))}
            </div>

            <div className="hidden md:flex flex-col items-center gap-1 w-32 shrink-0">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest flex items-center gap-1.5">
                <Clock className="h-3 w-3" />
                Updated
              </span>
              <span className="text-xs font-medium">{formatRelativeTime(project.last_commit ?? '')}</span>
            </div>

            <div className="flex flex-col items-end gap-1 w-28 shrink-0">
              <div className="flex items-center gap-2">
                <span className={cn('font-black text-xl tracking-tighter tabular-nums', getHealthColor(project.health_score))}>
                  {project.health_score.toFixed(0)}%
                </span>
              </div>
              <Progress
                value={project.health_score}
                className="w-full h-1.5 glass"
                indicatorClassName={cn(
                  'transition-all duration-500',
                  project.health_score >= 70
                    ? 'bg-green-500 glow-success'
                    : project.health_score >= 50
                    ? 'bg-yellow-500 glow-warning'
                    : 'bg-red-500 glow-danger'
                )}
              />
            </div>

            <Button variant="ghost" size="icon" className="hover:bg-primary/10 shrink-0" asChild>
              <Link to={`/projects/${project.name}`}>
                <ExternalLink className="h-5 w-5" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function ProjectDetail({ project, analysis }: { project: Project; analysis: any }) {
  const summarizeMutation = useSummarizeProject()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" asChild>
          <Link to="/projects">← Back to Projects</Link>
        </Button>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <FolderKanban className="h-8 w-8" />
            {project.name}
          </h1>
          <p className="text-muted-foreground mt-1">
            {project.description || 'No description available'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={project.status as any} className="text-sm">
            {project.status}
          </Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={() => summarizeMutation.mutate(project.name)}
            disabled={summarizeMutation.isPending}
          >
            {summarizeMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 mr-2" />
            )}
            AI Summary
          </Button>
        </div>
      </div>

      {summarizeMutation.data && (
        <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-primary" />
              AI Summary
              {summarizeMutation.data.source === 'llamacpp' && (
                <Badge variant="secondary" className="ml-auto text-xs">Local LLM</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{summarizeMutation.data.summary}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">Health Score</div>
            <div className={cn('text-3xl font-bold', getHealthColor(project.health_score))}>
              {project.health_score.toFixed(0)}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">Languages</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {project.languages.map((lang) => (
                <Badge key={lang} variant="secondary">{lang}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">Last Commit</div>
            <div className="text-lg font-semibold">
              {formatRelativeTime(project.last_commit ?? '')}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-muted-foreground">Path</div>
            <div className="text-sm font-mono truncate">{project.path}</div>
          </CardContent>
        </Card>
      </div>

      {/* Analysis */}
      {analysis && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analysis.insights?.map((insight: string, i: number) => (
                  <li key={i} className="text-sm">• {insight}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analysis.recommendations?.map((rec: string, i: number) => (
                  <li key={i} className="text-sm">• {rec}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
