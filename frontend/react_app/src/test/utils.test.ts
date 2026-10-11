import { describe, it, expect } from 'vitest'
import { formatCurrencyINR, formatDate, formatTime, getTodayISO, cn } from '../lib/utils'

describe('Formatting Utilities', () => {
  it('formats INR currency accurately with ₹ symbol', () => {
    expect(formatCurrencyINR(1500)).toMatch(/₹\s?1,500/)
    expect(formatCurrencyINR(0)).toMatch(/₹\s?0/)
    expect(formatCurrencyINR(125000)).toMatch(/₹\s?1,25,000|₹\s?125,000/)
  })

  it('formats dates safely and handles empty/null gracefully', () => {
    expect(formatDate('2026-10-15')).toContain('Oct')
    expect(formatDate(null)).toBe('—')
    expect(formatDate(undefined)).toBe('—')
    expect(formatDate('')).toBe('—')
  })

  it('formats times safely and handles empty/null gracefully', () => {
    expect(formatTime('14:30:00')).toBeTruthy()
    expect(formatTime(null)).toBe('—')
    expect(formatTime(undefined)).toBe('—')
    expect(formatTime('')).toBe('—')
  })

  it('returns valid ISO date format for getTodayISO', () => {
    const today = getTodayISO()
    expect(today).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('merges class names correctly with cn()', () => {
    expect(cn('px-2 py-1', 'bg-blue-500', false && 'hidden')).toBe('px-2 py-1 bg-blue-500')
    expect(cn('p-4', 'p-2')).toBe('p-2') // tailwind-merge resolves conflicts
  })
})
