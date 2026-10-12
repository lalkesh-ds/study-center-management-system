import React, { useState } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
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

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  React.useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const avatarLetter = (user?.full_name || user?.username || 'U').charAt(0).toUpperCase()
  const displayName = user?.full_name || user?.username || 'User'
  const isAdmin = user?.role === 'ADMIN'

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0c1021] text-slate-300 border-r border-white/[0.06] select-none">

      {/* ── Brand Header ── */}
      <div className={`h-16 flex items-center border-b border-white/[0.06] shrink-0 ${collapsed ? 'justify-center px-3' : 'justify-between px-4'}`}>
        {!collapsed && (
          <div className="flex items-center gap-2.5 overflow-hidden min-w-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/30 shrink-0">
              SL
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-sm tracking-tight text-white leading-tight truncate">Smart Library</span>
              <span className="text-[10px] text-indigo-400/70 font-medium uppercase tracking-widest">Study Center OS</span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/30">
            SL
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/[0.06] transition-all focus:outline-none shrink-0"
            title="Collapse sidebar"
          >
            <PanelLeftClose size={16} />
          </button>
        )}
      </div>

      {/* ── Nav Items ── */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-5">
        {navSections.map((sec) => (
          <div key={sec.section}>
            {!collapsed && (
              <p className="px-3 mb-1.5 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">
                {sec.section}
              </p>
            )}
            <div className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    end={item.href === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                        isActive
                          ? 'bg-gradient-to-r from-indigo-600/30 to-violet-600/20 text-white border border-indigo-500/20 shadow-sm shadow-indigo-500/10'
                          : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-200'
                      } ${collapsed ? 'justify-center px-2.5' : ''}`
                    }
                    title={collapsed ? item.title : undefined}
                  >
                    {({ isActive }) => (
                      <>
                        <Icon
                          size={18}
                          className={`shrink-0 transition-colors ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`}
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
            className="w-full p-2.5 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-white/[0.05] transition-all flex items-center justify-center focus:outline-none"
            title="Expand sidebar"
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>
      )}

      {/* ── Footer: User + Logout ── */}
      <div className="p-2 border-t border-white/[0.06] space-y-1 shrink-0">
        {!collapsed && user && (
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] mb-1">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/30 to-violet-600/20 border border-indigo-500/20 text-indigo-300 flex items-center justify-center text-xs font-bold shrink-0">
              {avatarLetter}
            </div>
            <div className="flex flex-col overflow-hidden min-w-0">
              <span className="text-xs font-semibold text-white truncate">{displayName}</span>
              <span className="text-[10px] text-slate-500 flex items-center gap-1">
                {isAdmin ? (
                  <ShieldCheck size={9} className="text-emerald-400 shrink-0" />
                ) : (
                  <UserCheck size={9} className="text-blue-400 shrink-0" />
                )}
                {user?.role || 'STAFF'}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition-all ${
            collapsed ? 'justify-center px-2.5' : ''
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
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[#0c1021] border-b border-white/[0.06] z-40 flex items-center justify-between px-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-xs">
            SL
          </div>
          <span className="font-semibold text-white text-sm">Smart Library</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg text-slate-400 hover:bg-white/[0.06] focus:outline-none transition-all"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* ── Mobile Drawer ── */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
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
          collapsed ? 'w-16' : 'w-60'
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
