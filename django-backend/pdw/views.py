"""
PDW Data Preparation Views

Handles Excel file upload, data cleaning, and CSV export
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from core.decorators import require_product
import pandas as pd
import json
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


@require_product('pdw-data-prep')
def pdw_upload(request):
    """PDW Data Prep upload page"""
    return render(request, 'pdw/upload.html')


@csrf_exempt
@require_product('pdw-data-prep')
def pdw_parse(request):
    """
    Parse uploaded Excel file and return sheet info + data preview
    Handles multiple sheets and asks user to verify header rows
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    uploaded_file = request.FILES['file']

    try:
        # Read Excel file with pandas
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names

        logger.info(f"[PDW Parse] Uploaded file has {len(sheet_names)} sheets: {sheet_names}")

        # Read each sheet and get preview (first 10 rows)
        sheets_data = {}
        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # Replace NaN with empty strings for JSON compatibility
            df_clean = df.fillna('')

            # Convert first 10 rows to JSON for preview
            preview_rows = df_clean.head(10).values.tolist()

            sheets_data[sheet_name] = {
                'name': sheet_name,
                'total_rows': len(df),
                'total_cols': len(df.columns),
                'preview': preview_rows,
            }

        # Store full Excel file in session for later processing
        # Convert to JSON-serializable format
        request.session['pdw_sheets'] = sheet_names
        request.session['pdw_filename'] = uploaded_file.name

        # Store raw file data in session (base64 encoded)
        import base64
        uploaded_file.seek(0)
        file_data = uploaded_file.read()
        request.session['pdw_file_data'] = base64.b64encode(file_data).decode('utf-8')

        logger.info(f"[PDW Parse] Stored {len(sheet_names)} sheets in session")

        return JsonResponse({
            'success': True,
            'filename': uploaded_file.name,
            'sheets': sheets_data,
            'message': f'Uploaded {uploaded_file.name} with {len(sheet_names)} sheet(s)'
        })

    except Exception as e:
        logger.error(f"[PDW Parse] Error parsing file: {e}")
        return JsonResponse({
            'error': f'Failed to parse Excel file: {str(e)}'
        }, status=500)


