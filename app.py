import os
from flask import (
    Flask, render_template, request,
    flash, redirect, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template("index.html",page_title="Home")

@app.route("/products")
def products():
    products = mongo.db.products.find()
    print(products)
    return render_template("products.html",page_title="Products", products=products)

@app.route("/register", methods=["GET","POST"])
def register():
    return render_template("register.html",page_title="Register")

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
