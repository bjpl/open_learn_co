"""
API routes for text and data analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..database.connection import get_db
from ..database.models import ScrapedContent, ContentAnalysis
from nlp.pipeline import NLPPipeline
from nlp.sentiment_analyzer import SentimentAnalyzer
from nlp.topic_modeler import TopicModeler
from nlp.difficulty_scorer import DifficultyScorer

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """Request model for text analysis."""
    text: str = Field(..., min_length=10, description="Text to analyze")
    analysis_types: List[str] = Field(
        default=["sentiment", "entities", "topics", "difficulty"],
        description="Types of analysis to perform"
    )
    language: str = Field(default="es", description="Language code")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    id: Optional[int] = None
    text_preview: str
    sentiment: Optional[Dict[str, Any]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    topics: Optional[List[Dict[str, Any]]] = None
    difficulty: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    created_at: datetime


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""
    content_ids: List[int] = Field(..., description="IDs of scraped content to analyze")
    analysis_types: List[str] = Field(
        default=["sentiment", "entities", "topics"],
        description="Types of analysis to perform"
    )


# Initialize analysis components
nlp_pipeline = NLPPipeline()
sentiment_analyzer = SentimentAnalyzer()
topic_modeler = TopicModeler(n_topics=5)
difficulty_scorer = DifficultyScorer()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive text analysis.
    """
    try:
        result = {}
        text = request.text

        # Sentiment analysis
        if "sentiment" in request.analysis_types:
            sentiment_result = sentiment_analyzer.analyze(text)
            result["sentiment"] = {
                "polarity": sentiment_result.polarity,
                "subjectivity": sentiment_result.subjectivity,
                "classification": sentiment_result.classification,
                "confidence": sentiment_result.confidence
            }

        # Entity extraction
        if "entities" in request.analysis_types:
            entities = nlp_pipeline.extract_entities(text)
            result["entities"] = [
                {
                    "text": ent["text"],
                    "type": ent["label"],
                    "confidence": ent.get("confidence", 0.9)
                }
                for ent in entities
            ]

        # Topic modeling
        if "topics" in request.analysis_types:
            topics = topic_modeler.predict_topics(text)
            result["topics"] = topics

        # Difficulty scoring
        if "difficulty" in request.analysis_types:
            difficulty = difficulty_scorer.score(text)
            result["difficulty"] = {
                "score": difficulty.difficulty_score,
                "cefr_level": difficulty.cefr_level,
                "reading_time": difficulty.reading_time_minutes,
                "flesch_score": difficulty.flesch_score
            }

        # Generate summary
        if "summary" in request.analysis_types:
            summary = nlp_pipeline.summarize(text, max_length=150)
            result["summary"] = summary

        # Store in database (using ContentAnalysis model)
        # Note: ContentAnalysis is linked to ScrapedContent, so we skip DB storage for ad-hoc text
        # In production, create a ScrapedContent entry first or use separate AnalysisResult table

        # For now, return results without persisting ad-hoc text analysis
        db_result_id = None

        return AnalysisResponse(
            id=db_result_id,
            text_preview=text[:200] + "..." if len(text) > 200 else text,
            sentiment=result.get("sentiment"),
            entities=result.get("entities"),
            topics=result.get("topics"),
            difficulty=result.get("difficulty"),
            summary=result.get("summary"),
            created_at=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform batch analysis on multiple scraped contents.
    """
    try:
        # Fetch content from database
        contents = db.query(ScrapedContent).filter(
            ScrapedContent.id.in_(request.content_ids)
        ).all()

        if not contents:
            raise HTTPException(status_code=404, detail="No content found")

        # Schedule background analysis
        background_tasks.add_task(
            process_batch_analysis,
            contents,
            request.analysis_types,
            db
        )

        return {
            "message": f"Batch analysis started for {len(contents)} items",
            "content_ids": request.content_ids,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/results/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve analysis result by ID.
    """
    result = db.query(ContentAnalysis).filter(ContentAnalysis.id == analysis_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    return AnalysisResponse(
        id=result.id,
        text_preview=result.summary[:200] if result.summary else "No preview available",
        sentiment={
            "polarity": result.sentiment_score,
            "classification": result.sentiment_label or ("positive" if result.sentiment_score and result.sentiment_score > 0 else "negative")
        } if result.sentiment_score is not None else None,
        entities=result.entities,
        topics=result.topics,
        difficulty=None,  # ContentAnalysis doesn't have difficulty_score
        summary=result.summary,
        created_at=result.processed_at
    )


@router.get("/results")
async def list_analysis_results(
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List recent analysis results with offset pagination.
    """
    from app.schemas.common_schemas import OffsetPaginationParams
    from app.utils.pagination import calculate_offset, create_pagination_metadata

    # Validate and apply pagination
    params = OffsetPaginationParams(page=page, limit=min(limit, 100))
    offset = params.offset

    results = db.query(ContentAnalysis)\
        .order_by(ContentAnalysis.processed_at.desc())\
        .offset(offset)\
        .limit(params.limit)\
        .all()

    total = db.query(ContentAnalysis).count()
    metadata = create_pagination_metadata(total, params.page, params.limit)

    return {
        "items": [
            {
                "id": r.id,
                "preview": r.summary[:100] + "..." if r.summary and len(r.summary) > 100 else r.summary or "No summary",
                "sentiment_score": r.sentiment_score,
                "topics_count": len(r.topics) if r.topics else 0,
                "entities_count": len(r.entities) if r.entities else 0,
                "created_at": r.processed_at
            }
            for r in results
        ],
        "total": metadata["total"],
        "page": metadata["page"],
        "pages": metadata["pages"],
        "limit": metadata["limit"]
    }


@router.get("/statistics")
async def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    Get analysis statistics.
    """
    total_analyses = db.query(ContentAnalysis).count()

    # Calculate average sentiment
    avg_sentiment = db.query(ContentAnalysis).filter(
        ContentAnalysis.sentiment_score.isnot(None)
    ).with_entities(
        func.avg(ContentAnalysis.sentiment_score)
    ).scalar()

    # Get most common entities
    # Note: This is simplified; in production, aggregate from JSON field
    recent_entities = db.query(ContentAnalysis).filter(
        ContentAnalysis.entities.isnot(None)
    ).limit(100).all()

    entity_counts = {}
    for result in recent_entities:
        if result.entities:
            for entity in result.entities:
                entity_type = entity.get("type", "Unknown")
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

    return {
        "total_analyses": total_analyses,
        "average_sentiment": float(avg_sentiment) if avg_sentiment else 0,
        "entity_distribution": entity_counts,
        "last_analysis": db.query(ContentAnalysis)\
            .order_by(ContentAnalysis.processed_at.desc())\
            .first()\
            .processed_at if total_analyses > 0 else None
    }


def process_batch_analysis(
    contents: List[ScrapedContent],
    analysis_types: List[str],
    db: Session
):
    """
    Process batch analysis in background.
    """
    for content in contents:
        try:
            # Combine title and content for analysis
            text = f"{content.title}\n\n{content.content}"

            result = {}

            if "sentiment" in analysis_types:
                sentiment_result = sentiment_analyzer.analyze(text)
                result["sentiment_score"] = sentiment_result.polarity

            if "entities" in analysis_types:
                entities = nlp_pipeline.extract_entities(text)
                result["entities"] = entities

            if "topics" in analysis_types:
                topics = topic_modeler.predict_topics(text)
                result["topics"] = topics

            # Store analysis result
            db_result = ContentAnalysis(
                content_id=content.id,
                sentiment_score=result.get("sentiment_score"),
                sentiment_label="positive" if result.get("sentiment_score", 0) > 0 else "negative" if result.get("sentiment_score", 0) < 0 else "neutral",
                entities=result.get("entities"),
                topics=result.get("topics"),
                summary=text[:500]  # Store preview as summary
            )
            db.add(db_result)

        except Exception as e:
            print(f"Error analyzing content {content.id}: {str(e)}")
            continue

    db.commit()