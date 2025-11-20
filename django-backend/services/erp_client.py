"""
ERP Client Service - Django equivalent of Node.js erpProxy.js

This service handles all ERP API communications with proper authentication,
Redis token management, and error handling for all business entities.
"""

import requests
import json
import logging
import base64
from typing import Optional, Dict, Any, Union
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)

class ERPClientError(Exception):
    """Custom exception for ERP client errors"""
    pass

class ERPClient:
    """
    Core ERP client that handles authentication and API communication
    Designed to support all business entities: Products, Customers, Vendors,
    Sales Orders, Purchase Orders, etc.
    """

    def __init__(self):
        # Upstash Redis REST API configuration (same as Node.js backend)
        self.redis_rest_url = config('UPSTASH_REDIS_REST_URL', default=None)
        self.redis_rest_token = config('UPSTASH_REDIS_REST_TOKEN', default=None)

        if self.redis_rest_url and self.redis_rest_token:
            logger.info("Using Upstash Redis REST API for ERP token caching")
        else:
            logger.warning("Upstash Redis not configured, ERP tokens will not be cached")

        self.default_timeout = 30

    def _redis_get(self, key: str) -> Optional[str]:
        """
        Get value from Upstash Redis using REST API
        """
        if not self.redis_rest_url or not self.redis_rest_token:
            return None

        try:
            url = f"{self.redis_rest_url}/get/{key}"
            headers = {
                'Authorization': f'Bearer {self.redis_rest_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                result = response.json()
                return result.get('result')
            return None

        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def _redis_set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set value in Upstash Redis using REST API
        """
        if not self.redis_rest_url or not self.redis_rest_token:
            return False

        try:
            url = f"{self.redis_rest_url}/setex/{key}/{ttl}/{value}"
            headers = {
                'Authorization': f'Bearer {self.redis_rest_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, timeout=5)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def _redis_delete(self, key: str) -> bool:
        """
        Delete key from Upstash Redis using REST API
        """
        if not self.redis_rest_url or not self.redis_rest_token:
            return False

        try:
            url = f"{self.redis_rest_url}/del/{key}"
            headers = {
                'Authorization': f'Bearer {self.redis_rest_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, timeout=5)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def get_erp_token(self, user_id: str) -> Optional[str]:
        """
        Get ERP session token from Redis cache

        Args:
            user_id: User ID to lookup token for

        Returns:
            ERP session token or None if not found
        """
        redis_key = f"erpToken:{user_id}"
        token = self._redis_get(redis_key)

        if token is None:
            logger.error(f"Redis error getting ERP token for user {user_id}: No token found")

        return token

    def make_erp_request(
        self,
        user_id: str,
        company_api_base: str,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        port: Optional[int] = None,
        last_port: Optional[int] = 5000
    ) -> Dict[str, Any]:
        """
        Make authenticated request to ERP system

        Args:
            user_id: User ID for token lookup
            company_api_base: Company's ERP base URL
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: ERP endpoint (e.g., '/Products', '/Customers')
            data: Request body data
            params: Query parameters
            port: Override port (defaults to last_port)
            last_port: Default port to use

        Returns:
            ERP response data

        Raises:
            ERPClientError: If request fails
        """

        # Get ERP token
        erp_token = self.get_erp_token(user_id)
        if not erp_token:
            raise ERPClientError(
                f"ERP authentication failed for user '{user_id}'. "
                "Please ensure you are logged in and have a valid ERP session token."
            )

        # Build request URL
        final_port = port or last_port
        full_url = f"{company_api_base}:{final_port}{endpoint}"

        # Prepare headers (same pattern as Node.js)
        headers = {
            'Authorization': f'SessionToken {requests.utils.unquote(erp_token)}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        try:
            logger.info(f"ERP Request: {method} {full_url}")
            logger.info(f"ERP Headers: {headers}")
            if data:
                logger.info(f"ERP Request Body: {json.dumps(data, indent=2)}")
            if params:
                logger.info(f"ERP Query Params: {params}")

            # Console-style logging for debugging
            print(f"\n===== ERP API CALL DEBUG =====")
            print(f"URL: {full_url}")
            print(f"METHOD: {method}")
            if data:
                # Show key fields for debugging instead of massive JSON
                if isinstance(data, dict):
                    key_fields = {}
                    for key in ['id', 'FileName', 'DESC.OVRD.NUC', 'keywords', 'description', 'updateKey']:
                        if key in data:
                            key_fields[key] = data[key]
                    print(f"BODY KEY FIELDS: {json.dumps(key_fields, indent=2)}")
                    print(f"BODY TOTAL FIELDS: {len(data.keys()) if hasattr(data, 'keys') else 'unknown'}")
                else:
                    print(f"BODY: {json.dumps(data, indent=2)}")
            if params:
                print(f"PARAMS: {params}")
            print(f"================================\n")

            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.default_timeout
            )

            logger.info(f"ERP Response Status: {response.status_code}")
            logger.info(f"ERP Response Headers: {dict(response.headers)}")
            if response.content:
                logger.info(f"ERP Response Body: {response.text[:1000]}...")

            # Check for HTTP errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"ERP request failed: {method} {full_url}"

            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code

                if status_code == 401:
                    error_msg = f"ERP authentication failed (401). Please re-login to refresh your ERP session token."
                elif status_code == 403:
                    error_msg = f"ERP access denied (403). User '{user_id}' may not have permission for this operation."
                elif status_code == 404:
                    error_msg = f"ERP endpoint not found (404): {full_url}. Check the API endpoint configuration."
                elif status_code >= 500:
                    error_msg = f"ERP server error ({status_code}). The ERP system may be temporarily unavailable."
                else:
                    try:
                        error_data = e.response.json()
                        error_msg += f" - Status: {status_code}, Details: {error_data}"
                    except:
                        error_msg += f" - Status: {status_code}"
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_msg = f"Cannot connect to ERP server at {full_url}. Please check the server is running and accessible."
            elif isinstance(e, requests.exceptions.Timeout):
                error_msg = f"ERP request timed out after {self.default_timeout} seconds. Server may be overloaded."

            logger.error(error_msg)
            raise ERPClientError(error_msg)

    def search_products(
        self,
        user_id: str,
        company_api_base: str,
        keyword: str,
        include_inactive: bool = True,
        page_size: int = 50,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search products via ERP API

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            keyword: Search keyword
            include_inactive: Include inactive products
            page_size: Number of results to return
            port: ERP port override

        Returns:
            Product search results from ERP
        """
        params = {
            'keyword': keyword,
            'includeInactive': include_inactive,
            'pageSize': page_size
        }

        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint='/Products',
            params=params,
            port=port
        )

    def get_product(
        self,
        user_id: str,
        company_api_base: str,
        product_id: str,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get single product by ID

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            product_id: Product ID to retrieve
            port: ERP port override

        Returns:
            Product data from ERP
        """
        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Products/{product_id}',
            port=port
        )

    def update_product(
        self,
        user_id: str,
        company_api_base: str,
        product_id: str,
        product_data: Dict[str, Any],
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update product via Products endpoint

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            product_id: Product ID to update
            product_data: Full product data object with updateKey (ERP requirement)
            port: ERP port override

        Returns:
            Update response from ERP
        """
        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='PUT',
            endpoint=f'/Products/{product_id}',
            data=product_data,
            port=port
        )

    def get_product_class(
        self,
        user_id: str,
        company_api_base: str,
        product_id: str,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get PROD.CLASS via UserDefined endpoint

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            product_id: Product ID to retrieve
            port: ERP port override

        Returns:
            PROD.CLASS data from ERP
        """
        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/UserDefined/PROD.CLASS?id={product_id}',
            port=port
        )

    def update_product_class(
        self,
        user_id: str,
        company_api_base: str,
        product_id: str,
        product_data: Dict[str, Any],
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update PROD.CLASS via UserDefined endpoint

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            product_id: Product ID to update
            product_data: PROD.CLASS data (e.g., {'DESC.OVRD.NUC': 'description'})
            port: ERP port override

        Returns:
            Update response from ERP
        """
        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='PUT',
            endpoint=f'/UserDefined/PROD.CLASS?id={product_id}',
            data=product_data,
            port=port
        )

    # Generic CRUD methods for other entities
    def search_customers(self, user_id: str, company_api_base: str, keyword: str, **kwargs):
        """Search customers - follows same pattern as products"""
        params = {'keyword': keyword, **kwargs}
        return self.make_erp_request(user_id, company_api_base, 'GET', '/Customers', params=params)

    def search_vendors(self, user_id: str, company_api_base: str, keyword: str, **kwargs):
        """Search vendors - follows same pattern as products"""
        params = {'keyword': keyword, **kwargs}
        return self.make_erp_request(user_id, company_api_base, 'GET', '/Vendors', params=params)

    def get_sales_orders(self, user_id: str, company_api_base: str, **kwargs):
        """Get sales orders with filtering"""
        return self.make_erp_request(user_id, company_api_base, 'GET', '/SalesOrders', params=kwargs)

    def get_purchase_orders(self, user_id: str, company_api_base: str, **kwargs):
        """Get purchase orders with filtering"""
        return self.make_erp_request(user_id, company_api_base, 'GET', '/PurchaseOrders', params=kwargs)

    def create_entity(self, user_id: str, company_api_base: str, endpoint: str, data: Dict):
        """Generic entity creation"""
        return self.make_erp_request(user_id, company_api_base, 'POST', endpoint, data=data)

    def update_entity(self, user_id: str, company_api_base: str, endpoint: str, data: Dict):
        """Generic entity update"""
        return self.make_erp_request(user_id, company_api_base, 'PUT', endpoint, data=data)

    def delete_entity(self, user_id: str, company_api_base: str, endpoint: str):
        """Generic entity deletion"""
        return self.make_erp_request(user_id, company_api_base, 'DELETE', endpoint)

    def get_user(
        self,
        user_id: str,
        company_api_base: str,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get user details from ERP

        Args:
            user_id: User ID to retrieve
            company_api_base: Company ERP base URL
            port: ERP port override

        Returns:
            User data from ERP (includes name, email, etc.)
        """
        return self.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Users/{user_id}',
            port=port
        )


# Global ERP client instance
erp_client = ERPClient()