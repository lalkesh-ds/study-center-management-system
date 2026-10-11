import React from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Home } from 'lucide-react'

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="text-center space-y-4 max-w-md">
        <div className="w-16 h-16 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
          <AlertCircle size={32} />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">404 - Page Not Found</h1>
        <p className="text-sm text-slate-600">
          The operations module or page view you requested does not exist or has been relocated.
        </p>
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-colors"
          >
            <Home size={14} />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
