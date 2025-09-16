# 🇨🇴 OpenLearn Colombia - Colombian Open Data Intelligence Platform

## 🎯 Overview

**OpenLearn Colombia** is a comprehensive data intelligence platform that aggregates, analyzes, and provides insights from Colombian open data sources, news media, and government APIs. Built with modern Python and React, this platform serves as a powerful tool for researchers, journalists, analysts, and citizens interested in understanding Colombia through data.

## ✨ Key Features

### 🔍 Data Collection & Integration
- **15+ News Media Scrapers**: Real-time collection from major Colombian news outlets (El Tiempo, El Espectador, Semana, La República, and more)
- **7+ Government API Clients**: Direct integration with Colombian government data sources
  - DANE (National Statistics Department)
  - Banco de la República (Central Bank)
  - SECOP (Public Procurement)
  - IDEAM (Environmental Data)
  - DNP (National Planning Department)
  - MinHacienda (Finance Ministry)
  - Datos.gov.co (Open Data Portal)

### 🧠 Advanced NLP Processing
- **Colombian-specific NER**: Entity recognition optimized for Colombian names, places, and organizations
- **Sentiment Analysis**: Track public opinion and media sentiment on key topics
- **Topic Modeling**: Automatic categorization and trend detection
- **Difficulty Scoring**: Content complexity assessment for educational purposes
- **Vocabulary Extraction**: Build domain-specific glossaries from Colombian content

### 📊 Data Analysis & Visualization
- Real-time dashboards for monitoring news and data trends
- Cross-source correlation and fact-checking capabilities
- Time-series analysis of economic and social indicators
- Geographic mapping of regional data and events

### 🔐 Enterprise Features
- Rate-limited API clients with retry logic and error handling
- Robust caching system for optimal performance
- Comprehensive test suite with 95%+ coverage
- Production-ready configuration management
- Security-first design with authentication and authorization

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Redis (optional, for caching)
- Elasticsearch (optional, for search)
- Node.js 18+ (for frontend)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/bjpl/open_learn_co.git
cd open_learn_co
```

2. **Set up the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize the database**
```bash
python -m alembic upgrade head
```

5. **Start the backend server**
```bash
uvicorn app.main:app --reload --port 8000
```

6. **Set up the frontend** (in a new terminal)
```bash
cd frontend
npm install
npm start
```

7. **Access the application**
- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
open_learn_co/
│
├── backend/                    # Python FastAPI backend
│   ├── app/                   # Main application
│   │   ├── api/              # API endpoints
│   │   ├── config.py         # Configuration management
│   │   ├── database/         # Database models and connections
│   │   └── main.py           # FastAPI application
│   │
│   ├── api_clients/           # Government API integrations
│   │   ├── base/             # Base client with rate limiting
│   │   └── clients/          # Specific API implementations
│   │
│   ├── scrapers/              # News media scrapers
│   │   ├── base/             # Smart scraper base classes
│   │   └── sources/          # Media-specific scrapers
│   │
│   ├── nlp/                   # Natural Language Processing
│   │   ├── colombian_ner.py  # Entity recognition
│   │   ├── sentiment_analyzer.py
│   │   ├── topic_modeler.py
│   │   └── pipeline.py       # Processing pipeline
│   │
│   ├── services/              # Business logic services
│   └── tests/                 # Comprehensive test suite
│
├── frontend/                   # React frontend application
│   ├── public/
│   └── src/
│
└── docs/                      # Documentation and guides
```

## 🔧 Configuration

The platform uses environment variables for configuration. Key settings include:

```env
# Application
APP_NAME=OpenLearn Colombia
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost/openlearn_co

# Security
SECRET_KEY=your-secret-key-here

# APIs (Optional - add your keys)
DANE_API_KEY=
BANREP_API_KEY=

# Services
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200
```

## 📊 API Endpoints

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

## 🧪 Testing

Run the comprehensive test suite:

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

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention
We use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Test additions or fixes
- `refactor:` Code refactoring
- `perf:` Performance improvements

## 📈 Data Sources

### News Media Partners
- **National Media**: El Tiempo, El Espectador, Semana, La República
- **Business Press**: Portafolio, Dinero, La República
- **Regional Media**: El Colombiano, El País, El Heraldo, El Universal
- **Digital Media**: Pulzo, La Silla Vacía, Razón Pública
- **Radio**: La FM, Blu Radio
- **Fact-Checking**: Colombia Check

### Government Data Sources
- **DANE**: Demographics, economy, social indicators
- **Banco de la República**: Monetary policy, exchange rates, inflation
- **SECOP**: Public contracts and procurement
- **IDEAM**: Weather, climate, environmental data
- **DNP**: Development plans, public investment
- **MinHacienda**: Budget, fiscal data
- **Datos.gov.co**: Unified open data portal

## 🔒 Security

- All API endpoints require authentication (except public health checks)
- Rate limiting implemented on all external API calls
- SQL injection protection via parameterized queries
- XSS protection in frontend
- CORS properly configured
- Secrets managed via environment variables
- Regular security audits with `bandit` and `safety`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Colombian government agencies for providing open data APIs
- News media organizations for public access to content
- Open source community for the amazing tools and libraries

## 📧 Contact

- **Repository**: [https://github.com/bjpl/open_learn_co](https://github.com/bjpl/open_learn_co)
- **Issues**: [GitHub Issues](https://github.com/bjpl/open_learn_co/issues)

## 🚦 Project Status

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)

---

**Built with ❤️ for Colombia's data transparency and civic engagement**