import React, { useState } from 'react'
import { X, FileText, CheckCircle, ChevronDown, ChevronRight, Layers, Tag, CheckSquare, Square } from 'lucide-react'

export default function E2ETicketModal({
  e2eTicket,  // Single ticket (backwards compatible)
  e2eTickets, // Multiple tickets (new)
  scenarios,
  totalAcsExtracted,
  totalAcsPreserved,
  onClose,
  onAccept
}) {
  // Support both single ticket (old) and multiple tickets (new)
  const tickets = e2eTickets || (e2eTicket ? [e2eTicket] : [])

  const [expandedTickets, setExpandedTickets] = useState(
    tickets.reduce((acc, _, i) => ({ ...acc, [i]: true }), {})
  )
  const [selectedTickets, setSelectedTickets] = useState(
    tickets.reduce((acc, _, i) => ({ ...acc, [i]: true }), {})
  )

  if (tickets.length === 0) return null

  const toggleTicket = (index) => {
    setExpandedTickets(prev => ({ ...prev, [index]: !prev[index] }))
  }

  const toggleSelection = (index) => {
    setSelectedTickets(prev => ({ ...prev, [index]: !prev[index] }))
  }

  const selectAll = () => {
    setSelectedTickets(tickets.reduce((acc, _, i) => ({ ...acc, [i]: true }), {}))
  }

  const deselectAll = () => {
    setSelectedTickets(tickets.reduce((acc, _, i) => ({ ...acc, [i]: false }), {}))
  }

  const selectedCount = Object.values(selectedTickets).filter(Boolean).length

  const handleAccept = () => {
    const ticketsToAdd = tickets.filter((_, i) => selectedTickets[i])
    onAccept(ticketsToAdd)
  }

  // Calculate total ACs across all tickets
  const totalAcs = tickets.reduce((sum, t) => sum + (t.acceptance_criteria?.length || 0), 0)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-dark-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Layers className="text-purple-500" size={24} />
              <div>
                <h2 className="text-xl font-bold text-gray-100">
                  Functional Area E2E Tickets
                </h2>
                <p className="text-sm text-gray-400 mt-1">
                  {tickets.length} E2E tickets created, {totalAcs} total acceptance criteria
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

          {/* Stats bar */}
          {(totalAcsExtracted || totalAcsPreserved) && (
            <div className="flex items-center space-x-4 text-sm">
              <div className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
                <span className="text-green-400">
                  {totalAcsExtracted || totalAcs} ACs extracted
                </span>
              </div>
              <div className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <span className="text-purple-400">
                  {totalAcsPreserved || totalAcs} ACs preserved
                </span>
              </div>
              <div className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <span className="text-blue-400">
                  {tickets.length} functional areas
                </span>
              </div>
            </div>
          )}

          {/* Selection controls */}
          {tickets.length > 1 && (
            <div className="mt-4 flex items-center space-x-4">
              <span className="text-sm text-gray-400">
                {selectedCount} of {tickets.length} selected
              </span>
              <button
                onClick={selectAll}
                className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="text-sm text-gray-400 hover:text-gray-300 transition-colors"
              >
                Deselect All
              </button>
            </div>
          )}
        </div>

        {/* Content - Scrollable list of E2E tickets */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {tickets.map((ticket, index) => (
            <div
              key={ticket.id || index}
              className={`border rounded-xl overflow-hidden transition-colors ${
                selectedTickets[index]
                  ? 'border-purple-500/50 bg-purple-500/5'
                  : 'border-dark-700 bg-dark-800/50'
              }`}
            >
              {/* Ticket Header */}
              <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-dark-800/50 transition-colors"
                onClick={() => toggleTicket(index)}
              >
                <div className="flex items-center space-x-3">
                  {/* Selection checkbox */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleSelection(index)
                    }}
                    className="p-1 hover:bg-dark-700 rounded transition-colors"
                  >
                    {selectedTickets[index] ? (
                      <CheckSquare size={20} className="text-purple-400" />
                    ) : (
                      <Square size={20} className="text-gray-500" />
                    )}
                  </button>

                  {/* Expand/collapse */}
                  {expandedTickets[index] ? (
                    <ChevronDown size={20} className="text-gray-400" />
                  ) : (
                    <ChevronRight size={20} className="text-gray-400" />
                  )}

                  {/* Functional area tag */}
                  <div className="px-3 py-1 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/30 rounded-lg">
                    <span className="text-sm font-medium text-purple-300">
                      {ticket.functional_area || 'E2E Testing'}
                    </span>
                  </div>

                  {/* Ticket summary */}
                  <span className="text-gray-200 font-medium">
                    {ticket.summary}
                  </span>
                </div>

                {/* AC count badge */}
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 bg-dark-700 rounded text-xs text-gray-400">
                    {ticket.acceptance_criteria?.length || 0} ACs
                  </span>
                  <span className="px-2 py-1 bg-dark-700 rounded text-xs text-gray-400">
                    {ticket.scenarios?.length || 0} scenarios
                  </span>
                </div>
              </div>

              {/* Ticket Details (expandable) */}
              {expandedTickets[index] && (
                <div className="border-t border-dark-700 p-4 space-y-4">
                  {/* Description */}
                  <div>
                    <p className="text-gray-400 text-sm">{ticket.description}</p>
                  </div>

                  {/* Acceptance Criteria */}
                  {ticket.acceptance_criteria?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center space-x-2">
                        <CheckCircle size={16} className="text-green-400" />
                        <span>Acceptance Criteria ({ticket.acceptance_criteria.length})</span>
                      </h4>
                      <div className="bg-dark-900/50 rounded-lg p-3 space-y-2 max-h-60 overflow-y-auto">
                        {ticket.acceptance_criteria.map((ac, i) => (
                          <div key={i} className="flex items-start space-x-2">
                            <span className="text-xs text-gray-500 font-mono w-6 flex-shrink-0">
                              {i + 1}.
                            </span>
                            <span className="text-gray-300 text-sm">{ac}</span>
                            {/* Show source tickets if available */}
                            {ticket.ac_sources?.[i]?.length > 0 && (
                              <div className="flex-shrink-0 flex items-center space-x-1">
                                {ticket.ac_sources[i].slice(0, 2).map((src, j) => (
                                  <span
                                    key={j}
                                    className="px-1.5 py-0.5 bg-dark-700 rounded text-xs text-gray-500"
                                  >
                                    {src}
                                  </span>
                                ))}
                                {ticket.ac_sources[i].length > 2 && (
                                  <span className="text-xs text-gray-500">
                                    +{ticket.ac_sources[i].length - 2}
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Scenarios */}
                  {ticket.scenarios?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center space-x-2">
                        <FileText size={16} className="text-blue-400" />
                        <span>E2E Scenarios ({ticket.scenarios.length})</span>
                      </h4>
                      <div className="space-y-2">
                        {ticket.scenarios.map((scenario, i) => (
                          <div key={i} className="bg-dark-900/50 rounded-lg p-3 border border-dark-700">
                            <h5 className="text-gray-200 font-medium text-sm mb-1">
                              {scenario.scenario_name}
                            </h5>
                            <p className="text-gray-400 text-xs mb-2">{scenario.description}</p>

                            {scenario.user_journey?.length > 0 && (
                              <div className="text-xs">
                                <span className="text-gray-500">Steps: </span>
                                <span className="text-gray-400">
                                  {scenario.user_journey.length} steps
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source Tickets */}
                  {ticket.e2e_source_tickets?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center space-x-2">
                        <Tag size={16} className="text-purple-400" />
                        <span>Source Tickets ({ticket.e2e_source_tickets.length})</span>
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {ticket.e2e_source_tickets.map((ticketId, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-purple-500/10 border border-purple-500/30 rounded text-xs text-purple-400"
                          >
                            {ticketId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-dark-800 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            {selectedCount > 0 ? (
              <span>
                Adding {selectedCount} E2E ticket{selectedCount !== 1 ? 's' : ''} with{' '}
                {tickets
                  .filter((_, i) => selectedTickets[i])
                  .reduce((sum, t) => sum + (t.acceptance_criteria?.length || 0), 0)
                } total ACs
              </span>
            ) : (
              <span className="text-amber-400">Select at least one ticket to add</span>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAccept}
              disabled={selectedCount === 0}
              className={`px-6 py-3 font-medium rounded-lg transition-colors shadow-lg ${
                selectedCount > 0
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
                  : 'bg-dark-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              Add {selectedCount} E2E Ticket{selectedCount !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
