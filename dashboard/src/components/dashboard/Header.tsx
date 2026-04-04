import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Menu,
  RefreshCw,
  Bell,
  Search,
  Clock,
  ChevronDown,
  Mic,
  Settings,
  Sun,
  Moon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useDashboardStore, useQueryStore } from '@/stores/dashboard'
import { useAlerts, useScanMutation } from '@/hooks/useApi'
import { TIME_RANGES } from '@/types'
import { cn } from '@/lib/utils'

export function Header() {
  const {
    toggleSidebar,
    timeRange,
    setTimeRange,
    autoRefresh,
    setAutoRefresh,
    theme,
    setTheme,
  } = useDashboardStore()
  const { setQuery } = useQueryStore()
  const { data: alerts } = useAlerts()
  const scanMutation = useScanMutation()

  const [showTimeDropdown, setShowTimeDropdown] = useState(false)
  const [searchValue, setSearchValue] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchValue.trim()) {
      setQuery(searchValue.trim())
      window.location.href = `/intelligence?q=${encodeURIComponent(searchValue.trim())}`
    }
  }

  const handleScan = () => {
    scanMutation.mutate(undefined)
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 sm:h-16 items-center justify-between border-b bg-background/95 px-3 sm:px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="shrink-0"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Search */}
        <form onSubmit={handleSearch} className="relative hidden lg:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search intelligence..."
            className="w-64 xl:w-80 pl-10 pr-10"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2"
            title="Voice search"
          >
            <Mic className="h-4 w-4 text-muted-foreground" />
          </Button>
        </form>

        {/* Mobile Search Button */}
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Search className="h-5 w-5" />
        </Button>
      </div>

      {/* Right Section - Controls */}
      <div className="flex items-center gap-1 sm:gap-2">
        {/* Time Range Picker */}
        <div className="relative hidden sm:block">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => setShowTimeDropdown(!showTimeDropdown)}
          >
            <Clock className="h-4 w-4" />
            {TIME_RANGES.find((t) => t.value === timeRange)?.label || 'Select'}
            <ChevronDown className="h-4 w-4" />
          </Button>

          {showTimeDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute right-0 top-full z-50 mt-1 w-48 rounded-md border bg-popover p-1 shadow-md"
            >
              {TIME_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => {
                    setTimeRange(range.value)
                    setShowTimeDropdown(false)
                  }}
                  className={cn(
                    'flex w-full items-center rounded-sm px-2 py-1.5 text-sm',
                    timeRange === range.value
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  {range.label}
                </button>
              ))}
            </motion.div>
          )}
        </div>

        {/* Auto Refresh Toggle */}
        <Button
          variant={autoRefresh ? 'default' : 'outline'}
          size="sm"
          className="gap-2 hidden md:flex"
          onClick={() => setAutoRefresh(!autoRefresh)}
        >
          <RefreshCw
            className={cn(
              'h-4 w-4',
              autoRefresh && 'animate-spin',
              scanMutation.isPending && 'animate-spin'
            )}
          />
          <span className="hidden lg:inline">
            {autoRefresh ? 'Auto' : 'Manual'}
          </span>
        </Button>

        {/* Scan Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleScan}
          disabled={scanMutation.isPending}
          className="hidden sm:inline-flex"
        >
          <span className="hidden md:inline">
            {scanMutation.isPending ? 'Scanning...' : 'Scan'}
          </span>
          <RefreshCw className={cn('h-4 w-4 md:hidden', scanMutation.isPending && 'animate-spin')} />
        </Button>

        {/* Alerts */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {alerts && alerts.length > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs"
            >
              {alerts.length}
            </Badge>
          )}
        </Button>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="relative overflow-hidden group"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <motion.div
            initial={false}
            animate={{
              rotate: theme === 'dark' ? 0 : 180,
              scale: theme === 'dark' ? 1 : 0,
            }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <Moon className="h-5 w-5" />
          </motion.div>
          <motion.div
            initial={false}
            animate={{
              rotate: theme === 'dark' ? 180 : 0,
              scale: theme === 'dark' ? 0 : 1,
            }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <Sun className="h-5 w-5" />
          </motion.div>
        </Button>

        {/* Settings */}
        <Button variant="ghost" size="icon" asChild>
          <Link to="/settings">
            <Settings className="h-5 w-5" />
          </Link>
        </Button>
      </div>
    </header>
  )
}
