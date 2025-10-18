# Health Check Endpoints

Comprehensive health check system for monitoring OpenLearn platform dependencies and system status.

## Overview

The health check system provides detailed monitoring for:
- PostgreSQL database connectivity and performance
- Redis cache availability and hit rates
- Elasticsearch search functionality (optional)
- File system access and disk space
- Overall system health scoring

## Health Check Endpoints

### Basic Health Check

**Endpoint:** `GET /health`

Simple health check that always returns 200 if the service is running.

**Response:**
```json
{
  "status": "ok",
  "service": "openlearn"
}
```

**Use case:** Basic monitoring, load balancer health checks

---

### Kubernetes Liveness Probe

**Endpoint:** `GET /health/live`

Checks if the service is alive and not deadlocked. Returns 200 if alive, 503 if dead.

**Response:**
```json
{
  "alive": true,
  "status": "healthy",
  "timestamp": "2025-10-17T12:34:56.789Z"
}
```

**Kubernetes Configuration:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

---

### Kubernetes Readiness Probe

**Endpoint:** `GET /health/ready`

Checks if the service is ready to accept traffic. Returns 200 if ready, 503 if not ready.

**Response (Ready):**
```json
{
  "ready": true,
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "details": {
        "connection": {"status": "healthy"},
        "pool": {"status": "healthy"},
        "query_performance_ms": 25.5
      },
      "response_time_ms": 45.2
    },
    "redis": {
      "status": "healthy",
      "details": {
        "connected": true,
        "total_keys": 1250,
        "hit_rate_percent": 82.5
      },
      "response_time_ms": 12.3
    }
  },
  "timestamp": "2025-10-17T12:34:56.789Z",
  "response_time_ms": 58.5
}
```

**Response (Not Ready):**
Returns HTTP 503 with details about which checks failed.

**Kubernetes Configuration:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

### Kubernetes Startup Probe

**Endpoint:** `GET /health/startup`

Checks if the application has finished starting up. More lenient timeouts than readiness probe.

**Response:**
```json
{
  "started": true,
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  },
  "timestamp": "2025-10-17T12:34:56.789Z",
  "response_time_ms": 95.3
}
```

**Kubernetes Configuration:**
```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 10
  failureThreshold: 12  # 60 seconds total startup time
```

---

### Comprehensive Health Check

**Endpoint:** `GET /health/comprehensive`

Detailed health check for all system dependencies with health scoring.

**Response:**
```json
{
  "status": "healthy",
  "health_score": 92.5,
  "timestamp": "2025-10-17T12:34:56.789Z",
  "checks": {
    "database": {
      "status": "healthy",
      "details": {
        "connection": {"status": "healthy", "message": "Connected"},
        "pool": {
          "status": "healthy",
          "details": {
            "size": 10,
            "checked_out": 2,
            "overflow": 0
          }
        },
        "query_performance_ms": 25.5
      },
      "response_time_ms": 45.2
    },
    "redis": {
      "status": "healthy",
      "details": {
        "connected": true,
        "total_keys": 1250,
        "memory_used_mb": 45.2,
        "hit_rate_percent": 82.5
      },
      "response_time_ms": 12.3
    },
    "elasticsearch": {
      "status": "healthy",
      "details": {
        "cluster_status": "green",
        "number_of_nodes": 3,
        "active_shards": 15
      },
      "response_time_ms": 35.8
    },
    "filesystem": {
      "status": "healthy",
      "details": {
        "writable": true,
        "readable": true,
        "free_space_gb": 125.3
      },
      "response_time_ms": 2.1
    }
  },
  "response_time_ms": 95.4,
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Health Status Values

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `healthy` | Component is functioning normally | None |
| `degraded` | Component is functioning but with issues | Monitor closely |
| `unhealthy` | Component has failed | Immediate action required |
| `timeout` | Health check exceeded timeout | Check component performance |
| `unavailable` | Component not configured or not connected | Configuration needed |

---

## Health Score Calculation

Health score is calculated from 0-100 based on component health:

**Component Weights:**
- Database: 40%
- Redis: 30%
- Elasticsearch: 15%
- Filesystem: 15%

**Status Scores:**
- Healthy: 100 points
- Degraded: 50 points
- Unavailable: 25 points
- Timeout/Unhealthy: 0 points

**Example:**
```
Database (healthy): 100 * 0.4 = 40
Redis (healthy): 100 * 0.3 = 30
Elasticsearch (degraded): 50 * 0.15 = 7.5
Filesystem (healthy): 100 * 0.15 = 15
---
Total Health Score: 92.5
```

---

## Timeout Configuration

Each health check has configurable timeouts to prevent hanging:

| Check | Default Timeout | Environment Variable |
|-------|----------------|---------------------|
| Database | 5.0s | `DATABASE_HEALTH_TIMEOUT` |
| Redis | 3.0s | `REDIS_HEALTH_TIMEOUT` |
| Elasticsearch | 5.0s | `ELASTICSEARCH_HEALTH_TIMEOUT` |
| Filesystem | N/A (local) | N/A |

Timeouts can be adjusted via environment variables or in the health check requests.

---

## Monitoring Integration

### Prometheus

The health check endpoints can be scraped by Prometheus for alerting:

```yaml
scrape_configs:
  - job_name: 'openlearn-health'
    metrics_path: '/health/comprehensive'
    scrape_interval: 30s
    static_configs:
      - targets: ['openlearn:8000']
