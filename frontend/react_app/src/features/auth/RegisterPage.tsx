import React, { useState } from 'react'
import { Link, useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Eye, EyeOff, Loader2, ArrowLeft, ArrowRight, Sparkles } from 'lucide-react'

const inputClass =
  'w-full px-4 py-3 rounded-2xl bg-white/90 border border-slate-200/80 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/12 transition-all shadow-xs'
const labelClass = 'text-[11px] font-bold text-slate-500 uppercase tracking-wider'

export const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    libraryName: '',
    username: '',
    mobile: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { register, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()

  // 🔒 Security: already-authenticated users cannot see register page
  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match. Please re-enter.')
      return
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setIsSubmitting(true)
    try {
      await register({
        username: formData.username.trim(),
        email: formData.email.trim(),
        ...(formData.mobile.trim() ? { mobile: formData.mobile.trim() } : {}),
        full_name: `${formData.fullName.trim()} (${formData.libraryName.trim()})`,
        password: formData.password,
      })
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please verify your details.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#f8fafc] text-slate-800 p-4 sm:p-6 lg:p-8 font-sans overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* ── Luminous Ambient Mesh Orbs ── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -top-32 -right-32 w-[650px] h-[650px] rounded-full bg-gradient-to-br from-indigo-300/30 via-purple-300/25 to-pink-200/20 blur-[140px]" />
        <div className="absolute -bottom-32 -left-32 w-[650px] h-[650px] rounded-full bg-gradient-to-br from-sky-200/40 via-blue-300/25 to-indigo-200/20 blur-[150px]" />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-pink-200/20 via-purple-200/20 to-blue-200/20 blur-[160px]" />
      </div>

      <div className="relative z-10 w-full max-w-xl space-y-5 my-6">
        {/* Back navigation */}
        <Link
          to="/login"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-indigo-600 transition-colors bg-white/70 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white shadow-xs"
        >
          <ArrowLeft size={14} />
          Back to Sign In
        </Link>

        {/* Floating Frosted Glass Card */}
        <div className="bg-white/75 backdrop-blur-2xl border border-white/90 rounded-3xl p-8 sm:p-10 shadow-[0_20px_50px_rgba(79,70,229,0.08)] space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3.5 pb-2">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-indigo-500/25 shrink-0">
              SL
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                Register Your Library <Sparkles size={16} className="text-indigo-500" />
              </h2>
              <p className="text-slate-500 text-xs font-medium">Provision your Library Owner Administrator Account</p>
            </div>
          </div>

          {/* Error Notice */}
          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200/80 text-xs text-rose-700 font-semibold animate-in fade-in">
              <span className="shrink-0 mt-0.5">⚠</span>
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Row 1: Owner Name & Library Name */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className={labelClass}>Owner Full Name</label>
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="e.g. Ramesh Sharma"
                  required
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <label className={labelClass}>Library / Study Center Name</label>
                <input
                  type="text"
                  name="libraryName"
                  value={formData.libraryName}
                  onChange={handleChange}
                  placeholder="e.g. Apex Study Lounge"
                  required
                  className={inputClass}
                />
              </div>
            </div>

            {/* Row 2: Username & Mobile */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className={labelClass}>Admin Username</label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="e.g. apex_admin"
                  required
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <label className={labelClass}>Mobile Number (Optional)</label>
                <input
                  type="tel"
                  name="mobile"
                  value={formData.mobile}
                  onChange={handleChange}
                  placeholder="e.g. 9876543210"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Row 3: Email */}
            <div className="space-y-1.5">
              <label className={labelClass}>Official Email Address</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="e.g. owner@apexstudylounge.com"
                required
                className={inputClass}
              />
            </div>

            {/* Row 4: Password & Confirm Password */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className={labelClass}>Master Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Min 8 characters"
                    required
                    className={`${inputClass} pr-11`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className={labelClass}>Confirm Password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Re-enter password"
                  required
                  className={inputClass}
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Creating Admin Terminal…</span>
                  </>
                ) : (
                  <>
                    <span>Complete Registration</span>
                    <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Sign In Footer */}
          <div className="pt-3 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-600 font-medium">
              Already have an account?{' '}
              <Link to="/login" className="font-bold text-indigo-600 hover:text-indigo-700 transition-colors">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
