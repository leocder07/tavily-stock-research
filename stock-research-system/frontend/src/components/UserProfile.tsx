import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Typography,
  Row,
  Col,
  Tag,
  Space,
  Button,
  Avatar,
  Spin,
  message,
  Form,
  Select,
  Checkbox,
  Radio,
  Upload,
  Slider,
  Input,
} from 'antd';
import {
  UserOutlined,
  TrophyOutlined,
  SafetyOutlined,
  RocketOutlined,
  BulbOutlined,
  BarChartOutlined,
  LineChartOutlined,
  EditOutlined,
  CloseOutlined,
  SaveOutlined,
  CameraOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useUser } from '@clerk/clerk-react';
import axios from 'axios';
import { theme } from '../styles/theme';

const { Title, Text, Paragraph } = Typography;

interface UserProfileData {
  user_id: string;
  investmentGoals: string[];
  riskTolerance: string;
  experienceLevel: string;
  preferredSectors: string[];
  investmentHorizon: string;
  capitalRange?: string;
  aiPersonality: string;
  tradingStyle?: string;
  dashboardPreferences: {
    layout: string;
    dataVisualization: string;
    updateFrequency: string;
  };
  created_at?: string;
  updated_at?: string;
}

const AI_PERSONALITIES = [
  {
    id: 'buffett',
    name: 'Conservative Sage',
    icon: <SafetyOutlined />,
    description: 'Warren Buffett style - Focus on value investing',
    color: '#00D4AA',
    gradient: 'linear-gradient(135deg, #00D4AA 0%, #00A389 100%)',
    traits: ['Value Focused', 'Long-term', 'Risk-Averse'],
  },
  {
    id: 'wood',
    name: 'Growth Innovator',
    icon: <RocketOutlined />,
    description: 'Cathie Wood style - Disruptive innovation',
    color: '#D4AF37',
    gradient: 'linear-gradient(135deg, #D4AF37 0%, #B8941F 100%)',
    traits: ['Innovation', 'High Growth', 'Technology'],
  },
  {
    id: 'quant',
    name: 'Data Scientist',
    icon: <BarChartOutlined />,
    description: 'Quantitative approach - Algorithm-driven',
    color: '#FF9F0A',
    gradient: 'linear-gradient(135deg, #FF9F0A 0%, #E08700 100%)',
    traits: ['Data-Driven', 'Technical', 'Systematic'],
  },
  {
    id: 'dalio',
    name: 'Balanced Strategist',
    icon: <LineChartOutlined />,
    description: 'Ray Dalio style - Diversified investing',
    color: '#007AFF',
    gradient: 'linear-gradient(135deg, #007AFF 0%, #0056CC 100%)',
    traits: ['Diversified', 'Risk Parity', 'Macro'],
  },
  {
    id: 'lynch',
    name: 'Opportunity Hunter',
    icon: <BulbOutlined />,
    description: 'Peter Lynch style - Hidden gems',
    color: '#AF52DE',
    gradient: 'linear-gradient(135deg, #AF52DE 0%, #8E3BB5 100%)',
    traits: ['Research', 'Small-Mid Cap', 'Active'],
  },
];

const GOAL_OPTIONS = [
  { value: 'wealth-building', label: '💰 Build Long-term Wealth' },
  { value: 'retirement', label: '🏖️ Retirement Planning' },
  { value: 'income', label: '💵 Generate Passive Income' },
  { value: 'education', label: '🎓 Education Savings' },
  { value: 'growth', label: '📈 Aggressive Growth' },
  { value: 'preservation', label: '🛡️ Capital Preservation' },
];

const SECTOR_OPTIONS = [
  { value: 'technology', label: '💻 Technology' },
  { value: 'healthcare', label: '🏥 Healthcare' },
  { value: 'finance', label: '🏦 Finance' },
  { value: 'energy', label: '⚡ Energy' },
  { value: 'consumer', label: '🛍️ Consumer' },
  { value: 'industrial', label: '🏭 Industrial' },
  { value: 'realestate', label: '🏢 Real Estate' },
  { value: 'crypto', label: '🪙 Cryptocurrency' },
];

