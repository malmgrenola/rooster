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
from werkzeug.utils import secure_filename
import urllib
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import logging

if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

## AWS S3 is used as CDN, this client is the connection when uploading new images
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SESSION_TOKEN")
)
s3 = boto3.resource('s3')


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Render index for route "/", set page title and display index products
    """

    if request.method == "POST":
        if "product_id" in request.form:
            add_basket_item(request.form.get("product_id"),1)

    products = mongo.db.products.find()

    return render_template("index.html", page_title="Home", products=products)


@app.route("/s")
def search():
    """
    Render search for route "/s" and set page title to query
    """
    return render_template("search.html",page_title="Search")


@app.route("/products")
@app.route("/products/<category>")
def products(category=None):
    """
    Render products for route "/products" and set page title
    """

    category_id = mongo.db.categories.find_one({ "name": { "$eq": category } }).get("_id")
    products = mongo.db.products.find({ "categories": { "$in": [category_id] } })

    return render_template("products.html",page_title="Products", products=products)


@app.route('/product/')
@app.route("/product/<product_id>", methods=["GET", "POST"])
def product(product_id=None):
    """
    Render product for route "/product" and set page title
    """

    if request.method == "POST":
        if "amount" in request.form:
            amount = int(request.form.get("amount"))

    product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })

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
            index = indexOf(basket,"id",request.form["delete"])
            basket.pop(index)
            session["basket"] = basket
            storeBasket()

        elif "update" in request.form:
            # update amount manually
            if "input" in request.form:
                newValue = int(request.form["input"])
                index = indexOf(basket,"id",request.form["update"])
                if newValue > 0:
                    basket[index]["amount"] = newValue
                    session["basket"] = basket
                    storeBasket()

        elif "add" in request.form:
            product = get_basket_item(request.form.get("product_id"))
            add_basket_item(request.form.get("product_id"),int(request.form.get("amount")))
            # newValue = int(request.form["input"])
            # index = indexOf(basket,"id",request.form["update"])
            # if newValue > 0:
            #     basket[index]["amount"] = newValue
            #     session["basket"] = basket
            #     storeBasket()

        elif "place" in request.form:
            # Create a reservetion with current basket
            user = get_user()

            reservation = {
            "client_id": user["_id"],
            "client_name": user["name"],
            "client_email": user["email"],
            "order_comment": "",
            "order_date_confirm": 0,
            "order_date_last_progress": datetime.today(),
            "order_date_pickup": 0,
            "order_date_place": 0,
            "order_date_completed":0,
            "products": basket
            }
            id = mongo.db.reservations.insert_one(reservation).inserted_id

            return redirect(url_for("reservation",reservation_id=id))

        else:
            # a post ation where the the button name is not defiened
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

    # inject calculations & status
    for reservation in reservations:
        order_total = 0
        for product in reservation["products"]:
            sum = int(product["amount"]) * float(product["price"])
            product["sum"] = sum
            order_total += sum
        reservation["reservation_total"] = order_total

        statuses = ["Not Placed", "Not Confirmed by shop", "Confirmed", "Ready for pickup", "Collected"]

        status = 0

        if reservation["order_date_place"] != 0 and reservation["order_date_confirm"] == 0:
            status = 1

        if reservation["order_date_confirm"] != 0:
            status = 2

        reservation["reservation_status"] = statuses[status]

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



@app.route("/admin")
def admin():
    """
    Admin area, redirects to admin_collect by default
    """

    return redirect(url_for("admin_collect"))


@app.route("/admin/collect")
def admin_collect():
    """
    Admin Collect
    """
    reservations = list(mongo.db.reservations.find())

    for reservation in reservations:
        order_value = 0
        order_item_count = 0

        for product in reservation["products"]:
            sum = int(product["amount"]) * float(product["price"])
            order_item_count += int(product["amount"])
            print(product["amount"], product["price"], sum)
            product["sum"] = sum
            order_value += sum
        reservation["order_value"] = order_value
        reservation["order_item_count"] = order_item_count
        reservation["order_date_place"] = getDateTime(reservation["order_date_place"])
        reservation["order_date_pickup"] = getDateTime(reservation["order_date_pickup"])

    return render_template("admin/collect.html",page_title="Click & Collect",reservations=reservations)


@app.route("/admin/collect/<reservation_id>", methods=['GET','POST'])
@app.route("/admin/collect/<reservation_id>/<product_id>", methods=['GET','POST'])
def admin_collect_details(reservation_id=None,product_id=None):

    if request.method == "POST":

        if "save" in request.form:
            data = {}
            if (request.form.get("pickup-date-time") != ""):
                data["pickup-date-time"] = request.form.get("pickup-date-time")

            data["order_comment"] = request.form.get("order_comment")

            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": data})
            flash("Changes saved")

            return redirect(url_for("admin_collect_details",reservation_id=reservation_id))

        if "confirm" in request.form:
            flash("click & collect pickup confirmed")
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"order_date_confirm": datetime.today()}})
            return redirect(url_for("admin_collect_details",reservation_id=reservation_id))

        if "cancel" in request.form:
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {
            "$set": {
            "order_date_confirm": 0
            }})
            flash("click & collect pickup canceled")
            return redirect(url_for("admin_collect_details",reservation_id=reservation_id))

        products = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})["products"]
        index = indexOf(products,"id",ObjectId(product_id))

        if "delete" in request.form:
            products.pop(index)
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product removed")

        elif "update" in request.form:

            products[index]["amount"] = request.form.get("input")
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product amount updated")

        return redirect(url_for("admin_collect_details",reservation_id=reservation_id))


    details = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})

    if (details["order_date_pickup"]!= 0):
        details["order_date_pickup_datetime"] = datetime.strftime(details["order_date_pickup"], '%Y-%m-%dT%H:%M')

    return render_template("admin/collect_details.html",page_title="Click & Collect",details=details)


@app.route("/admin/categories")
def admin_categories():
    """
    Render categories for route "/categories" and set page title
    Categories are already fetched with context providers
    """
    return render_template("admin/categories.html",page_title="Categories")


@app.route("/admin/category/<category_id>", methods=['GET','POST'])
def admin_category(category_id=None):
    """
    Render category from id for route "/category/id" and set page title
    """
    if request.method == "POST":
        if "save" in request.form:
            data = {}
            data["name"] = request.form.get("category_name")
            mongo.db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": data})
            flash("Category details saved")
            return redirect(url_for("admin_categories"))

        if "delete" in request.form:
            mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
            flash("Category deleted")
            return redirect(url_for("admin_categories"))

        if "upload" in request.form:
            filename = handleUpload(request)
            if filename != "":
                mongo.db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": {"image_url": "https://d1o374on78xxxv.cloudfront.net/media/"+filename}})
                return redirect(url_for("admin_category",category_id=category_id))


    if category_id == "new":
        id = mongo.db.categories.insert_one({
        "name": "",
        "image_url": ""}).inserted_id

        return redirect(url_for("admin_category",category_id=id))


    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    return render_template("admin/category.html",page_title="Category",category=category)


@app.route("/admin/products")
def admin_products():

    products = list(mongo.db.products.find())

    for product in products:
        for category in product["categories"]:
            product["categories"] = mongo.db.categories.find_one({"_id": ObjectId(category)})

    return render_template("admin/products.html",page_title="Products",products=products)


@app.route("/admin/product/<product_id>", methods=['GET','POST'])
def admin_product(product_id=None):

    if request.method == "POST":

        if "save" in request.form:
            data = {}
            data["name"] = request.form.get("product_name")
            data["description"] = request.form.get("description")
            data["price"] = float(request.form.get("price"))
            data["categories"] = [ObjectId(request.form.get("category"))]

            mongo.db.products.update_one({"_id": ObjectId(product_id)}, {"$set": data})
            flash("Product details saved")

            return redirect(url_for("admin_products"))

        if "delete" in request.form:
            mongo.db.products.delete_one({"_id": ObjectId(product_id)})
            flash("Product deleted")
            return redirect(url_for("admin_products"))

        if "upload" in request.form:
            filename = handleUpload(request)
            if filename != "":
                mongo.db.products.update_one({"_id": ObjectId(product_id)}, {"$set": {"image_url": "https://d1o374on78xxxv.cloudfront.net/media/"+filename}})
                return redirect(url_for("admin_product",product_id=product_id))

    if product_id == "new":
        id = mongo.db.products.insert_one({
        "name": "",
        "price": None,
        "categories": [],
        "description": "",
        "image_url": ""}).inserted_id

        return redirect(url_for("admin_product",product_id=id))

    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})

    if "categories" in product:
        for category in product["categories"]:
            product["categories"] = mongo.db.categories.find_one({"_id": ObjectId(category)})

    return render_template("admin/product.html",page_title="Product",product=product)


@app.route("/admin/users")
def admin_users():

    users = list(mongo.db.users.find())

    return render_template("admin/users.html",page_title="Users",users=users)


@app.route("/admin/user/<user_id>", methods=['GET','POST'])
def admin_user(user_id=None):
    if request.method == "POST":
        if "save" in request.form:
            data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "isAdmin": bool(request.form.get("isadmin"))
            }
            mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": data})
            flash("User saved")


    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if (not user): return redirect(url_for("admin_users"))

    return render_template("admin/user.html",page_title="Users",user=user)


@app.context_processor
def get_session():
    """
    Session and genaral information avalible on all pages
    """

    user = get_user()
    basket = get_basket()
    categories = list(mongo.db.categories.find())

    basketItems = 0
    for product in basket:
        basketItems += int(product["amount"])

    # print(basketItems)
    # for category in categories:
    #     category["name"] = category["name"].upper()

    return dict(user=user,basket=basket,basketItems=basketItems,categories=categories)


def get_basket():
    """
    get basket from session
    """

    if not "basket" in session:
        session["basket"] = []

    return session["basket"]


def get_basket_item(product_id):
    basket = get_basket()
    index = indexOf(basket,"id",product_id)
    if (index >= 0): return basket[index]
    return []


def add_basket_item(product_id,amount=1):
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    basket = get_basket()

    index = indexOf(basket,"id",str(product["_id"]))
    if index >= 0:
        # Product is already in basket, lets update the quantaty
        basket[index]["amount"] += amount
    else:
        # Product missing in basket, lets add it
        item = {
        "id": str(product["_id"]),
        "name": product["name"],
        "amount": amount,
        "price":product["price"]
        }
        basket.append(item)

    session["basket"] = basket
    storeBasket()
    flash("Basket item added")

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


def sendToBasket():
    print("Send to basket was here")


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


def getDateTime(timestamp):
    print(20,timestamp)
    if (timestamp != 0):
        return timestamp.strftime('%Y-%m-%d %H:%M')

    return timestamp


def handleUpload(request):
    if 'image' not in request.files:
        flash('No file')
        return ""

    file = request.files['image']
    if file.filename == '':
        flash('No selected file')
        return ""

    if file:
        filename = secure_filename(file.filename)
        data = file.read()
        s3.Bucket('cdn.rooster').put_object(Key="media/"+filename, Body=data)
        flash('file uploaded')
        return filename
    return ""


if __name__ == "__main__":
    """
    Run all program functions
    """
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
