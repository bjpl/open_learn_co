"""
API endpoints for web scraping operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.database.models import ScrapedContent
from scrapers.sources.media.el_tiempo import ElTiempoScraper
from scrapers.sources.media.el_espectador import ElEspectadorScraper
from scrapers.sources.media.semana import SemanaScraper
from scrapers.sources.media.portafolio import PortafolioScraper
from scrapers.sources.strategic_sources import STRATEGIC_SOURCES, get_sources_by_priority

router = APIRouter()

# Scraper registry mapping source names to scraper classes
SCRAPER_REGISTRY = {
    'El Tiempo': ElTiempoScraper,
    'El Espectador': ElEspectadorScraper,
    'Semana': SemanaScraper,
    'Portafolio': PortafolioScraper,
}


@router.get("/sources")
async def list_sources(
    category: Optional[str] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """List all configured scraping sources"""

    if priority:
        sources = get_sources_by_priority(priority)
        return {
            "total": len(sources),
            "priority": priority,
            "sources": sources
        }

    if category and category in STRATEGIC_SOURCES:
        return {
            "category": category,
            "sources": STRATEGIC_SOURCES[category]
        }

    return {
        "total_categories": len(STRATEGIC_SOURCES),
        "categories": list(STRATEGIC_SOURCES.keys()),
        "sources": STRATEGIC_SOURCES
    }


@router.post("/trigger/{source_name}")
async def trigger_scraping(
    source_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Trigger scraping for a specific source"""

    # Find source configuration
    source_config = None
    for category, sources in STRATEGIC_SOURCES.items():
        for source in sources:
            if source.get("name") == source_name:
                source_config = source
                source_config["category"] = category
                break

    if not source_config:
        raise HTTPException(status_code=404, detail=f"Source {source_name} not found")

    # Check if scraper is implemented
    scraper_class = SCRAPER_REGISTRY.get(source_name)
    if scraper_class:
        background_tasks.add_task(run_scraper, scraper_class, source_config, db)
        return {
            "status": "triggered",
            "source": source_name,
            "scraper": scraper_class.__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "status": "not_implemented",
            "source": source_name,
            "message": f"Scraper for {source_name} is not yet implemented",
            "available_scrapers": list(SCRAPER_REGISTRY.keys())
        }


async def run_scraper(scraper_class, source_config: Dict[str, Any], db: AsyncSession):
    """Background task to run any scraper"""
    try:
        async with scraper_class(source_config) as scraper:
            articles = await scraper.scrape()

            # Save to database using ORM
            for article in articles:
                db.add(article)

            await db.commit()

            # Log success
            print(f"Successfully scraped {len(articles)} articles from {source_config.get('name', 'Unknown')}")

    except Exception as e:
        await db.rollback()
        # Log error - in production, send to monitoring
        print(f"Scraping error for {source_config.get('name', 'Unknown')}: {str(e)}")


@router.get("/status")
async def get_scraping_status(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get current scraping status and statistics"""
    try:
        # Get recent scraping activity (last 24 hours) using ORM
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_count_query = select(func.count(ScrapedContent.id)).where(
            ScrapedContent.scraped_at > twenty_four_hours_ago
        )
        recent_count_result = await db.execute(recent_count_query)
        recent_count = recent_count_result.scalar() or 0

        # Get source distribution using ORM
        source_stats_query = select(
            ScrapedContent.source,
            func.count(ScrapedContent.id).label('count')
        ).group_by(ScrapedContent.source)
        source_stats_result = await db.execute(source_stats_query)
        source_stats = source_stats_result.all()

        # Get total articles count
        total_count_query = select(func.count(ScrapedContent.id))
        total_count_result = await db.execute(total_count_query)
        total_count = total_count_result.scalar() or 0

        # Get last scraping timestamp
        last_scrape_query = select(func.max(ScrapedContent.scraped_at))
        last_scrape_result = await db.execute(last_scrape_query)
        last_scrape = last_scrape_result.scalar()

        return {
            "status": "operational",
            "total_articles": total_count,
            "recent_articles_24h": recent_count,
            "last_scrape": last_scrape.isoformat() if last_scrape else None,
            "source_distribution": [
                {"source": row.source, "count": row.count}
                for row in source_stats
            ],
            "available_scrapers": list(SCRAPER_REGISTRY.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching scraping status: {str(e)}"
        )


@router.get("/content")
async def get_scraped_content(
    source: Optional[str] = None,
    category: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 50,
    min_difficulty: Optional[float] = None,
    max_difficulty: Optional[float] = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get scraped content with cursor-based pagination (news feed style)"""
    try:
        from app.core.pagination import CursorPaginationParams, paginate_cursor_async, create_cursor

        # Build query using ORM
        query = select(ScrapedContent)

        # Apply filters
        if source:
            query = query.where(ScrapedContent.source == source)

        if category:
            query = query.where(ScrapedContent.category == category)

        if min_difficulty is not None:
            query = query.where(ScrapedContent.difficulty_score >= min_difficulty)

        if max_difficulty is not None:
            query = query.where(ScrapedContent.difficulty_score <= max_difficulty)

        # Apply cursor-based pagination (for real-time news feed)
        pagination_params = CursorPaginationParams(cursor=cursor, limit=min(limit, 100))
        articles, metadata = await paginate_cursor_async(
            query,
            db,
            pagination_params,
            sort_field="published_date",
            sort_order="desc"
        )

        # Convert to dict format
        articles_data = [
            {
                "id": article.id,
                "source": article.source,
                "source_url": article.source_url,
                "category": article.category,
                "title": article.title,
                "subtitle": article.subtitle,
                "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                "author": article.author,
                "word_count": article.word_count,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None,
                "difficulty_score": article.difficulty_score,
                "tags": article.tags,
                "colombian_entities": article.colombian_entities,
                "is_paywall": article.is_paywall
            }
            for article in articles
        ]

        return {
            "items": articles_data,
            "next_cursor": metadata.next_cursor,
            "has_more": metadata.has_more,
            "count": metadata.count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching content: {str(e)}"
        )