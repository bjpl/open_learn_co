"""
Unit tests for NLP sentiment analyzer
Testing sentiment analysis with Colombian Spanish context
"""

import pytest
from unittest.mock import Mock, patch

from nlp.sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentResult,
    analyze_sentiment
)


@pytest.fixture
def analyzer():
    """Create sentiment analyzer instance"""
    return SentimentAnalyzer(use_vader=False)


@pytest.fixture
def analyzer_with_vader():
    """Create sentiment analyzer with VADER enabled"""
    return SentimentAnalyzer(use_vader=True)


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer class"""

    def test_initialization(self):
        """Should initialize analyzer correctly"""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None

    def test_initialization_without_vader(self):
        """Should work without VADER dependency"""
        analyzer = SentimentAnalyzer(use_vader=False)
        assert analyzer.use_vader is False


class TestBasicSentimentAnalysis:
    """Test basic sentiment analysis functionality"""

    def test_positive_sentiment(self, analyzer):
        """Should detect positive sentiment"""
        text = "Este es un día maravilloso. Estoy muy feliz con los resultados."

        result = analyzer.analyze(text)

        assert isinstance(result, dict)
        assert "polarity" in result
        assert "subjectivity" in result
        assert "confidence" in result
        assert result["polarity"] > 0  # Positive

    def test_negative_sentiment(self, analyzer):
        """Should detect negative sentiment"""
        text = "Esta situación es terrible. Me siento muy triste y preocupado."

        result = analyzer.analyze(text)

        assert result["polarity"] < 0  # Negative

    def test_neutral_sentiment(self, analyzer):
        """Should detect neutral sentiment"""
        text = "El edificio está ubicado en la calle 50. Tiene 10 pisos."

        result = analyzer.analyze(text)

        assert -0.2 <= result["polarity"] <= 0.2  # Approximately neutral

    def test_empty_text(self, analyzer):
        """Should handle empty text gracefully"""
        result = analyzer.analyze("")

        assert result["polarity"] == 0.0
        assert result["subjectivity"] == 0.0
        assert result["confidence"] == 0.0

    def test_whitespace_only(self, analyzer):
        """Should handle whitespace-only text"""
        result = analyzer.analyze("   \n\t  ")

        assert result["polarity"] == 0.0

    def test_very_short_text(self, analyzer):
        """Should handle very short text"""
        result = analyzer.analyze("Bien")

        assert isinstance(result["polarity"], float)
        assert isinstance(result["confidence"], float)


class TestColombianContext:
    """Test Colombian Spanish context awareness"""

    def test_colombian_sentiment_words(self, analyzer):
        """Should recognize Colombian-specific sentiment words"""
        positive_text = "Hay paz y desarrollo en el país. Gran logro."
        result_positive = analyzer.analyze(positive_text)

        negative_text = "Violencia y corrupción amenazan la región."
        result_negative = analyzer.analyze(negative_text)

        assert result_positive["polarity"] > result_negative["polarity"]

    def test_colombian_intensifiers(self, analyzer):
        """Should apply Colombian intensifiers correctly"""
        text_basic = "Esto es bueno."
        text_intensified = "Esto es muy bueno."

        result_basic = analyzer.analyze(text_basic)
        result_intensified = analyzer.analyze(text_intensified)

        # Intensified should have stronger polarity
        assert abs(result_intensified["polarity"]) >= abs(result_basic["polarity"])

    def test_colombian_diminishers(self, analyzer):
        """Should apply Colombian diminishers correctly"""
        text_strong = "Es muy malo."
        text_diminished = "Es poco malo."

        result_strong = analyzer.analyze(text_strong)
        result_diminished = analyzer.analyze(text_diminished)

        # Diminished should have weaker polarity
        assert abs(result_diminished["polarity"]) <= abs(result_strong["polarity"])

    def test_negation_handling(self, analyzer):
        """Should handle Spanish negations"""
        text_positive = "Es bueno."
        text_negated = "No es bueno."

        result_positive = analyzer.analyze(text_positive)
        result_negated = analyzer.analyze(text_negated)

        # Negation should flip or reduce polarity
        assert result_negated["polarity"] < result_positive["polarity"]

    def test_specific_colombian_terms(self, analyzer):
        """Should recognize specific Colombian context terms"""
        # FARC reference (negative connotation)
        text_farc = "El grupo FARC causó problemas."
        result_farc = analyzer.analyze(text_farc)

        # Peace agreement (positive connotation)
        text_peace = "Se firmó el acuerdo de paz."
        result_peace = analyzer.analyze(text_peace)

        assert result_peace["polarity"] > result_farc["polarity"]


class TestTextNormalization:
    """Test text normalization functionality"""

    def test_url_removal(self, analyzer):
        """Should remove URLs from text"""
        text = "Visita https://example.com para más info. Es genial."
        result = analyzer.analyze(text)

        # Should still analyze sentiment without URL
        assert isinstance(result["polarity"], float)

    def test_lowercase_conversion(self, analyzer):
        """Should normalize case"""
        text_upper = "ESTO ES MARAVILLOSO"
        text_lower = "esto es maravilloso"

        result_upper = analyzer.analyze(text_upper)
        result_lower = analyzer.analyze(text_lower)

        # Should produce similar results
        assert abs(result_upper["polarity"] - result_lower["polarity"]) < 0.1

    def test_whitespace_normalization(self, analyzer):
        """Should normalize excessive whitespace"""
        text = "Esto    es     muy      bueno"
        result = analyzer.analyze(text)

        assert isinstance(result["polarity"], float)

    def test_colombian_contractions(self, analyzer):
        """Should handle Colombian contractions"""
        text = "Es pa' mañana, q bueno."
        result = analyzer.analyze(text)

        # Should process without errors
        assert isinstance(result, dict)


class TestConfidenceCalculation:
    """Test confidence score calculation"""

    def test_long_text_higher_confidence(self, analyzer):
        """Should have higher confidence for longer texts"""
        short_text = "Bueno."
        long_text = " ".join(["Es muy bueno"] * 20)

        result_short = analyzer.analyze(short_text)
        result_long = analyzer.analyze(long_text)

        assert result_long["confidence"] >= result_short["confidence"]

    def test_strong_polarity_higher_confidence(self, analyzer):
        """Should have higher confidence for strong polarity"""
        neutral_text = "El edificio tiene ventanas."
        strong_text = "¡Es absolutamente maravilloso! ¡Extraordinario!"

        result_neutral = analyzer.analyze(neutral_text)
        result_strong = analyzer.analyze(strong_text)

        assert result_strong["confidence"] > result_neutral["confidence"]

    def test_colombian_words_boost_confidence(self, analyzer):
        """Should boost confidence when Colombian context words present"""
        generic_text = "Es una situación difícil."
        colombian_text = "La violencia y corrupción son problemas graves."

        result_generic = analyzer.analyze(generic_text)
        result_colombian = analyzer.analyze(colombian_text)

        # Colombian context should boost confidence
        assert result_colombian["confidence"] >= result_generic["confidence"]


class TestVaderIntegration:
    """Test VADER integration when available"""

    @pytest.mark.skipif(
        not SentimentAnalyzer(use_vader=True).use_vader,
        reason="VADER not available"
    )
    def test_vader_enhancement(self, analyzer_with_vader):
        """Should enhance analysis with VADER when available"""
        text = "This is amazing news! Very positive development."

        result = analyzer_with_vader.analyze(text)

        assert isinstance(result["polarity"], float)
        assert "confidence" in result

    def test_vader_unavailable_fallback(self):
        """Should fall back gracefully when VADER unavailable"""
        with patch('nlp.sentiment_analyzer.VADER_AVAILABLE', False):
            analyzer = SentimentAnalyzer(use_vader=True)
            assert analyzer.use_vader is False


class TestBatchAnalysis:
    """Test batch analysis functionality"""

    def test_analyze_batch(self, analyzer):
        """Should analyze multiple texts in batch"""
        texts = [
            "Esto es excelente.",
            "Esto es terrible.",
            "Esto es normal."
        ]

        results = analyzer.analyze_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)
        assert all("polarity" in r for r in results)

    def test_batch_preserves_order(self, analyzer):
        """Should preserve order in batch analysis"""
        texts = ["Positivo", "Negativo", "Neutral"]
        results = analyzer.analyze_batch(texts)

        # First should be positive, second negative
        assert results[0]["polarity"] > results[1]["polarity"]

    def test_empty_batch(self, analyzer):
        """Should handle empty batch"""
        results = analyzer.analyze_batch([])
        assert results == []


class TestSentimentLabel:
    """Test sentiment label generation"""

    def test_positive_label(self, analyzer):
        """Should return 'positive' for positive polarity"""
        label = analyzer.get_sentiment_label(0.5)
        assert label == "positive"

    def test_negative_label(self, analyzer):
        """Should return 'negative' for negative polarity"""
        label = analyzer.get_sentiment_label(-0.5)
        assert label == "negative"

    def test_neutral_label(self, analyzer):
        """Should return 'neutral' for near-zero polarity"""
        label = analyzer.get_sentiment_label(0.05)
        assert label == "neutral"

        label = analyzer.get_sentiment_label(-0.05)
        assert label == "neutral"

    def test_boundary_values(self, analyzer):
        """Should handle boundary values correctly"""
        assert analyzer.get_sentiment_label(0.1) == "neutral"
        assert analyzer.get_sentiment_label(0.11) == "positive"
        assert analyzer.get_sentiment_label(-0.1) == "neutral"
        assert analyzer.get_sentiment_label(-0.11) == "negative"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_none_input(self, analyzer):
        """Should handle None input"""
        result = analyzer.analyze(None)
        assert result["polarity"] == 0.0

    def test_numeric_string(self, analyzer):
        """Should handle numeric strings"""
        result = analyzer.analyze("123 456 789")
        assert isinstance(result, dict)

    def test_special_characters(self, analyzer):
        """Should handle special characters"""
        text = "¡¡¡Increíble!!! @#$% ¿Verdad?"
        result = analyzer.analyze(text)
        assert isinstance(result["polarity"], float)

    def test_mixed_language(self, analyzer):
        """Should handle mixed Spanish-English"""
        text = "Es very bueno and excellent."
        result = analyzer.analyze(text)
        assert isinstance(result, dict)

    def test_emojis_and_unicode(self, analyzer):
        """Should handle emojis and unicode characters"""
        text = "Es genial 😊 muy feliz 🎉"
        result = analyzer.analyze(text)
        assert isinstance(result, dict)

    def test_very_long_text(self, analyzer):
        """Should handle very long text"""
        long_text = " ".join(["Es bueno."] * 1000)
        result = analyzer.analyze(long_text)

        assert isinstance(result, dict)
        assert result["confidence"] > 0


class TestConvenienceFunction:
    """Test convenience function"""

    def test_analyze_sentiment_function(self):
        """Should work through convenience function"""
        result = analyze_sentiment("Es maravilloso", use_vader=False)

        assert isinstance(result, dict)
        assert "polarity" in result
        assert result["polarity"] > 0


class TestRealWorldScenarios:
    """Test real-world Colombian news scenarios"""

    def test_political_news(self, analyzer):
        """Should analyze political news correctly"""
        text = """
        El presidente anunció una nueva reforma que busca mejorar
        la situación económica del país. Los expertos consideran
        que esta medida tendrá un impacto positivo.
        """

        result = analyzer.analyze(text)

        assert result["polarity"] > 0  # Positive news
        assert result["subjectivity"] > 0.3  # Somewhat subjective

    def test_crime_news(self, analyzer):
        """Should analyze crime news correctly"""
        text = """
        Una terrible masacre ocurrió en la región. Las autoridades
        reportan múltiples víctimas. La violencia continúa siendo
        un grave problema.
        """

        result = analyzer.analyze(text)

        assert result["polarity"] < 0  # Negative news
        assert result["confidence"] > 0.5

    def test_economic_news(self, analyzer):
        """Should analyze economic news"""
        text = """
        El crecimiento económico alcanzó el 3.5% este trimestre.
        La inversión extranjera aumentó significativamente, generando
        nuevos empleos y oportunidades de desarrollo.
        """

        result = analyzer.analyze(text)

        assert result["polarity"] > 0.3  # Positive economic news

    def test_neutral_reporting(self, analyzer):
        """Should recognize neutral factual reporting"""
        text = """
        El evento se realizará el próximo martes a las 10:00 AM
        en el centro de convenciones. Se esperan 500 asistentes.
        """

        result = analyzer.analyze(text)

        assert abs(result["polarity"]) < 0.3  # Mostly neutral
        assert result["subjectivity"] < 0.5  # Objective


# Parametrized tests for comprehensive coverage
class TestParametrizedScenarios:
    """Parametrized tests for various scenarios"""

    @pytest.mark.parametrize("text,expected_polarity_sign", [
        ("Es excelente y maravilloso", 1),  # Positive
        ("Es terrible y horrible", -1),  # Negative
        ("Es normal", 0),  # Neutral
        ("Me encanta este proyecto", 1),  # Positive
        ("Odio esta situación", -1),  # Negative
    ])
    def test_polarity_signs(self, analyzer, text, expected_polarity_sign):
        """Should correctly identify polarity sign"""
        result = analyzer.analyze(text)

        if expected_polarity_sign > 0:
            assert result["polarity"] > 0.1
        elif expected_polarity_sign < 0:
            assert result["polarity"] < -0.1
        else:
            assert abs(result["polarity"]) <= 0.3

    @pytest.mark.parametrize("intensifier", [
        "muy", "mucho", "super", "bastante", "extremadamente"
    ])
    def test_all_intensifiers(self, analyzer, intensifier):
        """Should handle all Colombian intensifiers"""
        text = f"Es {intensifier} bueno"
        result = analyzer.analyze(text)

        # Should be positive and stronger than baseline
        assert result["polarity"] > 0.2
