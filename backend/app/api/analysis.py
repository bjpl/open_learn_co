"""
API routes for text and data analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..database.database import get_db
from ..database.models import AnalysisResult, ScrapedContent
from ...nlp.pipeline import NLPPipeline
from ...nlp.sentiment_analyzer import SentimentAnalyzer
from ...nlp.topic_modeler import TopicModeler
from ...nlp.difficulty_scorer import DifficultyScorer

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

        # Store in database
        db_result = AnalysisResult(
            content=text[:500],  # Store preview
            sentiment_score=result.get("sentiment", {}).get("polarity"),
            entities=result.get("entities", []),
            topics=result.get("topics", []),
            difficulty_score=result.get("difficulty", {}).get("score"),
            summary=result.get("summary"),
            metadata={
                "analysis_types": request.analysis_types,
                "language": request.language
            }
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return AnalysisResponse(
            id=db_result.id,
            text_preview=text[:200] + "..." if len(text) > 200 else text,
            sentiment=result.get("sentiment"),
            entities=result.get("entities"),
            topics=result.get("topics"),
            difficulty=result.get("difficulty"),
            summary=result.get("summary"),
            created_at=db_result.created_at
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
    result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    return AnalysisResponse(
        id=result.id,
        text_preview=result.content,
        sentiment={
            "polarity": result.sentiment_score,
            "classification": "positive" if result.sentiment_score > 0 else "negative"
        } if result.sentiment_score is not None else None,
        entities=result.entities,
        topics=result.topics,
        difficulty={"score": result.difficulty_score} if result.difficulty_score else None,
        summary=result.summary,
        created_at=result.created_at
    )


@router.get("/results")
async def list_analysis_results(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List recent analysis results.
    """
    results = db.query(AnalysisResult)\
        .order_by(AnalysisResult.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    return {
        "results": [
            {
                "id": r.id,
                "preview": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                "sentiment_score": r.sentiment_score,
                "topics_count": len(r.topics) if r.topics else 0,
                "entities_count": len(r.entities) if r.entities else 0,
                "created_at": r.created_at
            }
            for r in results
        ],
        "total": db.query(AnalysisResult).count()
    }


@router.get("/statistics")
async def get_analysis_statistics(db: Session = Depends(get_db)):
    """
    Get analysis statistics.
    """
    total_analyses = db.query(AnalysisResult).count()

    # Calculate average sentiment
    avg_sentiment = db.query(AnalysisResult).filter(
        AnalysisResult.sentiment_score.isnot(None)
    ).with_entities(
        db.func.avg(AnalysisResult.sentiment_score)
    ).scalar()

    # Get most common entities
    # Note: This is simplified; in production, aggregate from JSON field
    recent_entities = db.query(AnalysisResult).filter(
        AnalysisResult.entities.isnot(None)
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
        "last_analysis": db.query(AnalysisResult)\
            .order_by(AnalysisResult.created_at.desc())\
            .first()\
            .created_at if total_analyses > 0 else None
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
            db_result = AnalysisResult(
                content=text[:500],
                scraped_content_id=content.id,
                **result,
                metadata={
                    "batch_analysis": True,
                    "source_url": content.url
                }
            )
            db.add(db_result)

        except Exception as e:
            print(f"Error analyzing content {content.id}: {str(e)}")
            continue

    db.commit()