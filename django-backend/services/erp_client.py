"""
ERP Client Service - Django equivalent of Node.js erpProxy.js

This service handles all ERP API communications with proper authentication,
Redis token management, and error handling for all business entities.
"""

import requests
import json
import logging
import base64
import time
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

    def refresh_session(
        self,
        refresh_token: str,
        company_api_base: str,
        user_id: str,
        port: int = 5000
    ) -> Dict[str, Any]:
        """
        Refresh an expired ERP session using refresh token

        Args:
            refresh_token: Refresh token from previous session
            company_api_base: Company's ERP base URL
            user_id: User ID to update token for
            port: ERP port

        Returns:
            New session data with sessionToken, refreshToken, expiresIn

        Raises:
            ERPClientError: If refresh fails
        """
        try:
            url = f"{company_api_base}:{port}/SessionRefresh"
            payload = {"refreshToken": refresh_token}

            logger.info(f"[Session Refresh] Refreshing session for user {user_id}")

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            session_data = response.json()

            # Update Redis with new token
            new_token = session_data.get('sessionToken')
            if new_token:
                redis_key = f"erpToken:{user_id}"
                self._redis_set(redis_key, new_token, 7200)
                logger.info(f"[Session Refresh] ✅ Session refreshed successfully for user {user_id}")

            return session_data

        except requests.exceptions.RequestException as e:
            error_msg = f"Session refresh failed: {str(e)}"
            logger.error(f"[Session Refresh] {error_msg}")
            raise ERPClientError(error_msg)

    def check_and_refresh_session(self, request) -> bool:
        """
        Check if session is about to expire and refresh it if needed

        Args:
            request: Django request object with session data

        Returns:
            True if session is valid/refreshed, False if refresh failed
        """
        from datetime import datetime, timedelta

        # Only check for customer users (not admin users)
        if request.session.get('customer_user_type') != 'customer':
            return True

        expires_at_str = request.session.get('customer_token_expires_at')
        refresh_token = request.session.get('customer_refresh_token')

        if not expires_at_str or not refresh_token:
            # No expiration tracking, assume valid
            return True

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now()

            # Refresh if session expires in less than 5 minutes
            buffer = timedelta(minutes=5)

            if now + buffer >= expires_at:
                logger.info(f"[Auto Refresh] Session expires soon, refreshing...")

                # Get session info for refresh
                user_id = request.session.get('customer_user_id')
                company_api_base = request.session.get('customer_company_api_base')
                port = int(request.session.get('customer_last_port', 5000))

                # Refresh the session
                try:
                    session_data = self.refresh_session(
                        refresh_token=refresh_token,
                        company_api_base=company_api_base,
                        user_id=user_id,
                        port=port
                    )

                    # Update session with new data
                    request.session['customer_erp_token'] = session_data.get('sessionToken')
                    request.session['customer_refresh_token'] = session_data.get('refreshToken')

                    new_expires_in = session_data.get('expiresIn')
                    if new_expires_in:
                        new_expires_at = datetime.now() + timedelta(seconds=new_expires_in)
                        request.session['customer_token_expires_at'] = new_expires_at.isoformat()
                        logger.info(f"[Auto Refresh] ✅ Session refreshed, new expiration: {new_expires_at.isoformat()}")

                    return True

                except ERPClientError as e:
                    logger.error(f"[Auto Refresh] ❌ Failed to refresh session: {e}")
                    return False
            else:
                # Session still valid
                time_remaining = expires_at - now
                logger.debug(f"[Session Check] Session valid for {int(time_remaining.total_seconds() / 60)} more minutes")
                return True

        except Exception as e:
            logger.error(f"[Auto Refresh] Error checking session: {e}")
            return True  # Don't block request on check error

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

        # Retry logic for transient failures (Railway production issue)
        max_retries = 2
        retry_delay = 0.5  # Start with 500ms
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"[ERP] Retry attempt {attempt}/{max_retries} for {endpoint}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

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

                # Track request timing
                start_time = time.time()

                response = requests.request(
                    method=method,
                    url=full_url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.default_timeout
                )

                elapsed_ms = (time.time() - start_time) * 1000

                logger.info(f"ERP Response Status: {response.status_code} (took {elapsed_ms:.0f}ms)")
                logger.info(f"ERP Response Headers: {dict(response.headers)}")
                if response.content:
                    logger.info(f"ERP Response Body: {response.text[:1000]}...")

                # Log slow requests (might indicate timeout/rate limit issues)
                if elapsed_ms > 5000:
                    logger.warning(f"[ERP] SLOW REQUEST: {endpoint} took {elapsed_ms:.0f}ms")

                # Check for HTTP errors
                response.raise_for_status()

                return response.json()

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"[ERP] Timeout on attempt {attempt + 1}, retrying...")
                    continue
                raise ERPClientError(f"ERP request timeout after {max_retries + 1} attempts: {full_url}")

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"[ERP] Connection error on attempt {attempt + 1}, retrying...")
                    continue
                raise ERPClientError(f"ERP connection error after {max_retries + 1} attempts: {full_url}")

            except requests.exceptions.RequestException as e:
                last_exception = e

                # Don't retry 404s - those are legitimate "not found" responses
                if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                    elapsed_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                    logger.warning(
                        f"[ERP] 404 Not Found: {endpoint} (took {elapsed_ms:.0f}ms) | "
                        f"This might be a Railway-specific issue if it works locally"
                    )
                    # Fall through to error handling

                # For other errors, only retry if not on last attempt
                elif attempt < max_retries and hasattr(e, 'response') and e.response is not None:
                    status = e.response.status_code
                    # Retry on 5xx errors and 429 (rate limit)
                    if status >= 500 or status == 429:
                        logger.warning(f"[ERP] Status {status} on attempt {attempt + 1}, retrying...")
                        continue

                # If we get here, we're done retrying - raise the error
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
                            error_msg = f"ERP request failed: {method} {full_url} - Status: {status_code}, Details: {error_data}"
                        except:
                            error_msg = f"ERP request failed: {method} {full_url} - Status: {status_code}"
                else:
                    error_msg = f"ERP request failed: {method} {full_url} - {str(e)}"

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
        # Extract port if provided, otherwise use None (will use default)
        port = kwargs.pop('port', None)
        params = {'keyword': keyword, **kwargs}
        return self.make_erp_request(user_id, company_api_base, 'GET', '/Vendors', params=params, port=port)

    def get_sales_orders(self, user_id: str, company_api_base: str, **kwargs):
        """Get sales orders with filtering"""
        return self.make_erp_request(user_id, company_api_base, 'GET', '/SalesOrders', params=kwargs)

    def get_purchase_orders(self, user_id: str, company_api_base: str, **kwargs):
        """Get purchase orders with filtering"""
        return self.make_erp_request(user_id, company_api_base, 'GET', '/PurchaseOrders', params=kwargs)

    def create_entity(self, user_id: str, company_api_base: str, endpoint: str, data: Dict, port: Optional[int] = None):
        """Generic entity creation"""
        return self.make_erp_request(user_id, company_api_base, 'POST', endpoint, data=data, port=port)

    def update_entity(self, user_id: str, company_api_base: str, endpoint: str, data: Dict, port: Optional[int] = None):
        """Generic entity update"""
        return self.make_erp_request(user_id, company_api_base, 'PUT', endpoint, data=data, port=port)

    def delete_entity(self, user_id: str, company_api_base: str, endpoint: str, port: Optional[int] = None):
        """Generic entity deletion"""
        return self.make_erp_request(user_id, company_api_base, 'DELETE', endpoint, port=port)

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