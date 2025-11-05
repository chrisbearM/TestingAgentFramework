import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Edit2, Save, X, CheckSquare, Download } from 'lucide-react'
import clsx from 'clsx'

export default function TestCaseEditor({ testCases, ticketInfo }) {
  const [cases, setCases] = useState(testCases)
  const [expandedCase, setExpandedCase] = useState(0)
  const [editingCase, setEditingCase] = useState(null)
  const [selectedCases, setSelectedCases] = useState(new Set())

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

  const handleExport = () => {
    const selectedTestCases = cases.filter((_, i) => selectedCases.has(i))
    const jsonData = JSON.stringify({
      ticket: ticketInfo,
      test_cases: selectedTestCases,
      exported_at: new Date().toISOString()
    }, null, 2)

    const blob = new Blob([jsonData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test_cases_${ticketInfo.key}.json`
    a.click()
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
            onClick={selectAll}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors flex items-center space-x-2"
          >
            <CheckSquare size={18} />
            <span>{selectedCases.size === cases.length ? 'Deselect All' : 'Select All'}</span>
          </button>
          <button
            onClick={handleExport}
            disabled={selectedCases.size === 0}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center space-x-2 shadow-nebula"
          >
            <Download size={18} />
            <span>Export ({selectedCases.size})</span>
          </button>
        </div>
      </div>

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
                              {testCase.steps.length} steps
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
                              {testCase.steps.map((step, i) => (
                                <div key={i} className="bg-dark-800 rounded-lg p-4">
                                  <div className="flex items-start space-x-3">
                                    <div className="w-8 h-8 rounded-full bg-primary-500/10 border border-primary-500/30 flex items-center justify-center flex-shrink-0">
                                      <span className="text-primary-400 font-semibold text-sm">{i + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-200 font-medium mb-2">{step.action || step.step}</p>
                                      {step.expected_result && (
                                        <div className="mt-2 pl-4 border-l-2 border-green-500/30">
                                          <p className="text-xs text-gray-400 mb-1">Expected Result:</p>
                                          <p className="text-green-400/80 text-sm">{step.expected_result}</p>
                                        </div>
                                      )}
                                      {step.data && (
                                        <div className="mt-2 pl-4 border-l-2 border-blue-500/30">
                                          <p className="text-xs text-gray-400 mb-1">Test Data:</p>
                                          <p className="text-blue-400/80 text-sm">{step.data}</p>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
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
    </div>
  )
}
