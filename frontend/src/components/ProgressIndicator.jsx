import React, { useState } from 'react'
import { Loader2, CheckCircle, XCircle, Info, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'
import { useWebSocket } from '../context/WebSocketContext'

export default function ProgressIndicator({ progress, mode = 'detailed' }) {
  const [expandedSections, setExpandedSections] = useState({})
  const { progressHistory } = useWebSocket()

  if (!progress) return null

  // Helper functions
  const getIcon = () => {
    switch (progress.type) {
      case 'complete':
        return <CheckCircle className="text-green-400" size={20} />
      case 'error':
        return <XCircle className="text-red-400" size={20} />
      case 'progress':
        return <Loader2 className="text-primary-500 animate-spin" size={20} />
      default:
        return <Info className="text-blue-400" size={20} />
    }
  }

  const getBgColor = () => {
    switch (progress.type) {
      case 'complete':
        return 'bg-green-900/20 border-green-800'
      case 'error':
        return 'bg-red-900/20 border-red-800'
      case 'progress':
        return 'bg-primary-900/20 border-primary-800'
      default:
        return 'bg-blue-900/20 border-blue-800'
    }
  }

  const getTextColor = () => {
    switch (progress.type) {
      case 'complete':
        return 'text-green-400'
      case 'error':
        return 'text-red-400'
      case 'progress':
        return 'text-primary-400'
      default:
        return 'text-blue-400'
    }
  }

  // Simple mode for epic analysis - just show a progress bar with current message
  if (mode === 'simple') {
    return (
      <div className={clsx('border rounded-xl p-4 mb-8', getBgColor())}>
        <div className="flex items-center space-x-3">
          {getIcon()}
          <div className="flex-1">
            <p className={clsx('font-medium', getTextColor())}>
              {progress.type === 'complete' ? 'Analysis Complete' : 'Analyzing Epic'}
            </p>
            {progress.message && (
              <p className="text-sm text-gray-400 mt-1">
                {progress.message}
              </p>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Detailed mode for test generation - show full accordion with history
  const toggleSection = (index) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const getSubstepLabel = (substep) => {
    switch (substep) {
      case 'generation':
        return '🤖 Generation'
      case 'critic_review':
        return '👨‍⚖️ Critic Review'
      case 'fixer':
        return '🔧 Fixer'
      default:
        return substep ? substep.replace(/_/g, ' ') : null
    }
  }

  // Organize messages by substep for consolidated view
  const MAX_HISTORY = 100
  const recentHistory = progressHistory.slice(-MAX_HISTORY)
  const allMessages = progress.step === 'generating' ? [...recentHistory, progress] : [progress]

  // Deduplicate messages by content using Set for O(n) performance
  const seen = new Set()
  const uniqueMessages = allMessages.filter(msg => {
    // Handle null/undefined properties safely
    const substep = msg?.substep || 'unknown'
    const message = msg?.message || ''
    const msgKey = `${substep}:${message}`

    if (seen.has(msgKey)) return false
    seen.add(msgKey)
    return true
  })

  // Group messages by substep
  const messagesBySubstep = uniqueMessages.reduce((acc, msg) => {
    const substep = msg?.substep || 'other'
    if (!acc[substep]) acc[substep] = []
    acc[substep].push(msg)
    return acc
  }, {})

  const getSubstepIcon = (substep, isActive) => {
    if (isActive) {
      return <Loader2 className="text-primary-400 animate-spin" size={16} />
    }
    switch (substep) {
      case 'generation':
        return <span className="text-sm">🤖</span>
      case 'critic_review':
        return <span className="text-sm">👨‍⚖️</span>
      case 'fixer':
        return <span className="text-sm">🔧</span>
      case 'complete':
        return <CheckCircle className="text-green-400" size={16} />
      default:
        return null
    }
  }

  return (
    <div className={clsx('border rounded-xl p-4 mb-8', getBgColor())}>
      <div className="flex items-center space-x-3 mb-4">
        {getIcon()}
        <div>
          <p className={clsx('font-medium', getTextColor())}>
            {progress.type === 'complete' ? 'Generation Complete' : 'Generating Test Cases'}
          </p>
          {progress.step && (
            <p className="text-sm text-gray-400">
              {progress.step.replace(/_/g, ' ')}
            </p>
          )}
        </div>
      </div>

      {/* Consolidated accordion view of all steps */}
      <div className="space-y-2">
        {Object.entries(messagesBySubstep).map(([substep, messages], idx) => {
          const isActive = progress.substep === substep
          const isExpanded = expandedSections[idx] !== false // Default to expanded
          const latestMessage = messages[messages.length - 1]
          const hasMultiple = messages.length > 1

          return (
            <div
              key={substep}
              className={clsx(
                'border rounded-lg transition-all',
                isActive ? 'border-primary-500/50 bg-primary-500/5' : 'border-dark-700 bg-dark-800/50'
              )}
            >
              {/* Section Header */}
              <button
                onClick={() => toggleSection(idx)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-dark-700/50 transition-colors rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {getSubstepIcon(substep, isActive)}
                  <span className={clsx(
                    'font-medium text-sm',
                    isActive ? 'text-primary-400' : 'text-gray-300'
                  )}>
                    {getSubstepLabel(substep)}
                  </span>
                  {hasMultiple && (
                    <span className="text-xs text-gray-500">
                      ({messages.length} updates)
                    </span>
                  )}
                </div>
                {isExpanded ? (
                  <ChevronUp size={16} className="text-gray-400" />
                ) : (
                  <ChevronDown size={16} className="text-gray-400" />
                )}
              </button>

              {/* Section Content */}
              {isExpanded && (
                <div className="px-4 pb-3 space-y-2">
                  {messages.map((msg, msgIdx) => (
                    <div
                      key={msgIdx}
                      className={clsx(
                        'whitespace-pre-wrap break-words overflow-y-auto max-h-96 text-sm',
                        msgIdx === messages.length - 1 ? 'text-gray-300' : 'text-gray-500'
                      )}
                      style={{
                        scrollbarWidth: 'thin',
                        scrollbarColor: 'rgba(255,255,255,0.2) transparent'
                      }}
                    >
                      {msg?.message || ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
