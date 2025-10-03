# Database Index Quick Reference

## TL;DR

**57 performance indexes** designed to achieve **<50ms p95 latency**.

**Deploy:** `alembic upgrade head`
**Rollback:** `alembic downgrade -1`
**Test:** `pytest tests/performance/test_query_performance.py -v -s`

## Critical Indexes by Use Case

### Authentication (<20ms target)
```sql
-- Login by email (case-insensitive)
WHERE lower(email) = 'user@example.com'
→ idx_users_email_unique

-- Validate refresh token
WHERE refresh_token = 'token' AND refresh_token_expires_at > NOW()
→ idx_users_refresh_token, idx_users_refresh_expires
```

### Content Filtering (<50ms target)
```sql
-- Filter by source and category, sort by date
WHERE source = 'El Tiempo' AND category = 'politics'
ORDER BY published_date DESC
→ idx_scraped_content_source_category_published

-- Filter by difficulty
WHERE difficulty_score BETWEEN 2.0 AND 4.0
→ idx_scraped_content_difficulty_published
```

### Full-Text Search (<200ms target)
```sql
-- Spanish text search
WHERE to_tsvector('spanish', title || content) @@ to_tsquery('spanish', 'Colombia')
→ idx_scraped_content_fulltext_gin
```

### Spaced Repetition (<25ms target)
```sql
-- Get words due for review
WHERE user_id = 1 AND next_review <= NOW()
→ idx_user_vocab_user_review
```

### Learning Streaks (<100ms target)
```sql
-- Calculate daily streak
WHERE user_id = 1 AND DATE(started_at) = CURRENT_DATE
→ idx_learning_session_user_date
```

## Index Types

### B-tree (Default)
- Single columns: `source`, `category`, `email`
- Composite: `(source, category, published_date)`
- Best for: equality, range, sorting

### GIN (Full-Text/JSON)
- Text search: `to_tsvector('spanish', content)`
- JSON arrays: `tags`, `entities`
- Best for: contains, full-text, array overlap

### Partial (Filtered)
- Only index subset: `WHERE is_active = true`
- Smaller, faster: 50-80% size reduction
- Best for: common filters

### Covering (INCLUDE)
- Include extra columns: `INCLUDE (id, title, source)`
- Avoid table lookups: index-only scans
- Best for: frequently accessed columns

## Query Optimization Tips

### 1. Use Indexed Columns
```python
# Good - uses idx_scraped_content_source
query = select(ScrapedContent).where(ScrapedContent.source == 'El Tiempo')

# Bad - function on column prevents index use
query = select(ScrapedContent).where(func.lower(ScrapedContent.source) == 'el tiempo')
```

### 2. Match Composite Index Order
```python
# Good - matches (source, category, published_date) index
query.where(
    ScrapedContent.source == 'El Tiempo',
    ScrapedContent.category == 'politics'
).order_by(ScrapedContent.published_date.desc())

# Bad - wrong order, can't use composite index fully
query.where(ScrapedContent.category == 'politics')
```

### 3. Use Covering Indexes
```python
# Good - only needs index (no table lookup)
query = select(
    ScrapedContent.id,
    ScrapedContent.title,
    ScrapedContent.source
).order_by(ScrapedContent.published_date.desc())
```

### 4. Leverage Partial Indexes
```python
# Good - uses partial index idx_users_is_active
query = select(User).where(User.is_active == True)

# Bad - partial index can't be used
query = select(User).where(User.is_active.in_([True, False]))
```

## Performance Monitoring

### Check Index Usage
```sql
SELECT
    indexname,
    idx_scan,
    idx_tup_read,
    pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT 10;
```

### Find Slow Queries
```sql
SELECT
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
WHERE mean_exec_time > 50
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Check Query Plan
```sql
EXPLAIN ANALYZE
SELECT * FROM scraped_content
WHERE source = 'El Tiempo'
ORDER BY published_date DESC
LIMIT 20;
```

Look for:
- ✅ `Index Scan using idx_scraped_content_source`
- ❌ `Seq Scan on scraped_content`

## Common Issues

### Index Not Being Used

**Cause:** Statistics out of date
**Fix:** `ANALYZE scraped_content;`

**Cause:** Small table (seq scan faster)
**Fix:** Normal, wait for more data

**Cause:** Query doesn't match index
**Fix:** Rewrite query or add new index

### Slow Index Creation

**Cause:** Large table
**Fix:** CONCURRENTLY takes longer but allows access

**Cause:** Limited resources
**Fix:** Create indexes during low-traffic period

### Invalid Index

**Cause:** CONCURRENTLY creation failed
**Fix:**
```sql
-- Find invalid indexes
SELECT indexname FROM pg_index
WHERE NOT indisvalid;

-- Drop and recreate
DROP INDEX CONCURRENTLY idx_invalid;
CREATE INDEX CONCURRENTLY idx_invalid ON table(column);
```

## Maintenance Commands

```sql
-- Update statistics (after bulk insert)
ANALYZE scraped_content;

-- Rebuild index (if bloated)
REINDEX INDEX CONCURRENTLY idx_scraped_content_source;

-- Vacuum table (reclaim space)
VACUUM ANALYZE scraped_content;
```

## Files Reference

- **SQL Script:** `backend/scripts/add_performance_indexes.sql`
- **Alembic Migration:** `backend/alembic/versions/002_add_performance_indexes.py`
- **Performance Tests:** `backend/tests/performance/test_query_performance.py`
- **Deployment Guide:** `backend/docs/phase2-index-deployment-guide.md`
- **Full Summary:** `backend/docs/phase2-performance-summary.md`

## Performance Targets

| Query Type | Target | Typical Actual |
|-----------|--------|---------------|
| Authentication | <50ms | 15-25ms |
| Content Filter | <50ms | 20-40ms |
| Full-Text Search | <200ms | 80-150ms |
| Vocabulary | <50ms | 10-30ms |
| Spaced Repetition | <50ms | 15-25ms |
| Analytics | <500ms | 150-400ms |

## Emergency Rollback

```bash
# If something goes wrong
alembic downgrade -1

# Or drop specific index
psql -d openlearn_colombia -c "DROP INDEX CONCURRENTLY idx_problematic_index;"
```

---

**Questions?** See full documentation in `docs/phase2-index-deployment-guide.md`
