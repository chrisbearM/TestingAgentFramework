import React, { useState } from 'react'
import { Search, Loader2, Sparkles, Copy, Check, AlertCircle, TrendingUp, ArrowRight, CheckCircle } from 'lucide-react'
import api from '../api/client'
import clsx from 'clsx'

export default function TicketImprover() {
  const [ticketKey, setTicketKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [ticket, setTicket] = useState(null)
  const [improvedTicket, setImprovedTicket] = useState(null)
  const [improvements, setImprovements] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const handleFetchTicket = async () => {
    if (!ticketKey.trim()) {
      setError('Please enter a ticket key')
      return
    }

    setLoading(true)
    setError('')
    setTicket(null)
    setImprovedTicket(null)
    setImprovements(null)

    try {
      // Fetch the ticket
      const ticketResponse = await api.get(`/tickets/${ticketKey.trim()}`)
      const ticketData = ticketResponse.data

      // Normalize ticket data for display
      // Handle description - might be a string or ADF object
      let description = ticketData.fields?.description || ''
      if (typeof description === 'object' && description !== null) {
        // If description is still an ADF object, show a message
        // (backend should convert this, but handle it gracefully)
        description = '[Description in unsupported format - please contact support]'
      }

      const normalizedTicket = {
        key: ticketData.key,
        summary: ticketData.fields?.summary || '',
        description: description,
        acceptance_criteria: ticketData.acceptance_criteria || ''
      }

      setTicket(normalizedTicket)

      // Improve the ticket
      const improveResponse = await api.post(`/tickets/${ticketKey.trim()}/improve`)

      console.log('Improve Response:', improveResponse.data)
      console.log('Improved Ticket Keys:', improveResponse.data.improved_ticket ? Object.keys(improveResponse.data.improved_ticket) : 'NO IMPROVED_TICKET')
      console.log('Out of Scope:', improveResponse.data.improved_ticket?.out_of_scope)

      if (improveResponse.data.success) {
        setImprovedTicket(improveResponse.data.improved_ticket)
        setImprovements(improveResponse.data.improvements_made)
      } else {
        setError('Failed to improve ticket')
      }
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to fetch or improve ticket')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleFetchTicket()
    }
  }

  const handleCopyImproved = () => {
    if (!improvedTicket) return

    // Format acceptance criteria based on format
    const formatACs = () => {
      if (improvedTicket.acceptance_criteria_grouped) {
        // New grouped format
        return improvedTicket.acceptance_criteria_grouped
          .map(cat => `\n### ${cat.category_name}\n${cat.criteria.map(ac => `- ${ac}`).join('\n')}`)
          .join('\n')
      } else if (improvedTicket.acceptance_criteria) {
        // Old flat format
        if (Array.isArray(improvedTicket.acceptance_criteria)) {
          return improvedTicket.acceptance_criteria.map((ac, i) => `${i + 1}. ${ac}`).join('\n')
        } else {
          return improvedTicket.acceptance_criteria
        }
      }
      return 'None'
    }

    const improvedText = `
Summary: ${improvedTicket.summary}

Description:
${improvedTicket.description}

Acceptance Criteria:
${formatACs()}

${improvedTicket.edge_cases && improvedTicket.edge_cases.length > 0 ? `Edge Cases:\n${improvedTicket.edge_cases.map((ec) => `- ${ec}`).join('\n')}\n` : ''}
${improvedTicket.error_scenarios && improvedTicket.error_scenarios.length > 0 ? `Error Scenarios:\n${improvedTicket.error_scenarios.map((es) => `- ${es}`).join('\n')}\n` : ''}
${improvedTicket.technical_notes ? `Technical Suggestions:\n${improvedTicket.technical_notes}\n` : ''}
${improvedTicket.testing_notes ? `Testing Suggestions:\n${improvedTicket.testing_notes}\n` : ''}
${improvedTicket.out_of_scope && improvedTicket.out_of_scope.length > 0 ? `Out of Scope:\n${improvedTicket.out_of_scope.map((item) => `- ${item}`).join('\n')}` : ''}
    `.trim()

    navigator.clipboard.writeText(improvedText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatAcceptanceCriteria = (criteria) => {
    if (!criteria) return []
    if (Array.isArray(criteria)) return criteria
    // If it's a string, split by newlines and filter empty lines
    return criteria.split('\n').filter(line => line.trim())
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-dark-900 border border-dark-800 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Sparkles className="text-purple-400" size={32} />
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Ticket Improver</h1>
            <p className="text-gray-400 text-sm">Enhance Jira tickets with clearer acceptance criteria, edge cases, and comprehensive details</p>
          </div>
        </div>

        {/* Search Input */}
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={ticketKey}
              onChange={(e) => setTicketKey(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter ticket key (e.g., PROJ-123)"
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500"
            />
          </div>
          <button
            onClick={handleFetchTicket}
            disabled={loading || !ticketKey.trim()}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>Improving...</span>
              </>
            ) : (
              <>
                <Search size={20} />
                <span>Improve Ticket</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start space-x-3">
            <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {improvedTicket && (
        <div className="space-y-6">
          {/* Quality Increase Badge */}
          {improvedTicket.quality_increase && (
            <div className="bg-green-900/20 border border-green-800 rounded-lg p-4 flex items-center space-x-3">
              <CheckCircle className="text-green-400" size={24} />
              <div className="flex-1">
                <p className="text-green-400 font-semibold">
                  Estimated Quality Increase: +{improvedTicket.quality_increase}%
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  This improvement addresses key gaps and enhances clarity
                </p>
              </div>
            </div>
          )}

          {/* Improvements Made */}
          {improvements && improvements.length > 0 && (
            <div className="bg-dark-900 border border-dark-800 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-gray-100 mb-4">Improvements Made</h2>
              <div className="space-y-3">
                {improvements.map((improvement, index) => (
                  <div key={index} className="bg-dark-800 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <ArrowRight className="text-primary-400 flex-shrink-0 mt-1" size={18} />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm font-semibold text-primary-400">
                            {improvement.area}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300 mb-2">{improvement.change}</p>
                        <p className="text-xs text-gray-400 italic">{improvement.rationale}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Original Ticket */}
            <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden">
              <div className="bg-dark-800 px-4 py-3 border-b border-dark-700">
                <h3 className="font-semibold text-gray-300">Original Ticket</h3>
              </div>
              <div className="p-4 space-y-4">
                {/* Summary */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2">SUMMARY</h4>
                  <p className="text-gray-300">{ticket?.summary}</p>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2">DESCRIPTION</h4>
                  <p className="text-gray-400 text-sm whitespace-pre-wrap">
                    {ticket?.description || 'No description provided'}
                  </p>
                </div>

                {/* Original Acceptance Criteria */}
                {ticket?.acceptance_criteria && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">ACCEPTANCE CRITERIA</h4>
                    <p className="text-gray-400 text-sm whitespace-pre-wrap">
                      {ticket.acceptance_criteria}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Improved Ticket */}
            <div className="bg-gradient-to-br from-green-900/20 to-primary-900/20 border border-green-800/50 rounded-xl overflow-hidden">
              <div className="bg-green-900/30 px-4 py-3 border-b border-green-800/50 flex items-center justify-between">
                <h3 className="font-semibold text-green-300">Improved Ticket</h3>
                <button
                  onClick={handleCopyImproved}
                  className="px-3 py-1 bg-green-800/30 hover:bg-green-800/50 border border-green-700/50 rounded-lg transition-colors flex items-center space-x-2"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-green-400" />
                      <span className="text-xs text-green-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} className="text-green-400" />
                      <span className="text-xs text-green-400">Copy</span>
                    </>
                  )}
                </button>
              </div>
              <div className="p-4 space-y-4">
                {/* Summary */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2">SUMMARY</h4>
                  <p className="text-green-300 font-medium">{improvedTicket.summary}</p>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2">DESCRIPTION</h4>
                  <p className="text-gray-300 text-sm whitespace-pre-wrap">
                    {improvedTicket.description}
                  </p>
                </div>

                {/* Acceptance Criteria - Grouped or Flat */}
                {(improvedTicket.acceptance_criteria_grouped || improvedTicket.acceptance_criteria) && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-3">ACCEPTANCE CRITERIA</h4>
                    {improvedTicket.acceptance_criteria_grouped ? (
                      // New grouped format
                      <div className="space-y-4">
                        {improvedTicket.acceptance_criteria_grouped.map((category, idx) => (
                          <div key={idx} className="bg-dark-800/50 rounded-lg p-3 border border-dark-700">
                            <h5 className="text-xs font-semibold text-primary-400 mb-2">{category.category_name}</h5>
                            <ul className="space-y-2">
                              {category.criteria.map((ac, i) => (
                                <li key={i} className="flex items-start space-x-2">
                                  <CheckCircle size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                                  <span className="text-sm text-gray-300">{ac}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    ) : (
                      // Old flat format (backward compatibility)
                      <ul className="space-y-2">
                        {formatAcceptanceCriteria(improvedTicket.acceptance_criteria).map((ac, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <CheckCircle size={16} className="text-green-400 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-300">{ac}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Edge Cases */}
                {improvedTicket.edge_cases && improvedTicket.edge_cases.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">EDGE CASES</h4>
                    <ul className="space-y-1">
                      {improvedTicket.edge_cases.map((ec, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-yellow-400 text-xs mt-1">▸</span>
                          <span className="text-sm text-gray-400">{ec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Error Scenarios */}
                {improvedTicket.error_scenarios && improvedTicket.error_scenarios.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">ERROR SCENARIOS</h4>
                    <ul className="space-y-1">
                      {improvedTicket.error_scenarios.map((es, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-red-400 text-xs mt-1">▸</span>
                          <span className="text-sm text-gray-400">{es}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Technical Suggestions */}
                {improvedTicket.technical_notes && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">TECHNICAL SUGGESTIONS</h4>
                    <p className="text-sm text-gray-400 whitespace-pre-wrap">{improvedTicket.technical_notes}</p>
                  </div>
                )}

                {/* Testing Suggestions */}
                {improvedTicket.testing_notes && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">TESTING SUGGESTIONS</h4>
                    <p className="text-sm text-gray-400 whitespace-pre-wrap">{improvedTicket.testing_notes}</p>
                  </div>
                )}

                {/* Out of Scope */}
                {improvedTicket.out_of_scope && improvedTicket.out_of_scope.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">OUT OF SCOPE</h4>
                    <ul className="space-y-1">
                      {improvedTicket.out_of_scope.map((item, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-gray-400 text-xs mt-1">▸</span>
                          <span className="text-sm text-gray-400">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer with Copy Button */}
          <div className="flex justify-end">
            <button
              onClick={handleCopyImproved}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <Copy size={18} />
              <span>Copy Improved Ticket</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
