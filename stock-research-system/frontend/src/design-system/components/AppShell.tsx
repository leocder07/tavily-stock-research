import React, { useState, ReactNode } from 'react';
import { Layout } from 'antd';
import { designTokens } from '../tokens';
import { useResponsive } from '../hooks/useResponsive';
import './AppShell.css';

const { Header, Sider, Content } = Layout;

interface AppShellProps {
  header: ReactNode;
  sidebar?: ReactNode;
  children: ReactNode;
  mobileHeader?: ReactNode;
  showSidebar?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  header,
  sidebar,
  children,
  mobileHeader,
  showSidebar = true,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { isMobile, isTablet, isDesktop } = useResponsive();

  // Automatically collapse sidebar on tablet
  React.useEffect(() => {
    if (isTablet) {
      setSidebarCollapsed(true);
    } else if (isDesktop) {
      setSidebarCollapsed(false);
    }
  }, [isTablet, isDesktop]);

  const sidebarWidth = parseInt(designTokens.layout.sidebarWidth);
  const sidebarCollapsedWidth = parseInt(designTokens.layout.sidebarWidthCollapsed);
  const headerHeight = isMobile
    ? designTokens.layout.headerHeightMobile
    : designTokens.layout.headerHeight;

  return (
    <Layout className="app-shell" style={{ minHeight: '100vh' }}>
      {/* Header */}
      <Header
        className={`app-shell__header ${isMobile ? 'app-shell__header--mobile' : ''}`}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: designTokens.zIndex.sticky,
          height: headerHeight,
          padding: 0,
          background: designTokens.colors.background.elevated,
          borderBottom: `1px solid ${designTokens.colors.border.default}`,
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}
      >
        {isMobile && mobileHeader ? mobileHeader : header}
      </Header>

      <Layout style={{ marginTop: headerHeight }}>
        {/* Sidebar - Desktop and Tablet only */}
        {!isMobile && showSidebar && sidebar && (
          <Sider
            className="app-shell__sidebar"
            collapsible
            collapsed={sidebarCollapsed}
            onCollapse={setSidebarCollapsed}
            width={sidebarWidth}
            collapsedWidth={sidebarCollapsedWidth}
            trigger={null}
            style={{
              position: 'fixed',
              left: 0,
              top: headerHeight,
              bottom: 0,
              zIndex: designTokens.zIndex.fixed,
              background: designTokens.colors.background.secondary,
              borderRight: `1px solid ${designTokens.colors.border.default}`,
              overflowY: 'auto',
              overflowX: 'hidden',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            <div className="app-shell__sidebar-content">
              {sidebar}
            </div>

            {/* Collapse Toggle Button */}
            <button
              className="app-shell__sidebar-toggle"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{
                position: 'absolute',
                right: '-12px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '24px',
                height: '48px',
                background: designTokens.colors.background.card,
                border: `1px solid ${designTokens.colors.border.default}`,
                borderRadius: '0 12px 12px 0',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: designTokens.colors.text.secondary,
                fontSize: '12px',
                transition: 'all 0.2s ease',
                zIndex: designTokens.zIndex.fixed + 1,
              }}
            >
              {sidebarCollapsed ? '▶' : '◀'}
            </button>
          </Sider>
        )}

        {/* Main Content Area */}
        <Content
          className="app-shell__content"
          style={{
            marginLeft: isMobile
              ? 0
              : showSidebar && sidebar
                ? (sidebarCollapsed ? sidebarCollapsedWidth : sidebarWidth)
                : 0,
            background: designTokens.colors.background.primary,
            minHeight: `calc(100vh - ${headerHeight})`,
            transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
          }}
        >
          <div
            className="app-shell__content-wrapper"
            style={{
              maxWidth: designTokens.layout.contentMaxWidth,
              margin: '0 auto',
              padding: isMobile
                ? designTokens.layout.containerPaddingMobile
                : designTokens.layout.containerPadding,
              width: '100%',
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};