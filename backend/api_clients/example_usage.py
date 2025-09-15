"""
Example usage of Colombian Government API Clients
Demonstrates how to use each client to fetch real data
"""

import asyncio
import logging
from datetime import datetime

from clients.datos_gov_client import DatosGovClient
from clients.secop_client import SECOPClient
from clients.ideam_client import IDEAMClient
from clients.dnp_client import DNPClient
from clients.minhacienda_client import MinHaciendaClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_datos_gov_client():
    """Test datos.gov.co CKAN API client"""
    logger.info("Testing DatosGovClient...")

    async with DatosGovClient() as client:
        # Test connection
        connection_test = await client.test_connection()
        logger.info(f"Connection test: {connection_test}")

        # Search for datasets
        search_results = await client.search_datasets(
            query="presupuesto",
            tags=["economia"],
            rows=5
        )
        logger.info(f"Found {len(search_results.get('result', {}).get('results', []))} datasets")

        # Get popular datasets
        popular = await client.get_popular_datasets(limit=3)
        logger.info(f"Popular datasets: {len(popular.get('result', {}).get('results', []))}")


async def test_secop_client():
    """Test SECOP procurement API client"""
    logger.info("Testing SECOPClient...")

    async with SECOPClient() as client:
        # Test connection
        connection_test = await client.test_connection()
        logger.info(f"Connection test: {connection_test}")

        # Search for high-value contracts
        contracts = await client.search_contracts(
            value_min=1_000_000_000,  # 1 billion COP
            page_size=5
        )
        logger.info(f"High-value contracts found: {len(contracts.get('results', []))}")

        # Monitor high-value contracts
        monitoring = await client.monitor_high_value_contracts(days_back=7)
        logger.info(f"Monitoring results: {monitoring.get('summary', {})}")


async def test_ideam_client():
    """Test IDEAM weather API client"""
    logger.info("Testing IDEAMClient...")

    async with IDEAMClient() as client:
        # Test connection
        connection_test = await client.test_connection()
        logger.info(f"Connection test: {connection_test}")

        # Get weather stations
        stations = await client.get_weather_stations(region="andina")
        logger.info(f"Weather stations: {len(stations.get('results', []))}")

        # Get weather forecast
        forecast = await client.get_weather_forecast(location="Bogotá", days=3)
        logger.info(f"Forecast available: {'forecast' in forecast}")

        # Get climate data
        climate = await client.get_climate_data(region="Cundinamarca")
        logger.info(f"Climate data: {'data' in climate}")


async def test_dnp_client():
    """Test DNP planning department API client"""
    logger.info("Testing DNPClient...")

    async with DNPClient() as client:
        # Test connection
        connection_test = await client.test_connection()
        logger.info(f"Connection test: {connection_test}")

        # Get development indicators
        indicators = await client.get_development_indicators(
            dimension="social",
            geographic_level="departmental"
        )
        logger.info(f"Development indicators: {'indicators' in indicators}")

        # Get territorial data
        territorial = await client.get_territorial_data(department="Cundinamarca")
        logger.info(f"Territorial data: {'territorial_data' in territorial}")

        # Get peace indicators
        peace = await client.get_peace_indicators(pdet_only=True)
        logger.info(f"Peace indicators: {'peace_indicators' in peace}")


async def test_minhacienda_client():
    """Test MinHacienda fiscal API client"""
    logger.info("Testing MinHaciendaClient...")

    async with MinHaciendaClient() as client:
        # Test connection
        connection_test = await client.test_connection()
        logger.info(f"Connection test: {connection_test}")

        # Get budget data
        budget = await client.get_budget_data(year=2024)
        logger.info(f"Budget data: {'budget_data' in budget}")

        # Get fiscal dashboard
        dashboard = await client.get_fiscal_dashboard()
        logger.info(f"Fiscal dashboard: {dashboard.get('year', 'N/A')}")

        # Get public debt data
        debt = await client.get_public_debt_data()
        logger.info(f"Debt data: {'debt_data' in debt}")


async def run_comprehensive_test():
    """Run comprehensive test of all API clients"""
    logger.info("Starting comprehensive API client tests...")

    try:
        # Test each client
        await test_datos_gov_client()
        await test_secop_client()
        await test_ideam_client()
        await test_dnp_client()
        await test_minhacienda_client()

        logger.info("All API client tests completed successfully!")

    except Exception as e:
        logger.error(f"Error during testing: {e}")


async def demonstrate_data_integration():
    """Demonstrate integration of data from multiple sources"""
    logger.info("Demonstrating data integration from multiple government sources...")

    # This would show how to combine data from multiple APIs
    # to create comprehensive reports or dashboards

    integration_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'sources_integrated': [
            'datos.gov.co',
            'SECOP',
            'IDEAM',
            'DNP',
            'MinHacienda'
        ],
        'integration_status': 'ready'
    }

    logger.info(f"Integration demonstration: {integration_results}")
    return integration_results


if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(run_comprehensive_test())

    # Demonstrate data integration
    asyncio.run(demonstrate_data_integration())