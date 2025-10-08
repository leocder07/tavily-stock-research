# 🎨 TavilyAI Pro - Comprehensive Design System
## Modern Financial Intelligence Platform

---

## 🎯 HEAD OF PRODUCT: Design Philosophy

### Core Principles
1. **Trust Through Transparency** - Show AI reasoning and data sources
2. **Progressive Complexity** - Simple for beginners, powerful for pros
3. **Delightful Intelligence** - AI that feels helpful, not overwhelming
4. **Speed & Performance** - Sub-second responses, instant feedback
5. **Accessibility First** - WCAG AAA compliant, keyboard navigation

### Product Design Goals
- **Reduce Time to Insight**: From 30 minutes → 30 seconds
- **Increase Decision Confidence**: Clear data provenance & AI reasoning
- **Minimize Cognitive Load**: Smart defaults, contextual help
- **Maximize Engagement**: Interactive, gamified learning
- **Enable Collaboration**: Share insights, team workspaces

---

## 🎨 HEAD OF DESIGN: Visual Language

### Design Inspiration
**Primary References:**
- Bloomberg Terminal (data density)
- Stripe Dashboard (clean aesthetics)
- Linear (smooth interactions)
- Raycast (command palette UX)
- TradingView (charting excellence)

---

## 🌈 COLOR THEMES

### 1. **"Midnight Intelligence"** (Default Dark)
```scss
// Professional dark theme inspired by Bloomberg Terminal
$colors-midnight: (
  // Background Layers
  bg-primary: #0A0E1B,      // Deep space blue
  bg-secondary: #101624,     // Slightly lighter
  bg-tertiary: #1A2332,      // Card backgrounds
  bg-elevated: #242B3D,      // Elevated surfaces

  // Brand Colors
  brand-primary: #00D4FF,    // Electric cyan
  brand-secondary: #7C3AED,  // Deep purple
  brand-accent: #FFB800,     // Golden yellow

  // Semantic Colors
  success: #10B981,          // Emerald green
  warning: #F59E0B,          // Amber
  danger: #EF4444,           // Red
  info: #3B82F6,            // Blue

  // Text Hierarchy
  text-primary: #FFFFFF,     // Pure white
  text-secondary: #94A3B8,   // Muted gray
  text-tertiary: #64748B,    // Subtle gray
  text-muted: #475569,       // Very subtle

  // Data Visualization
  chart-1: #00D4FF,          // Cyan
  chart-2: #7C3AED,          // Purple
  chart-3: #10B981,          // Green
  chart-4: #F59E0B,          // Orange
  chart-5: #EC4899,          // Pink
  chart-6: #8B5CF6,          // Violet

  // Interactive States
  hover: rgba(0, 212, 255, 0.1),
  active: rgba(0, 212, 255, 0.2),
  focus: rgba(0, 212, 255, 0.3),

  // Borders
  border-subtle: rgba(255, 255, 255, 0.06),
  border-default: rgba(255, 255, 255, 0.12),
  border-strong: rgba(255, 255, 255, 0.24)
);
```

### 2. **"Arctic Light"** (Premium Light)
```scss
// Clean, professional light theme inspired by Stripe
$colors-arctic: (
  // Background Layers
  bg-primary: #FFFFFF,       // Pure white
  bg-secondary: #FAFBFC,     // Off white
  bg-tertiary: #F6F8FA,      // Light gray
  bg-elevated: #FFFFFF,      // Cards

  // Brand Colors
  brand-primary: #5E2BF7,    // Royal purple
  brand-secondary: #0EA5E9,  // Sky blue
  brand-accent: #F97316,     // Orange

  // Semantic Colors
  success: #22C55E,          // Green
  warning: #EAB308,          // Yellow
  danger: #DC2626,           // Red
  info: #0EA5E9,            // Blue

  // Text Hierarchy
  text-primary: #0F172A,     // Almost black
  text-secondary: #475569,   // Gray
  text-tertiary: #94A3B8,    // Light gray
  text-muted: #CBD5E1,       // Very light

  // Data Visualization (High contrast)
  chart-1: #5E2BF7,          // Purple
  chart-2: #0EA5E9,          // Blue
  chart-3: #22C55E,          // Green
  chart-4: #F97316,          // Orange
  chart-5: #EC4899,          // Pink
  chart-6: #8B5CF6,          // Violet

  // Borders
  border-subtle: #F1F5F9,
  border-default: #E2E8F0,
  border-strong: #CBD5E1
);
```

