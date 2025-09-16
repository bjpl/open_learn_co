# Colombian Data Sources Comprehensive Guide

This document provides a complete reference for all 42+ data sources integrated into the Colombian Intelligence & Language Learning Platform.

## Overview

The platform integrates diverse Colombian data sources to provide comprehensive intelligence and authentic Spanish language learning content:

- **7 Government APIs** - Official statistics and economic data
- **18 News Scrapers** - Real-time news and analysis
- **8 Academic Sources** - Research and policy analysis
- **5 Security Sources** - Crime and conflict data
- **4 Regional Sources** - Local government data

**Total Sources**: 42+ active data sources

## Government Sources (APIs)

### 1. DANE - Departamento Administrativo Nacional de Estadística

**URL**: https://www.dane.gov.co
**Type**: Statistics API
**Priority**: High
**Update Frequency**: Daily
**Authentication**: API Key (optional)

**Data Types**:
- Economic indicators (GDP, inflation, employment)
- Demographic statistics and projections
- Census data and population studies
- Industrial production indices
- Foreign trade statistics

**API Endpoints**:
```
/indices/ipc          # Consumer Price Index (Inflation)
/cuentas/pib          # GDP Statistics
/mercado-laboral      # Employment Data
/comercio/exterior    # Foreign Trade
/demografia           # Population Data
```

**Rate Limit**: 100 requests/minute
**Content Language**: Spanish
**Learning Level**: Intermediate to Advanced

---

### 2. Banco de la República - Central Bank

**URL**: https://www.banrep.gov.co
**Type**: Economic API
**Priority**: High
**Update Frequency**: Daily
**Authentication**: None

**Data Types**:
- Exchange rates (TRM - Tasa Representativa del Mercado)
- Interest rates and monetary policy
- Economic research and reports
- Financial statistics
- International reserves

**API Endpoints**:
```
/tasas-cambio         # Exchange Rates
/tasas-interes        # Interest Rates
/politica-monetaria   # Monetary Policy
/investigaciones      # Economic Research
```

**Rate Limit**: 200 requests/minute
**Content Language**: Spanish
**Learning Level**: Advanced

---

### 3. SECOP - Sistema Electrónico de Contratación Pública

**URL**: https://www.colombiacompra.gov.co
**Type**: Procurement API
**Priority**: High
**Update Frequency**: Real-time
**Authentication**: Token Required

**Data Types**:
- Public contracts and tenders
- Government spending data
- Supplier information
- Procurement processes
- Transparency reports

**API Endpoints**:
```
/contratos            # Contract Data
/procesos             # Tender Processes
/proveedores          # Supplier Information
/estadisticas         # Procurement Statistics
```

**Rate Limit**: 300 requests/minute
**Content Language**: Spanish
**Learning Level**: Advanced (Legal/Administrative)

---

### 4. Datos Abiertos - Portal de Datos Abiertos

**URL**: https://www.datos.gov.co
**Type**: Open Data API (CKAN)
**Priority**: High
**Update Frequency**: Varies by dataset
**Authentication**: None

**Data Types**:
- Government datasets across all sectors
- Public spending and budget data
- Social programs and beneficiaries
- Environmental data
- Education and health statistics

**API Endpoints**:
```
/api/3/action/package_list       # List Datasets
/api/3/action/package_search     # Search Datasets
/api/3/action/resource_show      # Get Resources
```

**Rate Limit**: 1000 requests/minute
**Content Language**: Spanish
**Learning Level**: Varies (Beginner to Advanced)

---

### 5. DNP - Departamento Nacional de Planeación

**URL**: https://www.dnp.gov.co
**Type**: Planning API
**Priority**: Medium
**Update Frequency**: Weekly
**Authentication**: None

**Data Types**:
- National development plans
- Regional development projects
- Public investment data
- Territorial planning
- Development indicators

**Content Language**: Spanish
**Learning Level**: Advanced (Policy/Planning)

---

### 6. IDEAM - Instituto de Hidrología, Meteorología y Estudios Ambientales

**URL**: https://www.ideam.gov.co
**Type**: Environmental API
**Priority**: Medium
**Update Frequency**: Hourly/Daily
**Authentication**: API Key Required

