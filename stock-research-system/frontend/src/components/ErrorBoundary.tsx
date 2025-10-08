import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Collapse, Typography } from 'antd';
import { ReloadOutlined, BugOutlined, HomeOutlined } from '@ant-design/icons';
import { theme } from '../styles/theme';

const { Panel } = Collapse;
const { Text, Title, Paragraph } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { 
      hasError: true,
      error 
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { onError } = this.props;
    
    // Log error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));
    
    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }
    
    // Send error to monitoring service (e.g., Sentry)
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // In production, you would send this to a service like Sentry
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
    
    // For now, just log to console
    console.log('Error logged to service:', errorData);
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    const { hasError, error, errorInfo, errorCount } = this.state;
    const { children, fallback } = this.props;

    if (hasError && error) {
      // Custom fallback component
      if (fallback) {
        return <>{fallback}</>;
      }

      // Default error UI with premium styling
      return (
        <div style={{
          minHeight: '100vh',
          background: theme.colors.background.primary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}>
          <div style={{
            background: 'rgba(212, 175, 55, 0.02)',
            borderRadius: '24px',
            border: '1px solid rgba(212, 175, 55, 0.1)',
            backdropFilter: 'blur(20px)',
            padding: '48px',
            maxWidth: '800px',
            width: '100%',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
          }}>
            <Result
              status="error"
              icon={
                <div style={{
                  fontSize: '72px',
                  background: `linear-gradient(135deg, ${theme.colors.danger}, ${theme.colors.primary})`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  <BugOutlined />
                </div>
              }
              title={
                <Title level={2} style={{ 
                  color: theme.colors.text.primary,
                  marginTop: '24px',
                }}>
                  Oops! Something went wrong
                </Title>
              }
              subTitle={
                <Paragraph style={{ 
                  color: theme.colors.text.secondary,
                  fontSize: '16px',
                  marginTop: '8px',
                }}>
                  We're sorry for the inconvenience. The application encountered an unexpected error.
                  {errorCount > 1 && (
                    <Text style={{ 
                      display: 'block', 
                      marginTop: '8px',
                      color: theme.colors.warning 
                    }}>
                      This error has occurred {errorCount} times in this session.
                    </Text>
                  )}
                </Paragraph>
              }
              extra={[
                <Button
                  key="reload"
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={this.handleReload}
                  style={{
                    background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.warning})`,
                    border: 'none',
                    height: '44px',
                    borderRadius: '12px',
                    fontWeight: 600,
                    marginRight: '12px',
                  }}
                >
                  Reload Page
                </Button>,
                <Button
                  key="reset"
                  onClick={this.handleReset}
                  style={{
                    background: 'rgba(212, 175, 55, 0.1)',
                    border: '1px solid rgba(212, 175, 55, 0.2)',
                    color: theme.colors.primary,
                    height: '44px',
                    borderRadius: '12px',
                    fontWeight: 600,
                    marginRight: '12px',
                  }}
                >
                  Try Again
                </Button>,
                <Button
                  key="home"
                  icon={<HomeOutlined />}
                  onClick={this.handleGoHome}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: theme.colors.text.secondary,
                    height: '44px',
                    borderRadius: '12px',
                  }}
                >
                  Go Home
                </Button>,
              ]}
            />
            
            {/* Error details for developers */}
            {process.env.NODE_ENV === 'development' && errorInfo && (
              <Collapse
                ghost
                style={{ 
                  marginTop: '32px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: '12px',
                }}
              >
                <Panel 
                  header={
                    <Text style={{ color: theme.colors.text.secondary }}>
                      Error Details (Development Mode)
                    </Text>
                  } 
                  key="1"
                >
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    padding: '16px',
                    borderRadius: '8px',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    color: theme.colors.text.secondary,
                    overflowX: 'auto',
                  }}>
                    <div style={{ marginBottom: '16px' }}>
                      <Text style={{ color: theme.colors.danger, fontWeight: 600 }}>
                        Error Message:
                      </Text>
                      <pre style={{ marginTop: '8px', color: theme.colors.text.primary }}>
                        {error.message}
                      </pre>
                    </div>
                    
                    <div style={{ marginBottom: '16px' }}>
                      <Text style={{ color: theme.colors.danger, fontWeight: 600 }}>
                        Stack Trace:
                      </Text>
                      <pre style={{ 
                        marginTop: '8px', 
                        color: theme.colors.text.muted,
                        maxHeight: '200px',
                        overflow: 'auto',
                      }}>
                        {error.stack}
                      </pre>
                    </div>
                    
                    <div>
                      <Text style={{ color: theme.colors.danger, fontWeight: 600 }}>
                        Component Stack:
                      </Text>
                      <pre style={{ 
                        marginTop: '8px', 
                        color: theme.colors.text.muted,
                        maxHeight: '200px',
                        overflow: 'auto',
                      }}>
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  </div>
                </Panel>
              </Collapse>
            )}
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;

// Higher-order component for wrapping components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) => {
  return (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  );
};