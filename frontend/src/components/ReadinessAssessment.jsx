import React, { useState } from 'react'
import { ChevronDown, ChevronUp, AlertTriangle, AlertCircle, Info, CheckCircle, XCircle, HelpCircle, Sparkles, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import TicketImprovementComparison from './TicketImprovementComparison'

export default function ReadinessAssessment({ assessment, epicData, itemType = 'Epic' }) {
  const [expandedPriority, setExpandedPriority] = useState('Critical')
  const [improving, setImproving] = useState(false)
  const [improvement, setImprovement] = useState(null)
  const [showComparison, setShowComparison] = useState(false)

  if (!assessment || !assessment.prioritized_questions) {
    return null
  }

  const { prioritized_questions, summary } = assessment

  const handleImprove = async () => {
    if (!epicData) return

    setImproving(true)
    try {
      // Use all critical and important questions for improvement
      const relevantQuestions = prioritized_questions.filter(
        q => q.priority === 'Critical' || q.priority === 'Important'
      )

      const response = await api.post('/tickets/improve', {
        ticket: {
          key: epicData.key,
          summary: epicData.summary,
          description: epicData.description
        },
        questions: relevantQuestions,
        epic_context: null
      })

      setImprovement(response.data)
      setShowComparison(true)
    } catch (error) {
      console.error(`Failed to improve ${itemType}:`, error)
      alert(`Failed to improve ${itemType}: ${error.response?.data?.detail || error.message}`)
    } finally {
      setImproving(false)
    }
  }

  // Group questions by priority
  const criticalQuestions = prioritized_questions.filter(q => q.priority === 'Critical')
  const importantQuestions = prioritized_questions.filter(q => q.priority === 'Important')
  const niceToHaveQuestions = prioritized_questions.filter(q => q.priority === 'Nice-to-have')

  const getReadinessColor = (level) => {
    switch (level) {
      case 'High':
        return 'text-green-400'
      case 'Medium':
        return 'text-yellow-400'
      case 'Low':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getReadinessIcon = (level) => {
    switch (level) {
      case 'High':
        return <CheckCircle size={32} className="text-green-400" />
      case 'Medium':
        return <AlertCircle size={32} className="text-yellow-400" />
      case 'Low':
        return <XCircle size={32} className="text-red-400" />
      default:
        return <HelpCircle size={32} className="text-gray-400" />
    }
  }

  const getPriorityConfig = (priority) => {
    switch (priority) {
      case 'Critical':
        return {
          icon: AlertTriangle,
          color: 'text-red-400',
          bg: 'bg-red-900/20',
          border: 'border-red-800',
          questions: criticalQuestions
        }
      case 'Important':
        return {
          icon: AlertCircle,
          color: 'text-yellow-400',
          bg: 'bg-yellow-900/20',
          border: 'border-yellow-800',
          questions: importantQuestions
        }
      case 'Nice-to-have':
        return {
          icon: Info,
          color: 'text-blue-400',
          bg: 'bg-blue-900/20',
          border: 'border-blue-800',
          questions: niceToHaveQuestions
        }
      default:
        return {
          icon: HelpCircle,
          color: 'text-gray-400',
          bg: 'bg-gray-900/20',
          border: 'border-gray-800',
          questions: []
        }
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Readiness Assessment</h2>
          <p className="text-gray-400 mt-1">
            Questions to clarify before proceeding with test ticket generation
          </p>
        </div>
        {epicData && (
          <button
            onClick={handleImprove}
            disabled={improving}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            {improving ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Improving...</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Improve {itemType}</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Overall Readiness Card */}
      <div className="bg-dark-900 border border-dark-800 rounded-xl p-6">
        <div className="flex items-start space-x-4">
          {getReadinessIcon(summary.overall_readiness)}
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-xl font-semibold text-gray-100">Overall Readiness</h3>
              <span className={clsx('text-2xl font-bold', getReadinessColor(summary.overall_readiness))}>
                {summary.overall_readiness}
              </span>
            </div>
            <p className="text-gray-400 text-sm mb-4">
              {summary.readiness_rationale}
            </p>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-dark-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Total Questions</p>
                <p className="text-2xl font-bold text-gray-200">{summary.total_questions}</p>
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Critical</p>
                <p className="text-2xl font-bold text-red-400">{summary.critical_count}</p>
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Important</p>
                <p className="text-2xl font-bold text-yellow-400">{summary.important_count}</p>
              </div>
              <div className="bg-dark-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Nice-to-have</p>
                <p className="text-2xl font-bold text-blue-400">{summary.nice_to_have_count}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Questions by Priority */}
      {['Critical', 'Important', 'Nice-to-have'].map(priority => {
        const config = getPriorityConfig(priority)
        const Icon = config.icon
        const isExpanded = expandedPriority === priority

        if (config.questions.length === 0) return null

        return (
          <div
            key={priority}
            className={clsx('border rounded-xl overflow-hidden', config.border, config.bg)}
          >
            {/* Priority Header */}
            <div
              className="p-6 cursor-pointer hover:bg-dark-800/50 transition-colors"
              onClick={() => setExpandedPriority(isExpanded ? null : priority)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Icon size={24} className={config.color} />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-100">
                      {priority} Priority
                    </h3>
                    <p className="text-sm text-gray-400">
                      {config.questions.length} {config.questions.length === 1 ? 'question' : 'questions'}
                    </p>
                  </div>
                </div>
                <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors">
                  {isExpanded ? (
                    <ChevronUp size={20} className="text-gray-400" />
                  ) : (
                    <ChevronDown size={20} className="text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            {/* Questions List */}
            {isExpanded && (
              <div className="border-t border-dark-800 p-6 space-y-4">
                {config.questions.map((question, index) => (
                  <div
                    key={index}
                    className="bg-dark-900 border border-dark-800 rounded-lg p-4"
                  >
                    {/* Question Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className={clsx('text-xs font-semibold px-2 py-1 rounded', config.bg, config.color)}>
                            Score: {question.priority_score}/10
                          </span>
                          <span className="text-xs text-gray-400 px-2 py-1 bg-dark-800 rounded">
                            {question.category}
                          </span>
                        </div>
                        <h4 className="text-gray-100 font-medium">{question.question}</h4>
                      </div>
                    </div>

                    {/* Question Details */}
                    <div className="space-y-3">
                      {/* Rationale */}
                      {question.rationale && (
                        <div className="pl-4 border-l-2 border-gray-700">
                          <p className="text-xs text-gray-400 mb-1">Why this matters:</p>
                          <p className="text-sm text-gray-300">{question.rationale}</p>
                        </div>
                      )}

                      {/* Impact */}
                      {question.impact && (
                        <div className="pl-4 border-l-2 border-yellow-500/30">
                          <p className="text-xs text-gray-400 mb-1">Impact if not answered:</p>
                          <p className="text-sm text-yellow-300/90">{question.impact}</p>
                        </div>
                      )}

                      {/* Recommendation */}
                      {question.recommendation && (
                        <div className="pl-4 border-l-2 border-green-500/30">
                          <p className="text-xs text-gray-400 mb-1">Recommendation:</p>
                          <p className="text-sm text-green-300/90">{question.recommendation}</p>
                        </div>
                      )}

                      {/* Related Tickets */}
                      {question.related_tickets && question.related_tickets.length > 0 && (
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-400">Related:</span>
                          {question.related_tickets.map((ticket, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-1 bg-dark-800 border border-dark-700 rounded text-primary-400"
                            >
                              {ticket}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}

      {/* Ticket Improvement Comparison Modal */}
      {showComparison && improvement && epicData && (
        <TicketImprovementComparison
          original={{
            key: epicData.key,
            summary: epicData.summary,
            description: epicData.description
          }}
          improved={improvement.improved_ticket}
          improvements={improvement.improvements_made}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  )
}
