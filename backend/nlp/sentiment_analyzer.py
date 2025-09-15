"""
Sentiment Analysis for Colombian Content
Specialized for political and economic sentiment
"""

from typing import Dict, List, Optional
from spacy.tokens import Doc
import logging
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis tailored for Colombian news and political content
    """

    def __init__(self):
        self._initialize_lexicons()

    def _initialize_lexicons(self):
        """Initialize sentiment lexicons for Colombian context"""

        # Political sentiment indicators
        self.political_positive = [
            'paz', 'acuerdo', 'progreso', 'desarrollo', 'inversión',
            'crecimiento', 'estabilidad', 'democracia', 'transparencia',
            'justicia', 'reconciliación', 'diálogo', 'reforma', 'mejora'
        ]

        self.political_negative = [
            'corrupción', 'violencia', 'conflicto', 'crisis', 'escándalo',
            'asesinato', 'secuestro', 'amenaza', 'atentado', 'masacre',
            'desplazamiento', 'paramilitares', 'guerrilla', 'narcotráfico',
            'impunidad', 'desempleo', 'pobreza', 'desigualdad'
        ]

        # Economic sentiment indicators
        self.economic_positive = [
            'crecimiento', 'inversión', 'empleo', 'exportación', 'superávit',
            'recuperación', 'alza', 'ganancia', 'rentabilidad', 'expansión',
            'bonanza', 'prosperidad', 'competitividad'
        ]

        self.economic_negative = [
            'inflación', 'recesión', 'déficit', 'devaluación', 'crisis',
            'caída', 'pérdida', 'quiebra', 'desempleo', 'endeudamiento',
            'default', 'burbuja', 'colapso', 'estancamiento'
        ]

        # Conflict-related terms (usually negative)
        self.conflict_terms = [
            'enfrentamiento', 'combate', 'ataque', 'bomba', 'explosión',
            'tiroteo', 'emboscada', 'hostigamiento', 'extorsión', 'vacuna',
            'desaparición', 'fosa común', 'mina antipersonal'
        ]

        # Hope/positive future indicators
        self.hope_indicators = [
            'esperanza', 'futuro', 'solución', 'oportunidad', 'cambio positivo',
            'nueva era', 'transformación', 'renovación', 'optimismo'
        ]

    def analyze(self, doc: Doc, original_text: str = None) -> Dict[str, float]:
        """
        Analyze sentiment of text

        Args:
            doc: spaCy document
            original_text: Original text before preprocessing

        Returns:
            Dictionary with sentiment scores
        """
        text = original_text if original_text else doc.text

        # Get base sentiment using TextBlob
        base_sentiment = self._get_base_sentiment(text)

        # Get domain-specific sentiment
        political_sentiment = self._analyze_political_sentiment(text)
        economic_sentiment = self._analyze_economic_sentiment(text)
        conflict_sentiment = self._analyze_conflict_sentiment(text)

        # Combine sentiments with weights
        overall_sentiment = self._calculate_overall_sentiment(
            base_sentiment,
            political_sentiment,
            economic_sentiment,
            conflict_sentiment
        )

        return {
            'overall': overall_sentiment,
            'polarity': base_sentiment['polarity'],
            'subjectivity': base_sentiment['subjectivity'],
            'political': political_sentiment,
            'economic': economic_sentiment,
            'conflict': conflict_sentiment,
            'confidence': self._calculate_confidence(text)
        }

    def _get_base_sentiment(self, text: str) -> Dict[str, float]:
        """Get base sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity  # 0 to 1
            }
        except:
            return {'polarity': 0.0, 'subjectivity': 0.5}

    def _analyze_political_sentiment(self, text: str) -> float:
        """Analyze political sentiment"""
        text_lower = text.lower()

        positive_score = sum(1 for term in self.political_positive if term in text_lower)
        negative_score = sum(1 for term in self.political_negative if term in text_lower)

        if positive_score + negative_score == 0:
            return 0.0

        # Calculate normalized score (-1 to 1)
        sentiment = (positive_score - negative_score) / (positive_score + negative_score)
        return sentiment

    def _analyze_economic_sentiment(self, text: str) -> float:
        """Analyze economic sentiment"""
        text_lower = text.lower()

        positive_score = sum(1 for term in self.economic_positive if term in text_lower)
        negative_score = sum(1 for term in self.economic_negative if term in text_lower)

        if positive_score + negative_score == 0:
            return 0.0

        sentiment = (positive_score - negative_score) / (positive_score + negative_score)
        return sentiment

    def _analyze_conflict_sentiment(self, text: str) -> float:
        """Analyze conflict-related sentiment (usually negative)"""
        text_lower = text.lower()

        conflict_score = sum(1 for term in self.conflict_terms if term in text_lower)
        hope_score = sum(1 for term in self.hope_indicators if term in text_lower)

        if conflict_score + hope_score == 0:
            return 0.0

        # Conflict terms are negative, hope terms are positive
        sentiment = (hope_score - conflict_score) / (conflict_score + hope_score)
        return sentiment

    def _calculate_overall_sentiment(self, base: Dict, political: float,
                                    economic: float, conflict: float) -> float:
        """Calculate weighted overall sentiment"""

        # Weights for different components
        weights = {
            'base': 0.3,
            'political': 0.3,
            'economic': 0.2,
            'conflict': 0.2
        }

        overall = (
            weights['base'] * base['polarity'] +
            weights['political'] * political +
            weights['economic'] * economic +
            weights['conflict'] * conflict
        )

        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, overall))

    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence in sentiment analysis"""

        # Factors affecting confidence
        word_count = len(text.split())
        if word_count < 20:
            return 0.3  # Low confidence for very short texts
        elif word_count < 50:
            return 0.5
        elif word_count < 200:
            return 0.7
        else:
            return 0.9

    def get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score <= -0.5:
            return 'very_negative'
        elif score <= -0.1:
            return 'negative'
        elif score < 0.1:
            return 'neutral'
        elif score < 0.5:
            return 'positive'
        else:
            return 'very_positive'

    def analyze_trends(self, sentiments: List[Dict], time_window: str = 'daily') -> Dict:
        """
        Analyze sentiment trends over time

        Args:
            sentiments: List of sentiment results with timestamps
            time_window: Aggregation window (daily, weekly, monthly)

        Returns:
            Trend analysis results
        """
        if not sentiments:
            return {}

        # Calculate moving average
        scores = [s['overall'] for s in sentiments]
        avg_sentiment = sum(scores) / len(scores)

        # Detect trend direction
        if len(scores) >= 2:
            recent_avg = sum(scores[-5:]) / min(5, len(scores))
            older_avg = sum(scores[:-5]) / max(1, len(scores) - 5)
            trend = 'improving' if recent_avg > older_avg else 'declining'
        else:
            trend = 'stable'

        return {
            'average_sentiment': avg_sentiment,
            'trend': trend,
            'volatility': self._calculate_volatility(scores),
            'sentiment_distribution': self._get_distribution(scores)
        }

    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate sentiment volatility"""
        if len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance ** 0.5

    def _get_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Get distribution of sentiment labels"""
        distribution = {
            'very_negative': 0,
            'negative': 0,
            'neutral': 0,
            'positive': 0,
            'very_positive': 0
        }

        for score in scores:
            label = self.get_sentiment_label(score)
            distribution[label] += 1

        return distribution