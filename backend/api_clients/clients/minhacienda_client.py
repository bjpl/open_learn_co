"""
MinHacienda (Ministerio de Hacienda y Crédito Público) API Client
Access Colombian fiscal data, budget information, and public finance statistics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import calendar

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class MinHaciendaClient(BaseAPIClient):
    """
    Client for MinHacienda API - Colombian Ministry of Finance and Public Credit
    Provides access to fiscal data, budget execution, debt information, and tax statistics
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize MinHacienda client"""
        default_config = {
            'base_url': 'https://www.minhacienda.gov.co/api',
            'api_key': None,  # May require API key for detailed data
            'cache_ttl': 1800,  # 30 minutes cache for fiscal data
            'rate_limit': 60
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # MinHacienda API endpoints
        self.endpoints = {
            'budget': 'presupuesto',  # Budget data
            'execution': 'ejecucion-presupuestal',  # Budget execution
            'revenue': 'ingresos',  # Government revenue
            'expenditure': 'gastos',  # Government expenditure
            'debt': 'deuda-publica',  # Public debt
            'fiscal_balance': 'balance-fiscal',  # Fiscal balance
            'tax_revenue': 'ingresos-tributarios',  # Tax revenue
            'transfers': 'transferencias',  # Intergovernmental transfers
            'investment': 'inversion-publica',  # Public investment
            'statistics': 'estadisticas-fiscales'  # Fiscal statistics
        }

        # Budget classifications
        self.budget_classifications = {
            'functional': 'Clasificación Funcional',
            'economic': 'Clasificación Económica',
            'institutional': 'Clasificación Institucional',
            'geographic': 'Clasificación Geográfica'
        }

        # Revenue categories
        self.revenue_categories = {
            'tax_revenue': 'Ingresos Tributarios',
            'non_tax_revenue': 'Ingresos No Tributarios',
            'capital_revenue': 'Ingresos de Capital',
            'transfers': 'Transferencias',
            'other_revenue': 'Otros Ingresos'
        }

        # Expenditure categories
        self.expenditure_categories = {
            'current_expenditure': 'Gasto Corriente',
            'capital_expenditure': 'Gasto de Capital',
            'debt_service': 'Servicio de la Deuda',
            'transfers': 'Transferencias'
        }

        # Alert thresholds
        self.alert_thresholds = {
            'deficit_gdp_ratio': 3.0,  # Alert if fiscal deficit > 3% of GDP
            'debt_gdp_ratio': 60.0,  # Alert if debt > 60% of GDP
            'execution_rate': 85.0,  # Alert if budget execution < 85%
            'revenue_shortfall': 10.0,  # Alert if revenue shortfall > 10%
            'debt_service_ratio': 25.0  # Alert if debt service > 25% of revenue
        }

    async def get_budget_data(
        self,
        year: Optional[int] = None,
        entity: Optional[str] = None,
        classification: str = 'functional',
        level: str = 'sector'
    ) -> Dict:
        """
        Get budget data by classification

        Args:
            year: Budget year
            entity: Specific entity (ministry, department)
            classification: Budget classification type
            level: Detail level (sector, program, project)

        Returns:
            Budget data with analysis
        """
        params = {
            'clasificacion': classification,
            'nivel': level
        }

        if year:
            params['año'] = year
        else:
            params['año'] = datetime.now().year

        if entity:
            params['entidad'] = entity

        data = await self.fetch_data(self.endpoints['budget'], params)

        # Add budget analysis
        if 'budget_data' in data:
            data['budget_analysis'] = {
                'total_budget': self._calculate_total_budget(data['budget_data']),
                'sector_distribution': self._analyze_sector_distribution(data['budget_data']),
                'priority_areas': self._identify_priority_areas(data['budget_data']),
                'comparison': await self._get_budget_comparison(year or datetime.now().year)
            }

        return data

    async def get_budget_execution(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        entity: Optional[str] = None,
        detailed: bool = False
    ) -> Dict:
        """
        Get budget execution data

        Args:
            year: Execution year
            month: Specific month (1-12)
            entity: Specific entity
            detailed: Include detailed breakdown

        Returns:
            Budget execution with performance analysis
        """
        params = {}

        if year:
            params['año'] = year
        if month:
            params['mes'] = month
        if entity:
            params['entidad'] = entity
        if detailed:
            params['detallado'] = True

        data = await self.fetch_data(self.endpoints['execution'], params)

        # Add execution analysis
        if 'execution_data' in data:
            data['execution_analysis'] = {
                'overall_execution_rate': self._calculate_execution_rate(data['execution_data']),
                'sector_performance': self._analyze_sector_performance(data['execution_data']),
                'monthly_progress': self._analyze_monthly_progress(data['execution_data']),
                'efficiency_metrics': self._calculate_efficiency_metrics(data['execution_data']),
                'alerts': self._check_execution_alerts(data['execution_data'])
            }

        return data

    async def get_revenue_data(
        self,
        revenue_type: Optional[str] = None,
        year: Optional[int] = None,
        monthly_breakdown: bool = False
    ) -> Dict:
        """
        Get government revenue data

        Args:
            revenue_type: Type of revenue (tax, non-tax, etc.)
            year: Specific year
            monthly_breakdown: Include monthly data

        Returns:
            Revenue data with analysis
        """
        params = {}

        if revenue_type:
            params['tipo'] = revenue_type
        if year:
            params['año'] = year
        if monthly_breakdown:
            params['mensual'] = True

        data = await self.fetch_data(self.endpoints['revenue'], params)

        # Add revenue analysis
        if 'revenue_data' in data:
            data['revenue_analysis'] = {
                'total_revenue': self._calculate_total_revenue(data['revenue_data']),
                'composition': self._analyze_revenue_composition(data['revenue_data']),
                'growth_rates': self._calculate_revenue_growth(data['revenue_data']),
                'seasonality': self._analyze_revenue_seasonality(data['revenue_data']),
                'forecasting': self._forecast_revenue(data['revenue_data'])
            }

        return data

    async def get_expenditure_data(
        self,
        expenditure_type: Optional[str] = None,
        year: Optional[int] = None,
        classification: str = 'economic'
    ) -> Dict:
        """
        Get government expenditure data

        Args:
            expenditure_type: Type of expenditure
            year: Specific year
            classification: Classification type

        Returns:
            Expenditure data with analysis
        """
        params = {
            'clasificacion': classification
        }

        if expenditure_type:
            params['tipo'] = expenditure_type
        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['expenditure'], params)

        # Add expenditure analysis
        if 'expenditure_data' in data:
            data['expenditure_analysis'] = {
                'total_expenditure': self._calculate_total_expenditure(data['expenditure_data']),
                'composition': self._analyze_expenditure_composition(data['expenditure_data']),
                'efficiency': self._assess_expenditure_efficiency(data['expenditure_data']),
                'priority_analysis': self._analyze_spending_priorities(data['expenditure_data'])
            }

        return data

    async def get_public_debt_data(
        self,
        debt_type: Optional[str] = None,
        currency: Optional[str] = None,
        include_projections: bool = False
    ) -> Dict:
        """
        Get public debt information

        Args:
            debt_type: Internal/external debt
            currency: Currency denomination
            include_projections: Include debt projections

        Returns:
            Public debt data with sustainability analysis
        """
        params = {}

        if debt_type:
            params['tipo'] = debt_type
        if currency:
            params['moneda'] = currency
        if include_projections:
            params['proyecciones'] = True

        data = await self.fetch_data(self.endpoints['debt'], params)

        # Add debt analysis
        if 'debt_data' in data:
            data['debt_analysis'] = {
                'total_debt': self._calculate_total_debt(data['debt_data']),
                'debt_composition': self._analyze_debt_composition(data['debt_data']),
                'sustainability_metrics': self._assess_debt_sustainability(data['debt_data']),
                'risk_assessment': self._assess_debt_risks(data['debt_data']),
                'servicing_capacity': self._assess_debt_servicing_capacity(data['debt_data'])
            }

        return data

    async def get_fiscal_balance(
        self,
        year: Optional[int] = None,
        level: str = 'central_government',
        quarterly: bool = False
    ) -> Dict:
        """
        Get fiscal balance data

        Args:
            year: Specific year
            level: Government level (central, general, regional)
            quarterly: Include quarterly breakdown

        Returns:
            Fiscal balance with sustainability analysis
        """
        params = {
            'nivel': level
        }

        if year:
            params['año'] = year
        if quarterly:
            params['trimestral'] = True

        data = await self.fetch_data(self.endpoints['fiscal_balance'], params)

        # Add fiscal analysis
        if 'balance_data' in data:
            data['fiscal_analysis'] = {
                'primary_balance': self._calculate_primary_balance(data['balance_data']),
                'overall_balance': self._calculate_overall_balance(data['balance_data']),
                'structural_balance': self._calculate_structural_balance(data['balance_data']),
                'sustainability_indicators': self._assess_fiscal_sustainability(data['balance_data']),
                'cyclical_adjustment': self._perform_cyclical_adjustment(data['balance_data'])
            }

        return data

    async def get_tax_statistics(
        self,
        tax_type: Optional[str] = None,
        taxpayer_category: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict:
        """
        Get tax revenue statistics

        Args:
            tax_type: Type of tax (VAT, income, etc.)
            taxpayer_category: Category of taxpayer
            year: Specific year

        Returns:
            Tax statistics with performance analysis
        """
        params = {}

        if tax_type:
            params['tipo_impuesto'] = tax_type
        if taxpayer_category:
            params['categoria_contribuyente'] = taxpayer_category
        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['tax_revenue'], params)

        # Add tax analysis
        if 'tax_data' in data:
            data['tax_analysis'] = {
                'collection_efficiency': self._calculate_collection_efficiency(data['tax_data']),
                'tax_burden': self._calculate_tax_burden(data['tax_data']),
                'compliance_rates': self._analyze_compliance_rates(data['tax_data']),
                'revenue_elasticity': self._calculate_revenue_elasticity(data['tax_data'])
            }

        return data

    async def get_intergovernmental_transfers(
        self,
        transfer_type: Optional[str] = None,
        recipient_level: str = 'department',
        year: Optional[int] = None
    ) -> Dict:
        """
        Get intergovernmental transfer data

        Args:
            transfer_type: Type of transfer (SGP, SGR, etc.)
            recipient_level: Level of recipient government
            year: Specific year

        Returns:
            Transfer data with equity analysis
        """
        params = {
            'nivel_receptor': recipient_level
        }

        if transfer_type:
            params['tipo_transferencia'] = transfer_type
        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['transfers'], params)

        # Add transfer analysis
        if 'transfer_data' in data:
            data['transfer_analysis'] = {
                'total_transfers': self._calculate_total_transfers(data['transfer_data']),
                'distribution_equity': self._analyze_distribution_equity(data['transfer_data']),
                'per_capita_analysis': self._analyze_per_capita_transfers(data['transfer_data']),
                'formula_effectiveness': self._assess_formula_effectiveness(data['transfer_data'])
            }

        return data

    async def get_fiscal_dashboard(
        self,
        year: Optional[int] = None
    ) -> Dict:
        """
        Get comprehensive fiscal dashboard

        Args:
            year: Specific year for analysis

        Returns:
            Comprehensive fiscal indicators dashboard
        """
        current_year = year or datetime.now().year

        # Fetch key fiscal indicators concurrently
        endpoints = [
            {'endpoint': self.endpoints['budget'], 'params': {'año': current_year}},
            {'endpoint': self.endpoints['execution'], 'params': {'año': current_year}},
            {'endpoint': self.endpoints['revenue'], 'params': {'año': current_year}},
            {'endpoint': self.endpoints['fiscal_balance'], 'params': {'año': current_year}},
            {'endpoint': self.endpoints['debt'], 'params': {}}
        ]

        results = await self.batch_fetch(endpoints, max_concurrent=5)

        # Create comprehensive dashboard
        dashboard = {
            'year': current_year,
            'timestamp': datetime.utcnow().isoformat(),
            'budget': results[0] if results else {},
            'execution': results[1] if len(results) > 1 else {},
            'revenue': results[2] if len(results) > 2 else {},
            'fiscal_balance': results[3] if len(results) > 3 else {},
            'debt': results[4] if len(results) > 4 else {},
            'fiscal_health': self._assess_overall_fiscal_health(results),
            'key_indicators': self._extract_key_indicators(results),
            'alerts': self._check_fiscal_alerts(results),
            'recommendations': self._generate_fiscal_recommendations(results)
        }

        return dashboard

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform MinHacienda API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        transformed = {
            'source': 'MinHacienda',
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Handle different response structures
        if 'datos_presupuestales' in response:
            transformed['budget_data'] = response['datos_presupuestales']
        elif 'ejecucion_presupuestal' in response:
            transformed['execution_data'] = response['ejecucion_presupuestal']
        elif 'ingresos' in response:
            transformed['revenue_data'] = response['ingresos']
        elif 'gastos' in response:
            transformed['expenditure_data'] = response['gastos']
        elif 'deuda_publica' in response:
            transformed['debt_data'] = response['deuda_publica']
        elif 'balance_fiscal' in response:
            transformed['balance_data'] = response['balance_fiscal']
        else:
            transformed.update(response)

        # Add fiscal period metadata
        if 'periodo_fiscal' in response:
            transformed['fiscal_period'] = response['periodo_fiscal']

        # Convert monetary values to standard format
        transformed = self._standardize_monetary_values(transformed)

        return transformed

    def _calculate_total_budget(self, budget_data: Dict) -> Dict:
        """Calculate total budget allocations"""
        if isinstance(budget_data, list):
            total = sum(item.get('monto_asignado', 0) for item in budget_data)
        else:
            total = budget_data.get('total_presupuesto', 0)

        return {
            'total_amount': total,
            'currency': 'COP',
            'year': budget_data.get('año') if isinstance(budget_data, dict) else None
        }

    def _calculate_execution_rate(self, execution_data: Dict) -> float:
        """Calculate overall budget execution rate"""
        if isinstance(execution_data, list):
            total_allocated = sum(item.get('monto_asignado', 0) for item in execution_data)
            total_executed = sum(item.get('monto_ejecutado', 0) for item in execution_data)
        else:
            total_allocated = execution_data.get('total_asignado', 0)
            total_executed = execution_data.get('total_ejecutado', 0)

        return (total_executed / total_allocated * 100) if total_allocated > 0 else 0

    def _analyze_sector_distribution(self, budget_data: Any) -> Dict:
        """Analyze budget distribution by sector"""
        if not isinstance(budget_data, list):
            return {}

        sector_totals = {}
        for item in budget_data:
            sector = item.get('sector', 'unknown')
            amount = item.get('monto_asignado', 0)
            sector_totals[sector] = sector_totals.get(sector, 0) + amount

        # Calculate percentages
        total = sum(sector_totals.values())
        sector_percentages = {
            sector: (amount / total * 100) if total > 0 else 0
            for sector, amount in sector_totals.items()
        }

        return {
            'sector_amounts': sector_totals,
            'sector_percentages': sector_percentages,
            'largest_sector': max(sector_totals.items(), key=lambda x: x[1])[0] if sector_totals else None
        }

    def _check_execution_alerts(self, execution_data: Dict) -> List[Dict]:
        """Check for budget execution alerts"""
        alerts = []

        execution_rate = self._calculate_execution_rate(execution_data)

        if execution_rate < self.alert_thresholds['execution_rate']:
            alerts.append({
                'type': 'low_execution',
                'severity': 'medium' if execution_rate > 70 else 'high',
                'message': f'Low budget execution rate: {execution_rate:.1f}%',
                'value': execution_rate
            })

        return alerts

    def _assess_debt_sustainability(self, debt_data: Dict) -> Dict:
        """Assess public debt sustainability"""
        debt_to_gdp = debt_data.get('deuda_pib_ratio', 0)
        debt_service_ratio = debt_data.get('servicio_deuda_ingresos_ratio', 0)

        sustainability = {
            'debt_to_gdp_ratio': debt_to_gdp,
            'debt_service_ratio': debt_service_ratio,
            'sustainability_rating': 'sustainable'
        }

        if debt_to_gdp > self.alert_thresholds['debt_gdp_ratio']:
            sustainability['sustainability_rating'] = 'high_risk'
        elif debt_to_gdp > 50:
            sustainability['sustainability_rating'] = 'moderate_risk'

        if debt_service_ratio > self.alert_thresholds['debt_service_ratio']:
            sustainability['sustainability_rating'] = 'high_risk'

        return sustainability

    def _assess_overall_fiscal_health(self, fiscal_data: List[Dict]) -> Dict:
        """Assess overall fiscal health"""
        health_score = 100  # Start with perfect score

        # Deduct points for various fiscal issues
        # This would implement a comprehensive scoring algorithm

        health_rating = 'excellent' if health_score >= 80 else 'good' if health_score >= 60 else 'poor'

        return {
            'health_score': health_score,
            'health_rating': health_rating,
            'key_concerns': [],
            'strengths': []
        }

    def _extract_key_indicators(self, fiscal_data: List[Dict]) -> Dict:
        """Extract key fiscal indicators"""
        return {
            'fiscal_deficit': 0,  # Would calculate from data
            'primary_balance': 0,
            'debt_to_gdp': 0,
            'revenue_growth': 0,
            'expenditure_growth': 0
        }

    def _check_fiscal_alerts(self, fiscal_data: List[Dict]) -> List[Dict]:
        """Check for fiscal alert conditions"""
        alerts = []

        # This would implement comprehensive fiscal alert logic
        # Based on various thresholds and indicators

        return alerts

    def _generate_fiscal_recommendations(self, fiscal_data: List[Dict]) -> List[str]:
        """Generate fiscal policy recommendations"""
        recommendations = []

        # This would implement intelligent recommendation generation
        # Based on fiscal analysis

        return recommendations

    def _standardize_monetary_values(self, data: Dict) -> Dict:
        """Standardize monetary values to consistent format"""
        # This would implement monetary value standardization
        # Converting different formats to consistent COP values

        return data

    async def _get_budget_comparison(self, year: int) -> Dict:
        """Get budget comparison with previous year"""
        try:
            previous_year_data = await self.get_budget_data(year - 1)
            # Implement comparison logic
            return {
                'year_over_year_change': 0,
                'major_changes': []
            }
        except:
            return {}

    async def test_connection(self) -> Dict:
        """
        Test connection to MinHacienda API

        Returns:
            Connection test results
        """
        try:
            # Test with a simple budget request
            result = await self.get_budget_data(year=datetime.now().year)

            if 'budget_data' in result or 'error' not in result:
                return {
                    'status': 'success',
                    'message': 'Successfully connected to MinHacienda API',
                    'data_available': bool(result.get('budget_data')),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'MinHacienda API responded with error',
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to MinHacienda API: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }