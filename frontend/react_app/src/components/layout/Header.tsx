import React from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Activity, Sparkles } from 'lucide-react'

const routeTitles: Record<string, { title: string; subtitle: string; emoji: string }> = {
  '/':           { emoji: '📊', title: 'Dashboard',             subtitle: 'Real-time facility capacity, utilization rates, and revenue KPIs' },
  '/seats':      { emoji: '🪑', title: 'Seat Management',       subtitle: 'Live 100-desk floor plan, multi-shift availability and maintenance' },
  '/students':   { emoji: '🎓', title: 'Students Directory',    subtitle: 'Registered student database, KYC profiles and student codes' },
  '/memberships':{ emoji: '📋', title: 'Memberships',           subtitle: 'Conflict-free admissions, renewals, early cancellations and audit trails' },
  '/payments':   { emoji: '💳', title: 'Cashier & Payments',    subtitle: 'Fee collections, receipt generation and void audits' },
  '/attendance': { emoji: '📍', title: 'Attendance Terminal',   subtitle: 'Rapid check-in and check-out with shift validity verification' },
  '/analytics':  { emoji: '📈', title: 'Analytics & Reports',   subtitle: 'Seat capacity models, expiry queue and payment breakdowns' },
}

export const Header: React.FC = () => {
  const location = useLocation()
  const { user } = useAuth()
  const info = routeTitles[location.pathname] ?? {
    emoji: '⚙️',
    title: 'Smart Library',
    subtitle: '100 Physical Seats Management System',
  }

  const avatarLetter = (user?.full_name || user?.username || 'U').charAt(0).toUpperCase()
  const displayName = user?.full_name || user?.username || 'User'

  return (
    <header className="h-16 bg-white/70 backdrop-blur-xl border-b border-white/80 shadow-[0_4px_20px_rgba(0,0,0,0.02)] px-6 flex items-center justify-between shrink-0 z-20">
      {/* Left: Page title */}
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xl p-1.5 rounded-xl bg-white/80 border border-white shadow-xs">{info.emoji}</span>
        <div className="min-w-0">
          <h1 className="text-[15px] font-bold text-slate-900 tracking-tight leading-tight truncate">
            {info.title}
          </h1>
          <p className="text-[11px] text-slate-500 font-medium truncate hidden sm:block">{info.subtitle}</p>
        </div>
      </div>

      {/* Right: Status + user */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Live facility badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 text-xs font-semibold shadow-xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Live · 100 Desks</span>
        </div>

        {/* User avatar pill */}
        {user && (
          <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200/60">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold text-slate-800 leading-tight">{displayName}</p>
              <p className="text-[10px] text-indigo-600 font-semibold uppercase tracking-wider">{(user.role || 'staff').toLowerCase()}</p>
            </div>
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-indigo-500/20">
              {avatarLetter}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
