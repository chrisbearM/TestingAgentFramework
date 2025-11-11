import React, { useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, ChevronDown, ChevronUp, Copy, FileText } from 'lucide-react'
import clsx from 'clsx'

export default function ValidationReport({ validation, testTickets, epicKey, onRegenerate }) {
  const [expandedSection, setExpandedSection] = useState('coverage')

  if (!validation) return null

  const { coverage, overlaps } = validation

  // Calculate statistics
  const totalChildTickets = coverage?.total_child_tickets || 0
  const coveredTickets = coverage?.covered_tickets || []
  const uncoveredTickets = coverage?.uncovered_tickets || []
  const coveragePercentage = totalChildTickets > 0
    ? Math.round((coveredTickets.length / totalChildTickets) * 100)
    : 0

  const totalOverlaps = overlaps?.duplicates?.length || 0
  const hasGaps = uncoveredTickets.length > 0
  const hasOverlaps = totalOverlaps > 0
  const isValid = !hasGaps && !hasOverlaps

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden mb-6">
      {/* Header */}
      <div className={clsx(
        'p-6 border-b border-dark-800',
        isValid && 'bg-green-500/5',
        !isValid && 'bg-yellow-500/5'
      )}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              {isValid ? (
                <CheckCircle className="text-green-400" size={24} />
              ) : (
                <AlertTriangle className="text-yellow-400" size={24} />
              )}
              <h3 className="text-xl font-bold text-gray-100">Coverage Validation Report</h3>
            </div>
            <p className="text-gray-400 text-sm">
              {isValid
                ? 'All child tickets are covered with no duplicates detected'
                : 'Issues detected - review gaps and overlaps below'
              }
            </p>
          </div>

          {!isValid && onRegenerate && (
            <button
              onClick={onRegenerate}
              className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors text-sm font-medium"
            >
              Regenerate Tickets
            </button>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-dark-800 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-1">
              <FileText size={16} className="text-gray-400" />
              <span className="text-xs text-gray-400">Coverage</span>
            </div>
            <p className={clsx(
              'text-2xl font-bold',
              coveragePercentage === 100 ? 'text-green-400' : 'text-yellow-400'
            )}>
              {coveragePercentage}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {coveredTickets.length} of {totalChildTickets} covered
            </p>
          </div>

          <div className={clsx(
            'rounded-lg p-4',
            hasGaps ? 'bg-red-500/10 border border-red-500/30' : 'bg-dark-800'
          )}>
            <div className="flex items-center space-x-2 mb-1">
              <XCircle size={16} className={hasGaps ? 'text-red-400' : 'text-gray-400'} />
              <span className="text-xs text-gray-400">Gaps</span>
            </div>
            <p className={clsx(
              'text-2xl font-bold',
              hasGaps ? 'text-red-400' : 'text-gray-400'
            )}>
              {uncoveredTickets.length}
            </p>
            <p className="text-xs text-gray-500 mt-1">Uncovered tickets</p>
          </div>

          <div className={clsx(
            'rounded-lg p-4',
            hasOverlaps ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-dark-800'
          )}>
            <div className="flex items-center space-x-2 mb-1">
              <AlertTriangle size={16} className={hasOverlaps ? 'text-yellow-400' : 'text-gray-400'} />
              <span className="text-xs text-gray-400">Overlaps</span>
            </div>
            <p className={clsx(
              'text-2xl font-bold',
              hasOverlaps ? 'text-yellow-400' : 'text-gray-400'
            )}>
              {totalOverlaps}
            </p>
            <p className="text-xs text-gray-500 mt-1">Duplicate scenarios</p>
          </div>
        </div>
      </div>

      {/* Coverage Section */}
      <div className="border-b border-dark-800">
        <button
          onClick={() => toggleSection('coverage')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            {hasGaps ? (
              <XCircle className="text-red-400" size={20} />
            ) : (
              <CheckCircle className="text-green-400" size={20} />
            )}
            <span className="font-semibold text-gray-200">
              Coverage Map ({coveredTickets.length}/{totalChildTickets} tickets covered)
            </span>
          </div>
          {expandedSection === 'coverage' ? (
            <ChevronUp className="text-gray-400" size={20} />
          ) : (
            <ChevronDown className="text-gray-400" size={20} />
          )}
        </button>

        {expandedSection === 'coverage' && (
          <div className="p-4 bg-dark-950 space-y-3">
            {/* Covered Tickets */}
            {coveredTickets.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-green-400 mb-2">
                  ✓ Covered Tickets ({coveredTickets.length})
                </h4>
                <div className="space-y-2">
                  {coveredTickets.map((ticket, idx) => (
                    <div key={idx} className="bg-dark-800 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-primary-400 font-medium text-sm">
                              {ticket.key}
                            </span>
                            <span className="text-gray-500 text-xs">→</span>
                            <span className="text-gray-400 text-xs">
                              {ticket.covered_by?.join(', ') || 'Unknown test ticket'}
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm">{ticket.summary}</p>
                        </div>
                        <CheckCircle className="text-green-400 flex-shrink-0 ml-2" size={16} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Uncovered Tickets */}
            {uncoveredTickets.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-red-400 mb-2">
                  ✗ Uncovered Tickets ({uncoveredTickets.length})
                </h4>
                <div className="space-y-2">
                  {uncoveredTickets.map((ticket, idx) => (
                    <div key={idx} className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <span className="text-primary-400 font-medium text-sm">
                            {ticket.key}
                          </span>
                          <p className="text-gray-300 text-sm mt-1">{ticket.summary}</p>
                          <p className="text-red-400 text-xs mt-2">
                            ⚠ This ticket is not covered by any test ticket
                          </p>
                        </div>
                        <XCircle className="text-red-400 flex-shrink-0 ml-2" size={16} />
                      </div>
                    </div>
                  ))}
                </div>

                {uncoveredTickets.length > 0 && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <p className="text-sm text-yellow-400 mb-2">
                      💡 <strong>Recommendation:</strong> Consider adding test coverage for these tickets
                    </p>
                    <button
                      onClick={() => {
                        const ticketList = uncoveredTickets.map(t => `${t.key}: ${t.summary}`).join('\n')
                        copyToClipboard(ticketList)
                      }}
                      className="text-xs text-primary-400 hover:text-primary-300 flex items-center space-x-1"
                    >
                      <Copy size={12} />
                      <span>Copy uncovered tickets to clipboard</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Overlaps Section */}
      <div>
        <button
          onClick={() => toggleSection('overlaps')}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            {hasOverlaps ? (
              <AlertTriangle className="text-yellow-400" size={20} />
            ) : (
              <CheckCircle className="text-green-400" size={20} />
            )}
            <span className="font-semibold text-gray-200">
              Duplicate Detection ({totalOverlaps} duplicates found)
            </span>
          </div>
          {expandedSection === 'overlaps' ? (
            <ChevronUp className="text-gray-400" size={20} />
          ) : (
            <ChevronDown className="text-gray-400" size={20} />
          )}
        </button>

        {expandedSection === 'overlaps' && (
          <div className="p-4 bg-dark-950">
            {hasOverlaps ? (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2">
                  ⚠ Potential Duplicates
                </h4>
                {overlaps.duplicates.map((overlap, idx) => (
                  <div key={idx} className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-yellow-400 font-medium text-sm">
                        {Math.round(overlap.similarity * 100)}% similarity
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="bg-dark-800 rounded p-2">
                        <p className="text-xs text-gray-400">Test Case 1:</p>
                        <p className="text-gray-200 text-sm">{overlap.tc1_title}</p>
                      </div>
                      <div className="bg-dark-800 rounded p-2">
                        <p className="text-xs text-gray-400">Test Case 2:</p>
                        <p className="text-gray-200 text-sm">{overlap.tc2_title}</p>
                      </div>
                    </div>
                    <p className="text-xs text-yellow-400 mt-2">
                      💡 Consider keeping only one or merging them
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle className="mx-auto text-green-400 mb-2" size={32} />
                <p className="text-gray-400 text-sm">No duplicate test scenarios detected</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
