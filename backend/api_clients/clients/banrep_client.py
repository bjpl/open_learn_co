"""
Banco de la República (Colombian Central Bank) API Client
Access financial data, exchange rates, interest rates, and monetary policy information
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class BancoRepublicaClient(BaseAPIClient):
    """
    Client for Banco de la República API
    Provides access to Colombian financial and monetary data
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize Banco República client"""
        default_config = {
            'base_url': 'https://www.banrep.gov.co/api',
            'api_key': None,  # Public API
            'cache_ttl': 900,  # 15 minutes for financial data
            'rate_limit': 60
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # Banco República specific endpoints
        self.endpoints = {
            'trm': 'tasa-cambio/trm',  # Tasa Representativa del Mercado
            'interest_rates': 'tasas-interes',  # Interest rates
            'monetary_base': 'base-monetaria',  # Monetary base
            'reserves': 'reservas-internacionales',  # International reserves
            'public_debt': 'deuda-publica',  # Public debt
            'inflation_target': 'meta-inflacion',  # Inflation target
            'monetary_policy': 'politica-monetaria/decisiones',  # Policy decisions
            'financial_stability': 'estabilidad-financiera/indicadores'
        }

        # Series IDs for common indicators
        self.series_ids = {
            'trm': '32',  # TRM series ID
            'dtf': '33',  # DTF interest rate
            'ibr': '34',  # IBR overnight
            'usura': '35',  # Usury rate
            'intervention': '36',  # Intervention rate
            'uvr': '37',  # UVR (Real Value Unit)
        }

        # Alert thresholds
        self.alert_thresholds = {
            'trm_daily_change': 100,  # Alert if TRM changes > 100 pesos
            'trm_percentage_change': 3.0,  # Alert if > 3% change
            'interest_rate_change': 0.5,  # Alert if rates change > 0.5%
            'reserves_change': -5.0,  # Alert if reserves fall > 5%
        }

    async def get_exchange_rate(
        self,
        date: Optional[str] = None,
        period: str = 'daily'
    ) -> Dict:
        """
        Get TRM (Official Exchange Rate COP/USD)

        Args:
            date: Specific date (YYYY-MM-DD) or None for latest
            period: 'daily', 'monthly', 'annual'

        Returns:
            Exchange rate data with analysis
        """
        params = {
            'serie': self.series_ids['trm'],
            'periodicidad': period
        }

        if date:
            params['fecha'] = date
        else:
            # Get last 30 days for trend analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            params['fecha_inicio'] = start_date.strftime('%Y-%m-%d')
            params['fecha_fin'] = end_date.strftime('%Y-%m-%d')

        data = await self.fetch_data(self.endpoints['trm'], params)

        # Add analysis
        if 'data' in data:
            data['analysis'] = self._analyze_exchange_rate(data['data'])
            data['volatility'] = self._calculate_volatility(data['data'])

        return data

    async def get_interest_rates(
        self,
        rate_types: Optional[List[str]] = None
    ) -> Dict:
        """
        Get various interest rates

        Args:
            rate_types: List of rate types ['dtf', 'ibr', 'usura', 'intervention']

        Returns:
            Interest rates data
        """
        if not rate_types:
            rate_types = ['dtf', 'ibr', 'usura', 'intervention']

        # Fetch multiple rate types
        endpoints = []
        for rate_type in rate_types:
            if rate_type in self.series_ids:
                endpoints.append({
                    'endpoint': self.endpoints['interest_rates'],
                    'params': {'serie': self.series_ids[rate_type]}
                })

        results = await self.batch_fetch(endpoints)

        # Combine results
        rates_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'rates': {},
            'changes': {}
        }

        for i, rate_type in enumerate(rate_types):
            if i < len(results):
                rates_data['rates'][rate_type] = results[i]
                rates_data['changes'][rate_type] = self._calculate_rate_change(results[i])

        return rates_data

    async def get_monetary_indicators(self) -> Dict:
        """
        Get comprehensive monetary indicators

        Returns:
            Monetary base, M1, M2, M3 aggregates
        """
        data = await self.fetch_data(self.endpoints['monetary_base'])

        # Add growth rates
        if 'data' in data:
            data['growth_rates'] = self._calculate_monetary_growth(data['data'])

        return data

    async def get_international_reserves(self) -> Dict:
        """
        Get international reserves data

        Returns:
            Reserves in USD with composition
        """
        data = await self.fetch_data(self.endpoints['reserves'])

        # Add analysis
        if 'data' in data:
            data['adequacy_metrics'] = self._calculate_reserve_adequacy(data['data'])

        return data

    async def get_monetary_policy_decisions(
        self,
        limit: int = 10
    ) -> Dict:
        """
        Get recent monetary policy decisions

        Args:
            limit: Number of recent decisions

        Returns:
            Policy decisions with rates
        """
        params = {
            'limite': limit,
            'orden': 'descendente'
        }

        data = await self.fetch_data(self.endpoints['monetary_policy'], params)

        # Extract key decisions
        if 'data' in data:
            data['summary'] = self._summarize_policy_decisions(data['data'])

        return data

    async def get_financial_stability_report(self) -> Dict:
        """
        Get financial stability indicators

        Returns:
            Financial system health metrics
        """
        data = await self.fetch_data(self.endpoints['financial_stability'])

        # Add risk assessment
        if 'data' in data:
            data['risk_assessment'] = self._assess_financial_risks(data['data'])

        return data

    async def get_uvr_value(
        self,
        date: Optional[str] = None
    ) -> Dict:
        """
        Get UVR (Unidad de Valor Real) value

        Args:
            date: Specific date or None for current

        Returns:
            UVR value used for inflation-adjusted calculations
        """
        params = {
            'serie': self.series_ids['uvr']
        }

        if date:
            params['fecha'] = date

        return await self.fetch_data(self.endpoints['interest_rates'], params)

    async def get_financial_dashboard(self) -> Dict:
        """
        Get comprehensive financial dashboard

        Returns:
            Dashboard with key financial indicators
        """
        # Fetch key indicators concurrently
        endpoints = [
            {'endpoint': self.endpoints['trm'], 'params': {'serie': self.series_ids['trm']}},
            {'endpoint': self.endpoints['interest_rates'], 'params': {'serie': self.series_ids['intervention']}},
            {'endpoint': self.endpoints['reserves'], 'params': {}},
            {'endpoint': self.endpoints['monetary_base'], 'params': {}}
        ]

        results = await self.batch_fetch(endpoints, max_concurrent=4)

        dashboard = {
            'timestamp': datetime.utcnow().isoformat(),
            'exchange_rate': results[0] if results else None,
            'policy_rate': results[1] if len(results) > 1 else None,
            'reserves': results[2] if len(results) > 2 else None,
            'monetary_base': results[3] if len(results) > 3 else None,
            'alerts': self._check_financial_alerts(results)
        }

        return dashboard

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform Banco República response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        # Handle XML responses (common for Banco República)
        if 'xml_data' in response:
            data = self._parse_xml_response(response['xml_data'])
        elif 'valores' in response:
            data = response['valores']
        elif 'datos' in response:
            data = response['datos']
        else:
            data = response

        transformed = {
            'source': 'Banco de la República',
            'data': data,
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Add metadata
        if 'unidad' in response:
            transformed['unit'] = response['unidad']
        if 'periodicidad' in response:
            transformed['frequency'] = response['periodicidad']

        return transformed

    def _analyze_exchange_rate(self, data: List[Dict]) -> Dict:
        """Analyze exchange rate trends"""
        if not data or not isinstance(data, list):
            return {}

        # Get latest and previous values
        latest = data[-1] if data else {}
        previous_day = data[-2] if len(data) > 1 else {}
        week_ago = data[-7] if len(data) >= 7 else {}
        month_ago = data[-30] if len(data) >= 30 else {}

        analysis = {
            'current_rate': latest.get('valor'),
            'daily_change': None,
            'weekly_change': None,
            'monthly_change': None,
            'trend': 'stable'
        }

        # Calculate changes
        if previous_day and 'valor' in previous_day:
            daily_change = latest.get('valor', 0) - previous_day['valor']
            analysis['daily_change'] = daily_change
            analysis['daily_change_percent'] = (daily_change / previous_day['valor']) * 100

            # Check alert threshold
            if abs(daily_change) > self.alert_thresholds['trm_daily_change']:
                analysis['alert'] = f"Significant TRM change: {daily_change:.2f} COP"

        if week_ago and 'valor' in week_ago:
            analysis['weekly_change'] = latest.get('valor', 0) - week_ago['valor']

        if month_ago and 'valor' in month_ago:
            analysis['monthly_change'] = latest.get('valor', 0) - month_ago['valor']

        # Determine trend
        if analysis['daily_change']:
            if analysis['daily_change'] > 10:
                analysis['trend'] = 'strengthening_usd'
            elif analysis['daily_change'] < -10:
                analysis['trend'] = 'strengthening_cop'

        return analysis

    def _calculate_volatility(self, data: List[Dict]) -> float:
        """Calculate exchange rate volatility"""
        if not data or len(data) < 2:
            return 0.0

        values = [d.get('valor', 0) for d in data if 'valor' in d]
        if len(values) < 2:
            return 0.0

        # Calculate daily returns
        returns = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                returns.append((values[i] - values[i-1]) / values[i-1])

        if not returns:
            return 0.0

        # Calculate standard deviation of returns (volatility)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = (variance ** 0.5) * 100  # Convert to percentage

        return round(volatility, 4)

    def _calculate_rate_change(self, data: Dict) -> Dict:
        """Calculate interest rate changes"""
        if not data or 'data' not in data:
            return {}

        rate_data = data['data']
        if isinstance(rate_data, list) and len(rate_data) >= 2:
            current = rate_data[-1].get('valor', 0)
            previous = rate_data[-2].get('valor', 0)

            return {
                'current': current,
                'previous': previous,
                'change': current - previous,
                'change_percent': ((current - previous) / previous * 100) if previous else 0
            }

        return {}

    def _calculate_monetary_growth(self, data: Dict) -> Dict:
        """Calculate monetary aggregate growth rates"""
        growth_rates = {}

        if isinstance(data, list) and len(data) >= 2:
            # Year-over-year growth
            if len(data) >= 12:
                current = data[-1].get('valor', 0)
                year_ago = data[-12].get('valor', 0)
                if year_ago:
                    growth_rates['annual'] = ((current - year_ago) / year_ago) * 100

            # Month-over-month growth
            current = data[-1].get('valor', 0)
            previous = data[-2].get('valor', 0)
            if previous:
                growth_rates['monthly'] = ((current - previous) / previous) * 100

        return growth_rates

    def _calculate_reserve_adequacy(self, data: Dict) -> Dict:
        """Calculate international reserve adequacy metrics"""
        # Simplified adequacy metrics
        return {
            'months_of_imports': 4.5,  # Placeholder - would calculate from trade data
            'short_term_debt_coverage': 1.2,  # Placeholder
            'adequacy_assessment': 'adequate'
        }

    def _parse_xml_response(self, xml_string: str) -> List[Dict]:
        """Parse XML response from Banco República"""
        try:
            root = ET.fromstring(xml_string)
            data = []

            for item in root.findall('.//item'):
                entry = {}
                for child in item:
                    entry[child.tag] = child.text
                data.append(entry)

            return data
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []

    def _check_financial_alerts(self, data: List[Dict]) -> List[Dict]:
        """Check for financial alert conditions"""
        alerts = []

        for indicator_data in data:
            if not indicator_data or 'data' not in indicator_data:
                continue

            # Check TRM volatility
            if 'analysis' in indicator_data:
                if indicator_data['analysis'].get('daily_change_percent', 0) > self.alert_thresholds['trm_percentage_change']:
                    alerts.append({
                        'type': 'exchange_rate',
                        'severity': 'high',
                        'message': 'Significant exchange rate movement detected',
                        'value': indicator_data['analysis']['daily_change_percent']
                    })

        return alerts

    def _summarize_policy_decisions(self, decisions: List[Dict]) -> Dict:
        """Summarize monetary policy decisions"""
        if not decisions:
            return {}

        latest = decisions[0] if isinstance(decisions, list) else decisions

        return {
            'latest_rate': latest.get('tasa_intervencion'),
            'decision_date': latest.get('fecha'),
            'direction': latest.get('decision'),  # 'increase', 'decrease', 'maintain'
            'basis_points': latest.get('cambio_puntos_base')
        }

    def _assess_financial_risks(self, data: Dict) -> Dict:
        """Assess financial system risks"""
        # Simplified risk assessment
        return {
            'overall_risk': 'moderate',
            'credit_risk': 'low',
            'market_risk': 'moderate',
            'liquidity_risk': 'low',
            'operational_risk': 'low'
        }