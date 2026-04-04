import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search,
  Radio,
  Users,
  Globe,
  Code,
  Filter,
  Sparkles,
  Mic,
  StopCircle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useIntelligenceQuery, useIntelligenceStats } from '@/hooks/useApi'
import { getThreatColor, getIntelTypeColor, formatRelativeTime, cn } from '@/lib/utils'
import type { IntelligenceType, IntelligenceItem } from '@/types'

const INTEL_TYPES = [
  { value: 'sigint', label: 'Signals', icon: Radio, color: 'text-amber-500' },
  { value: 'humint', label: 'Human', icon: Users, color: 'text-green-500' },
  { value: 'osint', label: 'Open Source', icon: Globe, color: 'text-blue-500' },
  { value: 'techint', label: 'Technical', icon: Code, color: 'text-violet-500' },
]

export function Intelligence() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''

  const [query, setQuery] = useState(initialQuery)
  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [selectedTypes, setSelectedTypes] = useState<IntelligenceType[]>([])
  const [isListening, setIsListening] = useState(false)

  const { data: results, isLoading } = useIntelligenceQuery(searchQuery, {
    types: selectedTypes.length > 0 ? selectedTypes : undefined,
    semantic: true,
    limit: 50,
  })

  const { data: stats } = useIntelligenceStats()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchQuery(query)
    setSearchParams(query ? { q: query } : {})
  }

  const toggleType = (type: IntelligenceType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  // Voice recognition via Web Speech API
  const toggleVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    if (isListening) {
      setIsListening(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      setQuery(transcript)
      setSearchQuery(transcript)
      setSearchParams({ q: transcript })
      setIsListening(false)
    }

    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)

    recognition.start()
    setIsListening(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
          Intelligence
        </h1>
        <p className="text-muted-foreground text-lg">
          Search and explore intelligence from{' '}
          <span className="font-mono text-primary">~/master</span> ecosystem
        </p>
      </motion.div>

      {/* Stats */}
      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {INTEL_TYPES.map((type, index) => (
          <motion.div
            key={type.value}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ y: -4, scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card
              className={cn(
                'cursor-pointer border-0 shadow-md hover:shadow-xl transition-all duration-300 relative overflow-hidden',
                selectedTypes.includes(type.value as IntelligenceType)
                  ? 'ring-2 ring-primary ring-offset-2 bg-primary/5'
                  : 'hover:border-primary/30'
              )}
              onClick={() => toggleType(type.value as IntelligenceType)}
            >
              {/* Gradient background */}
              <div className={cn(
                'absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300',
                type.value === 'sigint' && 'bg-gradient-to-br from-amber-500/10 to-transparent',
                type.value === 'humint' && 'bg-gradient-to-br from-green-500/10 to-transparent',
                type.value === 'osint' && 'bg-gradient-to-br from-blue-500/10 to-transparent',
                type.value === 'techint' && 'bg-gradient-to-br from-violet-500/10 to-transparent'
              )} />

              <CardContent className="p-5 relative">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'p-2.5 rounded-xl bg-gradient-to-br shadow-sm',
                      type.value === 'sigint' && 'from-amber-500/20 to-amber-500/10',
                      type.value === 'humint' && 'from-green-500/20 to-green-500/10',
                      type.value === 'osint' && 'from-blue-500/20 to-blue-500/10',
                      type.value === 'techint' && 'from-violet-500/20 to-violet-500/10'
                    )}>
                      <type.icon className={cn('h-5 w-5', type.color)} />
                    </div>
                    <div>
                      <span className="font-semibold text-foreground">{type.label}</span>
                      <div className="text-xs text-muted-foreground uppercase tracking-wider mt-0.5">
                        {type.value}
                      </div>
                    </div>
                  </div>
                  <Badge
                    variant={selectedTypes.includes(type.value as IntelligenceType) ? 'default' : 'secondary'}
                    className="text-base font-bold px-3 py-1 shadow-sm"
                  >
                    {stats?.by_type?.[type.value] || 0}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden">
          {/* Gradient top border */}
          <div className="h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500" />

          <CardContent className="p-4 sm:p-6">
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              <div className="relative flex-1">
                <motion.div
                  className="absolute left-3 top-1/2 -translate-y-1/2"
                  animate={{ rotate: query ? 0 : 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                >
                  <Search className="h-5 w-5 text-muted-foreground" />
                </motion.div>
                <Input
                  placeholder="Search intelligence... (e.g., 'How does authentication work?')"
                  className="pl-12 pr-12 h-14 text-lg border-2 focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 hover:bg-primary/10"
                  onClick={toggleVoice}
                >
                  {isListening ? (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      <StopCircle className="h-5 w-5 text-red-500" />
                    </motion.div>
                  ) : (
                    <Mic className="h-5 w-5 text-muted-foreground" />
                  )}
                </Button>
              </div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="w-full sm:w-auto">
                <Button type="submit" size="lg" className="w-full sm:w-auto gap-2 h-12 sm:h-14 px-6 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-md hover:shadow-lg transition-all">
                  <Sparkles className="h-5 w-5" />
                  Search
                </Button>
              </motion.div>
            </form>

          {/* Filters */}
          <div className="flex items-center gap-4 mt-4">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filter by type:</span>
            {INTEL_TYPES.map((type) => (
              <Button
                key={type.value}
                variant={selectedTypes.includes(type.value as IntelligenceType) ? 'default' : 'outline'}
                size="sm"
                className="gap-2"
                onClick={() => toggleType(type.value as IntelligenceType)}
              >
                <type.icon className={cn('h-4 w-4', type.color)} />
                {type.label}
              </Button>
            ))}
            {selectedTypes.length > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setSelectedTypes([])}>
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      </motion.div>

      {/* Results */}
      {searchQuery && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              {isLoading ? 'Searching...' : `${results?.total || 0} results`}
            </h2>
            {results?.search_type && (
              <Badge variant="secondary">{results.search_type} search</Badge>
            )}
          </div>

          <div className="space-y-3">
            {results?.results.map((item, i) => (
              <IntelligenceCard key={item.id} item={item} index={i} />
            ))}
          </div>

          {results?.results.length === 0 && !isLoading && (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                No intelligence found for "{searchQuery}"
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Empty State */}
      {!searchQuery && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg overflow-hidden">
            {/* Gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />

            <CardContent className="p-12 text-center relative">
              <motion.div
                animate={{
                  scale: [1, 1.1, 1],
                  rotate: [0, 5, -5, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="inline-block"
              >
                <div className="rounded-full bg-gradient-to-br from-primary/20 to-primary/10 p-6 mb-6">
                  <Search className="h-12 w-12 text-primary" />
                </div>
              </motion.div>

              <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                Search Intelligence
              </h3>
              <p className="text-muted-foreground max-w-md mx-auto text-lg leading-relaxed mb-8">
                Enter a query to search across all indexed intelligence from your projects.
                Use natural language for semantic search.
              </p>

              <div className="flex flex-col gap-3">
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  Try these examples
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {[
                    'How does the RAG engine work?',
                    'Security configurations',
                    'API endpoints',
                    'Database schemas',
                  ].map((example, i) => (
                    <motion.div
                      key={example}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + i * 0.05 }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Button
                        variant="outline"
                        size="sm"
                        className="hover:bg-primary/10 hover:border-primary/30 transition-all shadow-sm"
                        onClick={() => {
                          setQuery(example)
                          setSearchQuery(example)
                        }}
                      >
                        {example}
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

function IntelligenceCard({ item, index }: { item: IntelligenceItem; index: number }) {
  const typeConfig = INTEL_TYPES.find((t) => t.value === item.type)
  const TypeIcon = typeConfig?.icon || Code

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, type: "spring", stiffness: 200 }}
      whileHover={{ y: -2, scale: 1.005 }}
    >
      <Card className="group hover:border-primary/30 transition-all duration-300 border-0 shadow-md hover:shadow-xl overflow-hidden cursor-pointer">
        {/* Gradient accent bar */}
        <div className={cn(
          'h-1 w-full transition-all duration-300 group-hover:h-1.5',
          typeConfig?.value === 'sigint' && 'bg-gradient-to-r from-amber-500 to-amber-600',
          typeConfig?.value === 'humint' && 'bg-gradient-to-r from-green-500 to-emerald-600',
          typeConfig?.value === 'osint' && 'bg-gradient-to-r from-blue-500 to-cyan-600',
          typeConfig?.value === 'techint' && 'bg-gradient-to-r from-violet-500 to-purple-600'
        )} />

        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <motion.div
              className={cn(
                'p-3 rounded-xl shadow-sm shrink-0',
                typeConfig?.value === 'sigint' && 'bg-gradient-to-br from-amber-500/20 to-amber-500/10',
                typeConfig?.value === 'humint' && 'bg-gradient-to-br from-green-500/20 to-green-500/10',
                typeConfig?.value === 'osint' && 'bg-gradient-to-br from-blue-500/20 to-blue-500/10',
                typeConfig?.value === 'techint' && 'bg-gradient-to-br from-violet-500/20 to-violet-500/10'
              )}
              whileHover={{ rotate: 5, scale: 1.1 }}
              transition={{ duration: 0.2 }}
            >
              <TypeIcon className={cn('h-5 w-5', typeConfig?.color)} />
            </motion.div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-bold text-lg truncate group-hover:text-primary transition-colors">
                  {item.title}
                </h3>
                {item.score && (
                  <Badge variant="secondary" className="shrink-0 shadow-sm font-semibold">
                    {(item.score * 100).toFixed(0)}% match
                  </Badge>
                )}
              </div>

              <p className="text-sm text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
                {item.content}
              </p>

              <div className="flex items-center flex-wrap gap-2 text-xs">
                <Badge variant={item.type as any} className="shadow-sm">
                  {item.type}
                </Badge>
                <Badge variant={item.threat_level as any} className="shadow-sm">
                  {item.threat_level}
                </Badge>
                <span className="text-muted-foreground font-medium">{item.source}</span>
                {item.related_projects?.length > 0 && (
                  <span className="text-muted-foreground">
                    • {item.related_projects.slice(0, 2).join(', ')}
                    {item.related_projects.length > 2 && ` +${item.related_projects.length - 2}`}
                  </span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