### 3. **"Terminal Green"** (Hacker Mode)
```scss
// Matrix-inspired theme for power users
$colors-terminal: (
  bg-primary: #000000,
  bg-secondary: #0A0A0A,
  bg-tertiary: #141414,

  brand-primary: #00FF41,    // Matrix green
  brand-secondary: #39FF14,  // Neon green
  brand-accent: #FFFF00,     // Yellow

  text-primary: #00FF41,
  text-secondary: #00CC33,

  chart-1: #00FF41,
  chart-2: #39FF14,
  chart-3: #FFFF00,
  chart-4: #FF00FF,
  chart-5: #00FFFF
);
```

### 4. **"Sunset Trading"** (Warm Professional)
```scss
// Warm, comfortable theme for long sessions
$colors-sunset: (
  bg-primary: #1A1418,
  bg-secondary: #251F24,
  bg-tertiary: #2D2530,

  brand-primary: #FF6B6B,    // Coral
  brand-secondary: #4ECDC4,  // Teal
  brand-accent: #FFE66D,     // Soft yellow

  text-primary: #FFF5F5,
  text-secondary: #FFB8B8
);
```

---

## 🎨 TYPOGRAPHY SYSTEM

### Font Stack
```scss
// Headings - Modern & Bold
$font-display: 'SF Pro Display', 'Inter', -apple-system, system-ui, sans-serif;

// Body - Readable & Clean
$font-body: 'Inter', 'SF Pro Text', -apple-system, system-ui, sans-serif;

// Data - Monospace for numbers
$font-mono: 'JetBrains Mono', 'SF Mono', 'Monaco', monospace;

// Special - For logos and accents
$font-brand: 'Gilroy', 'Montserrat', sans-serif;
```

### Type Scale (8-point Grid)
```scss
$type-scale: (
  // Display
  display-xl: (size: 72px, line: 80px, weight: 800),  // Hero
  display-lg: (size: 56px, line: 64px, weight: 700),  // Page title
  display-md: (size: 48px, line: 56px, weight: 700),  // Section

  // Headings
  h1: (size: 40px, line: 48px, weight: 600),
  h2: (size: 32px, line: 40px, weight: 600),
  h3: (size: 24px, line: 32px, weight: 600),
  h4: (size: 20px, line: 28px, weight: 500),

  // Body
  body-lg: (size: 18px, line: 28px, weight: 400),
  body-md: (size: 16px, line: 24px, weight: 400),     // Default
  body-sm: (size: 14px, line: 20px, weight: 400),

  // UI Elements
  button: (size: 15px, line: 20px, weight: 500),
  label: (size: 13px, line: 16px, weight: 500),
  caption: (size: 12px, line: 16px, weight: 400),

  // Data
  data-lg: (size: 20px, line: 24px, weight: 600),     // Big numbers
  data-md: (size: 16px, line: 20px, weight: 500),     // Regular data
  data-sm: (size: 13px, line: 16px, weight: 400)      // Table data
);
```

---

## 🎯 SPACING & LAYOUT

### Grid System
```scss
// 8-point grid system for consistency
$space: (
  0: 0,
  1: 4px,
  2: 8px,      // Base unit
  3: 12px,
  4: 16px,
  5: 20px,
  6: 24px,
  8: 32px,
  10: 40px,
  12: 48px,
  16: 64px,
  20: 80px,
  24: 96px,
  32: 128px
);

// Container Widths
$containers: (
  xs: 375px,   // Mobile
  sm: 640px,   // Small tablet
  md: 768px,   // Tablet
  lg: 1024px,  // Desktop
  xl: 1280px,  // Wide desktop
  2xl: 1536px, // Ultra-wide
  3xl: 1920px  // Full HD
);
```

