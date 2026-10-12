import React from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Activity } from 'lucide-react'

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
    <header className="h-16 bg-[#0e1629]/95 backdrop-blur-sm border-b border-white/[0.06] px-6 flex items-center justify-between shrink-0">
      {/* Left: Page title */}
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xl">{info.emoji}</span>
        <div className="min-w-0">
          <h1 className="text-[15px] font-bold text-white tracking-tight leading-tight truncate">
            {info.title}
          </h1>
          <p className="text-[11px] text-slate-500 font-normal truncate hidden sm:block">{info.subtitle}</p>
        </div>
      </div>

      {/* Right: Status + user */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Live badge */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold">
          <Activity size={11} className="text-emerald-400" />
          <span>Live · 100 Desks</span>
        </div>

        {/* User avatar */}
        {user && (
          <div className="flex items-center gap-2.5 pl-3 border-l border-white/[0.08]">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-white leading-tight">{displayName}</p>
              <p className="text-[10px] text-slate-500 capitalize">{(user.role || 'staff').toLowerCase()}</p>
            </div>
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500/40 to-violet-600/30 border border-indigo-500/30 text-indigo-200 flex items-center justify-center text-xs font-bold shadow-sm">
              {avatarLetter}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
