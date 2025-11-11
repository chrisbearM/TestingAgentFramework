import React, { useState } from 'react'
import { X, CheckCircle, Plus, Edit, Loader2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

export default function CoverageFixesModal({ fixes, onClose, onApply }) {
  const [selectedNewTickets, setSelectedNewTickets] = useState(new Set(fixes?.new_tickets?.map((_, i) => i) || []))
  const [selectedUpdates, setSelectedUpdates] = useState(new Set(fixes?.ticket_updates?.map((_, i) => i) || []))
  const [applying, setApplying] = useState(false)

  if (!fixes) {
    return null
  }

  const { new_tickets = [], ticket_updates = [], summary = {} } = fixes

  const toggleNewTicket = (index) => {
    const newSelected = new Set(selectedNewTickets)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedNewTickets(newSelected)
  }

  const toggleUpdate = (index) => {
    const newSelected = new Set(selectedUpdates)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedUpdates(newSelected)
  }

  const handleApply = async () => {
    setApplying(true)
    try {
      const selectedNew = new_tickets.filter((_, i) => selectedNewTickets.has(i))
      const selectedUpd = ticket_updates.filter((_, i) => selectedUpdates.has(i))
      await onApply(selectedNew, selectedUpd)
    } finally {
      setApplying(false)
    }
  }

  const totalSelected = selectedNewTickets.size + selectedUpdates.size

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-950 border border-dark-800 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-dark-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-100">Coverage Fixes</h2>
            <p className="text-sm text-gray-400 mt-1">
              AI-generated solutions to improve test ticket coverage
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Summary Banner */}
        <div className="bg-gradient-to-r from-green-900/20 to-primary-900/20 border-b border-green-800/50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="text-green-400" size={20} />
                <div>
                  <p className="text-sm text-gray-400">Gaps Addressed</p>
                  <p className="text-lg font-bold text-green-400">{summary.gaps_addressed || 0}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Plus className="text-primary-400" size={20} />
                <div>
                  <p className="text-sm text-gray-400">New Tickets</p>
                  <p className="text-lg font-bold text-primary-400">{new_tickets.length}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Edit className="text-yellow-400" size={20} />
                <div>
                  <p className="text-sm text-gray-400">Updates</p>
                  <p className="text-lg font-bold text-yellow-400">{ticket_updates.length}</p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Est. Coverage Improvement</p>
              <p className="text-2xl font-bold text-green-400">+{summary.estimated_coverage_improvement || 0}%</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* New Test Tickets */}
          {new_tickets.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Plus className="text-primary-400" size={20} />
                <h3 className="text-lg font-semibold text-gray-100">
                  New Test Tickets ({new_tickets.length})
                </h3>
              </div>
              <div className="space-y-4">
                {new_tickets.map((ticket, index) => (
                  <div
                    key={index}
                    className={clsx(
                      'border rounded-lg overflow-hidden transition-all',
                      selectedNewTickets.has(index)
                        ? 'border-primary-500 bg-primary-900/10'
                        : 'border-dark-700 bg-dark-900'
                    )}
                  >
                    <div className="p-4">
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedNewTickets.has(index)}
                          onChange={() => toggleNewTicket(index)}
                          className="mt-1 w-5 h-5 rounded border-dark-700 bg-dark-800 text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 cursor-pointer"
                        />
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-100 mb-2">{ticket.summary}</h4>
                          <p className="text-sm text-gray-400 mb-3">{ticket.description}</p>

                          {/* Addresses Gap */}
                          {ticket.addresses_gap && (
                            <div className="bg-green-900/20 border border-green-800 rounded-lg p-3 mb-3">
                              <p className="text-xs text-green-400 font-medium mb-1">Addresses Gap:</p>
                              <p className="text-sm text-gray-300">{ticket.addresses_gap}</p>
                            </div>
                          )}

                          {/* Acceptance Criteria */}
                          {ticket.acceptance_criteria && ticket.acceptance_criteria.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs font-semibold text-gray-400 mb-2">ACCEPTANCE CRITERIA</p>
                              <ul className="space-y-1">
                                {ticket.acceptance_criteria.map((ac, i) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <CheckCircle size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                                    <span className="text-sm text-gray-300">{ac}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Coverage Info */}
                          <div className="flex flex-wrap gap-2">
                            {ticket.covers_child_tickets && ticket.covers_child_tickets.length > 0 && (
                              <div className="text-xs px-2 py-1 bg-dark-800 border border-dark-700 rounded">
                                <span className="text-gray-400">Covers: </span>
                                <span className="text-primary-400">{ticket.covers_child_tickets.join(', ')}</span>
                              </div>
                            )}
                            {ticket.covers_requirements && ticket.covers_requirements.length > 0 && (
                              <div className="text-xs px-2 py-1 bg-dark-800 border border-dark-700 rounded">
                                <span className="text-gray-400">Requirements: </span>
                                <span className="text-green-400">{ticket.covers_requirements.length} items</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ticket Updates */}
          {ticket_updates.length > 0 && (
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Edit className="text-yellow-400" size={20} />
                <h3 className="text-lg font-semibold text-gray-100">
                  Ticket Updates ({ticket_updates.length})
                </h3>
              </div>
              <div className="space-y-4">
                {ticket_updates.map((update, index) => (
                  <div
                    key={index}
                    className={clsx(
                      'border rounded-lg overflow-hidden transition-all',
                      selectedUpdates.has(index)
                        ? 'border-yellow-500 bg-yellow-900/10'
                        : 'border-dark-700 bg-dark-900'
                    )}
                  >
                    <div className="p-4">
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedUpdates.has(index)}
                          onChange={() => toggleUpdate(index)}
                          className="mt-1 w-5 h-5 rounded border-dark-700 bg-dark-800 text-yellow-500 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-0 cursor-pointer"
                        />
                        <div className="flex-1">
                          <div className="mb-3">
                            <p className="text-xs text-gray-400 mb-1">Original Ticket:</p>
                            <p className="text-sm text-gray-500">{update.original_ticket_id}</p>
                          </div>

                          <h4 className="font-semibold text-gray-100 mb-2">{update.updated_summary}</h4>
                          <p className="text-sm text-gray-400 mb-3">{update.updated_description}</p>

                          {/* Changes Made */}
                          {update.changes_made && (
                            <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-3 mb-3">
                              <p className="text-xs text-yellow-400 font-medium mb-1">Changes Made:</p>
                              <p className="text-sm text-gray-300">{update.changes_made}</p>
                            </div>
                          )}

                          {/* Addresses Gap */}
                          {update.addresses_gap && (
                            <div className="bg-green-900/20 border border-green-800 rounded-lg p-3 mb-3">
                              <p className="text-xs text-green-400 font-medium mb-1">Addresses Gap:</p>
                              <p className="text-sm text-gray-300">{update.addresses_gap}</p>
                            </div>
                          )}

                          {/* Updated Acceptance Criteria */}
                          {update.updated_acceptance_criteria && update.updated_acceptance_criteria.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-400 mb-2">UPDATED ACCEPTANCE CRITERIA</p>
                              <ul className="space-y-1">
                                {update.updated_acceptance_criteria.map((ac, i) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <CheckCircle size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                                    <span className="text-sm text-gray-300">{ac}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No Fixes */}
          {new_tickets.length === 0 && ticket_updates.length === 0 && (
            <div className="text-center py-12">
              <AlertCircle className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No fixes generated</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-dark-800 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            {totalSelected} {totalSelected === 1 ? 'fix' : 'fixes'} selected
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={totalSelected === 0 || applying}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              {applying ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Applying...</span>
                </>
              ) : (
                <>
                  <CheckCircle size={18} />
                  <span>Apply Selected Fixes ({totalSelected})</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