**Data Types**:
- Weather and climate data
- Environmental monitoring
- Hydrological information
- Air quality indices
- Natural disaster alerts

**Rate Limit**: 100 requests/minute
**Content Language**: Spanish
**Learning Level**: Intermediate

---

### 7. MinHacienda - Ministerio de Hacienda

**URL**: https://www.minhacienda.gov.co
**Type**: Fiscal API
**Priority**: Medium
**Update Frequency**: Monthly
**Authentication**: None

**Data Types**:
- National budget and fiscal data
- Tax collection statistics
- Public debt information
- Fiscal policy reports
- Economic projections

**Content Language**: Spanish
**Learning Level**: Advanced (Economic/Fiscal)

## Media Sources (Scrapers)

### National Media

#### 8. El Tiempo

**URL**: https://www.eltiempo.com
**Type**: News Scraper
**Priority**: High
**Update Frequency**: 30 minutes
**Coverage**: National, comprehensive

**Sections Covered**:
- Política (Politics)
- Economía (Economy)
- Justicia (Justice)
- Bogotá (Local)
- Internacional (International)
- Deportes (Sports)
- Cultura (Culture)

**Content Features**:
- Colombian entity extraction
- Difficulty scoring for language learning
- Author and publication metadata
- Tag classification

**Learning Level**: Beginner to Advanced
**Daily Articles**: ~200

---

#### 9. El Espectador

**URL**: https://www.elespectador.com
**Type**: News Scraper
**Priority**: High
**Update Frequency**: 30 minutes
**Coverage**: National, investigative focus

**Specialties**:
- Investigative journalism
- Political analysis
- Judicial coverage
- Cultural content

**Learning Level**: Intermediate to Advanced
**Daily Articles**: ~150

---

#### 10. Semana

**URL**: https://www.semana.com
**Type**: Magazine Scraper
**Priority**: High
**Update Frequency**: 45 minutes
**Coverage**: Weekly analysis and investigative pieces

**Content Types**:
- Political analysis
- Long-form journalism
- Opinion pieces
- Special reports

**Learning Level**: Advanced
**Weekly Articles**: ~100

---

#### 11. La República

**URL**: https://www.larepublica.co
**Type**: Business News Scraper
**Priority**: High
**Update Frequency**: 60 minutes
**Coverage**: Economic and business focus

**Specialties**:
- Economic analysis
- Business news
- Market reports
- Corporate information

**Learning Level**: Advanced (Business Spanish)
**Daily Articles**: ~80

---

#### 12. Portafolio

**URL**: https://www.portafolio.co
**Type**: Financial News Scraper
**Priority**: Medium
**Update Frequency**: 60 minutes
**Coverage**: Financial markets and business

**Specialties**:
- Financial markets
- Investment analysis
- Economic indicators
- Business strategy

**Learning Level**: Advanced
**Daily Articles**: ~60

### Radio and Digital Media

#### 13. La FM

**URL**: https://www.lafm.com.co
**Type**: Radio News Scraper
**Priority**: Medium
**Update Frequency**: 30 minutes
**Coverage**: Radio journalism and analysis

**Content Types**:
- News summaries
- Interview transcripts
- Opinion segments
- Current affairs

**Learning Level**: Intermediate
**Daily Content**: ~50 pieces

---

#### 14. Blu Radio

**URL**: https://www.bluradio.com
**Type**: Radio News Scraper
**Priority**: Medium
**Update Frequency**: 30 minutes
**Coverage**: News and entertainment

**Specialties**:
- Breaking news
- Political interviews
- Sports coverage
- Entertainment news

**Learning Level**: Beginner to Intermediate
**Daily Content**: ~70 pieces

---

#### 15. RCN Radio

**URL**: https://www.rcnradio.com
**Type**: Radio News Scraper
**Priority**: Medium
**Update Frequency**: 45 minutes
**Coverage**: National radio network

**Learning Level**: Intermediate
**Daily Content**: ~60 pieces

### Regional Media

#### 16. El Colombiano (Antioquia)

**URL**: https://www.elcolombiano.com
**Type**: Regional News Scraper
**Priority**: Medium
**Update Frequency**: 45 minutes
**Coverage**: Antioquia region, Medellín focus

