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

  return (
    <div className={clsx('border rounded-xl p-4 mb-8 flex items-center space-x-3', getBgColor())}>
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
  )
}
