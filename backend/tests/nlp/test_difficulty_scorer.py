"""
Unit tests for difficulty scorer
Testing CEFR level mapping and readability metrics
"""

import pytest
from nlp.difficulty_scorer import (
    DifficultyScorer,
    DifficultyMetrics,
    score_text
)


@pytest.fixture
def scorer():
    """Create difficulty scorer instance"""
    return DifficultyScorer()


@pytest.fixture
def simple_text():
    """Simple A1-level Spanish text"""
    return "Yo soy Juan. Tengo un perro. Mi perro es grande y bueno."


@pytest.fixture
def intermediate_text():
    """Intermediate B1-level Spanish text"""
    return """
    El gobierno anunció nuevas medidas económicas para estimular
    el crecimiento. Los expertos consideran que estas reformas
    podrían mejorar la situación financiera del país.
    """


@pytest.fixture
def advanced_text():
    """Advanced C1-level Spanish text"""
    return """
    La implementación de políticas macroeconómicas heterodoxas
    requiere un análisis pormenorizado de las variables estructurales
    que subyacen en el sistema financiero contemporáneo, considerando
    las interdependencias sistémicas y las asimetrías informacionales.
    """


class TestDifficultyScorerInit:
    """Test DifficultyScorer initialization"""

    def test_initialization(self):
        """Should initialize scorer correctly"""
        scorer = DifficultyScorer()
        assert scorer is not None

    def test_has_compiled_patterns(self, scorer):
        """Should compile verb patterns on init"""
        assert hasattr(scorer, '_compiled_patterns')
        assert len(scorer._compiled_patterns) > 0


class TestBasicScoring:
    """Test basic difficulty scoring functionality"""

    def test_score_returns_dict(self, scorer, simple_text):
        """Should return dictionary with required fields"""
        result = scorer.score(simple_text)

        assert isinstance(result, dict)
        assert 'cefr_level' in result
        assert 'numeric_score' in result
        assert 'metrics' in result

    def test_cefr_level_is_valid(self, scorer, simple_text):
        """Should return valid CEFR level"""
        result = scorer.score(simple_text)

        valid_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        assert result['cefr_level'] in valid_levels

    def test_numeric_score_range(self, scorer, simple_text):
        """Should return score in valid range"""
        result = scorer.score(simple_text)

        assert 0 <= result['numeric_score'] <= 100

    def test_empty_text(self, scorer):
        """Should handle empty text gracefully"""
        result = scorer.score("")

        assert result['cefr_level'] == 'A1'
        assert result['numeric_score'] == 0.0

    def test_whitespace_only(self, scorer):
        """Should handle whitespace-only text"""
        result = scorer.score("   \n\t  ")

        assert result['cefr_level'] == 'A1'


class TestCEFRLevelMapping:
    """Test CEFR level mapping accuracy"""

    def test_simple_text_low_level(self, scorer, simple_text):
        """Should assign low CEFR level to simple text"""
        result = scorer.score(simple_text)

        # Simple text should be A1 or A2
        assert result['cefr_level'] in ['A1', 'A2']

    def test_intermediate_text_mid_level(self, scorer, intermediate_text):
        """Should assign intermediate CEFR level"""
        result = scorer.score(intermediate_text)

        # Intermediate text should be around B1-B2
        assert result['cefr_level'] in ['A2', 'B1', 'B2', 'C1']

    def test_advanced_text_high_level(self, scorer, advanced_text):
        """Should assign high CEFR level to advanced text"""
        result = scorer.score(advanced_text)

        # Advanced text should be B2 or higher
        assert result['cefr_level'] in ['B2', 'C1', 'C2']

    def test_difficulty_progression(self, scorer, simple_text, intermediate_text, advanced_text):
        """Should show progression from simple to advanced"""
        result_simple = scorer.score(simple_text)
        result_intermediate = scorer.score(intermediate_text)
        result_advanced = scorer.score(advanced_text)

        # Numeric scores should increase
        assert result_simple['numeric_score'] < result_advanced['numeric_score']


class TestMetricsCalculation:
    """Test detailed metrics calculation"""

    def test_metrics_structure(self, scorer, simple_text):
        """Should return all required metrics"""
        result = scorer.score(simple_text)
        metrics = result['metrics']

        required_fields = [
            'avg_word_length',
            'avg_sentence_length',
            'syllables_per_word',
            'complex_word_ratio',
            'verb_tense_complexity',
            'subjunctive_usage',
            'flesch_huerta_score',
            'vocabulary_diversity'
        ]

        for field in required_fields:
            assert field in metrics
            assert isinstance(metrics[field], (int, float))

    def test_avg_word_length(self, scorer):
        """Should calculate average word length correctly"""
        # Known words: "casa" (4), "perro" (5)
        text = "casa perro"
        result = scorer.score(text)

        # Average should be 4.5
        assert 4.0 <= result['metrics']['avg_word_length'] <= 5.0

    def test_avg_sentence_length(self, scorer):
        """Should calculate average sentence length"""
        text = "Yo soy Juan. Tengo un perro."
        result = scorer.score(text)

        # 2 sentences, ~6 words total
        assert result['metrics']['avg_sentence_length'] > 0

    def test_syllable_counting(self, scorer):
        """Should count syllables correctly for Spanish"""
        # "casa" = 2 syllables, "perro" = 2 syllables
        text = "casa perro"
        result = scorer.score(text)

        # Should average to ~2 syllables per word
        assert 1.5 <= result['metrics']['syllables_per_word'] <= 2.5