**Regional Focus**:
- Medellín metropolitan area
- Antioquia department news
- Regional development
- Local politics

**Learning Level**: Intermediate
**Daily Articles**: ~100

---

#### 17. El País (Valle del Cauca)

**URL**: https://www.elpais.com.co
**Type**: Regional News Scraper
**Priority**: Medium
**Update Frequency**: 45 minutes
**Coverage**: Valle del Cauca, Cali focus

**Regional Focus**:
- Cali and Valle del Cauca
- Pacific region news
- Port of Buenaventura
- Regional economy

**Learning Level**: Intermediate
**Daily Articles**: ~80

---

#### 18. El Heraldo (Atlántico)

**URL**: https://www.elheraldo.co
**Type**: Regional News Scraper
**Priority**: Medium
**Update Frequency**: 45 minutes
**Coverage**: Atlántico, Caribbean coast

**Regional Focus**:
- Barranquilla metropolitan area
- Caribbean region
- Port activities
- Carnival and culture

**Learning Level**: Intermediate
**Daily Articles**: ~70

---

#### 19. El Universal (Bolívar)

**URL**: https://www.eluniversal.com.co
**Type**: Regional News Scraper
**Priority**: Low
**Update Frequency**: 60 minutes
**Coverage**: Bolívar, Cartagena focus

**Learning Level**: Intermediate
**Daily Articles**: ~50

---

#### 20. Vanguardia (Santander)

**URL**: https://www.vanguardia.com
**Type**: Regional News Scraper
**Priority**: Low
**Update Frequency**: 60 minutes
**Coverage**: Santander, Bucaramanga focus

**Learning Level**: Intermediate
**Daily Articles**: ~40

---

#### 21. La Opinión (Norte de Santander)

**URL**: https://www.laopinion.com.co
**Type**: Regional News Scraper
**Priority**: Low
**Update Frequency**: 60 minutes
**Coverage**: Norte de Santander, border region

**Special Focus**: Colombian-Venezuelan border issues
**Learning Level**: Intermediate
**Daily Articles**: ~30

### Specialized Media

#### 22. Dinero

**URL**: https://www.dinero.com
**Type**: Business Magazine Scraper
**Priority**: Medium
**Update Frequency**: 120 minutes
**Coverage**: Business and economic analysis

**Content Types**:
- Business strategy
- Economic analysis
- Company profiles
- Market trends

**Learning Level**: Advanced (Business)
**Weekly Articles**: ~50

---

#### 23. La Silla Vacía

**URL**: https://www.lasillavacia.com
**Type**: Political Analysis Scraper
**Priority**: High
**Update Frequency**: 120 minutes
**Coverage**: Political analysis and investigation

**Specialties**:
- Political network analysis
- Power mapping
- Investigative reports
- Electoral analysis

**Learning Level**: Advanced (Political)
**Weekly Articles**: ~30

---

#### 24. Razón Pública

**URL**: https://razonpublica.com
**Type**: Academic Analysis Scraper
**Priority**: Medium
**Update Frequency**: 240 minutes
**Coverage**: Academic perspective on current affairs

**Content Types**:
- Policy analysis
- Academic research
- Expert opinions
- Social commentary

**Learning Level**: Expert (Academic)
**Weekly Articles**: ~20

---

#### 25. Colombia Check

**URL**: https://colombiacheck.com
**Type**: Fact-checking Scraper
**Priority**: Medium
**Update Frequency**: 120 minutes
**Coverage**: Fact-checking and verification

**Content Types**:
- Fact-check articles
- Verification reports
- Misleading claim analysis
- Truth ratings

**Special Features**:
- Claim verification
- Evidence assessment
- Truth scale ratings
- Source tracking

**Learning Level**: Advanced
**Weekly Articles**: ~15

## Academic Sources

### 26. Universidad de los Andes

**URL**: https://uniandes.edu.co
**Type**: Academic Research
**Priority**: Medium
**Coverage**: Economic research, policy analysis

**Research Areas**:
- Economic policy
- Political science
- Social studies
- Public administration

**Content Language**: Spanish/English
**Learning Level**: Expert

---

### 27. Universidad Nacional

