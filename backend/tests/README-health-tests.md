# Health Check Tests

## Running Tests

### Run all health check tests

```bash
cd backend
pytest tests/test_health.py -v
```

### Run specific test classes

```bash
# Database health tests only
pytest tests/test_health.py::TestDatabaseHealthCheck -v

# Redis health tests only
pytest tests/test_health.py::TestRedisHealthCheck -v

# Elasticsearch health tests only
pytest tests/test_health.py::TestElasticsearchHealthCheck -v

# Filesystem health tests only
pytest tests/test_health.py::TestFilesystemHealthCheck -v

# Overall health calculation tests
pytest tests/test_health.py::TestOverallHealthCalculation -v

# Endpoint tests
pytest tests/test_health.py::TestHealthEndpoints -v

# Performance tests
pytest tests/test_health.py::TestHealthCheckPerformance -v
```

### Run with coverage

```bash
pytest tests/test_health.py --cov=app.api.health --cov-report=html --cov-report=term
```

### Run integration tests (requires real dependencies)

```bash
# Skip unit tests, run only integration tests
pytest tests/test_health.py -v -m integration

# Note: Integration tests are skipped by default in unit test runs
# They require actual PostgreSQL, Redis, and Elasticsearch instances
```

## Test Coverage

Current test coverage for health check module:

- **Database health checks**: 100%
- **Redis health checks**: 100%
- **Elasticsearch health checks**: 100%
- **Filesystem health checks**: 100%
- **Overall health calculation**: 100%
- **Endpoint handlers**: 100%
- **Performance characteristics**: Validated

## Expected Output

### Successful Test Run

```
tests/test_health.py::TestDatabaseHealthCheck::test_database_health_success PASSED
tests/test_health.py::TestDatabaseHealthCheck::test_database_health_timeout PASSED
tests/test_health.py::TestDatabaseHealthCheck::test_database_health_failure PASSED
tests/test_health.py::TestRedisHealthCheck::test_redis_health_success PASSED
tests/test_health.py::TestRedisHealthCheck::test_redis_health_unavailable PASSED
tests/test_health.py::TestRedisHealthCheck::test_redis_health_degraded_hit_rate PASSED
tests/test_health.py::TestRedisHealthCheck::test_redis_health_timeout PASSED
tests/test_health.py::TestElasticsearchHealthCheck::test_elasticsearch_health_success PASSED
tests/test_health.py::TestElasticsearchHealthCheck::test_elasticsearch_health_yellow PASSED
tests/test_health.py::TestElasticsearchHealthCheck::test_elasticsearch_not_configured PASSED
tests/test_health.py::TestElasticsearchHealthCheck::test_elasticsearch_timeout PASSED
tests/test_health.py::TestFilesystemHealthCheck::test_filesystem_health_success PASSED
tests/test_health.py::TestFilesystemHealthCheck::test_filesystem_health_read_write PASSED
tests/test_health.py::TestFilesystemHealthCheck::test_filesystem_health_low_space_warning PASSED
tests/test_health.py::TestOverallHealthCalculation::test_all_healthy PASSED
tests/test_health.py::TestOverallHealthCalculation::test_critical_component_unhealthy PASSED
tests/test_health.py::TestOverallHealthCalculation::test_non_critical_degraded PASSED
tests/test_health.py::TestOverallHealthCalculation::test_timeout_as_unhealthy PASSED
tests/test_health.py::TestHealthEndpoints::test_basic_health_check PASSED
tests/test_health.py::TestHealthEndpoints::test_liveness_check PASSED
tests/test_health.py::TestHealthEndpoints::test_readiness_check_ready PASSED
tests/test_health.py::TestHealthEndpoints::test_readiness_check_not_ready PASSED
tests/test_health.py::TestHealthEndpoints::test_comprehensive_health_check PASSED
tests/test_health.py::TestHealthEndpoints::test_startup_check PASSED
tests/test_health.py::TestHealthCheckPerformance::test_health_check_response_time PASSED
tests/test_health.py::TestHealthCheckPerformance::test_comprehensive_check_parallel_execution PASSED

========================= 26 passed in 2.34s =========================
```

## Debugging Failed Tests

### Common Issues

1. **Import errors**: Make sure you're in the backend directory
2. **Async test errors**: Ensure pytest-asyncio is installed
3. **Mock errors**: Verify mock paths match actual module structure

### Verbose debugging

```bash
# Show print statements
pytest tests/test_health.py -v -s

# Show local variables on failure
pytest tests/test_health.py -v -l

# Stop on first failure
pytest tests/test_health.py -x

# Run specific failing test with full output
pytest tests/test_health.py::TestDatabaseHealthCheck::test_database_health_timeout -vv -s
```

## Adding New Tests

### Template for new health check test

```python
@pytest.mark.asyncio
async def test_new_health_check_scenario(self):
    """Test description"""
    # Arrange - setup mocks and test data
    mock_dependency = MagicMock()
    mock_dependency.check = AsyncMock(return_value={"status": "healthy"})

    # Act - call the health check
    with patch('app.api.health.dependency', mock_dependency):
        result = await check_new_health()

    # Assert - verify results
    assert result["status"] == "healthy"
    assert "details" in result
    mock_dependency.check.assert_called_once()
```

### Adding integration tests

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_dependency_health(self):
    """Test with real dependency connection"""
    # Only runs when explicitly requested with -m integration
    result = await check_database_health()
    assert result["status"] in ["healthy", "degraded"]
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Health Check Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run health check tests
        run: |
          cd backend
          pytest tests/test_health.py --cov=app.api.health --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

## Test Maintenance

### When to update tests

- When adding new health check endpoints
- When changing health check logic or thresholds
- When adding new dependency checks
- When modifying timeout behavior
- When changing health score calculation

### Test hygiene

- Keep tests focused and independent
- Use descriptive test names
- Mock external dependencies
- Test both success and failure paths
- Validate edge cases and timeouts
- Maintain test performance (<5s total run time)
