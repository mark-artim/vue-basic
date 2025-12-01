#!/usr/bin/env python
"""
Test script to verify warehouse CSV parsing works correctly

Usage: python scripts/test_csv_parsing.py
"""

import csv
import sys
import os

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_csv_parsing():
    """Test parsing the sample warehouse queue CSV"""
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_warehouse_queue.csv')

    if not os.path.exists(csv_path):
        print(f"❌ Sample CSV not found: {csv_path}")
        return False

    print("="*60)
    print("Testing Warehouse CSV Parsing")
    print("="*60)
    print(f"File: {csv_path}\n")

    records = []

    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        # Read first line and strip whitespace from column names
        first_line = csvfile.readline()
        fieldnames = [name.strip() for name in first_line.split(',')]

        # Create DictReader with cleaned fieldnames
        reader = csv.DictReader(csvfile, fieldnames=fieldnames, skipinitialspace=True)

        print(f"Column names detected: {fieldnames}\n")

        for row_num, row in enumerate(reader, start=2):
            # Skip empty rows
            if not any(row.values()):
                print(f"Row {row_num}: SKIPPED (empty row)")
                continue

            # Map Eclipse CSV columns to MongoDB document
            full_oid = row.get('FULL.OID', '').strip()
            branch = row.get('BR', '').strip()
            print_status = row.get('PRT', '').strip()
            ship_via = row.get('SHIP.VIA', '').strip()

            # Skip records with missing FULL.OID
            if not full_oid:
                print(f"Row {row_num}: SKIPPED (missing FULL.OID)")
                continue

            record = {
                'fullInvoiceID': full_oid,
                'branch': branch,
                'printStatus': print_status,
                'shipVia': ship_via,
            }

            records.append(record)
            print(f"Row {row_num}: OK {full_oid:20} BR={branch:4} PRT={print_status:2} SHIP.VIA={ship_via}")

    print("\n" + "="*60)
    print(f"Total records parsed: {len(records)}")
    print("="*60)

    # Show sample records
    if records:
        print("\nSample MongoDB documents:")
        for i, record in enumerate(records[:3], 1):
            print(f"\nRecord {i}:")
            print(f"  companyCode: 'heritage'")
            print(f"  fullInvoiceID: '{record['fullInvoiceID']}'")
            print(f"  branch: '{record['branch']}'")
            print(f"  printStatus: '{record['printStatus']}'")
            print(f"  shipVia: '{record['shipVia']}'")
            print(f"  lastUpdated: ISODate(...)")

    # Filter records with printStatus='Q'
    q_records = [r for r in records if r['printStatus'] == 'Q']
    print(f"\n>> Records with PRT='Q' (awaiting pickup): {len(q_records)}/{len(records)}")

    # Group by branch
    branches = {}
    for record in records:
        branch = record['branch']
        if branch not in branches:
            branches[branch] = 0
        branches[branch] += 1

    print(f"\nRecords by branch:")
    for branch, count in sorted(branches.items()):
        print(f"  {branch}: {count} records")

    print("\n" + "="*60)
    print(">> CSV parsing test complete!")
    print("="*60)

    return True


if __name__ == '__main__':
    success = test_csv_parsing()
    sys.exit(0 if success else 1)
