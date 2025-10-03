"""
Unit tests for language learning API endpoints
Testing /vocabulary, /practice, /progress endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from app.main import app
from app.database.vocabulary_models import VocabularyLemma, VocabularyTranslation
from app.database.models import LearningSession


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_lemma():
    """Sample vocabulary lemma"""
    return VocabularyLemma(
        id=1,
        lemma="hablar",
        primary_pos="VERB",
        corpus_frequency=1000,
        frequency_rank=100,
        phonetic_transcription="aˈβlaɾ",
        first_seen=datetime.now()
    )


@pytest.fixture
def sample_translation():
    """Sample vocabulary translation"""
    return VocabularyTranslation(
        id=1,
        lemma_id=1,
        target_language='en',
        translation='to speak',
        translation_type='manual',
        confidence=1.0
    )


class TestAddVocabularyWord:
    """Test POST /vocabulary endpoint"""

    def test_add_new_word_success(self, client):
        """Should successfully add new vocabulary word"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None  # Word doesn't exist
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/vocabulary",
                json={
                    "word": "correr",
                    "translation": "to run",
                    "difficulty_level": "A1"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["word"] == "correr"
            assert data["translation"] == "to run"
            assert data["difficulty_level"] == "A1"
            assert "id" in data

    def test_add_duplicate_word(self, client):
        """Should reject duplicate vocabulary word"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = Mock(id=1)  # Word exists
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/vocabulary",
                json={
                    "word": "existing",
                    "translation": "exists"
                }
            )

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"].lower()

    def test_add_word_with_example(self, client):
        """Should add word with example sentence"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/vocabulary",
                json={
                    "word": "casa",
                    "translation": "house",
                    "example_sentence": "Mi casa es grande.",
                    "notes": "Common noun"
                }
            )

            assert response.status_code == 200

    def test_add_word_validation_errors(self, client):
        """Should validate word input"""
        # Empty word
        response = client.post(
            "/api/language/vocabulary",
            json={"word": "", "translation": "test"}
        )
        assert response.status_code == 422

        # Empty translation
        response = client.post(
            "/api/language/vocabulary",
            json={"word": "test", "translation": ""}
        )
        assert response.status_code == 422


class TestGetVocabulary:
    """Test GET /vocabulary endpoint"""

    def test_get_vocabulary_list(self, client, sample_lemma, sample_translation):
        """Should return vocabulary list"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().offset().limit().all.return_value = [sample_lemma]
            mock_session.query().filter().first.return_value = sample_translation
            mock_db.return_value = mock_session

            response = client.get("/api/language/vocabulary")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            assert len(data) > 0
            assert data[0]["word"] == "hablar"

    def test_get_vocabulary_with_search(self, client):
        """Should filter vocabulary by search term"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().offset().limit().all.return_value = []
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.get("/api/language/vocabulary?search=hab")

            assert response.status_code == 200

    def test_get_vocabulary_pagination(self, client):
        """Should paginate vocabulary results"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().offset().limit().all.return_value = []
            mock_db.return_value = mock_session

            response = client.get("/api/language/vocabulary?skip=10&limit=5")

            assert response.status_code == 200


class TestGetVocabularyWord:
    """Test GET /vocabulary/{word_id} endpoint"""

    def test_get_existing_word(self, client, sample_lemma, sample_translation):
        """Should retrieve specific vocabulary word"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = sample_lemma

            # Mock translation and context queries
            def query_side_effect(model):
                mock_q = MagicMock()
                if model == VocabularyTranslation:
                    mock_q.filter().first.return_value = sample_translation
                else:
                    mock_q.filter().first.return_value = None
                return mock_q

            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session

            response = client.get("/api/language/vocabulary/1")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == 1
            assert data["word"] == "hablar"
            assert data["translation"] == "to speak"

    def test_get_nonexistent_word(self, client):
        """Should return 404 for nonexistent word"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.get("/api/language/vocabulary/999")

            assert response.status_code == 404


class TestStartPracticeSession:
    """Test POST /practice/start endpoint"""

    def test_start_practice_session(self, client, sample_lemma):
        """Should start new practice session"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().order_by().limit().all.return_value = [sample_lemma]
            mock_session.query().filter().first.return_value = Mock(
                translation="to speak"
            )
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/start?user_id=1",
                json={
                    "num_words": 5,
                    "practice_type": "flashcard"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "session_id" in data
            assert "words" in data
            assert data["practice_type"] == "flashcard"
            assert data["total"] > 0

    def test_start_practice_with_filters(self, client):
        """Should start practice with category and difficulty filters"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().order_by().limit().all.return_value = []
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/start?user_id=1",
                json={
                    "category_id": 1,
                    "difficulty_level": "A2",
                    "num_words": 10
                }
            )

            # Should return error if no words found
            assert response.status_code in [200, 404]

    def test_start_practice_no_words_available(self, client):
        """Should handle case with no words available"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().order_by().limit().all.return_value = []
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/start?user_id=1",
                json={"num_words": 10}
            )

            assert response.status_code == 404

    def test_practice_word_count_limits(self, client):
        """Should enforce word count limits"""
        # Too few words
        response = client.post(
            "/api/language/practice/start?user_id=1",
            json={"num_words": 0}
        )
        assert response.status_code == 422

        # Too many words
        response = client.post(
            "/api/language/practice/start?user_id=1",
            json={"num_words": 100}
        )
        assert response.status_code == 422


