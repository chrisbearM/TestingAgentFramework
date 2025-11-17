import React, { useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, Lightbulb, Copy, Plus, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import clsx from 'clsx'

export default function TestReviewPanel({ review, onAcceptSuggestion, onRequestAdditionalSuggestions, isGenerating }) {
  const [expandedSections, setExpandedSections] = useState({
    strengths: true,
    issues: true,
    suggestions: true,
    missingScenarios: false,
    redundantTests: false,
    coverage: false
  })

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  // Helper to get color based on score
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Helper to get rating badge color
  const getRatingColor = (rating) => {
    switch (rating) {
      case 'excellent': return 'bg-green-500/10 border-green-500/30 text-green-400'
      case 'good': return 'bg-blue-500/10 border-blue-500/30 text-blue-400'
      case 'fair': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
      case 'poor': return 'bg-red-500/10 border-red-500/30 text-red-400'
      default: return 'bg-gray-500/10 border-gray-500/30 text-gray-400'
    }
  }

  // Helper to get severity badge color
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/10 border-red-500/30 text-red-400'
      case 'high': return 'bg-orange-500/10 border-orange-500/30 text-orange-400'
      case 'medium': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
      case 'low': return 'bg-blue-500/10 border-blue-500/30 text-blue-400'
      default: return 'bg-gray-500/10 border-gray-500/30 text-gray-400'
    }
  }

  // Helper to get importance badge color
  const getImportanceColor = (importance) => {
    switch (importance) {
      case 'high': return 'bg-red-500/10 border-red-500/30 text-red-400'
      case 'medium': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
      case 'low': return 'bg-blue-500/10 border-blue-500/30 text-blue-400'
      default: return 'bg-gray-500/10 border-gray-500/30 text-gray-400'
    }
  }

  const overallScore = review.overall_score || 0
  const qualityRating = review.quality_rating || 'unknown'
  const summary = review.summary || 'No summary available'
  const strengths = review.strengths || []
  const issues = review.issues || []
  const suggestions = review.suggestions || []
  const missingScenarios = review.missing_scenarios || []
  const redundantTests = review.redundant_tests || []
  const coverageAnalysis = review.coverage_analysis || {}

  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden">
      {/* Header with Score */}
      <div className="p-6 border-b border-dark-800 bg-gradient-to-r from-primary-500/5 to-transparent">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-100 mb-1">AI Test Review</h2>
            <p className="text-gray-400">Comprehensive quality analysis of your test cases</p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Overall Score */}
            <div className="text-center">
              <div className={clsx('text-4xl font-bold', getScoreColor(overallScore))}>
                {overallScore}
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-wide">Score</div>
            </div>
            {/* Quality Rating Badge */}
            <div className={clsx('px-4 py-2 rounded-lg border text-sm font-semibold uppercase', getRatingColor(qualityRating))}>
              {qualityRating}
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="p-4 bg-dark-800/50 rounded-lg border border-dark-700">
          <p className="text-gray-300 text-sm leading-relaxed">{summary}</p>
        </div>
      </div>

      {/* Strengths Section */}
      {strengths.length > 0 && (
        <div className="border-b border-dark-800">
          <button
            onClick={() => toggleSection('strengths')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <CheckCircle className="text-green-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Strengths</h3>
                <p className="text-sm text-gray-500">{strengths.length} positive aspects identified</p>
              </div>
            </div>
            {expandedSections.strengths ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.strengths && (
            <div className="px-6 pb-6 space-y-2">
              {strengths.map((strength, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-green-500/5 border border-green-500/20 rounded-lg">
                  <CheckCircle className="text-green-400 flex-shrink-0 mt-0.5" size={16} />
                  <p className="text-sm text-gray-300">{strength}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Issues Section */}
      {issues.length > 0 && (
        <div className="border-b border-dark-800">
          <button
            onClick={() => toggleSection('issues')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <XCircle className="text-red-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Issues Found</h3>
                <p className="text-sm text-gray-500">{issues.length} issues requiring attention</p>
              </div>
            </div>
            {expandedSections.issues ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.issues && (
            <div className="px-6 pb-6 space-y-3">
              {issues.map((issue, index) => (
                <div key={index} className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-300">{issue.test_case}</span>
                      <span className={clsx('text-xs px-2 py-0.5 rounded border', getSeverityColor(issue.severity))}>
                        {issue.severity}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">
                    <span className="font-medium text-red-400">Issue:</span> {issue.issue}
                  </p>
                  <p className="text-sm text-gray-400">
                    <span className="font-medium text-green-400">Suggestion:</span> {issue.suggestion}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* General Suggestions Section */}
      {suggestions.length > 0 && (
        <div className="border-b border-dark-800">
          <button
            onClick={() => toggleSection('suggestions')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <Lightbulb className="text-yellow-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Improvement Suggestions</h3>
                <p className="text-sm text-gray-500">{suggestions.length} actionable improvements</p>
              </div>
            </div>
            {expandedSections.suggestions ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.suggestions && (
            <div className="px-6 pb-6">
              <div className="space-y-3 mb-4">
                {suggestions.map((suggestion, index) => (
                  <div key={index} className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <Lightbulb className="text-yellow-400 flex-shrink-0 mt-0.5" size={16} />
                      <div className="flex-1">
                        <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">{suggestion.category}</div>
                        <p className="text-sm text-gray-300">{suggestion.suggestion}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {onRequestAdditionalSuggestions && (
                <button
                  onClick={() => onRequestAdditionalSuggestions({ suggestions, issues, missingScenarios })}
                  disabled={isGenerating}
                  className={clsx(
                    "w-full px-4 py-3 text-white font-medium rounded-lg transition-colors flex items-center justify-center space-x-2",
                    isGenerating
                      ? "bg-gray-600 cursor-not-allowed"
                      : "bg-primary-500 hover:bg-primary-600"
                  )}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      <span>Implementing Improvements...</span>
                    </>
                  ) : (
                    <>
                      <Lightbulb size={18} />
                      <span>Implement Improvement Suggestions</span>
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Missing Scenarios Section */}
      {missingScenarios.length > 0 && (
        <div className="border-b border-dark-800">
          <button
            onClick={() => toggleSection('missingScenarios')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <AlertTriangle className="text-orange-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Missing Scenarios</h3>
                <p className="text-sm text-gray-500">{missingScenarios.length} scenarios not yet covered</p>
              </div>
            </div>
            {expandedSections.missingScenarios ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.missingScenarios && (
            <div className="px-6 pb-6 space-y-3">
              {missingScenarios.map((scenario, index) => (
                <div key={index} className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-sm font-medium text-gray-300">{scenario.scenario}</span>
                    <span className={clsx('text-xs px-2 py-0.5 rounded border ml-2 flex-shrink-0', getImportanceColor(scenario.importance))}>
                      {scenario.importance}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{scenario.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Redundant Tests Section */}
      {redundantTests.length > 0 && (
        <div className="border-b border-dark-800">
          <button
            onClick={() => toggleSection('redundantTests')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <Copy className="text-blue-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Redundant Tests</h3>
                <p className="text-sm text-gray-500">{redundantTests.length} potential duplicates found</p>
              </div>
            </div>
            {expandedSections.redundantTests ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.redundantTests && (
            <div className="px-6 pb-6 space-y-3">
              {redundantTests.map((redundancy, index) => (
                <div key={index} className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg">
                  <div className="mb-2">
                    <span className="text-xs uppercase tracking-wide text-gray-500">Overlapping Tests:</span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {redundancy.test_cases?.map((tc, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded">
                          {tc}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{redundancy.reason}</p>
                  <p className="text-xs text-green-400">
                    <span className="font-medium">Recommendation:</span> {redundancy.recommendation}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Coverage Analysis Section */}
      {Object.keys(coverageAnalysis).length > 0 && (
        <div>
          <button
            onClick={() => toggleSection('coverage')}
            className="w-full p-6 flex items-center justify-between hover:bg-dark-800/50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <TrendingUp className="text-purple-400" size={24} />
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-100">Coverage Analysis</h3>
                <p className="text-sm text-gray-500">Detailed scenario coverage breakdown</p>
              </div>
            </div>
            {expandedSections.coverage ? <ChevronUp size={20} className="text-gray-400" /> : <ChevronDown size={20} className="text-gray-400" />}
          </button>
          {expandedSections.coverage && (
            <div className="px-6 pb-6">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-400">{coverageAnalysis.positive_scenarios || 'N/A'}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Positive Scenarios</div>
                </div>
                <div className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-400">{coverageAnalysis.negative_scenarios || 'N/A'}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Negative Scenarios</div>
                </div>
                <div className="p-4 bg-dark-800/50 border border-dark-700 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-400">{coverageAnalysis.edge_cases || 'N/A'}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Edge Cases</div>
                </div>
              </div>
              {coverageAnalysis.gaps && coverageAnalysis.gaps.length > 0 && (
                <div className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-lg">
                  <div className="text-sm font-medium text-orange-400 mb-2">Coverage Gaps:</div>
                  <ul className="space-y-1">
                    {coverageAnalysis.gaps.map((gap, index) => (
                      <li key={index} className="text-sm text-gray-400 flex items-start space-x-2">
                        <span className="text-orange-400">•</span>
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
