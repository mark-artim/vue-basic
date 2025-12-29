# Secure File Management - Deployment Guide

## 🚨 Security Overview

This implementation fixes **CRITICAL security vulnerabilities** in the original Node.js file management system:

### Previous Vulnerabilities (Node.js):
- ❌ **No company isolation** - All files in same folder
- ❌ **No authentication** - Anyone could access files
- ❌ **No authorization** - Heritage could access Crescent's files
- ❌ **No audit logging** - No record of file access

### New Security Features (Django):
- ✅ **Company-based file isolation** - Files stored in `companies/{company_code}/` folders
- ✅ **Authentication required** - Must be logged in
- ✅ **Authorization enforcement** - Can ONLY access own company's files
- ✅ **Comprehensive audit logging** - Every file operation logged
- ✅ **Double validation** - Company check in both MongoDB and S3
- ✅ **Soft delete** - Files marked as deleted, not immediately removed

---

## File Organization in Wasabi

```
bucket-name/
├── companies/
│   ├── heritage/
│   │   └── user-uploads/
│   │       ├── invoice-2024-01.pdf
│   │       ├── po-12345.csv
│   │       └── quote-5678.xlsx
│   │
│   ├── crescent/
│   │   └── user-uploads/
│   │       ├── report-march.pdf
│   │       └── data-export.csv
│   │
│   └── {other-companies}/
│       └── user-uploads/
│           └── ...
```

**CRITICAL:** Heritage users can ONLY see/access files in `companies/heritage/`, never `companies/crescent/`.

---

## Installation Steps

### 1. Add to Django Settings

Add to `django-backend/emp54_django/settings.py`:

```python
# Add 'files' to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'files',  # ADD THIS
]

# Add Wasabi S3 Configuration
WASABI_ENDPOINT = os.getenv('WASABI_ENDPOINT', 'https://s3.wasabisys.com')
WASABI_ACCESS_KEY = os.getenv('WASABI_ACCESS_KEY')
WASABI_SECRET_KEY = os.getenv('WASABI_SECRET_KEY')
WASABI_BUCKET = os.getenv('WASABI_BUCKET')
WASABI_REGION = os.getenv('WASABI_REGION', 'us-east-1')
```

### 2. Add URL Routes

Add to `django-backend/emp54_django/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('files/', include('files.urls')),  # ADD THIS
]
```

### 3. Install Dependencies

```bash
cd django-backend
pip install boto3  # For AWS S3/Wasabi
pip install djongo  # If not already installed
```

### 4. Environment Variables

Add to `.env`:

```env
WASABI_ENDPOINT=https://s3.wasabisys.com
WASABI_ACCESS_KEY=your_access_key
WASABI_SECRET_KEY=your_secret_key
WASABI_BUCKET=your_bucket_name
WASABI_REGION=us-east-1
```

### 5. Run Migrations

```bash
cd django-backend
python manage.py makemigrations files
python manage.py migrate files
```

---

## API Endpoints

All endpoints require authentication (must be logged in as customer).

### List Files
```
GET /files/list/
Response: {
  "success": true,
  "files": [
    {
      "id": "...",
      "filename": "invoice.pdf",
      "file_size": 12345,
      "uploaded_by": "user@heritage.com",
      "uploaded_at": "2025-01-10T12:00:00Z"
    }
  ],
  "company_code": "heritage"
}
```

### Upload File
```
POST /files/upload/
Content-Type: multipart/form-data

Form Data:
- file: (binary file)
- category: (optional)
- description: (optional)

Response: {
  "success": true,
  "message": "Uploaded invoice.pdf",
  "file": { ... }
}
```

### Download File
```
GET /files/download/{file_id}/
Response: Binary file download
```

### Delete File
```
DELETE /files/delete/{file_id}/
Response: {
  "success": true,
  "message": "Deleted invoice.pdf"
}
```

### Rename File
```
POST /files/rename/{file_id}/
Content-Type: application/json

Body: {
  "new_filename": "updated-invoice.pdf"
}

Response: {
  "success": true,
  "message": "Renamed to updated-invoice.pdf"
}
```

---

## Security Validation

### Test Company Isolation

**Test 1: Heritage user tries to access Crescent file**

1. Log in as Heritage user
2. Try to download a file ID that belongs to Crescent
3. **Expected:** 404 error "File not found or access denied"
4. **Logged:** Unauthorized access attempt in `file_access_logs`

**Test 2: List files only shows company's files**

