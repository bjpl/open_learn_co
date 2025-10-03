"""
Database health monitoring and diagnostics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging
import asyncio
import time

from app.database.connection import (
    engine,
    async_engine,
    get_pool_status,
    get_async_pool_status,
    check_db_connection,
    check_async_db_connection
)

logger = logging.getLogger(__name__)

# Query performance tracking
query_metrics = {
    "total_queries": 0,
    "slow_queries": 0,
    "failed_queries": 0,
    "average_query_time": 0.0,
    "slow_query_threshold": 1000.0  # milliseconds
}

# Connection leak detection
connection_checkouts = {}
CONNECTION_LEAK_THRESHOLD = 300  # seconds


class DatabaseHealthChecker:
    """Database health check and monitoring utilities"""

    @staticmethod
    async def comprehensive_health_check() -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        start_time = time.time()

        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "duration_ms": 0
        }

        # 1. Connection check
        try:
            conn_healthy = await check_async_db_connection()
            health_status["checks"]["connection"] = {
                "status": "healthy" if conn_healthy else "unhealthy",
                "message": "Database connection successful" if conn_healthy else "Connection failed"
            }
            if not conn_healthy:
                health_status["overall_status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["connection"] = {
                "status": "unhealthy",
                "message": f"Connection check failed: {str(e)}"
            }
            health_status["overall_status"] = "unhealthy"

        # 2. Pool status check
        try:
            pool_status = await get_async_pool_status()
            health_status["checks"]["connection_pool"] = {
                "status": "healthy",
                "details": pool_status
            }

            # Check for pool saturation
            if pool_status.get("overflow", 0) > 0:
                health_status["checks"]["connection_pool"]["warning"] = "Pool overflow in use"

            # Check for potential leaks
            checked_out = pool_status.get("checked_out", 0)
            total_capacity = pool_status.get("total_capacity", 0)
            if checked_out > total_capacity * 0.8:
                health_status["checks"]["connection_pool"]["warning"] = "Pool utilization > 80%"

        except Exception as e:
            health_status["checks"]["connection_pool"] = {
                "status": "error",
                "message": f"Pool check failed: {str(e)}"
            }

        # 3. Query performance check
        try:
            query_start = time.time()
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            query_time = (time.time() - query_start) * 1000  # ms

            health_status["checks"]["query_performance"] = {
                "status": "healthy" if query_time < 100 else "degraded",
                "query_time_ms": round(query_time, 2),
                "threshold_ms": 100
            }
        except Exception as e:
            health_status["checks"]["query_performance"] = {
                "status": "unhealthy",
                "message": f"Query test failed: {str(e)}"
            }
            health_status["overall_status"] = "unhealthy"

        # 4. Database version check
        try:
            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                health_status["checks"]["database_version"] = {
                    "status": "healthy",
                    "version": version
                }
        except Exception as e:
            health_status["checks"]["database_version"] = {
                "status": "error",
                "message": f"Version check failed: {str(e)}"
            }

        # 5. Connection leak detection
        leak_check = DatabaseHealthChecker.detect_connection_leaks()
        health_status["checks"]["connection_leaks"] = leak_check
        if leak_check["potential_leaks"] > 0:
            health_status["overall_status"] = "degraded"

        # Calculate total duration
        health_status["duration_ms"] = round((time.time() - start_time) * 1000, 2)

        return health_status

    @staticmethod
    def detect_connection_leaks() -> Dict[str, Any]:
        """Detect potential connection leaks"""
        current_time = time.time()
        potential_leaks = 0
        leak_details = []

        for conn_id, checkout_time in list(connection_checkouts.items()):
            duration = current_time - checkout_time
            if duration > CONNECTION_LEAK_THRESHOLD:
                potential_leaks += 1
                leak_details.append({
                    "connection_id": conn_id,
                    "duration_seconds": round(duration, 2)
                })

        return {
            "status": "healthy" if potential_leaks == 0 else "warning",
            "potential_leaks": potential_leaks,
            "leak_threshold_seconds": CONNECTION_LEAK_THRESHOLD,
            "details": leak_details[:10]  # Limit to 10 entries
        }

    @staticmethod
    async def get_database_statistics() -> Dict[str, Any]:
        """Get database statistics and metrics"""
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "pool_metrics": {},
            "query_metrics": query_metrics.copy(),
            "tables": {}
        }

        # Get pool statistics
        try:
            stats["pool_metrics"] = await get_async_pool_status()
        except Exception as e:
            logger.error(f"Failed to get pool metrics: {str(e)}")
            stats["pool_metrics"] = {"error": str(e)}

        # Get table statistics
        try:
            async with async_engine.connect() as conn:
                # Get table sizes
                result = await conn.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """))

                tables = []
                for row in result:
                    tables.append({
                        "schema": row[0],
                        "name": row[1],
                        "size": row[2]
                    })
                stats["tables"] = tables
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            stats["tables"] = {"error": str(e)}

        return stats

    @staticmethod
    def track_query_performance(query_time_ms: float, success: bool = True):
        """Track query performance metrics"""
        query_metrics["total_queries"] += 1

        if not success:
            query_metrics["failed_queries"] += 1
            return

        # Update average query time
        current_avg = query_metrics["average_query_time"]
        total = query_metrics["total_queries"]
        query_metrics["average_query_time"] = (
            (current_avg * (total - 1) + query_time_ms) / total
        )

        # Track slow queries
        if query_time_ms > query_metrics["slow_query_threshold"]:
            query_metrics["slow_queries"] += 1
            logger.warning(
                f"Slow query detected: {query_time_ms:.2f}ms "
                f"(threshold: {query_metrics['slow_query_threshold']}ms)"
            )

    @staticmethod
    def register_connection_checkout(connection_id: str):
        """Register connection checkout for leak detection"""
        connection_checkouts[connection_id] = time.time()

    @staticmethod
    def register_connection_checkin(connection_id: str):
        """Register connection checkin"""
        connection_checkouts.pop(connection_id, None)

    @staticmethod
    async def test_connection_pool_performance() -> Dict[str, Any]:
        """Test connection pool performance under load"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "concurrent_connections": 10,
            "results": []
        }

        async def test_connection():
            start = time.time()
            try:
                async with async_engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return {
                    "success": True,
                    "duration_ms": round((time.time() - start) * 1000, 2)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "duration_ms": round((time.time() - start) * 1000, 2)
                }

        # Test concurrent connections
        tasks = [test_connection() for _ in range(10)]
        test_results = await asyncio.gather(*tasks)

        results["results"] = test_results
        results["success_count"] = sum(1 for r in test_results if r["success"])
        results["average_duration_ms"] = round(
            sum(r["duration_ms"] for r in test_results) / len(test_results), 2
        )
        results["max_duration_ms"] = max(r["duration_ms"] for r in test_results)

        return results


async def database_health_check() -> Dict[str, Any]:
    """Quick database health check endpoint"""
    return await DatabaseHealthChecker.comprehensive_health_check()


async def database_stats() -> Dict[str, Any]:
    """Get database statistics endpoint"""
    return await DatabaseHealthChecker.get_database_statistics()


async def pool_performance_test() -> Dict[str, Any]:
    """Test connection pool performance endpoint"""
    return await DatabaseHealthChecker.test_connection_pool_performance()
