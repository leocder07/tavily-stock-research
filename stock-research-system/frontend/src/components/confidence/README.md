# Confidence Score Visualization System

A comprehensive system for displaying AI analysis confidence scores with clear visual cues, agent breakdowns, and intelligent warnings.

## Overview

The confidence visualization system provides multiple components to display AI confidence scores throughout the application. It uses color coding, animations, and detailed breakdowns to help users understand the reliability of recommendations.

## Components

### 1. ConfidenceMeter

**Purpose**: Primary confidence visualization with a progress bar and visual indicators.

**Features**:
- Color-coded progress bar (Green: >70%, Yellow: 40-70%, Red: <40%)
- Animated icons for high confidence scores
- Customizable size (small, medium, large)
- Tooltip with detailed confidence description
- Vertical or horizontal orientation

**Usage**:
```tsx
import { ConfidenceMeter } from './components/confidence';

<ConfidenceMeter
  confidence={0.85}              // 0-1 or 0-100
  label="AI Confidence"
  size="large"                   // small | medium | large
  showIcon={true}
  showPercentage={true}
  vertical={false}
  animated={true}
/>
```

**Visual Thresholds**:
- **High (≥70%)**: Green with success icon, glowing animation
- **Medium (40-70%)**: Yellow with warning icon
- **Low (<40%)**: Red with danger icon

---

### 2. ConfidenceBadge

**Purpose**: Compact inline badge for displaying confidence in lists and cards.

**Features**:
- Minimal footprint for inline displays
- Hover effects with glow
- Optional pulsing animation for high confidence
- Tooltip with explanation

**Usage**:
```tsx
import { ConfidenceBadge } from './components/confidence';

<ConfidenceBadge
  confidence={0.75}
  size="default"                 // small | default | large
  showIcon={true}
  showLabel={true}
  inline={true}
  pulse={true}                   // Pulse animation for high confidence
/>
```

**Best Practices**:
- Use `size="small"` in compact spaces like table cells
- Enable `pulse` for recommendations with high confidence
- Use `inline={true}` when embedding in text flows

---

### 3. AgentConfidenceBreakdown

**Purpose**: Detailed breakdown showing confidence scores for each analysis agent.

**Features**:
- Individual agent confidence scores
- Consensus statistics (bullish/bearish/neutral indicators)
- Agent agreement level display
- Visual progress bars for each agent
- Low confidence warnings

**Usage**:
```tsx
import { AgentConfidenceBreakdown } from './components/confidence';

<AgentConfidenceBreakdown
  consensusBreakdown={{
    weighted_score: 0.75,
    total_confidence: 0.70,
    bullish_indicators: 3,
    bearish_indicators: 1,
    neutral_indicators: 1
  }}
  agentAgreement="Strong agreement across agents"
  agentScores={[
    { name: 'Fundamental Agent', confidence: 0.80, signal: 'BUY', weight: 0.35 },
    { name: 'Technical Agent', confidence: 0.70, signal: 'HOLD', weight: 0.25 },
    // ... more agents
  ]}
  compact={false}
/>
```

**Agent Types Recognized**:
- Fundamental Agent (Dollar icon)
- Technical Agent (Chart icon)
- Risk Agent (Alert icon)
- Sentiment Agent (Thunderbolt icon)
- Peer Comparison (Team icon)
- Synthesis Agent (Trophy icon)

---

### 4. ConfidenceWarning

**Purpose**: Contextual warnings that appear based on confidence levels.

**Features**:
- Automatic display based on confidence threshold
- Color-coded alerts (success, warning, error)
- Detailed reason lists
- Custom messaging support

**Usage**:
```tsx
import { ConfidenceWarning } from './components/confidence';

<ConfidenceWarning
  confidence={0.35}
  showAlways={false}             // Show even for high confidence
  customMessage="Custom warning text"
  reasons={[
    'Mixed signals from agents',
    'Limited data quality',
    'High market volatility'
  ]}
/>
```

**Display Logic**:
- **High (≥70%)**: Hidden by default (unless `showAlways={true}`)
- **Medium (40-70%)**: Yellow warning with caution message
- **Low (<40%)**: Red error with detailed warnings

---

## Integration with AnalysisResults

The confidence system is integrated into the main `AnalysisResults` component:

### 1. Executive Summary
Displays an inline confidence badge next to the summary title.

### 2. Overall Confidence Section
Shows a large confidence meter with warnings and agent breakdown side-by-side.

### 3. Recommendation Cards
Each stock recommendation card includes:
- Confidence badge in the card header
- Visual dimming for low confidence (<40%)
- Glowing border for high confidence (≥70%)
- Pulsing animation on high-confidence badges

