"""
Database models for robust vocabulary storage
Following linguistic data management best practices
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean,
    JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint,
    func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, TSVECTOR
from datetime import datetime

Base = declarative_base()


class VocabularyLemma(Base):
    """
    Master vocabulary table - one entry per unique lemma
    Following ISO 24613:2008 standards for lexical markup
    """
    __tablename__ = 'vocabulary_lemmas'

    id = Column(Integer, primary_key=True)
    lemma = Column(String(100), nullable=False, unique=True, index=True)

    # Primary POS (most common)
    primary_pos = Column(String(20), nullable=False)  # UPOS tags

    # Frequency data
    corpus_frequency = Column(Integer, default=0)  # Total occurrences in corpus
    document_frequency = Column(Integer, default=0)  # Number of documents
    frequency_rank = Column(Integer)  # Rank in frequency list
    frequency_percentile = Column(Float)  # Percentile in corpus

    # Linguistic properties
    syllable_count = Column(Integer)
    phonetic_transcription = Column(String(200))  # IPA
    stress_pattern = Column(String(50))

    # Colombian Spanish markers
    is_colombianism = Column(Boolean, default=False)
    regional_distribution = Column(JSONB)  # {region: frequency}
    register = Column(String(50))  # formal, informal, colloquial, vulgar
    domain = Column(String(50))  # politics, economy, sports, etc.

    # Standard Spanish equivalent
    standard_form = Column(String(100))
    peninsular_form = Column(String(100))  # Spain Spanish equivalent

    # Semantic information
    semantic_fields = Column(ARRAY(String))  # Multiple possible fields
    concept_id = Column(String(50))  # Link to ontology/wordnet

    # Metadata
    first_seen = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    confidence_score = Column(Float, default=1.0)

    # Full-text search vector
    search_vector = Column(TSVECTOR)

    # Relationships
    forms = relationship("VocabularyForm", back_populates="lemma_entry")
    translations = relationship("VocabularyTranslation", back_populates="lemma_entry")
    contexts = relationship("VocabularyContext", back_populates="lemma_entry")
    collocations = relationship("VocabularyCollocation",
                               foreign_keys="VocabularyCollocation.lemma_id",
                               back_populates="lemma_entry")

    # Indexes for performance
    __table_args__ = (
        Index('idx_frequency_rank', 'frequency_rank'),
        Index('idx_semantic_fields', 'semantic_fields', postgresql_using='gin'),
        Index('idx_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_is_colombianism', 'is_colombianism'),
        CheckConstraint('frequency_rank > 0', name='check_positive_rank'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1',
                       name='check_confidence_range'),
    )


class VocabularyForm(Base):
    """
    Different forms of a lemma (conjugations, inflections, etc.)
    """
    __tablename__ = 'vocabulary_forms'

    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)
    surface_form = Column(String(100), nullable=False, index=True)
    pos_tag = Column(String(20), nullable=False)
    pos_detail = Column(String(50))  # Detailed POS with features

    # Morphological features (following Universal Dependencies)
    morphology = Column(JSONB)  # {Gender: Masc, Number: Sing, Tense: Past, etc.}

    # Frequency for this specific form
    form_frequency = Column(Integer, default=0)
    form_probability = Column(Float)  # P(form|lemma)

    # Relationships
    lemma_entry = relationship("VocabularyLemma", back_populates="forms")

    __table_args__ = (
        UniqueConstraint('lemma_id', 'surface_form', 'morphology',
                        name='unique_form_morphology'),
        Index('idx_surface_form', 'surface_form'),
        Index('idx_morphology', 'morphology', postgresql_using='gin'),
    )


class VocabularyTranslation(Base):
    """
    Translations and definitions
    Following TEI (Text Encoding Initiative) dictionary standards
    """
    __tablename__ = 'vocabulary_translations'

    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)

    # Translation information
    target_language = Column(String(10), nullable=False, default='en')  # ISO 639-1
    translation = Column(String(200), nullable=False)
    translation_type = Column(String(50))  # literal, contextual, explanatory

    # Sense information
    sense_number = Column(Integer, default=1)  # For polysemous words
    definition = Column(Text)  # Full definition
    usage_notes = Column(Text)  # How to use this word

    # Examples
    example_source = Column(Text)  # Example in source language
    example_target = Column(Text)  # Example translation

    # Quality indicators
    translation_source = Column(String(50))  # dictionary, ml_model, human
    confidence = Column(Float, default=1.0)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)

    # Relationships
    lemma_entry = relationship("VocabularyLemma", back_populates="translations")

    __table_args__ = (
        Index('idx_target_language', 'target_language'),
        Index('idx_sense_number', 'sense_number'),
        UniqueConstraint('lemma_id', 'target_language', 'sense_number',
                        name='unique_translation_sense'),
    )


class VocabularyContext(Base):
    """
    Contextual examples for vocabulary items
    Stores rich context following corpus linguistics standards
    """
    __tablename__ = 'vocabulary_contexts'

    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)
    form_id = Column(Integer, ForeignKey('vocabulary_forms.id'))
    source_content_id = Column(Integer, ForeignKey('scraped_content.id'))

    # The context itself
    sentence = Column(Text, nullable=False)  # Full sentence
    paragraph = Column(Text)  # Full paragraph for broader context

    # Position information
    token_position = Column(Integer)  # Position in sentence
    char_start = Column(Integer)  # Character position start
    char_end = Column(Integer)  # Character position end

    # Linguistic context
    left_context = Column(String(200))  # Words before
    right_context = Column(String(200))  # Words after
    syntactic_role = Column(String(50))  # Subject, object, etc.
    dependency_head = Column(String(100))  # Syntactic head
    dependency_relation = Column(String(50))  # Dependency relation

    # Source metadata
    source_date = Column(DateTime)
    source_author = Column(String(200))
    source_category = Column(String(50))
    source_url = Column(String(500))

    # Quality and relevance
    is_exemplar = Column(Boolean, default=False)  # Is this a good example?
    clarity_score = Column(Float)  # How clear is this example
    difficulty_level = Column(String(10))  # A1-C2 CEFR level

    # Relationships
    lemma_entry = relationship("VocabularyLemma", back_populates="contexts")

    __table_args__ = (
        Index('idx_source_content', 'source_content_id'),
        Index('idx_is_exemplar', 'is_exemplar'),
        Index('idx_difficulty_level', 'difficulty_level'),
    )


class VocabularyCollocation(Base):
    """
    Collocations and multi-word expressions
    Following corpus linguistics collocation extraction standards
    """
    __tablename__ = 'vocabulary_collocations'

    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)
    collocate_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)

    # Collocation pattern
    pattern = Column(String(200), nullable=False)  # e.g., "hacer_caso", "tomar_decisión"
    pattern_type = Column(String(50))  # verb_noun, adj_noun, etc.
    position = Column(String(20))  # before, after

    # Statistical measures
    frequency = Column(Integer, default=0)
    mutual_information = Column(Float)  # MI score
    log_likelihood = Column(Float)  # Log-likelihood ratio
    dice_coefficient = Column(Float)  # Dice coefficient
    t_score = Column(Float)  # T-score

    # Linguistic properties
    is_fixed_expression = Column(Boolean, default=False)
    is_idiom = Column(Boolean, default=False)
    transparency = Column(Float)  # Semantic transparency (0-1)

    # Relationships
    lemma_entry = relationship("VocabularyLemma",
                              foreign_keys=[lemma_id],
                              back_populates="collocations")
    collocate_entry = relationship("VocabularyLemma",
                                  foreign_keys=[collocate_id])

    __table_args__ = (
        UniqueConstraint('lemma_id', 'collocate_id', 'position',
                        name='unique_collocation'),
        Index('idx_pattern', 'pattern'),
        Index('idx_frequency', 'frequency'),
        Index('idx_mutual_information', 'mutual_information'),
        CheckConstraint('mutual_information >= 0', name='check_positive_mi'),
    )


class VocabularyAcquisition(Base):
    """
    Track vocabulary acquisition for users
    Based on SLA (Second Language Acquisition) research
    """
    __tablename__ = 'vocabulary_acquisition'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lemma_id = Column(Integer, ForeignKey('vocabulary_lemmas.id'), nullable=False)

    # Exposure tracking
    first_exposure = Column(DateTime, default=func.now())
    last_exposure = Column(DateTime, default=func.now())
    total_exposures = Column(Integer, default=1)
    meaningful_exposures = Column(Integer, default=0)  # In context

    # Comprehension indicators
    comprehension_level = Column(Float, default=0.0)  # 0-1
    production_level = Column(Float, default=0.0)  # 0-1

    # Context of acquisition
    acquisition_contexts = Column(JSONB)  # List of context IDs
    preferred_translation = Column(String(200))  # User's preferred meaning

    # Notes and personalization
    user_notes = Column(Text)
    personal_examples = Column(JSONB)  # User's own examples
    mnemonic = Column(Text)  # Memory aid

    __table_args__ = (
        UniqueConstraint('user_id', 'lemma_id', name='unique_user_vocabulary'),
        Index('idx_user_vocabulary', 'user_id', 'lemma_id'),
        Index('idx_comprehension_level', 'comprehension_level'),
    )


class VocabularyList(Base):
    """
    Curated vocabulary lists for learning
    """
    __tablename__ = 'vocabulary_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # List metadata
    list_type = Column(String(50))  # frequency, thematic, news_based
    topic = Column(String(100))  # Politics, economy, daily_life
    source = Column(String(100))  # Created from news, manual, etc.

    # Learning parameters
    target_level = Column(String(10))  # A1-C2
    estimated_hours = Column(Float)  # Hours to learn

    # Content
    lemma_ids = Column(ARRAY(Integer))  # Ordered list of lemmas
    total_items = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    is_public = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_list_type', 'list_type'),
        Index('idx_topic', 'topic'),
        Index('idx_target_level', 'target_level'),
    )