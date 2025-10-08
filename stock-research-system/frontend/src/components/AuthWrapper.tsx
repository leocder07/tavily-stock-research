import React, { useEffect, useState } from 'react';
import {
  SignInButton,
  SignUpButton,
  UserButton,
  useUser,
} from '@clerk/clerk-react';
import { Button, Space, Switch } from 'antd';
import { UserOutlined, LoginOutlined, ExperimentOutlined } from '@ant-design/icons';
import { theme } from '../styles/theme';
import { TestUserLogin } from './TestUserLogin';

interface AuthWrapperProps {
  children: React.ReactNode;
}

export const AuthWrapper: React.FC<AuthWrapperProps> = ({ children }) => {
  const { isSignedIn, isLoaded } = useUser();
  const [showTestLogin, setShowTestLogin] = useState(false);
  const [testUserSession, setTestUserSession] = useState<any>(null);

  // Check for test user session on mount
  useEffect(() => {
    const session = localStorage.getItem('testUserSession');
    if (session) {
      const parsedSession = JSON.parse(session);
      // Check if session is still valid (within 24 hours)
      if (Date.now() - parsedSession.timestamp < 24 * 60 * 60 * 1000) {
        setTestUserSession(parsedSession);
      } else {
        localStorage.removeItem('testUserSession');
      }
    }
  }, []);

  // Handle test user login
  const handleTestLogin = () => {
    const session = localStorage.getItem('testUserSession');
    if (session) {
      setTestUserSession(JSON.parse(session));
    }
  };

  console.log('AuthWrapper - isLoaded:', isLoaded, 'isSignedIn:', isSignedIn, 'testUserSession:', testUserSession);

  // Add custom styles for Clerk modal
  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      /* Clerk modal backdrop - highest z-index */
      .cl-modalBackdrop {
        z-index: 9999 !important;
        background-color: rgba(0, 0, 0, 0.85) !important;
        backdrop-filter: blur(4px);
        pointer-events: auto !important;
      }

      /* Clerk modal content - higher than backdrop */
      .cl-modalContent {
        z-index: 10000 !important;
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        margin: 0 !important;
        pointer-events: auto !important;
      }

      /* Alternative selectors for different Clerk versions */
      .cl-card, .cl-rootBox {
        z-index: 10000 !important;
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        pointer-events: auto !important;
      }

      /* Ensure the modal dialog container is properly positioned */
      div[role="dialog"] {
        z-index: 10000 !important;
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        margin: 0 auto !important;
        pointer-events: auto !important;
      }

      /* Ensure all input fields are clickable */
      .cl-modalContent input,
      .cl-card input,
      .cl-rootBox input,
      div[role="dialog"] input {
        pointer-events: auto !important;
        z-index: 10001 !important;
        position: relative !important;
      }

      /* Ensure all buttons are clickable */
      .cl-modalContent button,
      .cl-card button,
      .cl-rootBox button,
      div[role="dialog"] button {
        pointer-events: auto !important;
        z-index: 10001 !important;
        position: relative !important;
      }

      /* Ensure proper spacing to prevent overlaps */
      .cl-modalContent > div,
      .cl-card > div,
      .cl-rootBox > div {
        margin-bottom: 16px !important;
      }

      /* Fix any form field containers */
      .cl-formFieldRow,
      .cl-formButtonPrimary {
        margin-bottom: 16px !important;
        pointer-events: auto !important;
      }

      /* Ensure the entire modal wrapper has proper stacking */
      .cl-component {
        z-index: 10000 !important;
        pointer-events: auto !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // Wait for Clerk to load
  if (!isLoaded) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: theme.colors.background.primary,
      }}>
        <div style={{ color: theme.colors.text.primary }}>Loading authentication...</div>
      </div>
    );
  }

  // If signed in or test user session, show children
  if (isSignedIn || testUserSession) {
    console.log('User is signed in or test user, showing children');
    return <>{children}</>;
  }

  // Show sign-in/sign-up UI with new design
  console.log('User is NOT signed in, showing auth UI');
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: theme.colors.background.primary,
      padding: '20px',
      gap: '32px',
    }}>
      {/* Main Auth Card */}
      <div style={{
        textAlign: 'center',
        padding: window.innerWidth < 768 ? '48px 32px' : '64px 56px',
        background: 'rgba(26, 26, 31, 0.8)',
        backdropFilter: 'blur(20px)',
        borderRadius: '32px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.6)',
        maxWidth: '680px',
        width: '100%',
      }}>
        {/* Icon */}
        <div style={{
          width: '80px',
          height: '80px',
          margin: '0 auto 32px',
          background: 'linear-gradient(135deg, #00D4AA 0%, #00B894 100%)',
          borderRadius: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 8px 24px rgba(0, 212, 170, 0.3)',
        }}>
          <span style={{ fontSize: '40px' }}>📊</span>
        </div>

        {/* Title */}
        <h1 style={{
          color: '#FFFFFF',
          marginBottom: '20px',
          fontSize: window.innerWidth < 768 ? '28px' : '40px',
          fontWeight: 700,
          letterSpacing: '-0.5px',
          lineHeight: 1.2,
        }}>
          AI-Powered Stock Research
        </h1>

        {/* Subtitle */}
        <p style={{
          color: 'rgba(255, 255, 255, 0.6)',
          fontSize: window.innerWidth < 768 ? '15px' : '17px',
          marginBottom: '40px',
          lineHeight: 1.6,
          maxWidth: '520px',
          margin: '0 auto 40px',
        }}>
          Welcome to the most advanced multi-agent stock research system. Sign in to access personalized AI advisors and real-time market insights.
        </p>

        {/* Buttons */}
        <div style={{
          display: 'flex',
          gap: '16px',
          justifyContent: 'center',
          flexDirection: window.innerWidth < 768 ? 'column' : 'row',
          marginBottom: '48px',
        }}>
          <SignInButton mode="modal">
            <Button
              size="large"
              type="primary"
              icon={<LoginOutlined />}
              style={{
                background: 'linear-gradient(135deg, #00D4AA 0%, #00B894 100%)',
                border: 'none',
                borderRadius: '16px',
                height: '56px',
                padding: '0 40px',
                fontSize: '16px',
                fontWeight: 600,
                color: '#FFFFFF',
                boxShadow: '0 4px 20px rgba(0, 212, 170, 0.4)',
                width: window.innerWidth < 768 ? '100%' : 'auto',
                minWidth: '180px',
              }}
            >
              Sign In
            </Button>
          </SignInButton>

          <SignUpButton mode="modal">
            <Button
              size="large"
              icon={<UserOutlined />}
              style={{
                background: 'transparent',
                border: '2px solid #00D4AA',
                borderRadius: '16px',
                height: '56px',
                padding: '0 40px',
                fontSize: '16px',
                fontWeight: 600,
                color: '#00D4AA',
                width: window.innerWidth < 768 ? '100%' : 'auto',
                minWidth: '180px',
              }}
            >
              Sign Up
            </Button>
          </SignUpButton>
        </div>

        {/* Feature Banner */}
        <div style={{
          padding: '20px 24px',
          background: 'rgba(0, 212, 170, 0.08)',
          borderRadius: '16px',
          border: '1px solid rgba(0, 212, 170, 0.2)',
        }}>
          <span style={{
            color: '#00D4AA',
            fontSize: '15px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}>
            🚀 New users get personalized AI advisor selection and custom dashboard setup
          </span>
        </div>
      </div>

      {/* Development Mode Toggle */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '18px 32px',
        background: 'rgba(26, 26, 31, 0.6)',
        border: '1px solid rgba(255, 165, 0, 0.3)',
        borderRadius: '16px',
        backdropFilter: 'blur(10px)',
      }}>
        <ExperimentOutlined style={{ color: '#FFA500', fontSize: '22px' }} />
        <span style={{
          color: 'rgba(255, 165, 0, 0.9)',
          fontSize: '15px',
          fontWeight: 600,
        }}>
          Development Mode
        </span>
        <Switch
          checked={showTestLogin}
          onChange={setShowTestLogin}
          style={{
            background: showTestLogin ? '#FFA500' : 'rgba(255, 255, 255, 0.2)',
          }}
        />
      </div>

      {/* Show Test Login Form when toggled */}
      {showTestLogin && (
        <TestUserLogin onTestLogin={handleTestLogin} />
      )}
    </div>
  );
};

export const AuthHeader: React.FC = () => {
  const { isSignedIn, user } = useUser();

  if (!isSignedIn || !user) {
    return null;
  }

  return (
    <div style={{
      position: 'absolute',
      top: '20px',
      right: '20px',
      zIndex: 1000,
    }}>
      <Space align="center">
        <span style={{
          color: theme.colors.text.secondary,
          fontSize: '14px',
        }}>
          {user?.firstName || user?.emailAddresses[0].emailAddress}
        </span>
        <UserButton
          afterSignOutUrl="/"
          appearance={{
              elements: {
                avatarBox: {
                  width: '40px',
                  height: '40px',
                }
              }
            }}
          />
      </Space>
    </div>
  );
};