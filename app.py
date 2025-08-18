from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bigcommerce_import_tool import ProductImporter
import os
import tempfile
from dotenv import load_dotenv
import requests
import json

load_dotenv()

# Debug: Check environment variables
print('Environment Variables Check:')
for store in ['WILSON_US', 'SIGNAL_US', 'WILSON_CA', 'SIGNAL_CA']:
    hash_var = f'{store}_HASH'
    token_var = f'{store}_ACCESS_TOKEN'
    client_var = f'{store}_CLIENT_ID'
    
    print(f'{hash_var}: {"✓" if os.getenv(hash_var) else "✗"}')
    print(f'{token_var}: {"✓" if os.getenv(token_var) else "✗"}')
    print(f'{client_var}: {"✓" if os.getenv(client_var) else "✗"}')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Simple in-memory user store (replace with database in production)
users_db = {}

# Load users from environment or create default admin user
def init_users():
    # Try to load users from environment variables
    admin_email = os.getenv('ADMIN_EMAIL', 'merchandising@silkworldwide.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'T!t@n2025')
    
    if admin_email not in users_db:
        users_db[admin_email] = {
            'id': '1',
            'email': admin_email,
            'password_hash': generate_password_hash(admin_password),
            'name': 'Administrator',
            'is_admin': True
        }
        print(f"Created default admin user: {admin_email}")

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.name = user_data['name']
        self.is_admin = user_data.get('is_admin', False)
    
    def check_password(self, password):
        user_data = users_db.get(self.email)
        if user_data:
            return check_password_hash(user_data['password_hash'], password)
        return False

@login_manager.user_loader
def load_user(user_id):
    for email, user_data in users_db.items():
        if user_data['id'] == user_id:
            return User(user_data)
    return None

# Initialize users on startup
init_users()

importer = ProductImporter()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")
        
        user_data = users_db.get(email)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash("Invalid email or password.", "error")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))



@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", user=current_user)

@app.route("/import", methods=["POST"])
@login_required
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
@login_required
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
@login_required
def get_stores():
    """Get list of all available stores"""
    return jsonify({
        "success": True,
        "stores": importer.get_all_stores()
    })

@app.route("/compare", methods=["POST"])
@login_required
def compare():
    store_a = request.form.get("store_a", "wilson_us")
    store_b = request.form.get("store_b", "signal_ca")
    sku_a = request.form.get("sku_a")
    sku_b = request.form.get("sku_b")
    
    if not sku_a:
        return jsonify({"success": False, "error": "Source Store SKU is required."}), 400
    
    try:
        result = importer.compare_products(store_a, store_b, sku_a, sku_b)
        
        # Get store display names for better error messages
        store_a_name = importer.get_store_display_name(store_a)
        store_b_name = importer.get_store_display_name(store_b)
        dest_sku = sku_b if sku_b else sku_a
        
        # Check if source product exists
        if not result["source_product"]:
            return jsonify({
                "success": False, 
                "error": f"Product with SKU '{sku_a}' not found in {store_a_name}. Please verify the SKU exists in the source store."
            }), 404
        
        # Check if destination product exists (this is optional for comparison)
        if not result["dest_product"]:
            return jsonify({
                "success": True,
                "product_a": result["source_product"],
                "product_b": None,
                "store_a_name": result["source_store_name"],
                "store_b_name": result["dest_store_name"],
                "warning": f"Product with SKU '{dest_sku}' not found in {store_b_name}. You can still proceed to create a new product or update an existing one."
            })
        
        # Both products exist
        return jsonify({
            "success": True,
            "product_a": result["source_product"],
            "product_b": result["dest_product"],
            "store_a_name": result["source_store_name"],
            "store_b_name": result["dest_store_name"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error comparing products: {str(e)}"})

@app.route("/get_product", methods=["POST"])
@login_required
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
            store_name = importer.get_store_display_name(store)
            return jsonify({
                "success": False, 
                "error": f"Product with SKU '{sku}' not found in {store_name}. Please verify the SKU exists in this store."
            })
    except Exception as e:
        return jsonify({"success": False, "error": f"Error fetching product: {str(e)}"})



@app.route("/update_target", methods=["POST"])
@login_required
def update_target():
    store_a = request.form.get("store_a")
    store_b = request.form.get("store_b")
    sku_a = request.form.get("sku_a")
    sku_b = request.form.get("sku_b")
    
    if not all([store_a, store_b, sku_a, sku_b]):
        return jsonify({"success": False, "error": "All store and SKU fields are required."}), 400
    
    try:
        # Debug: Print all form data
        print("=== DEBUG: All form data ===")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        print("========================")
        
        # Get the fields that should be synced
        sync_fields = []
        for key in request.form.keys():
            if key.startswith('sync_'):
                field_name = key[5:]  # Remove 'sync_' prefix
                sync_fields.append(field_name)
        
        print(f"=== DEBUG: Sync fields found: {sync_fields} ===")
        
        # Prepare update data
        update_data = {}
        for field in sync_fields:
            if field in request.form:
                value = request.form.get(field)
                print(f"=== DEBUG: Processing field '{field}' with value: '{value}' ===")
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
        
        print(f"=== DEBUG: Final update_data: {update_data} ===")
        
        # Use the importer to update the target product
        success = importer.update_target_product(store_b, sku_b, update_data)
        
        if success:
            return jsonify({"success": True, "message": f"Successfully updated product {sku_b} in target store"})
        else:
            return jsonify({"success": False, "error": f"Failed to update product {sku_b} in target store"})
            
    except Exception as e:
        print(f"=== DEBUG: Exception in update_target: {e} ===")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

 