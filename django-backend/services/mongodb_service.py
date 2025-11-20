"""
MongoDB Service - Handle user and company lookups
Mirrors the Node.js backend's MongoDB integration
"""

from pymongo import MongoClient
from decouple import config
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    MongoDB service for user and company data
    Connects to the same MongoDB instance as the Node.js backend
    """

    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = config('MONGODB_URI')
            self.client = MongoClient(mongodb_uri)

            # Use the same database as Node.js backend
            # Extract database name from URI or use default
            if 'my-db-name' in mongodb_uri:
                db_name = 'my-db-name'
            else:
                db_name = 'emp54'

            self.db = self.client[db_name]

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB database: {db_name}")

        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.db = None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find user by email address (same as Node.js User.findOne({ email }))

        Args:
            email: User's email address

        Returns:
            User document with populated company data, or None if not found
        """
        if self.db is None:
            logger.error("MongoDB not connected")
            return None

        try:
            # Find user by email
            users_collection = self.db.users
            user = users_collection.find_one({'email': email})

            if not user:
                logger.info(f"User not found for email: {email}")
                return None

            # Populate company data (like Node.js .populate('companyId'))
            if user.get('companyId'):
                companies_collection = self.db.companies
                company = companies_collection.find_one({'_id': user['companyId']})
                if company:
                    user['companyId'] = company
                    logger.info(f"Found user {email} with company {company.get('companyCode', 'unknown')}")
                else:
                    logger.warning(f"Company not found for user {email}")

            return user

        except Exception as e:
            logger.error(f"Error finding user {email}: {e}")
            return None

    def find_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Find company by ID

        Args:
            company_id: Company ObjectId as string

        Returns:
            Company document or None if not found
        """
        if self.db is None:
            logger.error("MongoDB not connected")
            return None

        try:
            from bson import ObjectId
            companies_collection = self.db.companies
            company = companies_collection.find_one({'_id': ObjectId(company_id)})

            if company:
                logger.info(f"Found company: {company.get('companyCode', 'unknown')}")

            return company

        except Exception as e:
            logger.error(f"Error finding company {company_id}: {e}")
            return None

    def verify_user_password(self, user: Dict[str, Any], password: str) -> bool:
        """
        Verify user password using bcrypt (same as Node.js backend)

        Args:
            user: User document from MongoDB
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        try:
            import bcrypt

            user_type = user.get('userType')
            user_email = user.get('email', 'unknown')

            if user_type == 'admin':
                # For admin users, verify against hashedPassword
                hashed_password = user.get('hashedPassword')
                if not hashed_password:
                    logger.error(f"Admin user {user_email} has no hashed password")
                    return False

                logger.info(f"[Password Verify] Verifying password for admin user {user_email}")
                logger.info(f"[Password Verify] Hash type: {type(hashed_password)}, Hash length: {len(hashed_password) if hashed_password else 0}")

                # Convert password to bytes
                password_bytes = password.encode('utf-8')

                # Hash might be string or bytes in MongoDB
                if isinstance(hashed_password, str):
                    hashed_password_bytes = hashed_password.encode('utf-8')
                else:
                    hashed_password_bytes = hashed_password

                result = bcrypt.checkpw(password_bytes, hashed_password_bytes)
                logger.info(f"[Password Verify] Result: {result}")
                return result

            elif user_type == 'customer':
                # For customer users, password will be verified against ERP
                # This method just validates that we have the required ERP fields
                return bool(user.get('erpUserName') and user.get('companyId'))

            else:
                logger.error(f"Unknown user type: {user_type}")
                return False

        except Exception as e:
            logger.error(f"Error verifying password for user {user.get('email')}: {e}")
            logger.exception(e)  # Full stack trace
            return False

    def get_user_erp_info(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract ERP connection info from user and company data

        Args:
            user: User document with populated company data

        Returns:
            Dictionary with ERP connection parameters
        """
        try:
            company = user.get('companyId', {})

            return {
                'erp_username': user.get('erpUserName'),
                'company_api_base': company.get('apiBaseUrl'),
                'last_port': user.get('lastPort', '5000'),
                'company_code': company.get('companyCode'),
                'user_id': str(user.get('_id')),
                'company_id': str(company.get('_id')) if company.get('_id') else None
            }

        except Exception as e:
            logger.error(f"Error extracting ERP info: {e}")
            return {}

    def update_user_port(self, user_id, new_port: str) -> bool:
        """
        Update user's lastPort in MongoDB

        Args:
            user_id: User ObjectId (can be string or ObjectId)
            new_port: New port number as string

        Returns:
            True if update was successful, False otherwise
        """
        if self.db is None:
            logger.error("MongoDB not connected")
            return False

        try:
            from bson import ObjectId

            # Convert to ObjectId if it's a string
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)

            users_collection = self.db.users
            result = users_collection.update_one(
                {'_id': user_id},
                {'$set': {'lastPort': new_port}}
            )

            if result.modified_count > 0:
                logger.info(f"Updated lastPort to {new_port} for user {user_id}")
                return True
            else:
                logger.warning(f"No user found with ID {user_id} or port was already {new_port}")
                return False

        except Exception as e:
            logger.error(f"Error updating user port: {e}")
            return False

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global MongoDB service instance
mongodb_service = MongoDBService()