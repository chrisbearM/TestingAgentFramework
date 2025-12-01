import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import EpicAnalysis from './pages/EpicAnalysis'
import TestGeneration from './pages/TestGeneration'
import TestTickets from './pages/TestTickets'
import TicketImprover from './pages/TicketImprover'
import Settings from './pages/Settings'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider, useAuth } from './context/AuthContext'
import { WebSocketProvider } from './context/WebSocketContext'
import { EpicAnalysisProvider } from './context/EpicAnalysisContext'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-primary-500 text-xl">Loading...</div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <WebSocketProvider>
            <EpicAnalysisProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<Dashboard />} />
                  <Route path="epic-analysis" element={<EpicAnalysis />} />
                  <Route path="test-generation" element={<TestGeneration />} />
                  <Route path="test-tickets" element={<TestTickets />} />
                  <Route path="ticket-improver" element={<TicketImprover />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
              </Routes>
            </EpicAnalysisProvider>
          </WebSocketProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  )
}

export default App
