import React, { useState } from 'react';
import { Button, Input, Form, message, Card } from 'antd';
import { LoginOutlined, ExperimentOutlined } from '@ant-design/icons';
import { theme } from '../styles/theme';

interface TestUserLoginProps {
  onTestLogin: (email: string, password: string) => void;
}

export const TestUserLogin: React.FC<TestUserLoginProps> = ({ onTestLogin }) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleTestLogin = async (values: { email: string; password: string }) => {
    setLoading(true);

    // Validate test user credentials
    if (values.email === 'vkpr15@gmail.com' && values.password === 'tavilyUser@123') {
      // Store test user session with Clerk-compatible format
      localStorage.setItem('testUserSession', JSON.stringify({
        id: 'user_2test_tavily_vkpr15', // Clerk-compatible ID format
        email: values.email,
        firstName: 'Tavily',
        lastName: 'Test User',
        imageUrl: 'https://api.dicebear.com/7.x/avataaars/svg?seed=TavilyTest',
        emailAddresses: [{
          emailAddress: values.email
        }],
        timestamp: Date.now()
      }));

      message.success('Test user logged in successfully!');
      onTestLogin(values.email, values.password);
    } else {
      message.error('Invalid test user credentials!');
    }

    setLoading(false);
  };

  return (
    <Card
      style={{
        background: theme.colors.gradient.glass,
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 165, 0, 0.3)',
        borderRadius: theme.borderRadius.xl,
        boxShadow: '0 8px 32px rgba(255, 165, 0, 0.2)',
        width: '100%',
        maxWidth: '400px',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <ExperimentOutlined style={{ fontSize: '48px', color: '#FFA500', marginBottom: '16px' }} />
        <h3 style={{ color: theme.colors.text.primary, margin: 0, fontSize: '22px', fontWeight: 600 }}>
          Test User Login
        </h3>
        <p style={{ color: theme.colors.text.secondary, fontSize: '14px', marginTop: '8px' }}>
          Development Mode Only
        </p>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleTestLogin}
        initialValues={{
          email: 'vkpr15@gmail.com',
          password: 'tavilyUser@123'
        }}
      >
        <Form.Item
          label={<span style={{ color: theme.colors.text.secondary, fontWeight: 500 }}>Email</span>}
          name="email"
          rules={[{ required: true, message: 'Please enter email' }]}
        >
          <Input
            size="large"
            placeholder="vkpr15@gmail.com"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: theme.colors.text.primary,
              borderRadius: '12px',
            }}
          />
        </Form.Item>

        <Form.Item
          label={<span style={{ color: theme.colors.text.secondary, fontWeight: 500 }}>Password</span>}
          name="password"
          rules={[{ required: true, message: 'Please enter password' }]}
        >
          <Input.Password
            size="large"
            placeholder="tavilyUser@123"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
            }}
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0 }}>
          <Button
            type="primary"
            size="large"
            icon={<LoginOutlined />}
            htmlType="submit"
            loading={loading}
            block
            style={{
              background: 'linear-gradient(135deg, #FFA500 0%, #FF8C00 100%)',
              border: 'none',
              height: '48px',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: 600,
              boxShadow: '0 4px 16px rgba(255, 165, 0, 0.4)',
            }}
          >
            Login as Test User
          </Button>
        </Form.Item>
      </Form>

      <div style={{
        marginTop: '24px',
        padding: '16px',
        background: 'rgba(255, 165, 0, 0.1)',
        border: '1px solid rgba(255, 165, 0, 0.2)',
        borderRadius: theme.borderRadius.md,
      }}>
        <p style={{ color: '#FFA500', fontSize: '12px', margin: 0, textAlign: 'center' }}>
          ⚠️ Test Credentials:<br />
          Email: vkpr15@gmail.com<br />
          Password: tavilyUser@123
        </p>
      </div>
    </Card>
  );
};
