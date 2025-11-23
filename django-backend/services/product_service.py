"""
Product Service - High-level interface for all product-related ERP operations

This service provides clean Python interfaces for product CRUD operations,
abstracting away the ERP communication details.
"""

import re
import json
from typing import List, Dict, Any, Optional
from .erp_client import erp_client, ERPClientError

class ProductService:
    """
    High-level service for product operations
    Handles business logic and calls ERP via erp_client
    """

    @staticmethod
    def search_products(
        user_id: str,
        company_api_base: str,
        keyword: str,
        include_inactive: bool = True,
        page_size: int = 50,
        port: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search products and return normalized results

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            keyword: Search keyword
            include_inactive: Include inactive products
            page_size: Number of results
            port: ERP port override

        Returns:
            List of normalized product dictionaries
        """
        try:
            response = erp_client.search_products(
                user_id=user_id,
                company_api_base=company_api_base,
                keyword=keyword,
                include_inactive=include_inactive,
                page_size=page_size,
                port=port
            )

            # Normalize the response (handle different ERP response formats)
            products = response.get('results', response.get('data', []))
            if not isinstance(products, list):
                products = [products] if products else []

            # Normalize each product
            normalized_products = []
            for product in products:
                normalized = ProductService._normalize_product(product)
                if normalized:
                    normalized_products.append(normalized)

            return normalized_products

        except ERPClientError:
            raise
        except Exception as e:
            raise ERPClientError(f"Product search failed: {str(e)}")

    @staticmethod
    def get_product(
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
            Normalized product dictionary
        """
        try:
            response = erp_client.get_product(
                user_id=user_id,
                company_api_base=company_api_base,
                product_id=product_id,
                port=port
            )

            return ProductService._normalize_product(response)

        except ERPClientError:
            raise
        except Exception as e:
            raise ERPClientError(f"Failed to get product {product_id}: {str(e)}")

    @staticmethod
    def merge_product_keywords(
        user_id: str,
        company_api_base: str,
        keeper_product_id: str,
        merge_product_id: str,
        selected_companies: Optional[Dict[str, bool]] = None,
        port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Merge keywords from two products and update the keeper product

        Args:
            user_id: User ID for authentication
            company_api_base: Company ERP base URL
            keeper_product_id: Product ID to keep and update
            merge_product_id: Product ID to merge keywords from
            selected_companies: Dict of company selections for description overrides
            port: ERP port override

        Returns:
            Updated product data with merged keywords
        """
        try:
            # Get both products
            keeper_product = ProductService.get_product(
                user_id, company_api_base, keeper_product_id, port
            )
            merge_product = ProductService.get_product(
                user_id, company_api_base, merge_product_id, port
            )

            # Merge keywords
            merged_keywords = ProductService._merge_keywords(
                keeper_product.get('keywords', ''),
                merge_product.get('keywords', ''),
                merge_product.get('description', '')
            )

            # ERP requires the complete product data object for updates
            # Use the raw ERP data to preserve all fields including updateKey
            keeper_erp_data = keeper_product.get('_raw_erp_data', keeper_product)

            # Update the keywords field in the complete ERP object (uppercased for ERP)
            keeper_erp_data['keywords'] = merged_keywords.upper()

            # Request 1: Update product keywords using /Products/{id}
            response1 = erp_client.update_product(
                user_id=user_id,
                company_api_base=company_api_base,
                product_id=keeper_product_id,
                product_data=keeper_erp_data,
                port=port
            )

            # Request 2: Update PROD.CLASS description overrides using /UserDefined/PROD.CLASS
            # Map frontend company selections to ERP field names
            company_field_mapping = {
                'benoist': 'DESC.OVRD.BBS',
                'coastal': 'DESC.OVRD.CSC',
                'edsCentral': 'DESC.OVRD.ESC',
                'edsEast': 'DESC.OVRD.ESE',
                'edsWest': 'DESC.OVRD.ESW',
                'nuComfort': 'DESC.OVRD.NCS'
            }

            # Skip PROD.CLASS update if no companies selected
            if not selected_companies or not any(selected_companies.values()):
                print(f"\n[INFO] No companies selected for description override updates")
                response2 = {'message': 'No companies selected for PROD.CLASS updates - skipped'}
            else:
                try:
                    print(f"\n===== PROD.CLASS GET EXISTING RECORD =====")
                    print(f"[TARGET] Getting existing PROD.CLASS for product: {keeper_product_id}")
                    print(f"[SELECTED COMPANIES] {selected_companies}")

                    # Get existing PROD.CLASS record
                    existing_prod_class = erp_client.get_product_class(
                        user_id=user_id,
                        company_api_base=company_api_base,
                        product_id=keeper_product_id,
                        port=port
                    )

                    print(f"[SUCCESS] Got existing PROD.CLASS record")
                    print(f"[DEBUG] Existing FileName: {existing_prod_class.get('FileName', 'NOT_FOUND')}")

                    # Update description overrides for selected companies
                    updated_fields = []
                    merge_description_upper = merge_product.get('description', '').strip().upper()

                    for company_key, selected in selected_companies.items():
                        if selected and company_key in company_field_mapping:
                            field_name = company_field_mapping[company_key]
                            existing_value = existing_prod_class.get(field_name, 'NOT_FOUND')
                            existing_prod_class[field_name] = merge_description_upper
                            updated_fields.append(f"{field_name}: '{existing_value}' -> '{merge_description_upper}'")
                            print(f"[DEBUG] Updated {field_name}: {existing_value} -> {merge_description_upper}")

                    existing_prod_class['FileName'] = 'PROD.CLASS'

                    # Remove the 'id' field that causes "The Key 'id' was not found in Dictionary" error
                    if 'id' in existing_prod_class:
                        del existing_prod_class['id']

                    print(f"\n===== PROD.CLASS UPDATE DEBUG INFO =====")
                    print(f"[TARGET] About to call: PUT /UserDefined/PROD.CLASS?id={keeper_product_id}")
                    print(f"[UPDATED FIELDS] {len(updated_fields)} company overrides updated:")
                    for field_update in updated_fields:
                        print(f"  - {field_update}")
                    print(f"[BODY] Key fields being sent:")
                    key_fields = {
                        'FileName': existing_prod_class.get('FileName'),
                        'total_fields': len(existing_prod_class.keys()) if hasattr(existing_prod_class, 'keys') else 'unknown',
                        'has_id_field': 'id' in existing_prod_class,
                        'updated_companies': list(company_field_mapping[k] for k, v in selected_companies.items() if v and k in company_field_mapping)
                    }
                    print(json.dumps(key_fields, indent=2))
                    print(f"[INFO] Removed 'id' field, keeping all other existing fields")
                    print(f"==========================================\n")

                    response2 = erp_client.update_product_class(
                        user_id=user_id,
                        company_api_base=company_api_base,
                        product_id=keeper_product_id,
                        product_data=existing_prod_class,
                        port=port
                    )

                    print(f"[SUCCESS] PROD.CLASS update completed successfully!")

                except Exception as e:
                    print(f"\n[ERROR] PROD.CLASS update failed: {str(e)}")
                    response2 = {
                        'error': f'PROD.CLASS update failed: {str(e)}',
                        'attempted_data': existing_prod_class if 'existing_prod_class' in locals() else 'Failed to get existing record'
                    }

            return {
                'success': True,
                'keeper_id': keeper_product_id,
                'merge_id': merge_product_id,
                'updated_keywords': merged_keywords,
                'product_response': response1,
                'prod_class_response': response2,
                'debug_info': {
                    'prod_class_operation': {
                        'endpoint': f'/UserDefined/PROD.CLASS?id={keeper_product_id}',
                        'selected_companies': selected_companies,
                        'updated_fields': updated_fields if 'updated_fields' in locals() else [],
                        'company_field_mapping': company_field_mapping,
                        'merge_description': merge_product.get('description', '').strip().upper(),
                        'filename': existing_prod_class.get('FileName', 'NOT_SET') if 'existing_prod_class' in locals() else 'FAILED_TO_GET',
                        'removed_id_field': 'id' in existing_prod_class if 'existing_prod_class' in locals() else False,
                        'total_fields_sent': len(existing_prod_class.keys()) if 'existing_prod_class' in locals() and hasattr(existing_prod_class, 'keys') else 'unknown'
                    }
                }
            }

        except ERPClientError:
            raise
        except Exception as e:
            raise ERPClientError(f"Failed to merge product keywords: {str(e)}")

    @staticmethod
    def _normalize_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize product data from ERP into consistent format

        Args:
            product_data: Raw product data from ERP

        Returns:
            Normalized product dictionary
        """
        if not product_data:
            return {}

        # Handle different possible field names from ERP
        product_id = (
            product_data.get('id') or
            product_data.get('productId') or
            product_data.get('ProductId') or
            str(product_data.get('ID', ''))
        )

        description = (
            product_data.get('description') or
            product_data.get('Description') or
            product_data.get('name') or
            product_data.get('Name') or
            'No description'
        )

        keywords = (
            product_data.get('keywords') or
            product_data.get('Keywords') or
            product_data.get('DESC.OVRD.NUC') or
            ''
        )

        return {
            'id': product_id,
            'description': description.strip(),
            'keywords': keywords.strip(),
            'category': product_data.get('category', ''),
            'display_name': f"{product_id} - {description.strip()}",
            'is_active': product_data.get('productStatusId') == 1,
            'productStatusId': product_data.get('productStatusId'),
            'upc': product_data.get('upc') or product_data.get('UPC') or '',
            'priceLineId': product_data.get('priceLineId') or product_data.get('PriceLineId') or '',
            'buyLineId': product_data.get('buyLineId') or product_data.get('BuyLineId') or '',
            # Keep raw ERP data for updates
            '_raw_erp_data': product_data
        }

    @staticmethod
    def _merge_keywords(
        keeper_keywords: str,
        merge_keywords: str,
        merge_description: str
    ) -> str:
        """
        Merge keywords from keeper product with keywords and description from merge product
        Remove duplicates and clean up the text

        Args:
            keeper_keywords: Existing keywords from keeper product
            merge_keywords: Keywords from merge product
            merge_description: Description from merge product

        Returns:
            Merged and deduplicated keywords string
        """
        # Combine all text sources
        all_text = []

        if keeper_keywords and keeper_keywords.strip():
            all_text.append(keeper_keywords.strip())
        if merge_keywords and merge_keywords.strip():
            all_text.append(merge_keywords.strip())
        if merge_description and merge_description.strip():
            all_text.append(merge_description.strip())

        if not all_text:
            return ''

        # Join all text
        combined_text = ' '.join(all_text)

        # Clean up: remove punctuation, split into words
        # Convert to lowercase for deduplication
        words = re.sub(r'[^\w\s]', ' ', combined_text.lower()).split()

        # Remove duplicates while preserving order, filter short words
        seen = set()
        unique_words = []
        for word in words:
            if len(word) > 2 and word not in seen:
                seen.add(word)
                unique_words.append(word)

        return ' '.join(unique_words)


# Global product service instance
product_service = ProductService()