"""
Test suite for all Colombian government API clients

Tests functionality for DANE, Banco de la República, SECOP, Datos Abiertos,
and other government API integrations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import aiohttp
from aioresponses import aioresponses

from backend.api_clients.clients.dane_client import DANEClient
from backend.api_clients.clients.banrep_client import BancoRepublicaClient
from backend.api_clients.clients.secop_client import SECOPClient
from backend.api_clients.clients.datos_gov_client import DatosGovClient
from backend.api_clients.clients.dnp_client import DNPClient
from backend.api_clients.clients.ideam_client import IDEAMClient
from backend.api_clients.clients.minhacienda_client import MinHaciendaClient
from backend.api_clients.base.base_client import BaseAPIClient

# Test classes for each API client


class TestDANEClient:
    """Test DANE (Statistics Department) API client"""

    @pytest.fixture
    def dane_client(self, api_client_config):
        """Create DANE client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.dane.gov.co/api'
        }
        return DANEClient(config)

    @pytest.fixture
    def sample_inflation_data(self):
        """Sample inflation data response"""
        return {
            "resultado": [
                {
                    "fecha": "2024-01-01",
                    "variacion_anual": 5.8,
                    "variacion_mensual": 0.4,
                    "indice": 118.45
                },
                {
                    "fecha": "2024-02-01",
                    "variacion_anual": 5.6,
                    "variacion_mensual": 0.3,
                    "indice": 118.80
                }
            ],
            "metadatos": {
                "fuente": "DANE",
                "actualizacion": "2024-02-15"
            }
        }

    @pytest.mark.asyncio
    async def test_initialization(self, dane_client):
        """Test DANE client initialization"""
        assert dane_client.base_url == 'https://test.dane.gov.co/api'
        assert 'ipc' in dane_client.endpoints
        assert 'pib' in dane_client.endpoints
        assert 'empleo' in dane_client.endpoints

    @pytest.mark.asyncio
    async def test_get_inflation_data(self, dane_client, sample_inflation_data, mock_aiohttp):
        """Test fetching inflation data"""
        # Mock API response
        mock_aiohttp.get(
            'https://test.dane.gov.co/api/indices/ipc',
            payload=sample_inflation_data
        )

        result = await dane_client.get_inflation_data()

        assert result is not None
        assert 'source' in result
        assert result['source'] == 'DANE'
        assert 'data' in result

    @pytest.mark.asyncio
    async def test_get_inflation_data_with_dates(self, dane_client, sample_inflation_data, mock_aiohttp):
        """Test fetching inflation data with date parameters"""
        mock_aiohttp.get(
            'https://test.dane.gov.co/api/indices/ipc?fecha_inicio=2024-01-01&fecha_fin=2024-02-01',
            payload=sample_inflation_data
        )

        result = await dane_client.get_inflation_data(
            start_date="2024-01-01",
            end_date="2024-02-01"
        )

        assert result is not None
        assert 'analysis' in result

    @pytest.mark.asyncio
    async def test_get_gdp_data(self, dane_client, mock_aiohttp):
        """Test fetching GDP data"""
        sample_gdp_data = {
            "resultado": {
                "pib_total": 1234567.89,
                "crecimiento_trimestral": 1.2,
                "crecimiento_anual": 3.5,
                "sectores": {
                    "agricultura": 45000.0,
                    "industria": 234000.0,
                    "servicios": 567000.0
                }
            }
        }

        mock_aiohttp.get(
            'https://test.dane.gov.co/api/cuentas/pib',
            payload=sample_gdp_data
        )

        result = await dane_client.get_gdp_data()

        assert result is not None
        assert 'data' in result

    @pytest.mark.asyncio
    async def test_get_employment_statistics(self, dane_client, mock_aiohttp):
        """Test fetching employment statistics"""
        sample_employment_data = {
            "resultado": {
                "pea": 25000000,  # Población Económicamente Activa
                "ocupados": 22500000,
                "desocupados": 2500000,
                "tasa_desempleo": 10.0,
                "tasa_ocupacion": 90.0
            }
        }

        mock_aiohttp.get(
            'https://test.dane.gov.co/api/mercado-laboral/empleo',
            payload=sample_employment_data
        )

        result = await dane_client.get_employment_statistics()

        assert result is not None
        assert 'unemployment_rate' in result

    @pytest.mark.asyncio
    async def test_inflation_analysis(self, dane_client):
        """Test inflation data analysis"""
        sample_data = [
            {"variacion_anual": 5.8, "variacion_mensual": 0.4},
            {"variacion_anual": 5.6, "variacion_mensual": 0.3}
        ]

        analysis = dane_client._analyze_inflation(sample_data)

        assert 'current_rate' in analysis
        assert 'monthly_change' in analysis
        assert 'trend' in analysis
        assert analysis['trend'] == 'decreasing'

    @pytest.mark.asyncio
    async def test_economic_alerts(self, dane_client):
        """Test economic alert detection"""
        # Test high inflation alert
        high_inflation_data = [{
            'data': {'variacion_mensual': 1.5}  # Above threshold
        }]

        alerts = dane_client._check_economic_alerts(high_inflation_data)

        assert len(alerts) > 0
        assert alerts[0]['type'] == 'inflation'
        assert alerts[0]['severity'] == 'high'

    @pytest.mark.asyncio
    async def test_error_handling(self, dane_client, mock_aiohttp):
        """Test error handling for API failures"""
        mock_aiohttp.get(
            'https://test.dane.gov.co/api/indices/ipc',
            status=500
        )

        with pytest.raises(Exception):
            await dane_client.get_inflation_data()


