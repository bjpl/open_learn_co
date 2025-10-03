# Test Suite Guide - Open Learn Platform

## Overview

The test suite consists of **15 test files** with **54+ integration test cases** covering all major components and workflows.

## Test Structure

```
backend/tests/
├── integration/           # End-to-end workflow tests (54 tests, ~2000 LOC)
│   ├── test_nlp_pipeline_integration.py      # NLP processing workflows
│   ├── test_vocabulary_flow.py               # Vocabulary learning flows
│   ├── test_content_analysis_flow.py         # Content analysis workflows
│   ├── test_api_database_integration.py      # API + Database integration
│   └── conftest.py                           # Integration test fixtures
├── api/                   # API endpoint tests
│   ├── test_analysis_endpoints.py
│   ├── test_language_endpoints.py
│   └── test_scraping_endpoints.py
├── nlp/                   # NLP component tests
├── services/              # Service layer tests
└── conftest.py            # Shared fixtures
```

## Quick Start

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Run with Coverage Report
```bash
pytest tests/integration/ --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html  # View coverage report
```

## Integration Test Categories

### 1. NLP Pipeline Integration (test_nlp_pipeline_integration.py)
**15 tests** covering:
- Complete text analysis workflows
- Entity extraction and sentiment analysis
- Topic modeling and difficulty scoring
- Multilingual text processing
- Colombian Spanish text handling
- Batch processing performance
- Concurrent processing
- Edge cases and error handling

**Key Tests:**
- `test_complete_pipeline_news_article` - Full analysis workflow
- `test_batch_processing_performance` - Performance benchmarks
- `test_colombian_text_processing` - Colombian slang handling
- `test_difficulty_levels_progressive` - Difficulty scoring accuracy

### 2. Vocabulary Flow Integration (test_vocabulary_flow.py)
**14 tests** covering:
- Vocabulary discovery and storage
- User acquisition tracking
- Practice session workflows
- Spaced repetition scheduling
- Vocabulary lists and filtering
- Word forms and conjugations
- Collocations
- User progress analytics

**Key Tests:**
- `test_vocabulary_discovery_and_storage` - Complete vocab storage
- `test_practice_session_creation_and_completion` - Full practice flow
- `test_user_vocabulary_acquisition_tracking` - Progress tracking
- `test_spaced_repetition_scheduling` - SR algorithm

### 3. Content Analysis Flow (test_content_analysis_flow.py)
**13 tests** covering:
- Scraping to storage pipeline
- Complete analysis workflows
- Vocabulary extraction from content
- Batch content processing
- Content deduplication
- Colombian entity detection
- Error handling and recovery
- Performance metrics

**Key Tests:**
- `test_scraping_to_storage_flow` - End-to-end scraping
- `test_analysis_pipeline_integration` - Full analysis chain
- `test_batch_content_processing` - Batch operations
- `test_colombian_entity_detection` - Colombian-specific NER

### 4. API-Database Integration (test_api_database_integration.py)
**12 tests** covering:
- Analysis API endpoints with database
- Language learning API endpoints
- Transaction management
- Data consistency
- Error handling (404, 400, 500)
- Concurrent access
- Pagination and filtering

**Key Tests:**
- `test_analyze_text_endpoint` - Analysis API integration
- `test_start_practice_session` - Practice API flow
- `test_transaction_rollback_on_error` - Transaction safety
- `test_data_consistency` - Cross-table consistency

## Running Specific Tests

### By File
```bash
pytest tests/integration/test_nlp_pipeline_integration.py -v
pytest tests/integration/test_vocabulary_flow.py -v
```

### By Class
```bash
pytest tests/integration/test_nlp_pipeline_integration.py::TestNLPPipelineIntegration -v
pytest tests/integration/test_vocabulary_flow.py::TestVocabularyAcquisitionFlow -v
```

### By Test Name
```bash
pytest tests/integration/test_nlp_pipeline_integration.py::TestNLPPipelineIntegration::test_complete_pipeline_news_article -v
```

### By Marker
```bash
pytest tests/integration/ -m "database" -v
pytest tests/integration/ -m "not slow" -v
```

## Test Markers