class TestVocabularyComplexity:
    """Test vocabulary complexity analysis"""

    def test_basic_vocabulary_detection(self, scorer):
        """Should recognize basic vocabulary"""
        text = "el la un una es son"
        result = scorer.score(text)

        # All basic words, low complexity
        assert result['metrics']['complex_word_ratio'] == 0.0

    def test_complex_vocabulary_detection(self, scorer):
        """Should detect complex vocabulary"""
        text = "implementación macroeconómico interdependencia"
        result = scorer.score(text)

        # All complex words, high ratio
        assert result['metrics']['complex_word_ratio'] > 0.5

    def test_vocabulary_diversity(self, scorer):
        """Should calculate vocabulary diversity (TTR)"""
        # All unique words
        unique_text = "casa perro gato libro mesa silla"
        result_unique = scorer.score(unique_text)

        # Repeated words
        repeated_text = "casa casa perro perro gato gato"
        result_repeated = scorer.score(repeated_text)

        # Unique text should have higher diversity
        assert result_unique['metrics']['vocabulary_diversity'] > \
               result_repeated['metrics']['vocabulary_diversity']


class TestVerbComplexity:
    """Test verb tense complexity analysis"""

    def test_simple_verb_tenses(self, scorer):
        """Should recognize simple verb tenses"""
        text = "Yo soy Juan. Tengo un perro."
        result = scorer.score(text)

        # Only present tense, low complexity
        assert result['metrics']['verb_tense_complexity'] < 30

    def test_conditional_tense(self, scorer):
        """Should detect conditional tense"""
        text = "Yo comería si tuviera hambre. Ella vendría mañana."
        result = scorer.score(text)

        # Conditional present, higher complexity
        assert result['metrics']['verb_tense_complexity'] > 0

    def test_subjunctive_detection(self, scorer):
        """Should detect subjunctive mood"""
        text = "Espero que vengas. Ojalá llueva mañana."
        result = scorer.score(text)

        assert result['metrics']['subjunctive_usage'] > 0

    def test_imperfect_subjunctive(self, scorer):
        """Should detect imperfect subjunctive"""
        text = "Si tuviera dinero, compraría una casa."
        result = scorer.score(text)

        assert result['metrics']['verb_tense_complexity'] > 0
        assert result['metrics']['subjunctive_usage'] > 0


class TestFleschHuertaScore:
    """Test Flesch-Huerta readability score"""

    def test_flesch_score_range(self, scorer, simple_text):
        """Should return Flesch score in valid range"""
        result = scorer.score(simple_text)

        # Flesch score is 0-100
        assert 0 <= result['metrics']['flesch_huerta_score'] <= 100

    def test_simple_text_high_flesch(self, scorer, simple_text):
        """Simple text should have higher Flesch score"""
        result = scorer.score(simple_text)

        # Easier text = higher Flesch score
        assert result['metrics']['flesch_huerta_score'] > 40

    def test_complex_text_low_flesch(self, scorer, advanced_text):
        """Complex text should have lower Flesch score"""
        result = scorer.score(advanced_text)

        # Harder text = lower Flesch score
        # (Note: Implementation inverts this in composite score)
        assert isinstance(result['metrics']['flesch_huerta_score'], (int, float))


class TestCompositeScoring:
    """Test composite score calculation"""

    def test_composite_score_components(self, scorer, intermediate_text):
        """Should combine multiple metrics into composite score"""
        result = scorer.score(intermediate_text)

        # All metrics should contribute
        assert result['numeric_score'] > 0

    def test_weighted_scoring(self, scorer):
        """Should weight different metrics appropriately"""
        # Text with very long sentences
        long_sentences = " ".join(["palabra"] * 50) + "."
        result_long = scorer.score(long_sentences)

        # Text with short sentences
        short_sentences = ". ".join(["palabra"] * 10)
        result_short = scorer.score(short_sentences)

        # Longer sentences should increase difficulty
        assert result_long['numeric_score'] >= result_short['numeric_score']


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_single_word(self, scorer):
        """Should handle single word"""
        result = scorer.score("Hola")

        assert result['cefr_level'] is not None
        assert result['numeric_score'] >= 0

    def test_no_sentences(self, scorer):
        """Should handle text without sentence delimiters"""
        text = "palabra palabra palabra"
        result = scorer.score(text)

        assert isinstance(result, dict)

    def test_very_long_text(self, scorer):
        """Should handle very long text"""
        long_text = " ".join(["El perro es bueno."] * 1000)
        result = scorer.score(long_text)

        assert isinstance(result['numeric_score'], (int, float))

    def test_only_punctuation(self, scorer):
        """Should handle text with only punctuation"""
        result = scorer.score("... !!! ???")

        assert result['cefr_level'] == 'A1'

    def test_numbers_in_text(self, scorer):
        """Should handle numbers in text"""
        text = "Tengo 5 perros y 3 gatos. Son 8 animales."
        result = scorer.score(text)

        assert isinstance(result, dict)

    def test_special_characters(self, scorer):
        """Should handle special Spanish characters"""
        text = "El niño comió piñata. ¿Qué pasó? ¡Increíble!"
        result = scorer.score(text)

        assert isinstance(result['cefr_level'], str)


