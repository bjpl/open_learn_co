# Colombian Platform System Architecture

This document provides a comprehensive overview of the Colombian Intelligence & Language Learning Platform architecture, covering all components, data flows, and integration patterns.

## System Overview

The platform is a distributed, microservices-oriented system designed to collect, process, and serve Colombian data for intelligence gathering and Spanish language learning.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Applications  │
│                 │    │    Pipeline     │    │                 │
│ • 7 Gov APIs    │    │                 │    │ • Web Dashboard │
│ • 18 News Sites │───▶│ • Collection    │───▶│ • Mobile App    │
│ • 8 Academic    │    │ • Processing    │    │ • API Endpoints │
│ • 9 Other       │    │ • Storage       │    │ • Integrations  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Data Collection Layer**
   - API Clients (7 government APIs)
   - Web Scrapers (18+ news sources)
   - Source Manager (orchestration)

2. **Processing Layer**
   - NLP Pipeline (entity extraction, difficulty scoring)
   - Data Transformation
   - Quality Assurance

3. **Storage Layer**
   - PostgreSQL (structured data)
   - Redis (caching, sessions)
   - File System (raw content, logs)

4. **Application Layer**
   - REST API (FastAPI/Django)
   - Web Dashboard (React)
   - Background Jobs (Celery)

5. **Infrastructure Layer**
   - Load Balancer
   - Application Servers
   - Database Cluster
   - Monitoring & Logging

## Detailed Architecture

### Data Collection Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Source Manager                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Scheduler │  │ Rate Limiter│  │ Health Check│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │   API   │  │  Web    │  │ Smart   │
    │ Clients │  │Scrapers │  │Scrapers │
    └─────────┘  └─────────┘  └─────────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │  DANE   │  │El Tiempo│  │ AI-Based│
    │BancoRep │  │El Espec │  │ Content │
    │ SECOP   │  │ Semana  │  │Extractor│
    │  etc.   │  │  etc.   │  │         │
    └─────────┘  └─────────┘  └─────────┘
```

#### API Client Architecture

```python
BaseAPIClient
    ├── Authentication Handler
    ├── Rate Limiter
    ├── Request Manager
    ├── Response Parser
    ├── Error Handler
    └── Cache Manager

Specialized Clients:
    ├── DANEClient (Statistics)
    ├── BancoRepublicaClient (Economic)
    ├── SECOPClient (Procurement)
    ├── DatosGovClient (Open Data)
    ├── DNPClient (Planning)
    ├── IDEAMClient (Weather)
    └── MinHaciendaClient (Fiscal)
```

#### Scraper Architecture

```python
BaseScraper
    ├── HTTP Client (aiohttp)
    ├── HTML Parser (BeautifulSoup)
    ├── Rate Limiter
    ├── Content Validator
    ├── Error Handler
    └── Cache Manager

Specialized Scrapers:
    ├── ElTiempoScraper
    ├── ElEspectadorScraper
    ├── SemanaScraper
    ├── RegionalScrapers
    └── SpecializedScrapers

SmartScraper (AI-powered)
    ├── Content Structure Detection
    ├── Automatic Selector Generation
    ├── Adaptive Parsing
    └── Machine Learning Models
```

### Data Processing Pipeline

```
Raw Data → Validation → Transformation → NLP Processing → Storage
    │           │            │             │              │
    │           │            │             │              ▼
    │           │            │             │         ┌──────────┐
    │           │            │             │         │PostgreSQL│
    │           │            │             │         │   Main   │
    │           │            │             │         │ Database │
    │           │            │             │         └──────────┘
    │           │            │             │              │
    │           │            │             │              ▼
    │           │            │             │         ┌──────────┐
    │           │            │             │         │  Redis   │
    │           │            │             │         │  Cache   │
    │           │            │             │         └──────────┘
    │           │            │             │
    │           │            │             ▼
    │           │            │    ┌─────────────────┐
    │           │            │    │ NLP Processing  │
    │           │            │    │ • Entity Extr.  │
    │           │            │    │ • Difficulty    │
    │           │            │    │ • Sentiment     │
    │           │            │    │ • Keywords      │
    │           │            │    └─────────────────┘
    │           │            │
    │           │            ▼
    │           │    ┌─────────────────┐
    │           │    │ Data Transform  │
    │           │    │ • Standardize   │
    │           │    │ • Enrich        │
    │           │    │ • Categorize    │
    │           │    └─────────────────┘
    │           │
    │           ▼
    │    ┌─────────────────┐
    │    │   Validation    │
    │    │ • Schema Check  │
    │    │ • Quality Score │
    │    │ • Duplicate Det │
    │    └─────────────────┘
    │
    ▼
