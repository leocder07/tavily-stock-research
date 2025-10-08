import React, { useState } from 'react';
import {
  Card,
  Steps,
  Button,
  Space,
  Typography,
  Radio,
  Slider,
  Select,
  Progress,
  Avatar,
  Tag,
  message,
  Checkbox,
} from 'antd';
import {
  
  TrophyOutlined,
  RobotOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  RocketOutlined,
  LineChartOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { theme } from '../styles/theme';
import { useUser } from '@clerk/clerk-react';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface OnboardingQuestionnaireProps {
  onComplete: (profile: UserProfile) => void;
}

interface UserProfile {
  user_id: string;
  investmentGoals: string[];
  riskTolerance: string;
  experienceLevel: string;
  preferredSectors: string[];
  investmentHorizon: string;
  capitalRange: string;
  aiPersonality: string;
  tradingStyle: string;
  dashboardPreferences: {
    layout: string;
    dataVisualization: string;
    updateFrequency: string;
  };
}

const AI_PERSONALITIES = [
  {
    id: 'buffett',
    name: 'Conservative Sage',
    icon: <SafetyOutlined />,
    description: 'Warren Buffett style - Focus on value investing and long-term growth',
    color: '#00D4AA',
    traits: ['Value Focused', 'Long-term', 'Fundamental Analysis', 'Risk-Averse'],
  },
  {
    id: 'wood',
    name: 'Growth Innovator',
    icon: <RocketOutlined />,
    description: 'Cathie Wood style - Emphasis on disruptive innovation and growth',
    color: '#D4AF37',
    traits: ['Innovation', 'High Growth', 'Technology Focus', 'Future-Oriented'],
  },
  {
    id: 'quant',
    name: 'Data Scientist',
    icon: <BarChartOutlined />,
    description: 'Quantitative approach - Algorithm-driven analysis and patterns',
    color: '#FF9F0A',
    traits: ['Data-Driven', 'Technical Analysis', 'Pattern Recognition', 'Systematic'],
  },
  {
    id: 'dalio',
    name: 'Balanced Strategist',
    icon: <LineChartOutlined />,
    description: 'Ray Dalio style - Diversified, principle-based investing',
    color: '#007AFF',
    traits: ['Diversified', 'Risk Parity', 'Macro Analysis', 'Systematic'],
  },
  {
    id: 'lynch',
    name: 'Opportunity Hunter',
    icon: <BulbOutlined />,
    description: 'Peter Lynch style - Find hidden gems before the crowd',
    color: '#AF52DE',
    traits: ['Research Intensive', 'Small-Mid Cap', 'Growth at Reasonable Price', 'Active'],
  },
];

export const OnboardingQuestionnaire: React.FC<OnboardingQuestionnaireProps> = ({ onComplete }) => {
  const { user } = useUser();
  const [currentStep, setCurrentStep] = useState(0);
  const [profile, setProfile] = useState<Partial<UserProfile>>({
    user_id: user?.id || '',
    investmentGoals: [],
    preferredSectors: [],
    dashboardPreferences: {
      layout: 'comprehensive',
      dataVisualization: 'charts',
      updateFrequency: 'real-time',
    },
  });

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    try {
      // Save profile to backend
      await axios.post('/api/v1/user/profile', profile);
      localStorage.setItem('onboardingComplete', 'true');
      message.success('Profile created successfully! Your AI advisor is ready.');
      onComplete(profile as UserProfile);
    } catch (error) {
      message.error('Failed to save profile. Please try again.');
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
              Welcome! Let's personalize your experience
            </Title>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text style={{ color: theme.colors.text.secondary }}>
                  What are your investment goals? (Select all that apply)
                </Text>
                <Checkbox.Group
                  style={{ width: '100%', marginTop: '16px' }}
                  value={profile.investmentGoals}
                  onChange={(values) => setProfile({ ...profile, investmentGoals: values as string[] })}
                >
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {[
                      { value: 'wealth-building', label: '💰 Build Long-term Wealth' },
                      { value: 'retirement', label: '🏖️ Retirement Planning' },
                      { value: 'income', label: '💵 Generate Passive Income' },
                      { value: 'growth', label: '📈 Aggressive Growth' },
                      { value: 'preservation', label: '🛡️ Capital Preservation' },
                      { value: 'education', label: '🎓 Education/Learning' },
                    ].map((goal) => (
                      <Card
                        key={goal.value}
                        style={{
                          background: profile.investmentGoals?.includes(goal.value)
                            ? 'rgba(212, 175, 55, 0.1)'
                            : 'rgba(255, 255, 255, 0.05)',
                          border: profile.investmentGoals?.includes(goal.value)
                            ? '1px solid rgba(212, 175, 55, 0.5)'
                            : '1px solid rgba(255, 255, 255, 0.1)',
                          cursor: 'pointer',
                        }}
                      >
                        <Checkbox value={goal.value} style={{ width: '100%' }}>
                          <Text style={{ color: theme.colors.text.primary, fontSize: '16px' }}>
                            {goal.label}
                          </Text>
                        </Checkbox>
                      </Card>
                    ))}
                  </Space>
                </Checkbox.Group>
              </div>
            </Space>
          </motion.div>
        );

      case 1:
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
              Risk & Experience Assessment
            </Title>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text style={{ color: theme.colors.text.secondary }}>
                  What's your risk tolerance?
                </Text>
                <Radio.Group
                  style={{ width: '100%', marginTop: '16px' }}
                  value={profile.riskTolerance}
                  onChange={(e) => setProfile({ ...profile, riskTolerance: e.target.value })}
                >
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {[
                      { value: 'conservative', label: 'Conservative', icon: '🛡️', desc: 'Preserve capital, minimal risk' },
                      { value: 'moderate', label: 'Moderate', icon: '⚖️', desc: 'Balanced risk and reward' },
                      { value: 'aggressive', label: 'Aggressive', icon: '🚀', desc: 'High risk, high potential returns' },
                    ].map((option) => (
                      <Card
                        key={option.value}
                        style={{
                          background: profile.riskTolerance === option.value
                            ? 'rgba(212, 175, 55, 0.1)'
                            : 'rgba(255, 255, 255, 0.05)',
                          border: profile.riskTolerance === option.value
                            ? '1px solid rgba(212, 175, 55, 0.5)'
                            : '1px solid rgba(255, 255, 255, 0.1)',
                          cursor: 'pointer',
                        }}
                        onClick={() => setProfile({ ...profile, riskTolerance: option.value })}
                      >
                        <Radio value={option.value}>
                          <Space>
                            <span style={{ fontSize: '24px' }}>{option.icon}</span>
                            <div>
                              <div style={{ color: theme.colors.text.primary, fontSize: '16px', fontWeight: 600 }}>
                                {option.label}
                              </div>
                              <Text style={{ color: theme.colors.text.secondary, fontSize: '14px' }}>
                                {option.desc}
                              </Text>
                            </div>
                          </Space>
                        </Radio>
                      </Card>
                    ))}
                  </Space>
                </Radio.Group>
              </div>

              <div>
                <Text style={{ color: theme.colors.text.secondary }}>
                  Your trading experience level:
                </Text>
                <Slider
                  marks={{
                    0: 'Beginner',
                    50: 'Intermediate',
                    100: 'Expert',
                  }}
                  defaultValue={50}
                  onChange={(value) => {
                    const level = value <= 33 ? 'beginner' : value <= 66 ? 'intermediate' : 'expert';
                    setProfile({ ...profile, experienceLevel: level });
                  }}
                  style={{ marginTop: '24px' }}
                />
              </div>
            </Space>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
              Choose Your AI Advisor Personality
            </Title>
            <Paragraph style={{ color: theme.colors.text.secondary, marginBottom: '32px' }}>
              Select an AI personality that matches your investment philosophy
            </Paragraph>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '16px',
            }}>
              {AI_PERSONALITIES.map((personality) => (
                <Card
                  key={personality.id}
                  hoverable
                  style={{
                    background: profile.aiPersonality === personality.id
                      ? `linear-gradient(135deg, ${personality.color}20, transparent)`
                      : 'rgba(255, 255, 255, 0.05)',
                    border: profile.aiPersonality === personality.id
                      ? `2px solid ${personality.color}`
                      : '1px solid rgba(255, 255, 255, 0.1)',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                  }}
                  onClick={() => setProfile({ ...profile, aiPersonality: personality.id })}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space>
                      <Avatar
                        size={48}
                        style={{
                          background: personality.color,
                          fontSize: '24px',
                        }}
                      >
                        {personality.icon}
                      </Avatar>
                      <div>
                        <Title level={5} style={{ color: theme.colors.text.primary, margin: 0 }}>
                          {personality.name}
                        </Title>
                        <Text style={{ color: theme.colors.text.secondary, fontSize: '12px' }}>
                          {personality.description}
                        </Text>
                      </div>
                    </Space>
                    <Space wrap size={[4, 4]}>
                      {personality.traits.map((trait) => (
                        <Tag
                          key={trait}
                          style={{
                            background: 'rgba(255, 255, 255, 0.1)',
                            border: 'none',
                            color: personality.color,
                          }}
                        >
                          {trait}
                        </Tag>
                      ))}
                    </Space>
                  </Space>
                </Card>
              ))}
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
              Market Preferences
            </Title>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text style={{ color: theme.colors.text.secondary }}>
                  Preferred sectors (Select up to 5)
                </Text>
                <Select
                  mode="multiple"
                  size="large"
                  placeholder="Select your preferred sectors"
                  style={{ width: '100%', marginTop: '16px' }}
                  value={profile.preferredSectors}
                  onChange={(values) => setProfile({ ...profile, preferredSectors: values })}
                  maxTagCount={5}
                  options={[
                    { value: 'technology', label: '💻 Technology' },
                    { value: 'healthcare', label: '🏥 Healthcare' },
                    { value: 'finance', label: '🏦 Finance' },
                    { value: 'energy', label: '⚡ Energy' },
                    { value: 'consumer', label: '🛍️ Consumer' },
                    { value: 'industrial', label: '🏭 Industrial' },
                    { value: 'realestate', label: '🏠 Real Estate' },
                    { value: 'materials', label: '🔧 Materials' },
                    { value: 'utilities', label: '💡 Utilities' },
                    { value: 'crypto', label: '🪙 Cryptocurrency' },
                  ]}
                />
              </div>

              <div>
                <Text style={{ color: theme.colors.text.secondary }}>
                  Investment horizon
                </Text>
                <Radio.Group
                  style={{ width: '100%', marginTop: '16px' }}
                  value={profile.investmentHorizon}
                  onChange={(e) => setProfile({ ...profile, investmentHorizon: e.target.value })}
                >
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {[
                      { value: 'day-trading', label: 'Day Trading', desc: 'Minutes to hours' },
                      { value: 'swing', label: 'Swing Trading', desc: 'Days to weeks' },
                      { value: 'position', label: 'Position Trading', desc: 'Weeks to months' },
                      { value: 'long-term', label: 'Long-term Investing', desc: 'Years' },
                    ].map((option) => (
                      <Card
                        key={option.value}
                        style={{
                          background: profile.investmentHorizon === option.value
                            ? 'rgba(212, 175, 55, 0.1)'
                            : 'rgba(255, 255, 255, 0.05)',
                          border: profile.investmentHorizon === option.value
                            ? '1px solid rgba(212, 175, 55, 0.5)'
                            : '1px solid rgba(255, 255, 255, 0.1)',
                          cursor: 'pointer',
                        }}
                        onClick={() => setProfile({ ...profile, investmentHorizon: option.value })}
                      >
                        <Radio value={option.value}>
                          <Space direction="vertical" size={0}>
                            <Text style={{ color: theme.colors.text.primary, fontSize: '16px' }}>
                              {option.label}
                            </Text>
                            <Text style={{ color: theme.colors.text.secondary, fontSize: '14px' }}>
                              {option.desc}
                            </Text>
                          </Space>
                        </Radio>
                      </Card>
                    ))}
                  </Space>
                </Radio.Group>
              </div>
            </Space>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title level={3} style={{ color: theme.colors.text.primary, marginBottom: '24px' }}>
              🎉 Perfect! Your Profile is Ready
            </Title>
            <Card
              style={{
                background: theme.colors.gradient.glass,
                border: '1px solid rgba(212, 175, 55, 0.3)',
                marginBottom: '24px',
              }}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text strong style={{ color: theme.colors.primary }}>AI Advisor:</Text>
                  <Text style={{ color: theme.colors.text.primary, marginLeft: '8px' }}>
                    {AI_PERSONALITIES.find(p => p.id === profile.aiPersonality)?.name}
                  </Text>
                </div>
                <div>
                  <Text strong style={{ color: theme.colors.primary }}>Risk Profile:</Text>
                  <Text style={{ color: theme.colors.text.primary, marginLeft: '8px', textTransform: 'capitalize' }}>
                    {profile.riskTolerance}
                  </Text>
                </div>
                <div>
                  <Text strong style={{ color: theme.colors.primary }}>Experience:</Text>
                  <Text style={{ color: theme.colors.text.primary, marginLeft: '8px', textTransform: 'capitalize' }}>
                    {profile.experienceLevel}
                  </Text>
                </div>
                <div>
                  <Text strong style={{ color: theme.colors.primary }}>Investment Goals:</Text>
                  <div style={{ marginTop: '8px' }}>
                    {profile.investmentGoals?.map((goal) => (
                      <Tag key={goal} style={{ marginBottom: '4px' }}>
                        {goal.replace('-', ' ').toUpperCase()}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Space>
            </Card>
            <div style={{
              textAlign: 'center',
              padding: '24px',
              background: 'rgba(0, 212, 170, 0.1)',
              borderRadius: theme.borderRadius.md,
              border: '1px solid rgba(0, 212, 170, 0.2)',
            }}>
              <CheckCircleOutlined style={{ fontSize: '48px', color: theme.colors.success }} />
              <Title level={4} style={{ color: theme.colors.text.primary, marginTop: '16px' }}>
                Your personalized dashboard is ready!
              </Title>
              <Paragraph style={{ color: theme.colors.text.secondary }}>
                Your AI advisor will now analyze markets based on your preferences
              </Paragraph>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      padding: '48px',
      background: theme.colors.background.primary,
    }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <Progress
          percent={(currentStep + 1) * 20}
          strokeColor={theme.colors.gradient.primary}
          showInfo={false}
          style={{ marginBottom: '48px' }}
        />

        <Steps current={currentStep} style={{ marginBottom: '48px' }}>
          <Step title="Goals" icon={<TrophyOutlined />} />
          <Step title="Risk Profile" icon={<SafetyOutlined />} />
          <Step title="AI Advisor" icon={<RobotOutlined />} />
          <Step title="Preferences" icon={<BarChartOutlined />} />
          <Step title="Complete" icon={<CheckCircleOutlined />} />
        </Steps>

        <Card
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            minHeight: '400px',
          }}
        >
          {renderStepContent()}
        </Card>

        <Space style={{ marginTop: '32px', width: '100%', justifyContent: 'space-between' }}>
          <Button
            size="large"
            onClick={handleBack}
            disabled={currentStep === 0}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            Back
          </Button>
          <Button
            size="large"
            type="primary"
            onClick={handleNext}
            style={{
              background: theme.colors.gradient.primary,
              border: 'none',
            }}
            icon={currentStep === 4 ? <CheckCircleOutlined /> : <ThunderboltOutlined />}
          >
            {currentStep === 4 ? 'Launch Dashboard' : 'Next'}
          </Button>
        </Space>
      </div>
    </div>
  );
};