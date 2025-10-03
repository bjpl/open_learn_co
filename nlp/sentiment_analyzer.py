"""
Sentiment Analysis Module for Colombian Spanish News Articles

Optimized for analyzing sentiment in Colombian news content with support for
Spanish language nuances and regional expressions.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import re
from textblob import TextBlob
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


@dataclass
class SentimentResult:
    """Structured sentiment analysis result"""
    polarity: float  # -1 (negative) to 1 (positive)
    subjectivity: float  # 0 (objective) to 1 (subjective)
    confidence: float  # 0 to 1
    compound: Optional[float] = None  # VADER compound score if available


class SentimentAnalyzer:
    """
    Advanced sentiment analyzer optimized for Colombian Spanish news articles.

    Combines TextBlob and VADER (when available) for robust sentiment detection
    with special handling for Colombian Spanish expressions and news context.
    """

    # Colombian Spanish intensifiers and modifiers
    COLOMBIAN_INTENSIFIERS = {
        'muy': 1.3, 'mucho': 1.3, 'muchísimo': 1.5, 'super': 1.4,
        'demasiado': 1.4, 'bastante': 1.2, 'bien': 1.2, 're': 1.3,
        'sumamente': 1.5, 'extremadamente': 1.6, 'totalmente': 1.4
    }

    COLOMBIAN_DIMINISHERS = {
        'poco': 0.7, 'apenas': 0.6, 'casi': 0.8, 'medio': 0.75,
        'algo': 0.8, 'un_poco': 0.7, 'ligeramente': 0.7
    }

    # Colombian Spanish negations
    NEGATIONS = {
        'no', 'nunca', 'jamás', 'tampoco', 'ningún', 'ninguno',
        'ninguna', 'nada', 'nadie', 'ni', 'sin'
    }

    # Context-specific sentiment words for Colombian news
    COLOMBIAN_SENTIMENT_LEXICON = {
        # Positive
        'paz': 0.8, 'acuerdo': 0.6, 'desarrollo': 0.7, 'crecimiento': 0.7,
        'inversión': 0.6, 'mejora': 0.7, 'éxito': 0.8, 'progreso': 0.7,
        'victoria': 0.8, 'logro': 0.7, 'avance': 0.6, 'beneficio': 0.6,

        # Negative
        'violencia': -0.8, 'conflicto': -0.7, 'corrupción': -0.9,
        'crisis': -0.8, 'problema': -0.5, 'amenaza': -0.7, 'muerte': -0.9,
        'asesinato': -1.0, 'ataque': -0.8, 'desastre': -0.9,
        'masacre': -1.0, 'secuestro': -0.9, 'narcotráfico': -0.9,

        # Colombian specific
        'farc': -0.3, 'eln': -0.4, 'bacrim': -0.8, 'paro': -0.5,
        'reforma': 0.3, 'diálogo': 0.5, 'reconciliación': 0.8
    }

    def __init__(self, use_vader: bool = True):
        """
        Initialize sentiment analyzer.

        Args:
            use_vader: Whether to use VADER for enhanced analysis (requires vaderSentiment)
        """
        self.use_vader = use_vader and VADER_AVAILABLE
        if self.use_vader:
            self.vader = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of Spanish text with Colombian context awareness.

        Args:
            text: Input text to analyze (Spanish)

        Returns:
            Dictionary with keys:
                - polarity: Sentiment polarity (-1 to 1)
                - subjectivity: Text subjectivity (0 to 1)
                - confidence: Analysis confidence (0 to 1)
        """
        if not text or not text.strip():
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "confidence": 0.0
            }

        # Normalize text
        normalized_text = self._normalize_text(text)

        # Get base sentiment from TextBlob
        blob = TextBlob(normalized_text)
        base_polarity = blob.sentiment.polarity
        base_subjectivity = blob.sentiment.subjectivity

        # Apply Colombian context adjustments
        adjusted_polarity = self._adjust_for_colombian_context(
            normalized_text,
            base_polarity
        )

        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(
            normalized_text,
            base_polarity,
            base_subjectivity
        )

        # Optionally enhance with VADER
        if self.use_vader:
            vader_scores = self.vader.polarity_scores(text)
            # Blend VADER compound with adjusted polarity
            adjusted_polarity = (adjusted_polarity * 0.6 + vader_scores['compound'] * 0.4)
            confidence = min(confidence * 1.1, 1.0)  # Boost confidence slightly

        return {
            "polarity": float(round(adjusted_polarity, 4)),
            "subjectivity": float(round(base_subjectivity, 4)),
            "confidence": float(round(confidence, 4))
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better analysis"""
        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Handle common Colombian contractions
        text = text.replace('pa\'', 'para')
        text = text.replace('q ', 'que ')

        return text.strip()

    def _adjust_for_colombian_context(self, text: str, base_polarity: float) -> float:
        """
        Adjust sentiment based on Colombian Spanish context.

        Handles intensifiers, diminishers, negations, and Colombian-specific terms.
        """
        words = text.split()
        adjustment = 0.0
        multiplier = 1.0

        # Check for Colombian-specific sentiment words
        for word in words:
            if word in self.COLOMBIAN_SENTIMENT_LEXICON:
                adjustment += self.COLOMBIAN_SENTIMENT_LEXICON[word] * 0.3

        # Check for intensifiers and diminishers
        for i, word in enumerate(words):
            # Handle intensifiers
            if word in self.COLOMBIAN_INTENSIFIERS:
                multiplier *= self.COLOMBIAN_INTENSIFIERS[word]

            # Handle diminishers
            if word in self.COLOMBIAN_DIMINISHERS:
                multiplier *= self.COLOMBIAN_DIMINISHERS[word]

            # Handle negations (flip polarity for next 3 words)
            if word in self.NEGATIONS and i < len(words) - 1:
                # Look ahead for sentiment words
                for j in range(i + 1, min(i + 4, len(words))):
                    if words[j] in self.COLOMBIAN_SENTIMENT_LEXICON:
                        adjustment -= self.COLOMBIAN_SENTIMENT_LEXICON[words[j]] * 0.5

        # Apply adjustments
        adjusted = base_polarity * multiplier + adjustment

        # Clamp to valid range
        return max(-1.0, min(1.0, adjusted))

    def _calculate_confidence(
        self,
        text: str,
        polarity: float,
        subjectivity: float
    ) -> float:
        """
        Calculate confidence score based on multiple factors.

        Higher confidence when:
        - Text contains clear sentiment indicators
        - Strong polarity (away from neutral)
        - Contains Colombian context words
        - Sufficient text length
        """
        confidence = 0.5  # Base confidence

        # Length factor (more text = higher confidence)
        word_count = len(text.split())
        if word_count > 50:
            confidence += 0.2
        elif word_count > 20:
            confidence += 0.1
        elif word_count < 5:
            confidence -= 0.2

        # Polarity strength (stronger sentiment = higher confidence)
        polarity_strength = abs(polarity)
        confidence += polarity_strength * 0.2

        # Check for Colombian context words
        words = text.split()
        context_words = sum(1 for word in words if word in self.COLOMBIAN_SENTIMENT_LEXICON)
        if context_words > 0:
            confidence += min(context_words * 0.05, 0.2)

        # Subjectivity factor (very objective or very subjective = higher confidence)
        if subjectivity > 0.7 or subjectivity < 0.3:
            confidence += 0.1

        # Clamp to valid range
        return max(0.0, min(1.0, confidence))

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Analyze multiple texts in batch.

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment dictionaries
        """
        return [self.analyze(text) for text in texts]

    def get_sentiment_label(self, polarity: float) -> str:
        """
        Convert polarity score to human-readable label.

        Args:
            polarity: Polarity score (-1 to 1)

        Returns:
            Sentiment label (positive, negative, neutral)
        """
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"


# Convenience function for quick analysis
def analyze_sentiment(text: str, use_vader: bool = True) -> Dict[str, float]:
    """
    Quick sentiment analysis function.

    Args:
        text: Text to analyze
        use_vader: Whether to use VADER enhancement

    Returns:
        Sentiment analysis results
    """
    analyzer = SentimentAnalyzer(use_vader=use_vader)
    return analyzer.analyze(text)
