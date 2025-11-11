import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Target, CheckCircle, XCircle, AlertTriangle, TrendingUp, Award, Lightbulb, Wrench, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import api from '../api/client'
import CoverageFixesModal from './CoverageFixesModal'

export default function CoverageReviewPanel({ coverageReview, testTickets, epicData, childTickets, existingTestTickets, onFixesApplied }) {
  const [expandedSection, setExpandedSection] = useState('gaps')
  const [generatingFixes, setGeneratingFixes] = useState(false)
  const [fixes, setFixes] = useState(null)
  const [showFixesModal, setShowFixesModal] = useState(false)

  if (!coverageReview) {
    return null
  }

  const {
    coverage_score,
    coverage_level,
    epic_coverage,
    child_ticket_coverage,
    gaps,
    strengths,
    recommendations,
    overall_assessment
  } = coverageReview

  const existingTestCount = existingTestTickets?.length || 0
  const newTestCount = testTickets?.length || 0
  const totalTestCount = existingTestCount + newTestCount

  const handleGenerateFixes = async () => {
    setGeneratingFixes(true)
    try {
      const response = await api.post('/test-tickets/fix-coverage', {
        coverage_review: coverageReview,
        existing_tickets: testTickets || [],
        epic_data: epicData,
        child_tickets: childTickets || []
      })

      setFixes(response.data)
      setShowFixesModal(true)
    } catch (error) {
      console.error('Failed to generate fixes:', error)
      alert(`Failed to generate fixes: ${error.response?.data?.detail || error.message}`)
    } finally {
      setGeneratingFixes(false)
    }
  }

  const handleApplyFixes = async (newTickets, ticketUpdates) => {
    try {
      const response = await api.post('/test-tickets/apply-fixes', {
        epic_key: epicData?.key,
        new_tickets: newTickets,
        ticket_updates: ticketUpdates,
        epic_data: epicData,
        child_tickets: childTickets
      })

      setShowFixesModal(false)
      alert(`Successfully applied ${response.data.applied_count} fixes!`)

      // Notify parent component to refresh tickets AND updated coverage
      if (onFixesApplied) {
        onFixesApplied(response.data.tickets, response.data.updated_coverage_review)
      }
    } catch (error) {
      console.error('Failed to apply fixes:', error)
      alert(`Failed to apply fixes: ${error.response?.data?.detail || error.message}`)
    }
  }

  const getCoverageLevelColor = (level) => {
    switch (level) {
      case 'Comprehensive':
        return 'text-green-400'
      case 'Adequate':
        return 'text-yellow-400'
      case 'Insufficient':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getCoverageLevelBg = (level) => {
    switch (level) {
      case 'Comprehensive':
        return 'bg-green-900/20 border-green-800'
      case 'Adequate':
        return 'bg-yellow-900/20 border-yellow-800'
      case 'Insufficient':
        return 'bg-red-900/20 border-red-800'
      default:
        return 'bg-gray-900/20 border-gray-800'
    }
  }

  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'Critical':
        return {
          color: 'text-red-400',
          bg: 'bg-red-900/20',
          border: 'border-red-800',
          icon: XCircle
        }
      case 'Important':
        return {
          color: 'text-yellow-400',
          bg: 'bg-yellow-900/20',
          border: 'border-yellow-800',
          icon: AlertTriangle
        }
      case 'Minor':
        return {
          color: 'text-blue-400',
          bg: 'bg-blue-900/20',
          border: 'border-blue-800',
          icon: AlertTriangle
        }
      default:
        return {
          color: 'text-gray-400',
          bg: 'bg-gray-900/20',
          border: 'border-gray-800',
          icon: AlertTriangle
        }
    }
  }

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <Target className="text-primary-500" size={28} />
          <div>
            <h3 className="text-xl font-bold text-gray-100">Coverage Review</h3>
            <p className="text-sm text-gray-400 mt-1">
              AI-powered analysis of test ticket coverage
            </p>
          </div>
        </div>
        <div className={clsx('px-4 py-2 border rounded-lg', getCoverageLevelBg(coverage_level))}>
          <div className="flex items-center space-x-2">
            <TrendingUp size={18} className={getCoverageLevelColor(coverage_level)} />
            <span className={clsx('text-2xl font-bold', getCoverageLevelColor(coverage_level))}>
              {coverage_score}%
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">{coverage_level}</p>
        </div>
      </div>

      {/* Overall Assessment */}
      {overall_assessment && (
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
          <p className="text-sm text-gray-300 leading-relaxed">{overall_assessment}</p>
        </div>
      )}

      {/* Test Ticket Breakdown */}
      {totalTestCount > 0 && (
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-200 mb-3">Test Coverage Breakdown</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-400">{existingTestCount}</p>
              <p className="text-xs text-gray-400 mt-1">Existing Test Tickets</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">{newTestCount}</p>
              <p className="text-xs text-gray-400 mt-1">Newly Generated</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary-400">{totalTestCount}</p>
              <p className="text-xs text-gray-400 mt-1">Total Test Tickets</p>
            </div>
          </div>
        </div>
      )}

      {/* Fix Coverage Gaps Button */}
      {gaps && gaps.length > 0 && (
        <div className="flex justify-center">
          <button
            onClick={handleGenerateFixes}
            disabled={generatingFixes}
            className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-lg flex items-center space-x-2"
          >
            {generatingFixes ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>Generating Fixes...</span>
              </>
            ) : (
              <>
                <Wrench size={20} />
                <span>Fix Coverage Gaps</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Coverage Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Epic Coverage */}
        {epic_coverage && (
          <div className="bg-dark-800 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Award className="text-primary-400" size={18} />
              <h4 className="text-sm font-semibold text-gray-200">Epic Coverage</h4>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">Coverage</span>
                <span className="text-lg font-bold text-primary-400">
                  {epic_coverage.coverage_percentage || 0}%
                </span>
              </div>
              {epic_coverage.covered_requirements && epic_coverage.covered_requirements.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Covered Requirements:</p>
                  <p className="text-xs text-green-400">{epic_coverage.covered_requirements.length} items</p>
                </div>
              )}
              {epic_coverage.missing_requirements && epic_coverage.missing_requirements.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Missing Requirements:</p>
                  <p className="text-xs text-red-400">{epic_coverage.missing_requirements.length} items</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Child Ticket Coverage */}
        {child_ticket_coverage && (
          <div className="bg-dark-800 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <CheckCircle className="text-green-400" size={18} />
              <h4 className="text-sm font-semibold text-gray-200">Child Ticket Coverage</h4>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">Coverage</span>
                <span className="text-lg font-bold text-green-400">
                  {child_ticket_coverage.coverage_percentage || 0}%
                </span>
              </div>
              {child_ticket_coverage.covered_tickets && child_ticket_coverage.covered_tickets.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Covered:</p>
                  <p className="text-xs text-green-400">{child_ticket_coverage.covered_tickets.length} tickets</p>
                </div>
              )}
              {child_ticket_coverage.partially_covered_tickets && child_ticket_coverage.partially_covered_tickets.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Partially Covered:</p>
                  <p className="text-xs text-yellow-400">{child_ticket_coverage.partially_covered_tickets.length} tickets</p>
                </div>
              )}
              {child_ticket_coverage.uncovered_tickets && child_ticket_coverage.uncovered_tickets.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Uncovered:</p>
                  <p className="text-xs text-red-400">{child_ticket_coverage.uncovered_tickets.length} tickets</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Gaps Section */}
      {gaps && gaps.length > 0 && (
        <div className="border border-dark-700 rounded-lg overflow-hidden">
          <div
            className="p-4 bg-dark-800 cursor-pointer hover:bg-dark-750 transition-colors flex items-center justify-between"
            onClick={() => toggleSection('gaps')}
          >
            <div className="flex items-center space-x-2">
              <AlertTriangle className="text-yellow-400" size={18} />
              <h4 className="font-semibold text-gray-200">Coverage Gaps ({gaps.length})</h4>
            </div>
            {expandedSection === 'gaps' ? (
              <ChevronUp size={18} className="text-gray-400" />
            ) : (
              <ChevronDown size={18} className="text-gray-400" />
            )}
          </div>
          {expandedSection === 'gaps' && (
            <div className="p-4 space-y-3">
              {gaps.map((gap, index) => {
                const config = getSeverityConfig(gap.severity)
                const Icon = config.icon
                return (
                  <div key={index} className={clsx('border rounded-lg p-3', config.border, config.bg)}>
                    <div className="flex items-start space-x-3">
                      <Icon size={16} className={clsx(config.color, 'flex-shrink-0 mt-1')} />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={clsx('text-xs font-semibold px-2 py-1 rounded', config.bg, config.color)}>
                            {gap.severity}
                          </span>
                          <span className="text-xs text-gray-400 px-2 py-1 bg-dark-800 rounded">
                            {gap.type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-200 font-medium mb-2">{gap.description}</p>
                        {gap.recommendation && (
                          <div className="pl-3 border-l-2 border-primary-500/30">
                            <p className="text-xs text-gray-400 mb-1">Recommendation:</p>
                            <p className="text-sm text-primary-300">{gap.recommendation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Strengths Section */}
      {strengths && strengths.length > 0 && (
        <div className="border border-dark-700 rounded-lg overflow-hidden">
          <div
            className="p-4 bg-dark-800 cursor-pointer hover:bg-dark-750 transition-colors flex items-center justify-between"
            onClick={() => toggleSection('strengths')}
          >
            <div className="flex items-center space-x-2">
              <CheckCircle className="text-green-400" size={18} />
              <h4 className="font-semibold text-gray-200">Strengths ({strengths.length})</h4>
            </div>
            {expandedSection === 'strengths' ? (
              <ChevronUp size={18} className="text-gray-400" />
            ) : (
              <ChevronDown size={18} className="text-gray-400" />
            )}
          </div>
          {expandedSection === 'strengths' && (
            <div className="p-4 space-y-2">
              {strengths.map((strength, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <CheckCircle size={16} className="text-green-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-gray-300">{strength}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recommendations Section */}
      {recommendations && recommendations.length > 0 && (
        <div className="border border-primary-800 rounded-lg overflow-hidden">
          <div
            className="p-4 bg-primary-900/20 cursor-pointer hover:bg-primary-900/30 transition-colors flex items-center justify-between"
            onClick={() => toggleSection('recommendations')}
          >
            <div className="flex items-center space-x-2">
              <Lightbulb className="text-primary-400" size={18} />
              <h4 className="font-semibold text-gray-200">Recommendations ({recommendations.length})</h4>
            </div>
            {expandedSection === 'recommendations' ? (
              <ChevronUp size={18} className="text-gray-400" />
            ) : (
              <ChevronDown size={18} className="text-gray-400" />
            )}
          </div>
          {expandedSection === 'recommendations' && (
            <div className="p-4 space-y-2">
              {recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <Lightbulb size={16} className="text-primary-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-gray-300">{recommendation}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Coverage Fixes Modal */}
      {showFixesModal && fixes && (
        <CoverageFixesModal
          fixes={fixes}
          onClose={() => setShowFixesModal(false)}
          onApply={handleApplyFixes}
        />
      )}
    </div>
  )
}
