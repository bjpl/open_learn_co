# Phase 2: Database Index Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying performance indexes to achieve <50ms p95 latency for common queries.

**Performance Targets:**
- Common queries: <50ms (p95)
- Search queries: <200ms (p95)
- Analytics queries: <500ms (p95)
- Index size: <20% of table size

## Files Created

1. **SQL Migration**: `backend/scripts/add_performance_indexes.sql`
   - Direct SQL script with all index definitions
   - Includes rollback commands
   - Can be run independently

2. **Alembic Migration**: `backend/alembic/versions/002_add_performance_indexes.py`
   - Professional Alembic migration
   - Zero-downtime deployment with CONCURRENTLY
   - Upgrade/downgrade support

3. **Performance Tests**: `backend/tests/performance/test_query_performance.py`
   - Comprehensive query benchmarks
   - Validates <50ms p95 latency
   - Generates performance reports

4. **Updated Models**: `backend/app/database/models.py`
   - Enhanced documentation of all indexes
   - Index purpose and expected impact

## Index Summary

### Total Indexes Created: 57

**ScrapedContent Table (13 indexes):**
- Single-column: source, category, scraped_at, is_paywall (partial)
- Composite: source+category+published, difficulty+published
- Full-text: title (GIN), content (GIN), combined (GIN)
- JSON: tags, entities
- Covering: list queries

**Users Table (9 indexes):**
- Authentication: email (unique, case-insensitive), username (unique)
- Session: refresh_token, refresh_expires (partial)
- Activity: last_login, created_at, is_active (partial)
- Filtering: role, spanish_level (partial)

**ContentAnalysis Table (7 indexes):**
- Foreign key: content_id
- Sentiment: sentiment_score (partial), sentiment_label
- Time-series: content+processed, processed_at
- JSON: entities, topics

**ExtractedVocabulary Table (7 indexes):**
- Basic: content_id, word, pos_tag, frequency
- Filtering: difficulty (partial), colombian (partial)
- Composite: word+difficulty

**UserVocabulary Table (6 indexes):**
- Spaced repetition: user+review (partial), next_review (partial)
- Mastery: user+mastery
- Lookups: user_id, vocabulary_id
- Covering: mastery queries

**LearningSession Table (6 indexes):**
- User tracking: user+started, user+date
- Filtering: type, active (partial)
- JSON: content_ids, vocabulary_ids

**UserContentProgress Table (5 indexes):**
- Composite: user+content, user+accessed, user+completed
- Lookups: content_id
- Filtering: read_percentage (partial)

**IntelligenceAlerts Table (7 indexes):**
- Status: status (partial), type+severity+created
- Time: created_at, expires_at (partial)
- User: acknowledged_by (partial)
- JSON: keywords, entities

## Deployment Options

### Option 1: Alembic Migration (Recommended)

**Advantages:**
- Version-controlled database changes
- Automatic upgrade/downgrade
- Integrates with existing migration workflow

**Steps:**

```bash
# 1. Review the migration
cat backend/alembic/versions/002_add_performance_indexes.py

# 2. Run upgrade
cd backend
alembic upgrade head

# 3. Verify indexes were created
psql -d openlearn_colombia -c "
  SELECT indexname, tablename
  FROM pg_indexes
  WHERE schemaname = 'public'
  ORDER BY tablename, indexname;
"

# 4. Check index sizes
psql -d openlearn_colombia -f scripts/check_index_sizes.sql
```

**Rollback if needed:**
```bash
alembic downgrade -1
```

### Option 2: Direct SQL Script

**Advantages:**
- Simple execution
- No Alembic setup required
- Easy to customize

**Steps:**

```bash
# 1. Review the script
cat backend/scripts/add_performance_indexes.sql

# 2. Execute with psql
psql -d openlearn_colombia -f backend/scripts/add_performance_indexes.sql

# 3. Verify creation (same as above)
```

**Rollback:**
```bash
# Use the rollback commands at the end of the SQL file
psql -d openlearn_colombia -c "
  DROP INDEX CONCURRENTLY IF EXISTS idx_scraped_content_source;
  -- (continue with all DROP commands)
"
```

## Zero-Downtime Deployment

All indexes use `CREATE INDEX CONCURRENTLY` which:
- Does not lock the table
- Allows reads and writes during creation
- Takes longer but prevents downtime

