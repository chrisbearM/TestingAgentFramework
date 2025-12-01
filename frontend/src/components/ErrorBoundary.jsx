import React from 'react'

/**
 * Error Boundary component to catch and handle React errors gracefully
 * Prevents the entire app from crashing when an error occurs
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error: error
    }
  }

  componentDidCatch(error, errorInfo) {
    // Log error details to console for debugging
    console.error('Error caught by ErrorBoundary:', error)
    console.error('Error info:', errorInfo)

    // Store error info in state
    this.setState({
      errorInfo: errorInfo
    })

    // Optional: Send to error tracking service (e.g., Sentry)
    // logErrorToService(error, errorInfo)
  }

  handleReload = () => {
    // Clear error state and reload
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
    window.location.reload()
  }

  handleReset = () => {
    // Clear error state without reloading
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render() {
    if (this.state.hasError) {
      // Error UI
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#1a1a1a',
          color: '#fff',
          padding: '2rem'
        }}>
          <div style={{
            maxWidth: '600px',
            width: '100%',
            textAlign: 'center'
          }}>
            <div style={{
              fontSize: '4rem',
              marginBottom: '1rem'
            }}>
              ⚠️
            </div>

            <h1 style={{
              fontSize: '2rem',
              marginBottom: '1rem',
              color: '#ff6b6b'
            }}>
              Something went wrong
            </h1>

            <p style={{
              fontSize: '1.1rem',
              marginBottom: '2rem',
              color: '#ccc',
              lineHeight: '1.6'
            }}>
              The application encountered an unexpected error.
              You can try reloading the page or going back to the previous screen.
            </p>

            {this.state.error && (
              <div style={{
                backgroundColor: '#2a2a2a',
                border: '1px solid #444',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '2rem',
                textAlign: 'left',
                overflow: 'auto',
                maxHeight: '200px'
              }}>
                <p style={{
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  color: '#ff6b6b',
                  margin: 0
                }}>
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <details style={{
                    marginTop: '1rem',
                    cursor: 'pointer'
                  }}>
                    <summary style={{
                      color: '#888',
                      fontSize: '0.9rem'
                    }}>
                      Show stack trace
                    </summary>
                    <pre style={{
                      fontFamily: 'monospace',
                      fontSize: '0.8rem',
                      color: '#ccc',
                      marginTop: '0.5rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={this.handleReload}
                style={{
                  padding: '0.75rem 2rem',
                  fontSize: '1rem',
                  backgroundColor: '#4a9eff',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#3a8eef'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#4a9eff'}
              >
                Reload Application
              </button>

              <button
                onClick={this.handleReset}
                style={{
                  padding: '0.75rem 2rem',
                  fontSize: '1rem',
                  backgroundColor: '#555',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#666'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#555'}
              >
                Try Again
              </button>

              <button
                onClick={() => window.history.back()}
                style={{
                  padding: '0.75rem 2rem',
                  fontSize: '1rem',
                  backgroundColor: 'transparent',
                  color: '#ccc',
                  border: '1px solid #555',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'border-color 0.2s, color 0.2s'
                }}
                onMouseOver={(e) => {
                  e.target.style.borderColor = '#888'
                  e.target.style.color = '#fff'
                }}
                onMouseOut={(e) => {
                  e.target.style.borderColor = '#555'
                  e.target.style.color = '#ccc'
                }}
              >
                Go Back
              </button>
            </div>

            <p style={{
              marginTop: '2rem',
              fontSize: '0.9rem',
              color: '#888'
            }}>
              If this problem persists, please contact support or check the browser console for more details.
            </p>
          </div>
        </div>
      )
    }

    // No error, render children normally
    return this.props.children
  }
}

export default ErrorBoundary
