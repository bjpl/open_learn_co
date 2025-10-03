# Export API Quick Start Guide

## Overview

The OpenLearn Colombia platform supports exporting data in multiple formats:
- **CSV** - For data analysis and Excel
- **JSON** - For API integration
- **JSONL** - For large datasets (streaming)
- **PDF** - For reports and presentations
- **Excel** - For business analysis with formatted worksheets

---

## Quick Examples

### 1. Export Articles to CSV

```bash
curl -X POST "http://localhost:8000/api/export/articles" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "limit": 100
  }'
```

**Response**:
```json
{
  "job_id": "abc123",
  "status": "queued",
  "estimated_time": 10,
  "message": "Export job created. Exporting 100 articles as csv."
}
```

### 2. Check Export Status

```bash
curl -X GET "http://localhost:8000/api/export/status/abc123"
```

**Response**:
```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "total": 100,
  "format": "csv",
  "record_count": 100,
  "file_ready": true
}
```

### 3. Download Export File

```bash
curl -X GET "http://localhost:8000/api/export/download/abc123" \
  --output articles.csv
```

---

## All Export Endpoints

### Export Articles

```http
POST /api/export/articles
Content-Type: application/json

{
  "format": "csv",              // csv, json, jsonl, pdf, excel
  "filters": {                   // Optional
    "category": "Politics",
    "sentiment": "positive",
    "date_from": "2025-01-01"
  },
  "fields": [                    // Optional - select specific fields
    "title",
    "summary",
    "category",
    "sentiment_score"
  ],
  "limit": 1000                  // Optional - max records
}
```

### Export Vocabulary

```http
POST /api/export/vocabulary
Content-Type: application/json

{
  "format": "excel",
  "filters": {
    "difficulty_level": "B1",
    "part_of_speech": "verb"
  },
  "limit": 500
}
```

### Export Analysis Results

```http
POST /api/export/analysis
Content-Type: application/json

{
  "format": "json",
  "filters": {
    "analysis_type": "sentiment",
    "date_from": "2025-01-01"
  },
  "limit": 200
}
```

### Export Custom Data

```http
POST /api/export/custom
Content-Type: application/json

{
  "format": "pdf",
  "limit": 50
}
```

**With data parameter**:
```python
import requests

data = [
    {"id": 1, "name": "Item 1", "value": 100},
    {"id": 2, "name": "Item 2", "value": 200}
]

response = requests.post(
    "http://localhost:8000/api/export/custom",
    json={
        "format": "csv",
        "limit": 10
    },
    params={"data": data}
)
```

---

## Format-Specific Details

### CSV Export
- **Max Records**: 50,000
- **Encoding**: UTF-8 with BOM (Excel-compatible)
- **Nested Data**: Flattened or JSON-encoded
- **Use Case**: Excel analysis, data processing

**Features**:
- Quoted text fields
- Date formatting (YYYY-MM-DD HH:MM:SS)
- Handles special characters
- Column ordering for articles/vocabulary

### JSON Export
- **Max Records**: 100,000
- **Format**: Pretty-printed (indent=2)
- **Structure**: Metadata + data array
- **Use Case**: API integration, archival

**Structure**:
```json
{
  "metadata": {
    "exported_at": "2025-10-03T14:30:22.123456",
    "total_records": 100,
    "version": "1.0"
  },
  "data": [...]
}
```

### JSONL Export
- **Max Records**: 1,000,000
- **Format**: One JSON object per line
- **Use Case**: Big data, streaming

**Features**:
- Memory-efficient
- Line-by-line processing
- Metadata as first line

### PDF Export
- **Max Records**: 100 (performance limit)
- **Page Size**: A4 portrait
- **Use Case**: Reports, presentations

**Features**:
- Professional styling
- Summary statistics
- Color-coded tables
- Page headers/footers

### Excel Export
- **Max Records**: 100,000
- **Format**: .xlsx multi-sheet
- **Use Case**: Business analysis

**Features**:
- Multiple sheets (Data, Summary, Metadata)
- Formatted headers
- Auto-sized columns
- Freeze panes
- Auto-filters
- Conditional formatting

---

## Limits and Quotas

### Per-User Limits
- **Exports per hour**: 10
- **Concurrent jobs**: 5
- **Max file size**: 50 MB

### Per-Format Limits
| Format | Max Rows | Est. Time (1K records) |
|--------|----------|------------------------|
| CSV | 50,000 | 2 seconds |
| JSON | 100,000 | 3 seconds |
| JSONL | 1,000,000 | 2 seconds |
| PDF | 100 | 10 seconds |
| Excel | 100,000 | 5 seconds |

### File Retention
- **Auto-delete**: After 24 hours
- **Cleanup**: Automatic background job

---

## Error Handling

### Common Errors

**400 - Bad Request**:
```json
{
  "detail": "Export size exceeds limit. Maximum 50000 records for csv format."
}
```

**404 - Not Found**:
```json
{
  "detail": "Export job not found"
}
```

**429 - Rate Limit**:
```json
{
  "detail": "Export rate limit exceeded. Maximum 10 exports per hour."
}
```

---

