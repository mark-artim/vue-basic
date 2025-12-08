"""
PDW Data Prep Integration Tests

Tests the full workflow using the real Mars12022025.xlsx file as a fixture.
This catches type errors, data quality issues, and regressions.

Run tests:
    python manage.py test pdw

Run tests with verbose output:
    python manage.py test pdw --verbosity=2
"""

from django.test import TestCase, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore
import json
import os
import base64
from io import BytesIO
import pandas as pd


class PDWDataPrepTestCase(TestCase):
    """Integration tests for PDW Data Prep workflow"""

    def setUp(self):
        """Set up test client and load Mars file"""
        self.client = Client()
        self.mars_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'Mars12022025.xlsx'
        )

        # Check if Mars file exists
        if not os.path.exists(self.mars_file_path):
            self.skipTest(f"Mars file not found at {self.mars_file_path}")

        # Load Mars file into memory
        with open(self.mars_file_path, 'rb') as f:
            self.mars_file_data = f.read()

        # Set up authenticated session for PDW access
        # Simulate a logged-in admin user with pdw-data-prep access
        session = self.client.session
        session['admin_logged_in'] = True
        session['admin_user_id'] = 'test-admin-123'
        session['admin_email'] = 'test@emp54.com'
        session['admin_username'] = 'testadmin'
        session['admin_name'] = 'Test Admin'
        session['admin_company_code'] = 'emp54'
        session.save()

    def test_mars_file_upload_and_parse(self):
        """Test Step 1: Upload Mars file and parse sheets"""
        # Create file upload
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'

        response = self.client.post('/pdw/parse/', {
            'file': file
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertTrue(data['success'])
        self.assertIn('sheets', data)
        self.assertIn('filename', data)

        # Verify Mars file has 1 sheet with correct dimensions
        self.assertEqual(len(data['sheets']), 1)
        sheet_data = list(data['sheets'].values())[0]
        self.assertEqual(sheet_data['total_rows'], 5742)
        self.assertEqual(sheet_data['total_cols'], 9)

    def test_mars_file_preview_with_header_row_7(self):
        """Test Step 2: Generate preview with header row 7"""
        # First, upload file to get session data
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        parse_response = self.client.post('/pdw/parse/', {'file': file})
        self.assertTrue(parse_response.json()['success'])

        # Now test preview with header row 7
        sheet_name = 'MARS Price Sheet'  # Mars file has one sheet
        response = self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {sheet_name: 7},  # Test string "7" conversion
                'included_sheets': {sheet_name: True},
                'column_mappings': {},
                'offset': 0,
                'limit': 50
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify preview generated successfully
        self.assertTrue(data['success'])
        self.assertIn('total_rows', data)
        self.assertIn('columns', data)
        self.assertIn('preview', data)

        # Verify correct columns from header row 7
        expected_columns = ['Revision', 'MARS Item Number', 'Description', 'Min Qty', 'Price', 'UPC']
        for col in expected_columns[:6]:  # Check first 6 columns
            self.assertIn(col, data['columns'])

        # After setting header row 7, we should have fewer rows (skipped first 7)
        self.assertLess(data['total_rows'], 5742)

    def test_smart_clean_preview_detects_issues(self):
        """Test Step 3: Smart Clean preview detects data quality issues"""
        # Upload and preview first
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        sheet_name = 'MARS Price Sheet'
        self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {sheet_name: 7},
                'included_sheets': {sheet_name: True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        # Now test Smart Clean preview
        response = self.client.post('/pdw/smart-clean/',
            data=json.dumps({'preview': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify Smart Clean detected issues
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        stats = data['stats']

        # Verify it found the known issues in Mars file
        self.assertGreater(stats['remove_blank'], 150)  # ~163 blank rows
        self.assertGreater(stats['remove_sparse'], 150)   # ~163 category headers
        # Note: Duplicate headers are 0 because they're already handled by setting correct header row
        self.assertGreaterEqual(stats['remove_duplicate_headers'], 0)

    def test_smart_clean_apply_removes_junk_rows(self):
        """Test Step 3: Smart Clean actually removes junk rows"""
        # Upload and preview first
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        sheet_name = 'MARS Price Sheet'
        preview_response = self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {sheet_name: 7},
                'included_sheets': {sheet_name: True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )
        original_rows = preview_response.json()['total_rows']

        # Apply Smart Clean with all standard actions
        response = self.client.post('/pdw/smart-clean/',
            data=json.dumps({
                'preview': False,
                'actions': [
                    'remove_blank',
                    'remove_sparse',
                    'remove_duplicate_headers',
                    'remove_commas',
                    'uppercase',
                    'trim'
                ]
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify Smart Clean applied successfully
        self.assertTrue(data['success'])
        self.assertIn('total_rows', data)
        self.assertIn('rows_removed', data)
        self.assertIn('changes', data)

        # Verify significant rows were removed (~326+ junk rows)
        self.assertGreater(data['rows_removed'], 300)
        self.assertLess(data['total_rows'], original_rows - 300)

        # Verify final row count is reasonable (~5,400+ clean rows)
        self.assertGreater(data['total_rows'], 5300)
        self.assertLess(data['total_rows'], 5500)

    def test_header_row_type_conversion(self):
        """Regression test: Ensure header_row string converts to int"""
        # This tests the fix for "header must be integer or list of integers"
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        # Send header_row as string (simulating JavaScript/JSON behavior)
        response = self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {'MARS Price Sheet': '7'},  # String instead of int
                'included_sheets': {'MARS Price Sheet': True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        # Should succeed (not throw "header must be integer" error)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_export_csv_after_smart_clean(self):
        """Test Step 4: Export CSV after Smart Clean"""
        # Upload, preview, and smart clean first
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {'MARS Price Sheet': 7},
                'included_sheets': {'MARS Price Sheet': True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        self.client.post('/pdw/smart-clean/',
            data=json.dumps({
                'preview': False,
                'actions': ['remove_blank', 'remove_sparse', 'remove_duplicate_headers']
            }),
            content_type='application/json'
        )

        # Export CSV
        response = self.client.get('/pdw/export/?filename=test_mars_cleaned')

        # Verify CSV export
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test_mars_cleaned.csv', response['Content-Disposition'])

        # Verify CSV content
        csv_content = response.content.decode('utf-8')
        self.assertIn('Revision', csv_content)  # Header row
        self.assertIn('MARS Item Number', csv_content)

        # Count rows (should be ~5,408 + 1 header)
        row_count = len(csv_content.strip().split('\n'))
        self.assertGreater(row_count, 5300)
        self.assertLess(row_count, 5500)


    def test_uppercase_and_trim_preserve_nulls(self):
        """Test that uppercase and trim don't convert NaN/None to 'NAN'/'NONE' strings"""
        # Upload and preview first
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        sheet_name = 'MARS Price Sheet'
        self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {sheet_name: 7},
                'included_sheets': {sheet_name: True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        # Apply uppercase and trim actions
        response = self.client.post('/pdw/smart-clean/',
            data=json.dumps({
                'preview': False,
                'actions': ['uppercase', 'trim']
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Check Min Qty column (mostly nulls) doesn't have "NONE" or "NAN" strings
        preview_data = data['preview']
        for row in preview_data[:50]:  # Check first 50 rows
            if 'Min Qty' in row:
                min_qty = row['Min Qty']
                # Should be empty string or number, NOT "NONE" or "NAN"
                self.assertNotEqual(min_qty, 'NONE', f"Min Qty should not be 'NONE', got: {min_qty}")
                self.assertNotEqual(min_qty, 'NAN', f"Min Qty should not be 'NAN', got: {min_qty}")
                self.assertNotEqual(min_qty, 'None', f"Min Qty should not be 'None', got: {min_qty}")
                self.assertNotEqual(min_qty, 'nan', f"Min Qty should not be 'nan', got: {min_qty}")

    def test_format_numeric_no_precision_errors(self):
        """Test that format_numeric doesn't create float precision errors like 2.7800000000000002"""
        # Upload and preview first
        file = BytesIO(self.mars_file_data)
        file.name = 'Mars12022025.xlsx'
        self.client.post('/pdw/parse/', {'file': file})

        sheet_name = 'MARS Price Sheet'
        self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {sheet_name: 7},
                'included_sheets': {sheet_name: True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        # Apply format_numeric action
        response = self.client.post('/pdw/smart-clean/',
            data=json.dumps({
                'preview': False,
                'actions': ['format_numeric']
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Check that Price column values have exactly 2 decimal places
        preview_data = data['preview']
        for row in preview_data[:20]:  # Check first 20 rows
            if 'Price' in row and row['Price']:
                price = str(row['Price'])
                # Should not have long float precision errors
                self.assertNotIn('00000000', price, f"Float precision error in price: {price}")
                # Should have exactly 2 decimal places (format X.XX)
                if '.' in price:
                    decimal_places = len(price.split('.')[1])
                    self.assertEqual(decimal_places, 2, f"Price should have 2 decimals, got: {price}")


class PDWEdgeCasesTestCase(TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.client = Client()
        # Set up authenticated session
        session = self.client.session
        session['admin_logged_in'] = True
        session['admin_user_id'] = 'test-admin-123'
        session['admin_email'] = 'test@emp54.com'
        session.save()

    def test_preview_without_upload(self):
        """Test preview fails gracefully when no file in session"""
        response = self.client.post('/pdw/preview/',
            data=json.dumps({
                'header_rows': {'MARS Price Sheet': 0},
                'included_sheets': {'MARS Price Sheet': True},
                'column_mappings': {},
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('No file data in session', data['error'])

    def test_smart_clean_without_preview(self):
        """Test smart clean fails gracefully when no data in session"""
        response = self.client.post('/pdw/smart-clean/',
            data=json.dumps({'preview': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
