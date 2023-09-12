from flask import Flask, request, session, make_response, jsonify
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import re
import psycopg2
import psycopg2.extras
import jwt

CREATE_USERS_TABLE = """CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY, 
                        first_name VARCHAR (100) NOT NULL, 
                        last_name VARCHAR (100) NOT NULL,
                        address VARCHAR (250) NOT NULL,
                        city VARCHAR (100) NOT NULL,
                        state VARCHAR (2) NOT NULL, 
                        zip INTEGER NOT NULL,
                        user_name VARCHAR (50) NOT NULL,
                        email VARCHAR (50) NOT NULL,
                        password VARCHAR (255) NOT NULL
                        );"""
INSERT_INTO_USERS_TABLE_RETURNING_ID = """INSERT INTO users (
                                        first_name, 
                                        last_name,
                                        address, 
                                        city, 
                                        state,
                                        zip, 
                                        user_name, 
                                        email, 
                                        password
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"""
GET_USER = "SELECT * FROM users WHERE user_name = %s;"
CREATE_PRODUCTS_TABLE = (
    "CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name VARCHAR(100), description VARCHAR(250), price NUMERIC (5, 2));"
)
INSERT_INTO_PRODUCTS_TABLE_RETURNING_ID = """INSERT INTO products (
                                        name, 
                                        description,
                                        price
                                    ) VALUES (%s, %s, %s) RETURNING id;"""
GET_PRODUCTS = "SELECT * FROM products WHERE name = %s;"
CREATE_ORDERS_TABLE = (
    "CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, order_status VARCHAR(100), user_id bigint REFERENCES users(id) ON DELETE CASCADE);"
)
INSERT_INTO_ORDERS_TABLE_RETURNING_ID = """INSERT INTO orders (
                                        order_status, 
                                        user_id
                                    ) VALUES (%s, %s) RETURNING id;"""
GET_ORDERS = "SELECT * FROM orders WHERE user_id = %s;"
CREATE_PRODUCTS_ORDERED_TABLE = (
    "CREATE TABLE products_ordered (id SERIAL PRIMARY KEY, order_id bigint REFERENCES orders(id) ON DELETE CASCADE, products_id bigint REFERNCES products(id) ON DELETE RESTRICT, quantity integer);"
)

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

def token_requireed(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert': 'Token missing!'})
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({"Alert": "Invalid Token"})
    return decorated

@app.route("/")
def home():
    if 'loggedin' in session:
        return {"message": {session['user_name']}}, 201
    return {"message": "User is not logged in!"}

@app.route("/api/auth")
@token_requireed
def auth():
    return {"message": "Authenticated!"}

@app.post("/api/login")
def login():
    data = request.get_json()
    user_name = data["user_name"]
    password = data["password"]
    with connection:
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(GET_USER, (user_name,))
            account = cursor.fetchone()
            if account:
                password_rs = account['password']
                token = jwt.encode({
                    'user': account["user_name"],
                    'expiration': str(datetime.utcnow() + timedelta(seconds=120))
                },
                app.config['SECRET_KEY'])

                if check_password_hash(password_rs, password):
                    session['loggedin'] =  True
                    session['id'] = account['id']
                    session['user_name'] = account['user_name']
                    return ({"message": "Login successful!", "token": token}), 201
                else:
                    return make_response("Unable to verify", 403, {"WWW-Authenticate": "Basic real: 'Authentication Failed!'"})
            else:
                return {"message": "Account not found!"}
            
@app.post("/api/signup")
def register():
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    address = data['address']
    city = data['city']
    state = data["state"]
    zip = data['zip']
    user_name =  data['user_name']
    email = data['email']
    password = data['password']
    
    with connection:
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(GET_USER, (user_name,))
            account = cursor.fetchone()
            if account:
                return {"message": "User already exists. Please login."}
            elif not re.match(r'[^@]+@[^@]+\.[^a]+', email):
                return {"message": "Invalid: please check email address."}
            elif not re.match(r'[A-Za-z0-9]+', user_name):
                return {"message": "Invalid: username must contain only characters and numbers."}
            elif not user_name or not password or not email:
                return {"message": "Invalid: please check username, email, and password."}
            else:
                cursor.execute(INSERT_INTO_USERS_TABLE_RETURNING_ID, (first_name, last_name, address, city, state, zip, user_name, email, generate_password_hash(password)))
                connection.commit()
                return {"message": "User successful registered"}, 201
@app.post("/api/products")
def create_product():
    data = request.get_json()
    name = data['name']
    description = data['description']
    price = data['price']
    with connection:
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(CREATE_PRODUCTS_TABLE)
            cursor.execute(GET_PRODUCTS, (name,))
            product = cursor.fetchone()
            if product:
                return {"message": data}
            elif not name:
                return {"message": "Product not found!"}
            else:
                cursor.execute(INSERT_INTO_PRODUCTS_TABLE_RETURNING_ID, (name, description, price))
                connection.commit()
                return {"message": 'Product added!'}, 201
@app.post("/api/orders")
def create_orders():
    data = request.get_json()
    order_status = data['order_status']
    user_id = data['user_id']
    with connection:
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(CREATE_ORDERS_TABLE)
            cursor.execute(GET_ORDERS, (user_id,))
            order = cursor.fetchone()
            if order:
                return {"message": data}
            elif not id:
                return {"message": "Order not found!"}
            else:
                cursor.execute(INSERT_INTO_ORDERS_TABLE_RETURNING_ID, (order_status, user_id))
                connection.commit()
                return {"message": "Order added!"}, 201