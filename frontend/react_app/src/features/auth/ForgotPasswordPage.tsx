import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, KeyRound, Loader2, Mail, Sparkles } from 'lucide-react'

export const ForgotPasswordPage: React.FC = () => {
  const [identifier, setIdentifier] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!identifier.trim()) return

    setIsSubmitting(true)
    // Simulate recovery link dispatch
    await new Promise((resolve) => setTimeout(resolve, 800))
    setIsSubmitting(false)
    setSubmitted(true)
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#f8fafc] text-slate-800 p-4 sm:p-6 lg:p-8 font-sans overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* ── Luminous Ambient Mesh Orbs ── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -top-32 -right-32 w-[650px] h-[650px] rounded-full bg-gradient-to-br from-indigo-300/30 via-purple-300/25 to-pink-200/20 blur-[140px]" />
        <div className="absolute -bottom-32 -left-32 w-[650px] h-[650px] rounded-full bg-gradient-to-br from-sky-200/40 via-blue-300/25 to-indigo-200/20 blur-[150px]" />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-pink-200/20 via-purple-200/20 to-blue-200/20 blur-[160px]" />
      </div>

      <div className="relative z-10 w-full max-w-md space-y-5 my-6">
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
              <KeyRound size={20} />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                Password Recovery <Sparkles size={16} className="text-indigo-500" />
              </h2>
              <p className="text-slate-500 text-xs font-medium">Reset your secure library workspace access</p>
            </div>
          </div>

          {submitted ? (
            <div className="space-y-4 text-center py-2">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-white flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
                <CheckCircle2 size={28} />
              </div>
              <h3 className="text-base font-bold text-slate-900">Recovery Instructions Sent</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                If an account exists for <span className="font-semibold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded-md">{identifier}</span>, password reset instructions have been dispatched.
              </p>
              <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/80 text-xs text-slate-600 text-left space-y-1">
                <p className="font-bold text-slate-800">Need Immediate Help?</p>
                <p className="text-slate-500">Visit your study center front-desk counter or contact your primary administrator for manual verification.</p>
              </div>
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition-all cursor-pointer"
              >
                <ArrowLeft size={14} />
                <span>Return to Sign In</span>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  Account Identifier
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="Enter email, username, or mobile"
                    required
                    className="w-full px-4 py-3 rounded-2xl bg-white/90 border border-slate-200/80 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/12 transition-all shadow-xs pr-11"
                  />
                  <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                    <Mail size={16} />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/35 transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer active:scale-[0.99]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Verifying Account...</span>
                  </>
                ) : (
                  <span>Send Recovery Instructions</span>
                )}
              </button>

              <div className="text-center pt-2">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-indigo-600 font-bold transition-colors"
                >
                  <ArrowLeft size={14} />
                  <span>Return to Sign In</span>
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
