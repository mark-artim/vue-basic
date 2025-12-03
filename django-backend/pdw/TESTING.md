# PDW Data Prep Testing Guide

## Overview

This test suite uses the **real Mars12022025.xlsx file** as a test fixture to ensure the PDW Data Prep tool works correctly with real-world vendor data.

## Why Testing Matters

The Mars file test caught:
- ✅ Type conversion bug (`header_row` string → int)
- ✅ Data quality detection (164 blank rows, 163 duplicate headers, 50 sparse rows)
- ✅ Smart Clean functionality
- ✅ CSV export correctness

Without automated tests, these issues would only be found manually in production.

## Running Tests

### Quick Test (Recommended)

From `django-backend/` directory:

```bash
run_pdw_tests.bat
```

### Manual Test

```bash
python manage.py test pdw --verbosity=2
```

### Run Specific Test

```bash
python manage.py test pdw.tests.PDWDataPrepTestCase.test_mars_file_upload_and_parse
```

## Test Coverage

### Integration Tests (Full Workflow)

1. **test_mars_file_upload_and_parse**
   - Tests file upload and parsing
   - Verifies 5,742 rows × 9 columns detected

2. **test_mars_file_preview_with_header_row_7**
   - Tests header row selection
   - Verifies column names extracted correctly
   - Tests string "7" → int conversion

3. **test_smart_clean_preview_detects_issues**
   - Tests Smart Clean preview mode
   - Verifies detection of:
     - 164 blank rows
     - 50+ sparse rows
     - 163 duplicate headers

4. **test_smart_clean_apply_removes_junk_rows**
   - Tests Smart Clean application
   - Verifies ~377 junk rows removed
   - Verifies final count ~5,365 clean rows

5. **test_export_csv_after_smart_clean**
   - Tests CSV export
   - Verifies file format and content
   - Verifies correct row count

### Regression Tests

6. **test_header_row_type_conversion**
   - Catches the "header must be integer" bug
   - Tests string → int conversion

### Error Handling Tests

7. **test_preview_without_upload**
   - Tests graceful error when no file uploaded

8. **test_smart_clean_without_preview**
   - Tests graceful error when no data in session

## Test Fixtures

### Mars12022025.xlsx

**Location:** `vue-basic/Mars12022025.xlsx`

**Why this file:**
- Real vendor file with actual data quality issues
- Contains all the problems we need to detect:
  - Blank rows
  - Category headers (sparse rows)
  - Duplicate header rows every 20-50 rows
  - Mixed case text
  - Commas in descriptions
  - UPC column

**Expected Results:**
- Original: 5,742 rows
- After header row 7 selection: ~5,735 rows (skips first 7)
- After Smart Clean: ~5,365 rows (removes ~370 junk rows)

## Before Committing Code

**Always run tests before committing changes to PDW:**

```bash
cd django-backend
run_pdw_tests.bat
```

If tests pass, commit is safe. If tests fail, fix the issue before committing.

## CI/CD Integration (Future)

To add GitHub Actions:

1. Create `.github/workflows/pdw-tests.yml`
2. Add Mars file to repository (or use test data generator)
3. Run tests on every push to main
4. Block merges if tests fail

## Adding New Tests

When adding new features to PDW Data Prep:

1. Add test case to `pdw/tests.py`
2. Use Mars file as fixture (or create new fixture if needed)
3. Run tests to verify
4. Commit tests with feature code

### Example:

```python
def test_new_smart_clean_action(self):
    """Test new Smart Clean action"""
    # Upload Mars file
    file = BytesIO(self.mars_file_data)
    file.name = 'Mars12022025.xlsx'
    self.client.post('/pdw/parse/', {'file': file})

    # Apply your new action
    response = self.client.post('/pdw/smart-clean/',
        data=json.dumps({
            'preview': False,
            'actions': ['your_new_action']
        }),
        content_type='application/json'
    )

    # Verify results
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertTrue(data['success'])
    # Add more assertions...
```

## Troubleshooting

### Mars file not found

```
ERROR: Mars12022025.xlsx not found
```

**Fix:** Place Mars file in project root: `vue-basic/Mars12022025.xlsx`

### Tests hang or timeout

**Fix:** Check if Django server is running on port 8000 (stop it before running tests)

### Database errors

**Fix:** Tests use Django's test database (separate from production). If errors persist, run:

```bash
python manage.py migrate
```

## Best Practices

1. **Run tests before every commit** to PDW code
2. **Add tests for new features** before merging
3. **Don't skip failing tests** - fix them or fix the code
4. **Keep Mars file up to date** if vendor changes format
5. **Add regression tests** when bugs are found

## Performance

Test suite runs in ~5-10 seconds:
- File upload: ~1s
- Preview generation: ~1-2s
- Smart Clean: ~2-3s
- CSV export: ~1s

Fast enough to run before every commit!