---

## 🎨 COMPONENT PATTERNS

### 1. **Glass Morphism Cards**
```scss
.glass-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.1),
    0 4px 6px rgba(0, 0, 0, 0.05),
    0 10px 15px -3px rgba(0, 0, 0, 0.1);

  &:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
    box-shadow:
      0 0 0 1px rgba(0, 0, 0, 0.1),
      0 10px 15px -3px rgba(0, 0, 0, 0.15),
      0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }
}
```

### 2. **Gradient Buttons**
```scss
.btn-gradient {
  background: linear-gradient(135deg, $brand-primary 0%, $brand-secondary 100%);
  color: white;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.05),
    0 2px 4px rgba(0, 0, 0, 0.05),
    0 4px 6px rgba(0, 0, 0, 0.05);

  &:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow:
      0 0 0 1px rgba(0, 0, 0, 0.05),
      0 4px 6px rgba(0, 0, 0, 0.1),
      0 10px 15px rgba(0, 0, 0, 0.1),
      0 0 40px rgba($brand-primary, 0.3);
  }

  &:active {
    transform: translateY(0) scale(0.98);
  }
}
```

### 3. **Neumorphism Elements**
```scss
.neumorphic {
  background: $bg-secondary;
  border-radius: 16px;
  box-shadow:
    inset 2px 2px 5px rgba(0, 0, 0, 0.2),
    inset -2px -2px 5px rgba(255, 255, 255, 0.05),
    5px 5px 10px rgba(0, 0, 0, 0.3),
    -5px -5px 10px rgba(255, 255, 255, 0.03);

  &.pressed {
    box-shadow:
      inset 5px 5px 10px rgba(0, 0, 0, 0.3),
      inset -5px -5px 10px rgba(255, 255, 255, 0.03);
  }
}
```

### 4. **Animated Gradients**
```scss
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.gradient-animated {
  background: linear-gradient(
    -45deg,
    #FF6B6B,
    #4ECDC4,
    #45B7D1,
    #96CEB4
  );
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
}
```

---

## 🎯 INTERACTION PATTERNS

### Micro-interactions
```typescript
// Hover Effects
const hoverVariants = {
  rest: { scale: 1, rotate: 0 },
  hover: {
    scale: 1.05,
    rotate: 1,
    transition: { type: "spring", stiffness: 300 }
  }
};

// Click Feedback
const tapVariants = {
  tap: { scale: 0.95 },
  release: { scale: 1 }
};

// Loading States
const loadingVariants = {
  initial: { opacity: 0.3 },
  animate: {
    opacity: 1,
    transition: {
      repeat: Infinity,
      repeatType: "reverse",
      duration: 0.8
    }
  }
};
```

### Page Transitions
```typescript
const pageTransitions = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: {
    type: "spring",
    damping: 20,
    stiffness: 100
  }
};
```

---

## 📊 DATA VISUALIZATION PALETTE

### Chart Color Schemes

#### **Categorical (Distinct)**
```javascript
const categorical = [
  '#00D4FF', // Cyan
  '#7C3AED', // Purple
  '#10B981', // Green
  '#F59E0B', // Orange
  '#EC4899', // Pink
  '#8B5CF6', // Violet
  '#06B6D4', // Teal
  '#F97316'  // Deep Orange
];
```

#### **Sequential (Gradients)**
```javascript
const sequential = {
  blue: ['#EFF6FF', '#DBEAFE', '#BFDBFE', '#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1D4ED8'],
  green: ['#F0FDF4', '#DCFCE7', '#BBF7D0', '#86EFAC', '#4ADE80', '#22C55E', '#16A34A', '#15803D'],
  red: ['#FEF2F2', '#FEE2E2', '#FECACA', '#FCA5A5', '#F87171', '#EF4444', '#DC2626', '#B91C1C']
};
```

#### **Diverging (Positive/Negative)**
```javascript
const diverging = [
  '#DC2626', // Strong negative
  '#EF4444',
  '#F87171',
  '#FCA5A5',
  '#E5E7EB', // Neutral
  '#86EFAC',
  '#4ADE80',
  '#22C55E',
  '#16A34A'  // Strong positive
];
```

