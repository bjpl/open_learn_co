# Avatar Upload API Documentation

## Overview

The Avatar Upload feature provides secure image upload functionality for user profile pictures with comprehensive security validation, EXIF data stripping, and image processing.

## Security Features

### 1. File Type Validation
- **Magic Bytes Validation**: File type is validated using actual file content, not just the extension
- **Allowed Formats**: JPEG, PNG, GIF, WebP
- **Prevents**: File extension spoofing, malicious file uploads

### 2. EXIF Data Stripping
- **Privacy Protection**: All EXIF metadata is stripped from images
- **Removes**: GPS coordinates, camera info, timestamps, user comments
- **Method**: Image is reprocessed through PIL/Pillow

### 3. Size and Dimension Limits
- **Max File Size**: 5MB (configurable)
- **Max Dimensions**: 2000x2000 pixels (configurable)
- **Min Dimensions**: 50x50 pixels (configurable)
- **Prevents**: Resource exhaustion, DoS attacks

### 4. Filename Sanitization
- **Safe Filenames**: Generated using user ID, timestamp, and hash
- **Format**: `avatar_{user_id}_{timestamp}_{hash}.{ext}`
- **Prevents**: Path traversal attacks, filename conflicts

### 5. Image Reprocessing
- **Security**: All images are decoded and re-encoded
- **Prevents**: Image-based exploits, malformed image attacks
- **Format Conversion**: Handles RGBA to RGB conversion automatically

## API Endpoints

### Upload Avatar

**POST** `/api/avatars/upload`

Upload a new avatar image. Automatically replaces the previous avatar.

**Authentication**: Required (Bearer token)

**Request**:
```http
POST /api/avatars/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary image data]
```

**Response** (201 Created):
```json
{
  "avatar_url": "/api/avatars/avatar_123_1705518000000_a1b2c3d4.jpg",
  "metadata": {
    "width": 800,
    "height": 800,
    "processed_format": "JPEG",
    "original_size_bytes": 524288,
    "processed_size_bytes": 245760,
    "uploaded_at": "2025-01-17T20:00:00.000000",
    "user_id": 123,
    "filename": "avatar_123_1705518000000_a1b2c3d4.jpg",
    "file_hash": "sha256_hash_here"
  },
  "message": "Avatar uploaded successfully"
}
```

**Error Responses**:

- **400 Bad Request**: Invalid file type, size limit exceeded, dimensions invalid
  ```json
  {
    "detail": "File size (6.5MB) exceeds maximum allowed size (5.0MB)"
  }
  ```

- **401 Unauthorized**: Missing or invalid authentication token
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

- **500 Internal Server Error**: Server-side processing error
  ```json
  {
    "detail": "Avatar upload failed. Please try again."
  }
  ```

### Delete Avatar

**DELETE** `/api/avatars/`

Delete the current user's avatar image.

**Authentication**: Required (Bearer token)

**Request**:
```http
DELETE /api/avatars/
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "message": "Avatar deleted successfully",
  "deleted": true
}
```

**Error Responses**:

- **404 Not Found**: No avatar to delete
  ```json
  {
    "detail": "No avatar to delete"
  }
  ```

### Get Avatar

**GET** `/api/avatars/{filename}`

Serve an avatar image file.

**Authentication**: Not required (public endpoint)

**Request**:
```http
GET /api/avatars/avatar_123_1705518000000_a1b2c3d4.jpg
```

**Response** (200 OK):
```
Content-Type: image/jpeg
Cache-Control: public, max-age=86400
ETag: "1705518000"

[binary image data]
```

**Error Responses**:

- **400 Bad Request**: Invalid filename (path traversal attempt)
- **404 Not Found**: Avatar file not found

## Usage Examples

### Frontend (TypeScript/React)

```typescript
import { uploadAvatar, deleteAvatar, validateAvatarFile } from '@/lib/api/avatar'

// Upload avatar
const handleUpload = async (file: File) => {
  try {
    // Client-side validation
    validateAvatarFile(file, 5) // 5MB max

    // Upload to backend
    const response = await uploadAvatar(file)

    console.log('Avatar uploaded:', response.avatar_url)
    console.log('Dimensions:', response.metadata.width, 'x', response.metadata.height)

    // Update user profile with new avatar URL
    updateProfile({ avatar: response.avatar_url })
  } catch (error) {
    console.error('Upload failed:', error.message)
  }
}

// Delete avatar
const handleDelete = async () => {
  try {
    const response = await deleteAvatar()
    console.log(response.message)

    // Clear avatar from profile
    updateProfile({ avatar: null })
  } catch (error) {
    console.error('Delete failed:', error.message)
  }
}
```

### Python Client

```python
import requests

# Upload avatar
def upload_avatar(token: str, file_path: str):
    url = "http://localhost:8000/api/avatars/upload"
    headers = {"Authorization": f"Bearer {token}"}

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 201:
        data = response.json()
        print(f"Avatar uploaded: {data['avatar_url']}")
        print(f"Dimensions: {data['metadata']['width']}x{data['metadata']['height']}")
        return data
    else:
        print(f"Upload failed: {response.json()['detail']}")
        return None

# Delete avatar
def delete_avatar(token: str):
    url = "http://localhost:8000/api/avatars/"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        print(response.json()['message'])
        return True
    else:
        print(f"Delete failed: {response.json()['detail']}")
        return False
```

### cURL

```bash
# Upload avatar
curl -X POST "http://localhost:8000/api/avatars/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/avatar.jpg"

# Delete avatar
curl -X DELETE "http://localhost:8000/api/avatars/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get avatar (public)
curl "http://localhost:8000/api/avatars/avatar_123_1705518000000_a1b2c3d4.jpg" \
  --output avatar.jpg
```

