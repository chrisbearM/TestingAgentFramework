import React, { useState } from 'react'
import { Search, Loader2, TestTube2, XCircle, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import TestCaseEditor from '../components/TestCaseEditor'
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

export default function TestGeneration() {
  const [ticketKey, setTicketKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [ticket, setTicket] = useState(null)
  const [assessment, setAssessment] = useState(null)
  const [testCases, setTestCases] = useState(null)
  const [error, setError] = useState('')
  const { progress, clearProgress } = useWebSocket()

  const handleLoadTicket = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setAssessment(null)
    setTestCases(null)
    clearProgress()

    try {
      const ticketResponse = await api.get(`/tickets/${ticketKey}`)
      setTicket(ticketResponse.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ticket')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeTicket = async () => {
    setError('')
    setAnalyzing(true)
    clearProgress()

    try {
      const response = await api.post(`/tickets/${ticketKey}/analyze`)
      setAssessment(response.data.assessment)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze ticket')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleGenerateTestCases = async () => {
    setError('')
    setGenerating(true)
    clearProgress()

    try {
      const response = await api.post('/test-cases/generate', {
        ticket_key: ticketKey,
        include_attachments: true
      })

      setTestCases(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate test cases')
    } finally {
      setGenerating(false)
    }
  }

  const getScoreBadgeColor = (score) => {
    switch (score) {
      case 'Excellent':
        return 'bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-green-500/50 text-green-400'
      case 'Good':
        return 'bg-gradient-to-r from-yellow-900/40 to-amber-900/40 border-yellow-500/50 text-yellow-400'
      case 'Poor':
        return 'bg-gradient-to-r from-red-900/40 to-rose-900/40 border-red-500/50 text-red-400'
      default:
        return 'bg-dark-800 border-dark-700 text-gray-400'
    }
  }

  const canGenerateTestCases = assessment && ['Excellent', 'Good'].includes(assessment.score)

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-100 mb-2">Test Case Generation</h1>
        <p className="text-gray-400">
          Load a ticket, analyze its readiness, then generate comprehensive test cases
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
        <form onSubmit={handleLoadTicket} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="ticketKey" className="block text-sm font-medium text-gray-300 mb-2">
              Ticket Key
            </label>
            <div className="relative">
              <TestTube2 className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                id="ticketKey"
                value={ticketKey}
                onChange={(e) => setTicketKey(e.target.value.toUpperCase())}
                placeholder="e.g., UEX-326"
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
                  <span>Loading...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Load Ticket</span>
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

      {/* Ticket Info */}
      {ticket && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-100 mb-1">
                {ticket.key}: {ticket.fields.summary}
              </h2>
              <p className="text-gray-400">
                {ticket.fields.issuetype?.name} • {ticket.fields.priority?.name}
              </p>
            </div>
            <div className="px-3 py-1 bg-primary-500/10 border border-primary-500/20 rounded-full">
              <span className="text-primary-400 text-sm font-medium">{ticket.fields.status?.name}</span>
            </div>
          </div>

          {ticket.fields.description && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
              <div className="text-gray-400 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
                {extractDescription(ticket.fields.description)}
              </div>
            </div>
          )}

          {/* Analyze Button */}
          {!assessment && (
            <div className="mt-6">
              <button
                onClick={handleAnalyzeTicket}
                disabled={analyzing}
                className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-purple-800 disabled:to-indigo-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all shadow-lg flex items-center justify-center space-x-2"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="animate-spin" size={18} />
                    <span>Analyzing Ticket Readiness...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <span>Analyze Ticket Readiness</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Assessment Results */}
      {assessment && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-100 mb-6">Readiness Assessment</h2>

          {/* Score Card */}
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-2">Readiness Score</h3>
                <p className="text-4xl font-bold text-gray-100">{assessment.confidence}%</p>
              </div>
              <div className={`px-6 py-3 rounded-full border-2 font-bold text-lg ${getScoreBadgeColor(assessment.score)}`}>
                {assessment.score}
              </div>
            </div>
          </div>

          {/* Summary */}
          {assessment.summary && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3">Summary</h3>
              <p className="text-gray-300">{assessment.summary}</p>
            </div>
          )}

          {/* Strengths */}
          {assessment.strengths && assessment.strengths.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center space-x-2">
                <CheckCircle2 className="text-green-500" size={20} />
                <span>Strengths</span>
              </h3>
              <ul className="list-disc list-inside space-y-2">
                {assessment.strengths.map((strength, idx) => (
                  <li key={idx} className="text-gray-300">{strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Elements */}
          {assessment.missing_elements && assessment.missing_elements.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center space-x-2">
                <XCircle className="text-red-500" size={20} />
                <span>Missing Elements</span>
              </h3>
              <ul className="list-disc list-inside space-y-2">
                {assessment.missing_elements.map((missing, idx) => (
                  <li key={idx} className="text-gray-300">{missing}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {assessment.recommendations && assessment.recommendations.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center space-x-2">
                <AlertTriangle className="text-yellow-500" size={20} />
                <span>Recommendations</span>
              </h3>
              <ul className="list-disc list-inside space-y-2">
                {assessment.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-gray-300">{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Questions for Author */}
          {assessment.questions_for_author && assessment.questions_for_author.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3">Questions for Author</h3>
              <ol className="list-decimal list-inside space-y-2">
                {assessment.questions_for_author.map((question, idx) => (
                  <li key={idx} className="text-gray-300">{question}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Ideal Ticket Example */}
          {assessment.ideal_ticket_example && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-200 mb-3">Ideal Ticket Example</h3>
              <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">{assessment.ideal_ticket_example}</pre>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleAnalyzeTicket}
              disabled={analyzing}
              className="px-6 py-3 bg-dark-700 hover:bg-dark-600 disabled:bg-dark-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              {analyzing ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Re-analyzing...</span>
                </>
              ) : (
                <span>Re-analyze Ticket</span>
              )}
            </button>

            <button
              onClick={handleGenerateTestCases}
              disabled={!canGenerateTestCases || generating}
              className={`flex-1 px-6 py-3 font-medium rounded-lg transition-all flex items-center justify-center space-x-2 ${
                canGenerateTestCases
                  ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg'
                  : 'bg-dark-700 text-gray-500 cursor-not-allowed'
              }`}
              title={!canGenerateTestCases ? 'Ticket must score "Excellent" or "Good" to generate test cases' : ''}
            >
              {generating ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Generating Test Cases...</span>
                </>
              ) : (
                <>
                  <TestTube2 size={18} />
                  <span>Generate Test Cases</span>
                </>
              )}
            </button>
          </div>

          {!canGenerateTestCases && (
            <div className="mt-4 p-4 bg-red-900/20 border border-red-800 rounded-lg">
              <p className="text-sm text-red-400">
                <strong>Cannot proceed:</strong> Ticket scored "{assessment.score}". Please improve the ticket based on the recommendations above before generating test cases.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Test Cases */}
      {testCases && (
        <TestCaseEditor
          testCases={testCases.test_cases}
          ticketInfo={testCases.ticket_info}
        />
      )}
    </div>
  )
}
