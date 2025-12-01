# Warehouse Email Processing System

## Overview

This system processes warehouse queue data from Eclipse ERP by fetching CSV files via email, storing them in Wasabi object storage, and loading them into MongoDB for fast querying.

## Architecture

```
Eclipse ERP → Email CSV → Zoho IMAP
    ↓
Django: fetch_warehouse_emails command
    ↓
Wasabi: {company}/upload/warehouse_queue.csv
    ↓
Django: process_warehouse_csv command
    ↓
MongoDB: warehouse_invoices collection
    ↓
Warehouse Dashboard API (query MongoDB)
```

## Why This Approach?

**Problem**: Eclipse ERP's direct API calls for warehouse queue data were:
- Unreliable (printStatus filtering didn't work consistently)
- Slow (multiple API calls per invoice for status lookup)
- Limited (PRINT.QUEUE file has no API endpoint)

**Solution**: Email-based CSV processing provides:
- **Reliability**: PRINT.QUEUE file is the authoritative source
- **Speed**: MongoDB queries are instant (no ERP API calls)
- **Multi-tenant**: Company-specific folder isolation in Wasabi

## Components

### 1. Email Fetcher (`fetch_warehouse_emails.py`)

**Purpose**: Fetch CSV attachments from Zoho email and upload to Wasabi

**Usage**:
```bash
python manage.py fetch_warehouse_emails
```

**What it does**:
1. Connects to Zoho IMAP (IMPORT folder)
2. Fetches unread emails
3. Extracts company code from subject line (e.g., `[HERITAGE]`)
4. Saves CSV attachments to temp files
5. Uploads to Wasabi: `data/uploads/{company}/upload/warehouse_queue.csv`
6. Moves processed emails to PROCESSED folder

**Environment Variables**:
- `ZOHO_EMAIL` - Email address
- `ZOHO_PASSWORD` - Email password
- `ZOHO_IMAP_SERVER` - IMAP server (default: imap.zoho.com)
- `WASABI_ACCESS_KEY` - Wasabi access key
- `WASABI_SECRET_KEY` - Wasabi secret key
- `WASABI_BUCKET_NAME` - Wasabi bucket name
- `WASABI_REGION` - Wasabi region (default: us-east-1)
- `WASABI_ENDPOINT` - Wasabi endpoint (default: https://s3.wasabisys.com)

### 2. CSV Processor (`process_warehouse_csv.py`)

**Purpose**: Download CSV files from Wasabi and load into MongoDB

**Usage**:
```bash
# Process all companies
python manage.py process_warehouse_csv

# Process specific company only
python manage.py process_warehouse_csv --company=heritage
```

**What it does**:
1. Downloads `warehouse_queue.csv` from Wasabi for each company
2. Parses CSV and validates records
3. Clears existing company records from MongoDB (replace, not append)
4. Inserts new records with company tagging
5. Moves processed CSV to `data/uploads/{company}/processed/warehouse_queue_{timestamp}.csv`

**Environment Variables**:
- `MONGO_URI` - MongoDB connection string
- `DB_NAME` - Database name (default: emp54)

**MongoDB Schema**:
```javascript
{
  companyCode: "heritage",          // Company identifier
  fullInvoiceID: "S105418530.001",  // Full Order ID from CSV
  branch: "19",                     // Ship branch from CSV
  printStatus: "Q",                 // Print status (Q = awaiting pickup)
  shipVia: "WILL CALL",             // Shipping method from CSV
  lastUpdated: ISODate("...")       // Last update timestamp
}
```

**Note**: Only these 4 fields come from the CSV. Additional fields (shipDate, custName, poNumber, balanceDue) are fetched from the ERP API on-demand when querying the warehouse dashboard.

### 3. Warehouse API (`warehouse_api_orders`)

**Purpose**: Query MongoDB for warehouse orders (replaces slow ERP API calls)

**Endpoint**: `GET /api/warehouse/orders?branch=ILMV&shipViaKeywords=UPS,FEDEX`

**What it does**:
1. Authenticates user and extracts company code from session
2. Queries MongoDB `warehouse_invoices` collection with filters:
   - `companyCode` - Company identifier
   - `branch` - Ship branch
   - `printStatus='Q'` - Awaiting pickup
   - `shipVia` keywords (optional filter)
3. For each invoice, fetches real-time status from PRINT.REVIEW API
4. Returns sorted list of orders

**Benefits**:
- **Fast**: MongoDB queries vs slow ERP API calls
- **Reliable**: Data comes from PRINT.QUEUE file (authoritative source)
- **Scalable**: Can handle thousands of invoices instantly

### 4. Wasabi Client Service (`wasabi_client.py`)

**Purpose**: Reusable S3 client for Wasabi operations

**Methods**:
- `upload_file(file_path, s3_key)` - Upload file to Wasabi
- `download_file(s3_key, local_path)` - Download file from Wasabi
- `list_files(prefix='')` - List files with optional prefix
- `delete_file(s3_key)` - Delete file from Wasabi
- `move_file(source_key, dest_key)` - Move file within bucket

## Scheduling

### Railway (Recommended)

Railway doesn't support traditional cron, but you can use:

1. **Railway Cron Jobs** (if available in your plan):
   ```yaml
   # railway.toml
   [deploy]
   cron = "*/5 * * * * cd django-backend && ./scripts/process_warehouse_emails.sh"
   ```

2. **External Cron Service** (e.g., cron-job.org, EasyCron):
   - Create HTTP endpoint that triggers the commands
   - Schedule external service to hit endpoint every 5 minutes

3. **Self-Hosted Cron** (if you have a server):
   ```bash
   # Add to crontab -e
   */5 * * * * /path/to/vue-basic/django-backend/scripts/process_warehouse_emails.sh >> /var/log/warehouse_email.log 2>&1
   ```

### Manual Testing

Run the full pipeline manually:
```bash
cd django-backend
./scripts/process_warehouse_emails.sh
```

Or run commands individually:
```bash
# Step 1: Fetch emails
python manage.py fetch_warehouse_emails

# Step 2: Process CSVs
python manage.py process_warehouse_csv
```

## Eclipse Configuration

### Email Setup

1. Configure Eclipse to export PRINT.QUEUE file to CSV
2. Set up Eclipse to email CSV with subject format: `[HERITAGE] Warehouse Queue Export`
3. Send to your Zoho email address configured in `ZOHO_EMAIL`
4. Schedule Eclipse export every 5 minutes (or desired frequency)

### CSV Format

The CSV file from Eclipse PRINT.QUEUE has these columns:
- `FULL.OID` - Full Order ID (e.g., S105418530.001)
- `BR` - Ship branch (e.g., ILMV, 19, 21)
- `PRT` - Print status (Q = awaiting pickup, M = other)
- `SHIP.VIA` - Shipping method (e.g., WILL CALL, OT OUR TRUCK, UPS GROUND)

**Example CSV:**
```
FULL.OID      ,BR  ,PRT  ,SHIP.VIA

S104971948.001,19  ,Q    ,WILL CALL
S105001015.002,21  ,Q    ,WILL CALL
S105014987.001,8   ,Q    ,OT OUR TRUCK
S105065989.002,19  ,Q    ,OT OUR TRUCK
```

**Notes:**
- CSV has extra whitespace in headers and values (handled by parser)
- May contain blank lines after header (handled by parser)
- Only 4 fields provided - shipDate, custName, etc. fetched from ERP API on demand

## Multi-Tenant Isolation

### Wasabi Folder Structure

```
/data/uploads/
├── heritage/
│   ├── upload/
│   │   └── warehouse_queue.csv     # Current file
│   └── processed/
│       ├── warehouse_queue_20251129_140500.csv
│       └── warehouse_queue_20251129_145000.csv
├── metro/
│   ├── upload/
│   └── processed/
└── [other-companies]/
```

### Company Code Mapping

Email subject `[HERITAGE]` → folder `heritage`
Email subject `[METRO]` → folder `metro`
Email subject `[TRISTATE]` → folder `tristate`

Add new companies to `COMPANY_CODE_MAP` in `fetch_warehouse_emails.py`:
```python
COMPANY_CODE_MAP = {
    'HERITAGE': 'heritage',
    'METRO': 'metro',
    'TRISTATE': 'tristate',
    'NEWCO': 'newco',  # Add new company here
}
```

## Monitoring

### Logs

All commands log to Django's logging system. Check logs for:
- `[Warehouse Email]` - Email fetching logs
- `[Warehouse CSV]` - CSV processing logs
- `[Warehouse API]` - API query logs

### Health Checks

1. **Email Processing**: Check `PROCESSED` folder in Zoho for moved emails
2. **Wasabi Storage**: Check `data/uploads/{company}/upload/` for CSV files
3. **MongoDB**: Query `warehouse_invoices` collection:
   ```javascript
   db.warehouse_invoices.find({companyCode: "heritage"}).count()
   ```
4. **API**: Test warehouse dashboard for real-time data

## Troubleshooting

### No orders showing up

1. Check if CSV file exists in Wasabi:
   ```bash
   python manage.py fetch_warehouse_emails  # Check logs
   ```

2. Check if MongoDB has records:
   ```python
   from pymongo import MongoClient
   client = MongoClient(MONGO_URI)
   db = client['emp54']
   print(list(db.warehouse_invoices.find({'companyCode': 'heritage'})))
   ```

3. Check Django logs for errors

### Email not processing

- Verify `ZOHO_EMAIL` and `ZOHO_PASSWORD` are correct
- Check Zoho IMAP is enabled for your account
- Ensure emails have correct subject format: `[HERITAGE]`
- Check `IMPORT` folder exists in Zoho

### CSV parsing errors

- Verify CSV has correct column names
- Check for malformed CSV (extra commas, quotes)
- Review logs for specific row errors

## Future Enhancements

1. **Webhooks**: Instead of cron, use Zoho email webhooks to trigger processing
2. **Balance Due**: Add ERP API call to fetch real-time balance due
3. **PO Number**: Add to CSV export if needed
4. **Historical Data**: Keep 30-day history in MongoDB (currently replaces all records)
5. **Dashboard Refresh**: Add auto-refresh to warehouse dashboard
6. **Email Notifications**: Alert when processing fails

## Related Files

- `django-backend/services/wasabi_client.py` - Wasabi S3 client
- `django-backend/products/management/commands/fetch_warehouse_emails.py` - Email fetcher
- `django-backend/products/management/commands/process_warehouse_csv.py` - CSV processor
- `django-backend/products/views.py` - Warehouse API endpoints
- `django-backend/templates/products/warehouse_dashboard.html` - Dashboard UI
- `django-backend/scripts/process_warehouse_emails.sh` - Scheduler script
