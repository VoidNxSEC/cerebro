import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { CommandPalette } from '@/components/ui/CommandPalette'
import { useDashboardStore } from '@/stores/dashboard'

interface LayoutProps {
  children: React.ReactNode
}

const SIDEBAR_WIDTHS = { expanded: 272, collapsed: 64, hidden: 0 }

export function Layout({ children }: LayoutProps) {
  const { sidebarMode, theme, setCommandPaletteOpen } = useDashboardStore()

  // Apply theme
  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(theme)
  }, [theme])

  // Global Cmd+K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [setCommandPaletteOpen])

  const w = SIDEBAR_WIDTHS[sidebarMode]

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Overlay */}
      <AnimatePresence>
        {sidebarMode !== 'hidden' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={() => useDashboardStore.getState().setSidebarMode('hidden')}
          />
        )}
      </AnimatePresence>

      {/* Sidebar — always mounted, width animated */}
      <motion.aside
        animate={{ width: w }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="fixed inset-y-0 left-0 z-50 overflow-hidden border-r bg-card shadow-xl lg:shadow-none"
        style={{ width: w }}
      >
        <Sidebar collapsed={sidebarMode === 'collapsed'} />
      </motion.aside>

      {/* Main Content — margin tracks sidebar width */}
      <motion.div
        animate={{ marginLeft: w }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="flex min-h-screen flex-col"
      >
        <Header />
        <main className="flex-1 p-4 md:p-6">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {children}
          </motion.div>
        </main>
      </motion.div>

      {/* Global Command Palette */}
      <CommandPalette />
    </div>
  )
}
