"""
API routes for language learning features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ..database.connection import get_db
from ..database.vocabulary_models import VocabularyLemma
from ..database.models import User, UserVocabulary, LearningSession
from backend.services.vocabulary_service import VocabularyService

router = APIRouter(prefix="/language", tags=["language"])


class VocabularyWordRequest(BaseModel):
    """Request model for adding vocabulary."""
    word: str = Field(..., min_length=1, max_length=100)
    translation: str = Field(..., min_length=1, max_length=200)
    category_id: Optional[int] = None
    difficulty_level: Optional[str] = Field(default="A1")
    example_sentence: Optional[str] = None
    notes: Optional[str] = None


class VocabularyWordResponse(BaseModel):
    """Response model for vocabulary word."""
    id: int
    word: str
    translation: str
    category: Optional[str] = None
    difficulty_level: str
    frequency: float
    example_sentence: Optional[str] = None
    phonetic: Optional[str] = None
    created_at: datetime


class PracticeSessionRequest(BaseModel):
    """Request model for practice session."""
    category_id: Optional[int] = None
    difficulty_level: Optional[str] = None
    num_words: int = Field(default=10, ge=1, le=50)
    practice_type: str = Field(default="flashcard")


class PracticeResultRequest(BaseModel):
    """Request model for practice result."""
    word_id: int
    correct: bool
    response_time: float
    practice_type: str


class LearningProgressResponse(BaseModel):
    """Response model for learning progress."""
    total_words_learned: int
    words_mastered: int
    current_streak: int
    total_practice_time: float
    accuracy_rate: float
    level_distribution: Dict[str, int]
    recent_sessions: List[Dict[str, Any]]


# Note: Services require database session, initialized per request


@router.post("/vocabulary", response_model=VocabularyWordResponse)
async def add_vocabulary_word(
    request: VocabularyWordRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new vocabulary word.
    """
    try:
        # Check if lemma already exists
        existing = db.query(VocabularyLemma).filter(
            VocabularyLemma.lemma == request.word.lower()
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Word already exists")

        # Create new lemma entry
        lemma = VocabularyLemma(
            lemma=request.word.lower(),
            primary_pos="NOUN",  # Default POS, should be detected by NLP
            corpus_frequency=0,
            frequency_rank=0
        )

        db.add(lemma)
        db.commit()
        db.refresh(lemma)

        # Create translation
        from ..database.vocabulary_models import VocabularyTranslation
        translation = VocabularyTranslation(
            lemma_id=lemma.id,
            target_language='en',
            translation=request.translation,
            translation_type='manual',
            translation_source='user',
            confidence=1.0
        )
        db.add(translation)
        db.commit()

        return VocabularyWordResponse(
            id=lemma.id,
            word=lemma.lemma,
            translation=request.translation,
            category=None,  # Categories not implemented yet
            difficulty_level=request.difficulty_level or "A1",
            frequency=float(lemma.corpus_frequency) if lemma.corpus_frequency else 0.0,
            example_sentence=request.example_sentence,
            phonetic=lemma.phonetic_transcription,
            created_at=lemma.first_seen
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add word: {str(e)}")


@router.get("/vocabulary")
async def get_vocabulary(
    category_id: Optional[int] = None,
    difficulty_level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get vocabulary words with filtering and offset pagination.
    """
    from ..database.vocabulary_models import VocabularyTranslation
    from app.schemas.common_schemas import OffsetPaginationParams
    from app.utils.pagination import create_pagination_metadata

    # Validate pagination
    params = OffsetPaginationParams(page=page, limit=min(limit, 100))

    query = db.query(VocabularyLemma)

    # Note: category_id and difficulty_level filtering not implemented
    # These would require additional fields or joins

    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(VocabularyLemma.lemma.like(search_pattern))

    # Get total count
    total = query.count()

    # Apply pagination
    lemmas = query.offset(params.offset).limit(params.limit).all()

    results = []
    for lemma in lemmas:
        # Get first translation for this lemma
        translation = db.query(VocabularyTranslation).filter(
            VocabularyTranslation.lemma_id == lemma.id,
            VocabularyTranslation.target_language == 'en'
        ).first()

        results.append(VocabularyWordResponse(
            id=lemma.id,
            word=lemma.lemma,
            translation=translation.translation if translation else "",
            category=None,  # Categories not implemented
            difficulty_level="A1",  # Default level
            frequency=float(lemma.corpus_frequency) if lemma.corpus_frequency else 0.0,
            example_sentence=None,  # Would need to query VocabularyContext
            phonetic=lemma.phonetic_transcription,
            created_at=lemma.first_seen
        ))

    # Create pagination metadata
    metadata = create_pagination_metadata(total, params.page, params.limit)

    return {
        "items": results,
        "total": metadata["total"],
        "page": metadata["page"],
        "pages": metadata["pages"],
        "limit": metadata["limit"]
    }


@router.get("/vocabulary/{word_id}", response_model=VocabularyWordResponse)
async def get_vocabulary_word(
    word_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific vocabulary word.
    """
    from ..database.vocabulary_models import VocabularyTranslation, VocabularyContext

    lemma = db.query(VocabularyLemma).filter(VocabularyLemma.id == word_id).first()

    if not lemma:
        raise HTTPException(status_code=404, detail="Word not found")

    # Get translation
    translation = db.query(VocabularyTranslation).filter(
        VocabularyTranslation.lemma_id == lemma.id,
        VocabularyTranslation.target_language == 'en'
    ).first()

    # Get example context
    context = db.query(VocabularyContext).filter(
        VocabularyContext.lemma_id == lemma.id
    ).first()

    return VocabularyWordResponse(
        id=lemma.id,
        word=lemma.lemma,
        translation=translation.translation if translation else "",
        category=None,
        difficulty_level="A1",
        frequency=float(lemma.corpus_frequency) if lemma.corpus_frequency else 0.0,
        example_sentence=context.sentence if context else None,
        phonetic=lemma.phonetic_transcription,
        created_at=lemma.first_seen
    )


@router.post("/practice/start")
async def start_practice_session(
    request: PracticeSessionRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Start a new practice session.
    """
    try:
        from ..database.vocabulary_models import VocabularyTranslation

        # Get lemmas for practice
        query = db.query(VocabularyLemma)

        # Note: category and difficulty filtering not implemented yet
        # Would require additional metadata or filtering logic

        # Get random words
        words = query.order_by(func.random()).limit(request.num_words).all()

        if not words:
            raise HTTPException(status_code=404, detail="No words found for practice")

        # Create learning session
        session = LearningSession(
            user_id=user_id,
            session_type=request.practice_type,
            items_completed=0,
            correct_answers=0,
            incorrect_answers=0,
            content_ids=[],
            vocabulary_ids=[w.id for w in words]
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Prepare practice words with translations
        from ..database.vocabulary_models import VocabularyTranslation
        practice_words = []
        for w in words:
            translation = db.query(VocabularyTranslation).filter(
                VocabularyTranslation.lemma_id == w.id,
                VocabularyTranslation.target_language == 'en'
            ).first()

            practice_words.append({
                "id": w.id,
                "word": w.lemma,
                "translation": translation.translation if translation else "",
                "example": None,  # Would need VocabularyContext query
                "difficulty": "A1"  # Default
            })

        return {
            "session_id": session.id,
            "words": practice_words,
            "total": len(practice_words),
            "practice_type": request.practice_type
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/practice/result")
async def record_practice_result(
    request: PracticeResultRequest,
    session_id: int = Query(..., description="Session ID"),
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Record practice result for a word.
    """
    try:
        # Verify session exists
        session = db.query(LearningSession).filter(
            LearningSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Note: PracticeResult model doesn't exist in models.py
        # Results tracked via UserVocabulary and LearningSession instead

        # Update user vocabulary progress using vocabulary_models
        from ..database.vocabulary_models import VocabularyAcquisition

        user_vocab = db.query(VocabularyAcquisition).filter(
            and_(
                VocabularyAcquisition.user_id == user_id,
                VocabularyAcquisition.lemma_id == request.word_id
            )
        ).first()

        if not user_vocab:
            user_vocab = VocabularyAcquisition(
                user_id=user_id,
                lemma_id=request.word_id,
                total_exposures=1,
                meaningful_exposures=0,
                comprehension_level=0.0,
                production_level=0.0
            )
            db.add(user_vocab)
        else:
            user_vocab.total_exposures += 1

        # Update comprehension level based on correctness
        if request.correct:
            user_vocab.comprehension_level = min(user_vocab.comprehension_level + 0.1, 1.0)
            user_vocab.meaningful_exposures += 1
        else:
            user_vocab.comprehension_level = max(user_vocab.comprehension_level - 0.05, 0.0)

        user_vocab.last_exposure = datetime.utcnow()

        # Update session statistics
        session.items_completed += 1
        if request.correct:
            session.correct_answers += 1
        else:
            session.incorrect_answers += 1

        db.commit()

        return {
            "success": True,
            "new_mastery_level": user_vocab.comprehension_level,
            "total_practices": user_vocab.total_exposures,
            "session_progress": f"{session.items_completed}/{len(session.vocabulary_ids or [])}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record result: {str(e)}")


@router.get("/progress/{user_id}", response_model=LearningProgressResponse)
async def get_learning_progress(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's learning progress.
    """
    from ..database.vocabulary_models import VocabularyAcquisition

    # Get user vocabulary statistics
    user_vocab = db.query(VocabularyAcquisition).filter(
        VocabularyAcquisition.user_id == user_id
    ).all()

    total_words = len(user_vocab)
    words_mastered = sum(1 for v in user_vocab if v.comprehension_level >= 0.8)

    # Calculate accuracy
    total_practices = sum(v.total_exposures for v in user_vocab)
    total_correct = sum(v.meaningful_exposures for v in user_vocab)
    accuracy_rate = (total_correct / total_practices) if total_practices > 0 else 0

    # Get difficulty level distribution (simplified - not tracked in VocabularyAcquisition)
    level_dist = {
        "A1": 0,
        "A2": 0,
        "B1": 0,
        "B2": 0,
        "C1": 0,
        "C2": 0
    }

    # Get recent sessions
    recent_sessions = db.query(LearningSession).filter(
        LearningSession.user_id == user_id
    ).order_by(LearningSession.created_at.desc()).limit(5).all()

    session_data = [
        {
            "id": s.id,
            "date": s.started_at,
            "type": s.session_type,
            "accuracy": (s.correct_answers / s.items_completed) if s.items_completed > 0 else 0,
            "duration": s.duration_seconds / 60 if s.duration_seconds else 0  # Convert to minutes
        }
        for s in recent_sessions
    ]

    # Calculate current streak
    today = datetime.utcnow().date()
    streak = 0
    current_date = today

    while True:
        session_exists = db.query(LearningSession).filter(
            and_(
                LearningSession.user_id == user_id,
                func.date(LearningSession.created_at) == current_date
            )
        ).first()

        if session_exists:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    # Calculate total practice time (convert seconds to minutes)
    total_time_seconds = db.query(func.sum(LearningSession.duration_seconds)).filter(
        LearningSession.user_id == user_id
    ).scalar() or 0
    total_time = total_time_seconds / 60

    return LearningProgressResponse(
        total_words_learned=total_words,
        words_mastered=words_mastered,
        current_streak=streak,
        total_practice_time=float(total_time),
        accuracy_rate=accuracy_rate,
        level_distribution=level_dist,
        recent_sessions=session_data
    )


@router.get("/categories")
async def get_vocabulary_categories(db: Session = Depends(get_db)):
    """
    Get all vocabulary categories.
    Note: Category system not yet implemented in vocabulary_models.
    Returns semantic fields as categories instead.
    """
    from ..database.vocabulary_models import VocabularyLemma

    # Get unique semantic fields as categories
    # This is a simplified implementation until categories are properly added
    lemmas_with_fields = db.query(VocabularyLemma).filter(
        VocabularyLemma.semantic_fields.isnot(None)
    ).all()

    categories = {}
    for lemma in lemmas_with_fields:
        if lemma.semantic_fields:
            for field in lemma.semantic_fields:
                if field not in categories:
                    categories[field] = 0
                categories[field] += 1

    return [
        {
            "id": idx,
            "name": field,
            "description": f"Words in {field} semantic field",
            "word_count": count
        }
        for idx, (field, count) in enumerate(categories.items(), 1)
    ]


@router.post("/categories")
async def create_vocabulary_category(
    name: str = Query(..., min_length=1, max_length=50),
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new vocabulary category.
    Note: Category system not yet implemented in vocabulary_models.
    This endpoint is a placeholder for future implementation.
    """
    # Placeholder response
    raise HTTPException(
        status_code=501,
        detail="Category creation not yet implemented. Use semantic fields instead."
    )