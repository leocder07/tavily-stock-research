import React from 'react';

interface SupportResistanceDisplayProps {
  supportLevels?: number[];
  resistanceLevels?: number[];
  currentPrice?: number;
}

export const SupportResistanceDisplay: React.FC<SupportResistanceDisplayProps> = ({
  supportLevels = [],
  resistanceLevels = [],
  currentPrice
}) => {
  if (!supportLevels.length && !resistanceLevels.length) {
    return null;
  }

  // Find nearest levels
  const nearestSupport = supportLevels
    .filter(level => currentPrice ? level < currentPrice : true)
    .sort((a, b) => b - a)[0];

  const nearestResistance = resistanceLevels
    .filter(level => currentPrice ? level > currentPrice : true)
    .sort((a, b) => a - b)[0];

  return (
    <div style={{ marginTop: '24px' }}>
      <h3 style={{ fontSize: '16px', marginBottom: '16px', fontWeight: 600 }}>
        📊 Support & Resistance Levels
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Support Levels */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#10b981' }}>
            🟢 Support Levels
          </h4>
          {supportLevels.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {supportLevels.map((level, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: level === nearestSupport ? '#d1fae5' : '#f3f4f6',
                    borderRadius: '6px',
                    border: level === nearestSupport ? '2px solid #10b981' : '1px solid #e5e7eb',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ fontWeight: level === nearestSupport ? 600 : 400 }}>
                    ${level.toFixed(2)}
                  </span>
                  {level === nearestSupport && (
                    <span style={{ fontSize: '12px', color: '#059669', fontWeight: 500 }}>
                      NEAREST
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#9ca3af', fontSize: '14px' }}>No support levels identified</div>
          )}
        </div>

        {/* Resistance Levels */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#ef4444' }}>
            🔴 Resistance Levels
          </h4>
          {resistanceLevels.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {resistanceLevels.map((level, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '8px 12px',
                    backgroundColor: level === nearestResistance ? '#fee2e2' : '#f3f4f6',
                    borderRadius: '6px',
                    border: level === nearestResistance ? '2px solid #ef4444' : '1px solid #e5e7eb',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ fontWeight: level === nearestResistance ? 600 : 400 }}>
                    ${level.toFixed(2)}
                  </span>
                  {level === nearestResistance && (
                    <span style={{ fontSize: '12px', color: '#dc2626', fontWeight: 500 }}>
                      NEAREST
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#9ca3af', fontSize: '14px' }}>No resistance levels identified</div>
          )}
        </div>
      </div>

      {/* Current Price Position */}
      {currentPrice && (nearestSupport || nearestResistance) && (
        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#eff6ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
          <div style={{ fontSize: '14px', color: '#1e40af' }}>
            <strong>Current Price: ${currentPrice.toFixed(2)}</strong>
            {nearestSupport && (
              <div style={{ marginTop: '4px' }}>
                <span style={{ color: '#059669' }}>
                  ↓ ${(currentPrice - nearestSupport).toFixed(2)} above nearest support
                </span>
              </div>
            )}
            {nearestResistance && (
              <div style={{ marginTop: '4px' }}>
                <span style={{ color: '#dc2626' }}>
                  ↑ ${(nearestResistance - currentPrice).toFixed(2)} below nearest resistance
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SupportResistanceDisplay;
