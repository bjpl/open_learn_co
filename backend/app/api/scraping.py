"""
API endpoints for web scraping operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.database.models import ScrapedContent
from scrapers.sources.media.el_tiempo import ElTiempoScraper
from scrapers.sources.strategic_sources import STRATEGIC_SOURCES, get_sources_by_priority

router = APIRouter()


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

    # For now, only El Tiempo is implemented
    if "El Tiempo" in source_name:
        background_tasks.add_task(scrape_el_tiempo, source_config, db)
        return {
            "status": "triggered",
            "source": source_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "status": "not_implemented",
            "source": source_name,
            "message": "Scraper for this source is not yet implemented"
        }


async def scrape_el_tiempo(source_config: Dict[str, Any], db: AsyncSession):
    """Background task to scrape El Tiempo"""
    try:
        async with ElTiempoScraper(source_config) as scraper:
            articles = await scraper.scrape()

            # Save to database
            for article in articles:
                db.add(article)

            await db.commit()

    except Exception as e:
        await db.rollback()
        # Log error - in production, send to monitoring
        print(f"Scraping error: {str(e)}")


@router.get("/status")
async def get_scraping_status(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get current scraping status and statistics"""

    # Get recent scraping activity
    recent_count = await db.execute(
        "SELECT COUNT(*) FROM scraped_content WHERE scraped_at > NOW() - INTERVAL '24 hours'"
    )

    # Get source distribution
    source_stats = await db.execute(
        "SELECT source, COUNT(*) as count FROM scraped_content GROUP BY source"
    )

    return {
        "status": "operational",
        "recent_articles_24h": recent_count.scalar(),
        "source_distribution": [
            {"source": row[0], "count": row[1]}
            for row in source_stats
        ],
        "last_update": datetime.utcnow().isoformat()
    }


@router.get("/content")
async def get_scraped_content(
    source: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> List[Dict[str, Any]]:
    """Get scraped content with filters"""

    query = "SELECT * FROM scraped_content WHERE 1=1"
    params = {}

    if source:
        query += " AND source = :source"
        params["source"] = source

    if category:
        query += " AND category = :category"
        params["category"] = category

    query += " ORDER BY published_date DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(query, params)

    return [dict(row) for row in result]