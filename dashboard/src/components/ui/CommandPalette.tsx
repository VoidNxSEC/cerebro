import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, FolderKanban, BarChart3, Search,
  FileText, Bot, MessageSquare, Settings, ScanEye,
  Newspaper, Command, X,
} from 'lucide-react'
import { useDashboardStore } from '@/stores/dashboard'
import { useScanMutation, useScanMetrics } from '@/hooks/useApi'
import { cn } from '@/lib/utils'

interface PaletteCommand {
  id: string
  label: string
  description?: string
  icon: React.ElementType
  action: () => void
  group: string
}

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useDashboardStore()
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const scanMutation = useScanMutation()
  const metricsMutation = useScanMetrics()

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('')
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [commandPaletteOpen])

  const close = () => setCommandPaletteOpen(false)

  const run = (action: () => void) => {
    action()
    close()
  }

  const commands: PaletteCommand[] = [
    { id: 'nav-dashboard', label: 'Dashboard', description: 'Go to Dashboard', icon: LayoutDashboard, action: () => navigate('/'), group: 'Navigate' },
    { id: 'nav-projects', label: 'Projects', description: 'Browse all projects', icon: FolderKanban, action: () => navigate('/projects'), group: 'Navigate' },
    { id: 'nav-metrics', label: 'Metrics', description: 'View code metrics', icon: BarChart3, action: () => navigate('/metrics'), group: 'Navigate' },
    { id: 'nav-intel', label: 'Intelligence Search', description: 'Semantic search', icon: Search, action: () => navigate('/intelligence'), group: 'Navigate' },
    { id: 'nav-briefing', label: 'Briefing', description: 'Daily & executive summaries', icon: FileText, action: () => navigate('/briefing'), group: 'Navigate' },
    { id: 'nav-agents', label: 'Agents', description: 'AI agent launcher', icon: Bot, action: () => navigate('/agents'), group: 'Navigate' },
    { id: 'nav-chat', label: 'AI Chat', description: 'Chat with CEREBRO', icon: MessageSquare, action: () => navigate('/chat'), group: 'Navigate' },
    { id: 'nav-settings', label: 'Settings', description: 'Dashboard settings', icon: Settings, action: () => navigate('/settings'), group: 'Navigate' },
    { id: 'agent-scan', label: 'Run Ecosystem Scan', description: 'Scan all projects', icon: ScanEye, action: () => scanMutation.mutate(undefined), group: 'Agents' },
    { id: 'agent-metrics', label: 'Collect Metrics', description: 'Re-scan all repo metrics', icon: BarChart3, action: () => metricsMutation.mutate(), group: 'Agents' },
    { id: 'agent-briefing', label: 'Open Daily Briefing', description: 'View today\'s briefing', icon: Newspaper, action: () => navigate('/briefing'), group: 'Agents' },
  ]

  const filtered = query
    ? commands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.description?.toLowerCase().includes(query.toLowerCase()) ||
          c.group.toLowerCase().includes(query.toLowerCase())
      )
    : commands

  const groups = [...new Set(filtered.map((c) => c.group))]

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[100] bg-background/60 backdrop-blur-sm"
            onClick={close}
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="fixed left-1/2 top-[20vh] z-[101] w-full max-w-lg -translate-x-1/2"
          >
            <div className="rounded-xl border bg-card shadow-2xl overflow-hidden">
              {/* Search input */}
              <div className="flex items-center gap-3 border-b px-4 py-3">
                <Command className="h-4 w-4 text-muted-foreground shrink-0" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Type a command or search…"
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') close()
                    if (e.key === 'Enter' && filtered.length > 0) {
                      run(filtered[0].action)
                    }
                  }}
                />
                <button onClick={close} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Results */}
              <div className="max-h-80 overflow-y-auto p-2">
                {filtered.length === 0 ? (
                  <p className="py-6 text-center text-sm text-muted-foreground">No results for "{query}"</p>
                ) : (
                  groups.map((group) => (
                    <div key={group} className="mb-2">
                      <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                        {group}
                      </div>
                      {filtered
                        .filter((c) => c.group === group)
                        .map((cmd) => (
                          <button
                            key={cmd.id}
                            onClick={() => run(cmd.action)}
                            className={cn(
                              'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                              'hover:bg-muted text-left'
                            )}
                          >
                            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted">
                              <cmd.icon className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <div className="min-w-0">
                              <div className="font-medium truncate">{cmd.label}</div>
                              {cmd.description && (
                                <div className="text-xs text-muted-foreground truncate">{cmd.description}</div>
                              )}
                            </div>
                          </button>
                        ))}
                    </div>
                  ))
                )}
              </div>

              <div className="border-t px-4 py-2 text-xs text-muted-foreground flex gap-4">
                <span><kbd className="font-mono">↵</kbd> select</span>
                <span><kbd className="font-mono">Esc</kbd> close</span>
                <span><kbd className="font-mono">⌘K</kbd> toggle</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