### 4. Confidence-Based UI Behaviors

**Highlighting**:
```tsx
// High confidence recommendations get visual emphasis
style={{
  border: confidence >= 0.7 ? '2px solid rgba(0, 212, 170, 0.3)' : undefined,
  boxShadow: confidence >= 0.7 ? '0 0 20px rgba(0, 212, 170, 0.1)' : undefined,
}}
```

**Dimming**:
```tsx
// Low confidence recommendations are visually subdued
style={{
  opacity: confidence < 0.4 ? 0.7 : 1,
}}
```

## Data Structure

The confidence system expects the following data structure from the backend:

```typescript
interface AnalysisResults {
  confidence_score: number;           // Overall confidence (0-1)
  synthesis_result?: {
    confidence: number;                // Synthesis confidence
    consensus_breakdown?: {
      weighted_score: number;
      total_confidence: number;
      bullish_indicators: number;
      bearish_indicators: number;
      neutral_indicators: number;
    };
    agent_agreement?: string;
  };
  recommendations?: {
    [symbol: string]: {
      confidence?: number;             // Per-recommendation confidence
      action: string;
      conviction: string;
      // ... other fields
    };
  };
}
```

## Color Scheme

Based on the CRED-inspired theme:

- **Success/High Confidence**: `#00D4AA` (Emerald green)
- **Warning/Medium Confidence**: `#FF9F0A` (Orange)
- **Danger/Low Confidence**: `#FF453A` (Vibrant red)
- **Primary Accent**: `#D4AF37` (Gold)

## Confidence Score Mapping

The backend provides confidence scores in the range 0-1, which are mapped to visual elements:

| Backend Value | Percentage | Level | Visual Treatment |
|--------------|------------|-------|------------------|
| 0.85-1.0     | 85-100%    | Very High | Green, glowing, animated |
| 0.70-0.84    | 70-84%     | High   | Green, highlighted |
| 0.55-0.69    | 55-69%     | Moderate | Light yellow |
| 0.40-0.54    | 40-54%     | Medium | Yellow, warning |
| 0.25-0.39    | 25-39%     | Low    | Red, dimmed |
| 0.0-0.24     | 0-24%      | Very Low | Red, strong warning |

## Accessibility

- All components use high-contrast colors
- Tooltips provide text descriptions for screen readers
- Icons are supplemented with text labels
- Color is not the only indicator (icons, text, opacity also used)

## Performance Considerations

- Components use React.memo for optimization where appropriate
- CSS animations use GPU-accelerated properties (transform, opacity)
- Styled-components are scoped to prevent style leakage
- No heavy computations in render methods

## Testing

To view all confidence visualizations:

```tsx
import { ConfidenceShowcase } from './components/confidence';

// Render in a test route or development environment
<ConfidenceShowcase />
```

## Future Enhancements

- [ ] Add historical confidence tracking charts
- [ ] Implement confidence trends over time
- [ ] Add A/B testing for different visualization styles
- [ ] Create confidence comparison between multiple analyses
- [ ] Add confidence score calibration based on historical accuracy

## API Integration

### Backend Agent Confidence Scores

The system extracts agent-specific confidence from:
- `expert_fundamental_agent.py` - Fundamental analysis confidence
- `expert_technical_agent.py` - Technical analysis confidence
- `expert_risk_agent.py` - Risk assessment confidence
- `expert_synthesis_agent.py` - Overall synthesis confidence

### Consensus Calculation

Confidence consensus is calculated in `expert_synthesis_agent.py`:
```python
def _calculate_consensus(self, analyses: Dict) -> Dict:
    # Weighted average of all agent confidences
    # Returns consensus_breakdown with bullish/bearish/neutral indicators
```

## Examples

### Example 1: High Confidence Analysis
```tsx
// When confidence is high (>70%), the system:
// 1. Shows a green glowing meter with animated icon
// 2. Highlights recommendations with green borders
// 3. Displays "High Confidence" badge with pulse animation
// 4. Shows agent breakdown with mostly green bars
// 5. Optionally shows success message (if showAlways=true)
```

### Example 2: Low Confidence Analysis
```tsx
// When confidence is low (<40%), the system:
// 1. Shows a red meter with warning icon
// 2. Dims recommendation cards to 70% opacity
// 3. Displays prominent warning alert
// 4. Shows agent breakdown with conflicting signals
// 5. Lists specific reasons for low confidence
```

## Support

For questions or issues with the confidence visualization system, refer to:
- Main documentation: `/stock-research-system/CLAUDE.md`
- Theme documentation: `/frontend/src/styles/theme.ts`
- Backend agent code: `/backend/agents/expert_agents/`