const CAPITAL_RANGES = [
  { value: 'under-10k', label: 'Under $10K' },
  { value: '10k-50k', label: '$10K - $50K' },
  { value: '50k-100k', label: '$50K - $100K' },
  { value: '100k-500k', label: '$100K - $500K' },
  { value: '500k-1m', label: '$500K - $1M' },
  { value: 'over-1m', label: 'Over $1M' },
];

interface UserProfileProps {
  visible: boolean;
  onClose: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ visible, onClose }) => {
  const { user } = useUser();
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [form] = Form.useForm();

  // Check for test user session
  const testUserSession = localStorage.getItem('testUserSession');
  const testUser = testUserSession ? JSON.parse(testUserSession) : null;
  const effectiveUserId = testUser?.id || user?.id;

  useEffect(() => {
    if (visible && effectiveUserId) {
      fetchProfile();
    }
  }, [visible, effectiveUserId]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/user/profile/${effectiveUserId}`);

      const profileData = response.data.profile;
      const transformedProfile: UserProfileData = {
        user_id: profileData.user_id,
        investmentGoals: profileData.investment_goals || [],
        riskTolerance: profileData.risk_tolerance || '',
        experienceLevel: profileData.experience_level || '',
        preferredSectors: profileData.preferred_sectors || [],
        investmentHorizon: profileData.investment_horizon || '',
        capitalRange: profileData.capital_range,
        aiPersonality: profileData.ai_personality || '',
        tradingStyle: profileData.trading_style,
        dashboardPreferences: {
          layout: profileData.dashboard_preferences?.layout || 'modern',
          dataVisualization: profileData.dashboard_preferences?.data_visualization || 'charts',
          updateFrequency: profileData.dashboard_preferences?.update_frequency || 'real-time',
        },
        created_at: profileData.created_at,
        updated_at: profileData.updated_at,
      };

      setProfile(transformedProfile);
      form.setFieldsValue(transformedProfile);
      setAvatarUrl(user?.imageUrl || null);
    } catch (error) {
      message.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const values = await form.validateFields();

      const payload = {
        investment_goals: values.investmentGoals,
        risk_tolerance: values.riskTolerance,
        experience_level: values.experienceLevel,
        preferred_sectors: values.preferredSectors,
        investment_horizon: values.investmentHorizon,
        capital_range: values.capitalRange,
        ai_personality: values.aiPersonality,
        trading_style: values.tradingStyle,
        dashboard_preferences: {
          layout: values.dashboardPreferences?.layout || 'modern',
          data_visualization: values.dashboardPreferences?.dataVisualization || 'charts',
          update_frequency: values.dashboardPreferences?.updateFrequency || 'real-time',
        },
      };

      await axios.put(`/api/v1/user/profile/${effectiveUserId}`, payload);

      message.success('Profile updated successfully!');
      await fetchProfile();
      onClose();
    } catch (error: any) {
      console.error('Save error:', error);
      message.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const selectedPersonality = AI_PERSONALITIES.find((p) => p.id === form.getFieldValue('aiPersonality'));

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width="95%"
      style={{ top: 20, maxWidth: 1400 }}
      styles={{
        body: {
          background: theme.colors.background.primary,
          padding: 0,
          maxHeight: 'calc(100vh - 100px)',
          overflowY: 'auto',
        },
      }}
      closeIcon={null}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '100px 20px' }}>
          <Spin size="large" />
        </div>
      ) : (
        <div>
          {/* Header with Gradient and Avatar */}
          <div
            style={{
              background: selectedPersonality?.gradient || theme.colors.gradient.primary,
              padding: '48px 64px',
              position: 'relative',
            }}
          >
            <Button
              type="text"
              icon={<CloseOutlined style={{ fontSize: '24px', color: '#ffffff' }} />}
              onClick={onClose}
              style={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                padding: '12px',
              }}
            />

            <Row gutter={32} align="middle">
              <Col>
                <div style={{ position: 'relative' }}>
                  <Avatar
                    size={140}
                    src={avatarUrl}
                    icon={<UserOutlined />}
                    style={{
                      background: 'rgba(255, 255, 255, 0.25)',
                      backdropFilter: 'blur(10px)',
                      border: '4px solid rgba(255, 255, 255, 0.5)',
                    }}
                  />
                  <Button
                    shape="circle"
                    icon={<CameraOutlined />}
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      background: '#ffffff',
                      border: 'none',
                      width: '42px',
                      height: '42px',
                    }}
                    onClick={() => message.info('Avatar upload coming soon!')}
                  />
                </div>
              </Col>
              <Col flex={1}>
                <Title level={1} style={{ color: '#ffffff', margin: 0, fontSize: '40px', fontWeight: 700 }}>
                  {testUser?.firstName || user?.firstName || 'Investor'} {testUser?.lastName || user?.lastName || ''}
                </Title>
                <Text style={{ color: 'rgba(255, 255, 255, 0.85)', fontSize: '18px', display: 'block', marginTop: '8px' }}>
                  {testUser?.email || user?.emailAddresses?.[0]?.emailAddress}
                </Text>
                {selectedPersonality && (
                  <div style={{ marginTop: '20px' }}>
                    <Space size="middle">
                      <div
                        style={{
                          background: 'rgba(255, 255, 255, 0.2)',
                          backdropFilter: 'blur(20px)',
                          border: '1px solid rgba(255, 255, 255, 0.3)',
                          borderRadius: '12px',
                          padding: '8px 16px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '12px',
                        }}
                      >
                        <span style={{ fontSize: '24px', color: '#ffffff' }}>{selectedPersonality.icon}</span>
                        <div>
                          <Text strong style={{ color: '#ffffff', fontSize: '16px', display: 'block' }}>
                            {selectedPersonality.name}
                          </Text>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '13px' }}>
                            {selectedPersonality.description}
                          </Text>
                        </div>
                        <ThunderboltOutlined style={{ color: '#FFD700', fontSize: '20px' }} />
                      </div>
                    </Space>
                  </div>
                )}
              </Col>
            </Row>
          </div>

          {/* Form Content */}
          <div style={{ padding: '48px 64px' }}>
            <Form form={form} layout="vertical" initialValues={profile || undefined}>
              {/* AI Personality Section */}
              <Card
                style={{
                  background: theme.colors.gradient.glass,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: '20px',
                  marginBottom: '32px',
                  boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                }}
              >
                <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
                  <RocketOutlined style={{ color: theme.colors.primary, marginRight: '12px' }} />
                  AI Advisor Personality
                </Title>
                <Form.Item name="aiPersonality">
                  <Radio.Group style={{ width: '100%' }}>
                    <Row gutter={[16, 16]}>
                      {AI_PERSONALITIES.map((personality) => (
                        <Col xs={24} sm={12} lg={8} xl={4.8} key={personality.id}>
                          <Radio.Button
                            value={personality.id}
                            style={{
                              width: '100%',
                              height: 'auto',
                              padding: '20px',
                              borderRadius: '16px',
                              background: theme.colors.gradient.glass,
                              border: `2px solid ${theme.colors.border}`,
                            }}
                          >
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: '40px', color: personality.color, marginBottom: '12px' }}>
                                {personality.icon}
                              </div>
                              <Text strong style={{ color: theme.colors.text.primary, fontSize: '15px', display: 'block' }}>
                                {personality.name}
                              </Text>
                              <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}>
                                {personality.description}
                              </Text>
                              <Space wrap style={{ marginTop: '12px', justifyContent: 'center' }}>
                                {personality.traits.map((trait) => (
                                  <Tag
                                    key={trait}
                                    style={{
                                      background: `${personality.color}20`,
                                      border: `1px solid ${personality.color}40`,
                                      color: personality.color,
                                      fontSize: '11px',
                                    }}
                                  >
                                    {trait}
                                  </Tag>
                                ))}
                              </Space>
                            </div>
                          </Radio.Button>
                        </Col>
                      ))}
                    </Row>
                  </Radio.Group>
                </Form.Item>
              </Card>

              <Row gutter={32}>
                {/* Left Column */}
                <Col xs={24} lg={12}>
                  {/* Investment Goals */}
                  <Card
                    style={{
                      background: theme.colors.gradient.glass,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '20px',
                      marginBottom: '32px',
                      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                    }}
                  >
                    <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: '20px' }}>
                      <TrophyOutlined style={{ color: theme.colors.primary, marginRight: '12px' }} />
                      Investment Goals
                    </Title>
                    <Form.Item name="investmentGoals">
                      <Checkbox.Group style={{ width: '100%' }}>
                        <Row gutter={[12, 16]}>
                          {GOAL_OPTIONS.map((option) => (
                            <Col span={24} key={option.value}>
                              <Checkbox value={option.value} style={{ fontSize: '15px', width: '100%' }}>
                                <Text style={{ color: theme.colors.text.primary }}>{option.label}</Text>
                              </Checkbox>
                            </Col>
                          ))}
                        </Row>
                      </Checkbox.Group>
                    </Form.Item>
                  </Card>

                  {/* Risk & Experience */}
                  <Row gutter={16}>
                    <Col span={12}>
                      <Card
                        style={{
                          background: theme.colors.gradient.glass,
                          border: `1px solid ${theme.colors.border}`,
                          borderRadius: '16px',
                          marginBottom: '32px',
                          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                        }}
                      >
                        <Form.Item
                          name="riskTolerance"
                          label={<Text strong style={{ fontSize: '16px' }}>Risk Tolerance</Text>}
                        >
                          <Select size="large" style={{ width: '100%' }}>
                            <Select.Option value="conservative">🛡️ Conservative</Select.Option>
                            <Select.Option value="moderate">⚖️ Moderate</Select.Option>
                            <Select.Option value="aggressive">🚀 Aggressive</Select.Option>
                          </Select>
                        </Form.Item>
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card
                        style={{
                          background: theme.colors.gradient.glass,
                          border: `1px solid ${theme.colors.border}`,
                          borderRadius: '16px',
                          marginBottom: '32px',
                          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                        }}
                      >
                        <Form.Item
                          name="experienceLevel"
                          label={<Text strong style={{ fontSize: '16px' }}>Experience Level</Text>}
                        >
                          <Select size="large" style={{ width: '100%' }}>
                            <Select.Option value="beginner">🌱 Beginner</Select.Option>
                            <Select.Option value="intermediate">📈 Intermediate</Select.Option>
                            <Select.Option value="advanced">🎯 Advanced</Select.Option>
                            <Select.Option value="expert">🏆 Expert</Select.Option>
                          </Select>
                        </Form.Item>
                      </Card>
                    </Col>
                  </Row>

                  {/* Investment Details */}
                  <Row gutter={16}>
                    <Col span={12}>
                      <Card
                        style={{
                          background: theme.colors.gradient.glass,
                          border: `1px solid ${theme.colors.border}`,
                          borderRadius: '16px',
                          marginBottom: '32px',
                          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                        }}
                      >
                        <Form.Item
                          name="investmentHorizon"
                          label={<Text strong style={{ fontSize: '16px' }}>Investment Horizon</Text>}
                        >
                          <Select size="large">
                            <Select.Option value="short">⚡ Short Term</Select.Option>
                            <Select.Option value="medium">📊 Medium Term</Select.Option>
                            <Select.Option value="long">🎯 Long Term</Select.Option>
                          </Select>
                        </Form.Item>
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card
                        style={{
                          background: theme.colors.gradient.glass,
                          border: `1px solid ${theme.colors.border}`,
                          borderRadius: '16px',
                          marginBottom: '32px',
                          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                        }}
                      >
                        <Form.Item
                          name="tradingStyle"
                          label={<Text strong style={{ fontSize: '16px' }}>Trading Style</Text>}
                        >
                          <Select size="large">
                            <Select.Option value="value">💎 Value</Select.Option>
                            <Select.Option value="growth">🚀 Growth</Select.Option>
                            <Select.Option value="income">💰 Income</Select.Option>
                            <Select.Option value="momentum">⚡ Momentum</Select.Option>
                          </Select>
                        </Form.Item>
                      </Card>
                    </Col>
                  </Row>

                  {/* Capital Range */}
                  <Card
                    style={{
                      background: theme.colors.gradient.glass,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '16px',
                      marginBottom: '32px',
                      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                    }}
                  >
                    <Form.Item
                      name="capitalRange"
                      label={<Text strong style={{ fontSize: '16px' }}>Capital Range</Text>}
                    >
                      <Select size="large" placeholder="Select your investment capital range">
                        {CAPITAL_RANGES.map((range) => (
                          <Select.Option key={range.value} value={range.value}>
                            {range.label}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Card>
                </Col>

                {/* Right Column */}
                <Col xs={24} lg={12}>
                  {/* Preferred Sectors */}
                  <Card
                    style={{
                      background: theme.colors.gradient.glass,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '20px',
                      marginBottom: '32px',
                      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                    }}
                  >
                    <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: '20px' }}>
                      <BarChartOutlined style={{ color: theme.colors.primary, marginRight: '12px' }} />
                      Preferred Sectors
                    </Title>
                    <Form.Item name="preferredSectors">
                      <Checkbox.Group style={{ width: '100%' }}>
                        <Row gutter={[12, 16]}>
                          {SECTOR_OPTIONS.map((option) => (
                            <Col span={12} key={option.value}>
                              <Checkbox value={option.value} style={{ fontSize: '15px', width: '100%' }}>
                                <Text style={{ color: theme.colors.text.primary }}>{option.label}</Text>
                              </Checkbox>
                            </Col>
                          ))}
                        </Row>
                      </Checkbox.Group>
                    </Form.Item>
                  </Card>

                  {/* Dashboard Preferences */}
                  <Card
                    style={{
                      background: theme.colors.gradient.glass,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: '20px',
                      marginBottom: '32px',
                      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.08)',
                    }}
                  >
                    <Title level={4} style={{ color: theme.colors.text.primary, marginBottom: '20px' }}>
                      Dashboard Preferences
                    </Title>
                    <Form.Item name={['dashboardPreferences', 'layout']} label="Layout Style">
                      <Radio.Group>
                        <Radio.Button value="modern">Modern</Radio.Button>
                        <Radio.Button value="classic">Classic</Radio.Button>
                        <Radio.Button value="compact">Compact</Radio.Button>
                      </Radio.Group>
                    </Form.Item>
                    <Form.Item name={['dashboardPreferences', 'dataVisualization']} label="Data Visualization">
                      <Radio.Group>
                        <Radio.Button value="charts">Charts</Radio.Button>
                        <Radio.Button value="tables">Tables</Radio.Button>
                        <Radio.Button value="mixed">Mixed</Radio.Button>
                      </Radio.Group>
                    </Form.Item>
                    <Form.Item name={['dashboardPreferences', 'updateFrequency']} label="Update Frequency">
                      <Radio.Group>
                        <Radio.Button value="real-time">Real-time</Radio.Button>
                        <Radio.Button value="5min">5 Minutes</Radio.Button>
                        <Radio.Button value="15min">15 Minutes</Radio.Button>
                      </Radio.Group>
                    </Form.Item>
                  </Card>
                </Col>
              </Row>
            </Form>
          </div>

          {/* Footer Actions */}
          <div
            style={{
              padding: '24px 64px',
              borderTop: `1px solid ${theme.colors.border}`,
              background: theme.colors.background.secondary,
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '16px',
            }}
          >
            <Button size="large" onClick={onClose} style={{ height: '48px', padding: '0 32px', borderRadius: '12px' }}>
              Cancel
            </Button>
            <Button
              type="primary"
              size="large"
              icon={<SaveOutlined />}
              loading={saving}
              onClick={handleSave}
              style={{
                background: theme.colors.gradient.primary,
                border: 'none',
                height: '48px',
                padding: '0 40px',
                borderRadius: '12px',
                boxShadow: '0 4px 16px rgba(212, 175, 55, 0.4)',
                fontWeight: 600,
              }}
            >
              Save Profile
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};
