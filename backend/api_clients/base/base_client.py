"""
Base API client for Colombian open data sources
Implements common patterns for all API integrations
"""

import asyncio
import aiohttp
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode

import redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from api_clients.base.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """
    Abstract base class for API clients
    Implements common functionality for all Colombian data APIs
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize base API client

        Args:
            config: Configuration dictionary
        """
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1 hour default
        self.max_retries = config.get('max_retries', 3)

        # Initialize components
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(
            max_requests=config.get('rate_limit', 100),
            time_window=60
        )

        # Redis cache connection
        self.cache = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            decode_responses=True
        )

        # Request headers
        self.headers = self._build_headers()

        logger.info(f"{self.__class__.__name__} initialized for {self.base_url}")

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            'User-Agent': 'Colombia-Intel-Platform/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8'
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        return headers

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key for request

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Cache key string
        """
        cache_data = {
            'client': self.__class__.__name__,
            'endpoint': endpoint,
            'params': params or {}
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        Get data from cache

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None
        """
        try:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    async def _set_cache(self, cache_key: str, data: Dict, ttl: Optional[int] = None):
        """
        Set data in cache

        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        try:
            ttl = ttl or self.cache_ttl
            self.cache.setex(
                cache_key,
                ttl,
                json.dumps(data, ensure_ascii=False)
            )
            logger.debug(f"Cached {cache_key} for {ttl} seconds")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Response data
        """
        # Rate limiting
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint}"

        if params:
            url = f"{url}?{urlencode(params)}"

        logger.info(f"Making {method} request to {url}")

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()

                # Handle different content types
                content_type = response.headers.get('Content-Type', '')

                if 'application/json' in content_type:
                    return await response.json()
                elif 'text/csv' in content_type:
                    text = await response.text()
                    return {'csv_data': text, 'content_type': 'csv'}
                elif 'text/xml' in content_type or 'application/xml' in content_type:
                    text = await response.text()
                    return {'xml_data': text, 'content_type': 'xml'}
                else:
                    text = await response.text()
                    return {'raw_data': text, 'content_type': content_type}

        except aiohttp.ClientResponseError as e:
            logger.error(f"API error {e.status}: {e.message}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {url}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def fetch_data(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Fetch data from API with caching

        Args:
            endpoint: API endpoint
            params: Query parameters
            use_cache: Whether to use cache

        Returns:
            API response data
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(endpoint, params)
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # Make API request
        data = await self._make_request('GET', endpoint, params)

        # Transform data
        transformed_data = await self.transform_response(data)

        # Add metadata
        transformed_data['_metadata'] = {
            'source': self.__class__.__name__,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow().isoformat(),
            'cached': False
        }

        # Cache response
        if use_cache:
            await self._set_cache(cache_key, transformed_data)

        # Check for alerts
        await self.check_for_alerts(transformed_data)

        return transformed_data

    @abstractmethod
    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform API response to standard format
        Must be implemented by subclasses

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        pass

    async def check_for_alerts(self, data: Dict):
        """
        Check data for alert conditions

        Args:
            data: Transformed data
        """
        # Default implementation - can be overridden
        pass

    async def get_health_status(self) -> Dict:
        """
        Check API health status

        Returns:
            Health status information
        """
        try:
            # Make a simple request to check availability
            await self._make_request('GET', '')
            return {
                'status': 'healthy',
                'api': self.__class__.__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'api': self.__class__.__name__,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def batch_fetch(
        self,
        endpoints: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict]:
        """
        Fetch multiple endpoints concurrently

        Args:
            endpoints: List of endpoint configurations
            max_concurrent: Maximum concurrent requests

        Returns:
            List of responses
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(endpoint_config):
            async with semaphore:
                return await self.fetch_data(
                    endpoint_config['endpoint'],
                    endpoint_config.get('params')
                )

        tasks = [fetch_with_semaphore(ep) for ep in endpoints]
        return await asyncio.gather(*tasks)