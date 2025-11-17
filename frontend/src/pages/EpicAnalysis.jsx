import React, { useState, useEffect } from 'react'
import { Search, Loader2, FileText, Users, CheckCircle, XCircle, ArrowRight, ArrowLeft, Plus } from 'lucide-react'
import api from '../api/client'
import { useWebSocket } from '../context/WebSocketContext'
import { useEpicAnalysis } from '../context/EpicAnalysisContext'
import StrategicOptions from '../components/StrategicOptions'
import ProgressIndicator from '../components/ProgressIndicator'
import ReadinessAssessment from '../components/ReadinessAssessment'
import ManualTicketLoader from '../components/ManualTicketLoader'
import DocumentUpload from '../components/DocumentUpload'
import DraftRecoveryModal from '../components/DraftRecoveryModal'
import { useAutosave } from '../hooks/useAutosave'
import clsx from 'clsx'

// Helper function to safely extract text from Jira description
const extractDescription = (description) => {
  if (!description) return ''
  if (typeof description === 'string') return description

  // Handle Atlassian Document Format (ADF)
  if (description.type === 'doc' && description.content) {
    return extractTextFromADF(description)
  }

  return JSON.stringify(description)
}

const extractTextFromADF = (adf) => {
  if (!adf || !adf.content) return ''

  const extractFromNode = (node) => {
    let text = ''

    // Handle text nodes
    if (node.type === 'text' && node.text) {
      return node.text
    }

    // Handle nodes with content arrays
    if (node.content && Array.isArray(node.content)) {
      for (const child of node.content) {
        text += extractFromNode(child)
      }
    }

    // Add line breaks after certain node types
    if (node.type === 'paragraph' || node.type === 'heading') {
      text += '\n'
    } else if (node.type === 'listItem') {
      text = '• ' + text + '\n'
    } else if (node.type === 'codeBlock') {
      text = '\n' + text + '\n'
    } else if (node.type === 'hardBreak') {
      text += '\n'
    }

    return text
  }

  let result = ''
  for (const node of adf.content) {
    result += extractFromNode(node)
  }

  return result.trim()
}

