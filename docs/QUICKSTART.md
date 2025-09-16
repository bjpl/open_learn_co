# Colombian Platform Quick Start Guide

Get the Colombian Intelligence & Language Learning Platform up and running in 15 minutes.

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Git

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/open_learn.git
cd open_learn
```

### 2. Backend Setup (5 minutes)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

**Essential Environment Variables**:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/colombian_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (optional for testing)
DANE_API_KEY=your_dane_key
SECOP_API_TOKEN=your_secop_token
IDEAM_API_KEY=your_ideam_key
```

### 3. Database Setup

```bash
# Create database
createdb colombian_platform

# Run migrations
cd backend
python manage.py migrate

# Load initial data
python manage.py loaddata fixtures/initial_sources.json
```

### 4. Frontend Setup (3 minutes)

```bash
cd frontend
npm install
npm run build
```

### 5. Start Services (2 minutes)

```bash
# Start Redis (if not running)
redis-server

# Start backend
cd backend
python manage.py runserver

# Start frontend (new terminal)
cd frontend
npm start
```

### 6. Verify Installation

Visit `http://localhost:3000` and you should see the platform dashboard.

## Quick Test Run

### Test API Clients

```bash
cd backend
python -c "
from api_clients.clients.dane_client import DANEClient
import asyncio

async def test():
    client = DANEClient({'base_url': 'https://www.dane.gov.co/api'})
    result = await client.test_connection()
    print('DANE API Test:', result)

asyncio.run(test())
"
```

### Test Scrapers

```bash
python -c "
from scrapers.sources.media.el_tiempo import ElTiempoScraper

scraper = ElTiempoScraper({'base_url': 'https://eltiempo.com'})
print('El Tiempo Scraper initialized successfully')
"
```

### Test Source Manager

```bash
python -c "
from core.source_manager import SourceManager
import asyncio

async def test():
    manager = SourceManager()
    status = manager.get_status()
    print(f'Loaded {status[\"total_sources\"]} sources')

asyncio.run(test())
"
```

## Docker Quick Start (Alternative)

If you prefer Docker:

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access application
open http://localhost:3000
```

## Basic Usage Examples

### 1. Collect Economic Data

```python
from api_clients.clients.dane_client import DANEClient
import asyncio

async def get_economic_data():
    dane = DANEClient()

    # Get latest inflation data
    inflation = await dane.get_inflation_data()
    print(f"Current inflation: {inflation['analysis']['current_rate']}%")

    # Get GDP data
    gdp = await dane.get_gdp_data()
    print(f"GDP data: {gdp}")

asyncio.run(get_economic_data())
```

### 2. Scrape News Articles

```python
from scrapers.sources.media.el_tiempo import ElTiempoScraper
import asyncio

async def scrape_news():
    scraper = ElTiempoScraper()

    # Get latest articles
    articles = scraper.scrape_batch(limit=5)

    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Difficulty: {article['difficulty_score']}/5.0")
        print("---")

asyncio.run(scrape_news())
```

### 3. Start Source Manager

```python
from core.source_manager import SourceManager
import asyncio

async def start_collection():
    manager = SourceManager()

    # Initialize all data collectors
    await manager.initialize_collectors()

    # Start scheduled collection
    manager.schedule_all_sources()

    print("Data collection started!")

asyncio.run(start_collection())
```

## API Usage

### Economic Indicators Endpoint

```bash
curl http://localhost:8000/api/economic/indicators/latest
```

Response:
```json
{
  "inflation": {
    "current_rate": 5.8,
    "monthly_change": 0.4,
    "trend": "decreasing"
  },
  "gdp": {
    "quarterly_growth": 3.2,
    "annual_growth": 4.1
  },
  "employment": {
    "unemployment_rate": 9.2,
    "employment_rate": 90.8
  }
}
```

### News Articles Endpoint

```bash
curl "http://localhost:8000/api/news/articles?source=el_tiempo&limit=10"
```

### Language Learning Endpoint

```bash
curl "http://localhost:8000/api/learning/articles?difficulty=intermediate&topic=economia"
```

## Configuration

### Source Configuration

Edit `backend/config/sources.yaml`:

```yaml
government:
  dane:
    priority: "high"
    update_frequency: "daily"
    rate_limit: "100/minute"

