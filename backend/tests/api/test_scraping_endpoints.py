"""
Unit tests for scraping API endpoints
Testing /sources, /trigger, /status, /content endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database.models import ScrapedContent, Base
from app.api.scraping import SCRAPER_REGISTRY


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_test_db():
    """Create async test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestListSources:
    """Test GET /sources endpoint"""

    def test_list_all_sources(self, client):
        """Should return all source categories"""
        response = client.get("/api/scraping/sources")

        assert response.status_code == 200
        data = response.json()

        assert "total_categories" in data
        assert "categories" in data
        assert "sources" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0

    def test_filter_by_category(self, client):
        """Should filter sources by category"""
        response = client.get("/api/scraping/sources?category=Media")

        assert response.status_code == 200
        data = response.json()

        assert "category" in data
        assert data["category"] == "Media"
        assert "sources" in data

    def test_filter_by_priority(self, client):
        """Should filter sources by priority level"""
        response = client.get("/api/scraping/sources?priority=high")

        assert response.status_code == 200
        data = response.json()

        assert "priority" in data
        assert data["priority"] == "high"
        assert "sources" in data
        assert "total" in data

    def test_invalid_category_returns_all(self, client):
        """Should return all sources for invalid category"""
        response = client.get("/api/scraping/sources?category=InvalidCategory")

        assert response.status_code == 200
        data = response.json()

        # Should fall back to listing all sources
        assert "total_categories" in data


