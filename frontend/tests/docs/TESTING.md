# Frontend Testing Documentation

## Overview

This document provides comprehensive information about the testing setup for the OpenLearn Colombia frontend application.

## Test Stack

### Unit & Integration Testing
- **Jest**: Test runner and framework
- **React Testing Library**: Component testing utilities
- **@swc/jest**: Fast TypeScript/JSX transformation
- **@testing-library/user-event**: User interaction simulation

### End-to-End Testing
- **Playwright**: Cross-browser E2E testing
- Supports Chrome, Firefox, Safari, and mobile browsers

## Running Tests

### Unit & Integration Tests

```bash
# Run all tests
npm test

# Watch mode for development
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run specific test file
npm test -- StatsCard.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="renders correctly"
```

### End-to-End Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug

# Run specific browser
npx playwright test --project=chromium

# Run specific test file
npx playwright test tests/e2e/dashboard.spec.ts
```

### All Tests

```bash
# Run all tests (unit + E2E)
npm run test:all
```

## Test Structure

```
frontend/
├── tests/
│   ├── setup.ts                 # Jest configuration
│   ├── __mocks__/              # Mock files
│   │   ├── styleMock.js
│   │   └── fileMock.js
│   ├── utils/                   # Test utilities
│   │   └── test-utils.tsx
│   ├── fixtures/                # Mock data
│   │   ├── preferences.ts
│   │   ├── articles.ts
│   │   └── dashboard.ts
│   ├── components/              # Component tests
│   │   ├── StatsCard.test.tsx
│   │   ├── Dashboard.test.tsx
│   │   ├── Navbar.test.tsx
│   │   ├── ui/
│   │   │   ├── AvatarUpload.test.tsx
│   │   │   ├── Select.test.tsx
│   │   │   └── FilterTag.test.tsx
│   │   ├── preferences/
│   │   │   └── ProfilePreferences.test.tsx
│   │   ├── filters/
│   │   │   └── FilterPanel.test.tsx
│   │   └── auth/
│   │       └── LoginForm.test.tsx
│   ├── lib/                     # Hook/utility tests
│   │   └── preferences/
│   │       └── use-preferences.test.tsx
│   └── e2e/                     # E2E tests
│       ├── dashboard.spec.ts
│       ├── navigation.spec.ts
│       ├── preferences.spec.ts
│       └── search.spec.ts
```

## Writing Tests

### Component Tests

Use the custom `renderWithProviders` helper to render components with all necessary providers:

```typescript
import { renderWithProviders, screen, userEvent } from '@/tests/utils/test-utils'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    renderWithProviders(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    renderWithProviders(<MyComponent />)
    const button = screen.getByRole('button')
    await userEvent.click(button)
    expect(screen.getByText('Clicked')).toBeInTheDocument()
  })
})
```

### Using Test Fixtures

Import mock data from fixtures for consistent testing:

```typescript
import { mockUserPreferences } from '@/tests/fixtures/preferences'
import { mockArticles } from '@/tests/fixtures/articles'

it('displays user preferences', () => {
  renderWithProviders(<Component preferences={mockUserPreferences} />)
  // ... assertions
})
```

### Testing Async Operations

```typescript
import { waitFor } from '@testing-library/react'

it('loads data asynchronously', async () => {
  renderWithProviders(<AsyncComponent />)

  await waitFor(() => {
    expect(screen.getByText('Loaded Data')).toBeInTheDocument()
  })
})
```

### Testing File Uploads

```typescript
import { createMockFile } from '@/tests/utils/test-utils'

it('handles file upload', async () => {
  renderWithProviders(<UploadComponent />)

  const file = createMockFile('test.png', 1024, 'image/png')
  const input = screen.getByLabelText('Upload')

  await userEvent.upload(input, file)

  expect(mockOnUpload).toHaveBeenCalledWith(file)
})
```

### E2E Tests

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('performs action', async ({ page }) => {
    await page.click('text=Button')
    await expect(page).toHaveURL('/new-page')
  })
})
```

## Coverage Goals

### Current Targets
- **Statements**: 70%
- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%

### Viewing Coverage

```bash
npm run test:coverage
```

Coverage report will be generated in `coverage/` directory. Open `coverage/lcov-report/index.html` in your browser for detailed view.

## Test Utilities

### Custom Render Function

`renderWithProviders()` - Renders components with QueryClient, Auth, and Preferences providers.

### Mock Helpers

- `createMockFile()` - Create mock File objects
- `createMockApiResponse()` - Mock API responses
- `createMockErrorResponse()` - Mock error responses
- `MockFileReader` - Mock FileReader for upload testing

### Test Fixtures

- `mockUserPreferences` - Complete user preferences object
- `mockArticle` - Single article object
- `mockArticles` - Array of articles
- `mockDashboardStats` - Dashboard statistics data

## Mocking

### Mocking Modules

```typescript
jest.mock('@/lib/api/client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}))
```

### Mocking Hooks

```typescript
jest.mock('@/lib/preferences/use-preferences', () => ({
  usePreferences: () => ({
    preferences: mockUserPreferences,
    updateProfile: jest.fn(),
  }),
}))
```

### Mocking Next.js Router

```typescript
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
  }),
  usePathname: () => '/',
}))
```

## Accessibility Testing

Use semantic queries for better accessibility:

```typescript
// ✅ Good - Accessible queries
screen.getByRole('button', { name: 'Submit' })
screen.getByLabelText('Email')
screen.getByText('Welcome')

// ❌ Avoid - Implementation details
screen.getByClassName('btn-submit')
screen.getByTestId('email-input')
```

## Debugging Tests

### Debug Output

```typescript
import { screen } from '@testing-library/react'

screen.debug() // Print entire DOM
screen.debug(element) // Print specific element
```

### Playwright Debug Mode

```bash
npm run test:e2e:debug
```

Opens Playwright Inspector for step-by-step debugging.

## CI/CD Integration

Tests are configured to run in CI with:
- No watch mode
- Coverage reports
- JUnit XML output for CI systems
- HTML reports for artifacts

## Best Practices

1. **Test behavior, not implementation**
   - Focus on what users see and do
   - Avoid testing internal state

2. **Use semantic queries**
   - Prefer `getByRole`, `getByLabelText`
   - Makes tests more accessible

3. **Keep tests isolated**
   - Each test should be independent
   - Use `beforeEach` for setup

4. **Mock external dependencies**
   - API calls
   - Browser APIs
   - Third-party libraries

5. **Test error states**
   - Loading states
   - Error messages
   - Edge cases

6. **Write descriptive test names**
   - Clearly state what is being tested
   - Include expected outcome

## Troubleshooting

### Common Issues

**Tests timeout**
- Increase timeout in jest.config.js
- Check for unresolved promises
- Ensure all async operations complete

**Module resolution errors**
- Check path aliases in jest.config.js
- Verify tsconfig.json paths

**Canvas/Chart errors**
- Mocks are in tests/setup.ts
- HTMLCanvasElement.getContext is mocked

**localStorage errors**
- Mocked in tests/setup.ts
- Clear mocks between tests

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
