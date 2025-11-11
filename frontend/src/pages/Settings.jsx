import React, { useState, useEffect } from 'react'
import { Save, Settings as SettingsIcon, Sparkles, Target, AlertTriangle, CheckCircle } from 'lucide-react'
import api from '../api/client'

export default function Settings() {
  const [settings, setSettings] = useState({
    multiAgentMode: true,
    maxIterations: 3,
    qualityThreshold: 80,
    autoValidation: true,
    enableCriticAgent: true,
    enableRefinement: true
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await api.get('/settings')
      setSettings(response.data)
    } catch (error) {
      console.error('Failed to load settings:', error)
      // Use defaults if loading fails
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveMessage('')

    try {
      await api.post('/settings', settings)
      setSaveMessage('Settings saved successfully!')

      setTimeout(() => {
        setSaveMessage('')
      }, 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveMessage('Failed to save settings. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }

  if (loading) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-400">Loading settings...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <SettingsIcon className="text-primary-500" size={32} />
          <h1 className="text-3xl font-bold text-gray-100">Settings & Preferences</h1>
        </div>
        <p className="text-gray-400">
          Configure multi-agent behavior and quality standards
        </p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Multi-Agent Mode Section */}
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6">
          <div className="flex items-start space-x-3 mb-4">
            <Sparkles className="text-purple-400 flex-shrink-0 mt-1" size={24} />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-100 mb-1">Multi-Agent Mode</h2>
              <p className="text-gray-400 text-sm">
                Enable collaborative multi-agent workflows for improved quality
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.multiAgentMode}
                onChange={(e) => handleChange('multiAgentMode', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-dark-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
            </label>
          </div>

          {settings.multiAgentMode && (
            <div className="ml-9 space-y-4 pt-4 border-t border-dark-800">
              {/* Enable Critic Agent */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-200 font-medium">Enable Critic Agent</p>
                  <p className="text-gray-400 text-sm">Review test cases for quality issues</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enableCriticAgent}
                    onChange={(e) => handleChange('enableCriticAgent', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-dark-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                </label>
              </div>

              {/* Enable Refinement */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-200 font-medium">Enable Refinement Agent</p>
                  <p className="text-gray-400 text-sm">Automatically improve low-quality test cases</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enableRefinement}
                    onChange={(e) => handleChange('enableRefinement', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-dark-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                </label>
              </div>

              {/* Max Iterations */}
              <div>
                <label className="block text-gray-200 font-medium mb-2">
                  Maximum Refinement Iterations
                </label>
                <p className="text-gray-400 text-sm mb-3">
                  How many times should the system attempt to improve test cases? (1-5)
                </p>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={settings.maxIterations}
                  onChange={(e) => handleChange('maxIterations', parseInt(e.target.value))}
                  className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-2">
                  <span>1 (Fast)</span>
                  <span className="text-primary-400 font-semibold">{settings.maxIterations}</span>
                  <span>5 (Thorough)</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quality Standards Section */}
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6">
          <div className="flex items-start space-x-3 mb-4">
            <Target className="text-green-400 flex-shrink-0 mt-1" size={24} />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-100 mb-1">Quality Standards</h2>
              <p className="text-gray-400 text-sm">
                Set minimum quality thresholds for test cases
              </p>
            </div>
          </div>

          <div className="ml-9 space-y-4">
            {/* Quality Threshold */}
            <div>
              <label className="block text-gray-200 font-medium mb-2">
                Minimum Quality Score
              </label>
              <p className="text-gray-400 text-sm mb-3">
                Test cases below this score will be automatically refined (0-100)
              </p>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={settings.qualityThreshold}
                onChange={(e) => handleChange('qualityThreshold', parseInt(e.target.value))}
                className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer accent-green-500"
              />
              <div className="flex justify-between text-sm text-gray-400 mt-2">
                <span>0 (Lenient)</span>
                <span className="text-green-400 font-semibold">{settings.qualityThreshold}</span>
                <span>100 (Strict)</span>
              </div>

              {/* Quality Indicator */}
              <div className="mt-4 p-3 bg-dark-800 rounded-lg">
                {settings.qualityThreshold >= 80 ? (
                  <div className="flex items-center space-x-2 text-green-400">
                    <CheckCircle size={18} />
                    <span className="text-sm">High quality standard - expect thorough reviews</span>
                  </div>
                ) : settings.qualityThreshold >= 60 ? (
                  <div className="flex items-center space-x-2 text-yellow-400">
                    <AlertTriangle size={18} />
                    <span className="text-sm">Medium quality standard - balanced approach</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 text-gray-400">
                    <AlertTriangle size={18} />
                    <span className="text-sm">Low quality standard - minimal refinement</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Validation Section */}
        <div className="bg-dark-900 border border-dark-800 rounded-xl p-6">
          <div className="flex items-start space-x-3 mb-4">
            <CheckCircle className="text-blue-400 flex-shrink-0 mt-1" size={24} />
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-100 mb-1">Validation & Coverage</h2>
              <p className="text-gray-400 text-sm">
                Automatic validation of test coverage and gaps
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoValidation}
                onChange={(e) => handleChange('autoValidation', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-dark-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
            </label>
          </div>

          {settings.autoValidation && (
            <div className="ml-9 pt-4 border-t border-dark-800">
              <p className="text-gray-400 text-sm">
                When enabled, the system will automatically validate coverage and detect duplicates after test ticket generation.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex items-center justify-between bg-dark-900 border border-dark-800 rounded-xl p-6">
        <div>
          {saveMessage && (
            <p className={`text-sm font-medium ${
              saveMessage.includes('success') ? 'text-green-400' : 'text-red-400'
            }`}>
              {saveMessage}
            </p>
          )}
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors shadow-nebula flex items-center space-x-2"
        >
          <Save size={18} />
          <span>{saving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>
    </div>
  )
}
