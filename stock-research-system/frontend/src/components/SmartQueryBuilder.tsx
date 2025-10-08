import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  Input,
  AutoComplete,
  Button,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Collapse,
  Select,
  Slider,
  Switch,
  Badge,
  Alert,
  Typography,
  Divider,
  Spin,
  message,
} from 'antd';
import {
  SearchOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  QuestionCircleOutlined,
  RocketOutlined,
  SettingOutlined,
  StarOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  LineChartOutlined,
  FundProjectionScreenOutlined,
  SafetyOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { debounce } from 'lodash';
import './GlassCard.css';

const { Panel } = Collapse;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

interface QueryTemplate {
  id: string;
  name: string;
  template: string;
  description: string;
  category: string;
  icon?: React.ReactNode;
}

interface QuerySuggestion {
  type: 'stock' | 'query' | 'template';
  value: string;
  display: string;
  query: string;
}

interface ParsedQuery {
  original_query: string;
  enhanced_query: string;
  intent: string;
  confidence: number;
  extracted_entities: {
    symbols: string[];
    timeframe: string | null;
    comparison_mode: boolean;
    sectors: string[];
    analysis_types: string[];
  };
  suggested_params: any;
  follow_up_suggestions: string[];
  tavily_apis_needed: string[];
}

interface SmartQueryBuilderProps {
  onSubmit: (query: string, params: any) => void;
  loading?: boolean;
}

const SmartQueryBuilder: React.FC<SmartQueryBuilderProps> = ({ onSubmit, loading = false }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<QuerySuggestion[]>([]);
  const [parsedQuery, setParsedQuery] = useState<ParsedQuery | null>(null);
  const [templates, setTemplates] = useState<QueryTemplate[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [expertiseLevel, setExpertiseLevel] = useState<'beginner' | 'intermediate' | 'expert'>('intermediate');
  const [validationResult, setValidationResult] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const inputRef = useRef<any>(null);

  // Questionnaire state
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [questionnaireStep, setQuestionnaireStep] = useState(0);
  const [questionnaireAnswers, setQuestionnaireAnswers] = useState<Record<string, any>>({});

  // Advanced settings
  const [advancedSettings, setAdvancedSettings] = useState({
    timeframe: '1y',
    depth: 'standard',
    includeTechnical: true,
    includeFundamental: true,
    includeSentiment: true,
    includeNews: true,
    riskAssessment: true,
    maxRevisions: 3,
  });

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/query/templates');
      const templatesWithIcons = response.data.map((t: QueryTemplate) => ({
        ...t,
        icon: getCategoryIcon(t.category),
      }));
      setTemplates(templatesWithIcons);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, React.ReactNode> = {
      analysis: <LineChartOutlined />,
      comparison: <BarChartOutlined />,
      screening: <FundProjectionScreenOutlined />,
      risk: <SafetyOutlined />,
      technical: <LineChartOutlined />,
      income: <StarOutlined />,
      events: <ClockCircleOutlined />,
    };
    return icons[category] || <BulbOutlined />;
  };

  // Debounced auto-suggestions
  const fetchSuggestions = useCallback(
    debounce(async (value: string) => {
      if (value.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        const response = await axios.get(`http://localhost:8000/api/query/suggest?q=${value}`);
        setSuggestions(response.data.suggestions);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
      }
    }, 300),
    []
  );

  // Parse query in real-time
  const parseQuery = useCallback(
    debounce(async (value: string) => {
      if (value.length < 3) {
        setParsedQuery(null);
        return;
      }

      setIsParsing(true);
      try {
        const response = await axios.post('http://localhost:8000/api/query/parse', {
          query: value,
        });
        setParsedQuery(response.data);
      } catch (error) {
        console.error('Failed to parse query:', error);
      } finally {
        setIsParsing(false);
      }
    }, 500),
    []
  );

  // Validate query before submission
  const validateQuery = async (value: string) => {
    setIsValidating(true);
    try {
      const response = await axios.get(`http://localhost:8000/api/query/validate?q=${value}`);
      setValidationResult(response.data);
      return response.data.is_valid;
    } catch (error) {
      console.error('Failed to validate query:', error);
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    fetchSuggestions(value);
    parseQuery(value);
  };

  const handleTemplateClick = (template: QueryTemplate) => {
    // For demo, just use the template as is
    setQuery(template.template);
    parseQuery(template.template);
    message.info(`Selected template: ${template.name}`);
  };

  const handleSubmit = async () => {
    if (!query.trim()) {
      message.warning('Please enter a query');
      return;
    }

    const isValid = await validateQuery(query);
    if (!isValid && validationResult?.issues?.length > 0) {
      message.error(validationResult.issues[0]);
      return;
    }

    // Combine query with parsed params and advanced settings
    const finalParams = {
      ...advancedSettings,
      ...(parsedQuery?.suggested_params || {}),
      expertise_level: expertiseLevel,
      tavily_apis: parsedQuery?.tavily_apis_needed || ['search'],
    };

    onSubmit(parsedQuery?.enhanced_query || query, finalParams);
  };

  const renderQuickTemplates = () => (
    <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
      <Col span={24}>
        <Text type="secondary">Quick Actions:</Text>
      </Col>
      {templates.slice(0, 4).map((template) => (
        <Col key={template.id}>
          <Button
            size="small"
            icon={template.icon}
            onClick={() => handleTemplateClick(template)}
            style={{ borderRadius: 16 }}
          >
            {template.name}
          </Button>
        </Col>
      ))}
    </Row>
  );

  const renderQueryInsights = () => {
    if (!parsedQuery) return null;

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="query-insights"
        style={{ marginTop: 12 }}
      >
        <Space wrap>
          <Tag icon={<BulbOutlined />} color="gold">
            Intent: {parsedQuery.intent}
          </Tag>
          <Tag color={parsedQuery.confidence > 0.7 ? 'green' : 'orange'}>
            Confidence: {(parsedQuery.confidence * 100).toFixed(0)}%
          </Tag>
          {parsedQuery.extracted_entities.symbols.map((symbol) => (
            <Tag key={symbol} color="blue">
              ${symbol}
            </Tag>
          ))}
          {parsedQuery.extracted_entities.comparison_mode && (
            <Tag icon={<BarChartOutlined />} color="purple">
              Comparison Mode
            </Tag>
          )}
        </Space>

        {/* Show which Tavily APIs will be used */}
        <div style={{ marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Tavily APIs to use:
          </Text>
          <Space wrap style={{ marginTop: 4 }}>
            {parsedQuery.tavily_apis_needed.map((api) => (
              <Badge key={api} status="processing" text={api.toUpperCase()} />
            ))}
          </Space>
        </div>
      </motion.div>
    );
  };

  const renderAdvancedOptions = () => (
    <Collapse
      ghost
      activeKey={showAdvanced ? ['1'] : []}
      onChange={(keys) => setShowAdvanced(keys.includes('1'))}
    >
      <Panel
        header={
          <Space>
            <SettingOutlined />
            Advanced Options
            <Tag color="blue">{expertiseLevel}</Tag>
          </Space>
        }
        key="1"
      >
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Text type="secondary">Expertise Level</Text>
            <Select
              value={expertiseLevel}
              onChange={setExpertiseLevel}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="beginner">
                <Space>
                  <StarOutlined />
                  Beginner
                </Space>
              </Option>
              <Option value="intermediate">
                <Space>
                  <ThunderboltOutlined />
                  Intermediate
                </Space>
              </Option>
              <Option value="expert">
                <Space>
                  <RocketOutlined />
                  Expert
                </Space>
              </Option>
            </Select>
          </Col>

          <Col span={8}>
            <Text type="secondary">Analysis Timeframe</Text>
            <Select
              value={advancedSettings.timeframe}
              onChange={(value) => setAdvancedSettings({ ...advancedSettings, timeframe: value })}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="1w">1 Week</Option>
              <Option value="1m">1 Month</Option>
              <Option value="3m">3 Months</Option>
              <Option value="ytd">Year to Date</Option>
              <Option value="1y">1 Year</Option>
              <Option value="3y">3 Years</Option>
              <Option value="5y">5 Years</Option>
            </Select>
          </Col>

          <Col span={8}>
            <Text type="secondary">Analysis Depth</Text>
            <Select
              value={advancedSettings.depth}
              onChange={(value) => setAdvancedSettings({ ...advancedSettings, depth: value })}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="quick">Quick (1-2 min)</Option>
              <Option value="standard">Standard (3-5 min)</Option>
              <Option value="deep">Deep (5-10 min)</Option>
              <Option value="research">Research (10+ min)</Option>
            </Select>
          </Col>
        </Row>

        <Divider />

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">Include in Analysis</Text>
              <Space wrap>
                <Switch
                  checked={advancedSettings.includeTechnical}
                  onChange={(checked) =>
                    setAdvancedSettings({ ...advancedSettings, includeTechnical: checked })
                  }
                  checkedChildren="Technical"
                  unCheckedChildren="Technical"
                />
                <Switch
                  checked={advancedSettings.includeFundamental}
                  onChange={(checked) =>
                    setAdvancedSettings({ ...advancedSettings, includeFundamental: checked })
                  }
                  checkedChildren="Fundamental"
                  unCheckedChildren="Fundamental"
                />
                <Switch
                  checked={advancedSettings.includeSentiment}
                  onChange={(checked) =>
                    setAdvancedSettings({ ...advancedSettings, includeSentiment: checked })
                  }
                  checkedChildren="Sentiment"
                  unCheckedChildren="Sentiment"
                />
                <Switch
                  checked={advancedSettings.includeNews}
                  onChange={(checked) =>
                    setAdvancedSettings({ ...advancedSettings, includeNews: checked })
                  }
                  checkedChildren="News"
                  unCheckedChildren="News"
                />
              </Space>
            </Space>
          </Col>

          <Col span={12}>
            <Text type="secondary">Max Analysis Iterations</Text>
            <Slider
              min={1}
              max={5}
              value={advancedSettings.maxRevisions}
              onChange={(value) => setAdvancedSettings({ ...advancedSettings, maxRevisions: value })}
              marks={{
                1: '1',
                2: '2',
                3: '3',
                4: '4',
                5: '5',
              }}
            />
          </Col>
        </Row>
      </Panel>
    </Collapse>
  );

  const renderValidationFeedback = () => {
    if (!validationResult) return null;

    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          {validationResult.warnings?.map((warning: string, idx: number) => (
            <Alert
              key={idx}
              message={warning}
              type="warning"
              showIcon
              style={{ marginTop: 8 }}
              closable
            />
          ))}
          {validationResult.issues?.map((issue: string, idx: number) => (
            <Alert
              key={idx}
              message={issue}
              type="error"
              showIcon
              style={{ marginTop: 8 }}
              closable
            />
          ))}
        </motion.div>
      </AnimatePresence>
    );
  };

  const renderFollowUpSuggestions = () => {
    if (!parsedQuery?.follow_up_suggestions?.length) return null;

    return (
      <div style={{ marginTop: 16 }}>
        <Text type="secondary">You might also want to ask:</Text>
        <Space wrap style={{ marginTop: 8 }}>
          {parsedQuery.follow_up_suggestions.map((suggestion, idx) => (
            <Tag
              key={idx}
              style={{ cursor: 'pointer' }}
              onClick={() => setQuery(suggestion)}
              color="blue"
            >
              {suggestion}
            </Tag>
          ))}
        </Space>
      </div>
    );
  };

  return (
    <Card
      className="glass-card"
      style={{ marginBottom: 24 }}
      title={
        <Space>
          <SearchOutlined />
          <span>Smart Query Builder</span>
          {isParsing && <Spin size="small" />}
        </Space>
      }
      extra={
        <Tooltip title="AI-powered query understanding">
          <Badge status="processing" text="AI Enhanced" />
        </Tooltip>
      }
    >
      {renderQuickTemplates()}

      <AutoComplete
        ref={inputRef}
        value={query}
        onChange={handleQueryChange}
        options={suggestions.map((s) => ({
          value: s.query,
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{s.display}</span>
              <Tag color={s.type === 'stock' ? 'blue' : 'green'} style={{ fontSize: 10 }}>
                {s.type}
              </Tag>
            </div>
          ),
        }))}
        style={{ width: '100%' }}
      >
        <Input.Search
          size="large"
          placeholder="Ask anything about stocks... (e.g., 'Compare AAPL vs GOOGL' or 'Find undervalued tech stocks')"
          enterButton={
            <Button
              type="primary"
              icon={<RocketOutlined />}
              loading={loading || isValidating}
            >
              Analyze
            </Button>
          }
          onSearch={handleSubmit}
        />
      </AutoComplete>

      {renderQueryInsights()}
      {renderValidationFeedback()}
      {renderAdvancedOptions()}
      {renderFollowUpSuggestions()}
    </Card>
  );
};

export default SmartQueryBuilder;