## Database Schema

### User Model Updates

```sql
-- Avatar columns added to users table
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN avatar_metadata JSON;

-- Index for efficient avatar queries
CREATE INDEX idx_users_avatar ON users (avatar_url) WHERE avatar_url IS NOT NULL;
```

**Fields**:
- `avatar_url` (VARCHAR(500)): URL path to the avatar image
- `avatar_metadata` (JSON): Upload metadata including dimensions, file size, hash

**Example metadata**:
```json
{
  "width": 800,
  "height": 800,
  "processed_format": "JPEG",
  "original_size_bytes": 524288,
  "processed_size_bytes": 245760,
  "uploaded_at": "2025-01-17T20:00:00.000000",
  "user_id": 123,
  "filename": "avatar_123_1705518000000_a1b2c3d4.jpg",
  "file_hash": "abc123..."
}
```

## Storage

### Local Storage (Default)

- **Path**: `uploads/avatars/`
- **Format**: `avatar_{user_id}_{timestamp}_{hash}.{ext}`
- **Permissions**: Directory must be writable by application
- **Cleanup**: Old avatars are automatically deleted when new ones are uploaded

### Cloud Storage (Production Ready)

The implementation is designed to easily integrate with cloud storage:

```python
# Example S3 integration
from boto3 import client

class S3AvatarService(AvatarService):
    def __init__(self, bucket_name: str, region: str):
        self.s3_client = client('s3', region_name=region)
        self.bucket_name = bucket_name
        super().__init__(storage_path='', base_url=f'https://{bucket_name}.s3.amazonaws.com')

    def upload_avatar(self, user_id: int, file_data: bytes, filename: str, old_avatar_url: str = None):
        # Validate and process (same as local)
        clean_data, format, metadata = self.validator.validate_and_process(file_data, filename)

        # Upload to S3
        safe_filename = self.validator.sanitize_filename(filename, user_id)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f'avatars/{safe_filename}',
            Body=clean_data,
            ContentType=self.validator.get_mime_type(format)
        )

        # Generate URL
        avatar_url = f"{self.base_url}/avatars/{safe_filename}"

        # Delete old avatar if exists
        if old_avatar_url:
            self.delete_avatar(old_avatar_url)

        return avatar_url, metadata
```

## Testing

### Running Tests

```bash
# Run all avatar tests
pytest backend/tests/api/test_avatar_upload.py -v

# Run specific test class
pytest backend/tests/api/test_avatar_upload.py::TestImageValidator -v

# Run with coverage
pytest backend/tests/api/test_avatar_upload.py --cov=app.services.media --cov=app.utils.security
```

### Test Coverage

- ✅ File type validation (magic bytes)
- ✅ Size limit enforcement
- ✅ Dimension validation (min/max)
- ✅ EXIF data stripping
- ✅ Filename sanitization (path traversal prevention)
- ✅ Image reprocessing
- ✅ Upload/delete flow
- ✅ Old avatar cleanup
- ✅ Error handling
- ✅ Security edge cases

## Migration Guide

### Running the Migration

```bash
# Navigate to backend directory
cd backend

# Run Alembic migration
alembic upgrade head

# Verify migration
alembic current
```

### Rollback (if needed)

```bash
# Rollback last migration
alembic downgrade -1

# Verify
alembic current
```

## Performance Considerations

### Image Processing
- **CPU Usage**: Image reprocessing is CPU-intensive
- **Recommendation**: Use background job queue for large uploads
- **Optimization**: Consider using async processing for better concurrency

### Storage
- **Local Storage**: Fast for small deployments, limited scalability
- **Cloud Storage**: Recommended for production (S3, GCS, Azure Blob)
- **CDN**: Use CloudFront, CloudFlare for better performance

### Caching
- **Browser Cache**: Avatars are cached for 24 hours (Cache-Control header)
- **ETags**: Implemented for efficient cache validation
- **CDN**: Recommended for production deployments

## Security Best Practices

1. **Always Validate on Backend**: Never trust client-side validation alone
2. **Use HTTPS**: Prevent man-in-the-middle attacks during upload
3. **Rate Limiting**: Prevent abuse and DoS attacks
4. **Monitor Storage**: Set up alerts for unusual storage growth
5. **Regular Cleanup**: Run orphaned avatar cleanup periodically
6. **Virus Scanning**: Consider integrating ClamAV for additional security

## Troubleshooting

### Common Issues

**Issue**: "PIL/Pillow not installed"
```bash
# Solution: Install Pillow
pip install Pillow==10.2.0
```

**Issue**: "Permission denied" when saving avatars
```bash
# Solution: Create directory with proper permissions
mkdir -p uploads/avatars
chmod 755 uploads/avatars
```

**Issue**: Avatars not displaying
- Check `CORS_ORIGINS` in settings includes frontend URL
- Verify file exists in `uploads/avatars/`
- Check network tab in browser DevTools for 404 errors

**Issue**: Upload fails with "File too large"
- Check `MAX_SIZE_BYTES` in `ImageValidator` configuration
- Verify nginx/reverse proxy file size limits

## Future Enhancements

- [ ] Automatic image optimization (compression, format conversion)
- [ ] Multiple avatar sizes (thumbnail, small, medium, large)
- [ ] Avatar cropping interface
- [ ] Background processing queue
- [ ] Cloud storage integration (S3, GCS)
- [ ] CDN integration
- [ ] Virus scanning (ClamAV)
- [ ] Image moderation (content filtering)
- [ ] Avatar history/versioning

## Support

For issues or questions:
- GitHub Issues: [Repository Link]
- Documentation: `/docs` endpoint
- API Playground: `/docs` (Swagger UI)
