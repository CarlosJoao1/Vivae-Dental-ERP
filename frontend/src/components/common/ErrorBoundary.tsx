import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  context?: string
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Optionally log to monitoring service
    // console.error('ErrorBoundary caught an error', { error, info, context: this.props.context })
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="p-4 border border-red-200 bg-red-50 rounded">
          <div className="font-semibold text-red-700 mb-1">Something went wrong.</div>
          {this.props.context && (
            <div className="text-sm text-red-600 mb-2">Context: {this.props.context}</div>
          )}
          <pre className="text-xs text-red-600 whitespace-pre-wrap mb-3">{this.state.error?.message}</pre>
          <button type="button" onClick={this.handleRetry} className="px-3 py-1.5 text-sm bg-white border border-red-300 text-red-700 rounded hover:bg-red-100">
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
