"""
Integration tests for complete NLP pipeline workflows
Tests end-to-end text processing with real NLP components
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict

from nlp.pipeline import NLPPipeline
from nlp.sentiment_analyzer import SentimentAnalyzer
from nlp.topic_modeler import TopicModeler
from nlp.difficulty_scorer import DifficultyScorer


@pytest.fixture
def nlp_pipeline():
    """Initialize NLP pipeline with all components"""
    return NLPPipeline()


@pytest.fixture
def sentiment_analyzer():
    """Initialize sentiment analyzer"""
    return SentimentAnalyzer()


@pytest.fixture
def topic_modeler():
    """Initialize topic modeler"""
    return TopicModeler(n_topics=5)


@pytest.fixture
def difficulty_scorer():
    """Initialize difficulty scorer"""
    return DifficultyScorer()


@pytest.fixture
def sample_spanish_texts():
    """Sample Spanish texts for testing"""
    return {
        "simple": "Hoy es un día hermoso en Colombia. El clima está perfecto para salir a caminar.",
        "intermediate": """
            La economía colombiana mostró un crecimiento del 3.2% en el último trimestre,
            superando las expectativas de los analistas. El sector agrícola lideró esta expansión,
            con aumentos significativos en la producción de café y aguacate.
        """,
        "advanced": """
            El debate sobre la implementación de políticas económicas heterodoxas en Colombia
            ha cobrado relevancia en los círculos académicos y gubernamentales. Los economistas
            discrepan sobre la viabilidad de medidas fiscales expansivas en el contexto de
            presiones inflacionarias persistentes y volatilidad cambiaria.
        """,
        "colombian_slang": """
            ¿Qué más parcero? Ayer me fui a tomar tinto con los manes del barrio.
            Nos la pasamos bacano hablando de vaina y media. Fue una chimba de tarde.
        """,
        "news_article": """
            Bogotá, 15 de enero - El presidente Gustavo Petro anunció hoy nuevas medidas
            para fortalecer el sistema de salud colombiano. Durante su discurso en la Plaza
            de Bolívar, el mandatario destacó la importancia de garantizar acceso universal
            a servicios médicos de calidad. La reforma propuesta incluye aumentos en el
            presupuesto destinado a hospitales públicos y la contratación de 5,000 nuevos
            profesionales de la salud.
        """
    }


class TestNLPPipelineIntegration:
    """Integration tests for NLP pipeline"""

    @pytest.mark.asyncio
    async def test_complete_pipeline_simple_text(self, nlp_pipeline, sample_spanish_texts):
        """Test complete NLP processing on simple text"""
        text = sample_spanish_texts["simple"]

        # Extract entities
        entities = nlp_pipeline.extract_entities(text)
        assert isinstance(entities, list)
        assert any(ent["text"] == "Colombia" for ent in entities)

        # Generate summary
        summary = nlp_pipeline.summarize(text, max_length=50)
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) < len(text)

    @pytest.mark.asyncio
    async def test_complete_pipeline_news_article(self, nlp_pipeline, sentiment_analyzer,
                                                   topic_modeler, difficulty_scorer,
                                                   sample_spanish_texts):
        """Test complete analysis workflow on news article"""
        text = sample_spanish_texts["news_article"]

        # Step 1: Entity extraction
        entities = nlp_pipeline.extract_entities(text)
        assert len(entities) > 0

        # Verify key entities detected
        entity_texts = [e["text"] for e in entities]
        assert "Bogotá" in entity_texts or "Gustavo Petro" in entity_texts

        # Step 2: Sentiment analysis
        sentiment = sentiment_analyzer.analyze(text)
        assert hasattr(sentiment, 'polarity')
        assert hasattr(sentiment, 'subjectivity')
        assert -1.0 <= sentiment.polarity <= 1.0
        assert 0.0 <= sentiment.subjectivity <= 1.0

        # Step 3: Topic modeling
        topics = topic_modeler.predict_topics(text)
        assert isinstance(topics, list)

        # Step 4: Difficulty scoring
        difficulty = difficulty_scorer.score(text)
        assert hasattr(difficulty, 'difficulty_score')
        assert hasattr(difficulty, 'cefr_level')
        assert difficulty.cefr_level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

        # Step 5: Summarization
        summary = nlp_pipeline.summarize(text, max_length=100)
        assert len(summary) < len(text)
        assert len(summary) > 20

    @pytest.mark.asyncio
    async def test_multilingual_support(self, nlp_pipeline, sentiment_analyzer):
        """Test processing of texts in different languages"""
        texts = {
            "spanish": "La economía colombiana está creciendo rápidamente.",
            "english": "The Colombian economy is growing rapidly.",
            "mixed": "Colombia's economía is showing great crecimiento."
        }

        for lang, text in texts.items():
            # Should handle all texts without errors
            entities = nlp_pipeline.extract_entities(text)
            sentiment = sentiment_analyzer.analyze(text)

            assert isinstance(entities, list)
            assert hasattr(sentiment, 'polarity')

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, nlp_pipeline, sample_spanish_texts):
        """Test performance of batch text processing"""
        import time

        texts = [sample_spanish_texts["news_article"]] * 10

        start_time = time.time()
        results = []

        for text in texts:
            entities = nlp_pipeline.extract_entities(text)
            summary = nlp_pipeline.summarize(text, max_length=100)
            results.append({
                "entities": entities,
                "summary": summary
            })

        duration = time.time() - start_time

        # Should process 10 articles in reasonable time (< 30 seconds)
        assert duration < 30.0
        assert len(results) == 10
        assert all("entities" in r and "summary" in r for r in results)

    @pytest.mark.asyncio
    async def test_colombian_text_processing(self, nlp_pipeline, sentiment_analyzer,
                                            sample_spanish_texts):
        """Test processing of Colombian-specific text and slang"""
        text = sample_spanish_texts["colombian_slang"]

        # Should process Colombian slang without errors
        entities = nlp_pipeline.extract_entities(text)
        sentiment = sentiment_analyzer.analyze(text)

        assert isinstance(entities, list)
        # Sentiment should still be calculated
        assert hasattr(sentiment, 'polarity')

    @pytest.mark.asyncio
    async def test_difficulty_levels_progressive(self, difficulty_scorer, sample_spanish_texts):
        """Test that difficulty scoring recognizes text complexity levels"""
        simple_text = sample_spanish_texts["simple"]
        intermediate_text = sample_spanish_texts["intermediate"]
        advanced_text = sample_spanish_texts["advanced"]

        simple_score = difficulty_scorer.score(simple_text)
        intermediate_score = difficulty_scorer.score(intermediate_text)
        advanced_score = difficulty_scorer.score(advanced_text)

        # Convert CEFR levels to numeric for comparison
        cefr_to_num = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}

        simple_level = cefr_to_num[simple_score.cefr_level]
        intermediate_level = cefr_to_num[intermediate_score.cefr_level]
        advanced_level = cefr_to_num[advanced_score.cefr_level]

        # Verify progressive difficulty
        assert simple_level <= intermediate_level
        assert intermediate_level <= advanced_level

    @pytest.mark.asyncio
    async def test_entity_types_variety(self, nlp_pipeline, sample_spanish_texts):
        """Test that various entity types are detected"""
        text = sample_spanish_texts["news_article"]
        entities = nlp_pipeline.extract_entities(text)

        # Should detect multiple entity types
        entity_types = set(e["label"] for e in entities)

        # Should have at least location and person entities
        assert len(entity_types) >= 2

    @pytest.mark.asyncio
    async def test_sentiment_consistency(self, sentiment_analyzer):
        """Test sentiment analysis consistency"""
        positive_text = "Esta es una noticia excelente y maravillosa para Colombia."
        negative_text = "Esta es una tragedia terrible y devastadora para el país."
        neutral_text = "El informe presentó los datos económicos del trimestre."

        pos_sentiment = sentiment_analyzer.analyze(positive_text)
        neg_sentiment = sentiment_analyzer.analyze(negative_text)
        neu_sentiment = sentiment_analyzer.analyze(neutral_text)

        # Verify sentiment direction
        assert pos_sentiment.polarity > 0
        assert neg_sentiment.polarity < 0
        # Neutral should be close to zero
        assert abs(neu_sentiment.polarity) < abs(pos_sentiment.polarity)

    @pytest.mark.asyncio
    async def test_empty_and_edge_cases(self, nlp_pipeline, sentiment_analyzer,
                                       difficulty_scorer):
        """Test handling of edge cases"""
        edge_cases = {
            "empty": "",
            "whitespace": "   \n\t  ",
            "single_word": "Colombia",
            "punctuation": "¿¡!?.,;:",
            "numbers": "123 456 789",
            "very_short": "Hola.",
            "very_long": "palabra " * 1000  # 1000 repetitions
        }

        for case_name, text in edge_cases.items():
            try:
                # Should handle all edge cases gracefully
                if text.strip():  # Only process non-empty texts
                    entities = nlp_pipeline.extract_entities(text)
                    sentiment = sentiment_analyzer.analyze(text)

                    assert isinstance(entities, list)
                    assert hasattr(sentiment, 'polarity')
            except Exception as e:
                pytest.fail(f"Failed on edge case '{case_name}': {str(e)}")

    @pytest.mark.asyncio
    async def test_topic_modeling_coherence(self, topic_modeler, sample_spanish_texts):
        """Test topic modeling produces coherent topics"""
        text = sample_spanish_texts["news_article"]

        topics = topic_modeler.predict_topics(text)

        assert isinstance(topics, list)
        # Topics should have structure
        if topics:
            assert all(isinstance(t, (dict, list)) for t in topics)

    @pytest.mark.asyncio
    async def test_summarization_quality(self, nlp_pipeline, sample_spanish_texts):
        """Test summarization quality metrics"""
        text = sample_spanish_texts["news_article"]

        # Test different summary lengths
        short_summary = nlp_pipeline.summarize(text, max_length=50)
        medium_summary = nlp_pipeline.summarize(text, max_length=100)
        long_summary = nlp_pipeline.summarize(text, max_length=200)

        # Summaries should be progressively longer
        assert len(short_summary) < len(medium_summary)
        assert len(medium_summary) <= len(long_summary)

        # All should be shorter than original
        assert len(short_summary) < len(text)
        assert len(medium_summary) < len(text)
        assert len(long_summary) <= len(text)

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, nlp_pipeline, sample_spanish_texts):
        """Test concurrent text processing"""
        texts = [
            sample_spanish_texts["simple"],
            sample_spanish_texts["intermediate"],
            sample_spanish_texts["advanced"],
            sample_spanish_texts["news_article"]
        ]

        async def process_text(text):
            entities = nlp_pipeline.extract_entities(text)
            summary = nlp_pipeline.summarize(text, max_length=100)
            return {"entities": entities, "summary": summary}

        # Process all texts concurrently
        tasks = [process_text(text) for text in texts]
        results = await asyncio.gather(*tasks)

        assert len(results) == len(texts)
        assert all("entities" in r and "summary" in r for r in results)

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, nlp_pipeline):
        """Test pipeline handles errors gracefully"""
        invalid_inputs = [
            None,
            123,
            [],
            {},
        ]

        for invalid_input in invalid_inputs:
            try:
                # Should either handle gracefully or raise appropriate exception
                if invalid_input is not None:
                    entities = nlp_pipeline.extract_entities(invalid_input)
            except (TypeError, ValueError, AttributeError):
                # Expected exceptions for invalid input
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_pipeline_integration_with_real_data_flow(self, nlp_pipeline, sentiment_analyzer,
                                                       topic_modeler, difficulty_scorer):
        """Test complete data flow from raw text to structured analysis"""
        raw_text = """
            El Ministerio de Hacienda anunció nuevas medidas fiscales para estimular
            la inversión extranjera. Las reformas incluyen incentivos tributarios
            para empresas tecnológicas y reducción de aranceles en importaciones
            de equipos industriales.
        """

        # Simulate complete analysis workflow
        analysis_result = {
            "raw_text": raw_text,
            "timestamp": datetime.now(),
            "processing_steps": []
        }

        # Step 1: Entity extraction
        entities = nlp_pipeline.extract_entities(raw_text)
        analysis_result["entities"] = entities
        analysis_result["processing_steps"].append("entity_extraction")

        # Step 2: Sentiment
        sentiment = sentiment_analyzer.analyze(raw_text)
        analysis_result["sentiment"] = {
            "polarity": sentiment.polarity,
            "subjectivity": sentiment.subjectivity,
            "classification": sentiment.classification
        }
        analysis_result["processing_steps"].append("sentiment_analysis")

        # Step 3: Topics
        topics = topic_modeler.predict_topics(raw_text)
        analysis_result["topics"] = topics
        analysis_result["processing_steps"].append("topic_modeling")

        # Step 4: Difficulty
        difficulty = difficulty_scorer.score(raw_text)
        analysis_result["difficulty"] = {
            "score": difficulty.difficulty_score,
            "level": difficulty.cefr_level,
            "flesch_score": difficulty.flesch_score
        }
        analysis_result["processing_steps"].append("difficulty_scoring")

        # Step 5: Summary
        summary = nlp_pipeline.summarize(raw_text, max_length=100)
        analysis_result["summary"] = summary
        analysis_result["processing_steps"].append("summarization")

        # Verify complete workflow
        assert len(analysis_result["processing_steps"]) == 5
        assert all(key in analysis_result for key in
                  ["entities", "sentiment", "topics", "difficulty", "summary"])
        assert isinstance(analysis_result["timestamp"], datetime)
