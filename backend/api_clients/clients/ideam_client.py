"""
IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales) API Client
Access Colombian meteorological, hydrological, and environmental data
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class IDEAMClient(BaseAPIClient):
    """
    Client for IDEAM API - Colombian Institute of Hydrology, Meteorology and Environmental Studies
    Provides access to weather, climate, and environmental monitoring data
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize IDEAM client"""
        default_config = {
            'base_url': 'https://www.ideam.gov.co/api',
            'api_key': None,  # May require API key for detailed data
            'cache_ttl': 900,  # 15 minutes cache for weather data
            'rate_limit': 120,  # Moderate rate limit
            'timeout': 45
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # IDEAM API endpoints
        self.endpoints = {
            'stations': 'estaciones',  # Weather stations
            'observations': 'observaciones',  # Weather observations
            'forecasts': 'pronosticos',  # Weather forecasts
            'climate': 'climatologia',  # Climate data
            'hydrology': 'hidrologia',  # Water resources
            'air_quality': 'calidad-aire',  # Air quality
            'alerts': 'alertas',  # Weather alerts
            'statistics': 'estadisticas',  # Climate statistics
            'extremes': 'extremos',  # Extreme weather events
            'indices': 'indices'  # Climate indices
        }

        # Weather variables
        self.weather_variables = {
            'PTPM_CON': 'Precipitación',  # Precipitation
            'TMAX_CON': 'Temperatura Máxima',  # Max temperature
            'TMIN_CON': 'Temperatura Mínima',  # Min temperature
            'TMED_CON': 'Temperatura Media',  # Mean temperature
            'HR_CON': 'Humedad Relativa',  # Relative humidity
            'VV_CON': 'Velocidad del Viento',  # Wind speed
            'DV_CON': 'Dirección del Viento',  # Wind direction
            'PA_CON': 'Presión Atmosférica',  # Atmospheric pressure
            'ETP_CON': 'Evapotranspiración',  # Evapotranspiration
            'BSHG_CON': 'Brillo Solar'  # Solar brightness
        }

        # Colombian regions
        self.regions = {
            'amazonia': 'Amazonía',
            'andina': 'Región Andina',
            'caribe': 'Región Caribe',
            'orinoquia': 'Orinoquía',
            'pacifica': 'Región Pacífica',
            'insular': 'Región Insular'
        }

        # Alert thresholds
        self.alert_thresholds = {
            'extreme_precipitation': 100,  # mm/day
            'extreme_temperature': 38,  # °C
            'drought_days': 30,  # Consecutive days without rain
            'flood_risk_precipitation': 200,  # mm/24h
            'air_quality_unhealthy': 150  # AQI
        }

    async def get_weather_stations(
        self,
        region: Optional[str] = None,
        department: Optional[str] = None,
        active_only: bool = True
    ) -> Dict:
        """
        Get weather stations information

        Args:
            region: Filter by region
            department: Filter by department
            active_only: Only active stations

        Returns:
            Weather stations data
        """
        params = {}

        if region:
            params['region'] = region
        if department:
            params['departamento'] = department
        if active_only:
            params['activa'] = True

        data = await self.fetch_data(self.endpoints['stations'], params)

        # Add station analytics
        if 'results' in data:
            stations = data['results']
            data['analytics'] = {
                'total_stations': len(stations),
                'regional_distribution': self._count_by_region(stations),
                'station_types': self._count_station_types(stations),
                'coverage_analysis': self._analyze_geographic_coverage(stations)
            }

        return data

    async def get_current_weather(
        self,
        station_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        variables: Optional[List[str]] = None
    ) -> Dict:
        """
        Get current weather observations

        Args:
            station_id: Specific station ID
            latitude: Latitude for nearest station
            longitude: Longitude for nearest station
            variables: Weather variables to include

        Returns:
            Current weather data
        """
        params = {}

        if station_id:
            params['estacion'] = station_id
        elif latitude and longitude:
            params['lat'] = latitude
            params['lon'] = longitude

        if variables:
            params['variables'] = ','.join(variables)
        else:
            # Default essential variables
            params['variables'] = 'TMED_CON,PTPM_CON,HR_CON,VV_CON'

        data = await self.fetch_data(self.endpoints['observations'], params)

        # Add weather analysis
        if 'data' in data:
            data['analysis'] = self._analyze_current_weather(data['data'])
            data['comfort_index'] = self._calculate_comfort_index(data['data'])

        return data

    async def get_historical_weather(
        self,
        station_id: str,
        start_date: str,
        end_date: str,
        variables: Optional[List[str]] = None,
        aggregation: str = 'daily'
    ) -> Dict:
        """
        Get historical weather data

        Args:
            station_id: Station identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            variables: Weather variables
            aggregation: 'hourly', 'daily', 'monthly'

        Returns:
            Historical weather data with analysis
        """
        params = {
            'estacion': station_id,
            'fecha_inicio': start_date,
            'fecha_fin': end_date,
            'agregacion': aggregation
        }

        if variables:
            params['variables'] = ','.join(variables)

        data = await self.fetch_data(self.endpoints['observations'], params)

        # Add statistical analysis
        if 'data' in data:
            data['statistics'] = self._calculate_weather_statistics(data['data'])
            data['trends'] = self._analyze_weather_trends(data['data'])
            data['extremes'] = self._identify_extreme_events(data['data'])

        return data

    async def get_weather_forecast(
        self,
        location: str,
        days: int = 7,
        include_hourly: bool = False
    ) -> Dict:
        """
        Get weather forecast

        Args:
            location: City or region name
            days: Number of forecast days
            include_hourly: Include hourly forecasts

        Returns:
            Weather forecast data
        """
        params = {
            'ubicacion': location,
            'dias': min(days, 15),  # Limit to 15 days
            'por_horas': include_hourly
        }

        data = await self.fetch_data(self.endpoints['forecasts'], params)

        # Add forecast analysis
        if 'forecast' in data:
            data['forecast_analysis'] = {
                'summary': self._summarize_forecast(data['forecast']),
                'alerts': self._check_forecast_alerts(data['forecast']),
                'confidence': self._assess_forecast_confidence(data['forecast'])
            }

        return data

    async def get_climate_data(
        self,
        region: str,
        period: str = 'monthly',
        years: Optional[Tuple[int, int]] = None
    ) -> Dict:
        """
        Get climate data and normals

        Args:
            region: Region or department
            period: 'monthly', 'seasonal', 'annual'
            years: Year range tuple (start, end)

        Returns:
            Climate data with analysis
        """
        params = {
            'region': region,
            'periodo': period
        }

        if years:
            params['año_inicio'] = years[0]
            params['año_fin'] = years[1]

        data = await self.fetch_data(self.endpoints['climate'], params)

        # Add climate analysis
        if 'data' in data:
            data['climate_analysis'] = {
                'seasonal_patterns': self._analyze_seasonal_patterns(data['data']),
                'variability': self._calculate_climate_variability(data['data']),
                'anomalies': self._detect_climate_anomalies(data['data']),
                'long_term_trends': self._analyze_long_term_trends(data['data'])
            }

        return data

    async def get_hydrological_data(
        self,
        basin: str,
        data_type: str = 'flow',
        period: Optional[str] = None
    ) -> Dict:
        """
        Get hydrological data

        Args:
            basin: River basin name
            data_type: 'flow', 'level', 'quality'
            period: Time period

        Returns:
            Hydrological data
        """
        params = {
            'cuenca': basin,
            'tipo': data_type
        }

        if period:
            params['periodo'] = period

        data = await self.fetch_data(self.endpoints['hydrology'], params)

        # Add hydrological analysis
        if 'data' in data:
            data['hydro_analysis'] = {
                'flow_regime': self._analyze_flow_regime(data['data']),
                'water_balance': self._calculate_water_balance(data['data']),
                'drought_risk': self._assess_drought_risk(data['data']),
                'flood_risk': self._assess_flood_risk(data['data'])
            }

        return data

    async def get_air_quality(
        self,
        city: str,
        pollutants: Optional[List[str]] = None
    ) -> Dict:
        """
        Get air quality data

        Args:
            city: City name
            pollutants: List of pollutants to include

        Returns:
            Air quality data with health assessment
        """
        params = {
            'ciudad': city
        }

        if pollutants:
            params['contaminantes'] = ','.join(pollutants)

        data = await self.fetch_data(self.endpoints['air_quality'], params)

        # Add air quality analysis
        if 'data' in data:
            data['aqi_analysis'] = {
                'overall_aqi': self._calculate_aqi(data['data']),
                'health_recommendations': self._get_health_recommendations(data['data']),
                'pollution_sources': self._identify_pollution_sources(data['data']),
                'trends': self._analyze_pollution_trends(data['data'])
            }

        return data

    async def get_weather_alerts(
        self,
        region: Optional[str] = None,
        alert_type: Optional[str] = None,
        active_only: bool = True
    ) -> Dict:
        """
        Get weather alerts and warnings

        Args:
            region: Filter by region
            alert_type: Type of alert
            active_only: Only active alerts

        Returns:
            Weather alerts with risk assessment
        """
        params = {}

        if region:
            params['region'] = region
        if alert_type:
            params['tipo'] = alert_type
        if active_only:
            params['activa'] = True

        data = await self.fetch_data(self.endpoints['alerts'], params)

        # Add alert analysis
        if 'alerts' in data:
            data['alert_analysis'] = {
                'risk_summary': self._assess_overall_risk(data['alerts']),
                'affected_areas': self._map_affected_areas(data['alerts']),
                'recommendations': self._generate_recommendations(data['alerts'])
            }

        return data

    async def get_climate_indices(
        self,
        index_type: str = 'soi',  # Southern Oscillation Index
        period: str = 'monthly'
    ) -> Dict:
        """
        Get climate indices (El Niño, La Niña, etc.)

        Args:
            index_type: 'soi', 'oni', 'iod' (Indian Ocean Dipole)
            period: 'monthly', 'seasonal'

        Returns:
            Climate indices data
        """
        params = {
            'indice': index_type,
            'periodo': period
        }

        data = await self.fetch_data(self.endpoints['indices'], params)

        # Add ENSO analysis
        if 'data' in data:
            data['enso_analysis'] = {
                'current_phase': self._determine_enso_phase(data['data']),
                'strength': self._assess_enso_strength(data['data']),
                'impacts': self._predict_enso_impacts(data['data']),
                'forecast': self._forecast_enso_evolution(data['data'])
            }

        return data

    async def get_extreme_weather_events(
        self,
        event_type: str,
        start_date: str,
        end_date: str,
        region: Optional[str] = None
    ) -> Dict:
        """
        Get extreme weather events

        Args:
            event_type: 'drought', 'flood', 'hurricane', 'heatwave'
            start_date: Start date
            end_date: End date
            region: Filter by region

        Returns:
            Extreme weather events data
        """
        params = {
            'tipo_evento': event_type,
            'fecha_inicio': start_date,
            'fecha_fin': end_date
        }

        if region:
            params['region'] = region

        data = await self.fetch_data(self.endpoints['extremes'], params)

        # Add event analysis
        if 'events' in data:
            data['event_analysis'] = {
                'frequency': self._analyze_event_frequency(data['events']),
                'intensity': self._analyze_event_intensity(data['events']),
                'impacts': self._assess_event_impacts(data['events']),
                'return_periods': self._calculate_return_periods(data['events'])
            }

        return data

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform IDEAM API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        transformed = {
            'source': 'IDEAM',
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Handle different response structures
        if 'datos_meteorologicos' in response:
            transformed['data'] = response['datos_meteorologicos']
        elif 'estaciones' in response:
            transformed['results'] = response['estaciones']
        elif 'pronostico' in response:
            transformed['forecast'] = response['pronostico']
        elif 'alertas' in response:
            transformed['alerts'] = response['alertas']
        else:
            transformed.update(response)

        # Add data quality assessment
        if 'data' in transformed:
            transformed['quality_assessment'] = self._assess_data_quality(transformed['data'])

        # Convert units if needed
        if 'data' in transformed:
            transformed['data'] = self._standardize_units(transformed['data'])

        return transformed

    def _analyze_current_weather(self, weather_data: Dict) -> Dict:
        """Analyze current weather conditions"""
        analysis = {
            'conditions': 'normal',
            'warnings': []
        }

        # Temperature analysis
        temp = weather_data.get('TMED_CON')
        if temp:
            if temp > 35:
                analysis['conditions'] = 'extreme_heat'
                analysis['warnings'].append('Extreme heat warning')
            elif temp < 5:
                analysis['conditions'] = 'extreme_cold'
                analysis['warnings'].append('Cold weather warning')

        # Precipitation analysis
        precipitation = weather_data.get('PTPM_CON', 0)
        if precipitation > self.alert_thresholds['extreme_precipitation']:
            analysis['warnings'].append('Heavy precipitation alert')

        # Wind analysis
        wind_speed = weather_data.get('VV_CON', 0)
        if wind_speed > 15:  # m/s
            analysis['warnings'].append('Strong wind advisory')

        return analysis

    def _calculate_comfort_index(self, weather_data: Dict) -> Dict:
        """Calculate weather comfort index"""
        temp = weather_data.get('TMED_CON')
        humidity = weather_data.get('HR_CON')

        if not temp or not humidity:
            return {'index': None, 'description': 'Insufficient data'}

        # Simplified heat index calculation
        if temp >= 27:
            heat_index = -42.379 + 2.04901523*temp + 10.14333127*humidity
            heat_index += -0.22475541*temp*humidity - 6.83783e-3*temp*temp
            heat_index += -5.481717e-2*humidity*humidity + 1.22874e-3*temp*temp*humidity
            heat_index += 8.5282e-4*temp*humidity*humidity - 1.99e-6*temp*temp*humidity*humidity

            if heat_index > 40:
                comfort = 'dangerous'
            elif heat_index > 32:
                comfort = 'uncomfortable'
            else:
                comfort = 'moderate'
        else:
            # Use apparent temperature for cooler conditions
            comfort = 'comfortable' if 18 <= temp <= 24 else 'moderate'

        return {
            'index': temp,
            'description': comfort,
            'temperature': temp,
            'humidity': humidity
        }

    def _calculate_weather_statistics(self, data: List[Dict]) -> Dict:
        """Calculate statistical measures for weather data"""
        if not data:
            return {}

        stats = {}

        # Process each variable
        for variable in self.weather_variables.keys():
            values = [d.get(variable) for d in data if d.get(variable) is not None]

            if values:
                stats[variable] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }

        return stats

    def _analyze_weather_trends(self, data: List[Dict]) -> Dict:
        """Analyze weather trends over time"""
        if len(data) < 2:
            return {}

        # Simplified trend analysis
        trends = {}

        for variable in self.weather_variables.keys():
            values = [d.get(variable) for d in data if d.get(variable) is not None]

            if len(values) >= 3:
                # Simple linear trend (positive/negative/stable)
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]

                if first_half and second_half:
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    change = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0

                    if abs(change) < 5:
                        trend = 'stable'
                    elif change > 0:
                        trend = 'increasing'
                    else:
                        trend = 'decreasing'

                    trends[variable] = {
                        'trend': trend,
                        'change_percent': change
                    }

        return trends

    def _identify_extreme_events(self, data: List[Dict]) -> List[Dict]:
        """Identify extreme weather events in the data"""
        extremes = []

        for i, record in enumerate(data):
            date = record.get('fecha', f'Day {i+1}')

            # Extreme precipitation
            precip = record.get('PTPM_CON', 0)
            if precip > self.alert_thresholds['extreme_precipitation']:
                extremes.append({
                    'date': date,
                    'type': 'extreme_precipitation',
                    'value': precip,
                    'description': f'Extreme precipitation: {precip} mm'
                })

            # Extreme temperature
            temp_max = record.get('TMAX_CON')
            if temp_max and temp_max > self.alert_thresholds['extreme_temperature']:
                extremes.append({
                    'date': date,
                    'type': 'extreme_heat',
                    'value': temp_max,
                    'description': f'Extreme heat: {temp_max}°C'
                })

        return extremes

    def _count_by_region(self, stations: List[Dict]) -> Dict:
        """Count stations by region"""
        count = {}
        for station in stations:
            region = station.get('region', 'unknown')
            count[region] = count.get(region, 0) + 1
        return count

    def _count_station_types(self, stations: List[Dict]) -> Dict:
        """Count stations by type"""
        count = {}
        for station in stations:
            station_type = station.get('tipo', 'unknown')
            count[station_type] = count.get(station_type, 0) + 1
        return count

    def _analyze_geographic_coverage(self, stations: List[Dict]) -> Dict:
        """Analyze geographic coverage of stations"""
        if not stations:
            return {}

        latitudes = [s.get('latitud') for s in stations if s.get('latitud')]
        longitudes = [s.get('longitud') for s in stations if s.get('longitud')]

        if not latitudes or not longitudes:
            return {'coverage': 'insufficient_data'}

        return {
            'lat_range': {'min': min(latitudes), 'max': max(latitudes)},
            'lon_range': {'min': min(longitudes), 'max': max(longitudes)},
            'coverage': 'national' if (max(latitudes) - min(latitudes)) > 10 else 'regional'
        }

    def _standardize_units(self, data: Any) -> Any:
        """Standardize measurement units"""
        # This would implement unit conversions
        # For now, return data as-is
        return data

    def _assess_data_quality(self, data: Any) -> Dict:
        """Assess quality of weather data"""
        if not data:
            return {'quality': 'no_data', 'completeness': 0}

        if isinstance(data, list):
            total_fields = len(data) * len(self.weather_variables)
            missing_fields = 0

            for record in data:
                for variable in self.weather_variables.keys():
                    if variable not in record or record[variable] is None:
                        missing_fields += 1

            completeness = ((total_fields - missing_fields) / total_fields) * 100 if total_fields > 0 else 0

            return {
                'quality': 'high' if completeness > 90 else 'medium' if completeness > 70 else 'low',
                'completeness': completeness,
                'total_records': len(data)
            }

        return {'quality': 'unknown', 'completeness': 0}

    async def test_connection(self) -> Dict:
        """
        Test connection to IDEAM API

        Returns:
            Connection test results
        """
        try:
            # Test with a simple stations request
            result = await self.get_weather_stations(active_only=True)

            if 'results' in result or 'error' not in result:
                return {
                    'status': 'success',
                    'message': 'Successfully connected to IDEAM API',
                    'station_count': len(result.get('results', [])),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'IDEAM API responded with error',
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to IDEAM API: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }