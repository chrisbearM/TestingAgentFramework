import React from 'react'
import { Loader2, CheckCircle, XCircle, Info } from 'lucide-react'
import clsx from 'clsx'

export default function ProgressIndicator({ progress }) {
  if (!progress) return null

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

  return (
    <div className={clsx('border rounded-xl p-4 mb-8', getBgColor())}>
      <div className="flex items-center space-x-3">
        {getIcon()}
        <div className="flex-1">
          <p className={clsx('font-medium', getTextColor())}>{progress.message}</p>
          {progress.step && (
            <p className="text-sm text-gray-400 mt-0.5">
              Step: {progress.step.replace(/_/g, ' ')}
            </p>
          )}
        </div>
      </div>

      {/* AI Process Steps */}
      {progress.step === 'generating' && progress.substep && (
        <div className="mt-4 flex items-center space-x-2">
          <div className="flex-1 flex items-center space-x-2">
            {/* Generation */}
            <div className={clsx(
              'flex items-center space-x-2 px-3 py-2 rounded-lg flex-1 transition-all',
              progress.substep === 'generation'
                ? 'bg-primary-500/20 border border-primary-500/50'
                : progress.substep === 'critic_review' || progress.substep === 'fixer'
                ? 'bg-green-900/20 border border-green-500/50'
                : 'bg-dark-800 border border-dark-700'
            )}>
              <span className="text-xs">🤖</span>
              <span className={clsx(
                'text-sm font-medium',
                progress.substep === 'generation'
                  ? 'text-primary-400'
                  : progress.substep === 'critic_review' || progress.substep === 'fixer'
                  ? 'text-green-400'
                  : 'text-gray-500'
              )}>
                Generation
              </span>
              {progress.substep === 'generation' && (
                <Loader2 className="text-primary-400 animate-spin ml-auto" size={14} />
              )}
            </div>

            {/* Critic Review */}
            <div className={clsx(
              'flex items-center space-x-2 px-3 py-2 rounded-lg flex-1 transition-all',
              progress.substep === 'critic_review'
                ? 'bg-primary-500/20 border border-primary-500/50'
                : progress.substep === 'fixer'
                ? 'bg-green-900/20 border border-green-500/50'
                : 'bg-dark-800 border border-dark-700'
            )}>
              <span className="text-xs">👨‍⚖️</span>
              <span className={clsx(
                'text-sm font-medium',
                progress.substep === 'critic_review'
                  ? 'text-primary-400'
                  : progress.substep === 'fixer'
                  ? 'text-green-400'
                  : 'text-gray-500'
              )}>
                Critic Review
              </span>
              {progress.substep === 'critic_review' && (
                <Loader2 className="text-primary-400 animate-spin ml-auto" size={14} />
              )}
            </div>

            {/* Fixer */}
            <div className={clsx(
              'flex items-center space-x-2 px-3 py-2 rounded-lg flex-1 transition-all',
              progress.substep === 'fixer'
                ? 'bg-primary-500/20 border border-primary-500/50'
                : 'bg-dark-800 border border-dark-700'
            )}>
              <span className="text-xs">🔧</span>
              <span className={clsx(
                'text-sm font-medium',
                progress.substep === 'fixer' ? 'text-primary-400' : 'text-gray-500'
              )}>
                Fixer
              </span>
              {progress.substep === 'fixer' && (
                <Loader2 className="text-primary-400 animate-spin ml-auto" size={14} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
