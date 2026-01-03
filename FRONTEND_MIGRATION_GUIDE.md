# Frontend Migration Guide: MongoDB → DuckDB

## File to Update
`django-backend/templates/analytics/po_insights.html`

This file contains ALL the analytics API calls that need to be updated.

---

## Quick Reference: API Endpoint Mapping

| OLD (MongoDB) | NEW (DuckDB) | Status |
|---------------|--------------|--------|
| `/analytics/api/import-csv/` | `/analytics/parquet/import/` | ✅ Ready |
| `/analytics/api/top-vendors/` | `/analytics/duckdb/vendors/` | ✅ Ready |
| `/analytics/api/query-branches/` | `/analytics/duckdb/branches/` | ✅ Ready |
| `/analytics/api/monthly-trends/` | `/analytics/duckdb/trends/` | ✅ Ready |
| `/analytics/api/vendor/{name}/companies/` | `/analytics/duckdb/search/?vendor={name}` | ✅ Ready |
| `/analytics/api/query-companies/` | Use DuckDB search or branches | ⚠️  See note |
| `/analytics/api/filter-options/` | Not needed (DuckDB handles this) | ⚠️  See note |

---

## Changes Needed (9 total)

### 1. CSV Import (Line 680) ⭐ PRIORITY

**Current:**
```javascript
const response = await fetch('/analytics/api/import-csv/', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': this.getCSRFToken(),
    },
});
```

**Change to:**
```javascript
const response = await fetch('/analytics/parquet/import/', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': this.getCSRFToken(),
    },
});
```

**Response format changes:**
```javascript
// OLD response:
{
    success: true,
    import_batch_id: "uuid",
    message: "Import started..."
}

// NEW response:
{
    success: true,
    import_id: "uuid",
    records_imported: 5000,
    total_records: 116404,
    file_size_mb: 2.4,
    s3_path: "s3://...",
    message: "Successfully imported..."
}
```

**Code changes needed:**
```javascript
// Line ~693: Update batch ID reference
this.currentImportBatchId = data.import_id;  // Changed from import_batch_id

// Line ~698: REMOVE polling (Parquet import is instant)
// DELETE lines 698-708 (startPolling call and related code)

// Line ~747: Update success message
this.importMessage = `Imported ${data.records_imported} records (Total: ${data.total_records})`;
```

---

### 2. Remove Import Status Polling (Lines 712-765)

**Parquet imports are INSTANT** - no background processing needed!

**Delete entire polling system:**
```javascript
// DELETE startPolling() function (lines ~712-725)
// DELETE pollImportStatus() function (lines ~728-765)
// DELETE pollInterval in data (line ~606)
// DELETE importProgress in data (line ~605)
```

**Simplify import success:**
```javascript
async importCSV() {
    if (!this.selectedFile) return;

    this.uploading = true;
    this.importMessage = '';

    try {
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('skip_rows', Math.max(0, parseInt(this.skipRows) - 1));
        formData.append('mode', 'append');  // NEW: append or replace

        const response = await fetch('/analytics/parquet/import/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            },
        });

        const data = await response.json();

        if (data.success) {
            this.importSuccess = true;
            this.importMessage = `✅ Imported ${data.records_imported} records! Total: ${data.total_records}`;
            this.selectedFile = null;
            document.getElementById('csvFile').value = '';

            // Reload data immediately (no polling needed!)
            await this.loadTopVendors();
            await this.loadBranchData();
            await this.loadMonthlyTrends();
        } else {
            this.importSuccess = false;
            this.importMessage = `Error: ${data.error}`;
        }
    } catch (error) {
        this.importSuccess = false;
        this.importMessage = `Failed: ${error.message}`;
    } finally {
        this.uploading = false;
    }
}
```

---

### 3. Load Filter Options (Line 784) - OPTIONAL

**Current:**
```javascript
const response = await fetch('/analytics/api/filter-options/');
```

