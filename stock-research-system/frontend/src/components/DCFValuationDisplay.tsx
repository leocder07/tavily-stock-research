/**
 * DCF Valuation Analysis Display Component
 * Shows DCF intrinsic value, margin of safety, and scenario analysis
 */

import React from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Descriptions, Table, Space, Tooltip } from 'antd';
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface ValuationData {
  symbol: string;
  intrinsic_value: number;
  current_price: number;
  margin_of_safety: number;
  rating: 'UNDERVALUED' | 'FAIRLY_VALUED' | 'OVERVALUED';
  dcf_model: {
    enterprise_value: number;
    equity_value: number;
    shares_outstanding: number;
    discount_rate: number;
  };
  relative_valuation: {
    pe_ratio: number;
    sector_pe: number;
    pb_ratio: number;
    sector_pb: number;
  };
  scenarios: {
    bull_case: { value: number; probability: number };
    base_case: { value: number; probability: number };
    bear_case: { value: number; probability: number };
    weighted_fair_value: number;
  };
  confidence_score: number;
}

interface DCFValuationDisplayProps {
  data: Record<string, ValuationData>;
}

const DCFValuationDisplay: React.FC<DCFValuationDisplayProps> = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card title="DCF Valuation Analysis">
        <p>No valuation data available</p>
      </Card>
    );
  }

  const getValuationColor = (rating: string) => {
    switch (rating) {
      case 'UNDERVALUED':
        return 'green';
      case 'FAIRLY_VALUED':
        return 'blue';
      case 'OVERVALUED':
        return 'red';
      default:
        return 'default';
    }
  };

  const getMOSStatus = (mos: number) => {
    if (mos >= 30) return 'success';
    if (mos >= 15) return 'normal';
    return 'exception';
  };

  const scenarioColumns: ColumnsType<any> = [
    {
      title: 'Scenario',
      dataIndex: 'scenario',
      key: 'scenario',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Fair Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      title: 'Probability',
      dataIndex: 'probability',
      key: 'probability',
      render: (prob: number) => `${(prob * 100).toFixed(0)}%`,
    },
    {
      title: 'Upside/Downside',
      dataIndex: 'upside',
      key: 'upside',
      render: (upside: number) => (
        <Tag color={upside >= 0 ? 'green' : 'red'} icon={upside >= 0 ? <RiseOutlined /> : <FallOutlined />}>
          {upside >= 0 ? '+' : ''}{upside.toFixed(1)}%
        </Tag>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {Object.entries(data).map(([symbol, valuation]) => {
        const scenarioData = [
          {
            key: 'bull',
            scenario: 'Bull Case',
            value: valuation.scenarios.bull_case.value,
            probability: valuation.scenarios.bull_case.probability,
            upside: ((valuation.scenarios.bull_case.value - valuation.current_price) / valuation.current_price) * 100,
          },
          {
            key: 'base',
            scenario: 'Base Case',
            value: valuation.scenarios.base_case.value,
            probability: valuation.scenarios.base_case.probability,
            upside: ((valuation.scenarios.base_case.value - valuation.current_price) / valuation.current_price) * 100,
          },
          {
            key: 'bear',
            scenario: 'Bear Case',
            value: valuation.scenarios.bear_case.value,
            probability: valuation.scenarios.bear_case.probability,
            upside: ((valuation.scenarios.bear_case.value - valuation.current_price) / valuation.current_price) * 100,
          },
        ];

        return (
          <Card
            key={symbol}
            title={
              <Space>
                <DollarOutlined />
                {`${symbol} - DCF Valuation Analysis`}
                <Tag color={getValuationColor(valuation.rating)}>{valuation.rating}</Tag>
              </Space>
            }
            extra={
              <Tooltip title="Model confidence based on data quality">
                <Tag icon={<InfoCircleOutlined />} color="blue">
                  Confidence: {(valuation.confidence_score * 100).toFixed(0)}%
                </Tag>
              </Tooltip>
            }
          >
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic
                  title="Intrinsic Value"
                  value={valuation.intrinsic_value}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Current Price"
                  value={valuation.current_price}
                  precision={2}
                  prefix="$"
                />
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Margin of Safety"
                    value={valuation.margin_of_safety}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: valuation.margin_of_safety >= 20 ? '#3f8600' : '#cf1322' }}
                  />
                  <Progress
                    percent={Math.min(valuation.margin_of_safety, 100)}
                    status={getMOSStatus(valuation.margin_of_safety)}
                    showInfo={false}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Statistic
                  title="Weighted Fair Value"
                  value={valuation.scenarios.weighted_fair_value}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>

            <Card type="inner" title="DCF Model" size="small" style={{ marginBottom: 16 }}>
              <Descriptions size="small" column={2}>
                <Descriptions.Item label="Enterprise Value">
                  ${(valuation.dcf_model.enterprise_value / 1e9).toFixed(2)}B
                </Descriptions.Item>
                <Descriptions.Item label="Equity Value">
                  ${(valuation.dcf_model.equity_value / 1e9).toFixed(2)}B
                </Descriptions.Item>
                <Descriptions.Item label="Shares Outstanding">
                  {(valuation.dcf_model.shares_outstanding / 1e6).toFixed(1)}M
                </Descriptions.Item>
                <Descriptions.Item label="Discount Rate (WACC)">
                  {(valuation.dcf_model.discount_rate * 100).toFixed(1)}%
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card type="inner" title="Relative Valuation" size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="P/E Ratio"
                    value={valuation.relative_valuation.pe_ratio}
                    precision={1}
                    suffix={
                      <span style={{ fontSize: 12, color: '#666' }}>
                        (Sector: {valuation.relative_valuation.sector_pe.toFixed(1)})
                      </span>
                    }
                    valueStyle={{
                      color: valuation.relative_valuation.pe_ratio < valuation.relative_valuation.sector_pe
                        ? '#3f8600'
                        : '#cf1322',
                    }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="P/B Ratio"
                    value={valuation.relative_valuation.pb_ratio}
                    precision={2}
                    suffix={
                      <span style={{ fontSize: 12, color: '#666' }}>
                        (Sector: {valuation.relative_valuation.sector_pb.toFixed(2)})
                      </span>
                    }
                    valueStyle={{
                      color: valuation.relative_valuation.pb_ratio < valuation.relative_valuation.sector_pb
                        ? '#3f8600'
                        : '#cf1322',
                    }}
                  />
                </Col>
              </Row>
            </Card>

            <Card type="inner" title="Scenario Analysis" size="small">
              <Table
                columns={scenarioColumns}
                dataSource={scenarioData}
                pagination={false}
                size="small"
              />
              <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
                <Space>
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                  <span>
                    <strong>Weighted Fair Value: ${valuation.scenarios.weighted_fair_value.toFixed(2)}</strong>
                    {' '}(
                    {valuation.scenarios.weighted_fair_value > valuation.current_price ? (
                      <span style={{ color: '#3f8600' }}>
                        <RiseOutlined /> {(((valuation.scenarios.weighted_fair_value - valuation.current_price) / valuation.current_price) * 100).toFixed(1)}% upside
                      </span>
                    ) : (
                      <span style={{ color: '#cf1322' }}>
                        <FallOutlined /> {(((valuation.current_price - valuation.scenarios.weighted_fair_value) / valuation.current_price) * 100).toFixed(1)}% overvalued
                      </span>
                    )}
                    )
                  </span>
                </Space>
              </div>
            </Card>
          </Card>
        );
      })}
    </Space>
  );
};

export default DCFValuationDisplay;
