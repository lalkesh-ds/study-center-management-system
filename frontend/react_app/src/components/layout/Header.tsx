import React from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Sparkles } from 'lucide-react'

const routeTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Executive Operations Dashboard', subtitle: 'Real-time facility capacity, utilization rates, and revenue KPIs' },
  '/seats': { title: 'Physical Seat Inventory & Grid', subtitle: 'Live 100-desk floor plan, multi-shift availability, and maintenance controls' },
  '/students': { title: 'Students Directory & Aspirant KYC', subtitle: 'Registered student database, official student codes, and profile lookups' },
  '/memberships': { title: 'Membership Admissions & Lifecycle', subtitle: 'Conflict-free admissions, renewals, early cancellations, and audit trails' },
  '/payments': { title: 'Cashier Terminal & Financial Ledger', subtitle: 'Installment fee collections, official receipt generation, and void audits' },
  '/attendance': { title: 'Front-Desk Attendance Terminal', subtitle: 'Rapid check-in and check-out tracking with shift validity verification' },
  '/analytics': { title: 'Analytics & Financial Intelligence', subtitle: 'Detailed seat capacity models, expiry queue, and payment method breakdowns' },
}

export const Header: React.FC = () => {
  const location = useLocation()
  const { user } = useAuth()
  const info = routeTitles[location.pathname] || {
    title: 'Smart Library Operations',
    subtitle: '100 Physical Seats Management System',
  }

  return (
    <header className="h-18 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-xs">
      <div className="flex flex-col">
        <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          {info.title}
        </h1>
        <p className="text-xs text-slate-500 font-normal">{info.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium">
          <Sparkles size={13} className="text-blue-600" />
          <span>Facility Live • 100 Desks</span>
        </div>

        {user && (
          <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-slate-800">{user.full_name || user.username || 'User'}</p>
              <p className="text-[10px] text-slate-500 capitalize">{(user.role || 'Staff').toLowerCase()} Staff</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold shadow-xs">
              {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
