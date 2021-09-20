import os
from flask import (
    Flask, render_template, request,
    flash, redirect, session, url_for)
from markupsafe import escape
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
from bson.decimal128 import Decimal128, create_decimal128_context
import json
from werkzeug.security import generate_password_hash, check_password_hash
import urllib
from datetime import datetime

if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

result = mongo.db.reservations.aggregate([
    {
        '$set': {
            'order_date_completed': 0
        }
    }
])
print(1,list(result))
