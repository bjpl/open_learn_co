"""
Base scraper modules for Colombian Platform
"""

from .base_scraper import BaseScraper
from .rate_limiter import RateLimiter
from .smart_scraper import SmartScraper

__all__ = ['BaseScraper', 'RateLimiter', 'SmartScraper']