┌─────────────────┐
│   Raw Input     │
│ • API Response  │
│ • HTML Content  │
│ • Structured    │
└─────────────────┘
```

#### NLP Processing Architecture

```python
NLP Pipeline:
    ├── Text Preprocessing
    │   ├── Cleaning (remove HTML, normalize)
    │   ├── Tokenization
    │   └── Language Detection
    │
    ├── Entity Extraction
    │   ├── Colombian Institutions
    │   ├── Geographic Locations
    │   ├── Political Figures
    │   └── Economic Terms
    │
    ├── Language Learning Features
    │   ├── Difficulty Scoring
    │   ├── Vocabulary Extraction
    │   ├── Grammar Complexity
    │   └── Reading Level
    │
    ├── Content Analysis
    │   ├── Sentiment Analysis
    │   ├── Topic Classification
    │   ├── Keyword Extraction
    │   └── Summary Generation
    │
    └── Colombian Context
        ├── Regional Dialect Detection
        ├── Cultural References
        ├── Historical Context
        └── Political Mapping
```

### Storage Architecture

#### Database Schema

```sql
-- Core content tables
articles (
    id, title, content, url, source, published_date,
    author, category, difficulty_score, word_count,
    extracted_entities, metadata, created_at
)

economic_indicators (
    id, indicator_type, value, date, source,
    metadata, analysis, alerts, created_at
)

government_data (
    id, source, data_type, data, extracted_at,
    quality_score, metadata, processed_at
)

-- Language learning tables
vocabulary (
    id, word, definition, level, frequency,
    source_articles, examples, created_at
)

learning_paths (
    id, user_id, current_level, topics,
    progress, recommended_content
)

-- System tables
sources (
    id, name, type, priority, config,
    status, last_updated, metrics
)

collection_jobs (
    id, source_id, status, started_at,
    completed_at, items_collected, errors
)
```

#### Caching Strategy

```python
Redis Cache Layers:
    ├── L1: Request Cache (1 hour TTL)
    │   ├── API Responses
    │   ├── Web Pages
    │   └── Search Results
    │
    ├── L2: Processed Data (24 hour TTL)
    │   ├── Article Summaries
    │   ├── Entity Extractions
    │   └── Difficulty Scores
    │
    ├── L3: Aggregated Data (7 day TTL)
    │   ├── Economic Dashboards
    │   ├── News Trends
    │   └── Learning Analytics
    │
    └── Session Storage (30 day TTL)
        ├── User Sessions
        ├── Learning Progress
        └── Preferences
```

### Application Architecture

#### Backend API Structure

```
backend/
├── api/                    # API endpoints
│   ├── economic/          # Economic data endpoints
│   ├── news/              # News content endpoints
│   ├── learning/          # Language learning endpoints
│   └── admin/             # Administration endpoints
│
├── api_clients/           # External API integrations
│   ├── base/              # Base client functionality
│   └── clients/           # Specific API clients
│
├── scrapers/              # Web scraping components
│   ├── base/              # Base scraper classes
│   └── sources/           # Source-specific scrapers
│
├── core/                  # Core business logic
│   ├── source_manager.py  # Orchestration
│   ├── nlp_pipeline.py    # Text processing
│   └── quality_control.py # Data validation
│
├── models/                # Database models
├── services/              # Business services
├── utils/                 # Utility functions
└── config/                # Configuration files
```

#### Frontend Architecture

```
frontend/
├── src/
│   ├── components/        # Reusable components
│   │   ├── Dashboard/     # Dashboard components
│   │   ├── Learning/      # Learning interface
│   │   ├── News/          # News display
│   │   └── Charts/        # Data visualization
│   │
│   ├── pages/             # Page components
│   │   ├── Dashboard.js   # Main dashboard
│   │   ├── Learning.js    # Learning interface
│   │   ├── News.js        # News browser
│   │   └── Analytics.js   # Analytics page
│   │
│   ├── services/          # API services
│   │   ├── api.js         # API client
│   │   ├── auth.js        # Authentication
│   │   └── websocket.js   # Real-time updates
│   │
│   ├── store/             # State management
│   │   ├── economic.js    # Economic data store
│   │   ├── news.js        # News data store
│   │   └── learning.js    # Learning progress store
│   │
│   └── utils/             # Utility functions
│
└── public/                # Static assets
```

### Security Architecture

#### Authentication & Authorization

```
Authentication Flow:
User → Login → JWT Token → API Access