@csrf_exempt
@require_product('pdw-data-prep')
def pdw_preview(request):
    """
    Generate combined preview after user selects header rows
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        header_rows = data.get('header_rows', {})  # {sheet_name: row_index}
        included_sheets = data.get('included_sheets', {})  # {sheet_name: true/false}
        column_mappings = data.get('column_mappings', {})  # {sheet_name: {originalCol: {newName, included}}}

        logger.info(f"[PDW Preview] Processing preview with header_rows: {header_rows}")

        # Retrieve file from session
        import base64
        file_data_b64 = request.session.get('pdw_file_data')
        if not file_data_b64:
            logger.error("[PDW Preview] No file data in session")
            return JsonResponse({'error': 'No file data in session. Please upload the file again.'}, status=400)

        file_data = base64.b64decode(file_data_b64)
        excel_file = pd.ExcelFile(BytesIO(file_data))
        logger.info(f"[PDW Preview] Loaded Excel file with {len(excel_file.sheet_names)} sheets")

        # Read each sheet with specified header row (only included sheets)
        dataframes = []
        for sheet_name in excel_file.sheet_names:
            # Skip if sheet is not included
            if not included_sheets.get(sheet_name, True):
                logger.info(f"[PDW Preview] Skipping excluded sheet: {sheet_name}")
                continue

            header_row = header_rows.get(sheet_name, 0)
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

            # Apply column mappings for this sheet
            if sheet_name in column_mappings:
                sheet_mappings = column_mappings[sheet_name]

                # Build rename dict and columns to keep
                rename_dict = {}
                columns_to_keep = []

                for original_name, col_data in sheet_mappings.items():
                    if col_data.get('included', True):
                        new_name = col_data.get('newName', original_name)
                        # Only rename if name changed
                        if new_name != original_name and original_name in df.columns:
                            rename_dict[original_name] = new_name
                            columns_to_keep.append(new_name)
                        elif original_name in df.columns:
                            columns_to_keep.append(original_name)

                # Rename columns
                if rename_dict:
                    df = df.rename(columns=rename_dict)
                    logger.info(f"[PDW Preview] Renamed columns in {sheet_name}: {rename_dict}")

                # Keep only included columns
                if columns_to_keep:
                    # Filter to columns that actually exist
                    valid_columns = [col for col in columns_to_keep if col in df.columns]
                    df = df[valid_columns]
                    logger.info(f"[PDW Preview] Kept {len(valid_columns)} columns in {sheet_name}")

            dataframes.append(df)
            logger.info(f"[PDW Preview] Included sheet: {sheet_name} ({len(df)} rows, {len(df.columns)} cols)")

        # Check if any sheets were included
        if not dataframes:
            return JsonResponse({
                'error': 'No sheets selected. Please include at least one sheet.'
            }, status=400)

        # Combine all sheets
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Store combined data in session
        request.session['pdw_combined_data'] = combined_df.to_json(orient='split')
        request.session['pdw_columns'] = list(combined_df.columns)
        request.session.modified = True

        logger.info(f"[PDW Preview] Combined {len(dataframes)} sheets into {len(combined_df)} rows, {len(combined_df.columns)} columns")

        # Get pagination parameters
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)

        # Return paginated preview
        preview_data = combined_df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

        return JsonResponse({
            'success': True,
            'total_rows': len(combined_df),
            'total_cols': len(combined_df.columns),
            'columns': list(combined_df.columns),
            'preview': preview_data,
            'offset': offset,
            'limit': limit,
        })

    except Exception as e:
        logger.error(f"[PDW Preview] Error generating preview: {e}", exc_info=True)
        return JsonResponse({
            'error': f'Failed to generate preview: {str(e)}'
        }, status=500)


@csrf_exempt
@require_product('pdw-data-prep')
def pdw_apply_rule(request):
    """
    Apply data cleaning rule to a column
    Rules: uppercase, lowercase, trim, replace, remove_duplicates
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        rule_type = data.get('rule')
        column = data.get('column')
        params = data.get('params', {})
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)

        # Load current data from session
        combined_json = request.session.get('pdw_combined_data')
        if not combined_json:
            return JsonResponse({'error': 'No data in session'}, status=400)

        df = pd.read_json(combined_json, orient='split')

        logger.info(f"[PDW Rule] Applying {rule_type} to column '{column}'")

        # Apply rule
        if rule_type == 'uppercase':
            df[column] = df[column].astype(str).str.upper()
        elif rule_type == 'lowercase':
            df[column] = df[column].astype(str).str.lower()
        elif rule_type == 'trim':
            df[column] = df[column].astype(str).str.strip()
        elif rule_type == 'replace':
            find_text = params.get('find', '')
            replace_text = params.get('replace', '')

            # Count how many replacements were made
            original_values = df[column].astype(str)
            df[column] = original_values.str.replace(find_text, replace_text, regex=False)
            replacements_count = (original_values != df[column]).sum()

            logger.info(f"[PDW Rule] Replaced '{find_text}' with '{replace_text}' in {column}: {replacements_count} changes")

            # Save with replacement count
            request.session['pdw_combined_data'] = df.to_json(orient='split')
            request.session.modified = True
            preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

            return JsonResponse({
                'success': True,
                'message': f'Replaced "{find_text}" with "{replace_text}" in {column} ({replacements_count} changes)',
                'total_rows': len(df),
                'preview': preview_data,
                'offset': offset,
                'limit': limit,
            })
        elif rule_type == 'format_upc':
            # Format as 11-digit UPC: must be exactly 11 numeric digits
            def format_upc(value):
                # Convert to string and remove any whitespace
                value_str = str(value).strip()
                # Take first 11 characters
                truncated = value_str[:11]
                # Must be exactly 11 characters AND all numeric
                if len(truncated) == 11 and truncated.isdigit():
                    return truncated
                else:
                    return ''

            df[column] = df[column].apply(format_upc)
            logger.info(f"[PDW Rule] Formatted {column} as 11-digit UPC")
        elif rule_type == 'delete_blank_rows':
            original_count = len(df)
            # Remove rows where selected column is blank/empty/whitespace
            df = df[df[column].astype(str).str.strip() != '']
            deleted_count = original_count - len(df)
            logger.info(f"[PDW Rule] Deleted {deleted_count} rows where {column} was blank")

            request.session['pdw_combined_data'] = df.to_json(orient='split')
            request.session.modified = True
            preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

            return JsonResponse({
                'success': True,
                'message': f'Deleted {deleted_count} rows where {column} was blank',
                'total_rows': len(df),
                'preview': preview_data,
                'offset': offset,
                'limit': limit,
            })
        elif rule_type == 'add_wsc_sell_group':
            new_column_name = params.get('newColumnName', 'WSC_Sell_Group')

            # Track non-numeric values
            non_numeric_count = 0

            def calculate_wsc_level(value):
                nonlocal non_numeric_count
                try:
                    # Convert to numeric
                    num_value = float(value)

                    # Apply nested IF logic
                    if num_value < 50:
                        return 'WSC-NS-LEVEL1'
                    elif num_value < 100:
                        return 'WSC-NS-LEVEL2'
                    elif num_value < 150:
                        return 'WSC-NS-LEVEL3'
                    elif num_value < 200:
                        return 'WSC-NS-LEVEL4'
                    elif num_value < 500:
                        return 'WSC-NS-LEVEL5'
                    else:
                        return 'WSC-NS-LEVEL6'
                except (ValueError, TypeError):
                    # Non-numeric value
                    non_numeric_count += 1
                    return ''

            # Apply calculation to create new column
            df[new_column_name] = df[column].apply(calculate_wsc_level)

            logger.info(f"[PDW Rule] Added WSC Sell Group column '{new_column_name}' from '{column}', {non_numeric_count} non-numeric values skipped")

            # Save and return with updated columns
            request.session['pdw_combined_data'] = df.to_json(orient='split')
            request.session['pdw_columns'] = list(df.columns)
            request.session.modified = True
            preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

            message = f'Added column "{new_column_name}" with WSC Sell Group levels'
            if non_numeric_count > 0:
                message += f' ({non_numeric_count} non-numeric values skipped)'

            return JsonResponse({
                'success': True,
                'message': message,
                'total_rows': len(df),
                'columns': list(df.columns),
                'preview': preview_data,
                'offset': offset,
                'limit': limit,
            })
        elif rule_type == 'format_numeric':
            # Format as numeric with 2 decimal places, removing dollar signs
            non_numeric_count = 0

            def format_numeric_value(value):
                nonlocal non_numeric_count
                try:
                    # Convert to string and remove dollar signs, commas, and whitespace
                    value_str = str(value).strip().replace('$', '').replace(',', '')
                    # Convert to float and round to 2 decimal places
                    num_value = float(value_str)
                    return round(num_value, 2)
                except (ValueError, TypeError):
                    non_numeric_count += 1
                    return ''

            df[column] = df[column].apply(format_numeric_value)

            message = f'Formatted {column} as numeric with 2 decimal places'
            if non_numeric_count > 0:
                message += f' ({non_numeric_count} non-numeric values skipped)'

            logger.info(f"[PDW Rule] {message}")

            # Save and return
            request.session['pdw_combined_data'] = df.to_json(orient='split')
            request.session.modified = True
            preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

            return JsonResponse({
                'success': True,
                'message': message,
                'total_rows': len(df),
                'preview': preview_data,
                'offset': offset,
                'limit': limit,
            })
        elif rule_type == 'multiply_by':
            # Multiply column by a fixed number and create new column
            multiplier = params.get('multiplier')
            new_column_name = params.get('newColumnName', f'{column}_multiplied')

            # Validate multiplier
            try:
                multiplier = float(multiplier)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid multiplier value'}, status=400)

            non_numeric_count = 0

            def multiply_value(value):
                nonlocal non_numeric_count
                try:
                    # Convert to string and remove dollar signs, commas, and whitespace
                    value_str = str(value).strip().replace('$', '').replace(',', '')
                    # Convert to float and multiply
                    num_value = float(value_str)
                    result = round(num_value * multiplier, 2)
                    # Log first value for debugging
                    if non_numeric_count == 0 and num_value > 0:
                        logger.info(f"[PDW Multiply Debug] First value: {num_value} × {multiplier} = {result}")
                    return result
                except (ValueError, TypeError):
                    non_numeric_count += 1
                    return ''

            # Create new column with multiplied values
            df[new_column_name] = df[column].apply(multiply_value)

            message = f'Created column "{new_column_name}" by multiplying {column} by {multiplier}'
            if non_numeric_count > 0:
                message += f' ({non_numeric_count} non-numeric values skipped)'

            logger.info(f"[PDW Rule] {message}")

            # Save and return with updated columns
            request.session['pdw_combined_data'] = df.to_json(orient='split')
            request.session['pdw_columns'] = list(df.columns)
            request.session.modified = True
            preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

            return JsonResponse({
                'success': True,
                'message': message,
                'total_rows': len(df),
                'columns': list(df.columns),
                'preview': preview_data,
                'offset': offset,
                'limit': limit,
            })
        elif rule_type == 'remove_duplicates':
            original_count = len(df)
            df = df.drop_duplicates()
            removed_count = original_count - len(df)
            logger.info(f"[PDW Rule] Removed {removed_count} duplicate rows")
        else:
            return JsonResponse({'error': f'Unknown rule: {rule_type}'}, status=400)

        # Save updated data back to session
        request.session['pdw_combined_data'] = df.to_json(orient='split')
        request.session.modified = True

        # Return updated preview with pagination
        preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

        return JsonResponse({
            'success': True,
            'message': f'Applied {rule_type} to {column}',
            'total_rows': len(df),
            'preview': preview_data,
            'offset': offset,
            'limit': limit,
        })

    except Exception as e:
        logger.error(f"[PDW Rule] Error applying rule: {e}")
        return JsonResponse({
            'error': f'Failed to apply rule: {str(e)}'
        }, status=500)


