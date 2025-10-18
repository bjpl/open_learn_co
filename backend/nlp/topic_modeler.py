"""
Topic Modeling Module for Colombian News Intelligence
Analyzes text to extract relevant topics with confidence scores
"""

import numpy as np
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
import re
import unicodedata


class TopicModeler:
    """
    Topic modeling for Colombian news analysis using hybrid approach:
    - LDA for probabilistic topic discovery
    - NMF for interpretable topic extraction
    - Keyword-based classification for predefined categories
    """

    # Predefined Colombian news topics with keyword patterns
    COLOMBIAN_TOPICS = {
        'politics': {
            'keywords': [
                'gobierno', 'presidente', 'congreso', 'senado', 'política',
                'elecciones', 'votación', 'partido', 'ley', 'reforma',
                'ministro', 'alcalde', 'gobernador', 'legislativo', 'ejecutivo',
                'petro', 'duque', 'uribe', 'santos', 'paz', 'acuerdo'
            ],
            'weight': 1.2
        },
        'economics': {
            'keywords': [
                'economía', 'banco', 'dólar', 'peso', 'inflación', 'pib',
                'comercio', 'inversión', 'mercado', 'bolsa', 'empresa',
                'empleo', 'desempleo', 'salario', 'tributaria', 'impuesto',
                'bancolombia', 'ecopetrol', 'avianca', 'finanzas', 'fiscal'
            ],
            'weight': 1.1
        },
        'security': {
            'keywords': [
                'seguridad', 'policía', 'militar', 'ejército', 'crimen',
                'violencia', 'narcotráfico', 'guerrilla', 'farc', 'eln',
                'disidencias', 'paramilitares', 'homicidio', 'secuestro',
                'extorsión', 'atentado', 'conflicto', 'armas', 'defensa'
            ],
            'weight': 1.3
        },
        'culture': {
            'keywords': [
                'cultura', 'arte', 'música', 'cine', 'teatro', 'literatura',
                'festival', 'museo', 'patrimonio', 'tradición', 'carnaval',
                'vallenato', 'cumbia', 'shakira', 'botero', 'garcía márquez',
                'gastronomía', 'turismo', 'folclor', 'artista'
            ],
            'weight': 1.0
        },
        'education': {
            'keywords': [
                'educación', 'universidad', 'colegio', 'estudiante', 'maestro',
                'profesor', 'académico', 'investigación', 'ciencia', 'tecnología',
                'icfes', 'saber', 'graduación', 'matrícula', 'beca',
                'virtual', 'campus', 'docente', 'rector', 'mineducación'
            ],
            'weight': 1.0
        },
        'health': {
            'keywords': [
                'salud', 'hospital', 'médico', 'enfermedad', 'pandemia',
                'covid', 'vacuna', 'eps', 'paciente', 'tratamiento',
                'medicina', 'clínica', 'emergencia', 'minsalud', 'virus'
            ],
            'weight': 1.1
        },
        'environment': {
            'keywords': [
                'medio ambiente', 'deforestación', 'amazonía', 'clima',
                'contaminación', 'biodiversidad', 'parque', 'natural',
                'ecología', 'sostenible', 'energía', 'minería', 'recursos'
            ],
            'weight': 1.0
        },
        'sports': {
            'keywords': [
                'deporte', 'fútbol', 'ciclismo', 'colombia', 'selección',
                'nacional', 'james', 'falcao', 'nairo', 'egan',
                'campeonato', 'torneo', 'copa', 'liga', 'atlético'
            ],
            'weight': 0.9
        }
    }

    def __init__(
        self,
        n_topics: int = 8,
        min_confidence: float = 0.1,
        use_lda: bool = True,
        use_nmf: bool = True,
        max_features: int = 1000
    ):
        """
        Initialize TopicModeler with configurable algorithms

        Args:
            n_topics: Number of latent topics to discover
            min_confidence: Minimum confidence threshold for topic assignment
            use_lda: Enable Latent Dirichlet Allocation
            use_nmf: Enable Non-negative Matrix Factorization
            max_features: Maximum vocabulary size for vectorization
        """
        self.n_topics = n_topics
        self.min_confidence = min_confidence
        self.use_lda = use_lda
        self.use_nmf = use_nmf
        self.max_features = max_features

        # Initialize vectorizers
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            strip_accents='unicode',
            lowercase=True,
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2
        )

        self.count_vectorizer = CountVectorizer(
            max_features=max_features,
            strip_accents='unicode',
            lowercase=True,
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2
        )

        # Initialize models
        if self.use_lda:
            self.lda_model = LatentDirichletAllocation(
                n_components=n_topics,
                max_iter=10,
                learning_method='online',
                random_state=42,
                n_jobs=-1
            )

        if self.use_nmf:
            self.nmf_model = NMF(
                n_components=n_topics,
                init='nndsvd',
                max_iter=200,
                random_state=42
            )

        self._is_fitted = False

    def _normalize_text(self, text: str) -> str:
        """Normalize Spanish text for processing"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _calculate_keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate topic scores based on keyword matching"""
        normalized_text = self._normalize_text(text)
        words = set(normalized_text.split())

        scores = {}
        for topic, config in self.COLOMBIAN_TOPICS.items():
            # Count keyword matches
            matches = sum(1 for keyword in config['keywords']
                         if keyword in normalized_text)

            if matches > 0:
                # Calculate confidence based on keyword density and topic weight
                total_words = len(words)
                density = matches / max(total_words, 1)
                confidence = min(density * config['weight'] * 10, 1.0)

                if confidence >= self.min_confidence:
                    scores[topic] = confidence

        return scores

    def _fit_models_if_needed(self, texts: List[str]) -> None:
        """Fit models on provided texts if not already fitted"""
        if self._is_fitted or not texts:
            return

        try:
            if self.use_lda and len(texts) >= 5:
                count_matrix = self.count_vectorizer.fit_transform(texts)
                self.lda_model.fit(count_matrix)

            if self.use_nmf and len(texts) >= 5:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                self.nmf_model.fit(tfidf_matrix)

            self._is_fitted = True
        except Exception:
            # If fitting fails, continue with keyword-based approach
            pass

    def _get_lda_topics(self, text: str) -> Dict[str, float]:
        """Extract topics using LDA"""
        if not self.use_lda or not self._is_fitted:
            return {}

        try:
            count_vec = self.count_vectorizer.transform([text])
            topic_dist = self.lda_model.transform(count_vec)[0]

            topics = {}
            for idx, confidence in enumerate(topic_dist):
                if confidence >= self.min_confidence:
                    topics[f'lda_topic_{idx}'] = float(confidence)

            return topics
        except Exception:
            return {}

    def _get_nmf_topics(self, text: str) -> Dict[str, float]:
        """Extract topics using NMF"""
        if not self.use_nmf or not self._is_fitted:
            return {}

        try:
            tfidf_vec = self.tfidf_vectorizer.transform([text])
            topic_dist = self.nmf_model.transform(tfidf_vec)[0]

            # Normalize to probabilities
            total = topic_dist.sum()
            if total > 0:
                topic_dist = topic_dist / total

            topics = {}
            for idx, confidence in enumerate(topic_dist):
                if confidence >= self.min_confidence:
                    topics[f'nmf_topic_{idx}'] = float(confidence)

            return topics
        except Exception:
            return {}

    def predict_topics(
        self,
        text: str,
        fit_corpus: Optional[List[str]] = None,
        top_n: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """
        Predict topics for given text with confidence scores

        Args:
            text: Input text to analyze
            fit_corpus: Optional corpus to fit models (if not already fitted)
            top_n: Return only top N topics (None = all above threshold)

        Returns:
            List of topic dictionaries with 'topic' and 'confidence' keys,
            sorted by confidence descending

        Example:
            >>> modeler = TopicModeler()
            >>> topics = modeler.predict_topics("El presidente anunció nueva reforma tributaria")
            >>> # [{"topic": "politics", "confidence": 0.85}, {"topic": "economics", "confidence": 0.62}]
        """
        if not text or not text.strip():
            return []

        # Fit models if corpus provided
        if fit_corpus:
            self._fit_models_if_needed(fit_corpus)

        # Get keyword-based scores (primary method for Colombian topics)
        keyword_scores = self._calculate_keyword_scores(text)

        # Get LDA and NMF scores (if available and fitted)
        lda_scores = self._get_lda_topics(text)
        nmf_scores = self._get_nmf_topics(text)

        # Combine all scores
        all_scores = {}

        # Keyword scores have highest priority for Colombian topics
        for topic, score in keyword_scores.items():
            all_scores[topic] = score

        # Add LDA scores with lower weight
        for topic, score in lda_scores.items():
            if topic not in all_scores:
                all_scores[topic] = score * 0.5

        # Add NMF scores with lower weight
        for topic, score in nmf_scores.items():
            if topic not in all_scores:
                all_scores[topic] = score * 0.5

        # Convert to list of dictionaries and sort by confidence
        topics = [
            {"topic": topic, "confidence": round(confidence, 3)}
            for topic, confidence in all_scores.items()
        ]
        topics.sort(key=lambda x: x['confidence'], reverse=True)

        # Return top N if specified
        if top_n:
            topics = topics[:top_n]

        return topics

    def get_topic_keywords(self, topic_name: str) -> List[str]:
        """
        Get keywords associated with a predefined topic

        Args:
            topic_name: Name of the topic

        Returns:
            List of keywords for the topic
        """
        if topic_name in self.COLOMBIAN_TOPICS:
            return self.COLOMBIAN_TOPICS[topic_name]['keywords']
        return []

    def get_all_topics(self) -> List[str]:
        """
        Get list of all predefined Colombian topics

        Returns:
            List of topic names
        """
        return list(self.COLOMBIAN_TOPICS.keys())