1. Log in as Heritage user
2. Call `/files/list/`
3. **Expected:** Only Heritage files returned
4. **Expected:** Crescent files NOT in response

**Test 3: Upload creates company-specific path**

1. Log in as Heritage user
2. Upload `test.pdf`
3. **Expected:** File stored at `companies/heritage/user-uploads/test.pdf`
4. **Expected:** MongoDB record has `company_code: "heritage"`

---

## Audit Logging

Every file operation is logged in `file_access_logs` collection:

```javascript
{
  file_id: "...",
  file_key: "companies/heritage/user-uploads/invoice.pdf",
  operation: "download",  // upload, download, delete, rename
  user_id: "...",
  user_email: "user@heritage.com",
  company_code: "heritage",
  ip_address: "192.168.1.100",
  user_agent: "Mozilla/5.0...",
  success: true,
  timestamp: ISODate("2025-01-10T12:00:00Z")
}
```

### View Audit Logs

```python
# All file operations for Heritage
logs = FileAccessLog.objects.filter(company_code='heritage').order_by('-timestamp')

# Failed access attempts (potential security issues)
failed_attempts = FileAccessLog.objects.filter(success=False).order_by('-timestamp')

# Specific user's file history
user_logs = FileAccessLog.objects.filter(user_email='user@heritage.com')
```

---

## Migration from Node.js

### Option 1: Leave Old Files, Use Django Going Forward

- Keep existing Node.js files where they are
- New uploads go through Django with proper isolation
- Gradually migrate old files as needed

### Option 2: Migrate All Files

1. List all files in Wasabi
2. For each file, determine which company it belongs to
3. Copy to new company-specific path: `companies/{company_code}/user-uploads/`
4. Create MongoDB records for each file
5. Delete old files from `data/uploads/`

Migration script template:

```python
from files.models import CompanyFile
from files.s3_service import get_s3_service

# Map old files to companies (you'll need to determine this)
file_to_company = {
    'invoice-123.pdf': 'heritage',
    'po-456.csv': 'crescent',
    # ...
}

s3_service = get_s3_service()

for old_key, company_code in file_to_company.items():
    # Copy to new location
    new_key = f"companies/{company_code}/user-uploads/{old_key}"
    s3_service.s3_client.copy_object(
        Bucket=s3_service.bucket_name,
        CopySource={'Bucket': s3_service.bucket_name, 'Key': f'data/uploads/{old_key}'},
        Key=new_key
    )

    # Create MongoDB record
    CompanyFile.objects.create(
        filename=old_key,
        original_filename=old_key,
        file_key=new_key,
        company_code=company_code,
        # ... other fields
    )

    # Delete old file
    s3_service.s3_client.delete_object(
        Bucket=s3_service.bucket_name,
        Key=f'data/uploads/{old_key}'
    )
```

---

## Updating Vue Frontend

Update `src/pages/WasabiManager.vue` to use new Django endpoints:

```javascript
// Change from
const res = await axios.get('/wasabi/list');

// To
const res = await axios.get('/files/list/');
```

Update all endpoints:
- `/wasabi/list` → `/files/list/`
- `/wasabi/upload` → `/files/upload/`
- `/wasabi/download?filename=X` → `/files/download/{file_id}/`
- `/wasabi/delete` → `/files/delete/{file_id}/`
- `/wasabi/rename` → `/files/rename/{file_id}/`

**Note:** New API uses file IDs instead of filenames for better security.

---

## Testing Checklist

- [ ] Install dependencies (`boto3`)
- [ ] Add settings to `settings.py`
- [ ] Add URL routes
- [ ] Run migrations
- [ ] Test upload as Heritage user
- [ ] Verify file stored in `companies/heritage/` folder
- [ ] Test list - only shows Heritage files
- [ ] Log in as Crescent user
- [ ] Verify cannot see Heritage files
- [ ] Test download, delete, rename
- [ ] Check audit logs in MongoDB
- [ ] Test unauthorized access (should fail with 403/404)

---

## Next Steps

1. **Deploy Django implementation**
2. **Test thoroughly with multiple companies**
3. **Update Vue frontend** to use new endpoints
4. **Migrate existing files** (if needed)
5. **Deprecate Node.js wasabi routes** (optional)
6. **Monitor audit logs** for security issues

---

## Support

For issues or questions:
1. Check `file_access_logs` collection for audit trail
2. Check Django logs for errors
3. Verify Wasabi credentials in `.env`
4. Ensure user has `customer_company_code` in session
