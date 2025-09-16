"""
Colombian Media Scrapers Module

This module contains scrapers for Colombian news sources organized by type:
- National Media: Major newspapers and magazines with national coverage
- Regional Media: Regional newspapers focused on specific cities/departments
- Specialized Media: Business, political analysis, fact-checking, and digital sources

All scrapers inherit from SmartScraper and return ScrapedDocument objects
with Colombian entity detection and difficulty scoring for language learning.
"""

# National Media Scrapers (High Priority)
from .el_espectador import ElEspectadorScraper
from .semana import SemanaScraper
from .la_republica import LaRepublicaScraper
from .portafolio import PortafolioScraper
from .la_fm import LaFMScraper
from .blu_radio import BluRadioScraper

# Regional Media Scrapers (Medium Priority)
from .el_colombiano import ElColombianoScraper
from .el_pais import ElPaisScraper
from .el_heraldo import ElHeraldoScraper
from .el_universal import ElUniversalScraper

# Specialized Media Scrapers
from .dinero import DineroScraper
from .la_silla_vacia import LaSillaVaciaScraper
from .razon_publica import RazonPublicaScraper
from .colombia_check import ColombiaCheckScraper
from .pulzo import PulzoScraper

# Scraper registry for easy access
NATIONAL_SCRAPERS = {
    'el_espectador': ElEspectadorScraper,
    'semana': SemanaScraper,
    'la_republica': LaRepublicaScraper,
    'portafolio': PortafolioScraper,
    'la_fm': LaFMScraper,
    'blu_radio': BluRadioScraper,
}

REGIONAL_SCRAPERS = {
    'el_colombiano': ElColombianoScraper,
    'el_pais': ElPaisScraper,
    'el_heraldo': ElHeraldoScraper,
    'el_universal': ElUniversalScraper,
}

SPECIALIZED_SCRAPERS = {
    'dinero': DineroScraper,
    'la_silla_vacia': LaSillaVaciaScraper,
    'razon_publica': RazonPublicaScraper,
    'colombia_check': ColombiaCheckScraper,
    'pulzo': PulzoScraper,
}

# All scrapers combined
ALL_SCRAPERS = {
    **NATIONAL_SCRAPERS,
    **REGIONAL_SCRAPERS,
    **SPECIALIZED_SCRAPERS
}

# Export main classes
__all__ = [
    # National Media
    'ElEspectadorScraper',
    'SemanaScraper',
    'LaRepublicaScraper',
    'PortafolioScraper',
    'LaFMScraper',
    'BluRadioScraper',

    # Regional Media
    'ElColombianoScraper',
    'ElPaisScraper',
    'ElHeraldoScraper',
    'ElUniversalScraper',

    # Specialized Media
    'DineroScraper',
    'LaSillaVaciaScraper',
    'RazonPublicaScraper',
    'ColombiaCheckScraper',
    'PulzoScraper',

    # Registries
    'NATIONAL_SCRAPERS',
    'REGIONAL_SCRAPERS',
    'SPECIALIZED_SCRAPERS',
    'ALL_SCRAPERS'
]


def get_scraper_by_name(name: str):
    """Get a scraper class by name"""
    return ALL_SCRAPERS.get(name.lower())


def get_scrapers_by_type(scraper_type: str):
    """Get scrapers by type: 'national', 'regional', or 'specialized'"""
    if scraper_type.lower() == 'national':
        return NATIONAL_SCRAPERS
    elif scraper_type.lower() == 'regional':
        return REGIONAL_SCRAPERS
    elif scraper_type.lower() == 'specialized':
        return SPECIALIZED_SCRAPERS
    else:
        return {}


def get_all_scraper_names():
    """Get list of all available scraper names"""
    return list(ALL_SCRAPERS.keys())