**Option A: Remove entirely** (DuckDB doesn't need pre-loaded filters)
```javascript
// DELETE loadFilterOptions() function entirely
// DELETE from init()

// Filters still work - just type vendor/branch names directly
```

**Option B: Keep for autocomplete** (query DuckDB for unique values)
```javascript
async loadFilterOptions() {
    try {
        // Get unique vendors
        const vendorResp = await fetch('/analytics/duckdb/vendors/?limit=1000');
        const vendorData = await vendorResp.json();
        this.filterOptions.vendors = vendorData.data.map(v => v.vendor);

        // Get unique branches
        const branchResp = await fetch('/analytics/duckdb/branches/?limit=100');
        const branchData = await branchResp.json();
        this.filterOptions.branches = branchData.data.map(b => b.branch);
    } catch (error) {
        console.error('Failed to load filter options:', error);
    }
}
```

---

### 4. Load Top Vendors (Line 806) ⭐ PRIORITY

**Current:**
```javascript
const response = await fetch(`/analytics/api/top-vendors/?${params}`);
```

**Change to:**
```javascript
const response = await fetch(`/analytics/duckdb/vendors/?${params}`);
```

**Response format changes:**
```javascript
// OLD format:
{
    success: true,
    vendors: [{
        vendor_name: "...",
        total_spent: 123,
        order_count: 456
    }]
}

// NEW format:
{
    success: true,
    data: [{
        vendor: "...",        // Changed from vendor_name
        total_spent: 123,
        order_count: 456,
        vendor_id: "...",     // NEW field
        avg_order_value: 789, // NEW field
        first_order_date: "...", // NEW field
        last_order_date: "..."   // NEW field
    }]
}
```

**Update data handling (Line ~825):**
```javascript
if (data.success) {
    this.topVendors = data.data;  // Changed from data.vendors
    this.vendorsTotalCount = data.data.length;

    // Update stats
    if (this.topVendors.length > 0) {
        this.stats.totalSpent = this.topVendors.reduce((sum, v) => sum + (v.total_spent || 0), 0);
        this.stats.totalPOs = this.topVendors.reduce((sum, v) => sum + (v.order_count || 0), 0);
        this.stats.vendorCount = this.topVendors.length;
    }
}
```

**Update template references:**
```html
<!-- Find lines displaying vendor_name, change to vendor -->
<template x-for="vendor in topVendors">
    <div>
        <span x-text="vendor.vendor"></span>  <!-- Changed from vendor.vendor_name -->
    </div>
</template>
```

---

### 5. Load Branch Data (Line 887) ⭐ PRIORITY

**Current:**
```javascript
const response = await fetch(`/analytics/api/query-branches/?${params}`);
```

**Change to:**
```javascript
const response = await fetch(`/analytics/duckdb/branches/?${params}`);
```

**Response format changes:**
```javascript
// OLD format:
{
    success: true,
    branches: [{
        branch: "1",
        total_spent: 123,
        order_count: 456
    }]
}

// NEW format:
{
    success: true,
    data: [{
        branch: "1",
        total_value: 123,          // Changed from total_spent
        order_count: 456,
        avg_order_value: 789,      // NEW field
        unique_vendors: 50,        // NEW field
        earliest_order: "...",     // NEW field
        latest_order: "..."        // NEW field
    }]
}
```

**Update data handling (Line ~898):**
```javascript
if (data.success) {
    this.branchData = data.data;  // Changed from data.branches
    this.stats.branchCount = this.branchData.length;
}
```

---

### 6. Load Monthly Trends (Line 907) ⭐ PRIORITY

**Current:**
```javascript
const response = await fetch(`/analytics/api/monthly-trends/?${params}`);
```

**Change to:**
```javascript
const response = await fetch(`/analytics/duckdb/trends/?${params}`);
```

**Response format (mostly same!):**
```javascript
{
    success: true,
    data: [{
        month: "2025-12-01T00:00:00",
        monthly_total: 123,
        order_count: 456,
        avg_order_value: 789,      // NEW field
        unique_vendors: 50         // NEW field
    }]
}
```

**Update data handling (Line ~918):**
```javascript
if (data.success) {
    this.monthlyTrends = data.data;  // Same structure
}
```

---

### 7. Load Company Data (Line 927) - REMOVE

**This endpoint doesn't exist in DuckDB** (company field might not be useful)

**Option A: Remove entirely**
```javascript
// DELETE loadCompanyData() function
// DELETE from init()
// DELETE companyData from data
```

**Option B: Replace with branch grouping**
```javascript
async loadCompanyData() {
    // Use branch data instead
    this.companyData = this.branchData;
}
```

---

### 8. Vendor Drill-Down (Line 864)

**Current:**
```javascript
const response = await fetch(`/analytics/api/vendor/${encodeURIComponent(vendorName)}/companies/?${params}`);
```

**Change to:**
```javascript
const response = await fetch(`/analytics/duckdb/search/?vendor=${encodeURIComponent(vendorName)}&limit=100`);
```

**Response format changes:**
```javascript
// OLD format:
{
    success: true,
    companies: [{...}]
}

// NEW format:
{
    success: true,
    data: [{
        po_number: "...",
        vendor: "...",
        branch: "...",
        order_total: 123,
        order_date: "..."
    }]
}
```

**Update handling:**
```javascript
if (data.success) {
    this.vendorCompanies = data.data;  // Changed from data.companies
}
```

---

### 9. Export CSV (Line 966) - KEEP AS-IS

**This can stay the same** - export from DuckDB via new endpoint later.

For now, keep:
```javascript
window.location.href = `/analytics/api/export-csv/?${params}`;
```

---

## Summary Stats Update

**Add a NEW function to load summary stats** from DuckDB:

```javascript
async loadSummaryStats() {
    try {
        const response = await fetch('/analytics/duckdb/summary/');
        const data = await response.json();

        if (data.success) {
            this.stats = {
                totalPOs: data.data.total_orders,
                totalSpent: data.data.total_value,
                vendorCount: data.data.unique_vendors,
                branchCount: data.data.unique_branches
            };
        }
    } catch (error) {
        console.error('Failed to load summary:', error);
    }
}
```

**Add to init():**
```javascript
init() {
    this.loadSummaryStats();      // NEW - load overall stats
    this.loadTopVendors();
    this.loadBranchData();
    this.loadMonthlyTrends();
    this.loadImportHistory();      // Keep for now
}
```

---

## Testing Checklist

After making changes:

- [ ] CSV upload works and shows immediate success
- [ ] Top vendors table loads with correct data
- [ ] Branch analysis shows data
- [ ] Monthly trends chart displays
- [ ] Vendor drill-down works
- [ ] Stats cards show correct numbers
- [ ] No console errors

---

## Quick Migration Script

Run this in browser console to test DuckDB endpoints:

```javascript
// Test summary
fetch('/analytics/duckdb/summary/')
  .then(r => r.json())
  .then(d => console.log('Summary:', d));

// Test vendors
fetch('/analytics/duckdb/vendors/?limit=5')
  .then(r => r.json())
  .then(d => console.log('Vendors:', d));

// Test branches
fetch('/analytics/duckdb/branches/?limit=5')
  .then(r => r.json())
  .then(d => console.log('Branches:', d));
```

---

## Field Name Changes Reference

| OLD Field | NEW Field | Location |
|-----------|-----------|----------|
| `vendor_name` | `vendor` | Vendors endpoint |
| `total_spent` | `total_spent` (vendors) or `total_value` (branches) | Both |
| `vendors` | `data` | All responses |
| `branches` | `data` | All responses |
| `companies` | `data` | Search endpoint |
| `import_batch_id` | `import_id` | Import response |

---

## Next Steps

1. **Backup the file first:**
   ```bash
   cp django-backend/templates/analytics/po_insights.html django-backend/templates/analytics/po_insights.html.backup
   ```

2. **Make changes in this order:**
   - Summary stats (new function)
   - Top vendors (#4)
   - Branch data (#5)
   - Monthly trends (#6)
   - CSV import (#1)
   - Remove polling (#2)
   - Vendor drill-down (#8)

3. **Test after each change**

4. **Once working, run MongoDB cleanup:**
   ```bash
   python cleanup_mongodb_pos.py --confirm
   ```

Good luck! 🚀