**Important Notes:**
1. Cannot run inside a transaction block
2. Alembic automatically handles this with `postgresql_concurrently=True`
3. If index creation fails, it may leave an invalid index (check with `\d table_name`)

## Performance Testing

### Pre-Deployment Baseline

```bash
# Run performance tests BEFORE creating indexes
cd backend
pytest tests/performance/test_query_performance.py -v -s > performance_before.txt
```

### Post-Deployment Validation

```bash
# Run tests AFTER creating indexes
pytest tests/performance/test_query_performance.py -v -s > performance_after.txt

# Compare results
diff performance_before.txt performance_after.txt
```

### Expected Results

**Before indexes:**
- Most queries: 200-1000ms
- Some queries: >2000ms

**After indexes:**
- Common queries: 10-50ms (80-95% improvement)
- Search queries: 50-200ms
- Analytics: 100-500ms

### Continuous Monitoring

```sql
-- Check index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT 20;

-- Find unused indexes (after 1 week in production)
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Index Maintenance

### Monitoring

1. **Index bloat:** Run `REINDEX CONCURRENTLY` if needed
2. **Usage statistics:** Review monthly with pg_stat_user_indexes
3. **Query performance:** Monitor with pg_stat_statements

### Optimization

```sql
-- Update table statistics
ANALYZE scraped_content;
ANALYZE users;
ANALYZE content_analysis;
-- etc.

-- Vacuum tables (after bulk inserts)
VACUUM ANALYZE scraped_content;
```

### Cleanup

Remove unused indexes after 30 days if idx_scan = 0:

```sql
-- Be careful! Only drop if truly unused
DROP INDEX CONCURRENTLY IF EXISTS idx_unused_example;
```

## Troubleshooting

### Index Creation Failed

```sql
-- Check for invalid indexes
SELECT indexname, indisvalid
FROM pg_index
JOIN pg_class ON pg_index.indexrelid = pg_class.oid
WHERE NOT indisvalid;

-- Drop and recreate invalid indexes
DROP INDEX CONCURRENTLY idx_invalid_index;
CREATE INDEX CONCURRENTLY idx_invalid_index ON table_name(column_name);
```

### Query Still Slow

```sql
-- Check if index is being used
EXPLAIN ANALYZE
SELECT * FROM scraped_content
WHERE source = 'El Tiempo'
ORDER BY published_date DESC
LIMIT 20;

-- Look for "Index Scan using idx_..." in output
-- If seeing "Seq Scan", index is not being used
```

### Index Not Being Used

Possible causes:
1. Query planner thinks seq scan is faster (small table)
2. Statistics out of date (run ANALYZE)
3. Query doesn't match index pattern
4. Data distribution makes index inefficient

## Security Considerations

1. **Database user permissions:**
   ```sql
   -- Ensure migration user has CREATE INDEX privilege
   GRANT CREATE ON SCHEMA public TO migration_user;
   ```

2. **Connection pooling:**
   - CONCURRENTLY requires its own connection
   - Ensure connection pool has available connections

3. **Monitoring:**
   - Watch for long-running index builds
   - Monitor disk space (indexes need space)

## Success Criteria

- [ ] All 57 indexes created successfully
- [ ] No invalid indexes (check pg_index)
- [ ] Common queries <50ms p95
- [ ] Search queries <200ms p95
- [ ] Analytics queries <500ms p95
- [ ] Index size <20% of table size
- [ ] Zero downtime during deployment
- [ ] All performance tests passing

## Rollback Plan

If performance degrades or issues occur:

1. **Immediate rollback:**
   ```bash
   alembic downgrade -1
   ```

2. **Partial rollback** (drop specific index):
   ```sql
   DROP INDEX CONCURRENTLY idx_problematic_index;
   ```

3. **Verify rollback:**
   ```bash
   pytest tests/performance/test_query_performance.py
   ```

## Next Steps (Phase 3)

After successful deployment:
1. Monitor query performance for 1 week
2. Identify any remaining slow queries
3. Add additional indexes if needed
4. Implement query caching (Redis)
5. Add database connection pooling optimization
6. Set up automated performance monitoring

## Support

For issues or questions:
- Review performance test results
- Check PostgreSQL logs: `/var/log/postgresql/`
- Monitor with: `pg_stat_activity`, `pg_stat_user_indexes`
- Reference: PostgreSQL documentation on indexes

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Performance Baseline:** _____________
**Post-Deployment Performance:** _____________
**Status:** [ ] Success [ ] Partial [ ] Rollback
