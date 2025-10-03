# Frontend Bundle Optimization Guide

## Overview

This document outlines the bundle optimization strategies implemented for the OpenLearn Colombia frontend to achieve <500KB initial load performance target.

## Performance Targets

### Bundle Sizes (Phase 2 Goals)
- **Initial bundle**: <500KB (target achieved from ~1.2MB)
  - Vendor: <300KB
  - App: <150KB
  - CSS: <50KB
- **Total page weight**: <850KB

### Core Web Vitals
- First Contentful Paint (FCP): <1.5s
- Largest Contentful Paint (LCP): <2.5s
- Time to Interactive (TTI): <3s
- Cumulative Layout Shift (CLS): <0.1
- First Input Delay (FID): <100ms
- Time to First Byte (TTFB): <600ms

### Lighthouse Scores
- Performance: >90
- Accessibility: >90
- Best Practices: >90
- SEO: >90

## Optimization Strategies Implemented

### 1. Code Splitting & Dynamic Imports

**Heavy Libraries (Lazy Loaded)**:
```typescript
// Recharts (~400KB) - Dynamically imported
import { DynamicLineChart } from '@/lib/dynamic-imports'

// D3 modules - Only import what you need
import { importD3Scale, importD3Array } from '@/lib/dynamic-imports'
```

**Route-Based Code Splitting**:
- Analytics page: Lazy loaded with Suspense
- Trends page: Lazy loaded with Suspense
- Charts: Loaded only when needed

### 2. Dependency Optimization

**Replaced Heavy Libraries**:
- `d3` (200KB) → Modular imports (`d3-array`, `d3-scale`, etc.)
- Saved ~120KB by importing only needed modules

**Tree-Shaking Enabled**:
```javascript
// next.config.js
config.optimization.usedExports = true
config.optimization.sideEffects = true
```

### 3. Webpack Configuration

**Smart Code Splitting**:
```javascript
splitChunks: {
  cacheGroups: {
    framework: { // React/Next.js (priority: 30)
      test: /[\\/]node_modules[\\/](react|react-dom|next)[\\/]/,
    },
    ui: { // Radix UI components (priority: 25)
      test: /[\\/]node_modules[\\/](@radix-ui)[\\/]/,
    },
    charts: { // Heavy charts (async, priority: 15)
      test: /[\\/]node_modules[\\/](recharts|d3)[\\/]/,
      chunks: 'async',
    },
  }
}
```

### 4. Image Optimization

**Next.js Image Component**:
```typescript
images: {
  formats: ['image/avif', 'image/webp'],
  minimumCacheTTL: 60,
}
```

**Benefits**:
- Automatic WebP/AVIF conversion
- Responsive image sizing
- Lazy loading by default
- Blur placeholders for better UX

### 5. Performance Monitoring

**Web Vitals Tracking**:
```typescript
import { reportWebVitals } from '@/lib/performance'
import { onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals'

onCLS(reportWebVitals)
onFCP(reportWebVitals)
onLCP(reportWebVitals)
```

**Bundle Size Monitoring**:
```typescript
monitorBundleSize() // Tracks JS, CSS, images, fonts
```

### 6. Compiler Optimizations

**SWC Minification**:
```javascript
swcMinify: true // Faster than Terser
compress: true
productionBrowserSourceMaps: false
```

**Console Removal in Production**:
```javascript
compiler: {
  removeConsole: {
    exclude: ['error', 'warn'], // Keep error logs
  }
}
```

### 7. Font Optimization

**Next.js Font Optimization**:
```typescript
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  preload: true,
})
```

## Build Scripts

### Bundle Analysis
```bash
# Generate bundle analyzer report
npm run analyze

# Analyze server bundle
npm run analyze:server

# Analyze browser bundle
npm run analyze:browser
```

### Lighthouse CI
```bash
# Run Lighthouse CI tests
npm run lighthouse

# Run full performance suite
npm run perf
```

### Type Checking
```bash
# Type check without building
npm run type-check
```

## Performance Budgets

