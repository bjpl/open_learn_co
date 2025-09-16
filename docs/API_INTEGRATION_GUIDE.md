# Colombian Government APIs Integration Guide

This guide covers how to integrate and use the 7 Colombian government API clients in the platform.

## Overview

The platform integrates with key Colombian government data sources to provide real-time economic, statistical, and procurement information:

- **DANE** - National Statistics Department
- **Banco de la República** - Central Bank
- **SECOP** - Public Procurement System
- **Datos Abiertos** - Open Data Portal
- **DNP** - National Planning Department
- **IDEAM** - Weather and Climate Institute
- **MinHacienda** - Ministry of Finance

## Quick Start

### 1. Initialize a Client

```python
from backend.api_clients.clients.dane_client import DANEClient

# Initialize with configuration
config = {
    'base_url': 'https://www.dane.gov.co/api',
    'api_key': 'your_api_key',  # If required
    'rate_limit': 100,  # Requests per minute
    'cache_ttl': 3600   # Cache timeout in seconds
}

dane_client = DANEClient(config)
```

### 2. Fetch Data

```python
# Get inflation data
inflation_data = await dane_client.get_inflation_data(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Get economic dashboard
dashboard = await dane_client.get_economic_dashboard()
```

## API Client Details

### DANE Client (Statistics)

**Purpose**: Access Colombian economic indicators, demographics, and census data.

**Key Endpoints**:
- Inflation (IPC) data
- GDP statistics
- Employment data
- Foreign trade statistics
- Demographic projections

**Example Usage**:

```python
from backend.api_clients.clients.dane_client import DANEClient

client = DANEClient({
    'base_url': 'https://www.dane.gov.co/api',
    'rate_limit': 100
})

# Get latest inflation data
inflation = await client.get_inflation_data()
print(f"Current inflation: {inflation['analysis']['current_rate']}%")

# Get employment statistics for major cities
employment = await client.get_employment_statistics(
    cities=['Bogotá', 'Medellín', 'Cali'],
    include_informal=True
)

# Get GDP data by sector
gdp = await client.get_gdp_data(
    period='quarterly',
    sectors=['agriculture', 'industry', 'services']
)
```

**Response Format**:
```json
{
  "source": "DANE",
  "data": [
    {
      "fecha": "2024-01-01",
      "variacion_anual": 5.8,
      "variacion_mensual": 0.4,
      "indice": 118.45
    }
  ],
  "analysis": {
    "current_rate": 5.8,
    "trend": "decreasing",
    "alert": null
  },
  "extracted_at": "2024-01-15T10:00:00Z"
}
```

### Banco de la República Client (Central Bank)

**Purpose**: Access monetary policy, exchange rates, and economic reports.

**Key Features**:
- Exchange rates (TRM)
- Interest rates
- Monetary policy reports
- Economic research

**Example Usage**:

```python
from backend.api_clients.clients.banrep_client import BancoRepublicaClient

client = BancoRepublicaClient({
    'base_url': 'https://www.banrep.gov.co/api',
    'rate_limit': 200
})

# Get current exchange rates
exchange_rates = await client.get_exchange_rates(
    currencies=['USD', 'EUR'],
    start_date='2024-01-01'
)

# Get interest rates
interest_rates = await client.get_interest_rates()

# Get monetary policy reports
policy_reports = await client.get_policy_reports(
    report_type='monthly'
)
```

### SECOP Client (Public Procurement)

**Purpose**: Access public contract and procurement data.

**Key Features**:
- Contract information
- Tender processes
- Supplier data
- Spending analysis

**Example Usage**:

```python
from backend.api_clients.clients.secop_client import SECOPClient

client = SECOPClient({
    'base_url': 'https://www.colombiacompra.gov.co/api',
    'api_key': 'your_token',
    'rate_limit': 300
})

# Get contracts by entity
contracts = await client.get_contracts(
    entity="Ministerio de Educación",
    status="Adjudicado",
    min_amount=1000000000  # 1 billion COP
)

# Get tender processes
tenders = await client.get_tenders(
    category="Infrastructure",
    state="Open"
)

# Analyze spending by sector
spending = await client.get_spending_analysis(
    groupby="sector",
    year=2024
)
```

### Datos Abiertos Client (Open Data)

**Purpose**: Access Colombia's open data portal with various datasets.

**Key Features**:
- Dataset discovery
- CKAN API integration
- Multiple data formats
- Government transparency data

