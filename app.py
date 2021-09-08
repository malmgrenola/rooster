import os
from flask import (
    Flask, render_template, request,
    flash, redirect, session, url_for)
from markupsafe import escape
from flask_pymongo import PyMongo
from bson import json_util, ObjectId
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

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Render index for route "/", set page title and display index products
    """

    if request.method == "POST":
        print(request.form)
        if "product_id" in request.form:
            product = mongo.db.products.find_one({"_id": ObjectId(request.form.get("product_id"))})
            basket = get_basket()

            index = indexOf(basket,"id",str(product["_id"]))
            print(10,index)
            if index >= 0:
                # Product is already in basket, lets update the quantaty
                basket[index]["amount"] += 1
            else:
                # Product missing in basket, lets add it
                item = {
                "id": str(product["_id"]),
                "name": product["name"],
                "amount": 1,
                "price":product["price"]
                }
                basket.append(item)

            session["basket"] = basket
            storeBasket()
            flash("Basket item added")

    products = mongo.db.products.find()

    return render_template("index.html", page_title="Home", products=products)


@app.route("/s")
def search():
    """
    Render search for route "/s" and set page title to query
    """
    return render_template("search.html",page_title="Search")


@app.route("/products")
def products():
    """
    Render products for route "/products" and set page title
    """
    products = mongo.db.products.find()
    print(10,products)
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



@app.route("/basket", methods=["GET", "POST"])
def basket():
    """
    Render basket & button handlers for basket page
    """
    if request.method == "POST":
        basket = get_basket()

        if "delete" in request.form:
            # Remove product from basket
            print("del",request.form["delete"])
            index = indexOf(basket,"id",request.form["delete"])
            basket.pop(index)
            session["basket"] = basket
            storeBasket()

        elif "update" in request.form:
            # update amount manually
            print("update",request.form["update"])

            if "input" in request.form:
                newValue = int(request.form["input"])
                index = indexOf(basket,"id",request.form["update"])
                if newValue > 0:
                    basket[index]["amount"] = newValue
                    session["basket"] = basket
                    storeBasket()

        elif "place" in request.form:
            # Create a reservetion with current basket
            print("place",request.form["place"])
            user = get_user()

            reservation = {
            "client_name": user["name"],
            "client_email": user["email"],
            "order_comment": "",
            "order_date_confirm": 0,
            "order_date_last_progress": datetime.today(),
            "order_date_pickup": 0,
            "order_date_place": 0,
            "products": basket
            }
            id = mongo.db.reservations.insert_one(reservation).inserted_id

            return redirect(url_for("reservation",reservation_id=id))

        else:
            # a post ation where the the button name is not defiened
            print("unkown button",request.form)
            pass

    return render_template("basket.html",page_title="Basket")


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


@app.route("/signin", methods=["GET","POST"])
def signin():
    """
    Render signin for route "/signin" and set page title.
    If user exist function will redirect to a page.
    """
    if request.method == "POST":
        #Check if username already exists in db
        existing_user = mongo.db.users.find_one({"email": request.form.get("email").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):

                        session["user"] = request.form.get("email").lower()
                        if "basket" in existing_user:
                            print(300,existing_user)
                            session["basket"] = existing_user["basket"]
                            print(301,session)
                        flash("Welcome, {}".format(existing_user["name"]))
                        return redirect(url_for("profile"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("signin"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("signin"))


    return render_template("/auth/signin.html",page_title="Sign in")


@app.route("/users")
def users():
    """
    Render users for route "/users" and set page title
    """

    users = mongo.db.users.find({})

    return render_template("users.html",page_title="Users", users=users)


@app.route("/profile/overview", methods=['GET','POST'])
def profile():
    """
    Render user profile based on session cookie and set page title
    Post will update user details and set new user cookie
    """
    user = get_user()

    if not user:
        return redirect(url_for("signin"))

    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"email": user["email"]})

        filter = { '_id': existing_user["_id"] }
        newvalues = { "$set": {'name': request.form.get("name"), "email": request.form.get("email").lower()} }

        mongo.db.users.update_one(filter, newvalues)
        session["user"] = request.form.get("email").lower()
        flash("Your new details are saved")

    reservations = mongo.db.reservations.find({"client_email": user})
    return render_template("/profile/overview.html",page_title="User",reservations=reservations)


@app.route("/profile/reservations")
def reservations():
    """
    Render reservations for route "profile/reservations" and set page title
    """
    user = get_user()

    if not user:
        return redirect(url_for("signin"))

    reservations = list(mongo.db.reservations.find({"client_email": user["email"]}))
    return render_template("profile/reservations.html",page_title="Reservation", reservations=reservations)


@app.route("/profile/reservation/")
@app.route("/profile/reservation/<reservation_id>")
def reservation(reservation_id=0):
    """
    Render reservation for route "/reservation" and set page title
    """

    user = get_user()

    reservation = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})

    return render_template("profile/reservation.html",page_title="reservation", reservation=reservation)


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been signed out")
    session.pop("user")
    session.pop("basket")

    return redirect(url_for("signin"))


@app.context_processor
def get_session():
    """
    Session and genaral information avalible on all pages
    """

    user = get_user()
    basket = get_basket()
    categories = mongo.db.categories.find()

    return dict(user=user,basket=basket,categories=categories)


def get_basket():
    """
    get basket from session
    """

    if not "basket" in session:
        session["basket"] = []

    return session["basket"]

def get_user():
    """
    Return avalible user information based on current cookie.
    Ensure sensitive data is removed.
    """
    if not session:
        return {}

    if not "user" in session:
        return {}

    email = urllib.parse.unquote(session["user"])

    if not email:
        return {}

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return {}

    # Remove data we don't want to share
    user.pop('password', None)
    user.pop('isAdmin', None)
    user.pop('_id', None)
    user.pop('basket', None)

    return user


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def storeBasket():
    """
    Store basket on user record if user is signed in
    """

    user = get_user()

    if "email" in user:
        mongo.db.users.update_one({"email": user["email"]}, {"$set": {"basket": session["basket"]}})


def indexOf(array,key,value):
    """
    Return first index of specific key with a specific value in an array of objects.
    Nothing found returns index -1
    """
    for index, element in enumerate(array):
        if element[key] == value:
            return index
    return -1


if __name__ == "__main__":
    """
    Run all program functions
    """
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
