#!/usr/bin/env python3
"""
BigCommerce Batch Product Import Tool

This script allows batch importing of multiple products by SKU from one BigCommerce store to another.
You can provide SKUs via command line arguments or from a text file.

Usage:
    python batch_import.py SKU1 SKU2 SKU3
    python batch_import.py --file skus.txt
    python batch_import.py --file skus.txt --quiet
"""

import sys
import time
from bigcommerce_import_tool import ProductImporter

def read_skus_from_file(filename: str) -> list:
    """Read SKUs from a text file (one SKU per line)"""
    try:
        with open(filename, 'r') as f:
            skus = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return skus
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error reading file {filename}: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_import.py SKU1 SKU2 SKU3 ...")
        print("  python batch_import.py --file skus.txt")
        print("  python batch_import.py --file skus.txt --quiet")
        sys.exit(1)
    
    # Parse arguments
    show_details = "--quiet" not in sys.argv
    skus = []
    
    if "--file" in sys.argv:
        file_index = sys.argv.index("--file")
        if file_index + 1 < len(sys.argv):
            filename = sys.argv[file_index + 1]
            skus = read_skus_from_file(filename)
        else:
            print("❌ Please specify a filename after --file")
            sys.exit(1)
    else:
        # Get SKUs from command line (excluding flags)
        skus = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if not skus:
        print("❌ No SKUs provided")
        sys.exit(1)
    
    print(f"🚀 Starting batch import of {len(skus)} products...")
    print(f"📋 SKUs to import: {', '.join(skus)}")
    
    # Initialize importer
    importer = ProductImporter()
    
    # Track results
    successful_imports = []
    failed_imports = []
    
    # Import each product
    for i, sku in enumerate(skus, 1):
        print(f"\n{'='*50}")
        print(f"📦 Processing {i}/{len(skus)}: {sku}")
        print(f"{'='*50}")
        
        try:
            success = importer.import_product_by_sku(sku, show_details)
            if success:
                successful_imports.append(sku)
            else:
                failed_imports.append(sku)
        except Exception as e:
            print(f"❌ Unexpected error importing {sku}: {e}")
            failed_imports.append(sku)
        
        # Add a small delay between imports to be respectful to the API
        if i < len(skus):  # Don't sleep after the last item
            time.sleep(1)
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"📊 BATCH IMPORT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    print(f"📈 Success rate: {len(successful_imports)/len(skus)*100:.1f}%")
    
    if successful_imports:
        print(f"\n✅ Successfully imported SKUs:")
        for sku in successful_imports:
            print(f"   - {sku}")
    
    if failed_imports:
        print(f"\n❌ Failed to import SKUs:")
        for sku in failed_imports:
            print(f"   - {sku}")
    
    # Exit with appropriate code
    sys.exit(0 if len(failed_imports) == 0 else 1)

if __name__ == "__main__":
    main() 