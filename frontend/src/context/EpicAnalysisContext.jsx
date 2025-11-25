import React, { createContext, useContext, useState, useEffect } from 'react'

const EpicAnalysisContext = createContext(null)

export function EpicAnalysisProvider({ children }) {
  const [epicKey, setEpicKey] = useState('')
  const [epic, setEpic] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [options, setOptions] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isClearing, setIsClearing] = useState(false)  // Track if we're clearing history

  // Listen for history clear events
  useEffect(() => {
    const handleHistoryClear = () => {
      // Set clearing flag to prevent auto-save
      setIsClearing(true)

      // Clear all state when history is cleared
      setEpic(null)
      setReadiness(null)
      setOptions(null)
      setEpicKey('')
      setCurrentStep(0)
    }

    window.addEventListener('epicAnalysisHistoryCleared', handleHistoryClear)
    return () => window.removeEventListener('epicAnalysisHistoryCleared', handleHistoryClear)
  }, [])

  // Load epic analysis state from sessionStorage on mount
  useEffect(() => {
    try {
      const savedState = sessionStorage.getItem('epicAnalysisState')
      if (savedState) {
        const state = JSON.parse(savedState)
        if (state.epic) setEpic(state.epic)
        if (state.readiness) setReadiness(state.readiness)
        if (state.options) setOptions(state.options)
        if (state.epicKey) setEpicKey(state.epicKey)
        if (state.currentStep !== undefined) setCurrentStep(state.currentStep)
      }
    } catch (e) {
      console.error('Failed to load epic analysis state:', e)
    }
  }, [])

  // Save state to sessionStorage and history whenever it changes
  useEffect(() => {
    // Don't save if we're in the process of clearing history
    if (isClearing) return

    if (epic || readiness || options) {
      // Store only essential epic data to avoid quota issues
      const minimalEpic = epic ? {
        key: epic.key,
        fields: {
          summary: epic.fields?.summary,
          description: epic.fields?.description,
          status: epic.fields?.status
        }
      } : null

      const stateToSave = {
        epicKey,
        epic: minimalEpic,
        readiness,
        options,
        currentStep,
        epicSummary: epic?.fields?.summary || ''
      }

      try {
        sessionStorage.setItem('epicAnalysisState', JSON.stringify(stateToSave))
      } catch (e) {
        if (e.name === 'QuotaExceededError') {
          console.warn('Session storage quota exceeded, clearing old data')
          sessionStorage.removeItem('epicAnalysisHistory')
          try {
            sessionStorage.setItem('epicAnalysisState', JSON.stringify(stateToSave))
          } catch (e2) {
            console.error('Failed to save even after clearing history:', e2)
          }
        }
      }

      // Save to history if we have data
      if (epicKey && (readiness || options)) {
        const history = JSON.parse(sessionStorage.getItem('epicAnalysisHistory') || '[]')

        // Check if this epic already exists in history
        const existingIndex = history.findIndex(item => item.epicKey === epicKey)

        if (existingIndex !== -1) {
          // Update existing entry in place (don't reorder)
          history[existingIndex] = stateToSave
          sessionStorage.setItem('epicAnalysisHistory', JSON.stringify(history))
        } else {
          // New entry - add to the beginning
          history.unshift(stateToSave)
          // Keep only the last 10 entries
          const trimmedHistory = history.slice(0, 10)
          sessionStorage.setItem('epicAnalysisHistory', JSON.stringify(trimmedHistory))
        }

        window.dispatchEvent(new Event('epicAnalysisHistoryUpdated'))
      }
    }
  }, [epicKey, epic, readiness, options, currentStep, isClearing])

  const setEpicAnalysisData = (data) => {
    if (data.epic) setEpic(data.epic)
    if (data.readiness) setReadiness(data.readiness)
    if (data.options) setOptions(data.options)
    if (data.epicKey) setEpicKey(data.epicKey)
    if (data.currentStep !== undefined) setCurrentStep(data.currentStep)
  }

  const clearEpicAnalysis = () => {
    setEpic(null)
    setReadiness(null)
    setOptions(null)
    setCurrentStep(0)
    setEpicKey('')
  }

  return (
    <EpicAnalysisContext.Provider value={{
      epicKey,
      epic,
      readiness,
      options,
      currentStep,
      setEpicKey,
      setEpic,
      setReadiness,
      setOptions,
      setCurrentStep,
      setEpicAnalysisData,
      clearEpicAnalysis
    }}>
      {children}
    </EpicAnalysisContext.Provider>
  )
}

export function useEpicAnalysis() {
  const context = useContext(EpicAnalysisContext)
  if (!context) {
    throw new Error('useEpicAnalysis must be used within an EpicAnalysisProvider')
  }
  return context
}
