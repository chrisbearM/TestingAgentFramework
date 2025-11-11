import React, { createContext, useContext, useEffect, useState, useRef } from 'react'

const WebSocketContext = createContext(null)

export function WebSocketProvider({ children }) {
  const [progress, setProgress] = useState(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    connectWebSocket()

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    const wsUrl = import.meta.env.DEV
      ? 'ws://localhost:8000/ws/progress'
      : `ws://${window.location.host}/ws/progress`

    ws.current = new WebSocket(wsUrl)

    // Send heartbeat every 30 seconds to keep connection alive
    let heartbeatInterval = null

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)

      // Start heartbeat
      heartbeatInterval = setInterval(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type !== 'heartbeat') {
        setProgress(data)
      }
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)

      // Clear heartbeat interval
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval)
      }

      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
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
