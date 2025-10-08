import React from 'react';
import { useUser, useClerk } from '@clerk/clerk-react';

export const AuthDebug: React.FC = () => {
  const { isLoaded, isSignedIn, user } = useUser();
  const clerk = useClerk();

  return (
    <div style={{
      position: 'fixed',
      top: 10,
      right: 10,
      background: 'rgba(0,0,0,0.8)',
      color: '#00ff00',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      fontFamily: 'monospace',
      zIndex: 99999,
      maxWidth: '300px'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#00ff00' }}>🔍 Auth Debug</h4>
      <div>Clerk Loaded: {String(isLoaded)}</div>
      <div>Is Signed In: {String(isSignedIn)}</div>
      <div>User ID: {user?.id || 'N/A'}</div>
      <div>Session: {clerk.session?.id ? 'Active' : 'None'}</div>
      <div>Publishable Key: {clerk.publishableKey ? `${clerk.publishableKey.substring(0, 20)}...` : 'N/A'}</div>
    </div>
  );
};