import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { formatDistanceToNow } from 'date-fns'

/**
 * Utility function to merge Tailwind classes
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

/**
 * Get health color class based on score (0-100)
 */
export function getHealthColor(score: number): string {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    if (score >= 40) return 'text-orange-500'
    return 'text-red-500'
}

/**
 * Format relative time from timestamp
 */
export function formatRelativeTime(timestamp: string | number): string {
    try {
        const date = typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp * 1000)
        return formatDistanceToNow(date, { addSuffix: true })
    } catch {
        return 'Unknown'
    }
}

/**
 * Format date to readable string
 */
export function formatDate(timestamp: string | number | Date): string {
    try {
        const date = timestamp instanceof Date ? timestamp :
            typeof timestamp === 'string' ? new Date(timestamp) :
                new Date(timestamp * 1000)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    } catch {
        return 'Unknown'
    }
}

/**
 * Format bytes to human readable
 */
export function formatBytes(bytes: number, decimals = 2): string {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']

    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Format percentage
 */
export function formatPercent(value: number, decimals = 1): string {
    return `${value.toFixed(decimals)}%`
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
    if (text.length <= length) return text
    return text.slice(0, length) + '...'
}

/**
 * Get intelligence type color
 */
export function getIntelTypeColor(type: string): string {
    const colors: Record<string, string> = {
        sigint: 'text-amber-500',
        humint: 'text-green-500',
        osint: 'text-blue-500',
        techint: 'text-violet-500',
        default: 'text-gray-500',
    }
    return colors[type.toLowerCase()] || colors.default
}

/**
 * Get threat level color
 */
export function getThreatColor(level: string): string {
    const colors: Record<string, string> = {
        critical: 'text-red-500',
        high: 'text-orange-500',
        medium: 'text-yellow-500',
        low: 'text-green-500',
        info: 'text-blue-500',
        default: 'text-gray-500',
    }
    return colors[level.toLowerCase()] || colors.default
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: ReturnType<typeof setTimeout> | null = null

    return function executedFunction(...args: Parameters<T>) {
        const later = () => {
            timeout = null
            func(...args)
        }

        if (timeout) {
            clearTimeout(timeout)
        }
        timeout = setTimeout(later, wait)
    }
}