Authorization Levels:
├── Public (read-only access to news)
├── Registered (personalized learning)
├── Premium (full data access)
└── Admin (system management)

Security Measures:
├── JWT Token Authentication
├── Rate Limiting per User/IP
├── Input Validation & Sanitization
├── SQL Injection Prevention
├── XSS Protection
├── CORS Configuration
└── HTTPS Enforcement
```

#### Data Security

```python
Security Layers:
    ├── Network Security
    │   ├── VPC/Private Networks
    │   ├── Firewall Rules
    │   └── Load Balancer SSL
    │
    ├── Application Security
    │   ├── Input Validation
    │   ├── Output Sanitization
    │   ├── Authentication
    │   └── Authorization
    │
    ├── Data Security
    │   ├── Encryption at Rest
    │   ├── Encryption in Transit
    │   ├── Database Access Control
    │   └── Backup Encryption
    │
    └── Operational Security
        ├── Audit Logging
        ├── Intrusion Detection
        ├── Vulnerability Scanning
        └── Security Monitoring
```

### Scalability Architecture

#### Horizontal Scaling

```
Load Balancer
    ├── App Server 1 (Primary)
    ├── App Server 2 (Secondary)
    └── App Server N (Auto-scaling)

Database Cluster
    ├── Primary (Read/Write)
    ├── Replica 1 (Read-only)
    └── Replica N (Read-only)

Cache Cluster
    ├── Redis Master
    └── Redis Replicas

Background Jobs
    ├── Celery Worker 1
    ├── Celery Worker 2
    └── Celery Worker N
```

#### Performance Optimization

```python
Optimization Strategies:
    ├── Database
    │   ├── Query Optimization
    │   ├── Index Management
    │   ├── Connection Pooling
    │   └── Partition Tables
    │
    ├── Caching
    │   ├── Redis Cache
    │   ├── CDN for Static Assets
    │   ├── Application-level Cache
    │   └── Database Query Cache
    │
    ├── Application
    │   ├── Async/Await Processing
    │   ├── Batch Operations
    │   ├── Connection Pooling
    │   └── Resource Management
    │
    └── Infrastructure
        ├── Auto-scaling Groups
        ├── Load Balancing
        ├── Geographic Distribution
        └── Edge Caching
```

### Monitoring Architecture

#### System Monitoring

```
Monitoring Stack:
    ├── Application Metrics
    │   ├── API Response Times
    │   ├── Error Rates
    │   ├── Throughput
    │   └── Resource Usage
    │
    ├── Infrastructure Metrics
    │   ├── Server Performance
    │   ├── Database Performance
    │   ├── Network Metrics
    │   └── Storage Metrics
    │
    ├── Business Metrics
    │   ├── Data Collection Rates
    │   ├── Content Quality Scores
    │   ├── User Engagement
    │   └── Learning Progress
    │
    └── Alerting
        ├── Performance Degradation
        ├── System Failures
        ├── Data Quality Issues
        └── Security Events
```

#### Logging Architecture

```python
Logging Levels:
    ├── Error Logs
    │   ├── System Errors
    │   ├── API Failures
    │   ├── Data Processing Errors
    │   └── Security Incidents
    │
    ├── Warning Logs
    │   ├── Performance Issues
    │   ├── Rate Limit Approaches
    │   ├── Data Quality Issues
    │   └── Resource Constraints
    │
    ├── Info Logs
    │   ├── System Operations
    │   ├── Data Collection Events
    │   ├── User Activities
    │   └── Configuration Changes
    │
    └── Debug Logs
        ├── Detailed Tracing
        ├── Development Info
        └── Troubleshooting Data

Log Storage:
    ├── Local Files (rotating)
    ├── Centralized Logging (ELK Stack)
    ├── Metrics Storage (InfluxDB)
    └── Alert Manager
```

### Deployment Architecture

#### Environment Structure

```
Environments:
    ├── Development
    │   ├── Local Docker Compose
    │   ├── Shared Development Database
    │   ├── Mock External APIs
    │   └── Debug Logging
    │
    ├── Staging
    │   ├── Production-like Environment
    │   ├── Real API Connections
    │   ├── Performance Testing
    │   └── Integration Testing
    │
    └── Production
        ├── High Availability Setup
        ├── Auto-scaling
        ├── Monitoring & Alerting
        └── Backup & Recovery
