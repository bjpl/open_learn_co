# Test Suite Architecture - OpenLearn Platform

## Executive Summary

This document outlines a comprehensive test architecture for the OpenLearn Spanish language learning platform. The architecture targets 80%+ code coverage with a multi-layered testing strategy covering unit, integration, and end-to-end tests across backend, frontend, and scraper components.

## Table of Contents

1. [Test Directory Structure](#test-directory-structure)
2. [Testing Frameworks and Tools](#testing-frameworks-and-tools)
3. [Test Categories and Organization](#test-categories-and-organization)
4. [Backend Testing Strategy](#backend-testing-strategy)
5. [Frontend Testing Strategy](#frontend-testing-strategy)
6. [Integration Testing](#integration-testing)
7. [End-to-End Testing](#end-to-end-testing)
8. [CI/CD Integration](#cicd-integration)
9. [Coverage Targets](#coverage-targets)
10. [Mock and Fixture Strategy](#mock-and-fixture-strategy)

---

## 1. Test Directory Structure

```
open_learn/
├── backend/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                     # Pytest fixtures (EXISTING)
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_scrapers.py            # EXISTING - needs expansion
│   │   │   ├── test_api_clients.py         # EXISTING - needs expansion
│   │   │   ├── test_nlp_pipeline.py
│   │   │   ├── test_sentiment_analyzer.py
│   │   │   ├── test_topic_modeler.py
│   │   │   ├── test_difficulty_scorer.py
│   │   │   ├── test_vocabulary_service.py
│   │   │   ├── test_rate_limiter.py
│   │   │   ├── test_smart_scraper.py
│   │   │   └── test_validators.py
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_api_endpoints.py
│   │   │   ├── test_database_operations.py
│   │   │   ├── test_scraping_workflow.py
│   │   │   ├── test_analysis_workflow.py
│   │   │   ├── test_language_workflow.py
│   │   │   ├── test_source_manager.py      # EXISTING
│   │   │   └── test_scheduler.py
│   │   ├── e2e/
│   │   │   ├── __init__.py
│   │   │   ├── test_complete_scraping_pipeline.py
│   │   │   ├── test_multi_language_processing.py
│   │   │   ├── test_user_learning_journey.py
│   │   │   └── test_analytics_generation.py
│   │   ├── performance/
│   │   │   ├── __init__.py
│   │   │   ├── test_scraper_performance.py
│   │   │   ├── test_api_load.py
│   │   │   ├── test_database_queries.py
│   │   │   └── test_concurrent_operations.py
│   │   └── fixtures/
│   │       ├── __init__.py
│   │       ├── sample_html.py
│   │       ├── sample_api_responses.py
│   │       ├── sample_database_records.py
│   │       └── test_data/
│   │           ├── articles.json
│   │           ├── api_responses.json
│   │           └── mock_html/
│   │
│   ├── requirements-test.txt               # NEW
│   └── pytest.ini                          # NEW
│
├── frontend/
│   ├── __tests__/
│   │   ├── components/
│   │   │   ├── Navbar.test.tsx
│   │   │   ├── StatsCard.test.tsx
│   │   │   ├── SourceStatus.test.tsx
│   │   │   └── ErrorBoundary.test.tsx
│   │   ├── pages/
│   │   │   ├── Home.test.tsx
│   │   │   ├── News.test.tsx
│   │   │   ├── Analytics.test.tsx
│   │   │   ├── Sources.test.tsx
│   │   │   └── Trends.test.tsx
│   │   ├── hooks/
│   │   │   ├── useQuery.test.tsx
│   │   │   └── useWebSocket.test.tsx
│   │   ├── utils/
│   │   │   └── api.test.tsx
│   │   └── integration/
│   │       ├── app-navigation.test.tsx
│   │       └── data-flow.test.tsx
│   ├── jest.config.js                      # NEW
│   ├── jest.setup.js                       # NEW
│   └── package.json                        # UPDATE scripts
│
├── scrapers/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_el_tiempo.py
│   │   ├── test_el_espectador.py
│   │   └── test_all_scrapers.py
│   └── conftest.py                         # NEW
│
└── tests/
    ├── e2e/                                # NEW - System-wide E2E
    │   ├── test_full_platform.py
    │   ├── test_api_integration.py
    │   └── test_real_scraping.py
    └── load/                               # NEW - Load testing
        ├── locustfile.py
        └── k6_script.js
```

---

## 2. Testing Frameworks and Tools

### Backend (Python)

#### Core Testing Framework
- **pytest** (v7.4+): Primary testing framework
  - pytest-asyncio: Async test support
  - pytest-cov: Coverage reporting
  - pytest-mock: Advanced mocking
  - pytest-xdist: Parallel test execution
  - pytest-timeout: Test timeout handling

#### HTTP and API Testing
- **aioresponses**: Mock aiohttp requests
- **responses**: Mock requests library
- **httpx**: HTTP client for testing

#### Database Testing
- **pytest-postgresql**: PostgreSQL fixtures
- **faker**: Generate test data
- **factory-boy**: Model factories

#### Specialized Testing
- **freezegun**: Time mocking
- **pytest-benchmark**: Performance benchmarking
- **hypothesis**: Property-based testing

### Frontend (TypeScript/React)

#### Core Testing Framework
- **Jest** (v29+): Test runner and assertion library
- **React Testing Library**: Component testing
- **@testing-library/jest-dom**: Custom matchers

#### Integration Testing
- **MSW (Mock Service Worker)**: API mocking
- **@tanstack/react-query**: Query testing utilities

#### E2E Testing
- **Playwright**: Browser automation
- **Cypress** (alternative): Full E2E testing

#### Utilities
- **@testing-library/user-event**: User interaction simulation
- **jest-axe**: Accessibility testing

### Load Testing
- **Locust**: Python-based load testing
- **k6**: JavaScript-based performance testing
- **Apache Bench**: Simple HTTP benchmarking

---

## 3. Test Categories and Organization

### Unit Tests (60% of test suite)
**Purpose**: Test individual functions and classes in isolation

**Scope**:
- Individual scraper methods
- NLP processing functions
- API client methods
- Utility functions
- Database models
- React components (shallow)

**Characteristics**:
- Fast execution (< 100ms per test)
- No external dependencies
- Extensive mocking
- High code coverage (>85%)

### Integration Tests (30% of test suite)
**Purpose**: Test interactions between components

**Scope**:
- API endpoint workflows
- Database transactions
- Scraper + NLP pipelines
- Service layer integration
- Frontend + API integration

**Characteristics**:
- Moderate execution time (< 1s per test)
- Real database (test DB)
- Minimal mocking
- Focus on interfaces

### End-to-End Tests (10% of test suite)
**Purpose**: Test complete user workflows

**Scope**:
- Complete scraping workflow
- User learning journey
- Multi-language processing
- Analytics generation
- Frontend user flows

**Characteristics**:
- Slower execution (1-10s per test)
- Real services when possible
- Minimal mocking
- Critical path testing

---

## 4. Backend Testing Strategy

### 4.1 Unit Tests

#### Scrapers (`backend/tests/unit/test_scrapers.py`)

**Test Coverage**:
```python
# Per Scraper (El Tiempo, El Espectador, Semana, etc.)
- test_initialization()
- test_parse_article()
- test_extract_text()
- test_extract_metadata()
- test_extract_colombian_entities()
- test_difficulty_calculation()
- test_article_url_detection()
- test_paywall_detection()
- test_get_article_urls()
- test_rate_limiting()
- test_error_handling()

# Base Scraper
- test_html_parsing()
- test_text_cleaning()
- test_caching()
- test_user_agent_rotation()
- test_retry_mechanism()
```

**Example Test Structure**:
```python
class TestElTiempoScraper:
    @pytest.fixture
    def scraper(self, scraper_config):
        return ElTiempoScraper(scraper_config)

    @pytest.fixture
    def sample_html(self):
        return Path('fixtures/test_data/mock_html/el_tiempo.html').read_text()

    @pytest.mark.asyncio
    async def test_parse_article(self, scraper, sample_html):
        soup = BeautifulSoup(sample_html, 'html.parser')
        article = scraper.parse_article(soup, 'https://test.url')

        assert article is not None
        assert article['title']
        assert article['content']
        assert article['difficulty_score'] > 0
        assert 'DANE' in article['colombian_entities']['institutions']
```

#### NLP Components (`backend/tests/unit/test_nlp_*.py`)

**Test Coverage**:
```python
# Sentiment Analyzer
- test_analyze_positive_text()
- test_analyze_negative_text()
- test_analyze_neutral_text()
- test_spanish_sentiment_accuracy()
- test_confidence_scores()

# Topic Modeler
- test_train_model()
- test_predict_topics()
- test_topic_coherence()
- test_multilingual_support()

# Difficulty Scorer
- test_calculate_flesch_reading_ease()
- test_cefr_level_assignment()
- test_vocabulary_complexity()
- test_sentence_structure_analysis()

# Colombian NER
- test_extract_institutions()
- test_extract_locations()
- test_extract_persons()
- test_regional_entities()
```

#### API Clients (`backend/tests/unit/test_api_clients.py`)

**Test Coverage per Client**:
```python
# DANE Client
- test_get_inflation_data()
- test_get_gdp_data()
- test_get_employment_statistics()
- test_data_transformation()
- test_error_handling()

# Banco República Client
- test_get_exchange_rates()
- test_get_interest_rates()
- test_rate_history()

# SECOP Client
- test_get_contracts()
- test_filter_by_entity()
- test_pagination()
```

### 4.2 Integration Tests

#### API Endpoints (`backend/tests/integration/test_api_endpoints.py`)

**Test Coverage**:
```python
# Scraping Endpoints
- test_list_sources()
- test_trigger_scraping()
- test_get_scraping_status()
- test_get_scraped_content()
- test_filter_by_difficulty()

# Analysis Endpoints
- test_analyze_text()
- test_batch_analyze()
- test_get_analysis_results()
- test_analysis_statistics()

# Language Learning Endpoints
- test_add_vocabulary()
- test_get_vocabulary()
- test_start_practice_session()
- test_record_practice_result()
- test_get_learning_progress()
```

**Example Integration Test**:
```python
@pytest.mark.asyncio
async def test_complete_scraping_workflow(async_client, test_db):
    # Trigger scraping
    response = await async_client.post('/api/scrape/trigger/El Tiempo')
    assert response.status_code == 200

    # Wait for processing
    await asyncio.sleep(2)

    # Verify content stored
    content_response = await async_client.get('/api/scrape/content?source=El Tiempo')
    assert content_response.status_code == 200
    data = content_response.json()
    assert data['count'] > 0
    assert data['articles'][0]['difficulty_score'] is not None
```

#### Database Operations (`backend/tests/integration/test_database_operations.py`)

**Test Coverage**:
```python
- test_save_scraped_content()
- test_query_by_difficulty()
- test_query_by_category()
- test_save_analysis_results()
- test_vocabulary_acquisition()
- test_learning_session_tracking()
- test_transaction_rollback()
- test_concurrent_writes()
```

### 4.3 E2E Tests

#### Complete Workflows (`backend/tests/e2e/test_complete_scraping_pipeline.py`)

**Test Coverage**:
```python
- test_scrape_analyze_store_pipeline()
- test_multi_source_aggregation()
- test_vocabulary_extraction_workflow()
- test_user_learning_journey()
- test_analytics_generation()
```

---

## 5. Frontend Testing Strategy

### 5.1 Component Tests

**Test Coverage per Component**:
```typescript
// Navbar Component
describe('Navbar', () => {
  test('renders all navigation links', () => {})
  test('highlights active route', () => {})
  test('mobile menu toggle', () => {})
})

// StatsCard Component
describe('StatsCard', () => {
  test('displays metric correctly', () => {})
  test('formats numbers with locale', () => {})
  test('renders trend indicator', () => {})
  test('handles loading state', () => {})
  test('handles error state', () => {})
})

// SourceStatus Component
describe('SourceStatus', () => {
  test('displays source information', () => {})
  test('shows last update time', () => {})
  test('indicates active/inactive status', () => {})
})
```

### 5.2 Page Tests

**Test Coverage per Page**:
```typescript
// Home Page
describe('HomePage', () => {
  test('fetches and displays dashboard data', async () => {})
  test('shows loading skeleton', () => {})
  test('handles API errors gracefully', () => {})
  test('refreshes data on interval', () => {})
})

// News Page
describe('NewsPage', () => {
  test('displays article list', async () => {})
  test('filters by difficulty level', () => {})
  test('filters by source', () => {})
  test('pagination works correctly', () => {})
  test('search functionality', () => {})
})

// Analytics Page
describe('AnalyticsPage', () => {
  test('renders charts with data', async () => {})
  test('chart interactions work', () => {})
  test('date range filtering', () => {})
  test('export functionality', () => {})
})
```

### 5.3 Integration Tests

**Test Coverage**:
```typescript
// App Navigation
describe('App Navigation', () => {
  test('navigates between pages', () => {})
  test('maintains state during navigation', () => {})
  test('404 page for invalid routes', () => {})
})

// Data Flow
describe('Data Flow', () => {
  test('API -> Store -> Component', async () => {})
  test('WebSocket real-time updates', () => {})
  test('Error boundary catches errors', () => {})
})
```

---

## 6. Integration Testing

### 6.1 Backend-Frontend Integration

**Test Approach**: Use MSW to mock backend APIs

```typescript
// Example: frontend/src/__tests__/integration/api-integration.test.tsx
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.get('/api/scrape/content', (req, res, ctx) => {
    return res(ctx.json({
      articles: [
        { id: 1, title: 'Test Article', difficulty_score: 3.2 }
      ]
    }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('fetches articles from API', async () => {
  // Test implementation
})
```

### 6.2 Database Integration

**Test Approach**: Use pytest-postgresql for real database tests

```python
# backend/tests/integration/test_database_operations.py
@pytest.fixture
async def test_db(postgresql):
    # Setup test database
    engine = create_async_engine(postgresql.dsn())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.mark.asyncio
async def test_save_and_retrieve_article(test_db):
    async with AsyncSession(test_db) as session:
        article = ScrapedContent(
            title="Test Article",
            content="Content here",
            source="Test Source"
        )
        session.add(article)
        await session.commit()

        result = await session.execute(
            select(ScrapedContent).where(ScrapedContent.title == "Test Article")
        )
        retrieved = result.scalar_one()
        assert retrieved.title == "Test Article"
```

---

## 7. End-to-End Testing

### 7.1 Backend E2E with Playwright

```python
# tests/e2e/test_full_platform.py
import asyncio
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_complete_user_journey():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to home
        await page.goto('http://localhost:3000')

        # Verify dashboard loads
        await page.wait_for_selector('[data-testid="dashboard"]')

        # Navigate to news
        await page.click('a[href="/news"]')

        # Verify articles load
        await page.wait_for_selector('[data-testid="article-list"]')

        # Filter by difficulty
        await page.select_option('[data-testid="difficulty-filter"]', 'A2')

        # Verify filtering works
        articles = await page.query_selector_all('[data-testid="article-item"]')
        assert len(articles) > 0

        await browser.close()
```

### 7.2 API E2E Tests

```python
# tests/e2e/test_api_integration.py
@pytest.mark.asyncio
async def test_scrape_to_analysis_pipeline(live_server):
    async with aiohttp.ClientSession() as session:
        # Trigger scraping
        async with session.post(f'{live_server}/api/scrape/trigger/El Tiempo') as resp:
            assert resp.status == 200

        # Wait for processing
        await asyncio.sleep(5)

        # Get scraped content
        async with session.get(f'{live_server}/api/scrape/content?limit=1') as resp:
            data = await resp.json()
            assert data['count'] > 0
            article_id = data['articles'][0]['id']

        # Trigger analysis
        async with session.post(
            f'{live_server}/api/analysis/batch-analyze',
            json={'content_ids': [article_id]}
        ) as resp:
            assert resp.status == 200

        # Verify analysis results
        await asyncio.sleep(2)
        async with session.get(f'{live_server}/api/analysis/results') as resp:
            results = await resp.json()
            assert results['total'] > 0
```

---

## 8. CI/CD Integration

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpassword
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov=scrapers --cov=nlp --cov-report=xml

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://postgres:testpassword@localhost/test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python and Node
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Playwright
        run: |
          npm install -g playwright
          playwright install chromium

      - name: Start services
        run: |
          # Start backend
          cd backend
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &

          # Start frontend
          cd ../frontend
          npm ci
          npm run build
          npm run start &

          # Wait for services
          sleep 10

      - name: Run E2E tests
        run: |
          pytest tests/e2e -v
```

### 8.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-fast
        name: Fast unit tests
        entry: bash -c 'cd backend && pytest tests/unit -x --tb=short'
        language: system
        pass_filenames: false

      - id: jest
        name: Frontend tests
        entry: bash -c 'cd frontend && npm run test -- --bail --findRelatedTests'
        language: system
        pass_filenames: false
```

---

## 9. Coverage Targets

### Overall Target: 80%+ Coverage

#### Backend Coverage Goals

| Component | Target | Priority |
|-----------|--------|----------|
| API Endpoints | 85% | High |
| Scrapers | 80% | High |
| NLP Services | 85% | High |
| API Clients | 75% | Medium |
| Database Models | 70% | Medium |
| Utilities | 90% | Low |

#### Frontend Coverage Goals

| Component | Target | Priority |
|-----------|--------|----------|
| Pages | 75% | High |
| Components | 80% | High |
| Hooks | 85% | Medium |
| Utils | 90% | Low |

### Coverage Enforcement

```ini
# backend/pytest.ini
[pytest]
addopts =
    --cov=app
    --cov=scrapers
    --cov=nlp
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
```

```json
// frontend/package.json
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 75,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

---

## 10. Mock and Fixture Strategy

### 10.1 Backend Fixtures

**Shared Fixtures** (`backend/tests/conftest.py`):
```python
@pytest.fixture
def sample_article():
    """Sample scraped article"""
    return {
        'title': 'Test Article',
        'content': 'Test content for language learning',
        'source': 'El Tiempo',
        'difficulty_score': 3.2,
        'colombian_entities': {
            'institutions': ['DANE', 'Banco de la República']
        }
    }

@pytest.fixture
async def test_db():
    """Async test database session"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp client sessions"""
    with aioresponses() as m:
        yield m
```

**Specialized Fixtures** (`backend/tests/fixtures/`):
```python
# fixtures/sample_html.py
EL_TIEMPO_ARTICLE = """
<article>
    <h1>Economic Growth in Colombia</h1>
    <div class="content">
        <p>DANE reports 3.2% GDP growth...</p>
    </div>
</article>
"""

# fixtures/sample_api_responses.py
DANE_INFLATION_RESPONSE = {
    "resultado": [
        {"fecha": "2024-01-01", "variacion_anual": 5.8}
    ]
}
```

### 10.2 Frontend Mocks

**MSW Handlers** (`frontend/src/mocks/handlers.ts`):
```typescript
import { rest } from 'msw'

export const handlers = [
  rest.get('/api/scrape/content', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        articles: [
          {
            id: 1,
            title: 'Test Article',
            difficulty_score: 3.2,
            source: 'El Tiempo'
          }
        ],
        total: 1
      })
    )
  }),

  rest.post('/api/analysis/analyze', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        sentiment: { polarity: 0.5, classification: 'positive' },
        entities: [{ text: 'Colombia', type: 'GPE' }]
      })
    )
  })
]
```

**Component Test Utilities** (`frontend/src/test-utils.tsx`):
```typescript
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

export function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Set up pytest configuration and structure
2. Set up Jest configuration and structure
3. Create shared fixtures and mocks
4. Write basic unit tests for critical paths

### Phase 2: Core Coverage (Week 2-3)
1. Complete scraper unit tests
2. Complete NLP service unit tests
3. Complete API client unit tests
4. Complete component unit tests

### Phase 3: Integration (Week 4)
1. API endpoint integration tests
2. Database integration tests
3. Frontend integration tests
4. Service workflow tests

### Phase 4: E2E and Performance (Week 5)
1. Complete E2E test scenarios
2. Performance and load tests
3. CI/CD pipeline setup
4. Coverage reporting and enforcement

---

## Testing Best Practices

1. **Isolation**: Tests should be independent and runnable in any order
2. **Speed**: Unit tests < 100ms, Integration tests < 1s, E2E tests < 10s
3. **Clarity**: Test names should describe behavior, not implementation
4. **Reliability**: Avoid flaky tests with proper waits and deterministic data
5. **Maintainability**: Keep tests DRY with shared fixtures and utilities
6. **Coverage**: Target meaningful coverage, not just line coverage
7. **Documentation**: Tests serve as living documentation of expected behavior

---

## Monitoring and Metrics

### Test Metrics to Track
- Total test count
- Test execution time
- Coverage percentage (overall and per module)
- Test failure rate
- Flaky test identification
- Test maintenance overhead

### Reporting
- Coverage reports in CI/CD
- Test result dashboards
- Trend analysis over time
- Performance regression tracking

---

## Appendix

### A. Required Dependencies

**Backend** (`backend/requirements-test.txt`):
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-xdist==3.5.0
pytest-timeout==2.2.0
aioresponses==0.7.6
responses==0.24.1
httpx==0.26.0
pytest-postgresql==5.0.0
faker==22.0.0
factory-boy==3.3.0
freezegun==1.4.0
pytest-benchmark==4.0.0
hypothesis==6.96.1
locust==2.20.0
```

**Frontend** (`frontend/package.json`):
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "@testing-library/user-event": "^14.5.1",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@types/jest": "^29.5.11",
    "msw": "^2.0.11",
    "playwright": "^1.40.1",
    "@playwright/test": "^1.40.1",
    "jest-axe": "^8.0.0"
  }
}
```

### B. Configuration Files

**pytest.ini**:
```ini
[pytest]
minversion = 7.0
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov=scrapers
    --cov=nlp
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    e2e: mark test as end-to-end test
    slow: mark test as slow running
```

**jest.config.js**:
```javascript
module.exports = {
  preset: 'next/jest',
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/_*.{js,jsx,ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Author**: System Architect
**Review Status**: Ready for Implementation
