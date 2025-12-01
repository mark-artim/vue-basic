#!/usr/bin/env python
"""
Quick test script to verify warehouse email processing setup

Usage: python scripts/test_warehouse_setup.py
"""

import os
import sys

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("\n" + "="*60)
    print("Testing Environment Variables")
    print("="*60)

    from decouple import config

    required_vars = {
        'ZOHO_EMAIL': 'Zoho email address',
        'ZOHO_PASSWORD': 'Zoho email password',
        'WASABI_ACCESS_KEY': 'Wasabi access key',
        'WASABI_SECRET_KEY': 'Wasabi secret key',
        'WASABI_BUCKET_NAME': 'Wasabi bucket name',
        'MONGO_URI': 'MongoDB connection URI',
    }

    all_set = True
    for var, description in required_vars.items():
        try:
            value = config(var)
            # Mask sensitive values
            if 'PASSWORD' in var or 'SECRET' in var:
                masked = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '***'
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        except Exception as e:
            print(f"❌ {var}: NOT SET ({description})")
            all_set = False

    return all_set


def test_dependencies():
    """Test that required Python packages are installed"""
    print("\n" + "="*60)
    print("Testing Python Dependencies")
    print("="*60)

    required_packages = [
        'imap_tools',
        'boto3',
        'pymongo',
        'django',
        'decouple',
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED")
            all_installed = False

    return all_installed


def test_wasabi_connection():
    """Test connection to Wasabi S3"""
    print("\n" + "="*60)
    print("Testing Wasabi S3 Connection")
    print("="*60)

    try:
        from services.wasabi_client import wasabi_client

        # Try to list files (should work even if bucket is empty)
        files = wasabi_client.list_files(prefix='')
        print(f"✅ Connected to Wasabi bucket: {wasabi_client.bucket_name}")
        print(f"   Found {len(files)} files in bucket")
        return True
    except Exception as e:
        print(f"❌ Wasabi connection failed: {e}")
        return False


def test_mongodb_connection():
    """Test connection to MongoDB"""
    print("\n" + "="*60)
    print("Testing MongoDB Connection")
    print("="*60)

    try:
        from pymongo import MongoClient
        from decouple import config

        mongo_uri = config('MONGO_URI')
        db_name = config('DB_NAME', default='emp54')

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]

        # Test connection
        client.server_info()

        # Check warehouse_invoices collection
        count = db.warehouse_invoices.count_documents({})

        print(f"✅ Connected to MongoDB: {db_name}")
        print(f"   warehouse_invoices collection: {count} documents")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


def test_email_connection():
    """Test connection to Zoho IMAP"""
    print("\n" + "="*60)
    print("Testing Zoho IMAP Connection")
    print("="*60)

    try:
        from imap_tools import MailBox
        from decouple import config

        email_address = config('ZOHO_EMAIL')
        email_password = config('ZOHO_PASSWORD')
        imap_server = config('ZOHO_IMAP_SERVER', default='imap.zoho.com')

        # Try to connect (don't fetch emails, just test connection)
        with MailBox(imap_server).login(email_address, email_password):
            print(f"✅ Connected to {imap_server} as {email_address}")
            return True
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Warehouse Email Processing - Setup Verification")
    print("="*60)

    results = {
        'Environment Variables': test_environment_variables(),
        'Python Dependencies': test_dependencies(),
        'Wasabi S3': test_wasabi_connection(),
        'MongoDB': test_mongodb_connection(),
        'Zoho IMAP': test_email_connection(),
    }

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! Setup is complete.")
        print("\nYou can now run:")
        print("  python manage.py fetch_warehouse_emails")
        print("  python manage.py process_warehouse_csv")
    else:
        print("❌ Some tests failed. Please check configuration.")
        print("\nRefer to WAREHOUSE_EMAIL_PROCESSING.md for setup instructions.")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
