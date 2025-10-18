# Frontend Test Suite

Welcome to the OpenLearn Colombia frontend test suite!

## Quick Links

- 📚 [Quick Start Guide](./QUICK_START.md) - Get started with testing
- 📖 [Complete Testing Documentation](./docs/TESTING.md) - Comprehensive guide
- 📊 [Test Summary](./TEST_SUMMARY.md) - Overview of test coverage

## Test Structure

```
tests/
├── setup.ts                      # Jest configuration
├── __mocks__/                    # Module mocks
├── utils/                        # Test utilities & helpers
├── fixtures/                     # Mock data
├── components/                   # Component tests
│   ├── ui/                       # UI component tests
│   ├── auth/                     # Auth component tests
│   ├── filters/                  # Filter component tests
│   └── preferences/              # Preference component tests
├── lib/                          # Hook & utility tests
├── e2e/                          # End-to-end tests
└── docs/                         # Documentation
```

## Running Tests

### Quick Start

```bash
# Install dependencies
npm install

# Install Playwright browsers (first time only)
npx playwright install

# Run all tests
npm test

# Run E2E tests
npm run test:e2e
```

### Common Commands

```bash
npm test                    # Run unit tests
npm run test:watch         # Watch mode
npm run test:coverage      # Generate coverage
npm run test:e2e           # Run E2E tests
npm run test:e2e:ui        # E2E with UI
npm run test:all           # Run everything
```

## Test Coverage

Current coverage targets: **70%+** for all metrics
- Statements: 70%
- Branches: 70%
- Functions: 70%
- Lines: 70%

View coverage: `npm run test:coverage`

## What's Tested

✅ Dashboard components & charts
✅ User preferences & profile
✅ Navigation & routing
✅ Authentication flows
✅ Search & filtering
✅ UI components (avatars, selects, tags)
✅ Form validation
✅ File uploads
✅ Mobile responsiveness
✅ Keyboard navigation

## Writing Tests

See [QUICK_START.md](./QUICK_START.md) for examples and patterns.

## Documentation

- **QUICK_START.md** - Getting started guide
- **docs/TESTING.md** - Complete testing documentation
- **TEST_SUMMARY.md** - Test coverage summary

## Tech Stack

- Jest - Test framework
- React Testing Library - Component testing
- Playwright - E2E testing
- @swc/jest - Fast TypeScript compilation

---

For detailed information, see the [full documentation](./docs/TESTING.md).