**Example Usage**:

```python
from backend.api_clients.clients.datos_gov_client import DatosGovClient

client = DatosGovClient({
    'base_url': 'https://www.datos.gov.co/api',
    'rate_limit': 1000
})

# Search datasets
datasets = await client.search_datasets(
    query="contratos públicos",
    organization="SECOP"
)

# Get specific dataset
dataset = await client.get_dataset("contratos-publicos-2024")

# Download dataset resources
resources = await client.get_dataset_resources(
    dataset_id="contratos-publicos-2024",
    format="CSV"
)
```

## Configuration

### Environment Variables

Set these environment variables for API access:

```bash
# DANE API
DANE_API_KEY=your_dane_api_key
DANE_BASE_URL=https://www.dane.gov.co/api

# Banco de la República
BANREP_BASE_URL=https://www.banrep.gov.co/api

# SECOP
SECOP_API_TOKEN=your_secop_token
SECOP_BASE_URL=https://www.colombiacompra.gov.co/api

# Datos Abiertos
DATOS_GOV_BASE_URL=https://www.datos.gov.co/api

# DNP
DNP_BASE_URL=https://www.dnp.gov.co/api

# IDEAM
IDEAM_API_KEY=your_ideam_key
IDEAM_BASE_URL=https://www.ideam.gov.co/api

# MinHacienda
MINHACIENDA_BASE_URL=https://www.minhacienda.gov.co/api
```

### Configuration File

Create `config/api_config.yaml`:

```yaml
api_clients:
  dane:
    base_url: ${DANE_BASE_URL}
    api_key: ${DANE_API_KEY}
    rate_limit: 100
    timeout: 30
    retry_attempts: 3
    cache_ttl: 3600

  banco_republica:
    base_url: ${BANREP_BASE_URL}
    rate_limit: 200
    timeout: 30
    retry_attempts: 3
    cache_ttl: 1800

  secop:
    base_url: ${SECOP_BASE_URL}
    api_token: ${SECOP_API_TOKEN}
    rate_limit: 300
    timeout: 45
    retry_attempts: 5
    cache_ttl: 7200

  datos_gov:
    base_url: ${DATOS_GOV_BASE_URL}
    rate_limit: 1000
    timeout: 60
    cache_ttl: 3600
```

## Error Handling

### Common Error Types

1. **Rate Limiting**: APIs have rate limits to prevent abuse
2. **Authentication Errors**: Invalid or missing API keys
3. **Data Unavailable**: Temporary service interruptions
4. **Format Changes**: API response format updates

### Error Handling Example

```python
from backend.api_clients.base.exceptions import (
    RateLimitExceeded,
    AuthenticationError,
    DataUnavailable
)

try:
    data = await dane_client.get_inflation_data()
except RateLimitExceeded:
    # Wait and retry
    await asyncio.sleep(60)
    data = await dane_client.get_inflation_data()
except AuthenticationError:
    # Check API credentials
    logger.error("Invalid API credentials")
except DataUnavailable:
    # Use cached data or alternative source
    data = await get_cached_inflation_data()
```

## Rate Limiting

Each API has different rate limits:

| API | Rate Limit | Authentication |
|-----|------------|----------------|
| DANE | 100/minute | API Key (optional) |
| Banco República | 200/minute | None |
| SECOP | 300/minute | Token Required |
| Datos Abiertos | 1000/minute | None |
| DNP | 50/minute | None |
| IDEAM | 100/minute | API Key |
| MinHacienda | 100/minute | None |

### Rate Limiting Implementation

```python
from backend.api_clients.base.rate_limiter import RateLimiter

# Automatic rate limiting
client = DANEClient({
    'rate_limit': 100,  # Requests per minute
    'rate_limit_strategy': 'token_bucket'
})

# Manual rate limiting
rate_limiter = RateLimiter(100)  # 100 requests per minute

await rate_limiter.acquire()  # Wait if necessary
data = await make_api_request()
```

## Caching

### Response Caching

```python
# Configure caching
client = DANEClient({
    'cache_ttl': 3600,  # 1 hour
    'cache_strategy': 'memory'  # or 'redis'
})

# Cache key based on endpoint and parameters
cache_key = client.get_cache_key('/indices/ipc', {'fecha': '2024-01'})
```

### Cache Strategies

1. **Memory Cache**: Fast, limited capacity
2. **Redis Cache**: Shared across instances
3. **File Cache**: Persistent across restarts

