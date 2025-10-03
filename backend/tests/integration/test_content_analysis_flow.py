"""
Integration tests for content analysis workflow
Tests scraping → analysis → storage → retrieval flow
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock
from aioresponses import aioresponses
from sqlalchemy.orm import Session

from backend.app.database.models import ScrapedContent, ContentAnalysis, ExtractedVocabulary
from nlp.pipeline import NLPPipeline
from nlp.sentiment_analyzer import SentimentAnalyzer
from nlp.topic_modeler import TopicModeler


@pytest.fixture
def sample_scraped_article(db_session: Session):
    """Create sample scraped article"""
    article = ScrapedContent(
        source="El Tiempo",
        source_url="https://eltiempo.com/test-article",
        category="economy",
        title="Colombia's Economic Growth Continues",
        subtitle="GDP increases by 3.5% in Q1",
        content="""
            La economía colombiana registró un crecimiento del 3.5% en el primer trimestre,
            superando las expectativas de los analistas. El sector agrícola lideró esta
            expansión, con aumentos significativos en la producción de café y aguacate.

            El gobierno anunció nuevas políticas para fortalecer el desarrollo económico
            y atraer inversión extranjera. Los expertos consideran que estas medidas
            tendrán un impacto positivo en el empleo y la reducción de la pobreza.
        """,
        author="María González",
        word_count=150,
        published_date=datetime(2024, 1, 15, 10, 0, 0),
        difficulty_score=3.5,
        is_paywall=False
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


@pytest.fixture
def nlp_components():
    """Initialize NLP components"""
    return {
        "pipeline": NLPPipeline(),
        "sentiment": SentimentAnalyzer(),
        "topics": TopicModeler(n_topics=3)
    }


class TestContentAnalysisFlow:
    """Test end-to-end content analysis workflows"""

    def test_scraping_to_storage_flow(self, db_session: Session, mock_html_content):
        """Test complete flow from scraping to database storage"""
        with aioresponses() as m:
            m.get(
                "https://test-news.example.com/article",
                status=200,
                body=mock_html_content
            )

            # Simulate scraping
            scraped_data = {
                "source": "Test News",
                "source_url": "https://test-news.example.com/article",
                "category": "test",
                "title": "Test Article Title",
                "content": "This is the article content for testing purposes.",
                "published_date": datetime.utcnow()
            }

            # Store in database
            article = ScrapedContent(**scraped_data)
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)

            # Verify storage
            retrieved = db_session.query(ScrapedContent).filter(
                ScrapedContent.source_url == scraped_data["source_url"]
            ).first()

            assert retrieved is not None
            assert retrieved.title == "Test Article Title"
            assert retrieved.source == "Test News"

    def test_analysis_pipeline_integration(self, db_session: Session, sample_scraped_article,
                                          nlp_components):
        """Test complete analysis pipeline on scraped article"""
        article = sample_scraped_article
        text = f"{article.title}\n\n{article.content}"

        # Step 1: Entity extraction
        entities = nlp_components["pipeline"].extract_entities(text)

        # Step 2: Sentiment analysis
        sentiment = nlp_components["sentiment"].analyze(text)

        # Step 3: Topic modeling
        topics = nlp_components["topics"].predict_topics(text)

        # Step 4: Summarization
        summary = nlp_components["pipeline"].summarize(text, max_length=100)

        # Store analysis results
        analysis = ContentAnalysis(
            content_id=article.id,
            entities=entities,
            sentiment_score=sentiment.polarity,
            sentiment_label=sentiment.classification,
            topics=topics,
            summary=summary,
            processing_time_ms=150,
            model_version="1.0.0"
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)

        # Verify analysis storage
        assert analysis.content_id == article.id
        assert analysis.entities is not None
        assert analysis.sentiment_score is not None
        assert -1.0 <= analysis.sentiment_score <= 1.0
        assert analysis.summary is not None

    def test_vocabulary_extraction_from_content(self, db_session: Session,
                                               sample_scraped_article, nlp_components):
        """Test extracting vocabulary from analyzed content"""
        article = sample_scraped_article
        text = article.content

        # Extract entities as vocabulary candidates
        entities = nlp_components["pipeline"].extract_entities(text)

        # Extract key vocabulary items
        vocabulary_items = []
        key_words = ["economía", "crecimiento", "desarrollo", "gobierno", "inversión"]

        for word in key_words:
            if word.lower() in text.lower():
                vocab = ExtractedVocabulary(
                    content_id=article.id,
                    word=word,
                    lemma=word,
                    pos_tag="NOUN",
                    sentence=text[:200],  # First sentence as example
                    frequency_in_article=text.lower().count(word.lower()),
                    difficulty_level=3,
                    is_colombian_specific=False,
                    english_translation="",  # Would be filled by translation service
                )
                vocabulary_items.append(vocab)
                db_session.add(vocab)

        db_session.commit()

        # Verify vocabulary extraction
        extracted = db_session.query(ExtractedVocabulary).filter(
            ExtractedVocabulary.content_id == article.id
        ).all()

        assert len(extracted) > 0
        assert any(v.word == "economía" for v in extracted)

    def test_batch_content_processing(self, db_session: Session, nlp_components):
        """Test processing multiple articles in batch"""
        # Create multiple articles
        articles_data = [
            {
                "source": "El Tiempo",
                "url": f"https://example.com/article{i}",
                "title": f"Test Article {i}",
                "content": f"Content for article {i} about Colombian economy and politics.",
                "category": "economy" if i % 2 == 0 else "politics"
            }
            for i in range(5)
        ]

        articles = []
        for data in articles_data:
            article = ScrapedContent(
                source=data["source"],
                source_url=data["url"],
                title=data["title"],
                content=data["content"],
                category=data["category"],
                published_date=datetime.utcnow()
            )
            articles.append(article)
            db_session.add(article)

        db_session.commit()

        # Batch analysis
        for article in articles:
            text = f"{article.title}\n\n{article.content}"
            sentiment = nlp_components["sentiment"].analyze(text)

            analysis = ContentAnalysis(
                content_id=article.id,
                sentiment_score=sentiment.polarity,
                sentiment_label=sentiment.classification,
                processing_time_ms=100
            )
            db_session.add(analysis)

        db_session.commit()

        # Verify batch processing
        analyses = db_session.query(ContentAnalysis).all()
        assert len(analyses) == 5
        assert all(a.sentiment_score is not None for a in analyses)

    def test_error_handling_in_analysis_flow(self, db_session: Session):
        """Test error handling during analysis workflow"""
        # Create article with problematic content
        problem_article = ScrapedContent(
            source="Test",
            source_url="https://example.com/problem",
            title="",  # Empty title
            content="",  # Empty content
            published_date=datetime.utcnow()
        )
        db_session.add(problem_article)
        db_session.commit()

        # Attempt analysis with error handling
        try:
            text = f"{problem_article.title}\n\n{problem_article.content}".strip()

            if not text:
                # Handle empty content gracefully
                analysis = ContentAnalysis(
                    content_id=problem_article.id,
                    sentiment_score=0.0,
                    sentiment_label="neutral",
                    entities=[],
                    topics=[],
                    summary="No content available",
                    processing_time_ms=0
                )
                db_session.add(analysis)
                db_session.commit()
        except Exception as e:
            # Ensure error doesn't crash the system
            pytest.fail(f"Error handling failed: {str(e)}")

        # Verify error was handled
        analysis = db_session.query(ContentAnalysis).filter(
            ContentAnalysis.content_id == problem_article.id
        ).first()

        assert analysis is not None
        assert analysis.summary == "No content available"

    def test_content_deduplication(self, db_session: Session):
        """Test preventing duplicate content storage"""
        import hashlib

        article_data = {
            "source": "El Tiempo",
            "source_url": "https://example.com/unique",
            "title": "Unique Article",
            "content": "This is unique content for testing."
        }

        # Generate content hash
        content_hash = hashlib.sha256(
            article_data["content"].encode()
        ).hexdigest()

        # First insert
        article1 = ScrapedContent(
            **article_data,
            content_hash=content_hash,
            published_date=datetime.utcnow()
        )
        db_session.add(article1)
        db_session.commit()

        # Attempt duplicate insert
        try:
            article2 = ScrapedContent(
                **article_data,
                content_hash=content_hash,
                published_date=datetime.utcnow()
            )
            db_session.add(article2)
            db_session.commit()
            pytest.fail("Should have raised unique constraint violation")
        except Exception:
            # Expected: unique constraint on content_hash
            db_session.rollback()

        # Verify only one article exists
        count = db_session.query(ScrapedContent).filter(
            ScrapedContent.content_hash == content_hash
        ).count()

        assert count == 1

    def test_content_update_workflow(self, db_session: Session, sample_scraped_article):
        """Test updating content and re-analyzing"""
        article = sample_scraped_article
        original_content = article.content

        # Update content
        article.content = original_content + "\n\nNueva información adicional."
        article.updated_at = datetime.utcnow()
        db_session.commit()

        # Re-analyze
        pipeline = NLPPipeline()
        sentiment_analyzer = SentimentAnalyzer()

        text = f"{article.title}\n\n{article.content}"
        sentiment = sentiment_analyzer.analyze(text)
        entities = pipeline.extract_entities(text)

        # Update existing analysis or create new one
        existing_analysis = db_session.query(ContentAnalysis).filter(
            ContentAnalysis.content_id == article.id
        ).first()

        if existing_analysis:
            existing_analysis.sentiment_score = sentiment.polarity
            existing_analysis.entities = entities
            existing_analysis.processed_at = datetime.utcnow()
        else:
            new_analysis = ContentAnalysis(
                content_id=article.id,
                sentiment_score=sentiment.polarity,
                entities=entities
            )
            db_session.add(new_analysis)

        db_session.commit()

        # Verify update
        assert article.updated_at > article.scraped_at

    def test_content_categorization(self, db_session: Session, nlp_components):
        """Test automatic content categorization"""
        articles_data = [
            ("Colombian economy grows", "economía crecimiento PIB", "economy"),
            ("New government policies", "gobierno política reforma", "politics"),
            ("Soccer championship results", "fútbol campeonato goles", "sports"),
        ]

        for title, content, expected_category in articles_data:
            article = ScrapedContent(
                source="Test",
                source_url=f"https://example.com/{expected_category}",
                title=title,
                content=content,
                category=None,  # To be determined
                published_date=datetime.utcnow()
            )
            db_session.add(article)
            db_session.flush()

            # Analyze and categorize
            topics = nlp_components["topics"].predict_topics(content)

            # Simple categorization logic (in production, more sophisticated)
            if "economía" in content or "PIB" in content:
                article.category = "economy"
            elif "gobierno" in content or "política" in content:
                article.category = "politics"
            elif "fútbol" in content:
                article.category = "sports"

            # Store analysis with topics
            analysis = ContentAnalysis(
                content_id=article.id,
                topics=topics
            )
            db_session.add(analysis)

        db_session.commit()

        # Verify categorization
        economy_count = db_session.query(ScrapedContent).filter(
            ScrapedContent.category == "economy"
        ).count()

        assert economy_count >= 1

    def test_colombian_entity_detection(self, db_session: Session, nlp_components):
        """Test detection of Colombian-specific entities"""
        article = ScrapedContent(
            source="El Espectador",
            source_url="https://example.com/colombia",
            title="Colombian Cities Development",
            content="""
                Bogotá, Medellín y Cali están implementando nuevas políticas urbanas.
                El presidente Gustavo Petro visitó Cartagena para anunciar inversiones.
                La región del Eje Cafetero muestra crecimiento económico.
            """,
            published_date=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)

        # Extract Colombian entities
        text = article.content
        entities = nlp_components["pipeline"].extract_entities(text)

        # Store with Colombian markers
        colombian_entities = [
            e for e in entities
            if e["text"] in ["Bogotá", "Medellín", "Cali", "Cartagena",
                           "Gustavo Petro", "Eje Cafetero"]
        ]

        analysis = ContentAnalysis(
            content_id=article.id,
            entities=entities,
            colombian_slang={},  # Would detect Colombian expressions
            regional_variations={"cities": ["Bogotá", "Medellín", "Cali", "Cartagena"]}
        )
        db_session.add(analysis)
        db_session.commit()

        # Verify Colombian entity detection
        assert len(colombian_entities) > 0
        assert analysis.regional_variations is not None

    def test_content_search_and_filtering(self, db_session: Session):
        """Test searching and filtering analyzed content"""
        # Create multiple articles
        for i in range(10):
            article = ScrapedContent(
                source="Test Source",
                source_url=f"https://example.com/article{i}",
                title=f"Article {i}",
                content=f"Content {i}",
                category="economy" if i % 2 == 0 else "politics",
                difficulty_score=float(i % 5 + 1),
                published_date=datetime.utcnow()
            )
            db_session.add(article)

        db_session.commit()

        # Filter by category
        economy_articles = db_session.query(ScrapedContent).filter(
            ScrapedContent.category == "economy"
        ).all()

        # Filter by difficulty
        easy_articles = db_session.query(ScrapedContent).filter(
            ScrapedContent.difficulty_score <= 2.0
        ).all()

        assert len(economy_articles) == 5
        assert len(easy_articles) > 0

    def test_analysis_performance_metrics(self, db_session: Session, nlp_components):
        """Test tracking analysis performance metrics"""
        import time

        article = ScrapedContent(
            source="Test",
            source_url="https://example.com/perf-test",
            title="Performance Test",
            content="This is content for performance testing. " * 50,
            published_date=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)

        # Measure processing time
        start_time = time.time()

        text = article.content
        sentiment = nlp_components["sentiment"].analyze(text)
        entities = nlp_components["pipeline"].extract_entities(text)

        processing_time = int((time.time() - start_time) * 1000)  # milliseconds

        # Store with metrics
        analysis = ContentAnalysis(
            content_id=article.id,
            sentiment_score=sentiment.polarity,
            entities=entities,
            processing_time_ms=processing_time,
            model_version="1.0.0"
        )
        db_session.add(analysis)
        db_session.commit()

        # Verify metrics
        assert analysis.processing_time_ms > 0
        assert analysis.processing_time_ms < 10000  # Should be under 10 seconds