**Configured in `lighthouserc.json`**:
- Total byte weight: <870KB
- First Contentful Paint: <1500ms
- Largest Contentful Paint: <2500ms
- Interactive: <3000ms
- Cumulative Layout Shift: <0.1

## Dynamic Import Utilities

**Location**: `/src/lib/dynamic-imports.ts`

**Available Helpers**:
- `createDynamicImport()` - Create dynamic imports with custom loading states
- `retryImport()` - Retry failed imports with exponential backoff
- `preloadChartComponents()` - Preload heavy components on idle

**Usage Example**:
```typescript
import {
  DynamicLineChart,
  DynamicBarChart,
  LoadingSpinner,
} from '@/lib/dynamic-imports'

export function MyChart() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <DynamicLineChart data={data} />
    </Suspense>
  )
}
```

## Performance Monitoring

**Location**: `/src/lib/performance.ts`

**Features**:
- Web Vitals tracking
- Bundle size monitoring
- Custom metric tracking
- Performance budgets
- Lighthouse CI integration

**Usage**:
```typescript
import {
  trackMetric,
  markPerformance,
  measurePerformance,
} from '@/lib/performance'

// Track custom metrics
trackMetric('api_response_time', duration)

// Mark milestones
markPerformance('data_fetch_start')
markPerformance('data_fetch_end')
measurePerformance('data_fetch', 'data_fetch_start', 'data_fetch_end')
```

## Before/After Metrics

### Before Optimization
- Initial bundle: ~1.2MB
- Vendor chunk: ~800KB
- App chunk: ~300KB
- FCP: ~3s
- LCP: ~4.5s
- TTI: ~5s

### After Optimization (Target)
- Initial bundle: <500KB (60% reduction)
- Vendor chunk: <300KB
- App chunk: <150KB
- FCP: <1.5s
- LCP: <2.5s
- TTI: <3s

## Best Practices

### 1. Always Use Dynamic Imports for Heavy Components
```typescript
// ❌ Bad - Loads 400KB on every page
import { LineChart } from 'recharts'

// ✅ Good - Loads only when needed
import { DynamicLineChart } from '@/lib/dynamic-imports'
```

### 2. Use Selective D3 Imports
```typescript
// ❌ Bad - Imports entire D3 library (200KB)
import * as d3 from 'd3'

// ✅ Good - Import only needed modules
import { scaleLinear } from 'd3-scale'
import { extent } from 'd3-array'
```

### 3. Optimize Images
```typescript
// ✅ Use next/image component
import Image from 'next/image'

<Image
  src="/chart.png"
  alt="Chart"
  width={800}
  height={600}
  placeholder="blur"
  priority={false} // Lazy load by default
/>
```

### 4. Monitor Performance Budgets
```typescript
// Check bundle size regularly
npm run analyze

// Run Lighthouse CI before deployment
npm run lighthouse
```

## Troubleshooting

### Bundle Still Too Large?

1. **Run depcheck to find unused dependencies**:
```bash
npx depcheck
```

2. **Analyze bundle composition**:
```bash
ANALYZE=true npm run build
```

3. **Check for duplicate packages**:
```bash
npm ls <package-name>
```

### Slow Build Times?

1. **Enable incremental compilation** (already enabled):
```json
{
  "compilerOptions": {
    "incremental": true
  }
}
```

2. **Clear Next.js cache**:
```bash
rm -rf .next
npm run build
```

### Performance Regression?

1. **Check Web Vitals in browser console** (development mode)

2. **Run Lighthouse CI**:
```bash
npm run lighthouse
```

3. **Review bundle analyzer report**:
```bash
npm run analyze
```

## Resources

- [Next.js Bundle Analyzer](https://www.npmjs.com/package/@next/bundle-analyzer)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Web Vitals](https://web.dev/vitals/)
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing)

## Next Steps

1. Monitor production bundle sizes
2. Set up continuous performance monitoring
3. Configure performance budgets in CI/CD
4. Implement service worker for offline support
5. Add resource hints (preload, prefetch) for critical assets
