"""
DANE (Departamento Administrativo Nacional de Estadística) API Client
Access Colombian statistical data including economic indicators, demographics, and more
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class DANEClient(BaseAPIClient):
    """
    Client for DANE API - Colombian National Statistics Department
    Provides access to economic indicators, census data, and statistical information
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize DANE client with configuration"""
        default_config = {
            'base_url': 'https://www.dane.gov.co/api',
            'api_key': None,  # DANE API is mostly public
            'cache_ttl': 3600,  # 1 hour cache for most data
            'rate_limit': 100
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # DANE specific endpoints
        self.endpoints = {
            'ipc': 'indices/ipc',  # Índice de Precios al Consumidor (CPI)
            'pib': 'cuentas/pib',  # Producto Interno Bruto (GDP)
            'empleo': 'mercado-laboral/empleo',  # Employment statistics
            'comercio': 'comercio/exterior',  # Foreign trade
            'poblacion': 'demografia/poblacion',  # Population data
            'ipm': 'pobreza/ipm',  # Índice de Pobreza Multidimensional
            'industria': 'industria/manufacturera',  # Manufacturing industry
            'construccion': 'construccion/indicadores',  # Construction indicators
        }

        # Alert thresholds for economic indicators
        self.alert_thresholds = {
            'ipc_monthly_change': 1.0,  # Alert if inflation > 1% monthly
            'unemployment_rate': 15.0,  # Alert if unemployment > 15%
            'gdp_quarterly_change': -2.0,  # Alert if GDP contracts > 2%
            'exports_change': -10.0,  # Alert if exports fall > 10%
        }

    async def get_inflation_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get inflation (IPC) data

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Inflation data with analysis
        """
        params = {}
        if start_date:
            params['fecha_inicio'] = start_date
        if end_date:
            params['fecha_fin'] = end_date

        data = await self.fetch_data(self.endpoints['ipc'], params)

        # Add calculated metrics
        if 'data' in data and len(data['data']) > 1:
            data['analysis'] = self._analyze_inflation(data['data'])

        return data

    async def get_gdp_data(
        self,
        period: str = 'quarterly',
        sectors: Optional[List[str]] = None
    ) -> Dict:
        """
        Get GDP data

        Args:
            period: 'quarterly' or 'annual'
            sectors: List of economic sectors to include

        Returns:
            GDP data with breakdown
        """
        params = {
            'periodicidad': period,
            'desagregacion': 'sectores' if sectors else 'total'
        }

        if sectors:
            params['sectores'] = ','.join(sectors)

        return await self.fetch_data(self.endpoints['pib'], params)

    async def get_employment_statistics(
        self,
        cities: Optional[List[str]] = None,
        include_informal: bool = True
    ) -> Dict:
        """
        Get employment and unemployment statistics

        Args:
            cities: List of cities (default: national)
            include_informal: Include informal employment data

        Returns:
            Employment statistics
        """
        params = {
            'nivel_geografico': 'ciudades' if cities else 'nacional',
            'incluir_informalidad': include_informal
        }

        if cities:
            params['ciudades'] = ','.join(cities)

        data = await self.fetch_data(self.endpoints['empleo'], params)

        # Add unemployment rate calculation
        if 'data' in data:
            data['unemployment_rate'] = self._calculate_unemployment_rate(data['data'])

        return data

    async def get_foreign_trade_data(
        self,
        trade_type: str = 'both',
        countries: Optional[List[str]] = None,
        products: Optional[List[str]] = None
    ) -> Dict:
        """
        Get foreign trade statistics

        Args:
            trade_type: 'exports', 'imports', or 'both'
            countries: List of country codes
            products: List of product codes (HS codes)

        Returns:
            Trade statistics
        """
        params = {
            'tipo_comercio': trade_type,
            'agrupacion': 'paises_productos'
        }

        if countries:
            params['paises'] = ','.join(countries)
        if products:
            params['productos'] = ','.join(products)

        data = await self.fetch_data(self.endpoints['comercio'], params)

        # Calculate trade balance
        if 'data' in data and trade_type == 'both':
            data['trade_balance'] = self._calculate_trade_balance(data['data'])

        return data

    async def get_poverty_indicators(
        self,
        indicator_type: str = 'multidimensional',
        geographic_level: str = 'departmental'
    ) -> Dict:
        """
        Get poverty indicators

        Args:
            indicator_type: 'multidimensional', 'monetary', or 'both'
            geographic_level: 'national', 'departmental', or 'municipal'

        Returns:
            Poverty statistics
        """
        params = {
            'tipo_indicador': indicator_type,
            'nivel_geografico': geographic_level
        }

        return await self.fetch_data(self.endpoints['ipm'], params)

    async def get_demographic_data(
        self,
        data_type: str = 'population',
        projection_year: Optional[int] = None
    ) -> Dict:
        """
        Get demographic data and projections

        Args:
            data_type: 'population', 'births', 'deaths', 'migration'
            projection_year: Year for population projections

        Returns:
            Demographic data
        """
        params = {
            'tipo_dato': data_type
        }

        if projection_year:
            params['año_proyeccion'] = projection_year

        return await self.fetch_data(self.endpoints['poblacion'], params)

    async def get_economic_dashboard(self) -> Dict:
        """
        Get comprehensive economic dashboard data

        Returns:
            Dashboard with key economic indicators
        """
        # Fetch multiple indicators concurrently
        endpoints = [
            {'endpoint': self.endpoints['ipc'], 'params': {'ultimos_meses': 3}},
            {'endpoint': self.endpoints['pib'], 'params': {'ultimo_trimestre': True}},
            {'endpoint': self.endpoints['empleo'], 'params': {'ultimo_mes': True}},
            {'endpoint': self.endpoints['comercio'], 'params': {'ultimo_mes': True}},
        ]

        results = await self.batch_fetch(endpoints, max_concurrent=4)

        # Combine into dashboard
        dashboard = {
            'timestamp': datetime.utcnow().isoformat(),
            'indicators': {
                'inflation': results[0],
                'gdp': results[1],
                'employment': results[2],
                'trade': results[3]
            },
            'alerts': self._check_economic_alerts(results)
        }

        return dashboard

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform DANE API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        # Handle different DANE response formats
        if 'resultado' in response:
            data = response['resultado']
        elif 'datos' in response:
            data = response['datos']
        else:
            data = response

        transformed = {
            'source': 'DANE',
            'data': data,
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Extract metadata if present
        if 'metadatos' in response:
            transformed['metadata'] = response['metadatos']

        # Add data quality indicators
        transformed['data_quality'] = self._assess_data_quality(data)

        return transformed

    def _analyze_inflation(self, data: List[Dict]) -> Dict:
        """Analyze inflation trends"""
        if not data:
            return {}

        latest = data[-1] if isinstance(data, list) else data
        previous = data[-2] if len(data) > 1 else None

        analysis = {
            'current_rate': latest.get('variacion_anual'),
            'monthly_change': latest.get('variacion_mensual'),
            'trend': 'stable'
        }

        if previous:
            if latest.get('variacion_anual', 0) > previous.get('variacion_anual', 0):
                analysis['trend'] = 'increasing'
            elif latest.get('variacion_anual', 0) < previous.get('variacion_anual', 0):
                analysis['trend'] = 'decreasing'

        # Check alert threshold
        if analysis['monthly_change'] and analysis['monthly_change'] > self.alert_thresholds['ipc_monthly_change']:
            analysis['alert'] = f"High monthly inflation: {analysis['monthly_change']}%"

        return analysis

    def _calculate_unemployment_rate(self, data: Dict) -> float:
        """Calculate unemployment rate from employment data"""
        if 'desocupados' in data and 'pea' in data:  # PEA = Población Económicamente Activa
            return (data['desocupados'] / data['pea']) * 100
        return 0.0

    def _calculate_trade_balance(self, data: Dict) -> Dict:
        """Calculate trade balance from trade data"""
        exports = data.get('exportaciones', 0)
        imports = data.get('importaciones', 0)

        return {
            'exports': exports,
            'imports': imports,
            'balance': exports - imports,
            'coverage_ratio': (exports / imports * 100) if imports > 0 else 0
        }

    def _check_economic_alerts(self, data: List[Dict]) -> List[Dict]:
        """Check for economic alert conditions"""
        alerts = []

        # Check each indicator against thresholds
        for indicator_data in data:
            if 'data' in indicator_data:
                # Check inflation
                if 'variacion_mensual' in indicator_data['data']:
                    if indicator_data['data']['variacion_mensual'] > self.alert_thresholds['ipc_monthly_change']:
                        alerts.append({
                            'type': 'inflation',
                            'severity': 'high',
                            'message': f"Monthly inflation exceeds {self.alert_thresholds['ipc_monthly_change']}%",
                            'value': indicator_data['data']['variacion_mensual']
                        })

                # Check unemployment
                if 'tasa_desempleo' in indicator_data['data']:
                    if indicator_data['data']['tasa_desempleo'] > self.alert_thresholds['unemployment_rate']:
                        alerts.append({
                            'type': 'unemployment',
                            'severity': 'high',
                            'message': f"Unemployment rate exceeds {self.alert_thresholds['unemployment_rate']}%",
                            'value': indicator_data['data']['tasa_desempleo']
                        })

        return alerts

    def _assess_data_quality(self, data: Any) -> Dict:
        """Assess quality of returned data"""
        quality = {
            'completeness': 100.0,
            'timeliness': 'current',
            'issues': []
        }

        if not data:
            quality['completeness'] = 0.0
            quality['issues'].append('No data returned')
        elif isinstance(data, dict):
            # Check for null values
            null_count = sum(1 for v in data.values() if v is None)
            if null_count > 0:
                quality['completeness'] = ((len(data) - null_count) / len(data)) * 100
                quality['issues'].append(f'{null_count} null values found')

        return quality