import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  LayoutDashboard,
  FolderKanban,
  BarChart3,
  Search,
  FileText,
  Settings,
  MessageSquare,
  Bot,
  PanelLeftClose,
  PanelLeftOpen,
  Shield,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStatus } from '@/hooks/useApi'
import { useDashboardStore } from '@/stores/dashboard'

const navGroups = [
  {
    label: 'Overview',
    items: [
      { title: 'Dashboard', href: '/', icon: LayoutDashboard },
      { title: 'Projects', href: '/projects', icon: FolderKanban },
      { title: 'Metrics', href: '/metrics', icon: BarChart3 },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { title: 'Search', href: '/intelligence', icon: Search },
      { title: 'Briefing', href: '/briefing', icon: FileText },
    ],
  },
  {
    label: 'AI',
    items: [
      { title: 'Agents', href: '/agents', icon: Bot },
      { title: 'Chat', href: '/chat', icon: MessageSquare },
    ],
  },
  {
    label: 'System',
    items: [
      { title: 'Settings', href: '/settings', icon: Settings },
    ],
  },
]

interface SidebarProps {
  collapsed: boolean
}

export function Sidebar({ collapsed }: SidebarProps) {
  const { data: status } = useStatus()
  const { cycleSidebar, sidebarMode } = useDashboardStore()

  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className={cn(
        'flex h-16 items-center border-b shrink-0',
        collapsed ? 'justify-center px-0' : 'gap-3 px-5'
      )}>
        <motion.button
          onClick={cycleSidebar}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-3 focus:outline-none"
        >
          <motion.div
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          >
            <Brain className="h-7 w-7 shrink-0 text-cerebro-primary" />
          </motion.div>
          <AnimatePresence initial={false}>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.15 }}
                className="overflow-hidden"
              >
                <div className="whitespace-nowrap">
                  <div className="text-lg font-bold tracking-tight leading-none">CEREBRO</div>
                  <div className="text-[10px] text-muted-foreground tracking-wider uppercase">Intelligence System</div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>

      {/* Status strip */}
      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.15 }}
            className="border-b overflow-hidden"
          >
            <div className="p-4">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-muted-foreground">System</span>
                <div className="flex items-center gap-1.5">
                  <span className={cn(
                    'h-1.5 w-1.5 rounded-full',
                    status ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  )} />
                  <span className={cn('font-medium', status ? 'text-green-500' : 'text-red-500')}>
                    {status ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
              {status && (
                <div className="grid grid-cols-2 gap-1.5 text-xs">
                  <div className="rounded-md bg-muted/50 p-2">
                    <div className="text-muted-foreground">Projects</div>
                    <div className="font-bold text-base">{status.total_projects}</div>
                  </div>
                  <div className="rounded-md bg-muted/50 p-2">
                    <div className="text-muted-foreground">Health</div>
                    <div className={cn(
                      'font-bold text-base',
                      status.health_score >= 70 ? 'text-green-500'
                      : status.health_score >= 50 ? 'text-yellow-500'
                      : 'text-red-500'
                    )}>
                      {status.health_score.toFixed(0)}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-2">
            <AnimatePresence initial={false}>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.1 }}
                  className="px-2 mb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60"
                >
                  {group.label}
                </motion.div>
              )}
            </AnimatePresence>
            {group.items.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                end={item.href === '/'}
                title={collapsed ? item.title : undefined}
                className={({ isActive }) =>
                  cn(
                    'flex items-center rounded-lg text-sm font-medium transition-all duration-150 group relative',
                    collapsed ? 'justify-center h-10 w-10 mx-auto' : 'gap-3 px-3 py-2',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <item.icon className={cn('shrink-0', collapsed ? 'h-5 w-5' : 'h-4 w-4')} />
                    <AnimatePresence initial={false}>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          transition={{ duration: 0.15 }}
                          className="overflow-hidden whitespace-nowrap"
                        >
                          {item.title}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {isActive && collapsed && (
                      <span className="absolute right-0.5 top-1 h-1.5 w-1.5 rounded-full bg-primary-foreground" />
                    )}
                    {collapsed && (
                      <span className="pointer-events-none absolute left-full ml-3 hidden whitespace-nowrap rounded-md bg-popover px-2 py-1 text-xs font-medium shadow-md group-hover:block z-50 border">
                        {item.title}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className={cn('border-t py-3', collapsed ? 'px-2' : 'px-4')}>
        {!collapsed && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
            <Shield className="h-3.5 w-3.5" />
            <span>Classification: INTERNAL</span>
          </div>
        )}
        <button
          onClick={cycleSidebar}
          className={cn(
            'flex items-center gap-2 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors',
            collapsed ? 'justify-center h-10 w-10 mx-auto' : 'w-full px-3 py-2'
          )}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarMode === 'collapsed' ? (
            <PanelLeftOpen className="h-4 w-4 shrink-0" />
          ) : (
            <PanelLeftClose className="h-4 w-4 shrink-0" />
          )}
          {!collapsed && <span>Collapse</span>}
        </button>
        {!collapsed && (
          <div className="mt-2 flex items-center gap-1.5 px-1 text-[10px] text-muted-foreground/50">
            <Zap className="h-3 w-3" />
            <span>v1.0.0 · ~/master</span>
          </div>
        )}
      </div>
    </div>
  )
}