**URL**: https://unal.edu.co
**Type**: Academic Research
**Priority**: Medium
**Coverage**: Multi-disciplinary research

**Research Centers**:
- Observatory of Public Policy
- Social Research Institute
- Economic Studies Center

**Learning Level**: Expert

---

### 28. Fedesarrollo

**URL**: https://www.fedesarrollo.org.co
**Type**: Economic Research
**Priority**: Medium
**Coverage**: Economic studies and policy analysis

**Research Areas**:
- Macroeconomic analysis
- Policy evaluation
- Economic surveys
- Development studies

**Content Types**:
- Research reports
- Economic surveys
- Policy briefs
- Working papers

**Learning Level**: Expert (Economic)

---

### 29. CEDE - Universidad de los Andes

**URL**: https://economia.uniandes.edu.co/cede
**Type**: Economic Research Center
**Coverage**: Development economics

**Learning Level**: Expert

---

### 30. ICANH - Instituto Colombiano de Antropología e Historia

**URL**: https://www.icanh.gov.co
**Type**: Cultural and Historical Research
**Coverage**: Colombian culture and history

**Learning Level**: Advanced

---

### 31. Instituto de Estudios Urbanos - UN

**URL**: https://institutodeestudiosurbanos.info
**Type**: Urban Studies
**Coverage**: Urban development and planning

**Learning Level**: Expert

---

### 32. Observatorio de Restitución y Regulación de Derechos de Propiedad Agraria

**URL**: https://www.upra.gov.co
**Type**: Land Rights Research
**Coverage**: Rural and land issues

**Learning Level**: Expert

---

### 33. Centro de Estudios sobre Desarrollo Económico - CEDE

**Coverage**: Economic development studies
**Learning Level**: Expert

## Security Sources

### 34. Policía Nacional

**URL**: https://www.policia.gov.co
**Type**: Crime Statistics
**Priority**: High
**Coverage**: National crime and security data

**Data Types**:
- Crime statistics by region
- Security reports
- Police operations
- Public safety indicators

**Learning Level**: Intermediate to Advanced

---

### 35. Observatorio de Derechos Humanos

**URL**: https://www.derechoshumanos.gov.co
**Type**: Human Rights Data
**Priority**: High
**Coverage**: Human rights violations and protection

**Data Types**:
- Violation reports
- Conflict data
- Victim statistics
- Protection measures

**Learning Level**: Advanced

---

### 36. Fundación Ideas para la Paz (FIP)

**URL**: https://www.ideaspaz.org
**Type**: Security Analysis
**Priority**: Medium
**Coverage**: Conflict analysis and peace studies

**Research Areas**:
- Armed conflict analysis
- Illegal economies
- Peace process monitoring
- Security policy

**Content Types**:
- Policy briefs
- Situation reports
- Research papers
- Analysis articles

**Learning Level**: Advanced

---

### 37. CERAC - Centro de Recursos para el Análisis de Conflictos

**URL**: https://www.cerac.org.co
**Type**: Conflict Analysis
**Coverage**: Quantitative conflict analysis

**Learning Level**: Expert

---

### 38. Observatorio del Programa Presidencial de DH y DIH

**Coverage**: Human rights and international humanitarian law
**Learning Level**: Advanced

## Regional Government Sources

### 39. Alcaldía de Bogotá

**URL**: https://bogota.gov.co
**Type**: Municipal Government
**Priority**: Medium
**Coverage**: Bogotá city administration and data

**Data Types**:
- Municipal budget
- Public services
- Urban development
- Local regulations

**Learning Level**: Intermediate

---

### 40. Gobernación de Antioquia

**URL**: https://antioquia.gov.co
**Type**: Departmental Government
**Coverage**: Antioquia department administration

**Learning Level**: Intermediate

---

### 41. Alcaldía de Medellín

**URL**: https://medellin.gov.co
**Type**: Municipal Government
**Coverage**: Medellín city data and services

**Learning Level**: Intermediate

---

### 42. Gobernación del Valle del Cauca

**URL**: https://valledelcauca.gov.co
**Type**: Departmental Government
**Coverage**: Valle del Cauca administration

**Learning Level**: Intermediate

## Additional Specialized Sources

