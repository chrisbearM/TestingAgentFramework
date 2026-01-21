import React, { createContext, useContext, useEffect, useState, useRef } from 'react'

const WebSocketContext = createContext(null)

// Constants
const MAX_HISTORY_SIZE = 100
const MAX_RECONNECT_ATTEMPTS = 10
const INITIAL_RECONNECT_DELAY = 1000
const MAX_RECONNECT_DELAY = 30000

export function WebSocketProvider({ children }) {
  const [progress, setProgress] = useState(null)
  const [progressHistory, setProgressHistory] = useState([])  // Track message history
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)
  const lastMessageRef = useRef(null)
  const heartbeatIntervalRef = useRef(null)  // Store heartbeat interval in ref
  const shouldReconnectRef = useRef(true)  // Track if we should reconnect
  const reconnectAttemptsRef = useRef(0)  // Track reconnection attempts for exponential backoff

  useEffect(() => {
    shouldReconnectRef.current = true
    connectWebSocket()

    return () => {
      // Prevent reconnection after unmount
      shouldReconnectRef.current = false
      // Cleanup on unmount - ensure all resources are freed
      cleanupWebSocket()
    }
  }, [])

  const cleanupWebSocket = () => {
    // Clear heartbeat interval
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }

    // Close WebSocket connection with error handling
    if (ws.current) {
      try {
        // Only close if not already closed
        if (ws.current.readyState !== WebSocket.CLOSED &&
            ws.current.readyState !== WebSocket.CLOSING) {
          ws.current.close()
        }
      } catch (error) {
        console.error('Error closing WebSocket:', error)
      } finally {
        // Always clear the reference to prevent memory leaks
        ws.current = null
      }
    }
  }

  const connectWebSocket = () => {
    // Cleanup any existing connection first to prevent race conditions
    if (ws.current) {
      try {
        // Only close if not already closed/closing
        if (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING) {
          ws.current.close()
        }
      } catch (e) {
        console.error('Error closing existing WebSocket:', e)
      }
      ws.current = null
    }

    // Use WSS for HTTPS sites, WS for HTTP
    const protocol = import.meta.env.DEV
      ? 'ws:'
      : window.location.protocol === 'https:' ? 'wss:' : 'ws:'

    const wsUrl = import.meta.env.DEV
      ? 'ws://localhost:8000/ws/progress'
      : `${protocol}//${window.location.host}/ws/progress`

    console.log('Attempting to connect to WebSocket:', wsUrl)
    ws.current = new WebSocket(wsUrl)
    console.log('WebSocket created, readyState:', ws.current.readyState)

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
      // Reset reconnection attempts on successful connection
      reconnectAttemptsRef.current = 0

      // Start heartbeat - store in ref for proper cleanup
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('WebSocket message:', data)

        if (data.type !== 'heartbeat') {
          // Deduplicate messages by comparing with last message
          const messageKey = `${data.type}:${data.step}:${data.message}`
          if (messageKey !== lastMessageRef.current) {
            lastMessageRef.current = messageKey
            setProgress(data)

            // Add to history for test case generation process with size limit
            if (data.step === 'generating') {
              setProgressHistory(prev => {
                const newHistory = [...prev, { ...data, timestamp: Date.now() }]
                // Keep only the most recent MAX_HISTORY_SIZE messages
                return newHistory.slice(-MAX_HISTORY_SIZE)
              })
            } else if (data.type === 'complete' || data.type === 'error') {
              // Clear history on completion/error
              setProgressHistory([])
            }
          }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error, event.data)
      }
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)

      // Clear heartbeat interval using ref
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current)
        heartbeatIntervalRef.current = null
      }

      // Only reconnect if we should (not unmounted) and haven't exceeded max attempts
      if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        // Exponential backoff: delay increases with each attempt
        const delay = Math.min(
          INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
          MAX_RECONNECT_DELAY
        )
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${MAX_RECONNECT_ATTEMPTS})`)

        setTimeout(() => {
          reconnectAttemptsRef.current++
          connectWebSocket()
        }, delay)
      } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        console.error('Max reconnection attempts reached. Please refresh the page.')
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      // Ensure cleanup happens on error to prevent memory leaks
      setConnected(false)
      cleanupWebSocket()
    }
  }

  const clearProgress = () => {
    setProgress(null)
    setProgressHistory([])
  }

  return (
    <WebSocketContext.Provider value={{
      progress,
      progressHistory,
      connected,
      clearProgress
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
