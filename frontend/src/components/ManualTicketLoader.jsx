import React, { useState } from 'react'
import { X, Plus, Loader2, CheckCircle, AlertTriangle, Trash2 } from 'lucide-react'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'

export default function ManualTicketLoader({ epicKey, onTicketsAdded, onClose }) {
  const [ticketInput, setTicketInput] = useState('')
  const [ticketKeys, setTicketKeys] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const { progress } = useWebSocket()

  // Parse ticket keys from input
  const parseTicketKeys = (input) => {
    // Split by comma, newline, or space and trim each
    const keys = input
      .split(/[,\n\s]+/)
      .map(key => key.trim().toUpperCase())
      .filter(key => key.length > 0)
      .filter((key, index, self) => self.indexOf(key) === index) // Remove duplicates

    return keys
  }

  const handleInputChange = (e) => {
    const input = e.target.value
    setTicketInput(input)
    setTicketKeys(parseTicketKeys(input))
  }

  const handleRemoveTicket = (keyToRemove) => {
    const newKeys = ticketKeys.filter(key => key !== keyToRemove)
    setTicketKeys(newKeys)
    setTicketInput(newKeys.join(', '))
  }

  const handleLoadTickets = async () => {
    if (ticketKeys.length === 0) return

    setLoading(true)
    setResult(null)

    try {
      const response = await api.post(`/epics/${epicKey}/add-children`, {
        ticket_keys: ticketKeys
      })

      setResult(response.data)

      // If all tickets loaded successfully, notify parent and close after a delay
      if (response.data.failed_count === 0) {
        setTimeout(() => {
          onTicketsAdded(response.data.loaded_tickets)
          onClose()
        }, 1500)
      } else {
        // If some failed, still notify parent but don't auto-close
        onTicketsAdded(response.data.loaded_tickets)
      }

    } catch (err) {
      setResult({
        success: false,
        error: err.response?.data?.detail || err.message || 'Failed to load tickets'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-900 border border-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-800">
          <div>
            <h2 className="text-xl font-semibold text-gray-100">Add Child Tickets Manually</h2>
            <p className="text-sm text-gray-400 mt-1">
              Fallback method to add tickets that weren't loaded automatically
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Input Area */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ticket Keys
            </label>
            <textarea
              value={ticketInput}
              onChange={handleInputChange}
              placeholder="Enter ticket keys separated by commas or new lines&#10;e.g., PROJ-123, PROJ-456, PROJ-789"
              className="w-full h-32 bg-dark-800 border border-dark-700 rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none font-mono text-sm"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Supports comma, space, or newline separated keys
            </p>
          </div>

          {/* Parsed Keys Preview */}
          {ticketKeys.length > 0 && !result && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tickets to Load ({ticketKeys.length})
              </label>
              <div className="bg-dark-800 border border-dark-700 rounded-lg p-4 max-h-48 overflow-y-auto">
                <div className="flex flex-wrap gap-2">
                  {ticketKeys.map(key => (
                    <div
                      key={key}
                      className="flex items-center space-x-2 bg-dark-900 border border-dark-700 rounded px-3 py-1.5 text-sm"
                    >
                      <span className="text-gray-200 font-mono">{key}</span>
                      <button
                        onClick={() => handleRemoveTicket(key)}
                        className="text-gray-500 hover:text-red-400 transition-colors"
                        disabled={loading}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Progress */}
          {loading && progress && (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <Loader2 className="animate-spin text-primary-400" size={20} />
                <div className="flex-1">
                  <p className="text-sm text-gray-300">{progress.message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4">
              {/* Success */}
              {result.loaded_count > 0 && (
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="text-green-400 mt-0.5" size={20} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-400">
                        Successfully loaded {result.loaded_count} ticket{result.loaded_count !== 1 ? 's' : ''}
                      </p>
                      {result.loaded_tickets && result.loaded_tickets.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {result.loaded_tickets.map(ticket => (
                            <li key={ticket.key} className="text-xs text-gray-300 font-mono">
                              {ticket.key}: {ticket.fields?.summary || 'No summary'}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Failures */}
              {result.failed_count > 0 && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="text-red-400 mt-0.5" size={20} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-400">
                        Failed to load {result.failed_count} ticket{result.failed_count !== 1 ? 's' : ''}
                      </p>
                      {result.failed_tickets && result.failed_tickets.length > 0 && (
                        <ul className="mt-2 space-y-1">
                          {result.failed_tickets.map(failed => (
                            <li key={failed.key} className="text-xs text-gray-300">
                              <span className="font-mono">{failed.key}</span>: {failed.error}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Error */}
              {result.error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="text-red-400 mt-0.5" size={20} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-400">Error</p>
                      <p className="text-xs text-gray-300 mt-1">{result.error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-dark-800">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors"
            disabled={loading}
          >
            {result && result.loaded_count > 0 ? 'Done' : 'Cancel'}
          </button>
          <button
            onClick={handleLoadTickets}
            disabled={ticketKeys.length === 0 || loading}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-dark-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                <span>Loading...</span>
              </>
            ) : (
              <>
                <Plus size={16} />
                <span>Load {ticketKeys.length} Ticket{ticketKeys.length !== 1 ? 's' : ''}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
