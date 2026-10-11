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
  ChevronLeft,
  ChevronRight,
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
    section: 'Library Operations',
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
    navigate('/login')
  }

  // Close mobile drawer on route change
  React.useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-900 text-slate-200 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
        {!collapsed && (
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
              SL
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-sm tracking-tight text-white leading-tight">Smart Library</span>
              <span className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">Study Center OS</span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 mx-auto rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
            SL
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden md:flex p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navSections.map((sec) => (
          <div key={sec.section} className="space-y-1">
            {!collapsed && (
              <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                {sec.section}
              </p>
            )}
            {sec.items.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-sm font-semibold'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    } ${collapsed ? 'justify-center px-2' : ''}`
                  }
                  title={collapsed ? item.title : undefined}
                >
                  <Icon size={18} className="shrink-0" />
                  {!collapsed && <span className="truncate">{item.title}</span>}
                </NavLink>
              )
            })}
          </div>
        ))}
      </div>

      {/* Footer Profile & Logout */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        {!collapsed && user && (
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 mb-2">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-7 h-7 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold shrink-0">
                {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-xs font-semibold text-white truncate">{user.full_name || user.username || 'User'}</span>
                <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                  {user.role === 'ADMIN' ? (
                    <ShieldCheck size={10} className="text-emerald-400" />
                  ) : (
                    <UserCheck size={10} className="text-blue-400" />
                  )}
                  {user.role || 'STAFF'}
                </span>
              </div>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors ${
            collapsed ? 'justify-center px-2' : ''
          }`}
          title="Sign Out"
        >
          <LogOut size={16} className="shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile Top Toggle */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-slate-900 border-b border-slate-800 z-40 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
            SL
          </div>
          <span className="font-semibold text-white text-sm">Smart Library</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-md text-slate-300 hover:bg-slate-800 focus:outline-none"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setMobileOpen(false)}>
          <div
            className="w-72 h-full bg-slate-900 z-50 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
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