Available markers for filtering:
- `integration` - Integration tests
- `slow` - Slow running tests (>5s)
- `database` - Tests requiring database
- `api` - API endpoint tests
- `nlp` - NLP pipeline tests
- `vocabulary` - Vocabulary-related tests

## Performance Expectations

### Individual Tests
- Unit tests: < 0.5s
- Integration tests: < 2s
- NLP tests: < 5s

### Test Suites
- Integration suite: < 2 minutes
- Full test suite: < 5 minutes

## Coverage Goals

Target coverage for integration tests:
- **Overall**: 80%+
- **API Endpoints**: 90%+
- **Critical Workflows**: 95%+
- **Error Handling**: 100%

### Current Coverage
```bash
# Run to see current coverage
pytest tests/integration/ --cov=app --cov-report=term-missing
```

## Database Testing

Integration tests use **in-memory SQLite**:
- Fast test execution
- Fresh database per test
- No persistent state
- Automatic cleanup

### Database Fixtures
```python
@pytest.fixture
def db_session(db_engine):
    """Provides clean database session"""
    # Creates fresh session
    # Automatic rollback after test

@pytest.fixture
def test_user(db_session):
    """Provides test user"""
    # Creates user in test database
```

## Common Test Patterns

### Testing Complete Workflow
```python
def test_complete_workflow(db_session, nlp_components):
    # 1. Create data
    article = create_test_article(db_session)

    # 2. Process through pipeline
    analysis = analyze_content(article, nlp_components)

    # 3. Store results
    db_session.add(analysis)
    db_session.commit()

    # 4. Verify complete flow
    assert analysis.entities is not None
    assert analysis.sentiment_score is not None
```

### Testing Error Handling
```python
def test_error_handling(db_session):
    try:
        # Attempt problematic operation
        process_invalid_data()
        pytest.fail("Should have raised exception")
    except ValueError:
        # Expected exception
        db_session.rollback()
```

### Testing Database Transactions
```python
def test_transaction_rollback(db_session):
    initial_count = count_records(db_session)

    try:
        # Operations that cause error
        create_duplicate_record(db_session)
    except Exception:
        db_session.rollback()

    # Verify rollback
    assert count_records(db_session) == initial_count
```

## Debugging Failed Tests

### Verbose Output
```bash
pytest tests/integration/ -vv --tb=long
```

### Show Print Statements
```bash
pytest tests/integration/test_vocabulary_flow.py -s
```

### Run with Debugger
```bash
pytest tests/integration/test_vocabulary_flow.py --pdb
```

### Run Last Failed
```bash
pytest tests/integration/ --lf
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main
- Nightly builds

**CI Requirements:**
- All tests must pass
- Coverage >= 80%
- No skipped tests (except marked)
- Performance within limits

## Test Development Guidelines

1. **Test Real Workflows** - Integration tests should test complete user workflows
2. **Use Fixtures** - Reuse common setup via fixtures
3. **Test Error Paths** - Don't just test happy paths
4. **Mock External Services** - Don't call real APIs in tests
5. **Verify Database State** - Check that data is correctly stored
6. **Clean Up Resources** - Use fixtures for automatic cleanup
7. **Descriptive Names** - Test names should explain what's being tested

## Next Steps

### To Run Tests Now
```bash
cd backend
pytest tests/integration/ -v --cov=app
```

### To Add New Tests
1. Add test file to appropriate directory
2. Use existing fixtures from conftest.py
3. Follow naming convention: `test_*.py`
4. Add markers for categorization
5. Run locally before committing

### To Improve Coverage
```bash
# See what's missing coverage
pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML report for detailed analysis
pytest tests/ --cov=app --cov-report=html
```

## Test Results Summary

**Created:**
- ✅ 4 integration test files
- ✅ 54+ test cases
- ✅ ~2000 lines of test code
- ✅ Complete database fixtures
- ✅ Comprehensive coverage

**Covers:**
- ✅ NLP pipeline workflows
- ✅ Vocabulary acquisition flows
- ✅ Content analysis pipeline
- ✅ API-database integration
- ✅ Transaction management
- ✅ Error handling
- ✅ Performance testing
- ✅ Colombian-specific features
