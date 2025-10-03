# Integration Tests

This directory contains integration tests for the Open Learn platform. Integration tests verify that multiple components work together correctly and test complete workflows from end to end.

## Test Structure

### Test Files

1. **test_nlp_pipeline_integration.py**
   - Tests complete NLP analysis workflows
   - Entity extraction, sentiment analysis, topic modeling
   - Multi-language support
   - Performance benchmarks
   - Batch processing

2. **test_vocabulary_flow.py**
   - Vocabulary acquisition workflows
   - Practice session management
   - User progress tracking
   - Spaced repetition
   - Collocations and word forms

3. **test_content_analysis_flow.py**
   - Content scraping → analysis → storage flow
   - Batch content processing
   - Error handling and recovery
   - Content deduplication
   - Colombian entity detection

4. **test_api_database_integration.py**
   - API endpoints with real database
   - Transaction management
   - Data consistency checks
   - Error handling
   - Concurrent access

## Running Tests

### Run all integration tests:
```bash
cd backend
pytest tests/integration/ -v
```

### Run specific test file:
```bash
pytest tests/integration/test_nlp_pipeline_integration.py -v
```

### Run with coverage:
```bash
pytest tests/integration/ --cov=backend/app --cov-report=html
```

### Run specific test class:
```bash
pytest tests/integration/test_vocabulary_flow.py::TestVocabularyAcquisitionFlow -v
```

### Run specific test:
```bash
pytest tests/integration/test_api_database_integration.py::TestAnalysisAPIIntegration::test_analyze_text_endpoint -v
```

### Run with markers:
```bash
# Run only database tests
pytest tests/integration/ -m database

# Run only API tests
pytest tests/integration/ -m api

# Skip slow tests
pytest tests/integration/ -m "not slow"
```

## Test Categories

### By Component
- **NLP Tests**: Natural language processing workflows
- **Vocabulary Tests**: Vocabulary learning and practice
- **Content Tests**: Content scraping and analysis
- **API Tests**: API endpoints with database

### By Type
- **Flow Tests**: End-to-end workflows
- **Integration Tests**: Component interactions
- **Database Tests**: Database operations
- **Performance Tests**: Speed and efficiency

## Test Coverage Goals

- Overall integration coverage: **80%+**
- API endpoints: **90%+**
- Critical workflows: **95%+**
- Error handling: **100%**

## Database Setup

Integration tests use an in-memory SQLite database for speed:
- Fresh database for each test function
- Automatic table creation
- Automatic cleanup after tests
- No persistent data

## Fixtures

Common fixtures available (see conftest.py):
- `db_engine`: Database engine
- `db_session`: Database session
- `test_user`: Sample user
- `sample_vocabulary_items`: Sample vocabulary
- `nlp_components`: NLP pipeline components

## Best Practices

1. **Use fixtures** for common setup
2. **Test real workflows** not just individual functions
3. **Test error paths** as well as happy paths
4. **Mock external services** (news sites, APIs)
5. **Verify database state** after operations
6. **Clean up resources** in teardown
7. **Use descriptive test names** that explain what is being tested

## Performance Guidelines

- Individual tests: < 1 second
- NLP tests: < 5 seconds
- Batch processing: < 10 seconds
- Full suite: < 2 minutes

## Debugging Tests

### Run with detailed output:
```bash
pytest tests/integration/ -vv --tb=long
```

### Run single test with print statements:
```bash
pytest tests/integration/test_vocabulary_flow.py::test_name -s
```

### Run with Python debugger:
```bash
pytest tests/integration/test_vocabulary_flow.py::test_name --pdb
```

## Continuous Integration

These tests are run automatically on:
- Every pull request
- Every commit to main branch
- Nightly builds

CI requires all integration tests to pass before merging.