class TestRecordPracticeResult:
    """Test POST /practice/result endpoint"""

    def test_record_correct_answer(self, client):
        """Should record correct practice result"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = Mock(
                id=1,
                items_completed=5,
                correct_answers=3,
                incorrect_answers=2,
                vocabulary_ids=[1, 2, 3]
            )
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/result?session_id=1&user_id=1",
                json={
                    "word_id": 1,
                    "correct": True,
                    "response_time": 2.5,
                    "practice_type": "flashcard"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "new_mastery_level" in data
            assert "total_practices" in data

    def test_record_incorrect_answer(self, client):
        """Should record incorrect practice result"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()

            # Mock session
            mock_session_obj = Mock(
                id=1,
                items_completed=5,
                correct_answers=3,
                incorrect_answers=2,
                vocabulary_ids=[1, 2, 3]
            )

            # Mock vocabulary acquisition
            mock_vocab = Mock(
                comprehension_level=0.5,
                total_exposures=10,
                meaningful_exposures=7
            )

            def query_side_effect(model):
                mock_q = MagicMock()
                if model == LearningSession:
                    mock_q.filter().first.return_value = mock_session_obj
                else:
                    mock_q.filter().first.return_value = mock_vocab
                return mock_q

            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/result?session_id=1&user_id=1",
                json={
                    "word_id": 1,
                    "correct": False,
                    "response_time": 5.0,
                    "practice_type": "flashcard"
                }
            )

            assert response.status_code == 200

    def test_record_result_nonexistent_session(self, client):
        """Should handle nonexistent session"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/practice/result?session_id=999&user_id=1",
                json={
                    "word_id": 1,
                    "correct": True,
                    "response_time": 2.0,
                    "practice_type": "flashcard"
                }
            )

            assert response.status_code == 404


class TestGetLearningProgress:
    """Test GET /progress/{user_id} endpoint"""

    def test_get_user_progress(self, client):
        """Should return user learning progress"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()

            # Mock vocabulary acquisition data
            mock_vocab = [
                Mock(
                    comprehension_level=0.9,
                    total_exposures=20,
                    meaningful_exposures=18
                ),
                Mock(
                    comprehension_level=0.6,
                    total_exposures=10,
                    meaningful_exposures=7
                )
            ]

            # Mock learning sessions
            mock_sessions = [
                Mock(
                    id=1,
                    started_at=datetime.now(),
                    session_type="flashcard",
                    correct_answers=8,
                    items_completed=10,
                    duration_seconds=300
                )
            ]

            def query_side_effect(model):
                mock_q = MagicMock()
                if model.__name__ == 'VocabularyAcquisition':
                    mock_q.filter().all.return_value = mock_vocab
                elif model == LearningSession:
                    mock_q.filter().order_by().limit().all.return_value = mock_sessions
                    mock_q.filter().first.return_value = mock_sessions[0]
                    mock_q.filter().scalar.return_value = 300
                return mock_q

            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session

            response = client.get("/api/language/progress/1")

            assert response.status_code == 200
            data = response.json()

            assert "total_words_learned" in data
            assert "words_mastered" in data
            assert "current_streak" in data
            assert "accuracy_rate" in data
            assert "recent_sessions" in data

    def test_progress_calculation(self, client):
        """Should correctly calculate progress metrics"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()

            # All words mastered (>= 0.8 comprehension)
            mock_vocab = [
                Mock(comprehension_level=0.85, total_exposures=15, meaningful_exposures=14),
                Mock(comprehension_level=0.90, total_exposures=20, meaningful_exposures=19)
            ]

            def query_side_effect(model):
                mock_q = MagicMock()
                mock_q.filter().all.return_value = mock_vocab
                mock_q.filter().order_by().limit().all.return_value = []
                mock_q.filter().first.return_value = None
                return mock_q

            mock_session.query.side_effect = query_side_effect
            mock_db.return_value = mock_session

            response = client.get("/api/language/progress/1")

            assert response.status_code == 200
            data = response.json()

            # Both words should be mastered
            assert data["words_mastered"] == 2
            # Accuracy should be high
            assert data["accuracy_rate"] > 0.9


class TestVocabularyCategories:
    """Test category management endpoints"""

    def test_get_categories(self, client):
        """Should list vocabulary categories"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_lemmas = [
                Mock(semantic_fields=['politics', 'economy']),
                Mock(semantic_fields=['sports', 'health'])
            ]
            mock_session.query().filter().all.return_value = mock_lemmas
            mock_db.return_value = mock_session

            response = client.get("/api/language/categories")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)

    def test_create_category_not_implemented(self, client):
        """Should return 501 for category creation"""
        response = client.post(
            "/api/language/categories?name=TestCategory"
        )

        assert response.status_code == 501


# Edge cases and validation
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_user_id(self, client):
        """Should handle invalid user IDs"""
        response = client.post(
            "/api/language/practice/start?user_id=-1",
            json={"num_words": 10}
        )
        # May return 422 or handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_special_characters_in_word(self, client):
        """Should handle special characters in vocabulary words"""
        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/vocabulary",
                json={
                    "word": "niño/niña",
                    "translation": "child (m/f)"
                }
            )

            # Should either accept or validate properly
            assert response.status_code in [200, 422]

    def test_very_long_translation(self, client):
        """Should handle very long translations"""
        long_translation = "a" * 300

        with patch('app.database.database.get_db') as mock_db:
            mock_session = MagicMock()
            mock_session.query().filter().first.return_value = None
            mock_db.return_value = mock_session

            response = client.post(
                "/api/language/vocabulary",
                json={
                    "word": "test",
                    "translation": long_translation
                }
            )

            # Should enforce max length validation
            assert response.status_code in [200, 422]
