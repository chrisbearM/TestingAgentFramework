import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Edit2, Save, X, CheckSquare, Download, Target, Sparkles, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import TraceabilityMatrix from './TraceabilityMatrix'

export default function TestCaseEditor({ testCases, ticketInfo, requirements }) {
  const [cases, setCases] = useState(testCases)
  const [expandedCase, setExpandedCase] = useState(0)
  const [editingCase, setEditingCase] = useState(null)
  const [selectedCases, setSelectedCases] = useState(new Set())
  const [exportFormat, setExportFormat] = useState('csv')
  const [exporting, setExporting] = useState(false)
  const [showTraceability, setShowTraceability] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [reviewProgress, setReviewProgress] = useState('')

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

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Determine file extension
      const extension = exportFormat === 'xlsx' ? 'xlsx' : 'csv'
      const suffix = exportFormat === 'testrail' ? '_testrail' : ''
      link.setAttribute('download', `test_cases_${ticketInfo.key}${suffix}.${extension}`)

      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Failed to export test cases. Please try again.')
    } finally {
      setExporting(false)
    }
  }

  const handleReviewAndImprove = async () => {
    setReviewing(true)
    setReviewProgress('Analyzing test cases with Critic Agent...')

    try {
      const response = await api.post('/test-cases/review-and-improve', {
        test_cases: cases,
        ticket_info: ticketInfo,
        requirements: requirements
      })

      if (response.data.improved_cases) {
        setReviewProgress('Review complete! Applying improvements...')
        setCases(response.data.improved_cases)

        setTimeout(() => {
          alert(`Review complete!\n\nQuality Score: ${response.data.quality_score}/100\n\nImprovements:\n${response.data.improvements?.join('\n') || 'Test cases have been enhanced'}`)
          setReviewProgress('')
        }, 500)
      }
    } catch (error) {
      console.error('Review failed:', error)
      alert(`Failed to review test cases: ${error.response?.data?.detail || error.message}`)
      setReviewProgress('')
    } finally {
      setReviewing(false)
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
            onClick={handleReviewAndImprove}
            disabled={reviewing || cases.length === 0}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            {reviewing ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Reviewing...</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Review & Improve</span>
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
                        {testCase.preconditions && testCase.preconditions.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-2">Preconditions</h4>
                            <ul className="space-y-1">
                              {testCase.preconditions.map((precond, i) => (
                                <li key={i} className="flex items-start space-x-2">
                                  <span className="text-primary-400 text-xs mt-1">•</span>
                                  <span className="text-gray-400 text-sm">{precond}</span>
                                </li>
                              ))}
                            </ul>
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

                        {/* Edit Button */}
                        <div className="flex justify-end pt-4 border-t border-dark-800">
                          <button
                            onClick={() => setEditingCase(isEditing ? null : index)}
                            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors flex items-center space-x-2"
                          >
                            <Edit2 size={16} />
                            <span>Edit Test Case</span>
                          </button>
                        </div>
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
