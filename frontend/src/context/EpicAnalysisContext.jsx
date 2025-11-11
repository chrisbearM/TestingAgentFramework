import React, { createContext, useContext, useState } from 'react'

const EpicAnalysisContext = createContext(null)

export function EpicAnalysisProvider({ children }) {
  const [epicKey, setEpicKey] = useState('')
  const [epic, setEpic] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [options, setOptions] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)

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
