"""
Spanish Text Difficulty Scorer for Language Learning
Maps text complexity to CEFR levels (A1-C2) using readability metrics adapted for Spanish.
"""

import re
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class DifficultyMetrics:
    """Detailed metrics for text difficulty analysis"""
    avg_word_length: float
    avg_sentence_length: float
    syllables_per_word: float
    complex_word_ratio: float
    verb_tense_complexity: float
    subjunctive_usage: float
    flesch_huerta_score: float
    vocabulary_diversity: float


class DifficultyScorer:
    """
    Analyzes Spanish text difficulty and maps to CEFR levels.

    Uses multiple linguistic metrics:
    - Flesch-Huerta readability (Spanish adaptation)
    - Vocabulary complexity and diversity
    - Sentence structure complexity
    - Grammatical feature complexity (verb tenses, subjunctive)
    """

    # CEFR level thresholds based on composite score (0-100 scale)
    CEFR_THRESHOLDS = {
        'A1': (0, 20),
        'A2': (20, 35),
        'B1': (35, 50),
        'B2': (50, 65),
        'C1': (65, 80),
        'C2': (80, 100)
    }

    # Complex Spanish verb forms indicating advanced proficiency
    COMPLEX_VERB_PATTERNS = [
        r'\w+ría\b',  # Conditional
        r'\w+rías\b',
        r'\w+se\b',   # Subjunctive
        r'\w+ses\b',
        r'\w+ra\b',   # Imperfect subjunctive
        r'\w+ras\b',
        r'\w+ría\b',
        r'hubiera\b', # Compound subjunctive
        r'hubiese\b',
        r'habría\b'   # Conditional perfect
    ]

    # Common words at A1/A2 level (sample - production would use full list)
    BASIC_VOCABULARY = {
        'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', 'de', 'a', 'en',
        'por', 'para', 'con', 'sin', 'es', 'son', 'está', 'están', 'hay',
        'ser', 'estar', 'tener', 'hacer', 'ir', 'ver', 'dar', 'decir', 'poder',
        'hombre', 'mujer', 'niño', 'niña', 'casa', 'día', 'año', 'tiempo', 'vez',
        'bueno', 'malo', 'grande', 'pequeño', 'nuevo', 'viejo', 'primero', 'último',
        'todo', 'otro', 'mismo', 'tanto', 'mucho', 'poco', 'muy', 'más', 'menos',
        'qué', 'quién', 'cuándo', 'dónde', 'cómo', 'cuál', 'cuánto'
    }

    def __init__(self):
        """Initialize the difficulty scorer"""
        self._compiled_patterns = [re.compile(p, re.IGNORECASE)
                                   for p in self.COMPLEX_VERB_PATTERNS]

    def score(self, text: str) -> Dict:
        """
        Analyze text difficulty and return comprehensive scoring.

        Args:
            text: Spanish text to analyze

        Returns:
            Dictionary with:
                - cefr_level: str (A1, A2, B1, B2, C1, C2)
                - numeric_score: float (0-100)
                - metrics: dict with detailed analysis
        """
        if not text or not text.strip():
            return {
                'cefr_level': 'A1',
                'numeric_score': 0.0,
                'metrics': {}
            }

        # Calculate all metrics
        metrics = self._calculate_metrics(text)

        # Compute composite score
        numeric_score = self._compute_composite_score(metrics)

        # Map to CEFR level
        cefr_level = self._map_to_cefr(numeric_score)

        return {
            'cefr_level': cefr_level,
            'numeric_score': round(numeric_score, 2),
            'metrics': {
                'avg_word_length': round(metrics.avg_word_length, 2),
                'avg_sentence_length': round(metrics.avg_sentence_length, 2),
                'syllables_per_word': round(metrics.syllables_per_word, 2),
                'complex_word_ratio': round(metrics.complex_word_ratio, 2),
                'verb_tense_complexity': round(metrics.verb_tense_complexity, 2),
                'subjunctive_usage': round(metrics.subjunctive_usage, 2),
                'flesch_huerta_score': round(metrics.flesch_huerta_score, 2),
                'vocabulary_diversity': round(metrics.vocabulary_diversity, 2)
            }
        }

    def _calculate_metrics(self, text: str) -> DifficultyMetrics:
        """Calculate all linguistic metrics for the text"""
        # Tokenize
        sentences = self._split_sentences(text)
        words = self._extract_words(text)

        if not words:
            return DifficultyMetrics(0, 0, 0, 0, 0, 0, 100, 0)

        # Basic metrics
        total_words = len(words)
        total_sentences = max(len(sentences), 1)
        avg_sentence_length = total_words / total_sentences
        avg_word_length = sum(len(w) for w in words) / total_words

        # Syllable counting
        total_syllables = sum(self._count_syllables(w) for w in words)
        syllables_per_word = total_syllables / total_words

        # Vocabulary complexity
        complex_words = sum(1 for w in words
                           if w.lower() not in self.BASIC_VOCABULARY and len(w) > 6)
        complex_word_ratio = complex_words / total_words

        # Vocabulary diversity (Type-Token Ratio)
        unique_words = len(set(w.lower() for w in words))
        vocabulary_diversity = unique_words / total_words if total_words > 0 else 0

        # Grammatical complexity
        verb_complexity = self._analyze_verb_complexity(text, total_words)
        subjunctive_usage = self._detect_subjunctive(text, total_words)

        # Flesch-Huerta readability (Spanish adaptation)
        flesch_huerta = self._calculate_flesch_huerta(
            total_sentences, total_words, total_syllables
        )

        return DifficultyMetrics(
            avg_word_length=avg_word_length,
            avg_sentence_length=avg_sentence_length,
            syllables_per_word=syllables_per_word,
            complex_word_ratio=complex_word_ratio,
            verb_tense_complexity=verb_complexity,
            subjunctive_usage=subjunctive_usage,
            flesch_huerta_score=flesch_huerta,
            vocabulary_diversity=vocabulary_diversity
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text"""
        # Remove punctuation and split on whitespace
        words = re.findall(r'\b[a-záéíóúñü]+\b', text.lower())
        return words

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in Spanish word.
        Spanish syllables are based on vowel sounds.
        """
        word = word.lower()
        vowels = 'aeiouáéíóúü'

        # Count vowel groups (diphthongs count as one syllable)
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Minimum one syllable per word
        return max(syllable_count, 1)

    def _calculate_flesch_huerta(self, sentences: int, words: int,
                                 syllables: int) -> float:
        """
        Calculate Flesch-Huerta readability score (Spanish adaptation).
        Score ranges from 0-100 (higher = easier to read)
        """
        if sentences == 0 or words == 0:
            return 0.0

        # Flesch-Huerta formula for Spanish
        score = 206.84 - (60 * (syllables / words)) - (1.02 * (words / sentences))

        # Clamp to 0-100 range
        return max(0, min(100, score))

    def _analyze_verb_complexity(self, text: str, total_words: int) -> float:
        """
        Analyze verb tense complexity.
        Returns ratio of complex verb forms (0-1 scale, normalized to 0-100)
        """
        if total_words == 0:
            return 0.0

        complex_verbs = 0
        for pattern in self._compiled_patterns:
            complex_verbs += len(pattern.findall(text))

        # Normalize to 0-100 scale
        ratio = complex_verbs / total_words
        return min(ratio * 100, 100)

    def _detect_subjunctive(self, text: str, total_words: int) -> float:
        """
        Detect subjunctive mood usage.
        Returns normalized score (0-100)
        """
        if total_words == 0:
            return 0.0

        # Subjunctive indicators
        subjunctive_triggers = [
            r'\bque\s+\w+[ae]\b',  # que + subjunctive
            r'\bsi\s+\w+ra\b',     # si + imperfect subjunctive
            r'\bquizás?\b',        # quizá(s)
            r'\btal vez\b',        # tal vez
            r'\bojalá\b',          # ojalá
            r'\baunque\b'          # aunque
        ]

        count = 0
        for pattern_str in subjunctive_triggers:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            count += len(pattern.findall(text))

        # Normalize to 0-100 scale
        ratio = count / total_words
        return min(ratio * 100, 100)

    def _compute_composite_score(self, metrics: DifficultyMetrics) -> float:
        """
        Compute composite difficulty score from all metrics.
        Returns score on 0-100 scale (higher = more difficult)
        """
        # Invert Flesch-Huerta (higher Flesch = easier, we want higher = harder)
        inverted_flesch = 100 - metrics.flesch_huerta_score

        # Weighted composite score
        weights = {
            'flesch': 0.25,
            'sentence_length': 0.15,
            'word_length': 0.10,
            'syllables': 0.10,
            'complex_words': 0.15,
            'verb_complexity': 0.12,
            'subjunctive': 0.08,
            'vocabulary_diversity': 0.05
        }

        # Normalize each metric to 0-100 scale
        sentence_score = min(metrics.avg_sentence_length * 3, 100)
        word_score = min(metrics.avg_word_length * 12, 100)
        syllable_score = min(metrics.syllables_per_word * 30, 100)
        complex_word_score = metrics.complex_word_ratio * 100
        vocab_diversity_score = metrics.vocabulary_diversity * 100

        composite = (
            inverted_flesch * weights['flesch'] +
            sentence_score * weights['sentence_length'] +
            word_score * weights['word_length'] +
            syllable_score * weights['syllables'] +
            complex_word_score * weights['complex_words'] +
            metrics.verb_tense_complexity * weights['verb_complexity'] +
            metrics.subjunctive_usage * weights['subjunctive'] +
            vocab_diversity_score * weights['vocabulary_diversity']
        )

        return max(0, min(100, composite))

    def _map_to_cefr(self, score: float) -> str:
        """Map numeric score to CEFR level"""
        for level, (min_score, max_score) in self.CEFR_THRESHOLDS.items():
            if min_score <= score < max_score:
                return level
        return 'C2'  # Default to highest level if score >= 80


# Singleton instance for easy import
scorer = DifficultyScorer()


def score_text(text: str) -> Dict:
    """
    Convenience function to score text difficulty.

    Args:
        text: Spanish text to analyze

    Returns:
        Dictionary with cefr_level, numeric_score, and detailed metrics
    """
    return scorer.score(text)
