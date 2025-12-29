"""
Analytics MongoDB Service - Direct MongoDB operations for PO Analytics

Uses pymongo directly for better performance and full MongoDB features
(aggregation, indexing, etc.) without djongo compatibility issues.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from decouple import config
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class AnalyticsMongoDBService:
    """
    Direct MongoDB service for Purchase Order analytics.
    Bypasses Django ORM for better MongoDB integration.
    """

    def __init__(self):
        self.client = None
        self.db = None
        self.purchase_orders = None
        self.import_logs = None
        self.connect()

    def connect(self):
        """Connect to MongoDB and create indexes"""
        try:
            mongodb_uri = config('MONGODB_URI')
            self.client = MongoClient(mongodb_uri)

            # Use the same database as Node.js backend
            if 'my-db-name' in mongodb_uri:
                db_name = 'my-db-name'
            else:
                db_name = 'emp54'

            self.db = self.client[db_name]
            self.purchase_orders = self.db['purchase_orders']
            self.import_logs = self.db['po_import_logs']

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB for Analytics: {db_name}")

            # Create indexes for performance
            self.create_indexes()

        except Exception as e:
            logger.error(f"❌ Analytics MongoDB connection failed: {e}")
            self.client = None
            self.db = None

    def create_indexes(self):
        """Create MongoDB indexes for fast analytics queries"""
        try:
            # Compound indexes for common query patterns
            self.purchase_orders.create_index([
                ('company_code', ASCENDING),
                ('po_payto_name', ASCENDING),
                ('order_date', DESCENDING)
            ], name='company_vendor_date')

            self.purchase_orders.create_index([
                ('company_code', ASCENDING),
                ('po_branch', ASCENDING),
                ('order_date', DESCENDING)
            ], name='company_branch_date')

            self.purchase_orders.create_index([
                ('company_code', ASCENDING),
                ('order_date', DESCENDING)
            ], name='company_date')

            self.purchase_orders.create_index([
                ('import_batch_id', ASCENDING)
            ], name='batch_id')

            # Import logs indexes
            self.import_logs.create_index([
                ('company_code', ASCENDING),
                ('imported_at', DESCENDING)
            ], name='company_imported')

            logger.info("✅ Created MongoDB indexes for analytics")

        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")

    def insert_purchase_order(self, po_data: Dict[str, Any]) -> str:
        """Insert a single purchase order and return its ID"""
        result = self.purchase_orders.insert_one(po_data)
        return str(result.inserted_id)

    def insert_many_purchase_orders(self, po_list: List[Dict[str, Any]]) -> int:
        """Bulk insert purchase orders and return count"""
        if not po_list:
            return 0
        result = self.purchase_orders.insert_many(po_list)
        return len(result.inserted_ids)

    def find_purchase_order(self, po_number: str, company_code: str) -> Optional[Dict[str, Any]]:
        """Find PO by number and company"""
        return self.purchase_orders.find_one({
            'po_number': po_number,
            'company_code': company_code
        })

    def delete_purchase_order(self, po_number: str, company_code: str) -> int:
        """Delete PO by number and company"""
        result = self.purchase_orders.delete_one({
            'po_number': po_number,
            'company_code': company_code
        })
        return result.deleted_count

    def delete_by_batch_id(self, batch_id: str, company_code: str) -> int:
        """Delete all POs from a specific import batch"""
        result = self.purchase_orders.delete_many({
            'import_batch_id': batch_id,
            'company_code': company_code
        })
        return result.deleted_count

    def delete_all_company_data(self, company_code: str) -> int:
        """Delete all PO data for a company"""
        result = self.purchase_orders.delete_many({
            'company_code': company_code
        })
        return result.deleted_count

    def count_purchase_orders(self, company_code: str, filters: Dict[str, Any] = None) -> int:
        """Count POs with optional filters"""
        query = {'company_code': company_code}
        if filters:
            query.update(filters)
        return self.purchase_orders.count_documents(query)

    def aggregate_vendors(self, company_code: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Aggregate spending by vendor"""
        match_query = {'company_code': company_code}
        if filters:
            match_query.update(filters)

        pipeline = [
            {'$match': match_query},
            {'$group': {
                '_id': '$po_payto_name',
                'total_spent': {'$sum': '$order_total'},
                'po_count': {'$sum': 1}
            }},
            {'$sort': {'total_spent': -1}},
            {'$project': {
                'vendor_name': '$_id',
                'total_spent': 1,
                'po_count': 1,
                '_id': 0
            }}
        ]

        return list(self.purchase_orders.aggregate(pipeline))

    def aggregate_branches(self, company_code: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Aggregate spending by branch"""
        match_query = {'company_code': company_code}
        if filters:
            match_query.update(filters)

        pipeline = [
            {'$match': match_query},
            {'$group': {
                '_id': '$po_branch',
                'total_spent': {'$sum': '$order_total'},
                'po_count': {'$sum': 1}
            }},
            {'$sort': {'total_spent': -1}},
            {'$project': {
                'branch': '$_id',
                'total_spent': 1,
                'po_count': 1,
                '_id': 0
            }}
        ]

        return list(self.purchase_orders.aggregate(pipeline))

    def aggregate_companies(self, company_code: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Aggregate spending by PO company"""
        match_query = {'company_code': company_code}
        if filters:
            match_query.update(filters)

        pipeline = [
            {'$match': match_query},
            {'$group': {
                '_id': '$po_company',
                'total_spent': {'$sum': '$order_total'},
                'po_count': {'$sum': 1}
            }},
            {'$sort': {'total_spent': -1}},
            {'$project': {
                'company': '$_id',
                'total_spent': 1,
                'po_count': 1,
                '_id': 0
            }}
        ]

        return list(self.purchase_orders.aggregate(pipeline))

    def aggregate_monthly_trends(self, company_code: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Aggregate spending by month"""
        match_query = {'company_code': company_code}
        if filters:
            match_query.update(filters)

        pipeline = [
            {'$match': match_query},
            {'$group': {
                '_id': {
                    'year': {'$year': '$order_date'},
                    'month': {'$month': '$order_date'}
                },
                'total_spent': {'$sum': '$order_total'},
                'po_count': {'$sum': 1}
            }},
            {'$sort': {'_id.year': 1, '_id.month': 1}},
            {'$project': {
                'month': {
                    '$concat': [
                        {'$toString': '$_id.year'},
                        '-',
                        {'$cond': [
                            {'$lt': ['$_id.month', 10]},
                            {'$concat': ['0', {'$toString': '$_id.month'}]},
                            {'$toString': '$_id.month'}
                        ]}
                    ]
                },
                'total_spent': 1,
                'po_count': 1,
                '_id': 0
            }}
        ]

        return list(self.purchase_orders.aggregate(pipeline))

    def get_filter_options(self, company_code: str) -> Dict[str, List[str]]:
        """Get distinct values for filters"""
        return {
            'vendors': self.purchase_orders.distinct('po_payto_name', {'company_code': company_code}),
            'branches': self.purchase_orders.distinct('po_branch', {'company_code': company_code}),
            'companies': self.purchase_orders.distinct('po_company', {'company_code': company_code})
        }

    # Import log methods
    def create_import_log(self, log_data: Dict[str, Any]) -> str:
        """Create an import log entry"""
        result = self.import_logs.insert_one(log_data)
        return str(result.inserted_id)

    def update_import_log(self, batch_id: str, updates: Dict[str, Any]) -> int:
        """Update import log by batch ID"""
        result = self.import_logs.update_one(
            {'import_batch_id': batch_id},
            {'$set': updates}
        )
        return result.modified_count

    def get_import_history(self, company_code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get import history for a company"""
        return list(self.import_logs.find(
            {'company_code': company_code}
        ).sort('imported_at', DESCENDING).limit(limit))

    def get_import_log(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get import log by batch ID"""
        return self.import_logs.find_one({'import_batch_id': batch_id})


# Create singleton instance
analytics_mongodb = AnalyticsMongoDBService()