class TestBancoRepublicaClient:
    """Test Banco de la República API client"""

    @pytest.fixture
    def banrep_client(self, api_client_config):
        """Create Banco República client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.banrep.gov.co/api'
        }
        return BancoRepublicaClient(config)

    @pytest.fixture
    def sample_exchange_rate_data(self):
        """Sample exchange rate data"""
        return {
            "data": [
                {
                    "fecha": "2024-01-15",
                    "moneda": "USD",
                    "tasa": 4250.50,
                    "tipo": "TRM"
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_exchange_rates(self, banrep_client, sample_exchange_rate_data, mock_aiohttp):
        """Test fetching exchange rates"""
        mock_aiohttp.get(
            'https://test.banrep.gov.co/api/tasas-cambio',
            payload=sample_exchange_rate_data
        )

        result = await banrep_client.get_exchange_rates()

        assert result is not None
        assert 'data' in result

    @pytest.mark.asyncio
    async def test_get_interest_rates(self, banrep_client, mock_aiohttp):
        """Test fetching interest rates"""
        sample_rates = {
            "data": [
                {
                    "fecha": "2024-01-15",
                    "tasa_politica": 13.25,
                    "dtf": 12.85
                }
            ]
        }

        mock_aiohttp.get(
            'https://test.banrep.gov.co/api/tasas-interes',
            payload=sample_rates
        )

        result = await banrep_client.get_interest_rates()

        assert result is not None


class TestSECOPClient:
    """Test SECOP (Public Procurement) API client"""

    @pytest.fixture
    def secop_client(self, api_client_config):
        """Create SECOP client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.colombiacompra.gov.co/api'
        }
        return SECOPClient(config)

    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data"""
        return {
            "data": [
                {
                    "id_contrato": "COL-2024-001",
                    "nombre": "Infraestructura Educativa",
                    "valor": 5000000000,
                    "entidad": "Ministerio de Educación",
                    "estado": "Adjudicado",
                    "fecha_adjudicacion": "2024-01-15"
                }
            ],
            "pagination": {
                "page": 1,
                "total": 100,
                "per_page": 10
            }
        }

    @pytest.mark.asyncio
    async def test_get_contracts(self, secop_client, sample_contract_data, mock_aiohttp):
        """Test fetching contract data"""
        mock_aiohttp.get(
            'https://test.colombiacompra.gov.co/api/contratos',
            payload=sample_contract_data
        )

        result = await secop_client.get_contracts()

        assert result is not None
        assert 'data' in result
        assert len(result['data']) > 0

    @pytest.mark.asyncio
    async def test_get_contracts_by_entity(self, secop_client, sample_contract_data, mock_aiohttp):
        """Test fetching contracts by entity"""
        mock_aiohttp.get(
            'https://test.colombiacompra.gov.co/api/contratos?entidad=Ministerio%20de%20Educaci%C3%B3n',
            payload=sample_contract_data
        )

        result = await secop_client.get_contracts(entity="Ministerio de Educación")

        assert result is not None


class TestDatosGovClient:
    """Test Datos Abiertos (Open Data) API client"""

    @pytest.fixture
    def datos_client(self, api_client_config):
        """Create Datos Gov client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.datos.gov.co/api'
        }
        return DatosGovClient(config)

    @pytest.fixture
    def sample_dataset_data(self):
        """Sample dataset data"""
        return {
            "result": {
                "records": [
                    {
                        "id": "dataset-001",
                        "title": "Contratos Públicos 2024",
                        "description": "Base de datos de contratos públicos",
                        "organization": "SECOP",
                        "resources": [
                            {
                                "url": "https://datos.gov.co/dataset.csv",
                                "format": "CSV"
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_get_datasets(self, datos_client, sample_dataset_data, mock_aiohttp):
        """Test fetching datasets"""
        mock_aiohttp.get(
            'https://test.datos.gov.co/api/3/action/package_list',
            payload=sample_dataset_data
        )

        result = await datos_client.get_datasets()

        assert result is not None

    @pytest.mark.asyncio
    async def test_search_datasets(self, datos_client, sample_dataset_data, mock_aiohttp):
        """Test searching datasets"""
        mock_aiohttp.get(
            'https://test.datos.gov.co/api/3/action/package_search?q=contratos',
            payload=sample_dataset_data
        )

        result = await datos_client.search_datasets("contratos")

        assert result is not None


class TestDNPClient:
    """Test DNP (National Planning) API client"""

    @pytest.fixture
    def dnp_client(self, api_client_config):
        """Create DNP client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.dnp.gov.co/api'
        }
        return DNPClient(config)

    @pytest.mark.asyncio
    async def test_get_development_plans(self, dnp_client, mock_aiohttp):
        """Test fetching development plans"""
        sample_plans = {
            "data": [
                {
                    "id": "PND-2022-2026",
                    "nombre": "Plan Nacional de Desarrollo 2022-2026",
                    "estado": "Vigente"
                }
            ]
        }

        mock_aiohttp.get(
            'https://test.dnp.gov.co/api/planes-desarrollo',
            payload=sample_plans
        )

        result = await dnp_client.get_development_plans()

        assert result is not None


class TestIDEAMClient:
    """Test IDEAM (Weather/Climate) API client"""

    @pytest.fixture
    def ideam_client(self, api_client_config):
        """Create IDEAM client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.ideam.gov.co/api'
        }
        return IDEAMClient(config)

    @pytest.mark.asyncio
    async def test_get_weather_data(self, ideam_client, mock_aiohttp):
        """Test fetching weather data"""
        sample_weather = {
            "data": [
                {
                    "estacion": "BOGOTA",
                    "temperatura": 18.5,
                    "humedad": 65.0,
                    "precipitacion": 2.3,
                    "fecha": "2024-01-15T10:00:00Z"
                }
            ]
        }

        mock_aiohttp.get(
            'https://test.ideam.gov.co/api/meteorologia',
            payload=sample_weather
        )

        result = await ideam_client.get_weather_data()

        assert result is not None


class TestMinHaciendaClient:
    """Test MinHacienda (Finance Ministry) API client"""

    @pytest.fixture
    def minhacienda_client(self, api_client_config):
        """Create MinHacienda client instance"""
        config = {
            **api_client_config,
            'base_url': 'https://test.minhacienda.gov.co/api'
        }
        return MinHaciendaClient(config)

    @pytest.mark.asyncio
    async def test_get_budget_data(self, minhacienda_client, mock_aiohttp):
        """Test fetching budget data"""
        sample_budget = {
            "data": {
                "presupuesto_total": 350000000000000,  # COP
                "ejecutado": 280000000000000,
                "porcentaje_ejecucion": 80.0,
                "sectores": {
                    "educacion": 85000000000000,
                    "salud": 75000000000000,
                    "infraestructura": 60000000000000
                }
            }
        }

        mock_aiohttp.get(
            'https://test.minhacienda.gov.co/api/presupuesto',
            payload=sample_budget
        )

        result = await minhacienda_client.get_budget_data()

        assert result is not None


class TestBaseAPIClient:
    """Test base API client functionality"""

    @pytest.fixture
    def base_client(self, api_client_config):
        """Create base client instance"""
        return BaseAPIClient(api_client_config)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, base_client):
        """Test rate limiting functionality"""
        # Rate limiter should be initialized
        assert base_client.rate_limiter is not None

    @pytest.mark.asyncio
    async def test_caching(self, base_client, mock_aiohttp):
        """Test response caching"""
        sample_data = {"test": "data"}

        mock_aiohttp.get(
            'https://test-api.example.com/test',
            payload=sample_data
        )

        # First request
        result1 = await base_client.fetch_data('/test')

        # Second request should use cache
        result2 = await base_client.fetch_data('/test')

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, base_client, mock_aiohttp):
        """Test retry mechanism on failures"""
        # First two calls fail, third succeeds
        mock_aiohttp.get(
            'https://test-api.example.com/test',
            status=500
        )
        mock_aiohttp.get(
            'https://test-api.example.com/test',
            status=500
        )
        mock_aiohttp.get(
            'https://test-api.example.com/test',
            payload={"success": True}
        )

        result = await base_client.fetch_data('/test')
        assert result is not None

    @pytest.mark.asyncio
    async def test_batch_fetch(self, base_client, mock_aiohttp):
        """Test batch fetching multiple endpoints"""
        endpoints = [
            {'endpoint': '/test1', 'params': {}},
            {'endpoint': '/test2', 'params': {}},
            {'endpoint': '/test3', 'params': {}}
        ]

        # Mock responses
        mock_aiohttp.get('https://test-api.example.com/test1', payload={"data": 1})
        mock_aiohttp.get('https://test-api.example.com/test2', payload={"data": 2})
        mock_aiohttp.get('https://test-api.example.com/test3', payload={"data": 3})

        results = await base_client.batch_fetch(endpoints)

        assert len(results) == 3
        assert all('data' in result for result in results)

    @pytest.mark.asyncio
    async def test_transform_response(self, base_client):
        """Test response transformation"""
        raw_response = {
            "status": "ok",
            "payload": {"value": 123}
        }

        transformed = await base_client.transform_response(raw_response)

        assert 'extracted_at' in transformed
        assert transformed['data'] == raw_response

    @pytest.mark.asyncio
    async def test_connection_validation(self, base_client, mock_aiohttp):
        """Test API connection validation"""
        mock_aiohttp.get(
            'https://test-api.example.com/health',
            payload={"status": "healthy"}
        )

        is_valid = await base_client.test_connection()
        assert is_valid is True


# Integration tests across multiple clients
class TestAPIClientIntegration:
    """Integration tests across all API clients"""

    @pytest.mark.asyncio
    async def test_all_clients_initialization(self, api_client_config):
        """Test that all clients can be initialized"""
        clients = [
            DANEClient(api_client_config),
            BancoRepublicaClient(api_client_config),
            SECOPClient(api_client_config),
            DatosGovClient(api_client_config),
            DNPClient(api_client_config),
            IDEAMClient(api_client_config),
            MinHaciendaClient(api_client_config)
        ]

        for client in clients:
            assert client is not None
            assert hasattr(client, 'base_url')
            assert hasattr(client, 'fetch_data')

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, mock_aiohttp):
        """Test concurrent calls to multiple APIs"""
        # Setup mock responses for different APIs
        mock_aiohttp.get('https://test.dane.gov.co/api/indices/ipc', payload={"data": "dane"})
        mock_aiohttp.get('https://test.banrep.gov.co/api/tasas-cambio', payload={"data": "banrep"})
        mock_aiohttp.get('https://test.colombiacompra.gov.co/api/contratos', payload={"data": "secop"})

        # Create clients
        dane_client = DANEClient({'base_url': 'https://test.dane.gov.co/api'})
        banrep_client = BancoRepublicaClient({'base_url': 'https://test.banrep.gov.co/api'})
        secop_client = SECOPClient({'base_url': 'https://test.colombiacompra.gov.co/api'})

        # Make concurrent calls
        tasks = [
            dane_client.get_inflation_data(),
            banrep_client.get_exchange_rates(),
            secop_client.get_contracts()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All calls should succeed
        assert len(results) == 3
        assert all(isinstance(result, dict) for result in results if not isinstance(result, Exception))

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, api_client_config):
        """Test that all clients handle errors consistently"""
        clients = [
            DANEClient(api_client_config),
            BancoRepublicaClient(api_client_config),
            SECOPClient(api_client_config)
        ]

        for client in clients:
            # Test with invalid endpoint
            with pytest.raises(Exception):
                await client.fetch_data('/invalid-endpoint-12345')


# Performance and load tests
class TestAPIClientPerformance:
    """Performance tests for API clients"""

    @pytest.mark.asyncio
    async def test_rate_limit_compliance(self, api_client_config):
        """Test that clients respect rate limits"""
        client = DANEClient({
            **api_client_config,
            'rate_limit': 2  # Very low limit for testing
        })

        # Make multiple rapid requests
        start_time = datetime.now()

        tasks = []
        for _ in range(5):
            tasks.append(client.rate_limiter.acquire())

        await asyncio.gather(*tasks)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Should take at least 2 seconds due to rate limiting
        assert elapsed >= 1.5

    @pytest.mark.asyncio
    async def test_memory_usage(self, api_client_config, mock_aiohttp):
        """Test memory usage with large responses"""
        # Mock large response
        large_data = {"data": [{"item": i} for i in range(10000)]}
        mock_aiohttp.get(
            'https://test-api.example.com/large',
            payload=large_data
        )

        client = BaseAPIClient(api_client_config)
        result = await client.fetch_data('/large')

        assert result is not None
        assert len(result['data']) == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])