import React, { useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../context/AuthContext'
import {
  LayoutDashboard,
  Armchair,
  GraduationCap,
  ClipboardList,
  CreditCard,
  Clock,
  BarChart3,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  UserCheck,
  Menu,
  X,
  Sparkles,
} from 'lucide-react'

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
}

const navSections: { section: string; items: NavItem[] }[] = [
  {
    section: 'Overview',
    items: [{ title: 'Dashboard', href: '/', icon: LayoutDashboard }],
  },
  {
    section: 'Operations',
    items: [
      { title: 'Seat Management', href: '/seats', icon: Armchair },
      { title: 'Students', href: '/students', icon: GraduationCap },
      { title: 'Memberships', href: '/memberships', icon: ClipboardList },
      { title: 'Attendance', href: '/attendance', icon: Clock },
    ],
  },
  {
    section: 'Finance',
    items: [{ title: 'Cashier & Payments', href: '/payments', icon: CreditCard }],
  },
  {
    section: 'Intelligence',
    items: [{ title: 'Analytics & Reports', href: '/analytics', icon: BarChart3 }],
  },
]

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()

  const handleLogout = () => {
    logout()
    queryClient.clear()
    navigate('/login', { replace: true })
  }

  React.useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const avatarLetter = (user?.full_name || user?.username || 'U').charAt(0).toUpperCase()
  const displayName = user?.full_name || user?.username || 'User'
  const isAdmin = user?.role === 'ADMIN'

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white/70 backdrop-blur-2xl text-slate-700 border-r border-white/80 shadow-[4px_0_30px_rgba(0,0,0,0.02)] select-none">

      {/* ── Brand Header ── */}
      <div className={`h-16 flex items-center border-b border-slate-100/80 shrink-0 ${collapsed ? 'justify-center px-3' : 'justify-between px-4'}`}>
        {!collapsed && (
          <div className="flex items-center gap-3 overflow-hidden min-w-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/25 shrink-0">
              SL
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-sm tracking-tight text-slate-900 leading-tight truncate">Smart Library</span>
              <span className="text-[10px] text-indigo-600 font-semibold uppercase tracking-wider flex items-center gap-1">
                <Sparkles size={9} className="text-indigo-500" />
                Study Center OS
              </span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/25">
            SL
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100/70 transition-all focus:outline-none shrink-0"
            title="Collapse sidebar"
          >
            <PanelLeftClose size={16} />
          </button>
        )}
      </div>

      {/* ── Nav Items ── */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
        {navSections.map((sec) => (
          <div key={sec.section}>
            {!collapsed && (
              <p className="px-3 mb-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                {sec.section}
              </p>
            )}
            <div className="space-y-1">
              {sec.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    end={item.href === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/25 font-semibold'
                          : 'text-slate-600 hover:bg-white/80 hover:text-indigo-600 hover:shadow-xs'
                      } ${collapsed ? 'justify-center px-2.5' : ''}`
                    }
                    title={collapsed ? item.title : undefined}
                  >
                    {({ isActive }) => (
                      <>
                        <Icon
                          size={18}
                          className={`shrink-0 transition-transform ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-600'}`}
                        />
                        {!collapsed && <span className="truncate">{item.title}</span>}
                      </>
                    )}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* ── Expand Button (when collapsed) ── */}
      {collapsed && (
        <div className="px-2 pb-2">
          <button
            onClick={() => setCollapsed(false)}
            className="w-full p-2.5 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-white/80 transition-all flex items-center justify-center focus:outline-none"
            title="Expand sidebar"
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>
      )}

      {/* ── Footer: User Profile + Logout ── */}
      <div className="p-3 border-t border-slate-100/80 space-y-2 shrink-0">
        {!collapsed && user && (
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/70 border border-white shadow-xs">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white flex items-center justify-center text-xs font-bold shadow-xs shrink-0">
              {avatarLetter}
            </div>
            <div className="flex flex-col overflow-hidden min-w-0">
              <span className="text-xs font-bold text-slate-800 truncate">{displayName}</span>
              <span className="text-[10px] text-slate-500 flex items-center gap-1 font-medium">
                {isAdmin ? (
                  <ShieldCheck size={10} className="text-emerald-600 shrink-0" />
                ) : (
                  <UserCheck size={10} className="text-blue-600 shrink-0" />
                )}
                {user?.role || 'STAFF'}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-all ${
            collapsed ? 'justify-center px-2' : ''
          }`}
          title="Sign Out"
        >
          <LogOut size={15} className="shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* ── Mobile Top Bar ── */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 z-40 flex items-center justify-between px-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-indigo-500/20">
            SL
          </div>
          <span className="font-bold text-slate-900 text-sm">Smart Library</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg text-slate-600 hover:bg-slate-100/80 focus:outline-none transition-all"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* ── Mobile Drawer ── */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0 bg-slate-900/20 backdrop-blur-xs" />
          <div
            className="relative w-72 h-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}

      {/* ── Desktop Sidebar ── */}
      <aside
        className={`hidden md:flex flex-col shrink-0 h-screen sticky top-0 transition-all duration-200 z-30 ${
          collapsed ? 'w-18' : 'w-64'
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
