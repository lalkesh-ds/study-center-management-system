import React, { useState } from 'react'
import { Link, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  Eye, EyeOff, Loader2, Building2, CheckCircle2, ArrowRight,
  BookOpen, Users, BarChart3, Shield,
} from 'lucide-react'

const features = [
  { icon: Users, text: 'Multi-tenant library management' },
  { icon: BookOpen, text: 'Real-time seat & attendance tracking' },
  { icon: BarChart3, text: 'Financial analytics & reporting' },
  { icon: Shield, text: 'Secure, conflict-free admission system' },
]

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { login, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Safe redirect path validation to eliminate Open Redirect attacks
  const getSafeRedirect = (): string => {
    const from = (location.state as any)?.from
    const path = typeof from === 'string' ? from : from?.pathname
    if (path && typeof path === 'string' && path.startsWith('/') && !path.startsWith('//')) {
      return path
    }
    return '/'
  }

  // 🔒 Security: already-authenticated users cannot access login page
  if (!isLoading && isAuthenticated) {
    return <Navigate to={getSafeRedirect()} replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Please provide your username/email and password.')
      return
    }
    setError(null)
    setIsSubmitting(true)
    try {
      await login(username.trim(), password, rememberMe)
      navigate(getSafeRedirect(), { replace: true })
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your credentials.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex font-sans">
      {/* ── Left Panel: Branded Hero ── */}
      <div className="hidden lg:flex lg:w-[52%] relative bg-[#0a0f1e] flex-col justify-between p-12 overflow-hidden">
        {/* Ambient glow blobs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -right-32 w-[500px] h-[500px] rounded-full bg-indigo-600/20 blur-[120px]" />
          <div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] rounded-full bg-violet-700/15 blur-[120px]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-blue-600/10 blur-[80px]" />
        </div>

        {/* Grid overlay */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/40">
            SL
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-tight">Smart Library</p>
            <p className="text-indigo-400/80 text-[11px] font-medium uppercase tracking-widest">Study Center OS</p>
          </div>
        </div>

        {/* Main copy */}
        <div className="relative z-10 space-y-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              100 Desks · Live System
            </div>
            <h1 className="text-[42px] font-bold text-white leading-[1.15] tracking-tight">
              Manage your library
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400">
                with confidence.
              </span>
            </h1>
            <p className="text-slate-400 text-[15px] leading-relaxed max-w-sm">
              Complete study center management for library owners — seat allocation, memberships, payments, and analytics in one terminal.
            </p>
          </div>

          {/* Feature list */}
          <ul className="space-y-3">
            {features.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                  <Icon size={14} className="text-indigo-400" />
                </div>
                <span className="text-sm text-slate-300">{text}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Bottom status bar */}
        <div className="relative z-10 flex items-center gap-2.5 px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm w-fit">
          <CheckCircle2 size={14} className="text-emerald-400" />
          <span className="text-xs text-slate-400">All systems operational</span>
        </div>
      </div>

      {/* ── Right Panel: Login Form ── */}
      <div className="w-full lg:w-[48%] flex items-center justify-center bg-slate-950 p-8">
        <div className="w-full max-w-[380px] space-y-8">

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 justify-center mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm">
              SL
            </div>
            <span className="text-white font-semibold">Smart Library</span>
          </div>

          {/* Heading */}
          <div className="space-y-1.5">
            <h2 className="text-[26px] font-bold text-white tracking-tight">Welcome back</h2>
            <p className="text-slate-500 text-sm">Sign in to your library dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
                <span className="shrink-0 mt-0.5">⚠</span>
                <span>{error}</span>
              </div>
            )}

            {/* Username */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">
                Username, Email, or Mobile
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. owner@library.com"
                required
                autoFocus
                className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/60 transition-all"
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">Password</label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/60 transition-all pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400 transition-colors focus:outline-none"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember Me Toggle */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500/30 accent-indigo-600"
                />
                <span className="text-xs text-slate-400">Remember this session</span>
              </label>
              <span className="text-[11px] text-slate-600">
                {rememberMe ? 'Persistent' : 'Ends on close'}
              </span>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm shadow-lg shadow-indigo-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Signing in…</span>
                </>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Register link */}
          <div className="pt-4 border-t border-slate-800/80 text-center">
            <p className="text-sm text-slate-600">
              New Library Owner?{' '}
              <Link
                to="/register"
                className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors inline-flex items-center gap-1"
              >
                <Building2 size={13} />
                Register your Library
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
