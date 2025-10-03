"""
Integration tests for vocabulary acquisition workflow
Tests complete flow from vocabulary discovery to practice sessions
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.database.models import User, LearningSession
from backend.app.database.vocabulary_models import (
    VocabularyLemma, VocabularyTranslation, VocabularyContext,
    VocabularyAcquisition, VocabularyForm, VocabularyCollocation
)


@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        full_name="Test User",
        spanish_level="B1",
        learning_goals={"goal": "improve vocabulary"}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_vocabulary_items(db_session: Session):
    """Create sample vocabulary items"""
    items = []

    words_data = [
        {
            "lemma": "economía",
            "pos": "NOUN",
            "translation": "economy",
            "frequency": 1500,
            "is_colombianism": False
        },
        {
            "lemma": "parcero",
            "pos": "NOUN",
            "translation": "buddy, friend",
            "frequency": 800,
            "is_colombianism": True
        },
        {
            "lemma": "chimba",
            "pos": "ADJ",
            "translation": "awesome, cool",
            "frequency": 600,
            "is_colombianism": True
        },
        {
            "lemma": "desarrollo",
            "pos": "NOUN",
            "translation": "development",
            "frequency": 2000,
            "is_colombianism": False
        },
        {
            "lemma": "gobierno",
            "pos": "NOUN",
            "translation": "government",
            "frequency": 2500,
            "is_colombianism": False
        }
    ]

    for word_data in words_data:
        lemma = VocabularyLemma(
            lemma=word_data["lemma"],
            primary_pos=word_data["pos"],
            corpus_frequency=word_data["frequency"],
            frequency_rank=words_data.index(word_data) + 1,
            is_colombianism=word_data["is_colombianism"]
        )
        db_session.add(lemma)
        db_session.flush()

        translation = VocabularyTranslation(
            lemma_id=lemma.id,
            target_language="en",
            translation=word_data["translation"],
            translation_type="manual",
            translation_source="test",
            confidence=1.0
        )
        db_session.add(translation)
        items.append(lemma)

    db_session.commit()
    return items


class TestVocabularyAcquisitionFlow:
    """Test vocabulary learning and acquisition workflows"""

    def test_vocabulary_discovery_and_storage(self, db_session: Session):
        """Test discovering and storing new vocabulary"""
        # Create new vocabulary item
        lemma = VocabularyLemma(
            lemma="infraestructura",
            primary_pos="NOUN",
            corpus_frequency=1200,
            frequency_rank=500,
            is_colombianism=False
        )
        db_session.add(lemma)
        db_session.commit()
        db_session.refresh(lemma)

        # Add translation
        translation = VocabularyTranslation(
            lemma_id=lemma.id,
            target_language="en",
            translation="infrastructure",
            translation_type="literal",
            translation_source="dictionary",
            confidence=1.0
        )
        db_session.add(translation)
        db_session.commit()

        # Add context
        context = VocabularyContext(
            lemma_id=lemma.id,
            sentence="El gobierno invirtió en infraestructura vial.",
            left_context="El gobierno invirtió en",
            right_context="vial",
            is_exemplar=True,
            difficulty_level="B1"
        )
        db_session.add(context)
        db_session.commit()

        # Verify complete vocabulary item
        retrieved = db_session.query(VocabularyLemma).filter(
            VocabularyLemma.lemma == "infraestructura"
        ).first()

        assert retrieved is not None
        assert retrieved.translations[0].translation == "infrastructure"
        assert len(retrieved.contexts) == 1
        assert retrieved.contexts[0].is_exemplar is True

    def test_user_vocabulary_acquisition_tracking(self, db_session: Session, test_user,
                                                   sample_vocabulary_items):
        """Test tracking user's vocabulary acquisition progress"""
        lemma = sample_vocabulary_items[0]

        # Initial exposure
        acquisition = VocabularyAcquisition(
            user_id=test_user.id,
            lemma_id=lemma.id,
            total_exposures=1,
            meaningful_exposures=0,
            comprehension_level=0.1,
            production_level=0.0
        )
        db_session.add(acquisition)
        db_session.commit()

        # Simulate multiple exposures
        for _ in range(5):
            acquisition.total_exposures += 1
            acquisition.meaningful_exposures += 1
            acquisition.comprehension_level = min(acquisition.comprehension_level + 0.15, 1.0)
            acquisition.last_exposure = datetime.utcnow()

        db_session.commit()

        # Verify progress
        assert acquisition.total_exposures == 6
        assert acquisition.meaningful_exposures == 5
        assert acquisition.comprehension_level >= 0.7

    def test_practice_session_creation_and_completion(self, db_session: Session, test_user,
                                                       sample_vocabulary_items):
        """Test creating and completing a practice session"""
        # Create practice session
        session = LearningSession(
            user_id=test_user.id,
            session_type="flashcard",
            items_completed=0,
            correct_answers=0,
            incorrect_answers=0,
            vocabulary_ids=[item.id for item in sample_vocabulary_items[:3]]
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Simulate practice
        total_items = len(sample_vocabulary_items[:3])
        correct = 0
        incorrect = 0

        for lemma in sample_vocabulary_items[:3]:
            # Track acquisition
            acquisition = db_session.query(VocabularyAcquisition).filter(
                and_(
                    VocabularyAcquisition.user_id == test_user.id,
                    VocabularyAcquisition.lemma_id == lemma.id
                )
            ).first()

            if not acquisition:
                acquisition = VocabularyAcquisition(
                    user_id=test_user.id,
                    lemma_id=lemma.id,
                    total_exposures=1,
                    meaningful_exposures=0,
                    comprehension_level=0.0
                )
                db_session.add(acquisition)
            else:
                acquisition.total_exposures += 1

            # Simulate correct answer (80% success rate)
            is_correct = (lemma.id % 5) != 0

            if is_correct:
                correct += 1
                acquisition.meaningful_exposures += 1
                acquisition.comprehension_level = min(
                    acquisition.comprehension_level + 0.1, 1.0
                )
            else:
                incorrect += 1
                acquisition.comprehension_level = max(
                    acquisition.comprehension_level - 0.05, 0.0
                )

            acquisition.last_exposure = datetime.utcnow()

        # Update session
        session.items_completed = total_items
        session.correct_answers = correct
        session.incorrect_answers = incorrect
        session.score = (correct / total_items) * 100
        session.ended_at = datetime.utcnow()
        session.duration_seconds = 300  # 5 minutes

        db_session.commit()

        # Verify session
        assert session.items_completed == 3
        assert session.correct_answers + session.incorrect_answers == 3
        assert 0 <= session.score <= 100

    def test_vocabulary_list_generation_by_frequency(self, db_session: Session,
                                                      sample_vocabulary_items):
        """Test generating vocabulary list by frequency"""
        from backend.app.database.vocabulary_models import VocabularyList

        # Get top 3 most frequent words
        top_words = db_session.query(VocabularyLemma).order_by(
            VocabularyLemma.corpus_frequency.desc()
        ).limit(3).all()

        # Create list
        vocab_list = VocabularyList(
            name="Most Common Words",
            description="Top frequency vocabulary",
            list_type="frequency",
            topic="general",
            source="corpus_analysis",
            target_level="B1",
            lemma_ids=[w.id for w in top_words],
            total_items=len(top_words),
            created_by="system"
        )
        db_session.add(vocab_list)
        db_session.commit()

        # Verify list
        assert vocab_list.total_items == 3
        assert len(vocab_list.lemma_ids) == 3

    def test_colombian_vocabulary_filtering(self, db_session: Session,
                                            sample_vocabulary_items):
        """Test filtering Colombian-specific vocabulary"""
        colombian_words = db_session.query(VocabularyLemma).filter(
            VocabularyLemma.is_colombianism == True
        ).all()

        assert len(colombian_words) >= 2
        assert any(w.lemma == "parcero" for w in colombian_words)
        assert any(w.lemma == "chimba" for w in colombian_words)

    def test_vocabulary_context_linking(self, db_session: Session, sample_vocabulary_items):
        """Test linking vocabulary with context from scraped content"""
        from backend.app.database.models import ScrapedContent

        # Create scraped content
        content = ScrapedContent(
            source="El Tiempo",
            source_url="https://example.com/article1",
            title="Economic Development",
            content="El desarrollo económico de Colombia ha sido notable.",
            category="economy",
            published_date=datetime.utcnow(),
            word_count=50
        )
        db_session.add(content)
        db_session.commit()
        db_session.refresh(content)

        # Link vocabulary context
        lemma = sample_vocabulary_items[3]  # desarrollo

        context = VocabularyContext(
            lemma_id=lemma.id,
            source_content_id=content.id,
            sentence="El desarrollo económico de Colombia ha sido notable.",
            token_position=1,
            left_context="El",
            right_context="económico de Colombia",
            syntactic_role="subject",
            source_date=content.published_date,
            source_category=content.category,
            source_url=content.source_url,
            is_exemplar=True,
            difficulty_level="B2"
        )
        db_session.add(context)
        db_session.commit()

        # Verify linking
        assert context.source_content_id == content.id
        assert context.sentence in content.content

    def test_vocabulary_forms_and_conjugations(self, db_session: Session):
        """Test storing and retrieving verb forms"""
        # Create base verb
        verb = VocabularyLemma(
            lemma="hablar",
            primary_pos="VERB",
            corpus_frequency=3000,
            frequency_rank=100
        )
        db_session.add(verb)
        db_session.flush()

        # Add forms
        forms_data = [
            ("hablo", "VERB", {"Person": "1", "Number": "Sing", "Tense": "Pres"}),
            ("hablas", "VERB", {"Person": "2", "Number": "Sing", "Tense": "Pres"}),
            ("habla", "VERB", {"Person": "3", "Number": "Sing", "Tense": "Pres"}),
            ("hablé", "VERB", {"Person": "1", "Number": "Sing", "Tense": "Past"}),
        ]

        for surface, pos, morphology in forms_data:
            form = VocabularyForm(
                lemma_id=verb.id,
                surface_form=surface,
                pos_tag=pos,
                morphology=morphology,
                form_frequency=500
            )
            db_session.add(form)

        db_session.commit()

        # Verify forms
        retrieved_verb = db_session.query(VocabularyLemma).filter(
            VocabularyLemma.lemma == "hablar"
        ).first()

        assert len(retrieved_verb.forms) == 4
        present_forms = [f for f in retrieved_verb.forms
                        if f.morphology.get("Tense") == "Pres"]
        assert len(present_forms) == 3

    def test_vocabulary_collocations(self, db_session: Session):
        """Test storing and retrieving collocations"""
        # Create words
        verb = VocabularyLemma(
            lemma="tomar",
            primary_pos="VERB",
            corpus_frequency=2500
        )
        noun = VocabularyLemma(
            lemma="decisión",
            primary_pos="NOUN",
            corpus_frequency=1800
        )
        db_session.add_all([verb, noun])
        db_session.flush()

        # Create collocation
        collocation = VocabularyCollocation(
            lemma_id=verb.id,
            collocate_id=noun.id,
            pattern="tomar_decisión",
            pattern_type="verb_noun",
            position="before",
            frequency=450,
            mutual_information=5.2,
            is_fixed_expression=True
        )
        db_session.add(collocation)
        db_session.commit()

        # Verify collocation
        retrieved = db_session.query(VocabularyCollocation).filter(
            VocabularyCollocation.pattern == "tomar_decisión"
        ).first()

        assert retrieved is not None
        assert retrieved.is_fixed_expression is True
        assert retrieved.mutual_information > 0

    def test_spaced_repetition_scheduling(self, db_session: Session, test_user,
                                          sample_vocabulary_items):
        """Test spaced repetition scheduling logic"""
        lemma = sample_vocabulary_items[0]

        # Create acquisition
        acquisition = VocabularyAcquisition(
            user_id=test_user.id,
            lemma_id=lemma.id,
            total_exposures=1,
            comprehension_level=0.5,
            last_exposure=datetime.utcnow()
        )
        db_session.add(acquisition)
        db_session.commit()

        # Simulate learning progress with spaced repetition
        intervals = [1, 2, 4, 7, 14]  # Days

        for interval in intervals:
            acquisition.total_exposures += 1
            acquisition.comprehension_level = min(
                acquisition.comprehension_level + 0.1, 1.0
            )
            acquisition.last_exposure = datetime.utcnow()

        db_session.commit()

        # Verify progression
        assert acquisition.total_exposures == 6
        assert acquisition.comprehension_level >= 0.9

    def test_user_progress_analytics(self, db_session: Session, test_user,
                                     sample_vocabulary_items):
        """Test user progress analytics calculation"""
        # Create multiple acquisition records
        for lemma in sample_vocabulary_items:
            level = 0.2 * (sample_vocabulary_items.index(lemma) + 1)
            acquisition = VocabularyAcquisition(
                user_id=test_user.id,
                lemma_id=lemma.id,
                total_exposures=5,
                meaningful_exposures=4,
                comprehension_level=min(level, 1.0)
            )
            db_session.add(acquisition)

        db_session.commit()

        # Calculate statistics
        all_vocab = db_session.query(VocabularyAcquisition).filter(
            VocabularyAcquisition.user_id == test_user.id
        ).all()

        total_words = len(all_vocab)
        mastered_words = sum(1 for v in all_vocab if v.comprehension_level >= 0.8)
        total_exposures = sum(v.total_exposures for v in all_vocab)
        total_meaningful = sum(v.meaningful_exposures for v in all_vocab)
        accuracy = (total_meaningful / total_exposures) if total_exposures > 0 else 0

        assert total_words == 5
        assert mastered_words >= 1
        assert 0 <= accuracy <= 1

    def test_vocabulary_personalization(self, db_session: Session, test_user,
                                        sample_vocabulary_items):
        """Test user vocabulary personalization features"""
        lemma = sample_vocabulary_items[0]

        # Create personalized entry
        acquisition = VocabularyAcquisition(
            user_id=test_user.id,
            lemma_id=lemma.id,
            total_exposures=1,
            preferred_translation="My preferred meaning",
            user_notes="This word is important for my business meetings",
            mnemonic="Remember: economy = eco + nomy",
            personal_examples=[
                "La economía colombiana está creciendo.",
                "Estudio economía en la universidad."
            ]
        )
        db_session.add(acquisition)
        db_session.commit()

        # Verify personalization
        retrieved = db_session.query(VocabularyAcquisition).filter(
            and_(
                VocabularyAcquisition.user_id == test_user.id,
                VocabularyAcquisition.lemma_id == lemma.id
            )
        ).first()

        assert retrieved.preferred_translation == "My preferred meaning"
        assert retrieved.user_notes is not None
        assert retrieved.mnemonic is not None
        assert len(retrieved.personal_examples) == 2
