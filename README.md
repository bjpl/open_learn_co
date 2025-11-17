# OpenLearn Colombia

A comprehensive data intelligence platform for aggregating, analyzing, and providing insights from Colombian open data sources.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

OpenLearn Colombia is a data intelligence platform that integrates news media scrapers, government API clients, and advanced natural language processing to provide comprehensive insights into Colombian data. Built with Python FastAPI and React, the platform serves researchers, journalists, analysts, and citizens interested in understanding Colombia through data.

The platform employs a monorepo architecture with dedicated frontend and backend workspaces, offering real-time data collection from over 15 news sources and 7 government APIs.

## Features

### Data Collection and Integration

- Real-time collection from 15 major Colombian news outlets including El Tiempo, El Espectador, Semana, and La República
- Direct integration with 7 government data sources: DANE, Banco de la República, SECOP, IDEAM, DNP, MinHacienda, and Datos.gov.co
- Automated web scraping with rate limiting and error handling
- Robust caching system for optimal performance

### Natural Language Processing

- Colombian-specific named entity recognition optimized for local names, places, and organizations
- Sentiment analysis for tracking public opinion and media sentiment
- Topic modeling with automatic categorization and trend detection
- Content difficulty scoring for educational assessment
- Domain-specific vocabulary extraction from Colombian content

### Data Analysis and Visualization

- Real-time dashboards for monitoring news and data trends
- Cross-source correlation and fact-checking capabilities
- Time-series analysis of economic and social indicators
- Geographic mapping of regional data and events

### Enterprise Features

- Rate-limited API clients with retry logic
- Comprehensive test suite with 95%+ coverage
- Production-ready configuration management
- Authentication and authorization security

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 14 or higher
- Node.js 18 or higher
- Redis (optional, for caching)
- Elasticsearch (optional, for search)

### Setup

Clone the repository:
```bash
git clone https://github.com/bjpl/open_learn_co.git
cd open_learn_co
```

Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configure environment variables:
```bash
cp .env.example .env
# Edit .env with configuration settings
```

Initialize the database:
```bash
python -m alembic upgrade head
```

Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

Set up the frontend:
```bash
cd frontend
npm install
npm start
```

Access the application:
- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## Usage

The platform provides access through a RESTful API and web-based dashboard interface. API endpoints allow programmatic access to collected data, analysis results, and trending topics. The dashboard provides visual interfaces for exploring data sources, monitoring trends, and analyzing content.

## Project Structure

```
open_learn_co/
├── backend/                    # Python FastAPI backend
│   ├── app/                   # Main application
│   │   ├── api/              # API endpoints
│   │   ├── config.py         # Configuration management
│   │   ├── database/         # Database models and connections
│   │   └── main.py           # FastAPI application
│   ├── api_clients/           # Government API integrations
│   │   ├── base/             # Base client with rate limiting
│   │   └── clients/          # Specific API implementations
│   ├── scrapers/              # News media scrapers
│   │   ├── base/             # Smart scraper base classes
│   │   └── sources/          # Media-specific scrapers
│   ├── nlp/                   # Natural Language Processing
│   │   ├── colombian_ner.py  # Entity recognition
│   │   ├── sentiment_analyzer.py
│   │   ├── topic_modeler.py
│   │   └── pipeline.py       # Processing pipeline
│   ├── services/              # Business logic services
│   └── tests/                 # Comprehensive test suite
├── frontend/                   # React frontend application
│   ├── public/
│   └── src/
└── docs/                      # Documentation and guides
```

## Development

### Backend Development

The backend uses FastAPI with asynchronous request handling for optimal performance. Database models are managed with SQLAlchemy, and migrations are handled through Alembic.

### Frontend Development

The React frontend provides interactive dashboards and visualization components. Development follows modern React patterns with hooks and functional components.

### Running Tests

Backend tests with Python:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_api_clients.py

# Run tests in parallel
pytest -n auto
```

Frontend tests with Jest and Vitest:
```bash
npm test                  # Run all tests
npm run test:unit         # Unit tests
npm run test:integration  # Integration tests
```

## API Documentation

### Core Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/sources` - List available data sources
- `GET /api/v1/articles` - Retrieve news articles
- `GET /api/v1/data/{source}` - Get data from specific source
- `POST /api/v1/analyze` - Analyze text or documents
- `GET /api/v1/trends` - Current trending topics

### Government Data APIs

- `/api/v1/dane/` - National statistics data
- `/api/v1/banrep/` - Central bank indicators
- `/api/v1/secop/` - Public procurement data
- `/api/v1/ideam/` - Environmental data

Complete API documentation is available at the `/docs` endpoint when running the backend server.

## Testing

The project maintains a comprehensive test suite with 95%+ coverage. Tests include unit tests for individual components, integration tests for API endpoints, and end-to-end tests for critical workflows.

Testing infrastructure uses Jest and Vitest for the frontend, and pytest for the backend, ensuring code quality and reliability across both platforms.

## Security

Security measures include:

- Authentication required for all API endpoints except public health checks
- Rate limiting on external API calls
- SQL injection protection via parameterized queries
- XSS protection in frontend components
- Properly configured CORS policies
- Environment variable management for secrets
- Regular security audits with bandit and safety tools

## Deployment

The project is configured for deployment on Vercel with automatic CI/CD integration. Production deployment includes automated testing, build optimization, and environment configuration management.

## Contributing

Contributions are welcome. Please follow the conventional commit format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Test additions or fixes
- `refactor:` Code refactoring
- `perf:` Performance improvements

Submit pull requests with clear descriptions of proposed changes.

## License

This project is available under the MIT License. See LICENSE file for details.