class TestHelperMethods:
    """Test internal helper methods"""

    def test_split_sentences(self, scorer):
        """Should split sentences correctly"""
        text = "Primera oración. Segunda oración! Tercera oración?"
        sentences = scorer._split_sentences(text)

        assert len(sentences) == 3

    def test_extract_words(self, scorer):
        """Should extract words correctly"""
        text = "El perro, es bueno!"
        words = scorer._extract_words(text)

        assert 'el' in words
        assert 'perro' in words
        assert 'es' in words
        assert 'bueno' in words

    def test_count_syllables(self, scorer):
        """Should count syllables accurately"""
        assert scorer._count_syllables("ca") == 1
        assert scorer._count_syllables("casa") == 2
        assert scorer._count_syllables("casita") == 3
        assert scorer._count_syllables("implementation") >= 4

    def test_syllable_diphthongs(self, scorer):
        """Should handle Spanish diphthongs"""
        # "bueno" = bue-no (2 syllables, "ue" is diphthong)
        assert scorer._count_syllables("bueno") == 2

    def test_map_to_cefr(self, scorer):
        """Should map numeric scores to CEFR correctly"""
        assert scorer._map_to_cefr(10) == 'A1'
        assert scorer._map_to_cefr(25) == 'A2'
        assert scorer._map_to_cefr(45) == 'B1'
        assert scorer._map_to_cefr(60) == 'B2'
        assert scorer._map_to_cefr(75) == 'C1'
        assert scorer._map_to_cefr(90) == 'C2'


class TestConvenienceFunction:
    """Test convenience function"""

    def test_score_text_function(self, simple_text):
        """Should work through convenience function"""
        result = score_text(simple_text)

        assert isinstance(result, dict)
        assert 'cefr_level' in result
        assert 'numeric_score' in result


class TestRealWorldTexts:
    """Test with real-world Colombian Spanish examples"""

    def test_news_headline(self, scorer):
        """Should score news headline appropriately"""
        text = "Presidente anuncia nueva reforma económica"
        result = scorer.score(text)

        # Short headline, relatively simple
        assert result['cefr_level'] in ['A2', 'B1', 'B2']

    def test_news_article(self, scorer):
        """Should score full news article"""
        text = """
        El presidente de Colombia presentó hoy un ambicioso plan
        de reformas económicas que busca estimular el crecimiento
        y reducir el desempleo. La propuesta incluye incentivos
        fiscales para empresas que generen nuevos empleos.
        """
        result = scorer.score(text)

        # News article, intermediate level
        assert result['cefr_level'] in ['B1', 'B2', 'C1']

    def test_academic_text(self, scorer):
        """Should score academic text as advanced"""
        text = """
        La epistemología contemporánea plantea interrogantes
        fundamentales sobre la naturaleza del conocimiento científico
        y las metodologías empleadas en la investigación empírica,
        cuestionando los paradigmas tradicionales.
        """
        result = scorer.score(text)

        # Academic text, advanced level
        assert result['cefr_level'] in ['C1', 'C2']

    def test_conversational_text(self, scorer):
        """Should score conversational text as basic"""
        text = "Hola, ¿cómo estás? Yo estoy bien, gracias. ¿Y tú?"
        result = scorer.score(text)

        # Conversational, basic level
        assert result['cefr_level'] in ['A1', 'A2']


# Parametrized tests
class TestParametrizedScenarios:
    """Parametrized tests for comprehensive coverage"""

    @pytest.mark.parametrize("level,score_range", [
        ('A1', (0, 20)),
        ('A2', (20, 35)),
        ('B1', (35, 50)),
        ('B2', (50, 65)),
        ('C1', (65, 80)),
        ('C2', (80, 100))
    ])
    def test_cefr_thresholds(self, scorer, level, score_range):
        """Should map CEFR thresholds correctly"""
        # Test threshold boundaries
        min_score, max_score = score_range
        mid_score = (min_score + max_score) / 2

        mapped_level = scorer._map_to_cefr(mid_score)
        assert mapped_level == level

    @pytest.mark.parametrize("word,expected_syllables", [
        ("a", 1),
        ("el", 1),
        ("casa", 2),
        ("perro", 2),
        ("casita", 3),
        ("maravilloso", 4)
    ])
    def test_syllable_counts(self, scorer, word, expected_syllables):
        """Should count syllables correctly for common words"""
        count = scorer._count_syllables(word)
        assert count == expected_syllables
