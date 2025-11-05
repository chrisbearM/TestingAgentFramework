import React, { useState } from 'react'
import { Search, Loader2, FileText, Users, CheckCircle, XCircle } from 'lucide-react'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import StrategicOptions from '../components/StrategicOptions'
import ProgressIndicator from '../components/ProgressIndicator'

// Helper function to safely extract text from Jira description
const extractDescription = (description) => {
  if (!description) return ''
  if (typeof description === 'string') return description

  // Handle Atlassian Document Format (ADF)
  if (description.type === 'doc' && description.content) {
    return extractTextFromADF(description)
  }

  return JSON.stringify(description)
}

const extractTextFromADF = (adf) => {
  if (!adf || !adf.content) return ''

  const extractFromNode = (node) => {
    let text = ''

    // Handle text nodes
    if (node.type === 'text' && node.text) {
      return node.text
    }

    // Handle nodes with content arrays
    if (node.content && Array.isArray(node.content)) {
      for (const child of node.content) {
        text += extractFromNode(child)
      }
    }

    // Add line breaks after certain node types
    if (node.type === 'paragraph' || node.type === 'heading') {
      text += '\n'
    } else if (node.type === 'listItem') {
      text = '• ' + text + '\n'
    } else if (node.type === 'codeBlock') {
      text = '\n' + text + '\n'
    } else if (node.type === 'hardBreak') {
      text += '\n'
    }

    return text
  }

  let result = ''
  for (const node of adf.content) {
    result += extractFromNode(node)
  }

  return result.trim()
}

export default function EpicAnalysis() {
  const [epicKey, setEpicKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [epic, setEpic] = useState(null)
  const [options, setOptions] = useState(null)
  const [error, setError] = useState('')
  const { progress, clearProgress } = useWebSocket()

  const handleLoadEpic = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    clearProgress()

    try {
      // Load Epic
      const epicResponse = await api.post('/epics/load', {
        epic_key: epicKey,
        include_attachments: true
      })
      setEpic(epicResponse.data)

      // Analyze Epic with multi-agent system
      const analysisResponse = await api.post(`/epics/${epicKey}/analyze`)
      setOptions(analysisResponse.data)

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load Epic')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-100 mb-2">Epic Analysis</h1>
        <p className="text-gray-400">
          Load an Epic and let our multi-agent AI system propose strategic approaches for test ticket generation
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
        <form onSubmit={handleLoadEpic} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="epicKey" className="block text-sm font-medium text-gray-300 mb-2">
              Epic Key
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                id="epicKey"
                value={epicKey}
                onChange={(e) => setEpicKey(e.target.value.toUpperCase())}
                placeholder="e.g., UEX-17"
                required
                className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Analyze Epic</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-2">
            <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </div>

      {/* Progress Indicator */}
      {progress && <ProgressIndicator progress={progress} />}

      {/* Epic Info */}
      {epic && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-100 mb-1">
                {epic.epic.key}: {epic.epic.fields.summary}
              </h2>
              <p className="text-gray-400">
                {epic.child_count} child {epic.child_count === 1 ? 'ticket' : 'tickets'}
              </p>
            </div>
            <div className="px-3 py-1 bg-primary-500/10 border border-primary-500/20 rounded-full">
              <span className="text-primary-400 text-sm font-medium">{epic.epic.fields.status?.name}</span>
            </div>
          </div>

          {epic.epic.fields.description && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
              <div className="text-gray-400 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {extractDescription(epic.epic.fields.description)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Strategic Options */}
      {options && <StrategicOptions data={options} epicKey={epicKey} />}
    </div>
  )
}
