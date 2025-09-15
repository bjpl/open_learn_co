"""
API routes for language learning features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ..database.database import get_db
from ..database.vocabulary_models import (
    VocabularyWord, VocabularyCategory, UserVocabulary,
    LearningSession, PracticeResult
)
from ...services.vocabulary_service import VocabularyService
from ...nlp.difficulty_scorer import DifficultyScorer

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


# Initialize services
vocabulary_service = VocabularyService()
difficulty_scorer = DifficultyScorer()


@router.post("/vocabulary", response_model=VocabularyWordResponse)
async def add_vocabulary_word(
    request: VocabularyWordRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new vocabulary word.
    """
    try:
        # Check if word already exists
        existing = db.query(VocabularyWord).filter(
            VocabularyWord.word == request.word.lower()
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Word already exists")

        # Create new word
        word = VocabularyWord(
            word=request.word.lower(),
            translation=request.translation,
            category_id=request.category_id,
            difficulty_level=request.difficulty_level,
            example_sentence=request.example_sentence,
            frequency=0.5,  # Default frequency
            metadata={"notes": request.notes} if request.notes else {}
        )

        db.add(word)
        db.commit()
        db.refresh(word)

        # Get category name if exists
        category_name = None
        if word.category_id:
            category = db.query(VocabularyCategory).filter(
                VocabularyCategory.id == word.category_id
            ).first()
            category_name = category.name if category else None

        return VocabularyWordResponse(
            id=word.id,
            word=word.word,
            translation=word.translation,
            category=category_name,
            difficulty_level=word.difficulty_level,
            frequency=word.frequency,
            example_sentence=word.example_sentence,
            phonetic=word.phonetic,
            created_at=word.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add word: {str(e)}")


@router.get("/vocabulary", response_model=List[VocabularyWordResponse])
async def get_vocabulary(
    category_id: Optional[int] = None,
    difficulty_level: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get vocabulary words with filtering.
    """
    query = db.query(VocabularyWord)

    if category_id:
        query = query.filter(VocabularyWord.category_id == category_id)

    if difficulty_level:
        query = query.filter(VocabularyWord.difficulty_level == difficulty_level)

    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                VocabularyWord.word.like(search_pattern),
                VocabularyWord.translation.like(search_pattern)
            )
        )

    words = query.offset(skip).limit(limit).all()

    return [
        VocabularyWordResponse(
            id=w.id,
            word=w.word,
            translation=w.translation,
            category=w.category.name if w.category else None,
            difficulty_level=w.difficulty_level,
            frequency=w.frequency,
            example_sentence=w.example_sentence,
            phonetic=w.phonetic,
            created_at=w.created_at
        )
        for w in words
    ]


@router.get("/vocabulary/{word_id}", response_model=VocabularyWordResponse)
async def get_vocabulary_word(
    word_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific vocabulary word.
    """
    word = db.query(VocabularyWord).filter(VocabularyWord.id == word_id).first()

    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    return VocabularyWordResponse(
        id=word.id,
        word=word.word,
        translation=word.translation,
        category=word.category.name if word.category else None,
        difficulty_level=word.difficulty_level,
        frequency=word.frequency,
        example_sentence=word.example_sentence,
        phonetic=word.phonetic,
        created_at=word.created_at
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
        # Get words for practice
        query = db.query(VocabularyWord)

        if request.category_id:
            query = query.filter(VocabularyWord.category_id == request.category_id)

        if request.difficulty_level:
            query = query.filter(VocabularyWord.difficulty_level == request.difficulty_level)

        # Get random words
        words = query.order_by(func.random()).limit(request.num_words).all()

        if not words:
            raise HTTPException(status_code=404, detail="No words found for practice")

        # Create learning session
        session = LearningSession(
            user_id=user_id,
            session_type=request.practice_type,
            total_words=len(words),
            metadata={
                "category_id": request.category_id,
                "difficulty_level": request.difficulty_level
            }
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Prepare practice words
        practice_words = [
            {
                "id": w.id,
                "word": w.word,
                "translation": w.translation,
                "example": w.example_sentence,
                "difficulty": w.difficulty_level
            }
            for w in words
        ]

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

        # Record result
        result = PracticeResult(
            session_id=session_id,
            word_id=request.word_id,
            correct=request.correct,
            response_time=request.response_time,
            practice_type=request.practice_type
        )
        db.add(result)

        # Update user vocabulary progress
        user_vocab = db.query(UserVocabulary).filter(
            and_(
                UserVocabulary.user_id == user_id,
                UserVocabulary.word_id == request.word_id
            )
        ).first()

        if not user_vocab:
            user_vocab = UserVocabulary(
                user_id=user_id,
                word_id=request.word_id,
                mastery_level=0
            )
            db.add(user_vocab)

        # Update mastery level
        if request.correct:
            user_vocab.mastery_level = min(user_vocab.mastery_level + 0.1, 1.0)
            user_vocab.correct_count += 1
        else:
            user_vocab.mastery_level = max(user_vocab.mastery_level - 0.05, 0)

        user_vocab.practice_count += 1
        user_vocab.last_practiced = datetime.utcnow()

        # Update session statistics
        session.completed_words += 1
        if request.correct:
            session.correct_answers += 1

        db.commit()

        return {
            "success": True,
            "new_mastery_level": user_vocab.mastery_level,
            "total_practices": user_vocab.practice_count,
            "session_progress": f"{session.completed_words}/{session.total_words}"
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
    # Get user vocabulary statistics
    user_vocab = db.query(UserVocabulary).filter(
        UserVocabulary.user_id == user_id
    ).all()

    total_words = len(user_vocab)
    words_mastered = sum(1 for v in user_vocab if v.mastery_level >= 0.8)

    # Calculate accuracy
    total_practices = sum(v.practice_count for v in user_vocab)
    total_correct = sum(v.correct_count for v in user_vocab)
    accuracy_rate = (total_correct / total_practices) if total_practices > 0 else 0

    # Get difficulty level distribution
    level_dist = {}
    for vocab in user_vocab:
        word = db.query(VocabularyWord).filter(
            VocabularyWord.id == vocab.word_id
        ).first()
        if word:
            level = word.difficulty_level
            level_dist[level] = level_dist.get(level, 0) + 1

    # Get recent sessions
    recent_sessions = db.query(LearningSession).filter(
        LearningSession.user_id == user_id
    ).order_by(LearningSession.created_at.desc()).limit(5).all()

    session_data = [
        {
            "id": s.id,
            "date": s.created_at,
            "type": s.session_type,
            "accuracy": (s.correct_answers / s.total_words) if s.total_words > 0 else 0,
            "duration": s.duration_minutes
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

    # Calculate total practice time
    total_time = db.query(func.sum(LearningSession.duration_minutes)).filter(
        LearningSession.user_id == user_id
    ).scalar() or 0

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
    """
    categories = db.query(VocabularyCategory).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "word_count": db.query(VocabularyWord).filter(
                VocabularyWord.category_id == c.id
            ).count()
        }
        for c in categories
    ]


@router.post("/categories")
async def create_vocabulary_category(
    name: str = Query(..., min_length=1, max_length=50),
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new vocabulary category.
    """
    # Check if category exists
    existing = db.query(VocabularyCategory).filter(
        VocabularyCategory.name == name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = VocabularyCategory(
        name=name,
        description=description
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "created_at": category.created_at
    }