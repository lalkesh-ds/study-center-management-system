import React, { useState } from 'react'
import { Link, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  Eye, EyeOff, Loader2, Building2, CheckCircle2, ArrowRight,
  BookOpen, Users, BarChart3, Shield, Sparkles,
} from 'lucide-react'

const features = [
  { icon: Users, text: 'Multi-tenant study center management' },
  { icon: BookOpen, text: 'Real-time 100-desk occupancy tracking' },
  { icon: BarChart3, text: 'Cashier ledger & financial analytics' },
  { icon: Shield, text: 'Pessimistic lock admission protection' },
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
    <div className="relative min-h-screen flex font-sans bg-[#f8fafc] text-slate-800 overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* ── Luminous Ambient Mesh Orbs ── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -top-32 -left-32 w-[650px] h-[650px] rounded-full bg-gradient-to-br from-indigo-300/30 via-purple-300/25 to-pink-200/20 blur-[140px]" />
        <div className="absolute top-1/4 right-0 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-sky-200/40 via-blue-300/25 to-indigo-200/20 blur-[150px]" />
        <div className="absolute -bottom-32 left-1/3 w-[700px] h-[700px] rounded-full bg-gradient-to-tr from-pink-200/25 via-purple-200/20 to-blue-200/20 blur-[160px]" />
      </div>

      {/* ── Left Panel: Luminous Showcase ── */}
      <div className="hidden lg:flex lg:w-[50%] relative z-10 flex-col justify-between p-12 lg:p-16 border-r border-white/60 bg-white/40 backdrop-blur-2xl">
        {/* Brand header */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 flex items-center justify-center text-white font-black text-base shadow-lg shadow-indigo-500/30">
            SL
          </div>
          <div>
            <p className="text-slate-900 font-extrabold text-base tracking-tight leading-tight">Smart Library</p>
            <p className="text-indigo-600 font-bold text-[11px] uppercase tracking-widest flex items-center gap-1">
              <Sparkles size={10} /> Study Center OS
            </p>
          </div>
        </div>

        {/* Hero copy */}
        <div className="space-y-8 my-auto py-10">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 border border-white shadow-xs text-indigo-600 text-xs font-bold backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600"></span>
              </span>
              <span>100 Physical Desks · Production Grade</span>
            </div>

            <h1 className="text-[44px] font-black text-slate-900 leading-[1.12] tracking-tight">
              Lead your library
              <br />
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 bg-clip-text text-transparent">
                with modern elegance.
              </span>
            </h1>

            <p className="text-slate-600 text-base leading-relaxed max-w-md font-normal">
              Autonomous study center operating system. Conflict-free temporal seat allocation, student KYC, cashier ledgers, and attendance audits in one luminous terminal.
            </p>
          </div>

          {/* Feature list */}
          <ul className="space-y-3.5">
            {features.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-white/80 border border-white flex items-center justify-center shrink-0 shadow-xs text-indigo-600">
                  <Icon size={16} />
                </div>
                <span className="text-sm font-semibold text-slate-700">{text}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Live bottom badge */}
        <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-white/70 border border-white shadow-xs backdrop-blur-md w-fit">
          <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
          <span className="text-xs font-semibold text-slate-700">Cluster online · ACID transaction verified</span>
        </div>
      </div>

      {/* ── Right Panel: Floating Frosted Glass Form ── */}
      <div className="w-full lg:w-[50%] relative z-10 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-[420px] bg-white/75 backdrop-blur-2xl rounded-3xl p-8 sm:p-10 border border-white/90 shadow-[0_20px_50px_rgba(79,70,229,0.08)] space-y-7">

          {/* Mobile Logo Header */}
          <div className="lg:hidden flex items-center gap-3 justify-center">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-black text-sm shadow-md shadow-indigo-500/25">
              SL
            </div>
            <span className="text-slate-900 font-extrabold text-base">Smart Library</span>
          </div>

          {/* Title */}
          <div className="space-y-1">
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Welcome back</h2>
            <p className="text-slate-500 text-xs font-medium">Sign in to your library owner dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-start gap-2.5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200/80 text-xs text-rose-700 font-semibold animate-in fade-in">
                <span className="shrink-0 mt-0.5">⚠</span>
                <span>{error}</span>
              </div>
            )}

            {/* Username / Email */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Username, Email, or Mobile
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. owner@smartlibrary.com"
                required
                autoFocus
                className="w-full px-4 py-3 rounded-2xl bg-white/90 border border-slate-200/80 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/12 transition-all shadow-xs"
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Password</label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-bold transition-colors"
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
                  className="w-full px-4 py-3 rounded-2xl bg-white/90 border border-slate-200/80 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/12 transition-all shadow-xs pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors focus:outline-none cursor-pointer"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Remember Me Session Toggle */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded-md border-slate-300 text-indigo-600 focus:ring-indigo-500/20 accent-indigo-600 cursor-pointer"
                />
                <span className="text-xs text-slate-600 font-medium">Remember this session</span>
              </label>
              <span className="text-[11px] text-slate-400 font-semibold">
                {rememberMe ? 'Persistent' : 'Session only'}
              </span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
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

          {/* Registration link */}
          <div className="pt-4 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-600 font-medium">
              New Library Owner?{' '}
              <Link
                to="/register"
                className="font-bold text-indigo-600 hover:text-indigo-700 transition-colors inline-flex items-center gap-1"
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