---

## 🎨 ELEVATION & SHADOWS

```scss
$shadows: (
  xs: (0 1px 2px 0 rgba(0, 0, 0, 0.05)),
  sm: (0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)),
  md: (0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)),
  lg: (0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)),
  xl: (0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)),
  2xl: (0 25px 50px -12px rgba(0, 0, 0, 0.25)),
  glow: (0 0 40px rgba($brand-primary, 0.3)),
  inner: (inset 0 2px 4px 0 rgba(0, 0, 0, 0.06))
);
```

---

## 🎯 ACCESSIBILITY

### Color Contrast Ratios
- **Normal Text**: WCAG AAA (7:1)
- **Large Text**: WCAG AA (4.5:1)
- **UI Components**: 3:1 minimum
- **Focus Indicators**: 4.5:1

### Keyboard Navigation
```scss
// Focus Styles
:focus-visible {
  outline: 2px solid $brand-primary;
  outline-offset: 2px;
  border-radius: 4px;
}

// Skip Links
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: $brand-primary;
  color: white;
  padding: 8px;
  z-index: 100;

  &:focus {
    top: 0;
  }
}
```

---

## 🎨 ICONOGRAPHY

### Icon Library
- **Primary**: Lucide Icons (consistent, modern)
- **Secondary**: Tabler Icons (comprehensive)
- **Custom**: Financial symbols, chart types

### Icon Sizes
```scss
$icon-sizes: (
  xs: 12px,
  sm: 16px,
  md: 20px,  // Default
  lg: 24px,
  xl: 32px,
  2xl: 48px
);
```

---

## 📱 RESPONSIVE BREAKPOINTS

```scss
$breakpoints: (
  xs: 0,      // Mobile first
  sm: 640px,  // Large phone
  md: 768px,  // Tablet
  lg: 1024px, // Desktop
  xl: 1280px, // Wide desktop
  2xl: 1536px // Ultra-wide
);

// Usage
@media (min-width: map-get($breakpoints, md)) {
  // Tablet and up styles
}
```

---

## 🎯 MOTION & ANIMATION

### Animation Tokens
```scss
$motion: (
  // Durations
  instant: 0ms,
  fast: 150ms,
  normal: 250ms,
  slow: 350ms,
  slower: 500ms,

  // Easings
  ease-in: cubic-bezier(0.4, 0, 1, 1),
  ease-out: cubic-bezier(0, 0, 0.2, 1),
  ease-in-out: cubic-bezier(0.4, 0, 0.2, 1),
  spring: cubic-bezier(0.68, -0.55, 0.265, 1.55)
);
```

---

## 🎨 ADVANCED EFFECTS

### Glassmorphism Levels
```scss
@mixin glass($level: 1) {
  @if $level == 1 {
    backdrop-filter: blur(8px);
    background: rgba(255, 255, 255, 0.02);
  } @else if $level == 2 {
    backdrop-filter: blur(16px);
    background: rgba(255, 255, 255, 0.04);
  } @else if $level == 3 {
    backdrop-filter: blur(24px);
    background: rgba(255, 255, 255, 0.06);
  }
}
```

### Gradient Mesh Backgrounds
```scss
.gradient-mesh {
  background-image:
    radial-gradient(at 40% 20%, hsla(280, 100%, 70%, 0.3) 0px, transparent 50%),
    radial-gradient(at 80% 0%, hsla(189, 100%, 56%, 0.3) 0px, transparent 50%),
    radial-gradient(at 0% 50%, hsla(355, 100%, 93%, 0.3) 0px, transparent 50%),
    radial-gradient(at 80% 50%, hsla(340, 100%, 76%, 0.3) 0px, transparent 50%),
    radial-gradient(at 0% 100%, hsla(22, 100%, 77%, 0.3) 0px, transparent 50%);
}
```

---

This design system provides a comprehensive foundation for building a modern, professional financial intelligence platform that stands out in the market while maintaining usability and accessibility.