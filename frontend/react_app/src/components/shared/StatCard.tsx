import React from 'react'
import { cn } from '../../lib/utils'

// ─── Color scheme maps ─────────────────────────────────────────────────────
const iconGradients = {
  blue:    'from-blue-500/20 to-blue-600/10 border-blue-500/20',
  emerald: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/20',
  amber:   'from-amber-500/20 to-amber-600/10 border-amber-500/20',
  purple:  'from-violet-500/20 to-violet-600/10 border-violet-500/20',
  slate:   'from-slate-500/20 to-slate-600/10 border-slate-500/20',
} as const

const iconTextColors = {
  blue:    'text-blue-400',
  emerald: 'text-emerald-400',
  amber:   'text-amber-400',
  purple:  'text-violet-400',
  slate:   'text-slate-400',
} as const

const valueBars = {
  blue:    'from-blue-500/20 via-blue-600/5 to-transparent',
  emerald: 'from-emerald-500/20 via-emerald-600/5 to-transparent',
  amber:   'from-amber-500/20 via-amber-600/5 to-transparent',
  purple:  'from-violet-500/20 via-violet-600/5 to-transparent',
  slate:   'from-slate-500/20 via-slate-600/5 to-transparent',
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
    positive: 'text-emerald-400',
    negative: 'text-rose-400',
    neutral:  'text-slate-500',
  }

  return (
    <div className="relative group bg-[#0e1629] border border-white/[0.07] rounded-2xl overflow-hidden transition-all duration-200 hover:border-white/[0.14] hover:shadow-lg hover:shadow-black/30">
      {/* Gradient wash top-right */}
      <div className={cn('absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 bg-gradient-to-br opacity-50', valueBars[colorScheme])} />

      <div className="relative p-5 flex items-start justify-between gap-4">
        {/* Text */}
        <div className="space-y-1 min-w-0">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest truncate">
            {title}
          </p>
          <div className="text-[26px] font-bold text-white tracking-tight leading-none">
            {value}
          </div>
          {subtitle && (
            <p className="text-[11px] text-slate-500 font-medium">{subtitle}</p>
          )}
          {trend && (
            <p className={cn('text-[11px] font-semibold mt-1', trendColors[trendType])}>
              {trend}
            </p>
          )}
        </div>

        {/* Icon box */}
        <div className={cn(
          'w-11 h-11 rounded-xl bg-gradient-to-br border flex items-center justify-center shrink-0 mt-0.5',
          iconGradients[colorScheme]
        )}>
          <Icon size={20} className={iconTextColors[colorScheme]} />
        </div>
      </div>

      {/* Bottom accent line */}
      <div className={cn('h-[2px] bg-gradient-to-r to-transparent', valueBars[colorScheme])} />
    </div>
  )
}
