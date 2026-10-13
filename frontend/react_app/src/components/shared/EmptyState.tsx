import React from 'react'
import { FolderOpen } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
}) => {
  return (
    <div className="p-12 text-center flex flex-col items-center justify-center space-y-3.5 bg-white/60 backdrop-blur-md rounded-2xl border border-dashed border-slate-200/80 shadow-xs">
      <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-indigo-50 to-blue-50 text-indigo-500 border border-indigo-100 flex items-center justify-center shadow-xs">
        <FolderOpen size={24} />
      </div>
      <div className="space-y-1 max-w-sm">
        <h4 className="text-sm font-bold text-slate-800">{title}</h4>
        {description && <p className="text-xs text-slate-500 leading-relaxed font-normal">{description}</p>}
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all cursor-pointer"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
