import React, { createContext, useContext, useEffect, useState, useRef } from 'react'

const WebSocketContext = createContext(null)

export function WebSocketProvider({ children }) {
  const [progress, setProgress] = useState(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)
  const lastMessageRef = useRef(null)
  const heartbeatIntervalRef = useRef(null)  // Store heartbeat interval in ref

  useEffect(() => {
    connectWebSocket()

    return () => {
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
    const wsUrl = import.meta.env.DEV
      ? 'ws://localhost:8000/ws/progress'
      : `ws://${window.location.host}/ws/progress`

    ws.current = new WebSocket(wsUrl)

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)

      // Start heartbeat - store in ref for proper cleanup
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type !== 'heartbeat') {
        // Deduplicate messages by comparing with last message
        const messageKey = `${data.type}:${data.step}:${data.message}`
        if (messageKey !== lastMessageRef.current) {
          lastMessageRef.current = messageKey
          setProgress(data)
        }
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

      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
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
  }

  return (
    <WebSocketContext.Provider value={{
      progress,
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
