# Frontend Testing Quick Start Guide

## Installation

### Install Test Dependencies

```bash
cd frontend
npm install --save-dev \
  jest@^29.7.0 \
  @testing-library/react@^14.1.2 \
  @testing-library/jest-dom@^6.1.5 \
  @testing-library/user-event@^14.5.1 \
  @playwright/test@^1.40.1 \
  @swc/jest@^0.2.29 \
  jest-environment-jsdom@^29.7.0 \
  jest-watch-typeahead@^2.2.2 \
  identity-obj-proxy@^3.0.0 \
  @types/jest@^29.5.11
```

### Install Playwright Browsers

```bash
npx playwright install
```

## Running Tests

### Unit & Integration Tests

```bash
# Run all tests once
npm test

# Watch mode (auto-rerun on file changes)
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run specific test file
npm test -- AvatarUpload.test.tsx

# Run tests matching a pattern
npm test -- --testNamePattern="avatar"
```

### End-to-End Tests

```bash
# Run all E2E tests
npm run test:e2e

# Interactive UI mode (recommended for development)
npm run test:e2e:ui

# Debug mode (step-through)
npm run test:e2e:debug

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run specific test file
npx playwright test tests/e2e/dashboard.spec.ts
```

### Run All Tests

```bash
npm run test:all
```

## Writing Your First Test

### Component Test Example

Create a file: `tests/components/MyComponent.test.tsx`

```typescript
import { renderWithProviders, screen, userEvent } from '@/tests/utils/test-utils'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    renderWithProviders(<MyComponent title="Test" />)

    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('handles click', async () => {
    const mockOnClick = jest.fn()
    renderWithProviders(<MyComponent onClick={mockOnClick} />)

    await userEvent.click(screen.getByRole('button'))

    expect(mockOnClick).toHaveBeenCalledTimes(1)
  })
})
```

### E2E Test Example

Create a file: `tests/e2e/my-feature.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('My Feature', () => {
  test('works correctly', async ({ page }) => {
    await page.goto('/')

    await page.click('text=My Button')

    await expect(page.getByText('Success')).toBeVisible()
  })
})
```

## Common Testing Patterns

### Testing User Input

```typescript
it('handles form input', async () => {
  renderWithProviders(<MyForm />)

  const input = screen.getByLabelText('Name')
  await userEvent.type(input, 'John Doe')

  expect(input).toHaveValue('John Doe')
})
```

### Testing Async Operations

```typescript
it('loads data', async () => {
  renderWithProviders(<AsyncComponent />)

  // Wait for element to appear
  await waitFor(() => {
    expect(screen.getByText('Data Loaded')).toBeInTheDocument()
  })
})
```

### Testing File Upload

```typescript
import { createMockFile } from '@/tests/utils/test-utils'

it('uploads file', async () => {
  renderWithProviders(<FileUpload />)

  const file = createMockFile('photo.jpg', 1024, 'image/jpeg')
  const input = screen.getByLabelText('Upload')

  await userEvent.upload(input, file)

  expect(screen.getByText('photo.jpg')).toBeInTheDocument()
})
```

### Mocking API Calls

```typescript
import axios from 'axios'

jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

it('fetches data', async () => {
  mockedAxios.get.mockResolvedValue({ data: { items: [] } })

  renderWithProviders(<DataList />)

  await waitFor(() => {
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/items')
  })
})
```

## Debugging Tests

### Debug Jest Tests

```typescript
import { screen } from '@testing-library/react'

it('debug test', () => {
  renderWithProviders(<MyComponent />)

  // Print entire DOM
  screen.debug()

  // Print specific element
  const element = screen.getByRole('button')
  screen.debug(element)
})
```

### Debug Playwright Tests

```bash
# Run with Playwright Inspector
npm run test:e2e:debug

# Or run specific test in debug mode
npx playwright test --debug tests/e2e/dashboard.spec.ts
```

## Viewing Coverage

```bash
# Generate coverage report
npm run test:coverage

# Open HTML report in browser
# Location: coverage/lcov-report/index.html
```

On Windows:
```bash
start coverage/lcov-report/index.html
```

On Mac/Linux:
```bash
open coverage/lcov-report/index.html
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:coverage

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### "Cannot find module" errors

Check that path aliases are configured in `jest.config.js`:
```javascript
moduleNameMapper: {
  '^@/(.*)$': '<rootDir>/src/$1',
}
```

### Tests timing out

Increase timeout in specific tests:
```typescript
it('slow test', async () => {
  // ...
}, 10000) // 10 second timeout
```

### Canvas errors in tests

Canvas mocking is already set up in `tests/setup.ts`. If you see errors, ensure setup file is loaded.

### Playwright browser not found

```bash
npx playwright install chromium
```

## Best Practices

1. **Test user behavior, not implementation**
   ```typescript
   // ✅ Good
   await userEvent.click(screen.getByRole('button', { name: 'Submit' }))

   // ❌ Avoid
   await userEvent.click(container.querySelector('.submit-btn'))
   ```

2. **Use semantic queries**
   ```typescript
   // ✅ Good - accessible and resilient
   screen.getByRole('button', { name: 'Submit' })
   screen.getByLabelText('Email')

   // ❌ Avoid - brittle
   screen.getByTestId('submit-button')
   screen.getByClassName('email-input')
   ```

3. **Keep tests isolated**
   ```typescript
   beforeEach(() => {
     // Reset state before each test
     jest.clearAllMocks()
   })
   ```

4. **Use fixtures for consistency**
   ```typescript
   import { mockArticle } from '@/tests/fixtures/articles'

   it('displays article', () => {
     renderWithProviders(<Article data={mockArticle} />)
     // ...
   })
   ```

## Additional Resources

- [Full Testing Documentation](./docs/TESTING.md)
- [Test Summary](./TEST_SUMMARY.md)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)

## Getting Help

### Common Commands Reference

```bash
# Unit tests
npm test                          # Run all
npm test -- --watch              # Watch mode
npm test -- --coverage           # With coverage
npm test -- MyComponent          # Specific test

# E2E tests
npm run test:e2e                 # Run all
npm run test:e2e:ui              # Interactive
npm run test:e2e:debug           # Debug mode
npx playwright test --project=chromium  # Specific browser

# Debugging
npm test -- --verbose            # Detailed output
npx playwright test --debug      # Step through E2E
npx playwright codegen http://localhost:3000  # Record new E2E test
```

---

**Happy Testing!** 🧪✨
