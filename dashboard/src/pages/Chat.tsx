import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  Send,
  Trash2,
  Bot,
  User,
  Loader2,
  BookOpen,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useChatMutation, useAiHealth } from '@/hooks/useApi'
import { cn, formatRelativeTime } from '@/lib/utils'
import type { ChatMessage } from '@/types'

interface DisplayMessage extends ChatMessage {
  id: string
  timestamp: string
  sources?: Array<{ title: string; type: string; source: string; score?: number }>
  rag_used?: boolean
  model?: string | null
}

const SUGGESTIONS = [
  'How does the RAG engine work?',
  'What projects are in the ecosystem?',
  'Explain the embedding pipeline',
  'What are the current security findings?',
  'Show me the architecture overview',
]

export function Chat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [sourcesOpen, setSourcesOpen] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: aiHealth } = useAiHealth()
  const chatMutation = useChatMutation()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || chatMutation.isPending) return

    const userMsg: DisplayMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    const history: ChatMessage[] = [
      ...messages.map((m) => ({ role: m.role, content: m.content })),
      { role: 'user', content },
    ]

    setMessages((prev) => [...prev, userMsg])
    setInput('')

    chatMutation.mutate(
      { messages: history, use_rag: true },
      {
        onSuccess: (data) => {
          const assistantMsg: DisplayMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.message.content,
            timestamp: new Date().toISOString(),
            sources: data.sources,
            rag_used: data.rag_used,
            model: data.model,
          }
          setMessages((prev) => [...prev, assistantMsg])
        },
        onError: () => {
          const errMsg: DisplayMessage = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'An error occurred. Please try again.',
            timestamp: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, errMsg])
        },
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleSources = (id: string) => {
    setSourcesOpen((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Brain className="h-8 w-8 text-cerebro-primary" />
            AI Chat
          </h1>
          <p className="text-muted-foreground">
            Conversational AI powered by your knowledge base
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={aiHealth?.available ? 'default' : 'destructive'}>
            {aiHealth?.available ? `Online · ${aiHealth.model ?? 'local'}` : 'LLM Offline'}
          </Badge>
          {messages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMessages([])}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.length === 0 ? (
          <EmptyState onSuggestion={handleSend} />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <MessageBubble
                  msg={msg}
                  sourcesOpen={sourcesOpen[msg.id] ?? false}
                  onToggleSources={() => toggleSources(msg.id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        )}

        {chatMutation.isPending && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-start gap-3"
          >
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <Card className="border-0 shadow-sm">
              <CardContent className="p-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Thinking…</span>
              </CardContent>
            </Card>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="shrink-0">
        <Card className="border-0 shadow-lg overflow-hidden">
          <div className="h-0.5 bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500" />
          <CardContent className="p-3">
            <div className="flex gap-3 items-center">
              <Input
                ref={inputRef}
                placeholder="Ask about your codebase, projects, or ecosystem…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={chatMutation.isPending}
                className="border-0 shadow-none focus-visible:ring-0 text-base"
              />
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || chatMutation.isPending}
                size="icon"
                className="shrink-0 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70"
              >
                {chatMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
        <p className="text-xs text-muted-foreground text-center mt-2">
          Press Enter to send · RAG context from knowledge base · Local LLM only
        </p>
      </div>
    </div>
  )
}

function MessageBubble({
  msg,
  sourcesOpen,
  onToggleSources,
}: {
  msg: DisplayMessage
  sourcesOpen: boolean
  onToggleSources: () => void
}) {
  const isUser = msg.role === 'user'

  return (
    <div className={cn('flex items-start gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'h-8 w-8 rounded-full flex items-center justify-center shrink-0',
          isUser ? 'bg-muted' : 'bg-primary/10'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-muted-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>

      <div className={cn('flex flex-col gap-1 max-w-[80%]', isUser && 'items-end')}>
        <Card
          className={cn(
            'border-0 shadow-sm',
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted/50'
          )}
        >
          <CardContent className="p-3">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
              {msg.content}
            </pre>
          </CardContent>
        </Card>

        <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
          <span>{formatRelativeTime(msg.timestamp)}</span>
          {msg.rag_used && (
            <Badge variant="secondary" className="text-xs py-0 h-4">
              <BookOpen className="h-2.5 w-2.5 mr-1" />
              RAG
            </Badge>
          )}
          {msg.model && (
            <span className="font-mono">{msg.model}</span>
          )}
          {msg.sources && msg.sources.length > 0 && (
            <button
              onClick={onToggleSources}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              {sourcesOpen ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              {msg.sources.length} source{msg.sources.length !== 1 ? 's' : ''}
            </button>
          )}
        </div>

        {sourcesOpen && msg.sources && msg.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="w-full space-y-1"
          >
            {msg.sources.map((src, i) => (
              <div key={i} className="rounded-md border bg-muted/30 p-2 text-xs">
                <div className="flex items-center gap-2">
                  <Badge variant={src.type as any} className="text-[10px] py-0">
                    {src.type}
                  </Badge>
                  <span className="font-medium truncate">{src.title}</span>
                  {src.score != null && (
                    <span className="ml-auto text-muted-foreground">
                      {(src.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <span className="text-muted-foreground">{src.source}</span>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  )
}

function EmptyState({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-12 text-center">
      <motion.div
        animate={{ scale: [1, 1.05, 1], rotate: [0, 3, -3, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        className="rounded-full bg-gradient-to-br from-primary/20 to-primary/10 p-6 mb-6"
      >
        <Brain className="h-12 w-12 text-primary" />
      </motion.div>

      <h3 className="text-2xl font-bold mb-2">Chat with CEREBRO</h3>
      <p className="text-muted-foreground max-w-md mb-8 leading-relaxed">
        Ask anything about your projects, architecture decisions, code patterns,
        or get insights from the indexed knowledge base.
      </p>

      <div className="flex flex-col gap-2 w-full max-w-md">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
          Suggested questions
        </p>
        {SUGGESTIONS.map((s, i) => (
          <motion.div
            key={s}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.07 }}
          >
            <Button
              variant="outline"
              className="w-full justify-start gap-2 text-left hover:bg-primary/5 hover:border-primary/30"
              onClick={() => onSuggestion(s)}
            >
              <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
              {s}
            </Button>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