media:
  national:
    el_tiempo:
      priority: "high"
      scraping_interval: 30
      sections: ["politica", "economia"]
```

### Rate Limiting

Adjust rate limits in configuration:

```yaml
rate_limits:
  api_clients:
    default: "100/minute"
    dane: "100/minute"
    secop: "300/minute"

  scrapers:
    default: "5/minute"
    el_tiempo: "5/minute"
    respectful_delay: 10  # seconds
```

### Language Learning Settings

```yaml
language_learning:
  difficulty_scoring:
    enabled: true
    factors: ["sentence_length", "vocabulary", "grammar"]

  entity_extraction:
    enabled: true
    types: ["institutions", "locations", "people"]

  vocabulary_extraction:
    min_frequency: 2
    levels: ["beginner", "intermediate", "advanced"]
```

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# Verify connection
psql $DATABASE_URL
```

**2. Redis Connection Error**
```bash
# Start Redis
redis-server
# Or as service
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

**3. API Rate Limits**
```bash
# Check rate limiter status
python -c "
from api_clients.base.rate_limiter import RateLimiter
limiter = RateLimiter(100)
print(f'Rate limiter status: {limiter.get_status()}')
"
```

**4. Scraper Failures**
```bash
# Test specific scraper
python -c "
import asyncio
from scrapers.sources.media.el_tiempo import ElTiempoScraper

async def test():
    scraper = ElTiempoScraper()
    result = await scraper.test_connection()
    print(f'Scraper test: {result}')

asyncio.run(test())
"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your code here
```

### Health Check

```bash
# Check all systems
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "apis": "operational",
    "scrapers": "active"
  }
}
```

## Development Workflow

### 1. Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/test_integration.py -v
```

### 2. Code Quality

```bash
# Python linting
flake8 backend/
black backend/

# JavaScript linting
cd frontend
npm run lint
npm run format
```

### 3. Hot Reload Development

```bash
# Backend with auto-reload
python manage.py runserver --reload

# Frontend with hot reload
npm run dev
```

### 4. Database Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration status
python manage.py showmigrations
```

## Production Deployment

### Environment Setup

```bash
# Production environment variables
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@prod-db:5432/db
```

### Performance Optimization

```bash
# Optimize database
python manage.py optimize_db

# Cache warming
python manage.py warm_cache

# Static file collection
python manage.py collectstatic
```

### Monitoring

```bash
# Check system status
curl http://localhost:8000/api/status

# View metrics
curl http://localhost:8000/api/metrics
```

## Next Steps

### 1. Explore the API

- Browse to `http://localhost:8000/docs` for API documentation
- Try different endpoints with sample data
- Test language learning features

### 2. Customize Sources

- Add new news sources (see `SCRAPERS_GUIDE.md`)
- Configure additional APIs (see `API_INTEGRATION_GUIDE.md`)
- Adjust collection frequencies

### 3. Language Learning Features

- Test difficulty scoring on different articles
- Explore Colombian entity extraction
- Try vocabulary filtering by level

### 4. Data Analysis

- Query collected economic data
- Analyze news trends
- Generate learning content

### 5. Integration

- Connect to external language learning apps
- Integrate with business intelligence tools
- Set up automated reporting

## Support

### Documentation

- [API Integration Guide](API_INTEGRATION_GUIDE.md)
- [Scrapers Guide](SCRAPERS_GUIDE.md)
- [Data Sources Reference](DATA_SOURCES.md)
- [Architecture Overview](ARCHITECTURE.md)

### Getting Help

1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Join our Discord community
4. Contact support team

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Advanced Features

Once you have the basic system running, explore:

- **Real-time Dashboards**: Economic indicators and news trends
- **AI Analysis**: Automated content classification and sentiment analysis
- **Custom Scrapers**: Add your own data sources
- **Language Learning Paths**: Personalized content progression
- **Alert System**: Economic and political event notifications
- **Data Export**: API endpoints for external integrations

## Performance Tips

- Use Redis caching for frequently accessed data
- Implement rate limiting for external API calls
- Optimize database queries with proper indexing
- Use async/await for concurrent operations
- Monitor memory usage with large scraping operations

You're now ready to explore the Colombian Intelligence & Language Learning Platform!