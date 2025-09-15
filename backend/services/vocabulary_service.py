"""
Vocabulary service for managing linguistic data
Implements best practices for vocabulary storage and retrieval
"""

import logging
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database.vocabulary_models import (
    VocabularyLemma,
    VocabularyForm,
    VocabularyTranslation,
    VocabularyContext,
    VocabularyCollocation,
    VocabularyAcquisition,
    VocabularyList
)
from nlp.vocabulary_extractor import VocabularyItem
from app.database.connection import get_db

logger = logging.getLogger(__name__)


class VocabularyService:
    """
    Service layer for vocabulary management
    Handles all vocabulary-related database operations
    """

    def __init__(self, db_session: Session):
        """
        Initialize vocabulary service

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def store_vocabulary_item(self, item: VocabularyItem) -> VocabularyLemma:
        """
        Store or update a vocabulary item in the database

        Args:
            item: VocabularyItem from extraction

        Returns:
            VocabularyLemma database object
        """
        # Check if lemma exists
        lemma_entry = self.db.query(VocabularyLemma).filter_by(
            lemma=item.lemma
        ).first()

        if not lemma_entry:
            # Create new lemma entry
            lemma_entry = VocabularyLemma(
                lemma=item.lemma,
                primary_pos=item.pos_tag,
                corpus_frequency=item.total_frequency,
                document_frequency=item.document_frequency,
                frequency_rank=item.frequency_rank,
                is_colombianism=item.is_colombianism,
                register=item.register,
                standard_form=item.standard_spanish_equivalent,
                semantic_fields=[item.semantic_field] if item.semantic_field else [],
                confidence_score=item.confidence_score,
                first_seen=item.first_seen,
                last_seen=item.last_seen
            )
            self.db.add(lemma_entry)
            self.db.flush()  # Get ID without committing
        else:
            # Update existing entry
            lemma_entry.corpus_frequency += item.total_frequency
            lemma_entry.document_frequency += 1
            lemma_entry.last_seen = item.last_seen

            # Update semantic fields
            if item.semantic_field and item.semantic_field not in (lemma_entry.semantic_fields or []):
                if lemma_entry.semantic_fields:
                    lemma_entry.semantic_fields.append(item.semantic_field)
                else:
                    lemma_entry.semantic_fields = [item.semantic_field]

        # Store word forms
        self._store_word_form(lemma_entry.id, item)

        # Store translations
        if item.english_translation:
            self._store_translation(lemma_entry.id, item)

        # Store contexts
        for context in item.contexts:
            self._store_context(lemma_entry.id, item, context)

        # Store collocations
        for collocation, count in item.collocations.items():
            self._store_collocation(lemma_entry.id, collocation, count)

        self.db.commit()
        return lemma_entry

    def _store_word_form(self, lemma_id: int, item: VocabularyItem):
        """Store a specific word form"""
        # Check if form exists
        form_entry = self.db.query(VocabularyForm).filter_by(
            lemma_id=lemma_id,
            surface_form=item.surface_form
        ).first()

        if not form_entry:
            form_entry = VocabularyForm(
                lemma_id=lemma_id,
                surface_form=item.surface_form,
                pos_tag=item.pos_tag,
                pos_detail=item.pos_detail,
                morphology=item.morphology,
                form_frequency=item.total_frequency
            )
            self.db.add(form_entry)
        else:
            form_entry.form_frequency += item.total_frequency

    def _store_translation(self, lemma_id: int, item: VocabularyItem):
        """Store translation information"""
        # Check if translation exists
        translation = self.db.query(VocabularyTranslation).filter_by(
            lemma_id=lemma_id,
            target_language='en',
            translation=item.english_translation
        ).first()

        if not translation:
            translation = VocabularyTranslation(
                lemma_id=lemma_id,
                target_language='en',
                translation=item.english_translation,
                translation_type='contextual',
                usage_notes=item.usage_notes,
                translation_source='extraction',
                confidence=item.confidence_score
            )
            self.db.add(translation)

    def _store_context(self, lemma_id: int, item: VocabularyItem, context: Dict):
        """Store context example"""
        context_entry = VocabularyContext(
            lemma_id=lemma_id,
            sentence=context.get('sentence', ''),
            left_context=context.get('window', '').split(item.surface_form)[0][-100:],
            right_context=context.get('window', '').split(item.surface_form)[-1][:100],
            token_position=context.get('position', 0),
            source_date=datetime.utcnow(),
            source_category=item.semantic_field
        )
        self.db.add(context_entry)

    def _store_collocation(self, lemma_id: int, pattern: str, frequency: int):
        """Store collocation information"""
        # Parse collocation pattern
        parts = pattern.split('_')
        if len(parts) != 2:
            return

        # Get collocate lemma ID (create if doesn't exist)
        collocate_lemma = parts[0] if parts[0] != str(lemma_id) else parts[1]
        collocate_entry = self.db.query(VocabularyLemma).filter_by(
            lemma=collocate_lemma
        ).first()

        if not collocate_entry:
            # Create minimal entry for collocate
            collocate_entry = VocabularyLemma(
                lemma=collocate_lemma,
                primary_pos='UNKNOWN',
                corpus_frequency=frequency
            )
            self.db.add(collocate_entry)
            self.db.flush()

        # Check if collocation exists
        collocation = self.db.query(VocabularyCollocation).filter_by(
            lemma_id=lemma_id,
            collocate_id=collocate_entry.id,
            pattern=pattern
        ).first()

        if not collocation:
            collocation = VocabularyCollocation(
                lemma_id=lemma_id,
                collocate_id=collocate_entry.id,
                pattern=pattern,
                frequency=frequency,
                position='after' if pattern.startswith(str(lemma_id)) else 'before'
            )
            self.db.add(collocation)
        else:
            collocation.frequency += frequency

    def get_vocabulary_by_frequency(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[VocabularyLemma]:
        """
        Get vocabulary sorted by frequency

        Args:
            limit: Number of items to return
            offset: Offset for pagination

        Returns:
            List of VocabularyLemma objects
        """
        return self.db.query(VocabularyLemma).order_by(
            VocabularyLemma.corpus_frequency.desc()
        ).limit(limit).offset(offset).all()

    def get_colombianisms(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[VocabularyLemma]:
        """
        Get Colombian-specific vocabulary

        Args:
            limit: Number of items to return
            offset: Offset for pagination

        Returns:
            List of Colombian vocabulary
        """
        return self.db.query(VocabularyLemma).filter(
            VocabularyLemma.is_colombianism == True
        ).order_by(
            VocabularyLemma.corpus_frequency.desc()
        ).limit(limit).offset(offset).all()

    def get_vocabulary_by_semantic_field(
        self,
        field: str,
        limit: int = 100
    ) -> List[VocabularyLemma]:
        """
        Get vocabulary for a specific semantic field

        Args:
            field: Semantic field name
            limit: Number of items to return

        Returns:
            List of vocabulary in that field
        """
        return self.db.query(VocabularyLemma).filter(
            VocabularyLemma.semantic_fields.contains([field])
        ).order_by(
            VocabularyLemma.corpus_frequency.desc()
        ).limit(limit).all()

    def get_vocabulary_with_contexts(
        self,
        lemma: str,
        max_contexts: int = 5
    ) -> Dict[str, Any]:
        """
        Get a vocabulary item with example contexts

        Args:
            lemma: Lemma to look up
            max_contexts: Maximum contexts to return

        Returns:
            Dictionary with vocabulary and contexts
        """
        lemma_entry = self.db.query(VocabularyLemma).filter_by(
            lemma=lemma
        ).first()

        if not lemma_entry:
            return None

        # Get contexts
        contexts = self.db.query(VocabularyContext).filter_by(
            lemma_id=lemma_entry.id
        ).order_by(
            VocabularyContext.clarity_score.desc().nullsfirst()
        ).limit(max_contexts).all()

        # Get translations
        translations = self.db.query(VocabularyTranslation).filter_by(
            lemma_id=lemma_entry.id
        ).all()

        # Get collocations
        collocations = self.db.query(VocabularyCollocation).filter_by(
            lemma_id=lemma_entry.id
        ).order_by(
            VocabularyCollocation.frequency.desc()
        ).limit(10).all()

        return {
            'lemma': lemma_entry.lemma,
            'pos': lemma_entry.primary_pos,
            'frequency': lemma_entry.corpus_frequency,
            'is_colombianism': lemma_entry.is_colombianism,
            'register': lemma_entry.register,
            'contexts': [
                {
                    'sentence': ctx.sentence,
                    'left': ctx.left_context,
                    'right': ctx.right_context
                }
                for ctx in contexts
            ],
            'translations': [
                {
                    'language': trans.target_language,
                    'translation': trans.translation,
                    'notes': trans.usage_notes
                }
                for trans in translations
            ],
            'collocations': [
                {
                    'pattern': coll.pattern,
                    'frequency': coll.frequency
                }
                for coll in collocations
            ]
        }

    def search_vocabulary(
        self,
        query: str,
        limit: int = 50
    ) -> List[VocabularyLemma]:
        """
        Search vocabulary using full-text search

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching vocabulary items
        """
        # Use PostgreSQL full-text search
        return self.db.query(VocabularyLemma).filter(
            or_(
                VocabularyLemma.lemma.ilike(f'%{query}%'),
                VocabularyLemma.standard_form.ilike(f'%{query}%')
            )
        ).limit(limit).all()

    def create_vocabulary_list(
        self,
        name: str,
        description: str,
        lemmas: List[str],
        list_type: str = 'custom',
        topic: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> VocabularyList:
        """
        Create a curated vocabulary list

        Args:
            name: List name
            description: List description
            lemmas: List of lemmas to include
            list_type: Type of list
            topic: Topic if applicable
            created_by: Creator

        Returns:
            Created VocabularyList
        """
        # Get lemma IDs
        lemma_entries = self.db.query(VocabularyLemma).filter(
            VocabularyLemma.lemma.in_(lemmas)
        ).all()

        lemma_ids = [entry.id for entry in lemma_entries]

        vocabulary_list = VocabularyList(
            name=name,
            description=description,
            list_type=list_type,
            topic=topic,
            lemma_ids=lemma_ids,
            total_items=len(lemma_ids),
            created_by=created_by
        )

        self.db.add(vocabulary_list)
        self.db.commit()

        return vocabulary_list

    def get_vocabulary_statistics(self) -> Dict[str, Any]:
        """
        Get overall vocabulary statistics

        Returns:
            Dictionary of statistics
        """
        total_lemmas = self.db.query(func.count(VocabularyLemma.id)).scalar()
        total_forms = self.db.query(func.count(VocabularyForm.id)).scalar()
        total_contexts = self.db.query(func.count(VocabularyContext.id)).scalar()
        colombianisms = self.db.query(func.count(VocabularyLemma.id)).filter(
            VocabularyLemma.is_colombianism == True
        ).scalar()

        # POS distribution
        pos_dist = self.db.query(
            VocabularyLemma.primary_pos,
            func.count(VocabularyLemma.id)
        ).group_by(VocabularyLemma.primary_pos).all()

        # Semantic field distribution
        # Note: This is simplified - JSONB array queries are complex
        semantic_dist = self.db.query(
            func.unnest(VocabularyLemma.semantic_fields).label('field'),
            func.count('*')
        ).group_by('field').all()

        return {
            'total_lemmas': total_lemmas,
            'total_forms': total_forms,
            'total_contexts': total_contexts,
            'colombianisms_count': colombianisms,
            'colombianisms_percentage': (colombianisms / total_lemmas * 100) if total_lemmas > 0 else 0,
            'pos_distribution': dict(pos_dist),
            'semantic_distribution': dict(semantic_dist),
            'last_updated': datetime.utcnow().isoformat()
        }