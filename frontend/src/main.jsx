import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  // Temporarily disabled StrictMode - it causes WebSocket to disconnect immediately
  // due to double-mounting behavior in development
  // <React.StrictMode>
    <App />
  // </React.StrictMode>,
)
