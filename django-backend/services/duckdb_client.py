"""
DuckDB Client for Analytical Queries

Provides high-performance analytical queries on Parquet files stored in Wasabi S3.
Perfect for read-only analysis of large datasets (millions of rows).
"""

import duckdb
from decouple import config
import logging

logger = logging.getLogger(__name__)


class DuckDBClient:
    """Client for querying Parquet files with DuckDB"""

    def __init__(self):
        # Get Wasabi endpoint and strip https:// if present
        endpoint = config('WASABI_ENDPOINT', default='s3.wasabisys.com')
        self.wasabi_endpoint = endpoint.replace('https://', '').replace('http://', '')
        self.wasabi_region = config('WASABI_REGION', default='us-east-1')
        self.wasabi_bucket = config('WASABI_BUCKET', default='')
        # Try both naming conventions for access keys
        self.wasabi_access_key = config('WASABI_ACCESS_KEY', default='') or config('WASABI_ACCESS_KEY_ID', default='')
        self.wasabi_secret_key = config('WASABI_SECRET_KEY', default='') or config('WASABI_SECRET_ACCESS_KEY', default='')

    def get_connection(self):
        """
        Get a DuckDB connection configured for Wasabi S3

        Returns:
            duckdb.DuckDBPyConnection: Configured connection
        """
        conn = duckdb.connect(':memory:')  # In-memory database for fast queries

        # Configure S3/Wasabi access
        if self.wasabi_access_key and self.wasabi_secret_key:
            conn.execute("INSTALL httpfs;")
            conn.execute("LOAD httpfs;")
            conn.execute(f"SET s3_endpoint='{self.wasabi_endpoint}';")
            conn.execute(f"SET s3_region='{self.wasabi_region}';")
            conn.execute(f"SET s3_access_key_id='{self.wasabi_access_key}';")
            conn.execute(f"SET s3_secret_access_key='{self.wasabi_secret_key}';")

        return conn

    def query(self, sql, params=None):
        """
        Execute a SQL query and return results as a list of dicts

        Args:
            sql (str): SQL query to execute
            params (dict): Optional parameters for parameterized queries

        Returns:
            list: Query results as list of dictionaries

        Example:
            >>> client = DuckDBClient()
            >>> results = client.query('''
            ...     SELECT vendor, SUM(amount) as total
            ...     FROM 's3://bucket/purchase_orders.parquet'
            ...     WHERE order_date >= ?
            ...     GROUP BY vendor
            ... ''', params={'order_date': '2024-01-01'})
        """
        try:
            conn = self.get_connection()

            if params:
                result = conn.execute(sql, params).fetchdf()
            else:
                result = conn.execute(sql).fetchdf()

            conn.close()

            # Convert DataFrame to list of dicts for JSON serialization
            return result.to_dict('records')

        except Exception as e:
            logger.error(f"DuckDB query error: {e}")
            logger.error(f"SQL: {sql}")
            raise

    def query_dataframe(self, sql, params=None):
        """
        Execute a SQL query and return results as a pandas DataFrame

        Args:
            sql (str): SQL query to execute
            params (dict): Optional parameters

        Returns:
            pandas.DataFrame: Query results
        """
        try:
            conn = self.get_connection()

            if params:
                result = conn.execute(sql, params).fetchdf()
            else:
                result = conn.execute(sql).fetchdf()

            conn.close()
            return result

        except Exception as e:
            logger.error(f"DuckDB query error: {e}")
            raise

    def get_s3_path(self, filename):
        """
        Get full S3 path for a file in the configured bucket

        Args:
            filename (str): Name of the file

        Returns:
            str: Full S3 path (e.g., 's3://bucket/file.parquet')
        """
        return f"s3://{self.wasabi_bucket}/{filename}"

    def table_info(self, parquet_path):
        """
        Get schema information for a Parquet file

        Args:
            parquet_path (str): S3 path or local path to Parquet file

        Returns:
            list: Column information
        """
        try:
            conn = self.get_connection()
            result = conn.execute(f"DESCRIBE SELECT * FROM '{parquet_path}'").fetchdf()
            conn.close()
            return result.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            raise

    def count_records(self, parquet_path):
        """
        Get record count for a Parquet file

        Args:
            parquet_path (str): S3 path or local path to Parquet file

        Returns:
            int: Number of records
        """
        try:
            conn = self.get_connection()
            result = conn.execute(f"SELECT COUNT(*) as count FROM '{parquet_path}'").fetchone()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error counting records: {e}")
            raise


# Global singleton instance
duckdb_client = DuckDBClient()
