import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Spin, Alert, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import DeepAnalysis from './DeepAnalysis';
import { theme } from '../styles/theme';

const AnalysisPage: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [symbol, setSymbol] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysisData = async () => {
      if (!analysisId) {
        setError('No analysis ID provided');
        setLoading(false);
        return;
      }

      try {
        // Fetch analysis data to get the symbol
        const response = await fetch(`http://localhost:8000/api/v1/analyze/${analysisId}/result`);

        if (!response.ok) {
          throw new Error('Failed to fetch analysis data');
        }

        const data = await response.json();
        const extractedSymbol = data.symbols?.[0] || data.symbol || 'UNKNOWN';
        setSymbol(extractedSymbol);
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching analysis:', err);
        setError(err.message || 'Failed to load analysis');
        setLoading(false);
      }
    };

    fetchAnalysisData();
  }, [analysisId]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: theme.colors.background.primary
      }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: theme.colors.background.primary,
        padding: 24
      }}>
        <Alert
          message="Error Loading Analysis"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => navigate('/')}>
              Go Home
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: theme.colors.background.primary,
      position: 'relative'
    }}>
      {/* Back button */}
      <div style={{
        position: 'fixed',
        top: 24,
        left: 24,
        zIndex: 1001
      }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          style={{
            background: theme.colors.background.elevated,
            border: `1px solid ${theme.colors.border}`,
            color: theme.colors.text.primary
          }}
        >
          Back to Dashboard
        </Button>
      </div>

      {/* Deep Analysis Component */}
      <div style={{ paddingTop: 80 }}>
        <DeepAnalysis
          symbol={symbol}
          onClose={() => navigate('/')}
        />
      </div>
    </div>
  );
};

export default AnalysisPage;