## Python Client Example

```python
import requests
import time

class ExportClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def export_articles(self, format="csv", limit=100, filters=None):
        """Create export job"""
        response = requests.post(
            f"{self.base_url}/api/export/articles",
            json={
                "format": format,
                "limit": limit,
                "filters": filters or {}
            }
        )
        response.raise_for_status()
        return response.json()["job_id"]

    def wait_for_export(self, job_id, timeout=60):
        """Wait for export to complete"""
        start = time.time()

        while time.time() - start < timeout:
            status = self.get_status(job_id)

            if status["status"] == "completed":
                return True
            elif status["status"] == "failed":
                raise Exception(f"Export failed: {status['error']}")

            time.sleep(1)

        raise TimeoutError("Export did not complete in time")

    def get_status(self, job_id):
        """Get export status"""
        response = requests.get(
            f"{self.base_url}/api/export/status/{job_id}"
        )
        response.raise_for_status()
        return response.json()

    def download(self, job_id, output_file):
        """Download export file"""
        response = requests.get(
            f"{self.base_url}/api/export/download/{job_id}",
            stream=True
        )
        response.raise_for_status()

        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# Usage
client = ExportClient()

# Start export
job_id = client.export_articles(
    format="csv",
    limit=1000,
    filters={"category": "Politics"}
)

# Wait for completion
client.wait_for_export(job_id)

# Download file
client.download(job_id, "articles.csv")
```

---

## JavaScript/TypeScript Example

```typescript
interface ExportRequest {
  format: 'csv' | 'json' | 'jsonl' | 'pdf' | 'excel';
  filters?: Record<string, any>;
  fields?: string[];
  limit?: number;
}

class ExportClient {
  constructor(private baseUrl: string = 'http://localhost:8000') {}

  async exportArticles(request: ExportRequest): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/export/articles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    const data = await response.json();
    return data.job_id;
  }

  async getStatus(jobId: string) {
    const response = await fetch(`${this.baseUrl}/api/export/status/${jobId}`);
    return await response.json();
  }

  async waitForExport(jobId: string, timeout: number = 60000): Promise<void> {
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const status = await this.getStatus(jobId);

      if (status.status === 'completed') {
        return;
      } else if (status.status === 'failed') {
        throw new Error(`Export failed: ${status.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    throw new Error('Export timeout');
  }

  async download(jobId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/export/download/${jobId}`);
    return await response.blob();
  }
}

// Usage
const client = new ExportClient();

const jobId = await client.exportArticles({
  format: 'csv',
  limit: 1000,
  filters: { category: 'Politics' }
});

await client.waitForExport(jobId);

const blob = await client.download(jobId);
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'articles.csv';
a.click();
```

---

## Best Practices

### 1. Use Appropriate Formats
- **CSV**: For Excel analysis (≤50K rows)
- **JSON**: For programmatic use (≤100K rows)
- **JSONL**: For very large datasets (>100K rows)
- **PDF**: For presentations (≤100 rows)
- **Excel**: For business dashboards (≤100K rows)

### 2. Apply Filters Early
```json
{
  "format": "csv",
  "filters": {
    "category": "Politics",
    "date_from": "2025-01-01",
    "sentiment": "positive"
  }
}
```

### 3. Select Only Needed Fields
```json
{
  "format": "csv",
  "fields": ["title", "summary", "category"]
}
```

### 4. Respect Rate Limits
- Maximum 10 exports per hour
- Poll status every 1-2 seconds
- Don't create duplicate jobs

### 5. Handle Errors Gracefully
```python
try:
    job_id = client.export_articles(...)
    client.wait_for_export(job_id)
    client.download(job_id, "output.csv")
except HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded. Try again later.")
    else:
        print(f"Export failed: {e}")
```

---

## Troubleshooting

### Export Job Stuck in "Processing"
- Check `/api/export/status/{job_id}` for progress
- Wait for estimated_time before checking
- Max processing time: 5 minutes

### File Download Failed
- Verify job status is "completed"
- Check file hasn't expired (24-hour retention)
- Ensure proper content-type header support

### Rate Limit Exceeded
- Wait 1 hour for quota reset
- Check current usage
- Consider batching exports

### Format Size Exceeded
- Use JSONL for very large datasets
- Apply filters to reduce record count
- Split into multiple exports

---

## Advanced Usage

### Scheduled Exports
```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=2)
def daily_export():
    job_id = client.export_articles(
        format="csv",
        filters={"date": "yesterday"}
    )
    client.wait_for_export(job_id)
    client.download(job_id, f"daily_export_{date.today()}.csv")

scheduler.start()
```

### Batch Processing
```python
def export_by_category(categories):
    jobs = []

    for category in categories:
        job_id = client.export_articles(
            format="csv",
            filters={"category": category}
        )
        jobs.append((category, job_id))

    for category, job_id in jobs:
        client.wait_for_export(job_id)
        client.download(job_id, f"{category}.csv")
```

---

## Support

For issues or questions:
- API Documentation: http://localhost:8000/docs
- GitHub Issues: [Repository URL]
- Implementation: `/backend/docs/export-implementation-summary.md`
