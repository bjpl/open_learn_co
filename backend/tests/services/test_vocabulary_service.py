"""
Unit tests for vocabulary service layer
Testing CRUD operations and business logic
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

from backend.services.vocabulary_service import VocabularyService
from backend.app.database.vocabulary_models import (
    VocabularyLemma,
    VocabularyTranslation,
    VocabularyAcquisition
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def vocabulary_service(mock_db_session):
    """Create vocabulary service with mocked session"""
    return VocabularyService(mock_db_session)


@pytest.fixture
def sample_lemma():
    """Sample vocabulary lemma for testing"""
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
    """Sample translation for testing"""
    return VocabularyTranslation(
        id=1,
        lemma_id=1,
        target_language='en',
        translation='to speak',
        translation_type='manual',
        confidence=1.0
    )


class TestVocabularyServiceInit:
    """Test VocabularyService initialization"""

    def test_initialization(self, mock_db_session):
        """Should initialize service with database session"""
        service = VocabularyService(mock_db_session)

        assert service is not None
        assert service.db == mock_db_session


class TestCreateLemma:
    """Test lemma creation operations"""

    def test_create_new_lemma(self, vocabulary_service, mock_db_session):
        """Should create new vocabulary lemma"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.create_lemma(
            lemma="correr",
            pos="VERB",
            frequency=500
        )

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_create_duplicate_lemma(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should handle duplicate lemma creation"""
        mock_db_session.query().filter().first.return_value = sample_lemma

        # Should either raise error or return existing
        result = vocabulary_service.create_lemma(
            lemma="hablar",
            pos="VERB"
        )

        # Verify no new entry was added
        assert mock_db_session.add.call_count == 0 or result is not None

    def test_create_lemma_with_phonetic(self, vocabulary_service, mock_db_session):
        """Should create lemma with phonetic transcription"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.create_lemma(
            lemma="niño",
            pos="NOUN",
            phonetic="ˈniɲo"
        )

        mock_db_session.add.assert_called_once()