export default function EpicAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showManualLoader, setShowManualLoader] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [showDraftRecovery, setShowDraftRecovery] = useState(false)
  const [availableDrafts, setAvailableDrafts] = useState([])
  const { progress, clearProgress } = useWebSocket()
  const {
    epicKey,
    setEpicKey,
    epic,
    setEpic,
    readiness,
    setReadiness,
    options,
    setOptions,
    currentStep,
    setCurrentStep,
    clearEpicAnalysis
  } = useEpicAnalysis()

  // Get or create session ID for autosave
  const getSessionId = () => {
    let sessionId = localStorage.getItem('ai_tester_session_id')
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('ai_tester_session_id', sessionId)
    }
    return sessionId
  }

  const sessionId = getSessionId()

  // Calculate progress percentage based on current step
  const calculateProgress = () => {
    if (!epic) return 0
    if (currentStep === 1) return 33
    if (currentStep === 2) return 66
    if (currentStep === 3) return 100
    return 0
  }

  // Set up autosave hook
  const { saveDraft, loadDraft, deleteDraft } = useAutosave(
    sessionId,
    'epic_analysis',
    epic && readiness ? { epic, readiness, options, currentStep } : {},
    {
      epic_key: epicKey,
      progress: calculateProgress(),
      summary: epic?.epic?.fields?.summary || 'Epic Analysis in Progress'
    },
    30000, // 30 second debounce
    Boolean(epic && !loading) // Only autosave when epic is loaded and not actively loading
  )

  // Check for drafts on mount
  useEffect(() => {
    const checkForDrafts = async () => {
      try {
        const response = await api.get(`/sessions/${sessionId}/drafts`, {
          params: { data_type: 'epic_analysis' }
        })

        if (response.data.drafts && response.data.drafts.length > 0) {
          setAvailableDrafts(response.data.drafts)
          setShowDraftRecovery(true)
        }
      } catch (error) {
        console.error('Failed to check for drafts:', error)
      }
    }

    checkForDrafts()
  }, [sessionId])

  // Handle resuming a draft
  const handleResumeDraft = async (draft) => {
    try {
      const response = await api.get(`/sessions/${sessionId}/drafts/${draft.id}`)
      const draftData = response.data.draft.data

      // Restore all state from draft
      if (draftData.epic) setEpic(draftData.epic)
      if (draftData.readiness) setReadiness(draftData.readiness)
      if (draftData.options) setOptions(draftData.options)
      if (draftData.currentStep) setCurrentStep(draftData.currentStep)
      if (draft.metadata?.epic_key) setEpicKey(draft.metadata.epic_key)

      setShowDraftRecovery(false)
      console.log('Draft resumed successfully:', draft.id)
    } catch (error) {
      console.error('Failed to resume draft:', error)
      setError('Failed to resume draft. Please try again.')
    }
  }

  // Handle discarding a draft
  const handleDiscardDraft = async (draft) => {
    try {
      await api.delete(`/sessions/${sessionId}/drafts/${draft.id}`)

      // Remove from available drafts list
      setAvailableDrafts(prev => prev.filter(d => d.id !== draft.id))

      // Close modal if no more drafts
      if (availableDrafts.length <= 1) {
        setShowDraftRecovery(false)
      }

      console.log('Draft discarded:', draft.id)
    } catch (error) {
      console.error('Failed to discard draft:', error)
    }
  }

  // Handle closing draft recovery modal
  const handleCloseDraftRecovery = () => {
    setShowDraftRecovery(false)
  }

  const handleLoadEpic = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    clearProgress()

    // Reset states
    clearEpicAnalysis()
    console.log('=== STARTING EPIC ANALYSIS ===')
    console.log('Epic Key:', epicKey)

    try {
      // Load Epic
      console.log('Step 1: Loading epic from Jira...')
      const epicResponse = await api.post('/epics/load', {
        epic_key: epicKey,
        include_attachments: true
      })
      console.log('Epic loaded successfully:', epicResponse.data)
      setEpic(epicResponse.data)
      console.log('Epic state set')

      // Assess Readiness
      console.log('Step 2: Assessing Epic readiness...')
      const readinessResponse = await api.post(`/epics/${epicKey}/readiness`)
      console.log('Readiness assessment complete:', readinessResponse.data)
      setReadiness(readinessResponse.data.readiness_assessment)
      console.log('Readiness state set')

      // Analyze Epic with multi-agent system
      console.log('Step 3: Starting strategic analysis...')

      // Create FormData if files are uploaded
      let analysisResponse
      if (uploadedFiles.length > 0) {
        const formData = new FormData()
        uploadedFiles.forEach((file) => {
          formData.append('files', file)
        })

        console.log(`Uploading ${uploadedFiles.length} documents...`)
        analysisResponse = await api.post(`/epics/${epicKey}/analyze`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      } else {
        analysisResponse = await api.post(`/epics/${epicKey}/analyze`)
      }

      console.log('=== ANALYSIS RESPONSE RECEIVED ===')
      console.log('Full response object:', analysisResponse)
      console.log('Response status:', analysisResponse.status)
      console.log('Response data:', analysisResponse.data)
      console.log('Response data type:', typeof analysisResponse.data)
      console.log('Response data keys:', Object.keys(analysisResponse.data || {}))

      // Check if data has the expected structure
      if (analysisResponse.data) {
        console.log('Has epic_key?', 'epic_key' in analysisResponse.data)
        console.log('Has options?', 'options' in analysisResponse.data)
        console.log('Has generated_at?', 'generated_at' in analysisResponse.data)

        if (analysisResponse.data.options) {
          console.log('Options is array?', Array.isArray(analysisResponse.data.options))
          console.log('Options length:', analysisResponse.data.options.length)
          console.log('First option:', analysisResponse.data.options[0])
        } else {
          console.error('WARNING: No options property in response data!')
        }
      } else {
        console.error('WARNING: No data in analysis response!')
      }

      console.log('Step 3: Setting options state...')
      setOptions(analysisResponse.data)
      console.log('Options state set. Current value:', analysisResponse.data)

      // Clear progress after successful analysis
      setTimeout(() => clearProgress(), 1000)

      // Advance to first step (Epic Info)
      setCurrentStep(1)

    } catch (err) {
      console.error('=== ERROR DURING EPIC ANALYSIS ===')
      console.error('Error object:', err)
      console.error('Error response:', err.response)
      console.error('Error response data:', err.response?.data)
      console.error('Error message:', err.message)
      setError(err.response?.data?.detail || err.message || 'Failed to load Epic')
    } finally {
      console.log('=== FINALLY BLOCK ===')
      console.log('Setting loading to false')
      setLoading(false)
    }
  }

  const handleTicketsAdded = (newTickets) => {
    // Merge new tickets with existing children
    if (epic && epic.children) {
      const existingKeys = new Set(epic.children.map(child => child.key))
      const uniqueNewTickets = newTickets.filter(ticket => !existingKeys.has(ticket.key))

      if (uniqueNewTickets.length > 0) {
        setEpic({
          ...epic,
          children: [...epic.children, ...uniqueNewTickets],
          child_count: epic.child_count + uniqueNewTickets.length
        })
      }
    }
  }

  const steps = [
    { number: 1, name: 'Epic Overview', description: 'Review epic details' },
    { number: 2, name: 'Readiness Assessment', description: 'Evaluate epic quality' },
    { number: 3, name: 'Strategic Options', description: 'Select testing approach' }
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 mb-2">Epic Analysis</h1>
          <p className="text-gray-400">
            Load an Epic and let our multi-agent AI system propose strategic approaches for test ticket generation
          </p>
        </div>
        {epic && (
          <button
            onClick={clearEpicAnalysis}
            className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors flex items-center space-x-2 border border-dark-700"
          >
            <Search size={16} />
            <span>New Analysis</span>
          </button>
        )}
      </div>

      {/* Compact Epic Info - Show at top when navigating steps */}
      {epic && (
        <div className="bg-dark-900 border border-dark-800 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="text-primary-400" size={20} />
              <div>
                <h3 className="font-semibold text-gray-100">{epic.epic.key}: {epic.epic.fields.summary}</h3>
                <p className="text-sm text-gray-400">
                  {epic.child_count} child {epic.child_count === 1 ? 'ticket' : 'tickets'} • {epic.epic.fields.status?.name}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowManualLoader(true)}
              className="px-3 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 font-medium rounded-lg transition-colors flex items-center space-x-2 border border-dark-700 text-sm"
              title="Manually add child tickets"
            >
              <Plus size={16} />
              <span>Add Tickets</span>
            </button>
          </div>
        </div>
      )}

      {/* Step Indicator - Show only when we have an epic loaded */}
      {epic && (
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <React.Fragment key={step.number}>
                <div className="flex items-center space-x-4">
                  <div
                    className={clsx(
                      'flex items-center justify-center w-10 h-10 rounded-full font-semibold transition-all',
                      currentStep >= step.number
                        ? 'bg-primary-500 text-white'
                        : 'bg-dark-800 text-gray-400 border border-dark-700'
                    )}
                  >
                    {currentStep > step.number ? (
                      <CheckCircle size={20} />
                    ) : (
                      step.number
                    )}
                  </div>
                  <div className="hidden sm:block">
                    <div className={clsx(
                      'font-medium',
                      currentStep >= step.number ? 'text-gray-100' : 'text-gray-500'
                    )}>
                      {step.name}
                    </div>
                    <div className="text-sm text-gray-500">{step.description}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={clsx(
                      'flex-1 h-0.5 mx-4 transition-all',
                      currentStep > step.number ? 'bg-primary-500' : 'bg-dark-700'
                    )}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Search Form - Hide when epic is loaded */}
      {!epic && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <form onSubmit={handleLoadEpic} className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <label htmlFor="epicKey" className="block text-sm font-medium text-gray-300 mb-2">
                  Epic Key
                </label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <input
                    type="text"
                    id="epicKey"
                    value={epicKey}
                    onChange={(e) => setEpicKey(e.target.value.toUpperCase())}
                    placeholder="e.g., UEX-17"
                    required
                    className="w-full pl-10 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Search size={18} />
                      <span>Analyze Epic</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Document Upload */}
            <DocumentUpload
              files={uploadedFiles}
              onFilesChange={setUploadedFiles}
              disabled={loading}
            />
          </form>

        {error && (
          <div className="mt-4 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-2">
            <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </div>
      )}

      {/* Progress Indicator */}
      {progress && <ProgressIndicator progress={progress} />}

      {/* Step 1: Epic Info */}
      {epic && currentStep === 1 && (
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6 mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-100 mb-1">
                {epic.epic.key}: {epic.epic.fields.summary}
              </h2>
              <p className="text-gray-400">
                {epic.child_count} child {epic.child_count === 1 ? 'ticket' : 'tickets'}
              </p>
            </div>
            <div className="px-3 py-1 bg-primary-500/10 border border-primary-500/20 rounded-full">
              <span className="text-primary-400 text-sm font-medium">{epic.epic.fields.status?.name}</span>
            </div>
          </div>

          {epic.epic.fields.description && (
            <div className="mt-4 p-4 bg-dark-800 rounded-lg">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
              <div className="text-gray-400 text-sm whitespace-pre-wrap overflow-y-auto" style={{maxHeight: 'none'}}>
                {extractDescription(epic.epic.fields.description)}
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-end mt-6 pt-6 border-t border-dark-800">
            <button
              onClick={() => setCurrentStep(2)}
              disabled={!readiness}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-dark-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <span>Continue to Readiness Assessment</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Readiness Assessment */}
      {readiness && epic && currentStep === 2 && (
        <div className="mb-8">
          <ReadinessAssessment
            assessment={readiness}
            epicData={{
              key: epic.epic.key,
              summary: epic.epic.fields.summary,
              description: extractDescription(epic.epic.fields.description)
            }}
          />

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-6">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <ArrowLeft size={18} />
              <span>Back to Epic Overview</span>
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              disabled={!options}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-dark-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <span>Continue to Strategic Options</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Strategic Options */}
      {options && currentStep === 3 && (
        <div>
          <StrategicOptions data={options} epicKey={epicKey} />

          {/* Navigation Buttons */}
          <div className="flex justify-start mt-6">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-6 py-3 bg-dark-800 hover:bg-dark-700 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            >
              <ArrowLeft size={18} />
              <span>Back to Readiness Assessment</span>
            </button>
          </div>
        </div>
      )}

      {/* Manual Ticket Loader Modal */}
      {showManualLoader && epic && (
        <ManualTicketLoader
          epicKey={epic.epic.key}
          onTicketsAdded={handleTicketsAdded}
          onClose={() => setShowManualLoader(false)}
        />
      )}

      {/* Draft Recovery Modal */}
      {showDraftRecovery && (
        <DraftRecoveryModal
          drafts={availableDrafts}
          onResume={handleResumeDraft}
          onDiscard={handleDiscardDraft}
          onClose={handleCloseDraftRecovery}
        />
      )}
    </div>
  )
}
