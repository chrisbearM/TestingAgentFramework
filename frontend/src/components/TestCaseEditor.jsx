import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Edit2, Save, X, CheckSquare, Download, Target, Sparkles, Loader2, XCircle, Copy, Check, FileText } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import TraceabilityMatrix from './TraceabilityMatrix'
import TestReviewPanel from './TestReviewPanel'

export default function TestCaseEditor({ testCases, ticketInfo, requirements, improvedTicket }) {
  const [cases, setCases] = useState(testCases)
  const [expandedCase, setExpandedCase] = useState(0)
  const [editingCase, setEditingCase] = useState(null)
  const [selectedCases, setSelectedCases] = useState(new Set())
  const [exportFormat, setExportFormat] = useState('csv')
  const [exporting, setExporting] = useState(false)
  const [showTraceability, setShowTraceability] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [reviewProgress, setReviewProgress] = useState('')
  const [reviewResults, setReviewResults] = useState(null)
  const [generatingAdditional, setGeneratingAdditional] = useState(false)
  const [showImprovedTicket, setShowImprovedTicket] = useState(false)
  const [copiedToClipboard, setCopiedToClipboard] = useState(false)
  const [hasReviewed, setHasReviewed] = useState(false)
  const [hasAppliedImprovements, setHasAppliedImprovements] = useState(false)

  const toggleSelect = (index) => {
    const newSelected = new Set(selectedCases)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedCases(newSelected)
  }

  const selectAll = () => {
    if (selectedCases.size === cases.length) {
      setSelectedCases(new Set())
    } else {
      setSelectedCases(new Set(cases.map((_, i) => i)))
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const selectedTestCases = cases.filter((_, i) => selectedCases.has(i))

      const response = await api.post('/test-cases/export', {
        test_cases: selectedTestCases,
        ticket_key: ticketInfo.key,
        format: exportFormat
      }, {
        responseType: 'blob'
      })

      // Sanitize ticket key for filename (allow only alphanumeric, dash, underscore)
      const safeTicketKey = ticketInfo.key.replace(/[^a-zA-Z0-9-_]/g, '_')

      // Additional validation: ensure safeTicketKey is not empty and has reasonable length
      if (!safeTicketKey || safeTicketKey.length === 0 || safeTicketKey.length > 100) {
        throw new Error('Invalid ticket key for export')
      }

      // Determine file extension - validate exportFormat to prevent injection
      const validFormats = ['xlsx', 'csv', 'testrail']
      if (!validFormats.includes(exportFormat)) {
        throw new Error('Invalid export format')
      }

      const extension = exportFormat === 'xlsx' ? 'xlsx' : 'csv'
      const suffix = exportFormat === 'testrail' ? '_testrail' : ''

      // Construct filename with validated components
      const filename = `test_cases_${safeTicketKey}${suffix}.${extension}`

      // Use a safer approach without appendChild to avoid DOM-based XSS warnings
      // Create blob URL and trigger download using location assignment
      const url = window.URL.createObjectURL(new Blob([response.data]))

      // Create a temporary link element that's never added to DOM
      const link = document.createElement('a')
      link.href = url
      link.download = filename

      // Trigger click without adding to DOM (works in modern browsers)
      link.dispatchEvent(new MouseEvent('click', {
        bubbles: false,
        cancelable: true,
        view: window
      }))

      // Clean up immediately
      setTimeout(() => {
        window.URL.revokeObjectURL(url)
      }, 100)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Failed to export test cases. Please try again.')
    } finally {
      setExporting(false)
    }
  }

  const handleReviewTestCases = async () => {
    setReviewing(true)
    setReviewProgress('Analyzing test cases for quality and completeness...')

    try {
      const response = await api.post('/test-cases/review-and-improve', {
        test_cases: cases,
        requirements: requirements || [],
        ticket_context: ticketInfo ? {
          key: ticketInfo.key,
          summary: ticketInfo.summary,
          description: ticketInfo.description
        } : null
      })

      if (response.data.success && response.data.review) {
        setReviewProgress('')
        console.log('Review results:', response.data.review)
        setReviewResults(response.data.review)
        setHasReviewed(true)
      }
    } catch (error) {
      console.error('Review failed:', error)
      alert(`Failed to review test cases: ${error.response?.data?.detail || error.message}`)
      setReviewProgress('')
    } finally {
      setReviewing(false)
    }
  }

  const handleGenerateAdditionalTests = async (reviewFeedback) => {
    console.log('DEBUG: handleGenerateAdditionalTests called with:', reviewFeedback)
    setGeneratingAdditional(true)

    try {
      const requestData = {
        existing_test_cases: cases,
        requirements: requirements || [],
        ...reviewFeedback  // Spread suggestions, issues, missingScenarios
      }
      console.log('DEBUG: Request data:', requestData)

      const response = await api.post('/test-cases/suggest-additional', requestData)
      console.log('DEBUG: Response data:', response.data)

      if (response.data.success) {
        // Handle new format with separate improved and new test cases
        const improvedCases = response.data.improved_test_cases || []
        const newCases = response.data.new_test_cases || []

        // Backward compatibility: check for old format
        const oldFormatCases = response.data.suggested_cases || response.data.suggested_test_cases || []

        if (improvedCases.length > 0 || newCases.length > 0) {
          // New format: replace improved cases and append new cases
          const updatedCases = [...cases]

          // Replace improved test cases at their original indices
          improvedCases.forEach(improvedCase => {
            const index = improvedCase.index
            if (index !== undefined && index >= 0 && index < updatedCases.length) {
              console.log(`DEBUG: Replacing test case at index ${index}`)
              updatedCases[index] = improvedCase
            }
          })

          // Append new test cases
          const finalCases = [...updatedCases, ...newCases]

          console.log(`DEBUG: Applied ${improvedCases.length} improvements and added ${newCases.length} new test cases`)

          setCases(finalCases)
          setReviewResults(null)
          setHasAppliedImprovements(true)

          const message = []
          if (improvedCases.length > 0) {
            message.push(`${improvedCases.length} test case${improvedCases.length === 1 ? '' : 's'} improved`)
          }
          if (newCases.length > 0) {
            message.push(`${newCases.length} new test case${newCases.length === 1 ? '' : 's'} added`)
          }
          alert(`Successfully applied improvements: ${message.join(', ')}!`)
        } else if (oldFormatCases.length > 0) {
          // Old format: just append all cases
          setCases([...cases, ...oldFormatCases])
          setReviewResults(null)
          setHasAppliedImprovements(true)
          alert(`Successfully generated ${oldFormatCases.length} test case${oldFormatCases.length === 1 ? '' : 's'} based on review feedback!`)
        } else {
          console.log('DEBUG: No test cases generated')
          alert('No improvements generated. The AI may not have found any actionable improvements, or the test cases may already be optimal.')
        }
      } else {
        console.log('DEBUG: Response not successful')
        alert('No improvements generated. The AI may not have found any actionable improvements, or the test cases may already be optimal.')
      }
    } catch (error) {
      console.error('Failed to implement improvements:', error)
      alert(`Failed to implement improvements: ${error.response?.data?.detail || error.message}`)
    } finally {
      setGeneratingAdditional(false)
    }
  }

  const formatImprovedTicketForCopy = () => {
    if (!improvedTicket) return ''

    let text = ''

    if (improvedTicket.summary) {
      text += `**Summary:**\n${improvedTicket.summary}\n\n`
    }

    if (improvedTicket.description) {
      text += `**Description:**\n${improvedTicket.description}\n\n`
    }

    if (improvedTicket.acceptance_criteria && improvedTicket.acceptance_criteria.length > 0) {
      text += `**Acceptance Criteria:**\n`
      improvedTicket.acceptance_criteria.forEach((ac, i) => {
        text += `${i + 1}. ${ac}\n`
      })
      text += '\n'
    }

    if (improvedTicket.edge_cases && improvedTicket.edge_cases.length > 0) {
      text += `**Edge Cases:**\n`
      improvedTicket.edge_cases.forEach((ec, i) => {
        text += `- ${ec}\n`
      })
      text += '\n'
    }

    if (improvedTicket.error_scenarios && improvedTicket.error_scenarios.length > 0) {
      text += `**Error Scenarios:**\n`
      improvedTicket.error_scenarios.forEach((es, i) => {
        text += `- ${es}\n`
      })
      text += '\n'
    }

    if (improvedTicket.technical_notes) {
      text += `**Technical Notes:**\n${improvedTicket.technical_notes}\n`
    }

    return text.trim()
  }

  const copyImprovedTicketToClipboard = async () => {
    const text = formatImprovedTicketForCopy()
    try {
      await navigator.clipboard.writeText(text)
      setCopiedToClipboard(true)
      setTimeout(() => setCopiedToClipboard(false), 2000)
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
      alert('Failed to copy to clipboard')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Test Cases</h2>
          <p className="text-gray-400 mt-1">
            {cases.length} test {cases.length === 1 ? 'case' : 'cases'} generated
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReviewTestCases}
            disabled={reviewing || cases.length === 0 || hasReviewed}
            className={clsx(
              "px-4 py-2 rounded-lg transition-colors flex items-center space-x-2",
              hasReviewed
                ? "bg-green-600/20 border border-green-500/30 text-green-400 cursor-not-allowed"
                : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white"
            )}
            title={hasReviewed ? "Test cases have already been reviewed. Generate new test cases to review again." : ""}
          >
            {reviewing ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Reviewing...</span>
              </>
            ) : hasReviewed ? (
              <>
                <CheckSquare size={18} />
                <span>Test Cases Reviewed ✓</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Review Test Cases</span>
              </>
            )}
          </button>

          <button
            onClick={() => setShowTraceability(true)}
            disabled={!requirements || requirements.length === 0}
            className="px-4 py-2 bg-primary-500/10 hover:bg-primary-500/20 border border-primary-500/30 text-primary-400 rounded-lg transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Target size={18} />
            <span>View Traceability Matrix</span>
          </button>

          {improvedTicket && (
            <button
              onClick={() => setShowImprovedTicket(!showImprovedTicket)}
              className={clsx(
                "px-4 py-2 border rounded-lg transition-colors flex items-center space-x-2",
                showImprovedTicket
                  ? "bg-green-500/20 border-green-500/30 text-green-400"
                  : "bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-400"
              )}
            >
              <FileText size={18} />
              <span>{showImprovedTicket ? 'Hide' : 'View'} Improved Ticket</span>
            </button>
          )}

          <button
            onClick={selectAll}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors flex items-center space-x-2"
          >
            <CheckSquare size={18} />
            <span>{selectedCases.size === cases.length ? 'Deselect All' : 'Select All'}</span>
          </button>

          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value)}
            className="px-4 py-2 bg-dark-800 border border-dark-700 text-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="csv">CSV (Azure DevOps)</option>
            <option value="xlsx">Excel (XLSX)</option>
            <option value="testrail">TestRail CSV</option>
          </select>

          <button
            onClick={handleExport}
            disabled={selectedCases.size === 0 || exporting}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2 shadow-nebula"
          >
            <Download size={18} />
            <span>{exporting ? 'Exporting...' : `Export (${selectedCases.size})`}</span>
          </button>
        </div>
      </div>

      {/* Review Progress */}
      {reviewing && reviewProgress && (
        <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-500/30 rounded-xl p-4">
          <div className="flex items-center space-x-3">
            <Loader2 className="animate-spin text-purple-400" size={20} />
            <p className="text-purple-300 font-medium">{reviewProgress}</p>
          </div>
        </div>
      )}

      {/* Review Results Panel */}
      {reviewResults && (
        <div className="relative">
          {/* Close button */}
          <button
            onClick={() => setReviewResults(null)}
            className="absolute top-4 right-4 z-10 p-2 bg-dark-800 hover:bg-dark-700 rounded-lg border border-dark-700 transition-colors"
            title="Close review"
          >
            <XCircle size={20} className="text-gray-400" />
          </button>

          <TestReviewPanel
            review={reviewResults}
            onRequestAdditionalSuggestions={handleGenerateAdditionalTests}
            isGenerating={generatingAdditional}
            hasAppliedImprovements={hasAppliedImprovements}
          />
        </div>
      )}

      {/* Improved Ticket Display */}
      {showImprovedTicket && improvedTicket && (
        <div className="bg-gradient-to-r from-amber-900/20 to-yellow-900/20 border border-amber-500/30 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <FileText className="text-amber-400" size={24} />
              <div>
                <h3 className="text-lg font-semibold text-amber-300">Improved Ticket (Used for Analysis)</h3>
                <p className="text-sm text-amber-400/70">This preprocessed version was sent to AI agents for more consistent test case generation</p>
              </div>
            </div>
            <button
              onClick={copyImprovedTicketToClipboard}
              className={clsx(
                "px-4 py-2 rounded-lg transition-colors flex items-center space-x-2",
                copiedToClipboard
                  ? "bg-green-500/20 border border-green-500/30 text-green-400"
                  : "bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300"
              )}
            >
              {copiedToClipboard ? (
                <>
                  <Check size={18} />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={18} />
                  <span>Copy to Clipboard</span>
                </>
              )}
            </button>
          </div>

          <div className="space-y-4 text-sm">
            {improvedTicket.summary && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Summary</h4>
                <p className="text-gray-300">{improvedTicket.summary}</p>
              </div>
            )}

            {improvedTicket.description && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Description</h4>
                <p className="text-gray-300 whitespace-pre-wrap">{improvedTicket.description}</p>
              </div>
            )}

            {improvedTicket.acceptance_criteria && improvedTicket.acceptance_criteria.length > 0 && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Acceptance Criteria</h4>
                <ol className="list-decimal list-inside space-y-1">
                  {improvedTicket.acceptance_criteria.map((ac, i) => (
                    <li key={i} className="text-gray-300">{ac}</li>
                  ))}
                </ol>
              </div>
            )}

            {improvedTicket.edge_cases && improvedTicket.edge_cases.length > 0 && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Edge Cases</h4>
                <ul className="list-disc list-inside space-y-1">
                  {improvedTicket.edge_cases.map((ec, i) => (
                    <li key={i} className="text-gray-300">{ec}</li>
                  ))}
                </ul>
              </div>
            )}

            {improvedTicket.error_scenarios && improvedTicket.error_scenarios.length > 0 && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Error Scenarios</h4>
                <ul className="list-disc list-inside space-y-1">
                  {improvedTicket.error_scenarios.map((es, i) => (
                    <li key={i} className="text-gray-300">{es}</li>
                  ))}
                </ul>
              </div>
            )}

            {improvedTicket.technical_notes && (
              <div>
                <h4 className="font-semibold text-amber-300 mb-1">Technical Notes</h4>
                <p className="text-gray-400 italic">{improvedTicket.technical_notes}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Test Cases */}
      <div className="space-y-4">
        {cases.map((testCase, index) => {
          const isExpanded = expandedCase === index
          const isEditing = editingCase === index
          const isSelected = selectedCases.has(index)

          return (
            <div
              key={index}
              className={clsx(
                'bg-dark-900 border rounded-xl transition-all overflow-hidden',
                isSelected
                  ? 'border-primary-500 shadow-nebula'
                  : 'border-dark-800'
              )}
            >
              {/* Header */}
              <div className="p-6">
                <div className="flex items-start space-x-4">
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(index)}
                    className="mt-1 w-5 h-5 rounded border-dark-700 bg-dark-800 text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 cursor-pointer"
                  />

                  {/* Content */}
                  <div className="flex-1">
                    <div
                      className="cursor-pointer"
                      onClick={() => setExpandedCase(isExpanded ? null : index)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-100 flex-1">
                          Test Case {index + 1}: {testCase.title || testCase.objective}
                        </h3>
                        <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors ml-4">
                          {isExpanded ? (
                            <ChevronUp size={20} className="text-gray-400" />
                          ) : (
                            <ChevronDown size={20} className="text-gray-400" />
                          )}
                        </button>
                      </div>

                      {/* Quick Info */}
                      {!isExpanded && (
                        <div className="flex flex-wrap gap-2">
                          {testCase.priority && (
                            <span className="px-2 py-1 bg-dark-800 rounded-md text-xs text-gray-400">
                              Priority: <span className="text-primary-400 font-medium">{testCase.priority}</span>
                            </span>
                          )}
                          {testCase.steps && (
                            <span className="px-2 py-1 bg-dark-800 rounded-md text-xs text-gray-400">
                              {testCase.steps.filter(s => typeof s === 'string' ? s.startsWith('Step ') : true).length} steps
                            </span>
                          )}
                          {testCase.tags && testCase.tags.length > 0 && (
                            <span className="px-2 py-1 bg-dark-800 rounded-md text-xs text-gray-400">
                              {testCase.tags.join(', ')}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Expanded Content */}
                    {isExpanded && (
                      <div className="mt-4 space-y-4">
                        {/* Objective */}
                        {testCase.objective && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Objective</h4>
                            <p className="text-gray-400 text-sm">{testCase.objective}</p>
                          </div>
                        )}

                        {/* Preconditions */}
                        {testCase.preconditions && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Preconditions</h4>
                            {typeof testCase.preconditions === 'string' ? (
                              <p className="text-gray-400 text-sm">{testCase.preconditions}</p>
                            ) : (
                              <ul className="space-y-1">
                                {testCase.preconditions.map((precond, i) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <span className="text-primary-400 text-xs mt-1">•</span>
                                    <span className="text-gray-400 text-sm">{precond}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}

                        {/* Test Steps */}
                        {testCase.steps && testCase.steps.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-3">Test Steps</h4>
                            <div className="space-y-3">
                              {testCase.steps.map((step, i) => {
                                // Handle both string format (legacy) and object format (new)
                                const isString = typeof step === 'string'
                                const isStepLine = isString && step.startsWith('Step ')
                                const isExpectedLine = isString && step.startsWith('Expected Result:')

                                // Skip "Expected Result:" lines as they'll be shown with their corresponding step
                                if (isExpectedLine) return null

                                // For string steps, find the next expected result if it exists
                                let expectedResult = null
                                if (isString && isStepLine && i + 1 < testCase.steps.length) {
                                  const nextLine = testCase.steps[i + 1]
                                  if (typeof nextLine === 'string' && nextLine.startsWith('Expected Result:')) {
                                    expectedResult = nextLine.replace('Expected Result:', '').trim()
                                  }
                                }

                                const stepText = isString
                                  ? (isStepLine ? step.replace(/^Step \d+:\s*/, '') : step)
                                  : (step.action || step.step)
                                const stepNumber = isString && isStepLine
                                  ? testCase.steps.slice(0, i + 1).filter(s => typeof s === 'string' && s.startsWith('Step ')).length
                                  : i + 1

                                return (
                                  <div key={i} className="bg-dark-800 rounded-lg p-4">
                                    <div className="flex items-start space-x-3">
                                      <div className="w-8 h-8 rounded-full bg-primary-500/10 border border-primary-500/30 flex items-center justify-center flex-shrink-0">
                                        <span className="text-primary-400 font-semibold text-sm">{stepNumber}</span>
                                      </div>
                                      <div className="flex-1">
                                        <p className="text-gray-200 font-medium mb-2">{stepText}</p>
                                        {(expectedResult || (!isString && step.expected_result)) && (
                                          <div className="mt-2 pl-4 border-l-2 border-green-500/30">
                                            <p className="text-xs text-gray-400 mb-1">Expected Result:</p>
                                            <p className="text-green-400/80 text-sm">{expectedResult || step.expected_result}</p>
                                          </div>
                                        )}
                                        {!isString && step.data && (
                                          <div className="mt-2 pl-4 border-l-2 border-blue-500/30">
                                            <p className="text-xs text-gray-400 mb-1">Test Data:</p>
                                            <p className="text-blue-400/80 text-sm">{step.data}</p>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                )
                              }).filter(Boolean)}
                            </div>
                          </div>
                        )}

                        {/* Expected Results */}
                        {testCase.expected_results && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Expected Results</h4>
                            <p className="text-gray-400 text-sm">{testCase.expected_results}</p>
                          </div>
                        )}

                        {/* Tags */}
                        {testCase.tags && testCase.tags.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Tags</h4>
                            <div className="flex flex-wrap gap-2">
                              {testCase.tags.map((tag, i) => (
                                <span key={i} className="px-3 py-1 bg-primary-500/10 border border-primary-500/30 rounded-full text-primary-400 text-xs">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty State */}
      {cases.length === 0 && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-12 text-center">
          <TestTube2 size={48} className="text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No test cases yet</h3>
          <p className="text-gray-400">Generate test cases from a Jira ticket to get started</p>
        </div>
      )}

      {/* Traceability Matrix Modal */}
      {showTraceability && (
        <TraceabilityMatrix
          testCases={cases}
          requirements={requirements}
          onClose={() => setShowTraceability(false)}
        />
      )}
    </div>
  )
}
