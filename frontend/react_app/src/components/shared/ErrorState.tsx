import React from 'react'
import { AlertCircle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load data',
  message,
  onRetry,
}) => {
  return (
    <div className="p-8 rounded-xl bg-rose-50/50 border border-rose-200 text-center flex flex-col items-center justify-center space-y-3">
      <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center">
        <AlertCircle size={22} />
      </div>
      <div className="space-y-1 max-w-md">
        <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
        <p className="text-xs text-rose-700 leading-relaxed">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-white border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-lg text-xs font-semibold shadow-xs transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  )
}
