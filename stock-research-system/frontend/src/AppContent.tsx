import React, { useState, useEffect } from 'react';
import { ConfigProvider, Layout, theme as antTheme } from 'antd';
import { useUser } from '@clerk/clerk-react';
import PremiumDashboard from './components/PremiumDashboard';
import { AuthWrapper } from './components/AuthWrapper';
import { OnboardingQuestionnaire } from './components/OnboardingQuestionnaire';
import { theme } from './styles/theme';
import axios from 'axios';

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const { darkAlgorithm } = antTheme;

const AppContent: React.FC = () => {
  const [mounted, setMounted] = useState(false);
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const { isSignedIn, user } = useUser();

  useEffect(() => {
    setMounted(true);
    // Set dark background for entire app
    document.body.style.backgroundColor = theme.colors.background.primary;
    document.body.style.margin = '0';
    document.body.style.padding = '0';
  }, []);

  useEffect(() => {
    // Check if user has completed onboarding
    const checkUserProfile = async () => {
      // Check localStorage first for development bypass
      const onboardingComplete = localStorage.getItem('onboardingComplete');
      if (onboardingComplete === 'true') {
        setHasProfile(true);
        setLoading(false);
        return;
      }

      if (isSignedIn && user?.id) {
        try {
          const response = await axios.get(`/api/v1/user/profile/${user.id}`);
          setHasProfile(!!response.data.profile);
        } catch (error) {
          setHasProfile(false);
        }
      }
      setLoading(false);
    };

    checkUserProfile();
  }, [isSignedIn, user]);

  const handleOnboardingComplete = () => {
    localStorage.setItem('onboardingComplete', 'true');
    setHasProfile(true);
  };

  if (!mounted) {
    return null; // Prevent hydration issues
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: darkAlgorithm,
        token: {
          colorPrimary: theme.colors.primary,
          colorBgBase: theme.colors.background.primary,
          colorTextBase: theme.colors.text.primary,
          borderRadius: 12,
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        },
      }}
    >
      <Layout style={{
        minHeight: '100vh',
        background: theme.colors.background.primary
      }}>
        <AuthWrapper>
          {loading ? (
            <div style={{
              minHeight: '100vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <div style={{ color: theme.colors.text.primary }}>Loading...</div>
            </div>
          ) : !hasProfile && isSignedIn ? (
            <OnboardingQuestionnaire
              onComplete={handleOnboardingComplete}
            />
          ) : (
            <Layout.Content>
              <PremiumDashboard />
            </Layout.Content>
          )}
        </AuthWrapper>
      </Layout>
    </ConfigProvider>
  );
};

export default AppContent;