import React, { useState, useEffect } from 'react'
import { X, Save, AlertCircle, Star } from 'lucide-react'
import clsx from 'clsx'

export default function SaveViewModal({ isOpen, onClose, onSave, currentFilters, existingView = null }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isDefault, setIsDefault] = useState(false)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  // Pre-populate form if editing existing view
  useEffect(() => {
    if (existingView) {
      setName(existingView.name)
      setDescription(existingView.description || '')
      setIsDefault(existingView.is_default || false)
    } else {
      setName('')
      setDescription('')
      setIsDefault(false)
    }
    setError('')
  }, [existingView, isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('Please enter a name for this view')
      return
    }

    try {
      setSaving(true)
      await onSave({
        name: name.trim(),
        description: description.trim() || null,
        isDefault,
        filters: currentFilters
      })
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to save view')
    } finally {
      setSaving(false)
    }
  }

  // Get a summary of active filters
  const getFilterSummary = () => {
    if (!currentFilters) return 'No filters applied'

    const active = []
    if (currentFilters.epicKey) active.push(`Epic: ${currentFilters.epicKey}`)
    if (currentFilters.searchTerm) active.push(`Search: "${currentFilters.searchTerm}"`)
    if (currentFilters.status?.length > 0) active.push(`Status (${currentFilters.status.length})`)
    if (currentFilters.readiness?.length > 0) active.push(`Readiness (${currentFilters.readiness.length})`)
    if (currentFilters.testCount) active.push(`Tests: ${currentFilters.testCount.min}-${currentFilters.testCount.max}`)

    return active.length > 0 ? active.join(' • ') : 'No filters applied'
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-dark-900 border border-dark-800 rounded-xl max-w-xl w-full shadow-nebula-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-800">
          <div className="flex items-center space-x-3">
            <Save className="text-primary-500" size={24} />
            <div>
              <h2 className="text-xl font-bold text-gray-100">
                {existingView ? 'Update View' : 'Save View'}
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                Save your current filter configuration for quick access
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
            disabled={saving}
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* View Name */}
          <div>
            <label htmlFor="viewName" className="block text-sm font-medium text-gray-300 mb-2">
              View Name
            </label>
            <input
              type="text"
              id="viewName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Open Tickets, Critical Issues"
              required
              maxLength={50}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={saving}
            />
            <p className="text-xs text-gray-500 mt-1">{name.length}/50 characters</p>
          </div>

          {/* Description (Optional) */}
          <div>
            <label htmlFor="viewDescription" className="block text-sm font-medium text-gray-300 mb-2">
              Description <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
              id="viewDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add a description to help identify this view later"
              rows={3}
              maxLength={200}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              disabled={saving}
            />
            <p className="text-xs text-gray-500 mt-1">{description.length}/200 characters</p>
          </div>

          {/* Current Filters Summary */}
          <div className="p-4 bg-dark-800 border border-dark-700 rounded-lg">
            <h3 className="text-sm font-medium text-gray-300 mb-2">Filters to Save</h3>
            <p className="text-sm text-gray-400">{getFilterSummary()}</p>
          </div>

          {/* Set as Default */}
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              id="setAsDefault"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 focus:ring-offset-dark-900"
              disabled={saving}
            />
            <label htmlFor="setAsDefault" className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-300">Set as default view</span>
                <Star size={14} className="text-primary-400" />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                This view will be automatically loaded when you visit the page
              </p>
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-start space-x-2">
              <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-dark-800">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2',
                'bg-primary-500 hover:bg-primary-600 text-white',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Save size={18} />
              <span>{saving ? 'Saving...' : existingView ? 'Update View' : 'Save View'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
