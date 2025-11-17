import React from 'react'
import { X, Clock, FileText, Trash2 } from 'lucide-react'
import clsx from 'clsx'

export default function DraftRecoveryModal({ drafts, onResume, onDiscard, onClose }) {
  if (!drafts || drafts.length === 0) {
    return null
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-2xl w-full shadow-nebula-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-800">
          <div className="flex items-center space-x-3">
            <FileText className="text-primary-500" size={24} />
            <div>
              <h2 className="text-xl font-bold text-gray-100">Resume Previous Work?</h2>
              <p className="text-sm text-gray-400 mt-1">
                We found {drafts.length} unsaved draft{drafts.length === 1 ? '' : 's'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Drafts List */}
        <div className="p-6 space-y-3 max-h-96 overflow-y-auto">
          {drafts.map((draft) => {
            const epicKey = draft.metadata?.epic_key || 'Unknown'
            const updatedAt = draft.updated_at || draft.created_at

            return (
              <div
                key={draft.id}
                className="bg-dark-800 border border-dark-700 rounded-lg p-4 hover:border-primary-500/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-primary-400 font-medium">{epicKey}</span>
                      <span className="text-xs px-2 py-1 bg-primary-500/10 border border-primary-500/30 rounded text-primary-300">
                        {draft.data_type.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <div className="flex items-center space-x-4 text-sm text-gray-400">
                      <div className="flex items-center space-x-1">
                        <Clock size={14} />
                        <span>{formatDate(updatedAt)}</span>
                      </div>
                      {draft.metadata?.progress && (
                        <span>{draft.metadata.progress}% complete</span>
                      )}
                    </div>

                    {/* Preview if available */}
                    {draft.metadata?.summary && (
                      <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                        {draft.metadata.summary}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => onResume(draft)}
                      className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Resume
                    </button>
                    <button
                      onClick={() => onDiscard(draft)}
                      className="p-2 hover:bg-red-900/20 text-red-400 rounded-lg transition-colors"
                      title="Discard draft"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-dark-800">
          <p className="text-xs text-gray-500">
            Drafts are saved automatically every 30 seconds
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors"
          >
            Start Fresh
          </button>
        </div>
      </div>
    </div>
  )
}