```

### Alertmanager Rules

Example alerting rules:

```yaml
groups:
  - name: openlearn_health
    rules:
      - alert: OpenLearnUnhealthy
        expr: health_score < 50
        for: 5m
        annotations:
          summary: "OpenLearn health score below 50%"

      - alert: DatabaseUnhealthy
        expr: database_status != "healthy"
        for: 2m
        annotations:
          summary: "Database health check failing"
```

---

## Troubleshooting

### Database Unhealthy

**Symptoms:**
- `/health/ready` returns 503
- Database status shows "unhealthy" or "timeout"

**Checks:**
1. Verify database is running: `kubectl get pods -l app=postgres`
2. Check connection string in secrets
3. Review database logs: `kubectl logs <postgres-pod>`
4. Test connection from pod: `kubectl exec <pod> -- psql $DATABASE_URL -c "SELECT 1"`

---

### Redis Degraded

**Symptoms:**
- Redis shows "degraded" status
- Low cache hit rate (<50%)

**Checks:**
1. Review cache hit rate in `/health/cache` endpoint
2. Check if cache is being properly populated
3. Verify cache TTL settings are appropriate
4. Monitor memory usage

---

### Elasticsearch Unavailable

**Symptoms:**
- Elasticsearch shows "unavailable" or "degraded"
- Search features not working

**Checks:**
1. Verify Elasticsearch is running (if configured)
2. Check `ELASTICSEARCH_ENABLED` setting
3. Review Elasticsearch cluster health
4. Check network connectivity to Elasticsearch

**Note:** Elasticsearch is optional - system will show degraded but remain functional.

---

### Filesystem Issues

**Symptoms:**
- Filesystem shows "unhealthy"
- Low disk space warnings

**Checks:**
1. Check disk space: `kubectl exec <pod> -- df -h`
2. Review temporary file cleanup
3. Check volume mounts in deployment
4. Monitor disk usage over time

---

## Legacy Endpoints

The following endpoints are maintained for backward compatibility:

- `GET /health/database` - Database-specific health
- `GET /health/database/stats` - Database statistics
- `GET /health/database/pool` - Connection pool status
- `GET /health/cache` - Redis cache statistics
- `GET /health/compression` - Compression middleware stats

These endpoints provide more detailed information for specific components.

---

## Best Practices

1. **Use startup probes** for slow-starting applications
2. **Set appropriate timeouts** to avoid false positives
3. **Monitor health scores** over time to detect degradation
4. **Alert on patterns** rather than single failures
5. **Test health checks** in staging before production
6. **Document dependencies** and their criticality
7. **Plan for graceful degradation** when optional services fail

---

## Security Considerations

1. Health check endpoints are **unauthenticated** by design for Kubernetes
2. Endpoints do **not expose sensitive information** (secrets, keys)
3. Detailed error messages are **logged** but not returned in responses
4. Consider **rate limiting** health check endpoints if exposed publicly
5. Use **network policies** to restrict access in production

---

## Example Usage

### curl

```bash
# Basic health check
curl http://localhost:8000/health

# Comprehensive check
curl http://localhost:8000/health/comprehensive | jq '.'

# Check readiness
curl -i http://localhost:8000/health/ready

# Check liveness
curl http://localhost:8000/health/live
```

### Python

```python
import requests

response = requests.get("http://localhost:8000/health/comprehensive")
health = response.json()

if health["health_score"] < 80:
    print(f"Warning: Health score is {health['health_score']}")
    for component, status in health["checks"].items():
        if status["status"] != "healthy":
            print(f"  {component}: {status['status']}")
```

### Kubernetes

```bash
# Check pod readiness
kubectl get pods -l app=openlearn

# View health check logs
kubectl logs -l app=openlearn --tail=100 | grep health

# Execute health check from within pod
kubectl exec <pod-name> -- curl localhost:8000/health/comprehensive
```
