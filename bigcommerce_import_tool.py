#!/usr/bin/env python3
"""
BigCommerce Product Import Tool

This tool allows you to import product details from one BigCommerce store to another
using the product SKU as the identifier.

Features:
- Pull product details from source store using SKU
- Extract: name, description, SKU, UPC, MPN, GTIN, and URL
- Import product data into destination store
"""

import os
import sys
import json
import requests
from typing import Dict, Optional, Any
from dotenv import load_dotenv

class BigCommerceAPI:
    """BigCommerce API client wrapper"""
    
    def __init__(self, store_hash: str, access_token: str, client_id: str):
        self.store_hash = store_hash
        self.access_token = access_token
        self.client_id = client_id
        self.base_url = f"https://api.bigcommerce.com/stores/{store_hash}/v3"
        self.headers = {
            "X-Auth-Token": access_token,
            "X-Auth-Client": client_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get product details by SKU from BigCommerce store"""
        try:
            # Search for product by SKU
            url = f"{self.base_url}/catalog/products"
            params = {"sku": sku, "include": "variants,custom_fields,bulk_pricing_rules,primary_image,images"}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]
            else:
                print(f"No product found with SKU: {sku}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching product with SKU {sku}: {e}")
            return None
    
    def create_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new product in BigCommerce store"""
        try:
            url = f"{self.base_url}/catalog/products"
            
            response = requests.post(url, headers=self.headers, json=product_data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error creating product: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing product in BigCommerce store by product ID"""
        try:
            url = f"{self.base_url}/catalog/products/{product_id}"
            print(f"=== DEBUG: BigCommerce API update_product ===")
            print(f"  URL: {url}")
            print(f"  Product ID: {product_id}")
            print(f"  Request data: {product_data}")
            print(f"  Headers: {self.headers}")
            
            response = requests.put(url, headers=self.headers, json=product_data)
            
            print(f"=== DEBUG: HTTP Response ===")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response headers: {dict(response.headers)}")
            print(f"  Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating product: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
                print(f"=== DEBUG: Error response status: {e.response.status_code} ===")
            return None
    
    def get_brand_name(self, brand_id: int) -> str:
        """Fetch the brand name by brand_id from BigCommerce store."""
        if not brand_id:
            return ''
        try:
            url = f"{self.base_url}/catalog/brands/{brand_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {}).get('name', '')
        except Exception as e:
            print(f"Error fetching brand name for brand_id {brand_id}: {e}")
            return ''

class ProductImporter:
    """Main class for importing products between BigCommerce stores"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize all stores
        self.stores = {
            'wilson_us': BigCommerceAPI(
                store_hash=os.getenv("WILSON_US_HASH"),
                access_token=os.getenv("WILSON_US_ACCESS_TOKEN"),
                client_id=os.getenv("WILSON_US_CLIENT_ID")
            ),
            'signal_us': BigCommerceAPI(
                store_hash=os.getenv("SIGNAL_US_HASH"),
                access_token=os.getenv("SIGNAL_US_ACCESS_TOKEN"),
                client_id=os.getenv("SIGNAL_US_CLIENT_ID")
            ),
            'wilson_ca': BigCommerceAPI(
                store_hash=os.getenv("WILSON_CA_HASH"),
                access_token=os.getenv("WILSON_CA_ACCESS_TOKEN"),
                client_id=os.getenv("WILSON_CA_CLIENT_ID")
            ),
            'signal_ca': BigCommerceAPI(
                store_hash=os.getenv("SIGNAL_CA_HASH"),
                access_token=os.getenv("SIGNAL_CA_ACCESS_TOKEN"),
                client_id=os.getenv("SIGNAL_CA_CLIENT_ID")
            )
        }
        
        # Set default source and destination (for backward compatibility)
        self.source_store = self.stores['wilson_us']
        self.dest_store = self.stores['signal_us']
    
    def get_store_by_name(self, store_name):
        """Get store API by name"""
        return self.stores.get(store_name)
    
    def get_product_with_brand(self, store_name: str, sku: str) -> dict:
        """Fetch product by SKU and include brand name if available."""
        store = self.get_store_by_name(store_name)
        if not store:
            return None
            
        product = store.get_product_by_sku(sku)
        if product and product.get('brand_id'):
            product['brand'] = store.get_brand_name(product['brand_id'])
        else:
            product['brand'] = ''
        return product
    
    def compare_products(self, source_store: str, dest_store: str, sku_a: str, sku_b: str = None):
        """Compare products between two stores"""
        source_product = self.get_product_with_brand(source_store, sku_a)
        
        # Use sku_b if provided, otherwise try sku_a for Store B
        dest_sku = sku_b if sku_b else sku_a
        dest_product = self.get_product_with_brand(dest_store, dest_sku)
        
        return {
            'source_product': source_product,
            'dest_product': dest_product,
            'source_store_name': self.get_store_display_name(source_store),
            'dest_store_name': self.get_store_display_name(dest_store)
        }
    
    def get_store_display_name(self, store_name):
        """Get human-readable store name"""
        store_names = {
            'wilson_us': 'Wilson Amplifiers US',
            'signal_us': 'SignalBoosters US', 
            'wilson_ca': 'Wilson Amplifiers CA',
            'signal_ca': 'SignalBoosters CA'
        }
        return store_names.get(store_name, store_name)
    
    def get_all_stores(self):
        """Get list of all available stores"""
        return {
            'wilson_us': 'Wilson Amplifiers US',
            'signal_us': 'SignalBoosters US',
            'wilson_ca': 'Wilson Amplifiers CA', 
            'signal_ca': 'SignalBoosters CA'
        }
    
    def extract_product_fields(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the required fields from a BigCommerce product"""
        
        # Build the product URL
        store_url = f"https://{self.source_store.store_hash}.mybigcommerce.com"
        product_url = f"{store_url}/{product.get('custom_url', {}).get('url', '')}"
        
        extracted_data = {
            "name": product.get("name", ""),
            "description": product.get("description", ""),
            "sku": product.get("sku", ""),
            "upc": product.get("upc", ""),
            "mpn": product.get("mpn", ""),
            "gtin": product.get("gtin", ""),
            "url": product_url,
            
            # Additional fields needed for product creation
            "type": product.get("type", "physical"),
            "weight": product.get("weight", 0),
            "price": product.get("price", 0),
            "categories": product.get("categories", []),
            "availability": product.get("availability", "available"),
            "visible": product.get("is_visible", True),
            "custom_fields": product.get("custom_fields", []),
            "brand": product.get("brand", "")
        }
        
        # Debug logging for custom fields
        custom_fields = product.get("custom_fields", [])
        if custom_fields:
            print(f"=== DEBUG: Found {len(custom_fields)} custom fields in source product ===")
            for cf in custom_fields:
                print(f"  - {cf.get('name', 'Unknown')}: {cf.get('value', 'N/A')}")
        else:
            print(f"=== DEBUG: No custom fields found in source product ===")
        
        return extracted_data
    
    def prepare_product_for_import(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare extracted product data for import into destination store"""
        
        import_data = {
            "name": extracted_data["name"],
            "description": extracted_data["description"],
            "sku": extracted_data["sku"],
            "type": extracted_data["type"],
            "weight": extracted_data["weight"],
            "price": str(extracted_data["price"]),
            "is_visible": extracted_data["visible"],
            "availability": extracted_data["availability"],
            "brand": extracted_data["brand"]
        }
        
        # Add optional fields if they have values
        if extracted_data.get("upc"):
            import_data["upc"] = extracted_data["upc"]
        if extracted_data.get("mpn"):
            import_data["mpn"] = extracted_data["mpn"]
        if extracted_data.get("gtin"):
            import_data["gtin"] = extracted_data["gtin"]
        if extracted_data.get("categories"):
            import_data["categories"] = extracted_data["categories"]
        if extracted_data.get("custom_fields"):
            import_data["custom_fields"] = extracted_data["custom_fields"]
            print(f"=== DEBUG: Including {len(extracted_data['custom_fields'])} custom fields in import ===")
            for cf in extracted_data["custom_fields"]:
                print(f"  - {cf.get('name', 'Unknown')}: {cf.get('value', 'N/A')}")
            
        return import_data
    
    def import_product_by_sku(self, sku: str, show_details: bool = True, update_if_exists: bool = False) -> bool:
        """Import a product from source store to destination store using SKU. Update if exists if flag is set."""
        print(f"\nSearching for product with SKU: {sku}")
        # Get product from source store
        source_product = self.source_store.get_product_by_sku(sku)
        if not source_product:
            print(f"Product with SKU '{sku}' not found in source store")
            return False
        print(f"Found product: {source_product.get('name', 'Unknown')}")
        # Extract required fields
        extracted_data = self.extract_product_fields(source_product)
        if show_details:
            self.display_product_details(extracted_data)
        # Check if product already exists in destination store
        existing_product = self.dest_store.get_product_by_sku(sku)
        if existing_product:
            print(f"Product with SKU '{sku}' already exists in destination store")
            print(f"   Existing product: {existing_product.get('name', 'Unknown')}")
            if update_if_exists:
                # Prepare data for update
                update_data = self.prepare_product_for_import(extracted_data)
                print(f"Updating product in destination store...")
                result = self.dest_store.update_product(existing_product['id'], update_data)
                if result and result.get("data"):
                    print(f"Successfully updated product!")
                    print(f"   Updated product ID: {result['data'].get('id')}")
                    print(f"   Product name: {result['data'].get('name')}")
                    return True
                else:
                    print(f"Failed to update product")
                    return False
            else:
                return False
        # Prepare data for import
        import_data = self.prepare_product_for_import(extracted_data)
        print(f"Importing product to destination store...")
        # Create product in destination store
        result = self.dest_store.create_product(import_data)
        if result and result.get("data"):
            print(f"Successfully imported product!")
            print(f"   New product ID: {result['data'].get('id')}")
            print(f"   Product name: {result['data'].get('name')}")
            return True
        else:
            print(f"Failed to import product")
            return False
    
    def display_product_details(self, product_data: Dict[str, Any]):
        """Display the extracted product details"""
        print(f"\n📋 Product Details:")
        print(f"   Name: {product_data.get('name', 'N/A')}")
        print(f"   Description: {product_data.get('description', 'N/A')[:100]}{'...' if len(product_data.get('description', '')) > 100 else ''}")
        print(f"   SKU: {product_data.get('sku', 'N/A')}")
        print(f"   UPC: {product_data.get('upc', 'N/A')}")
        print(f"   MPN: {product_data.get('mpn', 'N/A')}")
        print(f"   GTIN: {product_data.get('gtin', 'N/A')}")
        print(f"   URL: {product_data.get('url', 'N/A')}")

    def import_product_between_stores(self, source_store_name: str, target_store_name: str, sku: str, update_if_exists: bool = False) -> bool:
        """Import a product from source store to target store using SKU"""
        try:
            source_store = self.get_store_by_name(source_store_name)
            target_store = self.get_store_by_name(target_store_name)
            
            if not source_store or not target_store:
                print(f"Invalid store names: {source_store_name}, {target_store_name}")
                return False
            
            # Get product from source store
            source_product = source_store.get_product_by_sku(sku)
            if not source_product:
                print(f"Product with SKU '{sku}' not found in source store")
                return False
            
            # Check if product already exists in target store
            existing_product = target_store.get_product_by_sku(sku)
            if existing_product:
                if update_if_exists:
                    # Update existing product
                    update_data = self.prepare_product_for_import(self.extract_product_fields(source_product))
                    result = target_store.update_product(existing_product['id'], update_data)
                    return result and result.get("data") is not None
                else:
                    print(f"Product with SKU '{sku}' already exists in target store")
                    return False
            
            # Create new product
            import_data = self.prepare_product_for_import(self.extract_product_fields(source_product))
            result = target_store.create_product(import_data)
            return result and result.get("data") is not None
            
        except Exception as e:
            print(f"Error importing product {sku}: {e}")
            return False

    def update_target_product(self, store_name: str, sku: str, update_data: Dict[str, Any]) -> bool:
        """Update a product in the target store with the provided data"""
        try:
            print(f"=== DEBUG: update_target_product called ===")
            print(f"  store_name: {store_name}")
            print(f"  sku: {sku}")
            print(f"  update_data: {update_data}")
            
            store = self.get_store_by_name(store_name)
            if not store:
                print(f"Store '{store_name}' not found")
                return False
            
            print(f"=== DEBUG: Store object retrieved successfully: {type(store)} ===")
            
            # Get the existing product
            existing_product = store.get_product_by_sku(sku)
            if not existing_product:
                print(f"Product with SKU '{sku}' not found in store '{store_name}'")
                return False
            
            print(f"=== DEBUG: Found existing product: {existing_product.get('name')} (ID: {existing_product.get('id')}) ===")
            print(f"=== DEBUG: existing_product type: {type(existing_product)} ===")
            print(f"=== DEBUG: existing_product keys: {list(existing_product.keys()) if existing_product else 'None'} ===")
            
            # Prepare the update data
            update_payload = {}
            
            print(f"=== DEBUG: Initializing update_payload: {type(update_payload)} ===")
            
            # Map the form fields to BigCommerce API fields
            field_mapping = {
                'name': 'name',
                'price': 'price',
                'brand': 'brand_name',  # BigCommerce uses brand_name for brand
                'description': 'description',
                'sku': 'sku',
                'mpn': 'mpn',
                'upc': 'upc',
                'gtin': 'gtin',
                'weight': 'weight',
                'width': 'width',
                'height': 'height',
                'depth': 'depth',
                'custom_fields': 'custom_fields',
                'images': 'images'
            }
            
            print(f"=== DEBUG: Starting field mapping process ===")
            
            for form_field, api_field in field_mapping.items():
                if form_field in update_data:
                    value = update_data[form_field]
                    print(f"=== DEBUG: Processing field mapping: {form_field} -> {api_field} = '{value}' ===")
                    
                    try:
                        # Handle special cases
                        if form_field == 'price' and value:
                            update_payload[api_field] = str(value)
                            print(f"=== DEBUG: Set price as string: '{str(value)}' ===")
                        elif form_field == 'weight' and value:
                            update_payload[api_field] = float(value)
                            print(f"=== DEBUG: Set weight as float: {float(value)} ===")
                        elif form_field in ['width', 'height', 'depth'] and value:
                            update_payload[api_field] = float(value)
                            print(f"=== DEBUG: Set {form_field} as float: {float(value)} ===")
                        elif form_field == 'brand' and value:
                            # For brand, we need to find the brand ID or create it
                            # For now, just set the brand name
                            update_payload['brand_name'] = value
                            print(f"=== DEBUG: Set brand_name: '{value}' ===")
                        elif form_field in ['custom_fields', 'images'] and value:
                            # These are complex objects, pass them through
                            update_payload[api_field] = value
                            print(f"=== DEBUG: Set {form_field} as object: {value} ===")
                        elif value:  # For other fields, only update if value exists
                            update_payload[api_field] = value
                            print(f"=== DEBUG: Set {form_field}: '{value}' ===")
                        else:
                            print(f"=== DEBUG: Skipped {form_field} because value is empty/falsy ===")
                            
                        print(f"=== DEBUG: update_payload after {form_field}: {update_payload} ===")
                        
                    except Exception as field_error:
                        print(f"=== DEBUG: Error processing field {form_field}: {field_error} ===")
                        print(f"=== DEBUG: update_payload type: {type(update_payload)} ===")
                        print(f"=== DEBUG: api_field: {api_field} ===")
                        print(f"=== DEBUG: value: {value} (type: {type(value)}) ===")
                        raise field_error
            
            print(f"=== DEBUG: Final update_payload to send to BigCommerce: {update_payload} ===")
            
            # Check that we have a valid product ID
            product_id = existing_product.get('id')
            if not product_id:
                print(f"No product ID found in existing product data")
                return False
                
            print(f"=== DEBUG: About to call store.update_product with ID: {product_id} ===")
            
            # Update the product
            result = store.update_product(product_id, update_payload)
            
            print(f"=== DEBUG: BigCommerce API response: {result} ===")
            
            if result and result.get("data"):
                print(f"Successfully updated product {sku} in store {store_name}")
                return True
            else:
                print(f"Failed to update product {sku} in store {store_name}")
                return False
                
        except Exception as e:
            print(f"Error updating product {sku} in store {store_name}: {e}")
            print(f"=== DEBUG: Exception details: {type(e).__name__}: {str(e)} ===")
            import traceback
            print(f"=== DEBUG: Full traceback: ===")
            traceback.print_exc()
            return False

def main():
    """Main function to run the import tool"""
    
    if len(sys.argv) < 2:
        print("Usage: python bigcommerce_import_tool.py <SKU> [--quiet]")
        print("Example: python bigcommerce_import_tool.py ABC123")
        print("         python bigcommerce_import_tool.py ABC123 --quiet")
        sys.exit(1)
    
    sku = sys.argv[1]
    show_details = "--quiet" not in sys.argv
    
    # Check if required environment variables are set
    required_vars = [
        "STORE_A_HASH", "STORE_A_ACCESS_TOKEN", "STORE_A_CLIENT_ID",
        "STORE_B_HASH", "STORE_B_ACCESS_TOKEN", "STORE_B_CLIENT_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease copy .env.example to .env and fill in your BigCommerce API credentials.")
        sys.exit(1)
    
    # Initialize and run the importer
    importer = ProductImporter()
    success = importer.import_product_by_sku(sku, show_details)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 