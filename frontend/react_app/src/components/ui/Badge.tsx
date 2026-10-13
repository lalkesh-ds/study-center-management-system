import React from 'react'
import { cn } from '../../lib/utils'

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  children: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', className, children, ...props }) => {
  const variantStyles: Record<BadgeVariant, string> = {
    success: 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20 shadow-xs shadow-emerald-500/5',
    warning: 'bg-amber-500/10 text-amber-700 border-amber-500/20 shadow-xs shadow-amber-500/5',
    danger:  'bg-rose-500/10 text-rose-700 border-rose-500/20 shadow-xs shadow-rose-500/5',
    info:    'bg-blue-500/10 text-blue-700 border-blue-500/20 shadow-xs shadow-blue-500/5',
    purple:  'bg-violet-500/10 text-violet-700 border-violet-500/20 shadow-xs shadow-violet-500/5',
    neutral: 'bg-slate-500/10 text-slate-700 border-slate-500/20 shadow-xs',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider backdrop-blur-xs transition-all',
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
