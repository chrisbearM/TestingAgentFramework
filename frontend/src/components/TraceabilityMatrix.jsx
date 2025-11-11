import React, { useMemo } from 'react'
import { X, CheckCircle, AlertTriangle, FileText, Target } from 'lucide-react'
import clsx from 'clsx'

export default function TraceabilityMatrix({ testCases, requirements, onClose }) {
  // Build traceability map: requirement_id -> test cases
  const traceabilityMap = useMemo(() => {
    const map = {}

    // Initialize map with all requirements
    if (requirements && Array.isArray(requirements)) {
      requirements.forEach(req => {
        const reqId = req.id || req.req_id
        if (reqId) {
          map[reqId] = {
            id: reqId,
            description: req.description || req.text || '',
            source: req.source || 'Unknown',
            cases: []
          }
        }
      })
    }

    // Map test cases to requirements
    if (testCases && Array.isArray(testCases)) {
      testCases.forEach(tc => {
        const reqId = tc.requirement_id
        if (reqId) {
          if (!map[reqId]) {
            // Requirement not in the list, add it
            map[reqId] = {
              id: reqId,
              description: tc.requirement_desc || 'No description',
              source: 'Test Case',
              cases: []
            }
          }
          map[reqId].cases.push(tc)
        } else {
          // Unmapped test case
          if (!map['UNMAPPED']) {
            map['UNMAPPED'] = {
              id: 'UNMAPPED',
              description: 'Test cases without requirement mapping',
              source: 'None',
              cases: []
            }
          }
          map['UNMAPPED'].cases.push(tc)
        }
      })
    }

    return map
  }, [testCases, requirements])

  const requirementsList = Object.values(traceabilityMap)

  // Calculate coverage statistics
  const stats = useMemo(() => {
    const total = requirementsList.filter(r => r.id !== 'UNMAPPED').length
    const complete = requirementsList.filter(r => r.id !== 'UNMAPPED' && r.cases.length === 3).length
    const partial = requirementsList.filter(r => r.id !== 'UNMAPPED' && r.cases.length > 0 && r.cases.length < 3).length
    const missing = requirementsList.filter(r => r.id !== 'UNMAPPED' && r.cases.length === 0).length
    const unmapped = traceabilityMap['UNMAPPED']?.cases.length || 0

    return { total, complete, partial, missing, unmapped }
  }, [requirementsList, traceabilityMap])

  const getCoverageStatus = (cases) => {
    if (cases.length === 0) return { status: 'missing', color: 'red', text: 'No Coverage' }
    if (cases.length === 3) return { status: 'complete', color: 'green', text: 'Complete (3/3)' }
    return { status: 'partial', color: 'yellow', text: `Partial (${cases.length}/3)` }
  }

  const getTestTypeColor = (testType) => {
    if (!testType) return 'text-gray-400'
    const type = testType.toLowerCase()
    if (type.includes('positive')) return 'text-green-400'
    if (type.includes('negative')) return 'text-red-400'
    if (type.includes('edge')) return 'text-yellow-400'
    return 'text-gray-400'
  }

  const getTestTypeIcon = (testType) => {
    if (!testType) return '○'
    const type = testType.toLowerCase()
    if (type.includes('positive')) return '✓'
    if (type.includes('negative')) return '✗'
    if (type.includes('edge')) return '◆'
    return '○'
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-900 rounded-xl border border-dark-800 w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-800">
          <div className="flex items-center space-x-3">
            <Target className="text-primary-500" size={24} />
            <div>
              <h2 className="text-2xl font-bold text-gray-100">Requirement Traceability Matrix</h2>
              <p className="text-sm text-gray-400 mt-1">
                Mapping of requirements to test cases for complete coverage verification
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

        {/* Statistics Bar */}
        <div className="p-6 border-b border-dark-800 bg-dark-950">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-dark-900 rounded-lg p-4 border border-dark-800">
              <div className="flex items-center space-x-2 mb-1">
                <FileText size={16} className="text-gray-400" />
                <span className="text-xs text-gray-400">Total Requirements</span>
              </div>
              <p className="text-2xl font-bold text-gray-100">{stats.total}</p>
            </div>

            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-1">
                <CheckCircle size={16} className="text-green-400" />
                <span className="text-xs text-green-400">Complete</span>
              </div>
              <p className="text-2xl font-bold text-green-400">{stats.complete}</p>
              <p className="text-xs text-gray-400 mt-1">3/3 test cases</p>
            </div>

            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-1">
                <AlertTriangle size={16} className="text-yellow-400" />
                <span className="text-xs text-yellow-400">Partial</span>
              </div>
              <p className="text-2xl font-bold text-yellow-400">{stats.partial}</p>
              <p className="text-xs text-gray-400 mt-1">1-2 test cases</p>
            </div>

            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-1">
                <X size={16} className="text-red-400" />
                <span className="text-xs text-red-400">Missing</span>
              </div>
              <p className="text-2xl font-bold text-red-400">{stats.missing}</p>
              <p className="text-xs text-gray-400 mt-1">0 test cases</p>
            </div>

            <div className="bg-gray-500/10 border border-gray-500/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-1">
                <AlertTriangle size={16} className="text-gray-400" />
                <span className="text-xs text-gray-400">Unmapped</span>
              </div>
              <p className="text-2xl font-bold text-gray-400">{stats.unmapped}</p>
              <p className="text-xs text-gray-400 mt-1">No requirement</p>
            </div>
          </div>
        </div>

        {/* Traceability List */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {requirementsList.map((req) => {
              const coverage = getCoverageStatus(req.cases)

              return (
                <div
                  key={req.id}
                  className={clsx(
                    'bg-dark-800 rounded-lg border overflow-hidden',
                    coverage.status === 'complete' && 'border-green-500/30',
                    coverage.status === 'partial' && 'border-yellow-500/30',
                    coverage.status === 'missing' && 'border-red-500/30',
                    req.id === 'UNMAPPED' && 'border-gray-500/30'
                  )}
                >
                  {/* Requirement Header */}
                  <div className={clsx(
                    'p-4 border-b border-dark-700',
                    coverage.status === 'complete' && 'bg-green-500/5',
                    coverage.status === 'partial' && 'bg-yellow-500/5',
                    coverage.status === 'missing' && 'bg-red-500/5',
                    req.id === 'UNMAPPED' && 'bg-gray-500/5'
                  )}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className={clsx(
                            'px-2 py-1 rounded text-xs font-mono font-semibold',
                            coverage.status === 'complete' && 'bg-green-500/20 text-green-400',
                            coverage.status === 'partial' && 'bg-yellow-500/20 text-yellow-400',
                            coverage.status === 'missing' && 'bg-red-500/20 text-red-400',
                            req.id === 'UNMAPPED' && 'bg-gray-500/20 text-gray-400'
                          )}>
                            {req.id}
                          </span>
                          <span className="text-xs text-gray-500">from {req.source}</span>
                        </div>
                        <p className="text-sm text-gray-300">{req.description}</p>
                      </div>

                      <div className={clsx(
                        'px-3 py-1 rounded-full text-xs font-medium ml-4',
                        coverage.status === 'complete' && 'bg-green-500/20 text-green-400',
                        coverage.status === 'partial' && 'bg-yellow-500/20 text-yellow-400',
                        coverage.status === 'missing' && 'bg-red-500/20 text-red-400',
                        req.id === 'UNMAPPED' && 'bg-gray-500/20 text-gray-400'
                      )}>
                        {coverage.text}
                      </div>
                    </div>
                  </div>

                  {/* Test Cases */}
                  {req.cases.length > 0 ? (
                    <div className="p-4 space-y-2">
                      {req.cases.map((tc, idx) => (
                        <div
                          key={idx}
                          className="flex items-start space-x-3 p-3 bg-dark-900 rounded-lg hover:bg-dark-950 transition-colors"
                        >
                          <span className={clsx(
                            'text-lg font-semibold mt-0.5',
                            getTestTypeColor(tc.test_type)
                          )}>
                            {getTestTypeIcon(tc.test_type)}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className={clsx(
                                'px-2 py-0.5 rounded text-xs font-medium',
                                tc.test_type?.toLowerCase().includes('positive') && 'bg-green-500/20 text-green-400',
                                tc.test_type?.toLowerCase().includes('negative') && 'bg-red-500/20 text-red-400',
                                tc.test_type?.toLowerCase().includes('edge') && 'bg-yellow-500/20 text-yellow-400',
                                !tc.test_type && 'bg-gray-500/20 text-gray-400'
                              )}>
                                {tc.test_type || 'Unknown Type'}
                              </span>
                              {tc.priority && (
                                <span className="text-xs text-gray-500">
                                  Priority: {tc.priority}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-300 font-medium">{tc.title}</p>
                            {tc.steps && (
                              <p className="text-xs text-gray-500 mt-1">
                                {Array.isArray(tc.steps) ? tc.steps.length : 0} steps
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-gray-500 text-sm">
                      No test cases mapped to this requirement
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-dark-800 bg-dark-950">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              <span className="font-semibold text-gray-300">Coverage Formula:</span> Each requirement should have exactly 3 test cases (1 Positive, 1 Negative, 1 Edge Case)
            </div>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
