import React from 'react'
import { cn } from '../../lib/utils'

// ─── Color scheme maps ─────────────────────────────────────────────────────
const iconGradients = {
  blue:    'bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/25',
  emerald: 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-500/25',
  amber:   'bg-gradient-to-tr from-amber-500 to-orange-500 text-white shadow-md shadow-amber-500/25',
  purple:  'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/25',
  slate:   'bg-gradient-to-tr from-slate-600 to-slate-700 text-white shadow-md shadow-slate-500/25',
} as const

const ambientWash = {
  blue:    'from-blue-400/15 via-indigo-400/5 to-transparent',
  emerald: 'from-emerald-400/15 via-teal-400/5 to-transparent',
  amber:   'from-amber-400/15 via-orange-400/5 to-transparent',
  purple:  'from-purple-400/15 via-indigo-400/5 to-transparent',
  slate:   'from-slate-400/15 via-slate-400/5 to-transparent',
} as const

const accentBorder = {
  blue:    'from-blue-500 to-indigo-500',
  emerald: 'from-emerald-500 to-teal-500',
  amber:   'from-amber-500 to-orange-500',
  purple:  'from-purple-500 to-indigo-500',
  slate:   'from-slate-400 to-slate-500',
} as const

type ColorScheme = keyof typeof iconGradients

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  trend?: string
  trendType?: 'positive' | 'negative' | 'neutral'
  colorScheme?: ColorScheme
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendType = 'neutral',
  colorScheme = 'blue',
}) => {
  const trendColors = {
    positive: 'text-emerald-600 bg-emerald-500/10 border-emerald-500/20',
    negative: 'text-rose-600 bg-rose-500/10 border-rose-500/20',
    neutral:  'text-slate-600 bg-slate-500/10 border-slate-500/20',
  }

  return (
    <div className="relative group bg-white/75 backdrop-blur-xl border border-white/80 rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-[0_14px_40px_rgb(79,70,229,0.08)] hover:-translate-y-0.5 hover:border-white shadow-[0_8px_30px_rgb(0,0,0,0.03)]">
      {/* Ambient glowing gradient orb in top corner */}
      <div className={cn('absolute -top-10 -right-10 w-36 h-36 rounded-full blur-2xl opacity-60 bg-gradient-to-br', ambientWash[colorScheme])} />

      <div className="relative p-5.5 flex items-start justify-between gap-4">
        {/* Text Details */}
        <div className="space-y-1.5 min-w-0">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest truncate">
            {title}
          </p>
          <div className="text-[28px] font-black text-slate-900 tracking-tight leading-none">
            {value}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
          )}
          {trend && (
            <span className={cn('inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border mt-1', trendColors[trendType])}>
              {trend}
            </span>
          )}
        </div>

        {/* Icon Badge */}
        <div className={cn(
          'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 mt-0.5 transition-transform group-hover:scale-105 duration-200',
          iconGradients[colorScheme]
        )}>
          <Icon size={22} />
        </div>
      </div>

      {/* Bottom accent glow strip */}
      <div className={cn('h-1 bg-gradient-to-r opacity-80', accentBorder[colorScheme])} />
    </div>
  )
}
