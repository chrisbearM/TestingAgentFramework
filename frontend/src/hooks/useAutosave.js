import { useEffect, useRef, useCallback } from 'react'
import api from '../api/client'

/**
 * Custom hook for autosaving data to session storage and backend
 *
 * @param {string} sessionId - Session identifier (typically user email)
 * @param {string} dataType - Type of draft ('epic_analysis', 'test_tickets', 'test_cases')
 * @param {object} data - Data to autosave
 * @param {object} metadata - Optional metadata (epic_key, timestamp, etc.)
 * @param {number} debounceMs - Debounce delay in milliseconds (default: 30000 = 30s)
 * @param {boolean} enabled - Whether autosave is enabled (default: true)
 * @returns {object} - { saveDraft, loadDraft, deleteDraft, isSaving, lastSaved }
 */
export function useAutosave(
  sessionId,
  dataType,
  data,
  metadata = {},
  debounceMs = 30000,
  enabled = true
) {
  const timerRef = useRef(null)
  const draftIdRef = useRef(null)
  const lastSavedRef = useRef(null)
  const isSavingRef = useRef(false)

  /**
   * Save draft to backend
   */
  const saveDraft = useCallback(async () => {
    if (!sessionId || !dataType || !data || !enabled) {
      return
    }

    // Skip if data is empty
    if (Object.keys(data).length === 0) {
      return
    }

    try {
      isSavingRef.current = true

      // If we have a draft ID, update it; otherwise create new
      if (draftIdRef.current) {
        await api.put(`/sessions/${sessionId}/drafts/${draftIdRef.current}`, {
          data,
          metadata: {
            ...metadata,
            last_updated: new Date().toISOString()
          }
        })
        console.log('Draft updated:', draftIdRef.current)
      } else {
        const response = await api.post('/sessions/drafts', {
          session_id: sessionId,
          data_type: dataType,
          data,
          metadata: {
            ...metadata,
            created: new Date().toISOString()
          }
        })
        draftIdRef.current = response.data.draft_id
        console.log('Draft created:', draftIdRef.current)
      }

      lastSavedRef.current = new Date()

      // Also save to localStorage as backup
      const localStorageKey = `draft_${dataType}_${metadata.epic_key || 'unknown'}`
      localStorage.setItem(localStorageKey, JSON.stringify({
        data,
        metadata,
        draft_id: draftIdRef.current,
        timestamp: new Date().toISOString()
      }))

    } catch (error) {
      console.error('Failed to save draft:', error)
    } finally {
      isSavingRef.current = false
    }
  }, [sessionId, dataType, data, metadata, enabled])

  /**
   * Load draft from backend or localStorage
   */
  const loadDraft = useCallback(async (epicKey) => {
    if (!sessionId) {
      return null
    }

    try {
      // Try to load from backend first
      const response = await api.get(`/sessions/${sessionId}/drafts`, {
        params: { data_type: dataType }
      })

      if (response.data.drafts && response.data.drafts.length > 0) {
        // Find draft for this epic (if epicKey provided)
        let draft = response.data.drafts[0] // Default to most recent

        if (epicKey) {
          const epicDraft = response.data.drafts.find(d =>
            d.metadata?.epic_key === epicKey
          )
          if (epicDraft) {
            draft = epicDraft
          }
        }

        // Load the full draft data
        const draftResponse = await api.get(`/sessions/${sessionId}/drafts/${draft.id}`)
        draftIdRef.current = draft.id

        console.log('Draft loaded from backend:', draft.id)
        return draftResponse.data.draft
      }

      // Fallback to localStorage
      const localStorageKey = `draft_${dataType}_${epicKey || 'unknown'}`
      const localDraft = localStorage.getItem(localStorageKey)
      if (localDraft) {
        const parsed = JSON.parse(localDraft)
        console.log('Draft loaded from localStorage')
        return parsed
      }

      return null
    } catch (error) {
      console.error('Failed to load draft:', error)

      // Try localStorage as fallback
      const localStorageKey = `draft_${dataType}_${epicKey || 'unknown'}`
      const localDraft = localStorage.getItem(localStorageKey)
      if (localDraft) {
        return JSON.parse(localDraft)
      }

      return null
    }
  }, [sessionId, dataType])

  /**
   * Delete draft from backend and localStorage
   */
  const deleteDraft = useCallback(async () => {
    if (!sessionId || !draftIdRef.current) {
      return
    }

    try {
      await api.delete(`/sessions/${sessionId}/drafts/${draftIdRef.current}`)
      console.log('Draft deleted:', draftIdRef.current)

      draftIdRef.current = null
      lastSavedRef.current = null

      // Also remove from localStorage
      const localStorageKey = `draft_${dataType}_${metadata.epic_key || 'unknown'}`
      localStorage.removeItem(localStorageKey)
    } catch (error) {
      console.error('Failed to delete draft:', error)
    }
  }, [sessionId, dataType, metadata])

  // Set up autosave timer
  useEffect(() => {
    if (!enabled || !data || Object.keys(data).length === 0) {
      return
    }

    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      saveDraft()
    }, debounceMs)

    // Cleanup
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [data, enabled, debounceMs, saveDraft])

  // Save on unmount (page close)
  useEffect(() => {
    return () => {
      if (enabled && data && Object.keys(data).length > 0) {
        // Use sendBeacon for reliable save on page close
        const payload = {
          session_id: sessionId,
          data_type: dataType,
          data,
          metadata: {
            ...metadata,
            saved_on_close: true
          }
        }

        // Try sendBeacon first (more reliable)
        if (navigator.sendBeacon) {
          navigator.sendBeacon(
            `${api.defaults.baseURL}/sessions/drafts`,
            JSON.stringify(payload)
          )
        } else {
          // Fallback to synchronous save
          saveDraft()
        }
      }
    }
  }, []) // Only run on unmount

  return {
    saveDraft,
    loadDraft,
    deleteDraft,
    isSaving: isSavingRef.current,
    lastSaved: lastSavedRef.current,
    draftId: draftIdRef.current
  }
}

export default useAutosave
