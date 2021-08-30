import os
from flask import (
    Flask, render_template, request,
    flash, redirect, session, url_for)
from markupsafe import escape
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
    """
    Render index for route "/" and set page title
    """
    return render_template("index.html",page_title="Home")


@app.route("/c")
def products():
    """
    Render products for route "/products" and set page title
    """
    products = mongo.db.products.find()
    return render_template("products.html",page_title="Products", products=products)


@app.route('/product/')
@app.route("/product/<product>")
def product(product=None):
    """
    Render product for route "/product" and set page title
    """
    return render_template("product.html",page_title=f'Product {escape(product)}', product=product)


@app.route("/categories")
def categories():
    """
    Render categories for route "/categories" and set page title
    """
    categories = mongo.db.categories.find()
    print(categories)
    return render_template("categories.html",page_title="Categories", categories=categories)

@app.route("/category/")
@app.route("/category/<category>")
def category(category=None):
    """
    Render category for route "/category" and set page title
    """
    category = mongo.db.categories.find_one()
    return render_template("category.html",page_title="Category", category=category)


@app.route("/reservations")
def reservations():
    """
    Render reservations for route "/reservations" and set page title
    """
    reservations = mongo.db.reservations.find()
    print(reservations)
    return render_template("reservations.html",page_title="Reservation", reservations=reservations)


@app.route("/reservation/")
@app.route("/reservation/<reservation>")
def reservation(reservation=None):
    """
    Render reservation for route "/reservation" and set page title
    """
    reservation = mongo.db.reservations.find_one(reservation)
    print(reservation)
    return render_template("reservation.html",page_title="reservation", reservation=reservation)


@app.route("/register", methods=["GET","POST"])
def register():
    """
    Render register for route "/register" and set page title.
    If user exist function will redirect to signin page.
    First user in DB will be admin otherwise user will be added to DB.
    """
    if request.method == "POST":
        #Check if username already exists in db
        existing_user = mongo.db.users.find_one(
        {"email": request.form.get("email").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("signin"))

        register = {
            "name": request.form.get("name"),
            "email": request.form.get("email").lower(),
            "isAdmin": False,
            "password": generate_password_hash(request.form.get("password"))
        }

        #Check if it is the first user and make sure it's a administrator.
        numberOfRecords = mongo.db.users.count_documents({})

        if numberOfRecords == 0:
            register["isAdmin"] = True

        mongo.db.users.insert_one(register)
        # put user in a 'session' cookie
        session["email"] = request.form.get("email").lower()
        flash("Registration Successful!")


    return render_template("/auth/register.html",page_title="Register")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    """
    Run all program functions
    """
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
