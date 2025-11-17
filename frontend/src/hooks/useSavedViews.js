import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

/**
 * Custom hook for managing saved views/filters
 *
 * @param {string} sessionId - Session identifier
 * @returns {object} - View management functions and state
 */
export function useSavedViews(sessionId) {
  const [views, setViews] = useState([])
  const [defaultView, setDefaultView] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Load all views for the session
   */
  const loadViews = useCallback(async () => {
    if (!sessionId) return

    try {
      setLoading(true)
      setError(null)

      const response = await api.get('/views', {
        params: { session_id: sessionId }
      })

      setViews(response.data.views || [])

      // Find the default view
      const defaultViewItem = response.data.views?.find(v => v.is_default)
      setDefaultView(defaultViewItem || null)

      console.log('Loaded views:', response.data.views?.length)
    } catch (err) {
      console.error('Failed to load views:', err)
      setError(err.message || 'Failed to load views')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  /**
   * Save a new view
   */
  const saveView = useCallback(async (name, filters, description = null, isDefault = false) => {
    if (!sessionId) {
      throw new Error('Session ID is required')
    }

    try {
      setLoading(true)
      setError(null)

      const response = await api.post('/views', {
        session_id: sessionId,
        name,
        filters,
        description,
        is_default: isDefault
      })

      console.log('View saved:', response.data.view_id)

      // Reload views to get the updated list
      await loadViews()

      return response.data.view_id
    } catch (err) {
      console.error('Failed to save view:', err)
      setError(err.message || 'Failed to save view')
      throw err
    } finally {
      setLoading(false)
    }
  }, [sessionId, loadViews])

  /**
   * Update an existing view
   */
  const updateView = useCallback(async (viewId, updates) => {
    if (!sessionId) {
      throw new Error('Session ID is required')
    }

    try {
      setLoading(true)
      setError(null)

      await api.put(`/views/${viewId}`, updates, {
        params: { session_id: sessionId }
      })

      console.log('View updated:', viewId)

      // Reload views to get the updated list
      await loadViews()
    } catch (err) {
      console.error('Failed to update view:', err)
      setError(err.message || 'Failed to update view')
      throw err
    } finally {
      setLoading(false)
    }
  }, [sessionId, loadViews])

  /**
   * Delete a view
   */
  const deleteView = useCallback(async (viewId) => {
    if (!sessionId) {
      throw new Error('Session ID is required')
    }

    try {
      setLoading(false)
      setError(null)

      await api.delete(`/views/${viewId}`, {
        params: { session_id: sessionId }
      })

      console.log('View deleted:', viewId)

      // Reload views to get the updated list
      await loadViews()
    } catch (err) {
      console.error('Failed to delete view:', err)
      setError(err.message || 'Failed to delete view')
      throw err
    } finally {
      setLoading(false)
    }
  }, [sessionId, loadViews])

  /**
   * Set a view as the default
   */
  const setAsDefault = useCallback(async (viewId) => {
    if (!sessionId) {
      throw new Error('Session ID is required')
    }

    try {
      setLoading(true)
      setError(null)

      await api.post(`/views/${viewId}/set-default`, null, {
        params: { session_id: sessionId }
      })

      console.log('Default view set:', viewId)

      // Reload views to get the updated list
      await loadViews()
    } catch (err) {
      console.error('Failed to set default view:', err)
      setError(err.message || 'Failed to set default view')
      throw err
    } finally {
      setLoading(false)
    }
  }, [sessionId, loadViews])

  /**
   * Clear the default view
   */
  const clearDefault = useCallback(async () => {
    if (!sessionId) {
      throw new Error('Session ID is required')
    }

    try {
      setLoading(true)
      setError(null)

      await api.delete('/views/default', {
        params: { session_id: sessionId }
      })

      console.log('Default view cleared')

      // Reload views to get the updated list
      await loadViews()
    } catch (err) {
      console.error('Failed to clear default view:', err)
      setError(err.message || 'Failed to clear default view')
      throw err
    } finally {
      setLoading(false)
    }
  }, [sessionId, loadViews])

  /**
   * Get the default view
   */
  const loadDefaultView = useCallback(async () => {
    if (!sessionId) return null

    try {
      const response = await api.get('/views/default', {
        params: { session_id: sessionId }
      })

      const view = response.data.view
      setDefaultView(view)

      console.log('Default view loaded:', view?.id)
      return view
    } catch (err) {
      console.error('Failed to load default view:', err)
      return null
    }
  }, [sessionId])

  // Load views on mount and when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadViews()
    }
  }, [sessionId, loadViews])

  return {
    views,
    defaultView,
    loading,
    error,
    loadViews,
    saveView,
    updateView,
    deleteView,
    setAsDefault,
    clearDefault,
    loadDefaultView
  }
}

export default useSavedViews
