from flask import Flask, render_template, request, jsonify, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import datetime # Import datetime for order_date

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = 'your_very_secret_key_change_this_in_production' # VERY IMPORTANT: Change this to a strong, random key!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Set the login view for Flask-Login

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    """Callback to reload the user object from the user ID stored in the session."""
    return User.query.get(int(user_id))

# --- Database Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False) # This line was added earlier

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', 'Admin: {self.is_admin}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    imageUrl = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"Product('{self.name}', ${self.price}, Stock: {self.stock})"

# --- New Order and OrderItem Models ---
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    total_amount = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Order('{self.id}', 'User ID: {self.user_id}', 'Total: ${self.total_amount:.2f}')"

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', backref=db.backref('order_items_product', lazy=True))

    def __repr__(self):
        return f"OrderItem('Order ID: {self.order_id}', 'Product ID: {self.product_id}', 'Qty: {self.quantity}')"


# --- WTForms for Registration and Login ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# --- Initial Product Data (for first-time setup) ---
initial_products_data = [
    {
        "name": "Laptop Pro",
        "price": 1200,
        "stock": 10000,
        "imageUrl": "https://images.unsplash.com/photo-1511385348-a52b4a160dc2?q=80&w=907&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    },
    {
        "name": "Smartphone X",
        "price": 750,
        "stock": 1500,
        "imageUrl": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?q=80&w=627&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    },
    {
        "name": "Wireless Headphones",
        "price": 150,
        "stock": 300,
        "imageUrl": "https://images.unsplash.com/photo-1612465289702-7c84b5258fde?q=80&w=673&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    },
    {
        "name": "4K Monitor",
        "price": 400,
        "stock": 800,
        "imageUrl": "https://plus.unsplash.com/premium_photo-1669380425564-6e1a281a4d30?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    },
    {
        "name": "Mechanical Keyboard",
        "price": 90,
        "stock": 200,
        "imageUrl": "https://media.istockphoto.com/id/963312720/vector/computer-keyboard.jpg?s=2048x2048&w=is&k=20&c=fmRG-erzWU9KkVfIqNgriCHhl9W9-Cq1_efErymIb6s="
    }
]

# --- Routes ---
@app.route('/')
def index():
    """Renders the main shopping page."""
    return render_template('index.html', current_user=current_user)

@app.route('/orders')
@login_required
def orders():
    """Renders the order history page for the logged-in user."""
    return render_template('orders.html', current_user=current_user)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Renders a specific product's detail page."""
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product, current_user=current_user)

@app.route('/profile')
@login_required
def profile():
    """Renders the user profile page."""
    return render_template('profile.html', title='Profile', current_user=current_user)

@app.route('/api/products', methods=['GET'])
def get_products():
    """Returns the list of products with current stock from the database."""
    products = Product.query.all()
    products_data = [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "stock": p.stock,
        "imageUrl": p.imageUrl
    } for p in products]
    return jsonify(products_data)

@app.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    """Handles the checkout process, updating stock in the database and saving the order."""
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Please log in to checkout."}), 401

    data = request.get_json()
    cart_items = data.get('cartItems')

    if not cart_items:
        return jsonify({"success": False, "message": "Cart is empty."}), 400

    print(f"Received checkout request for {len(cart_items)} items from user {current_user.username} (ID: {current_user.id}):")
    total_cost = 0
    processed_items_for_response = []

    try:
        new_order = Order(user_id=current_user.id, total_amount=0)
        db.session.add(new_order)
        db.session.flush()

        for item in cart_items:
            product_id = item.get('id')
            quantity = item.get('quantity')

            product = Product.query.get(product_id)

            if not product:
                db.session.rollback()
                return jsonify({"success": False, "message": f"Product with ID {product_id} not found."}), 404

            if product.stock < quantity:
                db.session.rollback()
                return jsonify({"success": False, "message": f"Not enough stock for {product.name}. Available: {product.stock}"}), 400

            product.stock -= quantity
            db.session.add(product)

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity,
                price_at_purchase=product.price
            )
            db.session.add(order_item)

            total_cost += product.price * quantity
            processed_items_for_response.append({
                "id": product.id,
                "name": product.name,
                "quantity": quantity,
                "price": product.price
            })
            print(f"   - {product.name} x {quantity} (New stock: {product.stock})")

        new_order.total_amount = total_cost
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Order placed successfully!",
            "orderId": new_order.id,
            "total": total_cost,
            "items": processed_items_for_response,
            "user_id": current_user.id,
            "username": current_user.username
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error during checkout: {e}")
        return jsonify({"success": False, "message": "An error occurred during checkout."}), 500

@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    """Returns the order history for the current logged-in user."""
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()

    orders_data = []
    for order in user_orders:
        order_items_data = []
        for item in order.items:
            product = Product.query.get(item.product_id)
            product_name = product.name if product else "Unknown Product"

            order_items_data.append({
                "product_name": product_name,
                "quantity": item.quantity,
                "price_at_purchase": item.price_at_purchase
            })
        orders_data.append({
            "order_id": order.id,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": order.total_amount,
            "items": order_items_data
        })
    return jsonify(orders_data)


# --- User Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # --- DEBUGGING PRINTS ---
        print(f"Attempting login with Email: '{form.email.data}'")
        print(f"Attempting login with Password: '{form.password.data}'")
        # --- END DEBUGGING PRINTS ---

        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Flask CLI Commands for Database Setup ---
@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    print("Deleting existing database (if any)...")
    db_path = os.path.join(app.root_path, 'site.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with app.app_context():
        db.create_all()
        print("Database tables created.")

        if Product.query.count() == 0:
            print("Populating initial product data...")
            for p_data in initial_products_data:
                product = Product(
                    name=p_data['name'],
                    price=p_data['price'],
                    stock=p_data['stock'],
                    imageUrl=p_data['imageUrl']
                )
                db.session.add(product)
            db.session.commit()
            print("Initial product data populated.")
        else:
            print("Database already contains product data, skipping initial population.")
        
        # --- THIS BLOCK WILL NOW CREATE AN ADMIN USER IF NO USERS EXIST ---
        if User.query.count() == 0:
            print("No users found. Creating a default admin user...")
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpassword') # CHANGE THIS PASSWORD!

            admin_user = User(
                username=admin_username,
                email=admin_email,
                is_admin=True # Set them as admin
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Default admin user created: Username: {admin_username}, Email: {admin_email}")
            print(">>> IMPORTANT: Remember to change the default admin password in production! <<<")
        else:
            print("Users already exist. Skipping admin user creation.")

    print("Database initialization complete.")

if __name__ == '__main__':
    app.run(debug=True)