```

#### Container Architecture

```yaml
# Docker Compose Structure
services:
  api:
    image: colombian-platform/api
    depends_on: [database, redis]
    environment: [DATABASE_URL, REDIS_URL]

  worker:
    image: colombian-platform/worker
    depends_on: [database, redis]
    command: celery worker

  scheduler:
    image: colombian-platform/scheduler
    depends_on: [database, redis]
    command: celery beat

  database:
    image: postgres:14
    volumes: [db-data:/var/lib/postgresql/data]

  redis:
    image: redis:6
    volumes: [redis-data:/data]

  frontend:
    image: colombian-platform/frontend
    depends_on: [api]
    ports: ["3000:3000"]
```

### Data Flow Architecture

#### Real-time Data Flow

```
External Sources → Collection → Processing → Storage → API → Frontend
                     ↓              ↓          ↓       ↓       ↓
                 Rate Limit → Validation → Cache → Serve → Display
                     ↓              ↓          ↓       ↓       ↓
                 Schedule → Transform → Index → Query → Render
```

#### Batch Processing Flow

```
Scheduled Jobs → Source Manager → Parallel Collection → Queue Processing
       ↓               ↓                ↓                    ↓
   Cron/Celery → Initialize → API Clients & Scrapers → Background Jobs
       ↓               ↓                ↓                    ↓
   Job Queue → Health Check → Concurrent Requests → Process Results
       ↓               ↓                ↓                    ↓
   Execute → Monitor → Collect Data → Store & Cache
```

#### Language Learning Flow

```
Raw Content → NLP Analysis → Difficulty Scoring → Vocabulary Extraction
     ↓             ↓              ↓                    ↓
 Article Text → Entity Extract → Level Assignment → Word Database
     ↓             ↓              ↓                    ↓
 Clean Text → Colombian Context → Learning Path → Recommendation
     ↓             ↓              ↓                    ↓
 Store Content → Tag Content → User Progress → Personalized Content
```

## Integration Patterns

### External API Integration

```python
Integration Pattern:
    ├── Authentication Handling
    │   ├── API Keys
    │   ├── OAuth 2.0
    │   └── Token Management
    │
    ├── Rate Limiting
    │   ├── Token Bucket
    │   ├── Sliding Window
    │   └── Adaptive Limiting
    │
    ├── Error Handling
    │   ├── Retry Logic
    │   ├── Circuit Breaker
    │   └── Fallback Strategies
    │
    └── Data Processing
        ├── Response Validation
        ├── Data Transformation
        ├── Quality Assessment
        └── Storage Management
```

### Web Scraping Integration

```python
Scraping Pattern:
    ├── Respectful Scraping
    │   ├── robots.txt Compliance
    │   ├── Rate Limiting
    │   └── User-Agent Identification
    │
    ├── Content Extraction
    │   ├── CSS Selector-based
    │   ├── XPath-based
    │   └── AI-powered Extraction
    │
    ├── Quality Control
    │   ├── Content Validation
    │   ├── Duplicate Detection
    │   └── Relevance Scoring
    │
    └── Adaptation
        ├── Structure Detection
        ├── Selector Updates
        └── Fallback Strategies
```

## Performance Characteristics

### System Capacity

```
Current Capacity:
    ├── Data Collection: 10,000 articles/day
    ├── API Requests: 100,000 requests/day
    ├── Concurrent Users: 1,000 active users
    └── Storage: 1TB structured data

Target Capacity:
    ├── Data Collection: 100,000 articles/day
    ├── API Requests: 1,000,000 requests/day
    ├── Concurrent Users: 10,000 active users
    └── Storage: 10TB structured data
```

### Response Times

```
Performance Targets:
    ├── API Response Time: < 200ms (95th percentile)
    ├── Page Load Time: < 2 seconds
    ├── Search Response: < 500ms
    └── Data Processing: < 5 minutes per batch
```

## Future Architecture Considerations

### Microservices Evolution

```
Current Monolith → Microservices Migration:
    ├── Data Collection Service
    ├── NLP Processing Service
    ├── User Management Service
    ├── Learning Engine Service
    └── Analytics Service
```

### AI/ML Integration

```
Machine Learning Pipeline:
    ├── Content Classification
    ├── Personalized Recommendations
    ├── Automated Quality Assessment
    ├── Trend Detection
    └── Predictive Analytics
```

### International Expansion

```
Multi-country Architecture:
    ├── Country-specific Data Sources
    ├── Regional Language Models
    ├── Cultural Context Processing
    └── Localized User Interfaces
```

This architecture provides a robust, scalable foundation for the Colombian Intelligence & Language Learning Platform, supporting both current needs and future growth.