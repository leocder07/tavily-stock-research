import React, { useState } from 'react';
import { Dropdown, Space, Typography, Avatar, Button, Menu } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  DashboardOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { useUser, useClerk } from '@clerk/clerk-react';
import { theme } from '../styles/theme';
import { UserProfile } from './UserProfile';

const { Text } = Typography;

export const EnhancedAuthHeader: React.FC = () => {
  const { isSignedIn, user } = useUser();
  const { signOut } = useClerk();
  const [profileVisible, setProfileVisible] = useState(false);

  // Check for test user session
  const testUserSession = localStorage.getItem('testUserSession');
  const testUser = testUserSession ? JSON.parse(testUserSession) : null;

  if (!isSignedIn && !testUser) {
    return null;
  }

  // Determine effective user (test user or Clerk user)
  const effectiveUser = testUser || user;

  const handleSignOut = async () => {
    // Check if test user and clear localStorage
    if (testUser) {
      localStorage.removeItem('testUserSession');
      window.location.reload();
    } else {
      await signOut();
    }
  };

  const handleMenuClick = (key: string) => {
    switch (key) {
      case 'profile':
        setProfileVisible(true);
        break;
      case 'settings':
        setProfileVisible(true); // For now, redirect to profile
        break;
      case 'help':
        window.open('https://github.com/your-repo/docs', '_blank');
        break;
      case 'signout':
        handleSignOut();
        break;
    }
  };

  const menu = (
    <Menu
      onClick={({ key }) => handleMenuClick(key)}
      style={{
        background: theme.colors.gradient.glass,
        backdropFilter: 'blur(10px)',
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.md,
        minWidth: '220px',
        padding: '8px',
      }}
      items={[
        {
          key: 'user-info',
          label: (
            <div style={{
              padding: '8px 4px',
              borderBottom: `1px solid ${theme.colors.border}`,
              marginBottom: '8px',
            }}>
              <Text strong style={{ color: theme.colors.text.primary, display: 'block' }}>
                {effectiveUser?.firstName || 'User'}
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {effectiveUser?.emailAddresses?.[0]?.emailAddress || effectiveUser?.email}
              </Text>
            </div>
          ),
          disabled: true,
        },
        {
          key: 'profile',
          icon: <UserOutlined style={{ fontSize: '16px' }} />,
          label: (
            <Text style={{ color: theme.colors.text.primary }}>
              View Profile
            </Text>
          ),
        },
        {
          key: 'dashboard',
          icon: <DashboardOutlined style={{ fontSize: '16px' }} />,
          label: (
            <Text style={{ color: theme.colors.text.primary }}>
              Dashboard
            </Text>
          ),
        },
        {
          key: 'settings',
          icon: <SettingOutlined style={{ fontSize: '16px' }} />,
          label: (
            <Text style={{ color: theme.colors.text.primary }}>
              Settings
            </Text>
          ),
        },
        {
          type: 'divider',
        },
        {
          key: 'help',
          icon: <QuestionCircleOutlined style={{ fontSize: '16px' }} />,
          label: (
            <Text style={{ color: theme.colors.text.primary }}>
              Help & Support
            </Text>
          ),
        },
        {
          type: 'divider',
        },
        {
          key: 'signout',
          icon: <LogoutOutlined style={{ fontSize: '16px', color: theme.colors.error }} />,
          label: (
            <Text style={{ color: theme.colors.error }}>
              Sign Out
            </Text>
          ),
          danger: true,
        },
      ]}
    />
  );

  const getInitials = () => {
    if (effectiveUser?.firstName && effectiveUser?.lastName) {
      return `${effectiveUser.firstName[0]}${effectiveUser.lastName[0]}`.toUpperCase();
    } else if (effectiveUser?.firstName) {
      return effectiveUser.firstName.substring(0, 2).toUpperCase();
    } else if (effectiveUser?.emailAddresses?.[0]) {
      return effectiveUser.emailAddresses[0].emailAddress.substring(0, 2).toUpperCase();
    } else if (effectiveUser?.email) {
      return effectiveUser.email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  const getAvatarColor = () => {
    const colors = [theme.colors.primary, theme.colors.success, theme.colors.accent, '#AF52DE', '#007AFF'];
    const index = (effectiveUser?.id || '').charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <>
      <div style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999,
      }}>
        <Dropdown overlay={menu} trigger={['click']} placement="bottomRight">
          <Button
            type="text"
            className="profile-dropdown-button"
            style={{
              height: '44px',
              minWidth: '120px',
              padding: '6px 16px',
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              position: 'relative',
              pointerEvents: 'auto',
              zIndex: 1,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)';
              e.currentTarget.style.border = '1px solid rgba(255, 255, 255, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.border = '1px solid rgba(255, 255, 255, 0.15)';
            }}
          >
            <Space align="center" size={10}>
              <Avatar
                size={36}
                style={{
                  backgroundColor: getAvatarColor(),
                  fontSize: '16px',
                  fontWeight: 600,
                  border: '2px solid rgba(255, 255, 255, 0.1)',
                }}
                src={effectiveUser?.imageUrl}
              >
                {!effectiveUser?.imageUrl && getInitials()}
              </Avatar>
              <Text style={{
                color: theme.colors.text.primary,
                fontSize: '15px',
                fontWeight: 500,
                maxWidth: '150px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {effectiveUser?.firstName || (effectiveUser?.emailAddresses?.[0]?.emailAddress || effectiveUser?.email || '').split('@')[0]}
              </Text>
              <DownOutlined style={{
                fontSize: '12px',
                color: theme.colors.text.primary,
                marginLeft: '4px',
              }} />
            </Space>
          </Button>
        </Dropdown>
      </div>

      <UserProfile
        visible={profileVisible}
        onClose={() => setProfileVisible(false)}
      />
    </>
  );
};