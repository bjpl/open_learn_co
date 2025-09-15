"""
SECOP (Sistema Electrónico de Contratación Pública) API Client
Access Colombian public procurement data and contract information
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class SECOPClient(BaseAPIClient):
    """
    Client for SECOP API - Colombian Public Procurement System
    Provides access to public contracts, tenders, and procurement data
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize SECOP client"""
        default_config = {
            'base_url': 'https://www.colombiacompra.gov.co/api',
            'api_key': None,  # May require API key for some endpoints
            'cache_ttl': 1800,  # 30 minutes cache for procurement data
            'rate_limit': 60,  # Conservative rate limit
            'timeout': 60  # Longer timeout for large datasets
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # SECOP API endpoints
        self.endpoints = {
            'contracts': 'contratos',  # Contract search
            'processes': 'procesos',  # Procurement processes
            'entities': 'entidades',  # Contracting entities
            'contractors': 'contratistas',  # Contractors/suppliers
            'awards': 'adjudicaciones',  # Contract awards
            'amendments': 'adiciones',  # Contract amendments
            'statistics': 'estadisticas',  # Procurement statistics
            'budget': 'presupuesto',  # Budget execution
            'monitoring': 'seguimiento'  # Contract monitoring
        }

        # Contract states
        self.contract_states = {
            'convocado': 'Called for bids',
            'adjudicado': 'Awarded',
            'celebrado': 'Executed',
            'liquidado': 'Liquidated',
            'terminado': 'Terminated',
            'suspendido': 'Suspended',
            'desierto': 'Declared void'
        }

        # Procurement types
        self.procurement_types = {
            'LA': 'Licitación Pública',  # Public tender
            'SA': 'Selección Abreviada',  # Abbreviated selection
            'MC': 'Mínima Cuantía',  # Minimum amount
            'CD': 'Contratación Directa',  # Direct contracting
            'CE': 'Concurso de Méritos',  # Merit contest
            'LP': 'Licitación Privada'  # Private tender
        }

        # Alert thresholds
        self.alert_thresholds = {
            'high_value_contract': 10_000_000_000,  # 10 billion COP
            'cost_overrun_percentage': 20.0,  # Alert if contract increases > 20%
            'execution_delay_days': 30,  # Alert if delayed > 30 days
            'concentration_ratio': 0.3  # Alert if single contractor > 30% of entity's contracts
        }

    async def search_contracts(
        self,
        entity_name: Optional[str] = None,
        contractor_name: Optional[str] = None,
        contract_type: Optional[str] = None,
        value_min: Optional[float] = None,
        value_max: Optional[float] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        state: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict:
        """
        Search public contracts with filters

        Args:
            entity_name: Contracting entity name
            contractor_name: Contractor/supplier name
            contract_type: Type of procurement
            value_min: Minimum contract value (COP)
            value_max: Maximum contract value (COP)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            state: Contract state
            page: Page number for pagination
            page_size: Number of results per page

        Returns:
            Contract search results with metadata
        """
        params = {
            'pagina': page,
            'limite': min(page_size, 1000)  # API limit
        }

        # Add filters
        if entity_name:
            params['entidad'] = entity_name
        if contractor_name:
            params['contratista'] = contractor_name
        if contract_type:
            params['tipo_contratacion'] = contract_type
        if value_min:
            params['valor_minimo'] = value_min
        if value_max:
            params['valor_maximo'] = value_max
        if date_from:
            params['fecha_desde'] = date_from
        if date_to:
            params['fecha_hasta'] = date_to
        if state:
            params['estado'] = state

        data = await self.fetch_data(self.endpoints['contracts'], params)

        # Add search analytics
        if 'results' in data:
            data['analytics'] = self._analyze_contract_search(data['results'])
            data['pagination'] = {
                'current_page': page,
                'page_size': page_size,
                'total_results': data.get('total', 0),
                'has_next': len(data['results']) == page_size
            }

        return data

    async def get_contract_details(
        self,
        contract_id: str,
        include_amendments: bool = True,
        include_payments: bool = True
    ) -> Dict:
        """
        Get detailed information about a specific contract

        Args:
            contract_id: Contract identifier
            include_amendments: Include contract amendments
            include_payments: Include payment information

        Returns:
            Detailed contract information
        """
        params = {
            'id': contract_id,
            'incluir_adiciones': include_amendments,
            'incluir_pagos': include_payments
        }

        data = await self.fetch_data(self.endpoints['contracts'], params)

        if 'result' in data:
            contract = data['result']

            # Add analysis
            data['analysis'] = {
                'risk_score': self._calculate_contract_risk(contract),
                'execution_status': self._analyze_execution_status(contract),
                'cost_analysis': self._analyze_contract_costs(contract),
                'timeline_analysis': self._analyze_contract_timeline(contract)
            }

            # Check for alerts
            data['alerts'] = self._check_contract_alerts(contract)

        return data

    async def get_entity_contracts(
        self,
        entity_id: str,
        year: Optional[int] = None,
        include_statistics: bool = True
    ) -> Dict:
        """
        Get all contracts for a specific entity

        Args:
            entity_id: Entity identifier
            year: Filter by year
            include_statistics: Include statistical analysis

        Returns:
            Entity contracts with analytics
        """
        params = {
            'entidad_id': entity_id
        }

        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['contracts'], params)

        if 'results' in data and include_statistics:
            contracts = data['results']

            # Calculate entity statistics
            data['entity_statistics'] = {
                'total_contracts': len(contracts),
                'total_value': sum(c.get('valor_contrato', 0) for c in contracts),
                'average_value': sum(c.get('valor_contrato', 0) for c in contracts) / len(contracts) if contracts else 0,
                'contract_types': self._count_contract_types(contracts),
                'top_contractors': self._get_top_contractors(contracts),
                'monthly_distribution': self._get_monthly_distribution(contracts),
                'execution_rates': self._calculate_execution_rates(contracts)
            }

            # Risk analysis
            data['risk_analysis'] = {
                'concentration_risk': self._assess_contractor_concentration(contracts),
                'cost_overruns': self._identify_cost_overruns(contracts),
                'delayed_contracts': self._identify_delayed_contracts(contracts)
            }

        return data

    async def get_contractor_profile(
        self,
        contractor_id: str,
        include_performance: bool = True
    ) -> Dict:
        """
        Get contractor profile and performance history

        Args:
            contractor_id: Contractor identifier
            include_performance: Include performance metrics

        Returns:
            Contractor profile with performance data
        """
        data = await self.fetch_data(self.endpoints['contractors'], {'id': contractor_id})

        if 'result' in data and include_performance:
            contractor = data['result']

            # Get contractor's contracts
            contracts_data = await self.search_contracts(
                contractor_name=contractor.get('nombre'),
                page_size=1000
            )

            if 'results' in contracts_data:
                contracts = contracts_data['results']

                data['performance_metrics'] = {
                    'total_contracts': len(contracts),
                    'total_value': sum(c.get('valor_contrato', 0) for c in contracts),
                    'success_rate': self._calculate_success_rate(contracts),
                    'average_execution_time': self._calculate_avg_execution_time(contracts),
                    'cost_performance': self._analyze_cost_performance(contracts),
                    'entity_diversity': len(set(c.get('entidad_id') for c in contracts)),
                    'sector_specialization': self._analyze_sector_specialization(contracts)
                }

                # Risk indicators
                data['risk_indicators'] = {
                    'contract_failures': self._count_contract_failures(contracts),
                    'cost_overrun_frequency': self._calculate_overrun_frequency(contracts),
                    'delay_frequency': self._calculate_delay_frequency(contracts)
                }

        return data

    async def get_procurement_statistics(
        self,
        year: Optional[int] = None,
        entity_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict:
        """
        Get procurement statistics and trends

        Args:
            year: Filter by year
            entity_type: Type of entity
            region: Geographic region

        Returns:
            Procurement statistics and analytics
        """
        params = {}

        if year:
            params['año'] = year
        if entity_type:
            params['tipo_entidad'] = entity_type
        if region:
            params['region'] = region

        data = await self.fetch_data(self.endpoints['statistics'], params)

        # Add trend analysis
        if 'data' in data:
            data['trend_analysis'] = self._analyze_procurement_trends(data['data'])
            data['efficiency_metrics'] = self._calculate_efficiency_metrics(data['data'])
            data['transparency_score'] = self._calculate_transparency_score(data['data'])

        return data

    async def monitor_high_value_contracts(
        self,
        threshold: float = None,
        days_back: int = 30
    ) -> Dict:
        """
        Monitor high-value contracts for potential issues

        Args:
            threshold: Value threshold (defaults to alert threshold)
            days_back: Days to look back

        Returns:
            High-value contracts with risk analysis
        """
        threshold = threshold or self.alert_thresholds['high_value_contract']
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        high_value_contracts = await self.search_contracts(
            value_min=threshold,
            date_from=date_from,
            page_size=500
        )

        if 'results' in high_value_contracts:
            contracts = high_value_contracts['results']

            # Analyze each contract for risks
            risk_analysis = []
            for contract in contracts:
                risk_score = self._calculate_contract_risk(contract)
                if risk_score > 70:  # High risk threshold
                    risk_analysis.append({
                        'contract': contract,
                        'risk_score': risk_score,
                        'risk_factors': self._identify_risk_factors(contract)
                    })

            high_value_contracts['risk_analysis'] = risk_analysis
            high_value_contracts['summary'] = {
                'total_high_value': len(contracts),
                'total_value': sum(c.get('valor_contrato', 0) for c in contracts),
                'high_risk_count': len(risk_analysis),
                'average_risk_score': sum(r['risk_score'] for r in risk_analysis) / len(risk_analysis) if risk_analysis else 0
            }

        return high_value_contracts

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform SECOP API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        transformed = {
            'source': 'SECOP',
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Handle different response structures
        if 'datos' in response:
            transformed['data'] = response['datos']
        elif 'resultados' in response:
            transformed['results'] = response['resultados']
        elif 'contratos' in response:
            transformed['results'] = response['contratos']
        else:
            transformed.update(response)

        # Add pagination metadata if present
        if 'total' in response:
            transformed['total'] = response['total']
        if 'pagina' in response:
            transformed['pagination'] = {
                'current_page': response['pagina'],
                'total_pages': response.get('total_paginas'),
                'has_next': response.get('siguiente', False)
            }

        return transformed

    def _analyze_contract_search(self, contracts: List[Dict]) -> Dict:
        """Analyze contract search results"""
        if not contracts:
            return {}

        total_value = sum(c.get('valor_contrato', 0) for c in contracts)
        contract_types = {}
        states = {}

        for contract in contracts:
            # Count contract types
            contract_type = contract.get('tipo_contratacion', 'unknown')
            contract_types[contract_type] = contract_types.get(contract_type, 0) + 1

            # Count states
            state = contract.get('estado', 'unknown')
            states[state] = states.get(state, 0) + 1

        return {
            'total_contracts': len(contracts),
            'total_value': total_value,
            'average_value': total_value / len(contracts),
            'contract_types': contract_types,
            'contract_states': states,
            'value_distribution': self._calculate_value_distribution(contracts)
        }

    def _calculate_contract_risk(self, contract: Dict) -> float:
        """Calculate risk score for a contract (0-100)"""
        risk_score = 0.0

        # High value risk (20 points)
        value = contract.get('valor_contrato', 0)
        if value > self.alert_thresholds['high_value_contract']:
            risk_score += 20
        elif value > self.alert_thresholds['high_value_contract'] / 2:
            risk_score += 10

        # Contract type risk (15 points)
        contract_type = contract.get('tipo_contratacion', '')
        if contract_type == 'CD':  # Direct contracting
            risk_score += 15
        elif contract_type in ['SA', 'MC']:
            risk_score += 8

        # Timeline risk (20 points)
        start_date = contract.get('fecha_inicio')
        end_date = contract.get('fecha_fin')
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                duration = (end - start).days

                if duration > 365:  # Long-term contracts
                    risk_score += 20
                elif duration > 180:
                    risk_score += 10
            except:
                risk_score += 5  # Invalid dates

        # Amendment risk (20 points)
        amendments = contract.get('adiciones', [])
        if len(amendments) > 3:
            risk_score += 20
        elif len(amendments) > 1:
            risk_score += 10

        # Cost overrun risk (25 points)
        original_value = contract.get('valor_inicial', value)
        if original_value and value > original_value:
            overrun_pct = ((value - original_value) / original_value) * 100
            if overrun_pct > self.alert_thresholds['cost_overrun_percentage']:
                risk_score += 25
            elif overrun_pct > 10:
                risk_score += 15

        return min(risk_score, 100.0)

    def _analyze_execution_status(self, contract: Dict) -> Dict:
        """Analyze contract execution status"""
        status = {
            'state': contract.get('estado', 'unknown'),
            'progress_percentage': 0,
            'is_delayed': False,
            'delay_days': 0
        }

        # Calculate progress based on dates
        start_date = contract.get('fecha_inicio')
        end_date = contract.get('fecha_fin')
        current_date = datetime.now()

        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                if current_date < start.replace(tzinfo=None):
                    status['progress_percentage'] = 0
                elif current_date > end.replace(tzinfo=None):
                    status['progress_percentage'] = 100
                    status['is_delayed'] = True
                    status['delay_days'] = (current_date - end.replace(tzinfo=None)).days
                else:
                    total_days = (end - start).days
                    elapsed_days = (current_date - start.replace(tzinfo=None)).days
                    status['progress_percentage'] = (elapsed_days / total_days) * 100 if total_days > 0 else 0
            except:
                pass

        return status

    def _analyze_contract_costs(self, contract: Dict) -> Dict:
        """Analyze contract cost structure"""
        initial_value = contract.get('valor_inicial', 0)
        current_value = contract.get('valor_contrato', 0)
        amendments = contract.get('adiciones', [])

        cost_analysis = {
            'initial_value': initial_value,
            'current_value': current_value,
            'total_amendments': len(amendments),
            'amendment_value': sum(a.get('valor', 0) for a in amendments),
            'cost_increase': current_value - initial_value if initial_value else 0,
            'cost_increase_percentage': ((current_value - initial_value) / initial_value * 100) if initial_value else 0
        }

        # Categorize cost increase
        if cost_analysis['cost_increase_percentage'] > 50:
            cost_analysis['cost_category'] = 'high_increase'
        elif cost_analysis['cost_increase_percentage'] > 20:
            cost_analysis['cost_category'] = 'moderate_increase'
        elif cost_analysis['cost_increase_percentage'] > 0:
            cost_analysis['cost_category'] = 'slight_increase'
        else:
            cost_analysis['cost_category'] = 'no_increase'

        return cost_analysis

    def _analyze_contract_timeline(self, contract: Dict) -> Dict:
        """Analyze contract timeline"""
        timeline = {
            'planned_duration_days': 0,
            'actual_duration_days': 0,
            'is_overdue': False,
            'extension_count': 0
        }

        start_date = contract.get('fecha_inicio')
        end_date = contract.get('fecha_fin')
        actual_end = contract.get('fecha_fin_real') or end_date

        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                planned_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                timeline['planned_duration_days'] = (planned_end - start).days

                if actual_end:
                    actual_end_date = datetime.fromisoformat(actual_end.replace('Z', '+00:00'))
                    timeline['actual_duration_days'] = (actual_end_date - start).days
                    timeline['is_overdue'] = actual_end_date > planned_end
            except:
                pass

        # Count timeline extensions
        amendments = contract.get('adiciones', [])
        timeline['extension_count'] = len([a for a in amendments if a.get('tipo') == 'tiempo'])

        return timeline

    def _check_contract_alerts(self, contract: Dict) -> List[Dict]:
        """Check contract for alert conditions"""
        alerts = []

        # High value alert
        value = contract.get('valor_contrato', 0)
        if value > self.alert_thresholds['high_value_contract']:
            alerts.append({
                'type': 'high_value',
                'severity': 'high',
                'message': f'High-value contract: {value:,.0f} COP',
                'value': value
            })

        # Cost overrun alert
        initial_value = contract.get('valor_inicial', 0)
        if initial_value and value > initial_value:
            overrun_pct = ((value - initial_value) / initial_value) * 100
            if overrun_pct > self.alert_thresholds['cost_overrun_percentage']:
                alerts.append({
                    'type': 'cost_overrun',
                    'severity': 'medium',
                    'message': f'Significant cost increase: {overrun_pct:.1f}%',
                    'value': overrun_pct
                })

        # Timeline alert
        end_date = contract.get('fecha_fin')
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                days_overdue = (datetime.now() - end.replace(tzinfo=None)).days
                if days_overdue > self.alert_thresholds['execution_delay_days']:
                    alerts.append({
                        'type': 'execution_delay',
                        'severity': 'medium',
                        'message': f'Contract overdue by {days_overdue} days',
                        'value': days_overdue
                    })
            except:
                pass

        return alerts

    def _count_contract_types(self, contracts: List[Dict]) -> Dict:
        """Count contracts by type"""
        types = {}
        for contract in contracts:
            contract_type = contract.get('tipo_contratacion', 'unknown')
            types[contract_type] = types.get(contract_type, 0) + 1
        return types

    def _get_top_contractors(self, contracts: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top contractors by value"""
        contractor_values = {}
        for contract in contracts:
            contractor = contract.get('contratista', 'unknown')
            value = contract.get('valor_contrato', 0)
            contractor_values[contractor] = contractor_values.get(contractor, 0) + value

        sorted_contractors = sorted(
            contractor_values.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'name': name, 'total_value': value}
            for name, value in sorted_contractors[:limit]
        ]

    def _calculate_value_distribution(self, contracts: List[Dict]) -> Dict:
        """Calculate value distribution of contracts"""
        values = [c.get('valor_contrato', 0) for c in contracts if c.get('valor_contrato')]

        if not values:
            return {}

        values.sort()
        n = len(values)

        return {
            'min': values[0],
            'max': values[-1],
            'median': values[n // 2],
            'q1': values[n // 4],
            'q3': values[3 * n // 4],
            'mean': sum(values) / len(values)
        }

    async def test_connection(self) -> Dict:
        """
        Test connection to SECOP API

        Returns:
            Connection test results
        """
        try:
            # Test with a simple search
            result = await self.search_contracts(page_size=1)

            if 'results' in result or 'error' not in result:
                return {
                    'status': 'success',
                    'message': 'Successfully connected to SECOP API',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'SECOP API responded with error',
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to SECOP API: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }