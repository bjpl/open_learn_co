"""
Strategic open data and content sources for Colombian intelligence gathering
Comprehensive list of valuable public sources for OSINT analysis
"""

STRATEGIC_SOURCES = {
    # Government & Official Data
    "government": [
        {
            "name": "DANE - Estadísticas",
            "url": "https://www.dane.gov.co",
            "api": "https://www.dane.gov.co/servicios-al-ciudadano/servicios-de-informacion/api",
            "type": "statistics",
            "content": ["economic indicators", "demographics", "census data", "inflation", "employment"],
            "update_frequency": "daily/monthly",
            "priority": "high"
        },
        {
            "name": "Banco de la República",
            "url": "https://www.banrep.gov.co",
            "api": "https://www.banrep.gov.co/es/servicios-informacion/api",
            "type": "economic",
            "content": ["monetary policy", "exchange rates", "interest rates", "economic reports"],
            "update_frequency": "daily",
            "priority": "high"
        },
        {
            "name": "MinHacienda - Datos Abiertos",
            "url": "https://www.minhacienda.gov.co",
            "type": "fiscal",
            "content": ["budget", "public spending", "debt", "tax collection"],
            "update_frequency": "monthly",
            "priority": "high"
        },
        {
            "name": "Portal de Datos Abiertos Colombia",
            "url": "https://www.datos.gov.co",
            "api": "CKAN API available",
            "type": "open_data",
            "content": ["all government datasets", "CSV/JSON exports", "real-time data"],
            "datasets": [
                "contratos públicos",
                "presupuesto nacional",
                "indicadores de violencia",
                "datos electorales"
            ],
            "priority": "high"
        },
        {
            "name": "SIGEP - Información de Servidores Públicos",
            "url": "https://www.sigep.gov.co",
            "type": "public_servants",
            "content": ["government officials", "declarations", "organizational structure"],
            "priority": "medium"
        },
        {
            "name": "SECOP - Contratación Pública",
            "url": "https://www.colombiacompra.gov.co",
            "api": "https://www.colombiacompra.gov.co/transparencia/api",
            "type": "procurement",
            "content": ["public contracts", "tenders", "suppliers", "spending"],
            "priority": "high"
        }
    ],

    # Security & Defense
    "security": [
        {
            "name": "Policía Nacional - Estadísticas",
            "url": "https://www.policia.gov.co",
            "type": "crime_statistics",
            "content": ["crime rates", "security reports", "regional statistics"],
            "priority": "high"
        },
        {
            "name": "Observatorio de DDHH",
            "url": "https://www.derechoshumanos.gov.co",
            "type": "human_rights",
            "content": ["human rights violations", "conflict data", "victim statistics"],
            "priority": "high"
        },
        {
            "name": "CERAC - Conflict Analysis",
            "url": "https://www.cerac.org.co",
            "type": "conflict_research",
            "content": ["armed conflict analysis", "violence indicators", "peace process"],
            "priority": "medium"
        },
        {
            "name": "Fundación Ideas para la Paz",
            "url": "https://www.ideaspaz.org",
            "type": "security_analysis",
            "content": ["security analysis", "conflict dynamics", "illegal economies"],
            "priority": "medium"
        }
    ],

    # Economic & Business Intelligence
    "economic": [
        {
            "name": "Superintendencia de Sociedades",
            "url": "https://www.supersociedades.gov.co",
            "type": "corporate_registry",
            "content": ["company information", "financial reports", "bankruptcies"],
            "priority": "high"
        },
        {
            "name": "Superintendencia Financiera",
            "url": "https://www.superfinanciera.gov.co",
            "type": "financial",
            "content": ["banking sector", "financial indicators", "market data"],
            "priority": "medium"
        },
        {
            "name": "RUES - Registro Empresarial",
            "url": "https://www.rues.org.co",
            "type": "business_registry",
            "content": ["business registrations", "company data", "commercial registry"],
            "priority": "medium"
        },
        {
            "name": "Bolsa de Valores de Colombia",
            "url": "https://www.bvc.com.co",
            "api": "Market data API available",
            "type": "stock_market",
            "content": ["stock prices", "market indices", "corporate actions"],
            "priority": "medium"
        },
        {
            "name": "ANDI - Business Association",
            "url": "https://www.andi.com.co",
            "type": "business_intelligence",
            "content": ["industry reports", "economic analysis", "business surveys"],
            "priority": "low"
        }
    ],

    # Media & News Sources
    "media": [
        {
            "name": "El Tiempo",
            "url": "https://www.eltiempo.com",
            "rss": "https://www.eltiempo.com/rss",
            "priority": "high"
        },
        {
            "name": "El Espectador",
            "url": "https://www.elespectador.com",
            "rss": "https://www.elespectador.com/feeds",
            "priority": "high"
        },
        {
            "name": "Semana",
            "url": "https://www.semana.com",
            "priority": "high"
        },
        {
            "name": "La Silla Vacía",
            "url": "https://www.lasillavacia.com",
            "type": "investigative",
            "content": ["political analysis", "investigations", "power networks"],
            "priority": "high"
        },
        {
            "name": "Portafolio",
            "url": "https://www.portafolio.co",
            "type": "economic_news",
            "priority": "medium"
        },
        {
            "name": "La República",
            "url": "https://www.larepublica.co",
            "type": "business_news",
            "priority": "medium"
        }
    ],

    # Regional Sources
    "regional": [
        {
            "name": "El Colombiano - Medellín",
            "url": "https://www.elcolombiano.com",
            "region": "Antioquia",
            "priority": "medium"
        },
        {
            "name": "El País - Cali",
            "url": "https://www.elpais.com.co",
            "region": "Valle del Cauca",
            "priority": "medium"
        },
        {
            "name": "El Heraldo - Barranquilla",
            "url": "https://www.elheraldo.co",
            "region": "Atlántico",
            "priority": "medium"
        },
        {
            "name": "Vanguardia - Bucaramanga",
            "url": "https://www.vanguardia.com",
            "region": "Santander",
            "priority": "low"
        },
        {
            "name": "La Opinión - Cúcuta",
            "url": "https://www.laopinion.com.co",
            "region": "Norte de Santander",
            "priority": "low"
        }
    ],

    # Academic & Research
    "academic": [
        {
            "name": "Universidad de los Andes - Investigaciones",
            "url": "https://uniandes.edu.co",
            "type": "research",
            "content": ["economic research", "political analysis", "social studies"],
            "priority": "medium"
        },
        {
            "name": "Universidad Nacional - Observatorios",
            "url": "https://unal.edu.co",
            "type": "observatories",
            "content": ["social observatories", "economic analysis", "public policy"],
            "priority": "medium"
        },
        {
            "name": "Fedesarrollo",
            "url": "https://www.fedesarrollo.org.co",
            "type": "economic_research",
            "content": ["economic studies", "policy analysis", "surveys"],
            "priority": "medium"
        }
    ],

    # Social Media & Forums
    "social": [
        {
            "name": "Twitter/X Colombia Trends",
            "api": "Twitter API",
            "type": "social_media",
            "content": ["trending topics", "public sentiment", "breaking news"],
            "search_terms": [
                "#Colombia", "#Bogota", "#ColombiaNews",
                "Colombia política", "Colombia economía"
            ],
            "priority": "medium"
        },
        {
            "name": "Reddit - r/Colombia",
            "url": "https://www.reddit.com/r/Colombia",
            "api": "Reddit API",
            "type": "forum",
            "content": ["public discourse", "sentiment", "emerging issues"],
            "priority": "low"
        }
    ],

    # International Organizations
    "international": [
        {
            "name": "UN Colombia",
            "url": "https://colombia.un.org",
            "type": "international",
            "content": ["UN reports", "humanitarian situation", "development data"],
            "priority": "medium"
        },
        {
            "name": "World Bank - Colombia Data",
            "url": "https://data.worldbank.org/country/colombia",
            "api": "World Bank API",
            "type": "development_data",
            "content": ["development indicators", "economic data", "poverty statistics"],
            "priority": "medium"
        },
        {
            "name": "OECD - Colombia",
            "url": "https://www.oecd.org/countries/colombia",
            "type": "economic_analysis",
            "content": ["economic reviews", "policy recommendations", "statistics"],
            "priority": "low"
        },
        {
            "name": "OAS - Colombia Reports",
            "url": "https://www.oas.org",
            "type": "regional_organization",
            "content": ["human rights", "democracy", "regional security"],
            "priority": "low"
        }
    ],

    # Specialized Intelligence Sources
    "specialized": [
        {
            "name": "InSight Crime - Colombia",
            "url": "https://insightcrime.org/colombia-organized-crime-news",
            "type": "organized_crime",
            "content": ["organized crime", "drug trafficking", "criminal dynamics"],
            "priority": "high"
        },
        {
            "name": "Colombia Risk Analysis",
            "url": "https://colombiareports.com",
            "type": "risk_analysis",
            "content": ["security risks", "political analysis", "economic risks"],
            "priority": "medium"
        },
        {
            "name": "Crisis Group - Colombia",
            "url": "https://www.crisisgroup.org/latin-america-caribbean/andes/colombia",
            "type": "conflict_analysis",
            "content": ["conflict analysis", "peace process", "security dynamics"],
            "priority": "medium"
        }
    ],

    # Environmental & Natural Resources
    "environmental": [
        {
            "name": "IDEAM - Instituto de Meteorología",
            "url": "https://www.ideam.gov.co",
            "type": "environmental",
            "content": ["weather data", "climate change", "natural disasters", "water resources"],
            "priority": "low"
        },
        {
            "name": "ANH - Hidrocarburos",
            "url": "https://www.anh.gov.co",
            "type": "energy",
            "content": ["oil production", "gas reserves", "energy sector"],
            "priority": "medium"
        }
    ],

    # Legal & Judicial
    "legal": [
        {
            "name": "Corte Constitucional",
            "url": "https://www.corteconstitucional.gov.co",
            "type": "judicial",
            "content": ["constitutional rulings", "legal precedents"],
            "priority": "medium"
        },
        {
            "name": "Fiscalía General",
            "url": "https://www.fiscalia.gov.co",
            "type": "prosecution",
            "content": ["criminal cases", "investigations", "statistics"],
            "priority": "high"
        },
        {
            "name": "Rama Judicial - Consulta de Procesos",
            "url": "https://www.ramajudicial.gov.co",
            "type": "court_records",
            "content": ["court cases", "judicial decisions", "legal proceedings"],
            "priority": "medium"
        }
    ]
}


def get_sources_by_priority(priority: str) -> list:
    """Get all sources of a specific priority level"""
    sources = []
    for category, items in STRATEGIC_SOURCES.items():
        for source in items:
            if source.get("priority") == priority:
                sources.append({**source, "category": category})
    return sources


def get_sources_by_type(source_type: str) -> list:
    """Get all sources of a specific type"""
    sources = []
    for category, items in STRATEGIC_SOURCES.items():
        for source in items:
            if source.get("type") == source_type:
                sources.append({**source, "category": category})
    return sources


def get_api_enabled_sources() -> list:
    """Get all sources that have API access"""
    sources = []
    for category, items in STRATEGIC_SOURCES.items():
        for source in items:
            if "api" in source:
                sources.append({**source, "category": category})
    return sources


def get_realtime_sources() -> list:
    """Get sources that provide real-time or daily updates"""
    sources = []
    for category, items in STRATEGIC_SOURCES.items():
        for source in items:
            freq = source.get("update_frequency", "")
            if "daily" in freq or "real-time" in freq:
                sources.append({**source, "category": category})
    return sources