### 43. SINCHI - Instituto Amazónico de Investigaciones Científicas

**URL**: https://sinchi.org.co
**Type**: Amazon Research
**Coverage**: Amazon region studies

**Learning Level**: Expert

---

### 44. INVEMAR - Instituto de Investigaciones Marinas

**URL**: https://invemar.org.co
**Type**: Marine Research
**Coverage**: Coastal and marine studies

**Learning Level**: Expert

## Data Source Categories Summary

| Category | Count | Update Frequency | Learning Level |
|----------|-------|------------------|----------------|
| Government APIs | 7 | Real-time to Daily | Intermediate-Advanced |
| National Media | 8 | 30-60 minutes | Beginner-Advanced |
| Regional Media | 6 | 45-60 minutes | Intermediate |
| Radio/Digital | 3 | 30-45 minutes | Beginner-Intermediate |
| Specialized Media | 4 | 120-240 minutes | Advanced-Expert |
| Academic Sources | 8 | Weekly | Expert |
| Security Sources | 5 | Daily to Weekly | Advanced |
| Regional Government | 4 | Daily to Weekly | Intermediate |
| Research Institutes | 2 | Monthly | Expert |

## Content Classification

### By Language Learning Level

**Beginner (A1-A2)**:
- Blu Radio (basic news)
- Simple news articles from major papers
- Weather reports (IDEAM)

**Intermediate (B1-B2)**:
- El Tiempo (general news)
- El Espectador (standard articles)
- Regional newspapers
- Radio news content

**Advanced (C1)**:
- La República (business)
- Semana (analysis)
- Government documents
- Legal content (SECOP)

**Expert (C2)**:
- Academic research
- Complex policy documents
- Technical reports
- Specialized analysis

### By Content Type

**News & Current Affairs** (18 sources):
- Breaking news
- Political coverage
- Economic news
- Social issues

**Economic & Financial** (8 sources):
- Market data
- Economic indicators
- Business news
- Fiscal information

**Government & Policy** (12 sources):
- Official data
- Policy documents
- Regulatory information
- Public spending

**Academic & Research** (8 sources):
- Research papers
- Policy analysis
- Academic studies
- Expert opinions

**Regional & Local** (10 sources):
- Local news
- Regional development
- Municipal data
- Departmental information

## Source Reliability Ratings

### Tier 1 - Highest Reliability
- Government APIs (DANE, Banco República, etc.)
- El Tiempo, El Espectador
- Academic institutions

### Tier 2 - High Reliability
- Semana, La República
- Regional major newspapers
- Established research centers

### Tier 3 - Moderate Reliability
- Specialized blogs and analysis sites
- Opinion pieces
- Editorial content

## Technical Integration Details

### API Sources
- **Authentication**: Mix of API keys, tokens, and open access
- **Rate Limits**: 50-1000 requests/minute
- **Data Formats**: JSON, XML, CSV
- **Update Frequencies**: Real-time to weekly

### Scraper Sources
- **Rate Limits**: 3-10 requests/minute (respectful scraping)
- **Content Formats**: HTML parsing to structured data
- **Update Frequencies**: 30 minutes to 4 hours
- **Quality Control**: Content validation and duplicate detection

### Data Processing Pipeline
1. **Collection**: Automated gathering from all sources
2. **Processing**: Text cleaning, entity extraction, classification
3. **Storage**: Structured database storage with metadata
4. **Analysis**: NLP processing for language learning features
5. **Serving**: API endpoints for frontend consumption

## Usage Guidelines

### For Intelligence Gathering
- Focus on Tier 1 and Tier 2 sources for factual information
- Cross-reference information across multiple sources
- Pay attention to source bias and perspective
- Use academic sources for in-depth analysis

### For Language Learning
- Start with Beginner level sources for new learners
- Progress through levels based on comprehension
- Use Colombian entity extraction for cultural learning
- Leverage difficulty scoring for appropriate content selection

### For Research
- Combine government data with media analysis
- Use academic sources for theoretical framework
- Include regional sources for comprehensive coverage
- Validate information across multiple source types

This comprehensive guide provides the foundation for understanding and utilizing all data sources in the Colombian Intelligence & Language Learning Platform.