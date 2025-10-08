import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Form,
  Space,
  Alert,
  Progress,
  Tag,
  Divider,
  Row,
  Col,
  Typography,
  List,
  Spin,
  message,
  Radio,
} from 'antd';
import {
  SearchOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import AgentProgress from './AgentProgress';
import AnalysisResults from './AnalysisResults';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

interface AnalysisState {
  id: string | null;
  status: 'idle' | 'submitting' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentPhase: string;
  results: any | null;
  error: string | null;
}

const StockAnalysis: React.FC = () => {
  const [form] = Form.useForm();
  const [analysis, setAnalysis] = useState<AnalysisState>({
    id: null,
    status: 'idle',
    progress: 0,
    currentPhase: '',
    results: null,
    error: null,
  });
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Sample queries for user convenience
  const sampleQueries = [
    "Should I invest in Apple stock for long-term growth?",
    "Compare Microsoft vs Google for investment",
    "Analyze Tesla's fundamentals and growth potential",
    "Is Amazon stock overvalued at current prices?",
    "Best tech stocks to buy in current market",
    "Evaluate NVIDIA for AI investment opportunity"
  ];

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (analysis.id && analysis.status === 'processing') {
      const websocket = new WebSocket(`${WS_URL}/ws/analysis/${analysis.id}`);

      websocket.onopen = () => {
        console.log('WebSocket connected');
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
      };

      setWs(websocket);

      return () => {
        websocket.close();
      };
    }
  }, [analysis.id, analysis.status]);

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'status') {
      setAnalysis(prev => ({
        ...prev,
        currentPhase: data.message,
      }));
    } else if (data.type === 'progress') {
      setAnalysis(prev => ({
        ...prev,
        progress: data.percentage,
        currentPhase: data.phase,
      }));
    } else if (data.type === 'complete') {
      setAnalysis(prev => ({
        ...prev,
        status: 'completed',
        progress: 100,
      }));
      fetchResults();
    } else if (data.type === 'error') {
      setAnalysis(prev => ({
        ...prev,
        status: 'failed',
        error: data.message,
      }));
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      setAnalysis({
        id: null,
        status: 'submitting',
        progress: 0,
        currentPhase: 'Initializing analysis...',
        results: null,
        error: null,
      });

      const response = await axios.post(`${API_URL}/api/v1/analyze`, {
        query: values.query,
        priority: values.priority || 'normal',
        max_revisions: 2,
        include_technical: true,
        include_sentiment: true,
      });

      const { analysis_id } = response.data;

      setAnalysis({
        id: analysis_id,
        status: 'processing',
        progress: 10,
        currentPhase: 'Query parsing...',
        results: null,
        error: null,
      });

      // Start polling for status
      pollStatus(analysis_id);

    } catch (error: any) {
      message.error('Failed to start analysis');
      setAnalysis(prev => ({
        ...prev,
        status: 'failed',
        error: error.response?.data?.detail || 'Unknown error occurred',
      }));
    }
  };

  const pollStatus = async (analysisId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/analyze/${analysisId}/status`);
        const { status, progress } = response.data;

        if (status === 'completed') {
          clearInterval(pollInterval);
          fetchResults(analysisId);
        } else if (status === 'failed') {
          clearInterval(pollInterval);
          setAnalysis(prev => ({
            ...prev,
            status: 'failed',
            error: 'Analysis failed',
          }));
        } else {
          setAnalysis(prev => ({
            ...prev,
            progress: progress.percentage || prev.progress,
          }));
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    }, 2000);

    // Clear interval after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const fetchResults = async (analysisId?: string) => {
    const id = analysisId || analysis.id;
    if (!id) return;

    try {
      const response = await axios.get(`${API_URL}/api/v1/analyze/${id}/result`);
      setAnalysis(prev => ({
        ...prev,
        status: 'completed',
        progress: 100,
        results: response.data,
      }));
      message.success('Analysis completed successfully!');
    } catch (error: any) {
      console.error('Error fetching results:', error);
      if (error.response?.status === 202) {
        // Still processing
        setTimeout(() => fetchResults(id), 2000);
      } else {
        message.error('Failed to fetch results');
      }
    }
  };

  const handleReset = () => {
    setAnalysis({
      id: null,
      status: 'idle',
      progress: 0,
      currentPhase: '',
      results: null,
      error: null,
    });
    form.resetFields();
    if (ws) {
      ws.close();
    }
  };

  const handleExport = () => {
    if (analysis.results) {
      const dataStr = JSON.stringify(analysis.results, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
      const exportFileDefaultName = `stock_analysis_${analysis.id}.json`;

      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
      message.success('Analysis exported successfully');
    }
  };

  const getStatusIcon = () => {
    switch (analysis.status) {
      case 'processing':
        return <LoadingOutlined style={{ fontSize: 24 }} spin />;
      case 'completed':
        return <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />;
      case 'failed':
        return <WarningOutlined style={{ fontSize: 24, color: '#f5222d' }} />;
      default:
        return <ClockCircleOutlined style={{ fontSize: 24 }} />;
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Query Input Section */}
      {analysis.status === 'idle' && (
        <Card title={<Title level={3}>📊 Start Your Stock Analysis</Title>}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ priority: 'normal' }}
          >
            <Form.Item
              name="query"
              label="Investment Question"
              rules={[{ required: true, message: 'Please enter your investment question' }]}
            >
              <TextArea
                rows={4}
                placeholder="Enter your stock analysis question (e.g., 'Should I invest in Apple stock?')"
                maxLength={500}
                showCount
              />
            </Form.Item>

            <Form.Item name="priority" label="Analysis Priority">
              <Radio.Group>
                <Radio value="normal">Normal</Radio>
                <Radio value="high">High Priority</Radio>
              </Radio.Group>
            </Form.Item>

            <Space wrap style={{ marginBottom: 16 }}>
              <Text strong>Sample questions:</Text>
              {sampleQueries.map((query, index) => (
                <Tag
                  key={index}
                  style={{ cursor: 'pointer' }}
                  onClick={() => form.setFieldsValue({ query })}
                >
                  {query}
                </Tag>
              ))}
            </Space>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SearchOutlined />}
                size="large"
                block
              >
                Start Stock Analysis
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}

      {/* Processing Section */}
      {(analysis.status === 'submitting' || analysis.status === 'processing') && (
        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div style={{ textAlign: 'center' }}>
              {getStatusIcon()}
              <Title level={4} style={{ marginTop: 16 }}>
                {analysis.currentPhase || 'Analyzing...'}
              </Title>
            </div>

            <Progress
              percent={analysis.progress}
              status="active"
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />

            <AgentProgress analysisId={analysis.id} />

            <Alert
              message="Analysis in Progress"
              description="Our AI agents are analyzing market data, fundamentals, sentiment, and more to provide you with comprehensive investment insights."
              type="info"
              showIcon
            />
          </Space>
        </Card>
      )}

      {/* Results Section */}
      {analysis.status === 'completed' && analysis.results && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Card
            title={
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <span>Analysis Complete</span>
              </Space>
            }
            extra={
              <Space>
                <Button icon={<ExportOutlined />} onClick={handleExport}>
                  Export
                </Button>
                <Button type="primary" onClick={handleReset}>
                  New Analysis
                </Button>
              </Space>
            }
          >
            <AnalysisResults results={analysis.results} />
          </Card>
        </Space>
      )}

      {/* Error Section */}
      {analysis.status === 'failed' && (
        <Card>
          <Alert
            message="Analysis Failed"
            description={analysis.error || 'An unexpected error occurred during analysis'}
            type="error"
            showIcon
            action={
              <Button size="small" danger onClick={handleReset}>
                Try Again
              </Button>
            }
          />
        </Card>
      )}
    </div>
  );
};

export default StockAnalysis;