import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import './index.css';
import './styles/global.css'; // Import CRED-inspired global styles
import App from './App';
import reportWebVitals from './reportWebVitals';

// Get Clerk publishable key from environment
// Using process.env for Create React App compatibility
const PUBLISHABLE_KEY = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY || '';

// Check if we have a real Clerk key (not placeholder)
const hasValidClerkKey = PUBLISHABLE_KEY &&
  !PUBLISHABLE_KEY.includes('placeholder') &&
  PUBLISHABLE_KEY.startsWith('pk_');

console.log('Clerk Key Check:', {
  PUBLISHABLE_KEY: PUBLISHABLE_KEY ? `${PUBLISHABLE_KEY.substring(0, 20)}...` : 'NONE',
  hasValidClerkKey,
  keyStartsWithPk: PUBLISHABLE_KEY?.startsWith('pk_'),
  includesPlaceholder: PUBLISHABLE_KEY?.includes('placeholder')
});

if (!hasValidClerkKey) {
  console.warn('Clerk Authentication disabled - running without authentication');
} else {
  console.log('Clerk Authentication enabled with key:', PUBLISHABLE_KEY.substring(0, 20) + '...');
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    {hasValidClerkKey ? (
      <ClerkProvider
        publishableKey={PUBLISHABLE_KEY}
        afterSignOutUrl="/"
        appearance={{
          baseTheme: undefined,
          variables: {
            colorPrimary: '#D4AF37',
            colorBackground: '#1C1C1E',
            colorText: '#FFFFFF',
            colorTextSecondary: '#9A9A9D',
            colorInputBackground: '#2C2C2E',
            colorInputText: '#FFFFFF',
            borderRadius: '12px',
            fontFamily: 'Inter, -apple-system, sans-serif',
          },
          elements: {
            rootBox: {
              fontFamily: 'Inter, -apple-system, sans-serif',
            },
            card: {
              backgroundColor: '#1C1C1E',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            },
            headerTitle: {
              color: '#FFFFFF',
              fontSize: '24px',
              fontWeight: '600',
            },
            headerSubtitle: {
              color: '#9A9A9D',
              fontSize: '16px',
            },
            socialButtonsBlockButton: {
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#FFFFFF',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              }
            },
            formFieldInput: {
              backgroundColor: '#2C2C2E',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#FFFFFF',
              padding: '12px',
              fontSize: '16px',
              '&:focus': {
                border: '1px solid #D4AF37',
                boxShadow: '0 0 0 2px rgba(212, 175, 55, 0.2)',
                backgroundColor: '#363639',
              },
              '&::placeholder': {
                color: '#636366',
              }
            },
            formFieldLabel: {
              color: '#9A9A9D',
              fontSize: '14px',
              marginBottom: '8px',
            },
            formButtonPrimary: {
              backgroundColor: '#D4AF37',
              color: '#000000',
              fontWeight: '600',
              fontSize: '16px',
              padding: '12px 24px',
              '&:hover': {
                backgroundColor: '#F7DC6F',
              }
            },
            footerActionLink: {
              color: '#D4AF37',
              '&:hover': {
                color: '#F7DC6F',
              }
            },
            identityPreviewText: {
              color: '#FFFFFF',
              fontSize: '16px',
            },
            identityPreviewEditButton: {
              color: '#D4AF37',
              '&:hover': {
                color: '#F7DC6F',
              }
            },
            dividerLine: {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
            dividerText: {
              color: '#9A9A9D',
            },
            formResendCodeLink: {
              color: '#D4AF37',
              fontSize: '14px',
              fontWeight: '500',
              '&:hover': {
                color: '#F7DC6F',
                textDecoration: 'underline',
              }
            },
            // OTP Code Input specific styles - Enhanced visibility
            otpCodeFieldInput: {
              backgroundColor: '#3C3C3E !important',
              border: '2px solid rgba(255, 255, 255, 0.4) !important',
              color: '#FFFFFF !important',
              fontSize: '28px !important',
              fontWeight: '600 !important',
              width: '56px !important',
              height: '64px !important',
              textAlign: 'center' as const,
              borderRadius: '12px !important',
              margin: '0 6px !important',
              caretColor: '#D4AF37 !important',
              letterSpacing: '2px',
              fontFamily: 'JetBrains Mono, monospace',
              transition: 'all 0.2s ease',
              '&:focus': {
                border: '2px solid #D4AF37 !important',
                backgroundColor: '#4C4C4E !important',
                boxShadow: '0 0 0 4px rgba(212, 175, 55, 0.3) !important',
                outline: 'none !important',
                transform: 'scale(1.05)',
              },
              '&:hover': {
                border: '2px solid rgba(212, 175, 55, 0.6) !important',
                backgroundColor: '#454547 !important',
              },
              '&[data-state="selected"]': {
                border: '2px solid #D4AF37 !important',
                backgroundColor: '#4C4C4E !important',
              },
              '&:not(:placeholder-shown)': {
                border: '2px solid rgba(0, 212, 170, 0.5) !important',
              }
            },
            otpCodeFieldInputs: {
              gap: '12px',
              justifyContent: 'center',
              margin: '24px 0',
            },
            formFieldInputGroup: {
              backgroundColor: 'transparent',
            },
            formFieldInputGroupPrepend: {
              backgroundColor: '#2C2C2E',
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#9A9A9D',
            },
            alternativeMethodsBlockButton: {
              color: '#D4AF37',
              border: '1px solid rgba(212, 175, 55, 0.3)',
              backgroundColor: 'rgba(212, 175, 55, 0.1)',
              fontSize: '14px',
              padding: '10px 16px',
              '&:hover': {
                backgroundColor: 'rgba(212, 175, 55, 0.2)',
                border: '1px solid rgba(212, 175, 55, 0.5)',
              },
            },
            formFieldSuccessText: {
              color: '#00D4AA',
              fontSize: '14px',
            },
            formFieldErrorText: {
              color: '#FF453A',
              fontSize: '14px',
            },
            badge: {
              backgroundColor: 'rgba(212, 175, 55, 0.1)',
              color: '#D4AF37',
              border: '1px solid rgba(212, 175, 55, 0.3)',
            },
          }
        }}
      >
        <App />
      </ClerkProvider>
    ) : (
      <App />
    )}
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();