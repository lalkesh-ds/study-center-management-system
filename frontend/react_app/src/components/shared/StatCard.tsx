import React from 'react'
import { Card, CardContent } from '../ui/Card'
import { cn } from '../../lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  trend?: string
  trendType?: 'positive' | 'negative' | 'neutral'
  colorScheme?: 'blue' | 'emerald' | 'amber' | 'purple' | 'slate'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  colorScheme = 'blue',
}) => {
  const iconColors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    slate: 'bg-slate-100 text-slate-600 border-slate-200',
  }

  return (
    <Card className="hover:border-slate-300 transition-colors">
      <CardContent className="p-5 flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {trend && (
            <p className="text-xs font-medium text-blue-600 mt-1 flex items-center gap-1">
              <span>{trend}</span>
            </p>
          )}
        </div>
        <div className={cn('p-3 rounded-xl border shrink-0', iconColors[colorScheme])}>
          <Icon size={22} />
        </div>
      </CardContent>
    </Card>
  )
}