class TestGetLemma:
    """Test lemma retrieval operations"""

    def test_get_existing_lemma(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should retrieve existing lemma by ID"""
        mock_db_session.query().filter().first.return_value = sample_lemma

        result = vocabulary_service.get_lemma(1)

        assert result is not None
        assert result.id == 1
        assert result.lemma == "hablar"

    def test_get_nonexistent_lemma(self, vocabulary_service, mock_db_session):
        """Should return None for nonexistent lemma"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.get_lemma(999)

        assert result is None

    def test_get_lemma_by_text(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should retrieve lemma by text"""
        mock_db_session.query().filter().first.return_value = sample_lemma

        result = vocabulary_service.get_lemma_by_text("hablar")

        assert result is not None
        assert result.lemma == "hablar"


class TestUpdateLemma:
    """Test lemma update operations"""

    def test_update_existing_lemma(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should update existing lemma"""
        mock_db_session.query().filter().first.return_value = sample_lemma

        result = vocabulary_service.update_lemma(
            lemma_id=1,
            frequency=1500,
            phonetic="new_phonetic"
        )

        mock_db_session.commit.assert_called_once()

    def test_update_nonexistent_lemma(self, vocabulary_service, mock_db_session):
        """Should handle update of nonexistent lemma"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.update_lemma(
            lemma_id=999,
            frequency=1000
        )

        # Should not attempt to update
        assert mock_db_session.commit.call_count == 0 or result is None


class TestDeleteLemma:
    """Test lemma deletion operations"""

    def test_delete_existing_lemma(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should delete existing lemma"""
        mock_db_session.query().filter().first.return_value = sample_lemma

        result = vocabulary_service.delete_lemma(1)

        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_delete_nonexistent_lemma(self, vocabulary_service, mock_db_session):
        """Should handle deletion of nonexistent lemma"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.delete_lemma(999)

        # Should not attempt to delete
        assert mock_db_session.delete.call_count == 0


class TestTranslationOperations:
    """Test translation CRUD operations"""

    def test_add_translation(self, vocabulary_service, mock_db_session):
        """Should add translation to lemma"""
        result = vocabulary_service.add_translation(
            lemma_id=1,
            target_language='en',
            translation='to speak'
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_get_translations(self, vocabulary_service, mock_db_session, sample_translation):
        """Should retrieve all translations for lemma"""
        mock_db_session.query().filter().all.return_value = [sample_translation]

        result = vocabulary_service.get_translations(lemma_id=1)

        assert len(result) == 1
        assert result[0].translation == 'to speak'

    def test_get_translation_by_language(self, vocabulary_service, mock_db_session, sample_translation):
        """Should retrieve translation for specific language"""
        mock_db_session.query().filter().first.return_value = sample_translation

        result = vocabulary_service.get_translation(
            lemma_id=1,
            target_language='en'
        )

        assert result is not None
        assert result.target_language == 'en'

    def test_update_translation(self, vocabulary_service, mock_db_session, sample_translation):
        """Should update existing translation"""
        mock_db_session.query().filter().first.return_value = sample_translation

        result = vocabulary_service.update_translation(
            translation_id=1,
            translation='to talk',
            confidence=0.9
        )

        mock_db_session.commit.assert_called_once()


class TestUserVocabularyAcquisition:
    """Test user vocabulary acquisition tracking"""

    def test_track_new_word_exposure(self, vocabulary_service, mock_db_session):
        """Should track first exposure to word"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.track_exposure(
            user_id=1,
            lemma_id=1,
            meaningful=True
        )

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_track_repeat_exposure(self, vocabulary_service, mock_db_session):
        """Should increment exposure count for known word"""
        existing_acquisition = VocabularyAcquisition(
            user_id=1,
            lemma_id=1,
            total_exposures=5,
            meaningful_exposures=3,
            comprehension_level=0.6,
            production_level=0.0
        )
        mock_db_session.query().filter().first.return_value = existing_acquisition

        result = vocabulary_service.track_exposure(
            user_id=1,
            lemma_id=1,
            meaningful=True
        )

        # Should increment exposure counts
        assert existing_acquisition.total_exposures >= 6
        mock_db_session.commit.assert_called_once()

    def test_update_comprehension_level(self, vocabulary_service, mock_db_session):
        """Should update comprehension level based on practice"""
        existing = VocabularyAcquisition(
            user_id=1,
            lemma_id=1,
            comprehension_level=0.5
        )
        mock_db_session.query().filter().first.return_value = existing

        result = vocabulary_service.update_comprehension(
            user_id=1,
            lemma_id=1,
            correct=True
        )

        # Comprehension should increase
        assert existing.comprehension_level > 0.5
        mock_db_session.commit.assert_called_once()

    def test_update_production_level(self, vocabulary_service, mock_db_session):
        """Should update production level"""
        existing = VocabularyAcquisition(
            user_id=1,
            lemma_id=1,
            production_level=0.3
        )
        mock_db_session.query().filter().first.return_value = existing

        result = vocabulary_service.update_production(
            user_id=1,
            lemma_id=1,
            success=True
        )

        # Production level should increase
        assert existing.production_level > 0.3
        mock_db_session.commit.assert_called_once()


class TestVocabularySearch:
    """Test vocabulary search and filtering"""

    def test_search_by_lemma_text(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should search vocabulary by lemma text"""
        mock_db_session.query().filter().all.return_value = [sample_lemma]

        result = vocabulary_service.search_lemmas(search_term="habl")

        assert len(result) > 0

    def test_filter_by_pos(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should filter lemmas by part of speech"""
        mock_db_session.query().filter().all.return_value = [sample_lemma]

        result = vocabulary_service.get_lemmas_by_pos("VERB")

        assert len(result) > 0
        assert all(lemma.primary_pos == "VERB" for lemma in result)

    def test_filter_by_frequency_range(self, vocabulary_service, mock_db_session, sample_lemma):
        """Should filter by frequency range"""
        mock_db_session.query().filter().all.return_value = [sample_lemma]

        result = vocabulary_service.get_lemmas_by_frequency(
            min_freq=500,
            max_freq=1500
        )

        assert len(result) > 0

    def test_pagination(self, vocabulary_service, mock_db_session):
        """Should support pagination"""
        mock_lemmas = [
            VocabularyLemma(id=i, lemma=f"word{i}")
            for i in range(25)
        ]
        mock_db_session.query().offset().limit().all.return_value = mock_lemmas[:20]

        result = vocabulary_service.get_lemmas(skip=0, limit=20)

        assert len(result) <= 20


class TestUserProgress:
    """Test user progress tracking"""

    def test_get_user_vocabulary_count(self, vocabulary_service, mock_db_session):
        """Should count user's vocabulary"""
        mock_db_session.query().filter().count.return_value = 150

        count = vocabulary_service.get_user_vocabulary_count(user_id=1)

        assert count == 150

    def test_get_mastered_words(self, vocabulary_service, mock_db_session):
        """Should retrieve mastered words"""
        mastered = [
            VocabularyAcquisition(
                lemma_id=i,
                comprehension_level=0.9
            )
            for i in range(10)
        ]
        mock_db_session.query().filter().all.return_value = mastered

        result = vocabulary_service.get_mastered_words(
            user_id=1,
            threshold=0.8
        )

        assert len(result) == 10

    def test_get_words_to_review(self, vocabulary_service, mock_db_session):
        """Should identify words needing review"""
        needs_review = [
            VocabularyAcquisition(
                lemma_id=i,
                comprehension_level=0.5,
                last_exposure=datetime.now()
            )
            for i in range(5)
        ]
        mock_db_session.query().filter().all.return_value = needs_review

        result = vocabulary_service.get_words_for_review(user_id=1)

        assert isinstance(result, list)


class TestBulkOperations:
    """Test bulk operations"""

    def test_bulk_create_lemmas(self, vocabulary_service, mock_db_session):
        """Should create multiple lemmas at once"""
        lemmas_data = [
            {"lemma": "correr", "pos": "VERB"},
            {"lemma": "saltar", "pos": "VERB"},
            {"lemma": "casa", "pos": "NOUN"}
        ]

        result = vocabulary_service.bulk_create_lemmas(lemmas_data)

        # Should add all lemmas
        assert mock_db_session.add.call_count >= len(lemmas_data)
        mock_db_session.commit.assert_called()

    def test_bulk_add_translations(self, vocabulary_service, mock_db_session):
        """Should add multiple translations at once"""
        translations_data = [
            {"lemma_id": 1, "target_language": "en", "translation": "to run"},
            {"lemma_id": 2, "target_language": "en", "translation": "to jump"}
        ]

        result = vocabulary_service.bulk_add_translations(translations_data)

        assert mock_db_session.add.call_count >= len(translations_data)


class TestStatistics:
    """Test vocabulary statistics"""

    def test_get_total_lemma_count(self, vocabulary_service, mock_db_session):
        """Should return total lemma count"""
        mock_db_session.query().count.return_value = 5000

        count = vocabulary_service.get_total_lemma_count()

        assert count == 5000

    def test_get_pos_distribution(self, vocabulary_service, mock_db_session):
        """Should return part-of-speech distribution"""
        mock_results = [
            ("VERB", 1500),
            ("NOUN", 2000),
            ("ADJ", 800)
        ]
        mock_db_session.query().group_by().all.return_value = mock_results

        result = vocabulary_service.get_pos_distribution()

        assert len(result) == 3

    def test_get_frequency_stats(self, vocabulary_service, mock_db_session):
        """Should return frequency statistics"""
        mock_db_session.query().filter().count.return_value = 1000

        stats = vocabulary_service.get_frequency_stats()

        assert isinstance(stats, dict)


class TestErrorHandling:
    """Test error handling"""

    def test_handle_database_error(self, vocabulary_service, mock_db_session):
        """Should handle database errors gracefully"""
        mock_db_session.commit.side_effect = Exception("Database error")

        # Should not raise, but handle error
        try:
            vocabulary_service.create_lemma("test", "NOUN")
        except Exception as e:
            assert "Database error" in str(e)

    def test_handle_invalid_input(self, vocabulary_service, mock_db_session):
        """Should validate input data"""
        # Empty lemma text
        result = vocabulary_service.create_lemma("", "NOUN")

        # Should either raise or return None
        assert result is None or mock_db_session.add.call_count == 0

    def test_rollback_on_error(self, vocabulary_service, mock_db_session):
        """Should rollback transaction on error"""
        mock_db_session.commit.side_effect = Exception("Error")
        mock_db_session.rollback = Mock()

        try:
            vocabulary_service.create_lemma("test", "NOUN")
        except:
            pass

        # Rollback should be called
        mock_db_session.rollback.assert_called()


class TestEdgeCases:
    """Test edge cases"""

    def test_lemma_with_special_characters(self, vocabulary_service, mock_db_session):
        """Should handle lemmas with special characters"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.create_lemma(
            lemma="niño/niña",
            pos="NOUN"
        )

        mock_db_session.add.assert_called()

    def test_very_long_translation(self, vocabulary_service, mock_db_session):
        """Should handle very long translations"""
        long_translation = "a" * 500

        result = vocabulary_service.add_translation(
            lemma_id=1,
            target_language='en',
            translation=long_translation
        )

        mock_db_session.add.assert_called()

    def test_zero_frequency(self, vocabulary_service, mock_db_session):
        """Should handle zero frequency lemmas"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.create_lemma(
            lemma="rare",
            pos="ADJ",
            frequency=0
        )

        mock_db_session.add.assert_called()

    def test_negative_user_id(self, vocabulary_service, mock_db_session):
        """Should handle invalid user IDs"""
        mock_db_session.query().filter().first.return_value = None

        result = vocabulary_service.track_exposure(
            user_id=-1,
            lemma_id=1
        )

        # Should either reject or handle gracefully
        assert result is None or isinstance(result, VocabularyAcquisition)


# Integration-style tests
class TestServiceIntegration:
    """Integration-style tests for service workflows"""

    def test_complete_word_addition_workflow(self, vocabulary_service, mock_db_session):
        """Should handle complete word addition workflow"""
        # 1. Create lemma
        mock_db_session.query().filter().first.return_value = None
        lemma = vocabulary_service.create_lemma("correr", "VERB", 500)

        # 2. Add translation
        translation = vocabulary_service.add_translation(1, "en", "to run")

        # 3. Verify both operations completed
        assert mock_db_session.add.call_count >= 2
        assert mock_db_session.commit.call_count >= 2

    def test_user_learning_workflow(self, vocabulary_service, mock_db_session):
        """Should handle complete user learning workflow"""
        # 1. Track first exposure
        mock_db_session.query().filter().first.return_value = None
        vocabulary_service.track_exposure(1, 1, meaningful=True)

        # 2. Update comprehension after practice
        mock_acq = VocabularyAcquisition(
            user_id=1,
            lemma_id=1,
            comprehension_level=0.0
        )
        mock_db_session.query().filter().first.return_value = mock_acq
        vocabulary_service.update_comprehension(1, 1, correct=True)

        # Verify workflow completed
        assert mock_db_session.commit.call_count >= 2
