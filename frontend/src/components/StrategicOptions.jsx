import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronUp, TrendingUp, AlertTriangle, CheckCircle, Star, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'

export default function StrategicOptions({ data, epicKey }) {
  const [expandedOption, setExpandedOption] = useState(0)
  const [selectedOption, setSelectedOption] = useState(null)
  const [generating, setGenerating] = useState(false)
  const navigate = useNavigate()
  const { progress } = useWebSocket()

  // Use epic_key from data if epicKey prop is not provided
  const actualEpicKey = epicKey || data?.epic_key

  console.log('=== STRATEGIC OPTIONS COMPONENT ===')
  console.log('Received data:', data)
  console.log('Epic key prop:', epicKey)
  console.log('Epic key from data:', data?.epic_key)
  console.log('Using epic key:', actualEpicKey)

  if (!data || !data.options || !Array.isArray(data.options) || data.options.length === 0) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-xl p-6">
        <p className="text-red-400">Error: Invalid strategic options data</p>
      </div>
    )
  }

  const handleGenerateTestTickets = async () => {
    if (selectedOption === null) return

    setGenerating(true)
    try {
      console.log('Generating test tickets for epic:', actualEpicKey, 'option:', selectedOption)

      // Pass the full option data to avoid re-analysis on the backend
      const selectedOptionData = data.options[selectedOption]

      const response = await api.post('/test-tickets/generate', {
        epic_key: actualEpicKey,
        selected_option_index: selectedOption,
        selected_option: selectedOptionData  // Pass the full option data
      })

      console.log('Test tickets generated:', response.data)

      // Navigate to test tickets page with the epic key and context
      navigate(`/test-tickets?epic=${actualEpicKey}`, {
        state: {
          testTickets: response.data.test_tickets,
          validation: response.data.validation || null,
          coverageReview: response.data.coverage_review || null,
          epicKey: actualEpicKey,
          epicData: response.data.epic_data || null,
          childTickets: response.data.child_tickets || [],
          existingTestTickets: response.data.existing_test_tickets || []
        }
      })
    } catch (error) {
      console.error('Failed to generate test tickets:', error)
      const errorMsg = error.response?.data?.detail || error.message
      alert(`Failed to generate test tickets: ${errorMsg}`)
    } finally {
      setGenerating(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-400'
    if (score >= 6) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreBg = (score) => {
    if (score >= 8) return 'bg-green-500/10 border-green-500/30'
    if (score >= 6) return 'bg-yellow-500/10 border-yellow-500/30'
    return 'bg-red-500/10 border-red-500/30'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Strategic Options</h2>
          <p className="text-gray-400 mt-1">
            Our multi-agent system has analyzed the Epic and proposes 3 strategic approaches
          </p>
        </div>
        <div className="px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-lg">
          <p className="text-sm text-primary-400 font-medium">
            Generated {new Date(data.generated_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-4">
        {data.options.map((option, index) => {
          const isExpanded = expandedOption === index
          const isSelected = selectedOption === index
          const evaluation = option.evaluation || {}
          const overallScore = evaluation.overall || 0

          const scores = {
            testability: evaluation.testability || 0,
            coverage: evaluation.coverage || 0,
            manageability: evaluation.manageability || 0,
            independence: evaluation.independence || 0,
            parallel_execution: evaluation.parallel_execution || 0
          }

          return (
            <div
              key={index}
              className={clsx(
                'bg-dark-900 border rounded-xl transition-all overflow-hidden',
                isSelected
                  ? 'border-primary-500 shadow-nebula-lg'
                  : 'border-dark-800 hover:border-dark-700'
              )}
            >
              {/* Header */}
              <div
                className="p-6 cursor-pointer"
                onClick={() => setExpandedOption(isExpanded ? null : index)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-xl font-semibold text-gray-100">
                        Option {index + 1}: {option.strategy}
                      </h3>
                      {evaluation.recommended && (
                        <div className="px-2 py-1 bg-yellow-500/10 border border-yellow-500/30 rounded-md flex items-center space-x-1">
                          <Star size={14} className="text-yellow-400 fill-yellow-400" />
                          <span className="text-xs text-yellow-400 font-medium">Recommended</span>
                        </div>
                      )}
                    </div>
                    <p className="text-gray-400">{option.description}</p>
                  </div>

                  <div className="flex items-center space-x-4 ml-4">
                    {/* Score */}
                    <div className={clsx('px-4 py-2 border rounded-lg', getScoreBg(overallScore))}>
                      <div className="flex items-center space-x-2">
                        <TrendingUp size={18} className={getScoreColor(overallScore)} />
                        <span className={clsx('text-2xl font-bold', getScoreColor(overallScore))}>
                          {overallScore.toFixed(1)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">Overall Score</p>
                    </div>

                    {/* Expand Button */}
                    <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors">
                      {isExpanded ? (
                        <ChevronUp size={20} className="text-gray-400" />
                      ) : (
                        <ChevronDown size={20} className="text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Quick Stats */}
                {!isExpanded && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {Object.entries(scores).map(([key, value]) => (
                      <div key={key} className="px-3 py-1 bg-dark-800 rounded-md">
                        <span className="text-xs text-gray-400 capitalize">
                          {key.replace(/_/g, ' ')}:{' '}
                        </span>
                        <span className={clsx('text-xs font-medium', getScoreColor(value))}>
                          {value.toFixed(1)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="border-t border-dark-800 p-6 space-y-6">
                  {/* Evaluation Scores */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Evaluation Scores</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {Object.entries(scores).map(([key, value]) => (
                        <div key={key} className="bg-dark-800 rounded-lg p-3">
                          <p className="text-xs text-gray-400 mb-1 capitalize">
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className={clsx('text-2xl font-bold', getScoreColor(value))}>
                            {value.toFixed(1)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Rationale */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-2">Rationale</h4>
                    <p className="text-gray-400 text-sm">{option.rationale}</p>
                  </div>

                  {/* Advantages & Disadvantages */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {option.advantages && Array.isArray(option.advantages) && (
                      <div className="bg-dark-800 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-3">
                          <CheckCircle size={18} className="text-green-400" />
                          <h4 className="text-sm font-semibold text-gray-300">Advantages</h4>
                        </div>
                        <ul className="space-y-2">
                          {option.advantages.map((adv, i) => (
                            <li key={i} className="flex items-start space-x-2">
                              <span className="text-green-400 text-xs mt-1">✓</span>
                              <span className="text-gray-400 text-sm">{adv}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {option.disadvantages && Array.isArray(option.disadvantages) && (
                      <div className="bg-dark-800 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-3">
                          <AlertTriangle size={18} className="text-yellow-400" />
                          <h4 className="text-sm font-semibold text-gray-300">Disadvantages</h4>
                        </div>
                        <ul className="space-y-2">
                          {option.disadvantages.map((dis, i) => (
                            <li key={i} className="flex items-start space-x-2">
                              <span className="text-yellow-400 text-xs mt-1">!</span>
                              <span className="text-gray-400 text-sm">{dis}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Test Tickets Preview */}
                  {option.test_tickets && Array.isArray(option.test_tickets) && option.test_tickets.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-3">
                        Proposed Test Tickets ({option.test_tickets.length})
                      </h4>
                      <div className="space-y-2">
                        {option.test_tickets.slice(0, 3).map((ticket, i) => (
                          <div key={i} className="bg-dark-800 rounded-lg p-3">
                            <p className="font-medium text-gray-200 text-sm">{ticket.title || ticket.summary}</p>
                            {ticket.description && (
                              <p className="text-xs text-gray-400 mt-1 line-clamp-2">{ticket.description}</p>
                            )}
                          </div>
                        ))}
                        {option.test_tickets.length > 3 && (
                          <p className="text-sm text-gray-400 text-center py-2">
                            +{option.test_tickets.length - 3} more test tickets
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Recommendation */}
                  {evaluation.recommendation && (
                    <div className="bg-primary-900/20 border border-primary-800/30 rounded-lg p-4">
                      <h4 className="text-sm font-semibold text-primary-300 mb-2">AI Recommendation</h4>
                      <p className="text-gray-400 text-sm">{evaluation.recommendation}</p>
                    </div>
                  )}

                  {/* Select Button */}
                  <div className="flex justify-end pt-4 border-t border-dark-800">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedOption(isSelected ? null : index)
                      }}
                      className={clsx(
                        'px-6 py-3 rounded-lg font-medium transition-colors',
                        isSelected
                          ? 'bg-dark-800 text-gray-400 hover:bg-dark-700'
                          : 'bg-primary-500 text-white hover:bg-primary-600 shadow-nebula'
                      )}
                    >
                      {isSelected ? 'Deselect Option' : 'Select This Option'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Generate Button */}
      {selectedOption !== null && (
        <div className="bg-dark-900 border border-primary-500 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-100 mb-1">Ready to Generate Test Tickets?</h3>
              <p className="text-gray-400">
                You've selected Option {selectedOption + 1}. Click generate to create test tickets based on this strategy.
              </p>
            </div>
            <button
              onClick={handleGenerateTestTickets}
              disabled={generating}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
            >
              {generating ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Generating...</span>
                </>
              ) : (
                <span>Generate Test Tickets</span>
              )}
            </button>
          </div>

          {/* Show progress if generating */}
          {generating && progress && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg">
              <p className="text-sm text-gray-300">{progress.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
