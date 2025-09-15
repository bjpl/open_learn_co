"""
DNP (Departamento Nacional de Planeación) API Client
Access Colombian national planning data, development indicators, and territorial statistics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class DNPClient(BaseAPIClient):
    """
    Client for DNP API - Colombian National Planning Department
    Provides access to development indicators, territorial data, and planning information
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize DNP client"""
        default_config = {
            'base_url': 'https://www.dnp.gov.co/api',
            'api_key': None,  # Some endpoints may require API key
            'cache_ttl': 3600,  # 1 hour cache for planning data
            'rate_limit': 80
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # DNP API endpoints
        self.endpoints = {
            'indicators': 'indicadores',  # Development indicators
            'territorial': 'territorial',  # Territorial data
            'pnd': 'plan-nacional-desarrollo',  # National Development Plan
            'projects': 'proyectos',  # Public investment projects
            'sgr': 'sgr',  # Sistema General de Regalías
            'peace': 'paz',  # Peace-building indicators
            'pdet': 'pdet',  # Development Programs with Territorial Focus
            'statistics': 'estadisticas',  # Statistical data
            'maps': 'mapas',  # Geographic information
            'budget': 'presupuesto'  # Budget allocation
        }

        # Development dimensions
        self.development_dimensions = {
            'social': 'Desarrollo Social',
            'economic': 'Desarrollo Económico',
            'environmental': 'Sostenibilidad Ambiental',
            'institutional': 'Fortalecimiento Institucional',
            'infrastructure': 'Infraestructura',
            'innovation': 'Ciencia, Tecnología e Innovación'
        }

        # Geographic levels
        self.geographic_levels = {
            'national': 'Nacional',
            'regional': 'Regional',
            'departmental': 'Departamental',
            'municipal': 'Municipal',
            'veredal': 'Veredal'
        }

        # Alert thresholds for development indicators
        self.alert_thresholds = {
            'poverty_rate': 30.0,  # Alert if poverty > 30%
            'nbi_rate': 25.0,  # Unsatisfied Basic Needs > 25%
            'education_coverage': 85.0,  # Alert if coverage < 85%
            'health_coverage': 90.0,  # Alert if coverage < 90%
            'project_execution': 70.0  # Alert if execution < 70%
        }

    async def get_development_indicators(
        self,
        dimension: Optional[str] = None,
        geographic_level: str = 'departmental',
        entities: Optional[List[str]] = None,
        year: Optional[int] = None
    ) -> Dict:
        """
        Get development indicators

        Args:
            dimension: Development dimension
            geographic_level: Geographic aggregation level
            entities: List of entity codes/names
            year: Specific year (default: latest)

        Returns:
            Development indicators with analysis
        """
        params = {
            'nivel_geografico': geographic_level
        }

        if dimension:
            params['dimension'] = dimension
        if entities:
            params['entidades'] = ','.join(entities)
        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['indicators'], params)

        # Add analysis
        if 'indicators' in data:
            data['analysis'] = {
                'ranking': self._calculate_development_ranking(data['indicators']),
                'gaps': self._identify_development_gaps(data['indicators']),
                'trends': self._analyze_indicator_trends(data['indicators']),
                'alerts': self._check_development_alerts(data['indicators'])
            }

        return data

    async def get_territorial_data(
        self,
        department: Optional[str] = None,
        municipality: Optional[str] = None,
        include_subregions: bool = True
    ) -> Dict:
        """
        Get territorial characterization data

        Args:
            department: Department name or code
            municipality: Municipality name or code
            include_subregions: Include subregional data

        Returns:
            Territorial data with analysis
        """
        params = {}

        if department:
            params['departamento'] = department
        if municipality:
            params['municipio'] = municipality
        if include_subregions:
            params['incluir_subregiones'] = True

        data = await self.fetch_data(self.endpoints['territorial'], params)

        # Add territorial analysis
        if 'territorial_data' in data:
            data['territorial_analysis'] = {
                'demographic_profile': self._analyze_demographic_profile(data['territorial_data']),
                'economic_profile': self._analyze_economic_profile(data['territorial_data']),
                'development_index': self._calculate_territorial_development_index(data['territorial_data']),
                'challenges': self._identify_territorial_challenges(data['territorial_data'])
            }

        return data

    async def get_national_development_plan(
        self,
        plan_period: Optional[str] = None,
        strategic_objective: Optional[str] = None
    ) -> Dict:
        """
        Get National Development Plan data

        Args:
            plan_period: Plan period (e.g., '2018-2022')
            strategic_objective: Specific strategic objective

        Returns:
            PND data with execution analysis
        """
        params = {}

        if plan_period:
            params['periodo'] = plan_period
        if strategic_objective:
            params['objetivo'] = strategic_objective

        data = await self.fetch_data(self.endpoints['pnd'], params)

        # Add execution analysis
        if 'plan_data' in data:
            data['execution_analysis'] = {
                'overall_progress': self._calculate_overall_progress(data['plan_data']),
                'strategic_progress': self._analyze_strategic_progress(data['plan_data']),
                'sector_performance': self._analyze_sector_performance(data['plan_data']),
                'regional_implementation': self._analyze_regional_implementation(data['plan_data'])
            }

        return data

    async def get_public_investment_projects(
        self,
        sector: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        value_min: Optional[float] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict:
        """
        Get public investment projects

        Args:
            sector: Project sector
            department: Department filter
            status: Project status
            value_min: Minimum project value
            page: Page number
            page_size: Results per page

        Returns:
            Investment projects with analysis
        """
        params = {
            'pagina': page,
            'limite': page_size
        }

        if sector:
            params['sector'] = sector
        if department:
            params['departamento'] = department
        if status:
            params['estado'] = status
        if value_min:
            params['valor_minimo'] = value_min

        data = await self.fetch_data(self.endpoints['projects'], params)

        # Add investment analysis
        if 'projects' in data:
            data['investment_analysis'] = {
                'total_investment': self._calculate_total_investment(data['projects']),
                'sector_distribution': self._analyze_sector_distribution(data['projects']),
                'regional_distribution': self._analyze_regional_distribution(data['projects']),
                'execution_status': self._analyze_execution_status(data['projects']),
                'impact_assessment': self._assess_project_impact(data['projects'])
            }

        return data

    async def get_royalties_data(
        self,
        fund_type: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict:
        """
        Get Sistema General de Regalías (SGR) data

        Args:
            fund_type: Type of royalty fund
            department: Department filter
            year: Specific year

        Returns:
            Royalties data with distribution analysis
        """
        params = {}

        if fund_type:
            params['tipo_fondo'] = fund_type
        if department:
            params['departamento'] = department
        if year:
            params['año'] = year

        data = await self.fetch_data(self.endpoints['sgr'], params)

        # Add royalties analysis
        if 'royalties_data' in data:
            data['royalties_analysis'] = {
                'total_distribution': self._calculate_royalty_distribution(data['royalties_data']),
                'per_capita_distribution': self._calculate_per_capita_royalties(data['royalties_data']),
                'fund_performance': self._analyze_fund_performance(data['royalties_data']),
                'territorial_equity': self._assess_territorial_equity(data['royalties_data'])
            }

        return data

    async def get_peace_indicators(
        self,
        municipality: Optional[str] = None,
        indicator_type: Optional[str] = None,
        pdet_only: bool = False
    ) -> Dict:
        """
        Get peace-building indicators

        Args:
            municipality: Municipality filter
            indicator_type: Type of peace indicator
            pdet_only: Only PDET municipalities

        Returns:
            Peace indicators with progress analysis
        """
        params = {}

        if municipality:
            params['municipio'] = municipality
        if indicator_type:
            params['tipo_indicador'] = indicator_type
        if pdet_only:
            params['solo_pdet'] = True

        data = await self.fetch_data(self.endpoints['peace'], params)

        # Add peace analysis
        if 'peace_indicators' in data:
            data['peace_analysis'] = {
                'progress_index': self._calculate_peace_progress_index(data['peace_indicators']),
                'territorial_priorities': self._identify_territorial_priorities(data['peace_indicators']),
                'implementation_gaps': self._identify_implementation_gaps(data['peace_indicators']),
                'sustainability_assessment': self._assess_peace_sustainability(data['peace_indicators'])
            }

        return data

    async def get_pdet_data(
        self,
        subregion: Optional[str] = None,
        pillar: Optional[str] = None
    ) -> Dict:
        """
        Get PDET (Programas de Desarrollo con Enfoque Territorial) data

        Args:
            subregion: PDET subregion
            pillar: Development pillar

        Returns:
            PDET data with implementation analysis
        """
        params = {}

        if subregion:
            params['subregion'] = subregion
        if pillar:
            params['pilar'] = pillar

        data = await self.fetch_data(self.endpoints['pdet'], params)

        # Add PDET analysis
        if 'pdet_data' in data:
            data['pdet_analysis'] = {
                'implementation_progress': self._analyze_pdet_implementation(data['pdet_data']),
                'territorial_closure': self._assess_territorial_closure(data['pdet_data']),
                'pillar_advancement': self._analyze_pillar_advancement(data['pdet_data']),
                'community_participation': self._assess_community_participation(data['pdet_data'])
            }

        return data

    async def get_municipal_performance(
        self,
        municipality_code: str,
        include_comparison: bool = True
    ) -> Dict:
        """
        Get comprehensive municipal performance data

        Args:
            municipality_code: Municipality DANE code
            include_comparison: Include peer comparison

        Returns:
            Municipal performance dashboard
        """
        # Fetch multiple data sources for the municipality
        endpoints = [
            {'endpoint': self.endpoints['indicators'], 'params': {'entidades': municipality_code}},
            {'endpoint': self.endpoints['territorial'], 'params': {'municipio': municipality_code}},
            {'endpoint': self.endpoints['projects'], 'params': {'municipio': municipality_code}},
            {'endpoint': self.endpoints['peace'], 'params': {'municipio': municipality_code}}
        ]

        results = await self.batch_fetch(endpoints, max_concurrent=4)

        # Combine into comprehensive analysis
        dashboard = {
            'municipality_code': municipality_code,
            'timestamp': datetime.utcnow().isoformat(),
            'indicators': results[0] if results else {},
            'territorial': results[1] if len(results) > 1 else {},
            'projects': results[2] if len(results) > 2 else {},
            'peace': results[3] if len(results) > 3 else {},
            'comprehensive_analysis': self._create_comprehensive_analysis(results)
        }

        if include_comparison:
            dashboard['peer_comparison'] = await self._get_peer_comparison(municipality_code)

        return dashboard

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform DNP API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        transformed = {
            'source': 'DNP',
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Handle different response structures
        if 'indicadores' in response:
            transformed['indicators'] = response['indicadores']
        elif 'datos_territoriales' in response:
            transformed['territorial_data'] = response['datos_territoriales']
        elif 'proyectos' in response:
            transformed['projects'] = response['proyectos']
        elif 'plan_desarrollo' in response:
            transformed['plan_data'] = response['plan_desarrollo']
        else:
            transformed.update(response)

        # Add metadata
        if 'metadatos' in response:
            transformed['metadata'] = response['metadatos']

        # Add data quality assessment
        transformed['quality_assessment'] = self._assess_data_completeness(transformed)

        return transformed

    def _calculate_development_ranking(self, indicators: List[Dict]) -> List[Dict]:
        """Calculate development ranking for territories"""
        if not indicators:
            return []

        # Create composite development index
        scored_entities = []
        for indicator in indicators:
            entity = indicator.get('entidad', 'unknown')
            score = self._calculate_composite_score(indicator)
            scored_entities.append({
                'entity': entity,
                'score': score,
                'indicators': indicator
            })

        # Sort by score
        return sorted(scored_entities, key=lambda x: x['score'], reverse=True)

    def _identify_development_gaps(self, indicators: List[Dict]) -> List[Dict]:
        """Identify critical development gaps"""
        gaps = []

        for indicator in indicators:
            entity = indicator.get('entidad', 'unknown')

            # Check each indicator against thresholds
            if indicator.get('pobreza_monetaria', 0) > self.alert_thresholds['poverty_rate']:
                gaps.append({
                    'entity': entity,
                    'gap_type': 'poverty',
                    'value': indicator['pobreza_monetaria'],
                    'severity': 'high' if indicator['pobreza_monetaria'] > 40 else 'medium'
                })

            if indicator.get('nbi', 0) > self.alert_thresholds['nbi_rate']:
                gaps.append({
                    'entity': entity,
                    'gap_type': 'basic_needs',
                    'value': indicator['nbi'],
                    'severity': 'high' if indicator['nbi'] > 35 else 'medium'
                })

        return gaps

    def _analyze_indicator_trends(self, indicators: List[Dict]) -> Dict:
        """Analyze trends in development indicators"""
        # Simplified trend analysis
        trends = {
            'improving': 0,
            'stable': 0,
            'deteriorating': 0
        }

        for indicator in indicators:
            # This would compare with historical data
            # For now, use dummy logic
            change = indicator.get('cambio_anual', 0)
            if change > 2:
                trends['improving'] += 1
            elif change < -2:
                trends['deteriorating'] += 1
            else:
                trends['stable'] += 1

        return trends

    def _check_development_alerts(self, indicators: List[Dict]) -> List[Dict]:
        """Check for development alert conditions"""
        alerts = []

        for indicator in indicators:
            entity = indicator.get('entidad', 'unknown')

            # Poverty alert
            poverty_rate = indicator.get('pobreza_monetaria', 0)
            if poverty_rate > self.alert_thresholds['poverty_rate']:
                alerts.append({
                    'entity': entity,
                    'type': 'poverty',
                    'severity': 'high' if poverty_rate > 40 else 'medium',
                    'message': f'High poverty rate: {poverty_rate:.1f}%',
                    'value': poverty_rate
                })

            # Education coverage alert
            education_coverage = indicator.get('cobertura_educacion', 100)
            if education_coverage < self.alert_thresholds['education_coverage']:
                alerts.append({
                    'entity': entity,
                    'type': 'education',
                    'severity': 'medium',
                    'message': f'Low education coverage: {education_coverage:.1f}%',
                    'value': education_coverage
                })

        return alerts

    def _calculate_composite_score(self, indicator: Dict) -> float:
        """Calculate composite development score"""
        score = 0.0
        weights = {
            'pobreza_monetaria': -0.3,  # Negative weight (higher poverty = lower score)
            'nbi': -0.2,
            'cobertura_educacion': 0.2,
            'cobertura_salud': 0.15,
            'pib_per_capita': 0.15
        }

        for key, weight in weights.items():
            value = indicator.get(key, 0)
            if key in ['pobreza_monetaria', 'nbi']:
                # Invert poverty and NBI (lower is better)
                normalized_value = max(0, 100 - value) / 100
            else:
                # Normalize to 0-1 scale
                normalized_value = min(value / 100, 1.0)

            score += weight * normalized_value

        return max(0, score * 100)  # Scale to 0-100

    def _analyze_demographic_profile(self, territorial_data: Dict) -> Dict:
        """Analyze demographic profile"""
        return {
            'population': territorial_data.get('poblacion_total', 0),
            'density': territorial_data.get('densidad_poblacional', 0),
            'urban_rural_ratio': territorial_data.get('ratio_urbano_rural', 0),
            'age_structure': territorial_data.get('estructura_edad', {}),
            'growth_rate': territorial_data.get('tasa_crecimiento', 0)
        }

    def _analyze_economic_profile(self, territorial_data: Dict) -> Dict:
        """Analyze economic profile"""
        return {
            'gdp_per_capita': territorial_data.get('pib_per_capita', 0),
            'main_sectors': territorial_data.get('sectores_principales', []),
            'employment_rate': territorial_data.get('tasa_empleo', 0),
            'economic_diversification': territorial_data.get('diversificacion_economica', 0)
        }

    def _calculate_territorial_development_index(self, territorial_data: Dict) -> float:
        """Calculate territorial development index"""
        # Simplified calculation
        factors = [
            territorial_data.get('indice_desarrollo_humano', 0) * 0.4,
            territorial_data.get('indice_competitividad', 0) * 0.3,
            territorial_data.get('indice_institucional', 0) * 0.3
        ]

        return sum(factors)

    def _create_comprehensive_analysis(self, results: List[Dict]) -> Dict:
        """Create comprehensive analysis from multiple data sources"""
        analysis = {
            'development_level': 'medium',
            'key_strengths': [],
            'key_challenges': [],
            'priority_interventions': [],
            'overall_score': 0
        }

        # This would implement complex analysis logic
        # For now, return basic structure

        return analysis

    async def _get_peer_comparison(self, municipality_code: str) -> Dict:
        """Get peer comparison for municipality"""
        # This would implement peer municipality identification and comparison
        return {
            'peer_municipalities': [],
            'relative_performance': {},
            'best_practices': []
        }

    def _assess_data_completeness(self, data: Dict) -> Dict:
        """Assess completeness of DNP data"""
        completeness_score = 100  # Start with full score

        # Check for missing key fields
        required_fields = ['source', 'extracted_at']
        for field in required_fields:
            if field not in data:
                completeness_score -= 20

        return {
            'completeness_score': max(0, completeness_score),
            'data_quality': 'high' if completeness_score > 80 else 'medium' if completeness_score > 60 else 'low',
            'missing_fields': [f for f in required_fields if f not in data]
        }

    async def test_connection(self) -> Dict:
        """
        Test connection to DNP API

        Returns:
            Connection test results
        """
        try:
            # Test with a simple indicators request
            result = await self.get_development_indicators(geographic_level='national')

            if 'indicators' in result or 'error' not in result:
                return {
                    'status': 'success',
                    'message': 'Successfully connected to DNP API',
                    'data_available': bool(result.get('indicators')),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'DNP API responded with error',
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to DNP API: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }