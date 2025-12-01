#!/bin/bash
#
# Warehouse Email Processing Scheduler
#
# This script runs the warehouse email processing pipeline:
# 1. Fetch emails from Zoho IMAP and upload CSV files to Wasabi
# 2. Process CSV files from Wasabi into MongoDB
#
# Schedule this to run every 5 minutes via Railway cron or system cron

set -e  # Exit on error

echo "========================================="
echo "Warehouse Email Processing - $(date)"
echo "========================================="

# Change to Django project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DJANGO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DJANGO_DIR"

echo ""
echo "[1/2] Fetching emails from Zoho IMAP..."
python manage.py fetch_warehouse_emails

echo ""
echo "[2/2] Processing CSV files into MongoDB..."
python manage.py process_warehouse_csv

echo ""
echo "✅ Warehouse email processing complete - $(date)"
echo "========================================="
