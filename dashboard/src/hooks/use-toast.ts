import { useState, useEffect } from 'react'

interface ToastOptions {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  duration?: number
}

interface ToastItem extends ToastOptions {
  id: string
}

type Listener = (toasts: ToastItem[]) => void

let toasts: ToastItem[] = []
const listeners = new Set<Listener>()

function notify() {
  listeners.forEach((l) => l([...toasts]))
}

let counter = 0

export function toast(options: ToastOptions) {
  const id = String(++counter)
  const duration = options.duration ?? 4000
  toasts = [...toasts, { ...options, id }]
  notify()
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id)
    notify()
  }, duration)
}

export function useToastStore() {
  const [items, setItems] = useState<ToastItem[]>([...toasts])
  useEffect(() => {
    listeners.add(setItems)
    return () => { listeners.delete(setItems) }
  }, [])
  return items
}

export function useToast() {
  return { toast }
}
