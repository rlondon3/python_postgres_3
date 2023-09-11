import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request

CREATE_USERS_TABLE = (
    "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(100), password VARCHAR(100));"
)
CREATE_PRODUCTS_TABLE = (
    "CREATE TABLE IF NOT EXISTS product (id SERIAL PRIMARY KEY, name VARCHAR(100), description  VARCHAR(250), price NUMBER(5, 2));"
)
CREATE_ORDERS_TABLE = (
    "CREATE TABLE orders (id SERIAL PRIMARY KEY, order_status VARCHAR(100), user_id bigint REFERENCES users(id) ON DELETE CASCADE);"
)
CREATE_PRODUCTS_ORDERED_TABLE = (
    "CREATE TABLE products_ordered (id SERIAL PRIMARY KEY, order_id bigint REFERENCES orders(id) ON DELETE CASCADE, products_id bigint REFERNCES products(id) ON DELETE RESTRICT, quantity integer);"
)

app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Hello World!'