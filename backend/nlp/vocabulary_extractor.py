"""
Robust vocabulary extraction system for Colombian Spanish
Following best practices for linguistic annotation and storage
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json

from spacy.tokens import Doc, Token, Span
import spacy

logger = logging.getLogger(__name__)


@dataclass
class VocabularyItem:
    """
    Comprehensive vocabulary item following linguistic best practices
    """
    # Core linguistic properties
    surface_form: str          # Actual word as it appears in text
    lemma: str                 # Dictionary form
    pos_tag: str              # Part of speech (UPOS standard)
    pos_detail: str           # Detailed POS with features

    # Morphological features
    morphology: Dict[str, str]  # Gender, number, tense, mood, etc.

    # Frequency and distribution
    document_frequency: int    # Number of documents containing this word
    total_frequency: int      # Total occurrences across all documents
    frequency_rank: Optional[int]  # Rank in frequency list

    # Contextual information
    contexts: List[Dict]      # Multiple example contexts
    collocations: Dict[str, int]  # Common word combinations

    # Semantic information
    semantic_field: Optional[str]  # Topic/domain (politics, economy, etc.)
    register: Optional[str]    # Formal, informal, colloquial, etc.
    regional_marker: Optional[str]  # Colombian, regional, standard

    # Colombian Spanish specific
    is_colombianism: bool     # Colombian-specific term
    standard_spanish_equivalent: Optional[str]
    english_translation: Optional[str]
    usage_notes: Optional[str]

    # Metadata
    first_seen: datetime
    last_seen: datetime
    source_documents: List[str]  # Document IDs where found
    confidence_score: float    # Extraction confidence


class VocabularyExtractor:
    """
    Professional-grade vocabulary extraction for language learning
    """

    def __init__(self, nlp_model: spacy.Language, config: Optional[Dict] = None):
        """
        Initialize with spaCy model and configuration

        Args:
            nlp_model: Loaded spaCy model for Spanish
            config: Optional configuration dictionary
        """
        self.nlp = nlp_model
        self.config = config or self._default_config()

        # Load linguistic resources
        self._load_frequency_lists()
        self._load_colombianisms()
        self._load_semantic_fields()

        # Initialize caches for performance
        self.lemma_cache = {}
        self.translation_cache = {}

        logger.info("VocabularyExtractor initialized with robust configuration")

    def _default_config(self) -> Dict:
        """Default configuration following best practices"""
        return {
            'min_word_length': 3,
            'max_word_length': 30,
            'min_frequency': 1,
            'include_proper_nouns': True,
            'include_numbers': False,
            'context_window': 50,  # Characters before/after
            'max_contexts_per_word': 5,
            'collocation_window': 3,  # Words before/after for collocations
            'confidence_threshold': 0.7,
            'excluded_pos': ['PUNCT', 'SPACE', 'SYM'],
            'target_pos': ['NOUN', 'VERB', 'ADJ', 'ADV', 'PROPN']
        }

    def _load_frequency_lists(self):
        """Load frequency lists for Spanish vocabulary"""
        # In production, load from database or files
        # Using sample data for demonstration
        self.frequency_ranks = {
            # Most common Spanish words with ranks
            'el': 1, 'de': 2, 'la': 3, 'y': 4, 'a': 5,
            'en': 6, 'que': 7, 'es': 8, 'por': 9, 'para': 10
        }

        # Colombian Spanish frequency adjustments
        self.colombian_frequency = {
            'pues': 50,  # More common in Colombian Spanish
            'parce': 500,
            'chévere': 600
        }

    def _load_colombianisms(self):
        """Load Colombian Spanish specific vocabulary"""
        self.colombianisms = {
            'parcero': {
                'standard': 'amigo',
                'english': 'friend/buddy',
                'register': 'informal',
                'regions': ['all']
            },
            'bacano': {
                'standard': 'bueno',
                'english': 'cool/nice',
                'register': 'colloquial',
                'regions': ['all']
            },
            'berraco': {
                'standard': 'difícil/hábil',
                'english': 'tough/skilled',
                'register': 'colloquial',
                'regions': ['all']
            },
            'tinto': {
                'standard': 'café negro',
                'english': 'black coffee',
                'register': 'standard',
                'regions': ['all']
            },
            'ñapa': {
                'standard': 'extra/añadidura',
                'english': 'extra/bonus',
                'register': 'informal',
                'regions': ['all']
            }
        }

    def _load_semantic_fields(self):
        """Load semantic field mappings"""
        self.semantic_fields = {
            'política': ['presidente', 'gobierno', 'ministro', 'elección', 'votación'],
            'economía': ['peso', 'inflación', 'mercado', 'banco', 'inversión'],
            'conflicto': ['paz', 'guerra', 'violencia', 'acuerdo', 'víctima'],
            'educación': ['estudiante', 'profesor', 'universidad', 'escuela', 'aprendizaje'],
            'salud': ['médico', 'hospital', 'enfermedad', 'tratamiento', 'vacuna']
        }

    def extract(self, doc: Doc, source_id: Optional[str] = None) -> List[VocabularyItem]:
        """
        Extract vocabulary items from a spaCy document

        Args:
            doc: Processed spaCy document
            source_id: Optional document identifier

        Returns:
            List of VocabularyItem objects
        """
        vocabulary_items = []
        word_contexts = defaultdict(list)
        word_collocations = defaultdict(Counter)

        # First pass: collect all valid tokens and their contexts
        for token in doc:
            if self._should_extract(token):
                # Extract context
                context = self._extract_context(token, doc)
                word_contexts[token.lemma_].append(context)

                # Extract collocations
                collocations = self._extract_collocations(token, doc)
                word_collocations[token.lemma_].update(collocations)

        # Second pass: create VocabularyItem objects
        for lemma, contexts in word_contexts.items():
            # Get the most representative token for this lemma
            tokens = [c['token'] for c in contexts]
            representative_token = tokens[0]  # Could use more sophisticated selection

            vocabulary_item = self._create_vocabulary_item(
                representative_token,
                contexts,
                dict(word_collocations[lemma]),
                source_id
            )

            if vocabulary_item.confidence_score >= self.config['confidence_threshold']:
                vocabulary_items.append(vocabulary_item)

        return vocabulary_items

    def _should_extract(self, token: Token) -> bool:
        """
        Determine if a token should be extracted

        Args:
            token: spaCy token

        Returns:
            Boolean indicating if token should be extracted
        """
        # Check POS tag
        if token.pos_ in self.config['excluded_pos']:
            return False

        # Check if target POS (if specified)
        if self.config.get('target_pos') and token.pos_ not in self.config['target_pos']:
            return False

        # Check word length
        if not (self.config['min_word_length'] <= len(token.text) <= self.config['max_word_length']):
            return False

        # Check if it's a number (unless configured to include)
        if not self.config['include_numbers'] and token.like_num:
            return False

        # Check if it's a stop word (but might still be useful for learning)
        # We'll include stop words but mark them appropriately

        return True

    def _extract_context(self, token: Token, doc: Doc) -> Dict:
        """
        Extract rich context for a token

        Args:
            token: Target token
            doc: Full document

        Returns:
            Context dictionary
        """
        # Get sentence boundaries
        sent = token.sent
        sent_start = sent.start
        sent_end = sent.end

        # Get window around token
        window_size = self.config['context_window']
        start_char = max(0, token.idx - window_size)
        end_char = min(len(doc.text), token.idx + len(token.text) + window_size)

        # Extract syntactic information
        dependencies = {
            'head': token.head.text if token.head != token else None,
            'head_pos': token.head.pos_ if token.head != token else None,
            'dep_relation': token.dep_,
            'children': [{'text': child.text, 'dep': child.dep_} for child in token.children]
        }

        return {
            'token': token,
            'surface_form': token.text,
            'sentence': sent.text,
            'position_in_sentence': token.i - sent_start,
            'sentence_length': sent_end - sent_start,
            'window': doc.text[start_char:end_char],
            'dependencies': dependencies,
            'is_sentence_start': token.i == sent_start,
            'is_sentence_end': token.i == sent_end - 1
        }

    def _extract_collocations(self, token: Token, doc: Doc) -> Counter:
        """
        Extract collocations (common word combinations)

        Args:
            token: Target token
            doc: Full document

        Returns:
            Counter of collocations
        """
        collocations = Counter()
        window = self.config['collocation_window']

        # Left context
        for i in range(max(0, token.i - window), token.i):
            if doc[i].pos_ not in ['PUNCT', 'SPACE']:
                collocation = f"{doc[i].lemma_}_{token.lemma_}"
                collocations[collocation] += 1

        # Right context
        for i in range(token.i + 1, min(len(doc), token.i + window + 1)):
            if doc[i].pos_ not in ['PUNCT', 'SPACE']:
                collocation = f"{token.lemma_}_{doc[i].lemma_}"
                collocations[collocation] += 1

        return collocations

    def _create_vocabulary_item(
        self,
        token: Token,
        contexts: List[Dict],
        collocations: Dict[str, int],
        source_id: Optional[str]
    ) -> VocabularyItem:
        """
        Create a comprehensive VocabularyItem

        Args:
            token: Representative token
            contexts: List of contexts
            collocations: Collocation counts
            source_id: Source document ID

        Returns:
            VocabularyItem object
        """
        # Extract morphological features
        morphology = {
            'Gender': token.morph.get('Gender', [None])[0],
            'Number': token.morph.get('Number', [None])[0],
            'Tense': token.morph.get('Tense', [None])[0],
            'Mood': token.morph.get('Mood', [None])[0],
            'Person': token.morph.get('Person', [None])[0],
            'VerbForm': token.morph.get('VerbForm', [None])[0]
        }
        # Remove None values
        morphology = {k: v for k, v in morphology.items() if v is not None}

        # Determine if it's a Colombianism
        is_colombianism = token.lemma_ in self.colombianisms
        colombian_info = self.colombianisms.get(token.lemma_, {})

        # Get frequency rank
        frequency_rank = self.frequency_ranks.get(
            token.lemma_,
            self.colombian_frequency.get(token.lemma_)
        )

        # Determine semantic field
        semantic_field = self._determine_semantic_field(token.lemma_)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(token, contexts)

        # Prepare contexts for storage (limit to max configured)
        stored_contexts = []
        for ctx in contexts[:self.config['max_contexts_per_word']]:
            stored_contexts.append({
                'sentence': ctx['sentence'],
                'window': ctx['window'],
                'position': ctx['position_in_sentence']
            })

        return VocabularyItem(
            surface_form=token.text,
            lemma=token.lemma_,
            pos_tag=token.pos_,
            pos_detail=token.tag_,
            morphology=morphology,
            document_frequency=1,  # Will be updated in aggregation
            total_frequency=len(contexts),
            frequency_rank=frequency_rank,
            contexts=stored_contexts,
            collocations=collocations,
            semantic_field=semantic_field,
            register=colombian_info.get('register'),
            regional_marker='Colombian' if is_colombianism else 'Standard',
            is_colombianism=is_colombianism,
            standard_spanish_equivalent=colombian_info.get('standard'),
            english_translation=colombian_info.get('english'),
            usage_notes=None,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            source_documents=[source_id] if source_id else [],
            confidence_score=confidence_score
        )

    def _determine_semantic_field(self, lemma: str) -> Optional[str]:
        """Determine the semantic field of a word"""
        for field, words in self.semantic_fields.items():
            if lemma in words:
                return field
        return None

    def _calculate_confidence(self, token: Token, contexts: List[Dict]) -> float:
        """
        Calculate confidence score for extraction

        Args:
            token: Token being evaluated
            contexts: Contexts found

        Returns:
            Confidence score between 0 and 1
        """
        score = 1.0

        # Reduce confidence for very short words
        if len(token.text) < 3:
            score *= 0.8

        # Reduce confidence for single occurrence
        if len(contexts) == 1:
            score *= 0.9

        # Increase confidence for known vocabulary
        if token.lemma_ in self.frequency_ranks or token.lemma_ in self.colombianisms:
            score *= 1.1

        # Reduce confidence for entities (might be names)
        if token.ent_type_:
            score *= 0.9

        return min(1.0, score)

    def aggregate_vocabulary(
        self,
        vocabulary_items: List[VocabularyItem]
    ) -> Dict[str, VocabularyItem]:
        """
        Aggregate vocabulary items across multiple documents

        Args:
            vocabulary_items: List of vocabulary items from multiple sources

        Returns:
            Dictionary of aggregated vocabulary by lemma
        """
        aggregated = {}

        for item in vocabulary_items:
            if item.lemma not in aggregated:
                aggregated[item.lemma] = item
            else:
                # Merge information
                existing = aggregated[item.lemma]
                existing.total_frequency += item.total_frequency
                existing.document_frequency += 1
                existing.contexts.extend(item.contexts[:self.config['max_contexts_per_word']])
                existing.contexts = existing.contexts[:self.config['max_contexts_per_word']]

                # Merge collocations
                for collocation, count in item.collocations.items():
                    existing.collocations[collocation] = existing.collocations.get(collocation, 0) + count

                # Update timestamps
                existing.last_seen = max(existing.last_seen, item.last_seen)
                existing.source_documents.extend(item.source_documents)

        return aggregated

    def export_to_json(self, vocabulary_items: List[VocabularyItem]) -> str:
        """
        Export vocabulary items to JSON format

        Args:
            vocabulary_items: List of vocabulary items

        Returns:
            JSON string
        """
        items_dict = []
        for item in vocabulary_items:
            item_dict = asdict(item)
            # Convert datetime to string
            item_dict['first_seen'] = item_dict['first_seen'].isoformat()
            item_dict['last_seen'] = item_dict['last_seen'].isoformat()
            items_dict.append(item_dict)

        return json.dumps(items_dict, ensure_ascii=False, indent=2)

    def calculate_vocabulary_statistics(
        self,
        vocabulary_items: List[VocabularyItem]
    ) -> Dict[str, Any]:
        """
        Calculate statistics about extracted vocabulary

        Args:
            vocabulary_items: List of vocabulary items

        Returns:
            Dictionary of statistics
        """
        if not vocabulary_items:
            return {}

        pos_distribution = Counter(item.pos_tag for item in vocabulary_items)
        semantic_distribution = Counter(item.semantic_field for item in vocabulary_items if item.semantic_field)
        colombianisms_count = sum(1 for item in vocabulary_items if item.is_colombianism)

        return {
            'total_unique_words': len(vocabulary_items),
            'total_occurrences': sum(item.total_frequency for item in vocabulary_items),
            'pos_distribution': dict(pos_distribution),
            'semantic_fields': dict(semantic_distribution),
            'colombianisms_count': colombianisms_count,
            'colombianisms_percentage': (colombianisms_count / len(vocabulary_items)) * 100,
            'average_word_length': sum(len(item.surface_form) for item in vocabulary_items) / len(vocabulary_items),
            'most_frequent_words': sorted(vocabulary_items, key=lambda x: x.total_frequency, reverse=True)[:10]
        }