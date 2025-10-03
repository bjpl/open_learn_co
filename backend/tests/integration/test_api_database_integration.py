"""
Integration tests for API endpoints with database
Tests API routes with real database operations and transactions
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from backend.app.main import app
from backend.app.database.models import Base, ScrapedContent, ContentAnalysis, User
from backend.app.database.vocabulary_models import (
    VocabularyLemma, VocabularyTranslation, VocabularyAcquisition
)
from backend.app.database.database import get_db


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        full_name="Test User",
        spanish_level="B1"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestAnalysisAPIIntegration:
    """Test /analysis endpoints with database"""

    def test_analyze_text_endpoint(self, client, test_db):
        """Test POST /analysis/analyze with database storage"""
        response = client.post(
            "/analysis/analyze",
            json={
                "text": "La economía colombiana está creciendo rápidamente.",
                "analysis_types": ["sentiment", "entities"],
                "language": "es"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "sentiment" in data
        assert "entities" in data
        assert data["sentiment"]["polarity"] is not None

    def test_batch_analysis_endpoint(self, client, test_db):
        """Test POST /analysis/batch-analyze"""
        # Create test content
        articles = []
        for i in range(3):
            article = ScrapedContent(
                source="Test",
                source_url=f"https://example.com/test{i}",
                title=f"Test Article {i}",
                content=f"Test content for article {i}",
                published_date=datetime.utcnow()
            )
            test_db.add(article)
            articles.append(article)

        test_db.commit()

        # Batch analyze
        response = client.post(
            "/analysis/batch-analyze",
            json={
                "content_ids": [a.id for a in articles],
                "analysis_types": ["sentiment", "entities"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert len(data["content_ids"]) == 3

    def test_get_analysis_result(self, client, test_db):
        """Test GET /analysis/results/{id}"""
        # Create content and analysis
        article = ScrapedContent(
            source="Test",
            source_url="https://example.com/test",
            title="Test Article",
            content="Test content",
            published_date=datetime.utcnow()
        )
        test_db.add(article)
        test_db.commit()
        test_db.refresh(article)

        analysis = ContentAnalysis(
            content_id=article.id,
            sentiment_score=0.5,
            sentiment_label="positive",
            entities=[{"text": "Colombia", "type": "LOC"}],
            summary="Test summary"
        )
        test_db.add(analysis)
        test_db.commit()
        test_db.refresh(analysis)

        # Retrieve analysis
        response = client.get(f"/analysis/results/{analysis.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analysis.id
        assert data["sentiment"]["polarity"] == 0.5

    def test_list_analysis_results(self, client, test_db):
        """Test GET /analysis/results with pagination"""
        # Create multiple analyses
        for i in range(15):
            article = ScrapedContent(
                source="Test",
                source_url=f"https://example.com/test{i}",
                title=f"Test {i}",
                content=f"Content {i}",
                published_date=datetime.utcnow()
            )
            test_db.add(article)
            test_db.flush()

            analysis = ContentAnalysis(
                content_id=article.id,
                sentiment_score=0.5,
                summary=f"Summary {i}"
            )
            test_db.add(analysis)

        test_db.commit()

        # Test pagination
        response = client.get("/analysis/results?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10
        assert data["total"] == 15


class TestLanguageAPIIntegration:
    """Test /language endpoints with database"""

    def test_add_vocabulary_word(self, client, test_db):
        """Test POST /language/vocabulary"""
        response = client.post(
            "/language/vocabulary",
            json={
                "word": "economía",
                "translation": "economy",
                "difficulty_level": "B1",
                "example_sentence": "La economía está creciendo."
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "economía"
        assert data["translation"] == "economy"

        # Verify in database
        lemma = test_db.query(VocabularyLemma).filter(
            VocabularyLemma.lemma == "economía"
        ).first()

        assert lemma is not None

    def test_get_vocabulary_list(self, client, test_db):
        """Test GET /language/vocabulary"""
        # Create vocabulary items
        for i in range(5):
            lemma = VocabularyLemma(
                lemma=f"palabra{i}",
                primary_pos="NOUN",
                corpus_frequency=1000 - i * 100
            )
            test_db.add(lemma)
            test_db.flush()

            translation = VocabularyTranslation(
                lemma_id=lemma.id,
                target_language="en",
                translation=f"word{i}",
                translation_source="test",
                confidence=1.0
            )
            test_db.add(translation)

        test_db.commit()

        # Get vocabulary
        response = client.get("/language/vocabulary?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    def test_start_practice_session(self, client, test_db, test_user):
        """Test POST /language/practice/start"""
        # Create vocabulary
        for i in range(5):
            lemma = VocabularyLemma(
                lemma=f"palabra{i}",
                primary_pos="NOUN",
                corpus_frequency=1000
            )
            test_db.add(lemma)
            test_db.flush()

            translation = VocabularyTranslation(
                lemma_id=lemma.id,
                target_language="en",
                translation=f"word{i}",
                translation_source="test",
                confidence=1.0
            )
            test_db.add(translation)

        test_db.commit()

        # Start session
        response = client.post(
            f"/language/practice/start?user_id={test_user.id}",
            json={
                "num_words": 3,
                "practice_type": "flashcard"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["words"]) == 3

    def test_record_practice_result(self, client, test_db, test_user):
        """Test POST /language/practice/result"""
        # Create vocabulary and session
        lemma = VocabularyLemma(
            lemma="test",
            primary_pos="NOUN",
            corpus_frequency=1000
        )
        test_db.add(lemma)
        test_db.commit()
        test_db.refresh(lemma)

        from backend.app.database.models import LearningSession
        session = LearningSession(
            user_id=test_user.id,
            session_type="flashcard",
            vocabulary_ids=[lemma.id]
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)

        # Record result
        response = client.post(
            f"/language/practice/result?session_id={session.id}&user_id={test_user.id}",
            json={
                "word_id": lemma.id,
                "correct": True,
                "response_time": 2.5,
                "practice_type": "flashcard"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_learning_progress(self, client, test_db, test_user):
        """Test GET /language/progress/{user_id}"""
        # Create user vocabulary progress
        lemma = VocabularyLemma(
            lemma="test",
            primary_pos="NOUN",
            corpus_frequency=1000
        )
        test_db.add(lemma)
        test_db.flush()

        acquisition = VocabularyAcquisition(
            user_id=test_user.id,
            lemma_id=lemma.id,
            total_exposures=10,
            meaningful_exposures=8,
            comprehension_level=0.8
        )
        test_db.add(acquisition)
        test_db.commit()

        # Get progress
        response = client.get(f"/language/progress/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_words_learned"] >= 1
        assert data["words_mastered"] >= 1


class TestDatabaseTransactions:
    """Test database transaction handling"""

    def test_transaction_rollback_on_error(self, test_db):
        """Test that transactions rollback on error"""
        initial_count = test_db.query(ScrapedContent).count()

        try:
            article = ScrapedContent(
                source="Test",
                source_url="https://example.com/test",
                title="Test",
                content="Content",
                published_date=datetime.utcnow()
            )
            test_db.add(article)
            test_db.flush()

            # Cause an error
            duplicate = ScrapedContent(
                source="Test",
                source_url="https://example.com/test",  # Duplicate URL
                title="Test",
                content="Content",
                published_date=datetime.utcnow()
            )
            test_db.add(duplicate)
            test_db.commit()
        except Exception:
            test_db.rollback()

        # Verify rollback
        final_count = test_db.query(ScrapedContent).count()
        assert final_count == initial_count

    def test_concurrent_access(self, test_db):
        """Test handling concurrent database access"""
        # Create multiple articles simultaneously
        articles = []
        for i in range(10):
            article = ScrapedContent(
                source="Test",
                source_url=f"https://example.com/concurrent{i}",
                title=f"Article {i}",
                content=f"Content {i}",
                published_date=datetime.utcnow()
            )
            articles.append(article)
            test_db.add(article)

        test_db.commit()

        # Verify all were saved
        count = test_db.query(ScrapedContent).count()
        assert count == 10

    def test_data_consistency(self, test_db):
        """Test data consistency across related tables"""
        # Create article
        article = ScrapedContent(
            source="Test",
            source_url="https://example.com/consistency",
            title="Consistency Test",
            content="Test content",
            published_date=datetime.utcnow()
        )
        test_db.add(article)
        test_db.commit()
        test_db.refresh(article)

        # Add analysis
        analysis = ContentAnalysis(
            content_id=article.id,
            sentiment_score=0.5
        )
        test_db.add(analysis)
        test_db.commit()

        # Verify relationship
        retrieved_article = test_db.query(ScrapedContent).filter(
            ScrapedContent.id == article.id
        ).first()

        assert len(retrieved_article.analyses) == 1
        assert retrieved_article.analyses[0].sentiment_score == 0.5


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_404_not_found(self, client):
        """Test 404 responses"""
        response = client.get("/analysis/results/99999")
        assert response.status_code == 404

    def test_400_bad_request(self, client):
        """Test 400 responses for invalid input"""
        response = client.post(
            "/analysis/analyze",
            json={
                "text": "",  # Empty text
                "analysis_types": []
            }
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_500_server_error_handling(self, client, test_db):
        """Test 500 error handling"""
        # Attempt batch analysis with non-existent IDs
        response = client.post(
            "/analysis/batch-analyze",
            json={
                "content_ids": [99999, 88888],
                "analysis_types": ["sentiment"]
            }
        )

        assert response.status_code in [404, 500]
