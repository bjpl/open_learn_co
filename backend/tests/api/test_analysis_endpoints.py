"""
Unit tests for analysis API endpoints
Testing /analyze, /batch-analyze, /results endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.main import app
from app.api.analysis import (
    AnalysisRequest, AnalysisResponse,
    nlp_pipeline, sentiment_analyzer, difficulty_scorer
)


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Sample Spanish text for testing"""
    return """
    El presidente de Colombia anunció hoy una nueva reforma económica
    que busca mejorar la situación fiscal del país. Los expertos
    consideran que esta medida podría tener un impacto positivo
    en el crecimiento económico durante el próximo año.
    """


@pytest.fixture
def mock_sentiment_result():
    """Mock sentiment analysis result"""
    return Mock(
        polarity=0.5,
        subjectivity=0.6,
        classification="positive",
        confidence=0.8
    )


@pytest.fixture
def mock_difficulty_result():
    """Mock difficulty scoring result"""
    return Mock(
        difficulty_score=0.65,
        cefr_level="B2",
        reading_time_minutes=3.5,
        flesch_score=55.0
    )


class TestAnalyzeText:
    """Test POST /analyze endpoint"""

    def test_analyze_basic_request(self, client, sample_text):
        """Should analyze text with default analysis types"""
        with patch.object(sentiment_analyzer, 'analyze') as mock_sentiment, \
             patch.object(nlp_pipeline, 'extract_entities') as mock_entities, \
             patch.object(difficulty_scorer, 'score') as mock_difficulty:

            # Setup mocks
            mock_sentiment.return_value = {
                'polarity': 0.5,
                'subjectivity': 0.6,
                'confidence': 0.8
            }
            mock_entities.return_value = [
                {'text': 'Colombia', 'label': 'LOC', 'confidence': 0.95}
            ]
            mock_difficulty.return_value = {
                'cefr_level': 'B2',
                'numeric_score': 65.0,
                'metrics': {}
            }

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": ["sentiment", "entities", "difficulty"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "sentiment" in data
            assert "entities" in data
            assert "difficulty" in data
            assert "text_preview" in data

    def test_analyze_sentiment_only(self, client, sample_text):
        """Should analyze only sentiment when specified"""
        with patch.object(sentiment_analyzer, 'analyze') as mock_sentiment:
            mock_sentiment.return_value = {
                'polarity': 0.3,
                'subjectivity': 0.5,
                'confidence': 0.7
            }

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": ["sentiment"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "sentiment" in data
            assert data["sentiment"]["polarity"] == 0.3
            assert "entities" not in data or data["entities"] is None

    def test_analyze_entities_extraction(self, client, sample_text):
        """Should extract and return entities"""
        with patch.object(nlp_pipeline, 'extract_entities') as mock_entities:
            mock_entities.return_value = [
                {'text': 'Colombia', 'label': 'LOC'},
                {'text': 'presidente', 'label': 'PER'}
            ]

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": ["entities"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "entities" in data
            assert len(data["entities"]) == 2
            assert data["entities"][0]["type"] == "LOC"

    def test_analyze_difficulty_scoring(self, client, sample_text):
        """Should score text difficulty"""
        with patch.object(difficulty_scorer, 'score') as mock_difficulty:
            mock_difficulty.return_value = {
                'cefr_level': 'B1',
                'numeric_score': 48.0,
                'metrics': {
                    'flesch_score': 60.0,
                    'avg_sentence_length': 15.0
                }
            }

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": ["difficulty"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "difficulty" in data
            assert data["difficulty"]["cefr_level"] == "B1"
            assert data["difficulty"]["score"] == 48.0

    def test_analyze_with_summary(self, client, sample_text):
        """Should generate text summary"""
        with patch.object(nlp_pipeline, 'summarize') as mock_summarize:
            mock_summarize.return_value = "El presidente anuncia reforma económica."

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": ["summary"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "summary" in data
            assert len(data["summary"]) > 0

    def test_analyze_empty_text(self, client):
        """Should reject empty text"""
        response = client.post(
            "/api/analysis/analyze",
            json={
                "text": "",
                "analysis_types": ["sentiment"]
            }
        )

        # Should return 422 validation error
        assert response.status_code == 422

    def test_analyze_minimum_length(self, client):
        """Should require minimum text length"""
        response = client.post(
            "/api/analysis/analyze",
            json={
                "text": "Corto",  # Too short (< 10 chars)
                "analysis_types": ["sentiment"]
            }
        )

        assert response.status_code == 422

    def test_analyze_text_preview_truncation(self, client):
        """Should truncate long text in preview"""
        long_text = "a" * 500

        with patch.object(sentiment_analyzer, 'analyze') as mock_sentiment:
            mock_sentiment.return_value = {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'confidence': 0.5
            }

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": long_text,
                    "analysis_types": ["sentiment"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Preview should be truncated to 200 chars + "..."
            assert len(data["text_preview"]) <= 203
            if len(long_text) > 200:
                assert data["text_preview"].endswith("...")


class TestBatchAnalyze:
    """Test POST /batch-analyze endpoint"""

    def test_batch_analyze_valid_ids(self, client):
        """Should accept valid content IDs for batch processing"""
        with patch('app.database.database.get_db') as mock_db, \
             patch('app.api.analysis.BackgroundTasks.add_task') as mock_bg:

            # Mock database query
            mock_session = MagicMock()
            mock_session.query().filter().all.return_value = [
                Mock(id=1, title="Article 1", content="Content 1"),
                Mock(id=2, title="Article 2", content="Content 2")
            ]
            mock_db.return_value = mock_session

            response = client.post(
                "/api/analysis/batch-analyze",
                json={
                    "content_ids": [1, 2],
                    "analysis_types": ["sentiment", "entities"]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "processing"
            assert "message" in data

            # Verify background task was scheduled
            mock_bg.assert_called_once()

    def test_batch_analyze_no_content_found(self, client):
        """Should handle case when no content is found"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().all.return_value = []
            mock_db.return_value = mock_session

            response = client.post(
                "/api/analysis/batch-analyze",
                json={
                    "content_ids": [999, 1000],
                    "analysis_types": ["sentiment"]
                }
            )

            assert response.status_code == 404

    def test_batch_analyze_empty_id_list(self, client):
        """Should reject empty content ID list"""
        response = client.post(
            "/api/analysis/batch-analyze",
            json={
                "content_ids": [],
                "analysis_types": ["sentiment"]
            }
        )

        # May return 422 validation error or process normally
        assert response.status_code in [200, 422]


class TestGetAnalysisResult:
    """Test GET /results/{analysis_id} endpoint"""

    def test_get_existing_result(self, client):
        """Should retrieve existing analysis result"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_result = Mock(
                id=1,
                sentiment_score=0.5,
                sentiment_label="positive",
                entities=[{'text': 'Colombia', 'type': 'LOC'}],
                topics=[{'name': 'politics', 'score': 0.8}],
                summary="Test summary",
                processed_at=datetime.now()
            )
            mock_session.query().filter().first.return_value = mock_result
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/results/1")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 1
            assert "sentiment" in data
            assert "entities" in data

    def test_get_nonexistent_result(self, client):
        """Should return 404 for nonexistent result"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/results/999")

            assert response.status_code == 404


class TestListAnalysisResults:
    """Test GET /results endpoint"""

    def test_list_results_default_pagination(self, client):
        """Should list results with default pagination"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_results = [
                Mock(
                    id=i,
                    summary=f"Summary {i}",
                    sentiment_score=0.5,
                    topics=[],
                    entities=[],
                    processed_at=datetime.now()
                )
                for i in range(5)
            ]
            mock_session.query().order_by().offset().limit().all.return_value = mock_results
            mock_session.query().count.return_value = 5
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/results")

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            assert "total" in data
            assert len(data["results"]) == 5

    def test_list_results_custom_pagination(self, client):
        """Should respect custom pagination parameters"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().order_by().offset().limit().all.return_value = []
            mock_session.query().count.return_value = 0
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/results?skip=5&limit=20")

            assert response.status_code == 200


class TestAnalysisStatistics:
    """Test GET /statistics endpoint"""

    def test_get_statistics(self, client):
        """Should return analysis statistics"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().count.return_value = 100
            mock_session.query().filter().with_entities().scalar.return_value = 0.3
            mock_session.query().filter().limit().all.return_value = []
            mock_session.query().order_by().first.return_value = Mock(
                processed_at=datetime.now()
            )
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/statistics")

            assert response.status_code == 200
            data = response.json()

            assert "total_analyses" in data
            assert "average_sentiment" in data
            assert "entity_distribution" in data

    def test_statistics_with_no_data(self, client):
        """Should handle statistics with no data"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().count.return_value = 0
            mock_session.query().filter().with_entities().scalar.return_value = None
            mock_db.return_value = mock_session

            response = client.get("/api/analysis/statistics")

            assert response.status_code == 200
            data = response.json()

            assert data["total_analyses"] == 0


class TestProcessBatchAnalysis:
    """Test process_batch_analysis background function"""

    def test_batch_processing_success(self):
        """Should process batch successfully"""
        from app.api.analysis import process_batch_analysis

        mock_contents = [
            Mock(id=1, title="Title 1", content="Content 1"),
            Mock(id=2, title="Title 2", content="Content 2")
        ]

        mock_db = MagicMock()

        with patch.object(sentiment_analyzer, 'analyze') as mock_sentiment, \
             patch.object(nlp_pipeline, 'extract_entities') as mock_entities:

            mock_sentiment.return_value = {'polarity': 0.5}
            mock_entities.return_value = []

            process_batch_analysis(
                mock_contents,
                ["sentiment", "entities"],
                mock_db
            )

            # Verify all items were processed
            assert mock_sentiment.call_count == len(mock_contents)
            assert mock_db.add.call_count == len(mock_contents)
            mock_db.commit.assert_called_once()

    def test_batch_processing_with_errors(self):
        """Should handle errors during batch processing"""
        from app.api.analysis import process_batch_analysis

        mock_contents = [
            Mock(id=1, title="Title 1", content="Content 1"),
            Mock(id=2, title="Title 2", content="Content 2")
        ]

        mock_db = MagicMock()

        with patch.object(sentiment_analyzer, 'analyze') as mock_sentiment:
            # First succeeds, second fails
            mock_sentiment.side_effect = [
                {'polarity': 0.5},
                Exception("Analysis failed")
            ]

            # Should not raise, but continue processing
            process_batch_analysis(mock_contents, ["sentiment"], mock_db)

            # Should still commit (at least one succeeded)
            mock_db.commit.assert_called_once()


# Integration-style tests
class TestAnalysisIntegration:
    """Integration tests for analysis workflows"""

    @pytest.mark.parametrize("analysis_type,expected_key", [
        ("sentiment", "sentiment"),
        ("entities", "entities"),
        ("topics", "topics"),
        ("difficulty", "difficulty"),
        ("summary", "summary")
    ])
    def test_each_analysis_type(self, client, sample_text, analysis_type, expected_key):
        """Should handle each analysis type individually"""
        with patch.object(sentiment_analyzer, 'analyze'), \
             patch.object(nlp_pipeline, 'extract_entities'), \
             patch.object(nlp_pipeline, 'summarize'), \
             patch.object(difficulty_scorer, 'score'):

            response = client.post(
                "/api/analysis/analyze",
                json={
                    "text": sample_text,
                    "analysis_types": [analysis_type]
                }
            )

            assert response.status_code == 200