## Monitoring and Alerts

### Performance Monitoring

```python
# Monitor API response times
await client.get_inflation_data()
metrics = client.get_performance_metrics()

print(f"Average response time: {metrics['avg_response_time']}ms")
print(f"Success rate: {metrics['success_rate']}%")
```

### Economic Alerts

```python
# Set up economic alerts
alerts = dane_client._check_economic_alerts([
    {'data': {'variacion_mensual': 1.5}}  # High inflation alert
])

for alert in alerts:
    if alert['severity'] == 'high':
        notify_economic_team(alert)
```

## Data Processing Pipeline

### 1. Raw Data Collection

```python
async def collect_all_economic_data():
    """Collect data from all economic APIs"""
    tasks = [
        dane_client.get_inflation_data(),
        dane_client.get_gdp_data(),
        banrep_client.get_exchange_rates(),
        banrep_client.get_interest_rates()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return process_economic_results(results)
```

### 2. Data Transformation

```python
def transform_api_data(raw_data, source_type):
    """Transform raw API data to standard format"""
    transformed = {
        'source': source_type,
        'timestamp': datetime.utcnow().isoformat(),
        'data': standardize_data_format(raw_data),
        'quality_score': assess_data_quality(raw_data)
    }
    return transformed
```

### 3. Data Storage

```python
async def store_economic_data(transformed_data):
    """Store processed data in database"""
    async with database.transaction():
        await database.execute(
            "INSERT INTO economic_indicators ...",
            transformed_data
        )
```

## Testing

### Unit Tests

```python
import pytest
from backend.api_clients.clients.dane_client import DANEClient

@pytest.mark.asyncio
async def test_dane_inflation_data(mock_aiohttp):
    mock_aiohttp.get(
        'https://test.dane.gov.co/api/indices/ipc',
        payload={'resultado': [{'variacion_anual': 5.8}]}
    )

    client = DANEClient({'base_url': 'https://test.dane.gov.co/api'})
    result = await client.get_inflation_data()

    assert result['source'] == 'DANE'
    assert 'analysis' in result
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_economic_dashboard_integration():
    """Test complete economic dashboard data collection"""

    # Test with real API endpoints (if available)
    dashboard = await collect_economic_dashboard()

    assert 'inflation' in dashboard['indicators']
    assert 'gdp' in dashboard['indicators']
    assert 'exchange_rates' in dashboard['indicators']
```

## Best Practices

### 1. Async Operations

Always use async/await for API calls:

```python
# Good
data = await client.get_inflation_data()

# Bad - blocking
data = client.get_inflation_data_sync()
```

### 2. Error Handling

Handle specific exceptions:

```python
try:
    data = await client.fetch_data()
except RateLimitExceeded:
    await asyncio.sleep(60)
    data = await client.fetch_data()
except DataUnavailable:
    data = get_fallback_data()
```

### 3. Resource Management

Close connections properly:

```python
async with DANEClient(config) as client:
    data = await client.get_inflation_data()
# Connection automatically closed
```

### 4. Configuration Management

Use environment-specific configs:

```python
# Load config based on environment
config = load_api_config(environment='production')
client = DANEClient(config['dane'])
```

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Increase timeout values
   - Check network connectivity
   - Verify API endpoint availability

2. **Authentication Failures**
   - Verify API keys/tokens
   - Check expiration dates
   - Confirm API permissions

3. **Rate Limit Exceeded**
   - Implement exponential backoff
   - Reduce request frequency
   - Use caching effectively

4. **Data Format Changes**
   - Monitor API version updates
   - Implement flexible parsing
   - Add data validation

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('api_clients')

client = DANEClient(config)
client.set_debug_mode(True)
```

## API Endpoints Reference

### DANE Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/indices/ipc` | Inflation data | start_date, end_date |
| `/cuentas/pib` | GDP statistics | period, sectors |
| `/mercado-laboral/empleo` | Employment | cities, include_informal |
| `/comercio/exterior` | Foreign trade | countries, products |

### Banco República Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/tasas-cambio` | Exchange rates | currencies, date_range |
| `/tasas-interes` | Interest rates | rate_type |
| `/politica-monetaria` | Policy reports | report_type, year |

### SECOP Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `/contratos` | Contract data | entity, status, amount |
| `/procesos` | Tender processes | category, state |
| `/proveedores` | Supplier data | sector, region |

For detailed API documentation, visit each agency's developer portal or contact the platform maintainers.