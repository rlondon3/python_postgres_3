import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def hello_world():
    return 'Hello World!'