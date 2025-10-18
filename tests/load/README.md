# Load Testing Guide for OpenLearn Colombia

## Overview
This directory contains Locust-based load testing configurations for OpenLearn Colombia. The tests simulate realistic user behavior patterns and help validate system performance under load.

## Quick Start

### Installation
```bash
pip install locust
```

### Run Load Tests Locally
```bash
# Basic load test
locust -f locustfile.py --host http://localhost:8000

# Headless mode (automated)
locust -f locustfile.py \
  --host http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### Run Against Staging
```bash
locust -f locustfile.py \
  --host https://staging.openlearn.colombia \
  --users 1000 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html load-test-report.html
```

## Test Scenarios

### User Types and Distribution

1. **OpenLearnUser (50% of traffic)**
   - Browsing articles
   - Searching content
   - Viewing dashboards
   - General navigation

2. **AuthenticationUser (20% of traffic)**
   - Login attempts
   - Logout operations
   - Registration flows

3. **SearchHeavyUser (15% of traffic)**
   - Intensive search operations
   - Advanced filtering
   - Multiple query patterns

4. **DashboardUser (10% of traffic)**
   - Dashboard loading
   - Progress tracking
   - Analytics viewing

5. **ApiHeavyUser (5% of traffic)**
   - Batch API requests
   - Data fetching operations
   - Related content queries

### Load Profile (StepLoadShape)

The default load shape ramps up gradually:

- **Step 1** (0-2 min): 100 users
- **Step 2** (2-4 min): 300 users
- **Step 3** (4-6 min): 600 users
- **Step 4** (6-9 min): 1000 users
- **Step 5** (9-11 min): 500 users (cool down)

Total duration: 11 minutes

## Performance Targets

### Response Times
- **p50**: < 200ms
- **p95**: < 500ms
- **p99**: < 1000ms

### Throughput
- **Minimum**: 100 requests/second
- **Target**: 200+ requests/second
- **Peak**: 500+ requests/second

### Error Rate
- **Maximum**: < 1%
- **Target**: < 0.1%

## Running Specific Tests

### Test Authentication Only
```bash
locust -f locustfile.py \
  --class-picker \
  --host http://localhost:8000 \
  AuthenticationUser
```

### Test Search Performance
```bash
locust -f locustfile.py \
  --class-picker \
  --host http://localhost:8000 \
  SearchHeavyUser
```

### Custom Load Shape
```python
# Edit locustfile.py to modify StepLoadShape
class CustomLoadShape(LoadTestShape):
    def tick(self):
        run_time = self.get_run_time()
        if run_time < 300:
            return (500, 20)  # 500 users, 20 spawn rate
        return None
```

## Distributed Load Testing

For higher load (10,000+ users), use distributed mode:

### Start Master
```bash
locust -f locustfile.py \
  --master \
  --expect-workers 4
```

### Start Workers (on multiple machines)
```bash
# Worker 1
locust -f locustfile.py --worker --master-host=<master-ip>

# Worker 2
locust -f locustfile.py --worker --master-host=<master-ip>

# Worker 3
locust -f locustfile.py --worker --master-host=<master-ip>

# Worker 4
locust -f locustfile.py --worker --master-host=<master-ip>
```

## Interpreting Results

### Response Time Metrics
```
Name                              # reqs      # fails  |   Avg   Min   Max  Median  |   req/s  failures/s
---------------------------------------------------------------------------------------------------------
/api/articles/                      5234           0  |   145    87   654     130  |    87.2        0.00
/api/search/?q=[query]              3421          12  |   423   102  2341     350  |    57.0        0.20
/homepage                           8765           3  |    98    45   432      89  |   146.1        0.05
```

**Good indicators**:
- Low failure count
- Median close to average
- Max not too far from median

**Red flags**:
- High failure rate (>1%)
- Large gap between median and max
- Increasing response times over time

### Resource Utilization
Monitor during tests:
- CPU usage < 70%
- Memory usage < 80%
- Database connections < 80% of pool
- Redis memory < 75% capacity

## Common Issues and Solutions

### High Response Times
**Problem**: p95 > 500ms
**Solutions**:
- Check database query performance
- Review cache hit rate
- Optimize slow endpoints
- Add database indexes
- Scale horizontally

### High Error Rate
**Problem**: Failures > 1%
**Solutions**:
- Check application logs
- Verify database connection pool
- Review timeout settings
- Check rate limiting
- Monitor third-party services

### Memory Leaks
**Problem**: Memory usage increasing over time
**Solutions**:
- Profile application memory
- Check for connection leaks
- Review cache eviction policies
- Monitor Python garbage collection

### Database Bottlenecks
**Problem**: Database CPU/IO high
**Solutions**:
- Optimize slow queries
- Add connection pooling
- Implement read replicas
- Use database caching
- Review indexes

## CI/CD Integration

The load tests are automatically run in CI/CD:

```yaml
# .github/workflows/deploy.yml
- name: Run load tests
  run: |
    locust -f tests/load/locustfile.py \
      --host $DEPLOYMENT_URL \
      --users 1000 \
      --spawn-rate 10 \
      --run-time 5m \
      --headless \
      --html load-test-report.html
```

## Custom Test Scenarios

### Add Custom User Class
```python
class CustomUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def custom_action(self):
        self.client.get('/custom/endpoint/')
```

### Add Custom Load Shape
```python
class SpikeLoadShape(LoadTestShape):
    """Simulate traffic spike"""
    def tick(self):
        run_time = self.get_run_time()
        if run_time < 60:
            return (100, 10)
        elif run_time < 120:
            return (1000, 50)  # Spike!
        elif run_time < 180:
            return (100, 10)
        return None
```

## Monitoring During Tests

### Real-time Metrics
```bash
# Monitor application logs
tail -f logs/application.log

# Monitor database
watch -n 1 'psql -c "SELECT * FROM pg_stat_activity"'

# Monitor Redis
redis-cli --stat

# Monitor system resources
htop
```

### CloudWatch Dashboards
- Application metrics
- Database performance
- Cache hit rates
- Error rates

## Best Practices

1. **Start Small**: Begin with low user count, gradually increase
2. **Monitor Everything**: Watch all metrics during tests
3. **Test Realistic Scenarios**: Match production traffic patterns
4. **Run Regularly**: Weekly or before major releases
5. **Document Results**: Track performance trends over time
6. **Test at Peak Times**: Simulate highest expected load
7. **Include Ramp-Down**: Don't stop tests abruptly
8. **Analyze Failures**: Investigate every failure pattern

## Report Generation

### HTML Report
```bash
locust -f locustfile.py \
  --headless \
  --html report.html \
  --csv results
```

### CSV Export
```bash
locust -f locustfile.py \
  --headless \
  --csv results
```

This generates:
- `results_stats.csv`: Request statistics
- `results_failures.csv`: Failure details
- `results_stats_history.csv`: Time series data

## Troubleshooting

### Locust Not Finding Tests
**Error**: No tasks defined
**Solution**: Ensure classes inherit from `HttpUser` and have `@task` decorators

### Connection Refused
**Error**: Connection to host refused
**Solution**: Verify host URL is correct and accessible

### Timeout Errors
**Error**: Request timeout
**Solution**: Increase timeout in client settings or fix slow endpoints

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://github.com/locustio/locust/wiki/Best-practices)
- OpenLearn Performance Dashboard: https://metrics.openlearn.colombia
