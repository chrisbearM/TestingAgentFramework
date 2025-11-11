import React, { useState } from 'react'
import { X, CheckCircle, TrendingUp, ArrowRight, Copy, Check } from 'lucide-react'
import clsx from 'clsx'

export default function TicketImprovementComparison({ original, improved, improvements, onClose }) {
  const [copied, setCopied] = useState(false)

  if (!improved) {
    return null
  }

  const handleCopyImproved = () => {
    const improvedText = `
Summary: ${improved.summary}

Description:
${improved.description}

Acceptance Criteria:
${improved.acceptance_criteria?.map((ac, i) => `${i + 1}. ${ac}`).join('\n') || 'None'}

Edge Cases:
${improved.edge_cases?.map((ec, i) => `- ${ec}`).join('\n') || 'None'}

Error Scenarios:
${improved.error_scenarios?.map((es, i) => `- ${es}`).join('\n') || 'None'}

${improved.technical_notes ? `Technical Notes:\n${improved.technical_notes}` : ''}
    `.trim()

    navigator.clipboard.writeText(improvedText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-950 border border-dark-800 rounded-xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-dark-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <TrendingUp className="text-green-400" size={24} />
            <div>
              <h2 className="text-xl font-bold text-gray-100">Ticket Improvement Comparison</h2>
              <p className="text-sm text-gray-400">
                Review the suggested improvements to enhance ticket clarity
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Quality Increase Badge */}
            {improved.quality_increase && (
              <div className="bg-green-900/20 border border-green-800 rounded-lg p-4 flex items-center space-x-3">
                <CheckCircle className="text-green-400" size={24} />
                <div className="flex-1">
                  <p className="text-green-400 font-semibold">
                    Estimated Quality Increase: +{improved.quality_increase}%
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
                <h3 className="text-lg font-semibold text-gray-100 mb-4">Improvements Made</h3>
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
                    <p className="text-gray-300">{original.summary}</p>
                  </div>

                  {/* Description */}
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">DESCRIPTION</h4>
                    <p className="text-gray-400 text-sm whitespace-pre-wrap">
                      {original.description || 'No description provided'}
                    </p>
                  </div>
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
                    <p className="text-green-300 font-medium">{improved.summary}</p>
                  </div>

                  {/* Description */}
                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">DESCRIPTION</h4>
                    <p className="text-gray-300 text-sm whitespace-pre-wrap">
                      {improved.description}
                    </p>
                  </div>

                  {/* Acceptance Criteria */}
                  {improved.acceptance_criteria && improved.acceptance_criteria.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 mb-2">ACCEPTANCE CRITERIA</h4>
                      <ul className="space-y-2">
                        {improved.acceptance_criteria.map((ac, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <CheckCircle size={16} className="text-green-400 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-300">{ac}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Edge Cases */}
                  {improved.edge_cases && improved.edge_cases.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 mb-2">EDGE CASES</h4>
                      <ul className="space-y-1">
                        {improved.edge_cases.map((ec, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="text-yellow-400 text-xs mt-1">▸</span>
                            <span className="text-sm text-gray-400">{ec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Error Scenarios */}
                  {improved.error_scenarios && improved.error_scenarios.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 mb-2">ERROR SCENARIOS</h4>
                      <ul className="space-y-1">
                        {improved.error_scenarios.map((es, i) => (
                          <li key={i} className="flex items-start space-x-2">
                            <span className="text-red-400 text-xs mt-1">▸</span>
                            <span className="text-sm text-gray-400">{es}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Technical Notes */}
                  {improved.technical_notes && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 mb-2">TECHNICAL NOTES</h4>
                      <p className="text-sm text-gray-400">{improved.technical_notes}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-dark-800 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleCopyImproved}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <Copy size={18} />
            <span>Copy Improved Ticket</span>
          </button>
        </div>
      </div>
    </div>
  )
}
