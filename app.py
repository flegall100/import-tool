from flask import Flask, render_template, request, jsonify
from bigcommerce_import_tool import ProductImporter
import os
import tempfile
from dotenv import load_dotenv
import os
load_dotenv()
print('STORE_A_HASH:', os.getenv('STORE_A_HASH'))
app = Flask(__name__)

importer = ProductImporter()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/import", methods=["POST"])
def import_sku():
    sku = request.form.get("sku")
    source_store = request.form.get("source_store")
    target_store = request.form.get("target_store")
    update_if_exists = request.form.get("update_if_exists") == "on"
    
    if not sku:
        return jsonify({"success": False, "error": "No SKU provided."}), 400
    if not source_store or not target_store:
        return jsonify({"success": False, "error": "Both source and target stores must be selected."}), 400
    
    try:
        success = importer.import_product_between_stores(source_store, target_store, sku, update_if_exists=update_if_exists)
        if success:
            return jsonify({"success": True, "message": f"Successfully imported SKU: {sku} from {importer.get_store_display_name(source_store)} to {importer.get_store_display_name(target_store)}"})
        else:
            return jsonify({"success": False, "error": f"Failed to import or update SKU: {sku}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/batch_import", methods=["POST"])
def batch_import():
    source_store = request.form.get("source_store")
    target_store = request.form.get("target_store")
    update_if_exists = request.form.get("update_if_exists") == "on"
    
    if not source_store or not target_store:
        return jsonify({"success": False, "error": "Both source and target stores must be selected."}), 400
    
    skus = []
    if "sku_file" in request.files and request.files["sku_file"].filename:
        file = request.files["sku_file"]
        content = file.read().decode("utf-8")
        skus = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    elif request.form.get("sku_list"):
        skus = [sku.strip() for sku in request.form.get("sku_list").splitlines() if sku.strip()]
    else:
        return jsonify({"success": False, "error": "No SKUs provided."}), 400

    results = []
    for sku in skus:
        try:
            success = importer.import_product_between_stores(source_store, target_store, sku, update_if_exists=update_if_exists)
            results.append({"sku": sku, "success": success})
        except Exception as e:
            results.append({"sku": sku, "success": False, "error": str(e)})
    return jsonify({"success": True, "results": results})

@app.route("/stores", methods=["GET"])
def get_stores():
    """Get list of all available stores"""
    return jsonify({
        "success": True,
        "stores": importer.get_all_stores()
    })

@app.route("/compare", methods=["POST"])
def compare():
    store_a = request.form.get("store_a", "wilson_us")
    store_b = request.form.get("store_b", "signal_ca")
    sku_a = request.form.get("sku_a")
    sku_b = request.form.get("sku_b")
    
    if not sku_a:
        return jsonify({"success": False, "error": "Store A SKU is required."}), 400
    try:
        result = importer.compare_products(store_a, store_b, sku_a, sku_b)
        return jsonify({
            "success": True,
            "product_a": result["source_product"],
            "product_b": result["dest_product"],
            "store_a_name": result["source_store_name"],
            "store_b_name": result["dest_store_name"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get_product", methods=["POST"])
def get_product():
    store = request.form.get("store")
    sku = request.form.get("sku")
    
    if not store or not sku:
        return jsonify({"success": False, "error": "Store and SKU are required."}), 400
    try:
        product = importer.get_product_with_brand(store, sku)
        if product:
            return jsonify({"success": True, "product": product})
        else:
            return jsonify({"success": False, "error": "Product not found."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/update_target", methods=["POST"])
def update_target():
    store_a = request.form.get("store_a")
    store_b = request.form.get("store_b")
    sku_a = request.form.get("sku_a")
    sku_b = request.form.get("sku_b")
    
    if not all([store_a, store_b, sku_a, sku_b]):
        return jsonify({"success": False, "error": "All store and SKU fields are required."}), 400
    
    try:
        # Get the fields that should be synced
        sync_fields = []
        for key in request.form.keys():
            if key.startswith('sync_'):
                field_name = key[5:]  # Remove 'sync_' prefix
                sync_fields.append(field_name)
        
        # Prepare update data
        update_data = {}
        for field in sync_fields:
            if field in request.form:
                value = request.form.get(field)
                if field == 'images':
                    try:
                        # Parse JSON images data
                        import json
                        images_data = json.loads(value)
                        update_data[field] = images_data
                    except:
                        update_data[field] = value
                elif field == 'custom_fields':
                    try:
                        # Parse JSON custom fields data
                        import json
                        custom_fields = json.loads(value)
                        update_data[field] = custom_fields
                    except:
                        update_data[field] = value
                else:
                    update_data[field] = value
        
        # Use the importer to update the target product
        success = importer.update_target_product(store_b, sku_b, update_data)
        
        if success:
            return jsonify({"success": True, "message": f"Successfully updated product {sku_b} in target store"})
        else:
            return jsonify({"success": False, "error": f"Failed to update product {sku_b} in target store"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True) 