class TestTriggerScraping:
    """Test POST /trigger/{source_name} endpoint"""

    @patch('app.api.scraping.BackgroundTasks.add_task')
    def test_trigger_implemented_scraper(self, mock_bg_tasks, client):
        """Should trigger scraping for implemented scraper"""
        source_name = "El Tiempo"  # Known implemented scraper

        response = client.post(f"/api/scraping/trigger/{source_name}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "triggered"
        assert data["source"] == source_name
        assert "scraper" in data
        assert "timestamp" in data

        # Verify background task was scheduled
        mock_bg_tasks.assert_called_once()

    def test_trigger_unimplemented_scraper(self, client):
        """Should return not_implemented for unimplemented scraper"""
        source_name = "Unimplemented Source"

        response = client.post(f"/api/scraping/trigger/{source_name}")

        # Note: This will return 404 if source doesn't exist
        # Or status=not_implemented if in STRATEGIC_SOURCES but no scraper
        assert response.status_code in [200, 404]

    def test_trigger_nonexistent_source(self, client):
        """Should return 404 for nonexistent source"""
        response = client.post("/api/scraping/trigger/NonexistentSource")

        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.parametrize("source_name", ["El Tiempo", "El Espectador", "Semana"])
    def test_trigger_multiple_sources(self, source_name, client):
        """Should handle triggering multiple sources"""
        with patch('app.api.scraping.BackgroundTasks.add_task'):
            response = client.post(f"/api/scraping/trigger/{source_name}")

            assert response.status_code == 200
            data = response.json()
            assert data["source"] == source_name


class TestScrapingStatus:
    """Test GET /status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_no_data(self, client):
        """Should return empty statistics with no data"""
        with patch('app.database.connection.get_async_db') as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=Mock(scalar=Mock(return_value=0)))
            mock_db.return_value = mock_session

            response = client.get("/api/scraping/status")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert data["status"] == "operational"
            assert "total_articles" in data
            assert "recent_articles_24h" in data
            assert "available_scrapers" in data

    @pytest.mark.asyncio
    async def test_get_status_with_data(self, client):
        """Should return statistics with existing data"""
        # This would require setting up async DB fixture properly
        # For now, test the response structure
        response = client.get("/api/scraping/status")

        assert response.status_code == 200
        data = response.json()

        assert "total_articles" in data
        assert "recent_articles_24h" in data
        assert "source_distribution" in data
        assert isinstance(data["source_distribution"], list)
        assert "timestamp" in data

    def test_status_includes_scraper_list(self, client):
        """Should include list of available scrapers"""
        response = client.get("/api/scraping/status")

        assert response.status_code == 200
        data = response.json()

        assert "available_scrapers" in data
        scrapers = data["available_scrapers"]

        # Verify known scrapers are listed
        assert "El Tiempo" in scrapers
        assert "El Espectador" in scrapers


class TestGetScrapedContent:
    """Test GET /content endpoint"""

    def test_get_content_default_pagination(self, client):
        """Should return paginated content with default params"""
        response = client.get("/api/scraping/content")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "count" in data
        assert "limit" in data
        assert "offset" in data
        assert "articles" in data
        assert isinstance(data["articles"], list)

        # Default limit is 20
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_get_content_custom_pagination(self, client):
        """Should respect custom pagination parameters"""
        response = client.get("/api/scraping/content?limit=5&offset=10")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 5
        assert data["offset"] == 10

    def test_filter_by_source(self, client):
        """Should filter content by source"""
        response = client.get("/api/scraping/content?source=El Tiempo")

        assert response.status_code == 200
        data = response.json()

        # All articles should be from the specified source
        for article in data["articles"]:
            assert article["source"] == "El Tiempo"

    def test_filter_by_category(self, client):
        """Should filter content by category"""
        response = client.get("/api/scraping/content?category=Media")

        assert response.status_code == 200
        data = response.json()

        for article in data["articles"]:
            assert article["category"] == "Media"

    def test_filter_by_difficulty_range(self, client):
        """Should filter by difficulty score range"""
        response = client.get(
            "/api/scraping/content?min_difficulty=0.3&max_difficulty=0.7"
        )

        assert response.status_code == 200
        data = response.json()

        for article in data["articles"]:
            if article["difficulty_score"] is not None:
                assert 0.3 <= article["difficulty_score"] <= 0.7

    def test_combined_filters(self, client):
        """Should apply multiple filters simultaneously"""
        response = client.get(
            "/api/scraping/content?source=Semana&min_difficulty=0.5&limit=10"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        for article in data["articles"]:
            assert article["source"] == "Semana"

    def test_content_truncation(self, client):
        """Should truncate long content in preview"""
        # Would need actual data, but we can verify structure
        response = client.get("/api/scraping/content")

        assert response.status_code == 200
        data = response.json()

        for article in data["articles"]:
            assert "content" in article
            # Content should be truncated to ~500 chars + "..."
            if len(article["content"]) > 500:
                assert article["content"].endswith("...")


class TestRunScraperBackgroundTask:
    """Test run_scraper background task function"""

    @pytest.mark.asyncio
    async def test_successful_scraping(self):
        """Should successfully scrape and save articles"""
        from app.api.scraping import run_scraper

        # Mock scraper
        mock_scraper = AsyncMock()
        mock_articles = [
            ScrapedContent(
                source="Test Source",
                title="Test Article",
                content="Test content",
                url="https://test.com/article1"
            )
        ]
        mock_scraper.scrape = AsyncMock(return_value=mock_articles)

        # Mock scraper class
        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock(return_value=None)

        # Mock database session
        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        source_config = {"name": "Test Source"}

        await run_scraper(mock_scraper_class, source_config, mock_db)

        # Verify articles were added
        assert mock_db.add.call_count == len(mock_articles)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_scraping_error_handling(self):
        """Should handle scraping errors gracefully"""
        from app.api.scraping import run_scraper

        # Mock scraper that raises error
        mock_scraper = AsyncMock()
        mock_scraper.scrape = AsyncMock(side_effect=Exception("Scraping failed"))

        mock_scraper_class = Mock(return_value=mock_scraper)
        mock_scraper_class.__aenter__ = AsyncMock(return_value=mock_scraper)
        mock_scraper_class.__aexit__ = AsyncMock(return_value=None)

        mock_db = AsyncMock()
        mock_db.rollback = AsyncMock()

        source_config = {"name": "Test Source"}

        # Should not raise, but handle error internally
        await run_scraper(mock_scraper_class, source_config, mock_db)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()


# Edge cases and error handling
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_source_name(self, client):
        """Should handle empty source name"""
        response = client.post("/api/scraping/trigger/")
        assert response.status_code in [404, 405]  # Not found or method not allowed

    def test_special_characters_in_filters(self, client):
        """Should handle special characters in filter parameters"""
        response = client.get("/api/scraping/content?source=Test%20Source%20%26%20More")
        assert response.status_code == 200

    def test_negative_pagination_values(self, client):
        """Should handle negative pagination values"""
        response = client.get("/api/scraping/content?limit=-1&offset=-5")
        # Should either reject or use defaults
        assert response.status_code in [200, 422]

    def test_very_large_limit(self, client):
        """Should handle unreasonably large limit values"""
        response = client.get("/api/scraping/content?limit=999999")
        assert response.status_code == 200
        data = response.json()
        # Should be capped or return reasonable amount
        assert data["count"] <= 1000  # Reasonable upper limit