@csrf_exempt
@require_product('pdw-data-prep')
def pdw_smart_clean(request):
    """
    Smart Clean: Apply multiple common cleaning operations at once
    Actions: remove_blank, remove_sparse, remove_commas, uppercase, trim, format_numeric, format_upc
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        actions = data.get('actions', [])
        preview_mode = data.get('preview', False)
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)

        # Load current data from session
        combined_json = request.session.get('pdw_combined_data')
        if not combined_json:
            return JsonResponse({'error': 'No data in session'}, status=400)

        df = pd.read_json(combined_json, orient='split')
        original_row_count = len(df)
        stats = {}

        logger.info(f"[PDW Smart Clean] Starting with {original_row_count} rows, actions: {actions}")

        # If preview mode, just analyze and return stats
        if preview_mode:
            # Count blank rows
            blank_rows = df[df.isnull().all(axis=1)]
            stats['remove_blank'] = len(blank_rows)

            # Count sparse rows (fewer than 3 non-null values)
            sparse_rows = df[df.notna().sum(axis=1) < 3]
            stats['remove_sparse'] = len(sparse_rows)

            # Estimate comma removals (sample first 100 rows)
            sample_df = df.head(100)
            comma_count = 0
            for col in sample_df.columns:
                if sample_df[col].dtype == 'object':
                    comma_count += sample_df[col].astype(str).str.contains(',').sum()
            stats['remove_commas'] = f"~{comma_count * (len(df) // 100)} estimated"

            # Count text columns for uppercase/trim
            text_columns = [col for col in df.columns if df[col].dtype == 'object']
            stats['uppercase'] = f"{len(text_columns)} text columns"
            stats['trim'] = f"All {len(df.columns)} columns"

            # Count numeric columns
            numeric_columns = [col for col in df.columns if df[col].dtype in ['int64', 'float64', 'object']]
            stats['format_numeric'] = f"{len(numeric_columns)} columns"

            # Check for UPC column
            upc_columns = [col for col in df.columns if 'upc' in col.lower() or 'ean' in col.lower()]
            stats['format_upc'] = f"{len(upc_columns)} UPC columns found" if upc_columns else "No UPC columns detected"

            return JsonResponse({
                'success': True,
                'stats': stats,
                'total_rows': len(df)
            })

        # Apply mode - execute selected actions
        changes = []

        # 1. Remove completely blank rows
        if 'remove_blank' in actions:
            before = len(df)
            df = df.dropna(how='all')
            removed = before - len(df)
            changes.append(f"Removed {removed} completely blank rows")
            logger.info(f"[Smart Clean] Removed {removed} blank rows")

        # 2. Remove sparse rows (fewer than 3 non-null values)
        if 'remove_sparse' in actions:
            before = len(df)
            df = df[df.notna().sum(axis=1) >= 3]
            removed = before - len(df)
            changes.append(f"Removed {removed} sparse rows (< 3 values)")
            logger.info(f"[Smart Clean] Removed {removed} sparse rows")

        # 3. Remove commas from all text columns
        if 'remove_commas' in actions:
            comma_replacements = 0
            for col in df.columns:
                if df[col].dtype == 'object':
                    original = df[col].astype(str)
                    df[col] = original.str.replace(',', '', regex=False)
                    comma_replacements += (original != df[col]).sum()
            changes.append(f"Removed commas from all text columns ({comma_replacements} changes)")
            logger.info(f"[Smart Clean] Removed {comma_replacements} commas")

        # 4. Uppercase all text columns
        if 'uppercase' in actions:
            text_columns = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.upper()
                    text_columns.append(col)
            changes.append(f"Uppercased {len(text_columns)} text columns")
            logger.info(f"[Smart Clean] Uppercased {len(text_columns)} columns")

        # 5. Trim whitespace from all columns
        if 'trim' in actions:
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            changes.append(f"Trimmed whitespace from all columns")
            logger.info(f"[Smart Clean] Trimmed all columns")

        # 6. Format numeric columns (optional)
        if 'format_numeric' in actions:
            formatted_count = 0
            for col in df.columns:
                # Try to detect numeric columns by attempting conversion
                try:
                    # Check if column contains numeric-like data
                    sample = df[col].head(10).astype(str)
                    if sample.str.match(r'^[\$\d,\.\s-]+$').any():
                        non_numeric_count = 0

                        def format_num(value):
                            nonlocal non_numeric_count
                            try:
                                val_str = str(value).strip().replace('$', '').replace(',', '')
                                num_val = float(val_str)
                                return round(num_val, 2)
                            except (ValueError, TypeError):
                                non_numeric_count += 1
                                return value

                        df[col] = df[col].apply(format_num)
                        formatted_count += 1
                except:
                    pass
            changes.append(f"Formatted {formatted_count} numeric columns")
            logger.info(f"[Smart Clean] Formatted {formatted_count} numeric columns")

        # 7. Format UPC columns (optional)
        if 'format_upc' in actions:
            upc_columns = [col for col in df.columns if 'upc' in col.lower() or 'ean' in col.lower()]
            for col in upc_columns:
                def format_upc(value):
                    value_str = str(value).strip()
                    truncated = value_str[:11]
                    if len(truncated) == 11 and truncated.isdigit():
                        return truncated
                    else:
                        return ''
                df[col] = df[col].apply(format_upc)
            changes.append(f"Formatted {len(upc_columns)} UPC columns")
            logger.info(f"[Smart Clean] Formatted {len(upc_columns)} UPC columns")

        # Save updated data
        request.session['pdw_combined_data'] = df.to_json(orient='split')
        request.session['pdw_columns'] = list(df.columns)
        request.session.modified = True

        # Return updated preview
        preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

        final_row_count = len(df)
        rows_removed = original_row_count - final_row_count

        summary = f"Smart Clean complete: {rows_removed} rows removed, {len(changes)} operations applied"

        return JsonResponse({
            'success': True,
            'message': summary,
            'changes': changes,
            'total_rows': final_row_count,
            'rows_removed': rows_removed,
            'columns': list(df.columns),
            'preview': preview_data,
            'offset': offset,
            'limit': limit,
        })

    except Exception as e:
        logger.error(f"[PDW Smart Clean] Error: {e}", exc_info=True)
        return JsonResponse({
            'error': f'Smart Clean failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_product('pdw-data-prep')
def pdw_paginate(request):
    """
    Get paginated view of current processed data
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        offset = data.get('offset', 0)
        limit = data.get('limit', 50)

        # Load current data from session
        combined_json = request.session.get('pdw_combined_data')
        if not combined_json:
            return JsonResponse({'error': 'No data in session'}, status=400)

        df = pd.read_json(combined_json, orient='split')

        # Return paginated slice
        preview_data = df.iloc[offset:offset+limit].fillna('').to_dict(orient='records')

        return JsonResponse({
            'success': True,
            'preview': preview_data,
            'total_rows': len(df),
            'columns': list(df.columns),
            'offset': offset,
            'limit': limit,
        })

    except Exception as e:
        logger.error(f"[PDW Paginate] Error: {e}")
        return JsonResponse({
            'error': f'Failed to paginate: {str(e)}'
        }, status=500)


@require_product('pdw-data-prep')
def pdw_export(request):
    """
    Export cleaned data as CSV file
    """
    try:
        # Load current data from session
        combined_json = request.session.get('pdw_combined_data')
        if not combined_json:
            return JsonResponse({'error': 'No data to export'}, status=400)

        df = pd.read_json(combined_json, orient='split')

        # Get filename from query parameter
        user_filename = request.GET.get('filename', 'cleaned_data')
        # Remove any .csv extension if user added it
        user_filename = user_filename.replace('.csv', '')
        # Sanitize filename (remove invalid characters)
        import re
        safe_filename = re.sub(r'[^\w\s-]', '', user_filename).strip()
        csv_filename = f"{safe_filename}.csv"

        # Convert to CSV
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)

        logger.info(f"[PDW Export] Exporting {len(df)} rows as {csv_filename}")

        # Return as downloadable file
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{csv_filename}"'

        return response

    except Exception as e:
        logger.error(f"[PDW Export] Error exporting CSV: {e}")
        return JsonResponse({
            'error': f'Failed to export CSV: {str(e)}'
        }, status=500)
