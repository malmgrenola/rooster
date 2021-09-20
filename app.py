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

    products = mongo.db.products.aggregate([{ "$sample": { "size": 4 } }])

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

    category = mongo.db.categories.find_one({ "name": { "$eq": category } })
    category_id = category.get("_id")
    products = mongo.db.products.find({ "categories": { "$in": [category_id] } })

    return render_template("products.html",page_title=category["name"], products=products,category=category)


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

    return render_template("product.html",page_title=product["name"], product=product)


@app.route("/basket", methods=["GET", "POST"])
def basket():
    """
    Render basket & button handlers for basket page
    """

    basket = get_basket()

    if request.method == "POST":
        basket = get_basket()

        if "delete" in request.form:
            # Remove product from basket
            index = indexOf(basket,"id",request.form["delete"])
            basket.pop(index)
            session["basket"] = basket
            storeBasket()

        if "update" in request.form:
            # update amount manually
            if "input" in request.form:
                newValue = int(request.form["input"])
                index = indexOf(basket,"id",request.form["update"])
                if newValue > 0:
                    basket[index]["amount"] = newValue
                    session["basket"] = basket
                    storeBasket()

        if "add" in request.form:
            product = get_basket_item(request.form.get("product_id"))
            amount = int(request.form.get("amount")) if "amount" in request.form else 1

            add_basket_item(request.form.get("product_id"),amount)

        if "place" in request.form:
            # Create a reservation with current basket
            user = get_user()
            if not user:
                flash("You must sign up or sig in before order can be placed")
                return redirect(url_for("signin"))
            user_id = mongo.db.users.find_one({ "email": { "$eq": user["email"] } }).get("_id")

            reservation = {
            "client_id": user_id,
            "client_name": user["name"],
            "client_email": user["email"],
            "order_comment": "",
            "order_date_pickup": 0,
            "order_placed": False,
            "products": basket
            }
            id = mongo.db.reservations.insert_one(reservation).inserted_id
            session["basket"] = []
            flash("Your basket is now prepared for a collect")
            return redirect(url_for("reservation",reservation_id=id))

    basket_total = inject_basket(basket)

    return render_template("basket.html",page_title="Basket",basket_total=basket_total)


@app.route("/register", methods=["GET","POST"])
def register():
    """
    Render register for route "/register" and set page title.
    If user exist function will redirect to sign in page.
    First user in DB will be admin otherwise the user will be added to DB.
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

        #Check if it is the first user and make sure it's an administrator.
        numberOfRecords = mongo.db.users.count_documents({})

        if numberOfRecords == 0:
            register["isAdmin"] = True

        mongo.db.users.insert_one(register)
        # put user in a 'session' cookie
        session["email"] = request.form.get("email").lower()
        flash("Registration Successful!")
        return redirect(url_for("signin"))


    return render_template("/auth/register.html",page_title="Register")


@app.route("/signin", methods=["GET","POST"])
def signin():
    """
    Render signin for route "/signin" and set page title.
    If a user exists function will redirect to a page.
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
                            session["basket"] = existing_user["basket"]
                        flash("Welcome, {}".format(existing_user["name"]))
                        return redirect(url_for("me"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("signin"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("signin"))


    return render_template("/auth/signin.html",page_title="Sign in")


@app.route("/me/overview", methods=['GET','POST'])
def me():
    """
    Render user me based on session cookie and set page title
    Post will update user details and set new user cookie
    """
    user = get_user()

    if not user:
        return redirect(url_for("signin"))

    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"email": user["email"]})

        filter = { '_id': existing_user["_id"] }
        newvalues = { "$set": {'name': request.form.get("name")} }

        mongo.db.users.update_one(filter, newvalues)
        flash("Your new details are saved")
        return redirect(url_for("me"))

    reservations = get_reservations()

    return render_template("/me/overview.html",page_title="Me",reservations=reservations)


@app.route("/me/reservation/")
@app.route("/me/reservation/<reservation_id>",methods=['GET','POST'])
def reservation(reservation_id=0):
    """
    Render reservation for route "/reservation" and set page title
    """

    if request.method == "POST":

        # Delete button pressed
        if "delete" in request.form:
            order_placed = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)}).get("order_placed")
            if order_placed:
                flash("Can't delete collected order")
                return redirect(url_for("reservation",reservation_id=reservation_id))

            if not order_placed:
                mongo.db.reservations.delete_one({"_id": ObjectId(reservation_id)})
                flash("Reservation deleted")

            return redirect(url_for("me"))

        if "place" in request.form:
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"order_placed": True}})
            flash("Click & Collect placed! Thank you!")
            return redirect(url_for("reservation",reservation_id=reservation_id))

        if "set" in request.form:
            if not "pickup-date-time" in request.form:
                flash("No valid date")

            d = datetime.strptime(request.form.get("pickup-date-time"), "%Y-%m-%dT%H:%M")
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"order_date_pickup": d}})
            flash("Pickup date set")
            return redirect(url_for("reservation",reservation_id=reservation_id))

        if "update" in request.form:
            product_id = request.args.get('id')
            products = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)}).get("products")
            index = indexOf(products,"id",product_id)
            products[index]["amount"] = int(request.form.get("input"))
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product amount updated")
            return redirect(url_for("reservation",reservation_id=reservation_id))

        if "remove" in request.form:
            product_id = request.args.get('id')
            products = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)}).get("products")
            index = indexOf(products,"id",product_id)
            products.pop(index)
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product removed")
            return redirect(url_for("reservation",reservation_id=reservation_id))

    reservation = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})

    reservation = inject_reservation(reservation)

    return render_template("me/reservation.html",page_title="My Reservation", reservation=reservation)


@app.route("/logout")
def logout():
    # remove user from session cookie
    session.pop("user")
    session.pop("basket")
    flash("You have been signed out")
    return redirect(url_for("signin"))


# All Administrator Helpers
@app.route("/admin")
def admin():
    """
    Admin area, redirects to admin_collect by default
    """

    if not confirm_admin(): return redirect(url_for('logout'))

    return redirect(url_for("admin_collect"))


@app.route("/admin/collect")
def admin_collect():
    """
    Admin Collect
    """

    if not confirm_admin(): return redirect(url_for('logout'))
    list(mongo.db.reservations.find(filter={},sort=[( "order_date_pickup", -1 )]))
    reservations = list(mongo.db.reservations.find())

    for reservation in reservations:
        order_value = 0
        order_item_count = 0

        for product in reservation["products"]:
            sum = int(product["amount"]) * float(product["price"])
            order_item_count += int(product["amount"])
            product["sum"] = sum
            order_value += sum
        reservation["order_value"] = order_value
        reservation["order_item_count"] = order_item_count
        reservation["order_date_pickup"] = getDateTime(reservation["order_date_pickup"])

    return render_template("admin/collect.html",page_title="Click & Collect",reservations=reservations)


@app.route("/admin/collect/<reservation_id>", methods=['GET','POST'])
def admin_collect_details(reservation_id=None):

    if not confirm_admin(): return redirect(url_for('logout'))

    if request.method == "POST":

        if "save" in request.form:
            data = {}
            if (request.form.get("pickup-date-time") != ""):
                data["pickup-date-time"] = request.form.get("pickup-date-time")

            data["order_comment"] = request.form.get("order_comment")

            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": data})
            flash("Changes saved")

            return redirect(url_for("admin_collect_details",reservation_id=reservation_id))

        if "terminate" in request.form:
            mongo.db.reservations.delete_one({"_id": ObjectId(reservation_id)})
            flash("Click and Collect deleted")

            return redirect(url_for("admin_collect"))

        product_id = request.args.get('product_id')
        products = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})["products"]
        index = indexOf(products,"id",product_id)

        if "delete" in request.form:
            products.pop(index)
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product removed")

        if "update" in request.form:

            products[index]["amount"] = request.form.get("input")
            mongo.db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": {"products": products}})
            flash("product amount updated")

        return redirect(url_for("admin_collect_details",reservation_id=reservation_id))


    details = mongo.db.reservations.find_one({"_id": ObjectId(reservation_id)})

    if (details["order_date_pickup"]!= 0):
        details["order_date_pickup_datetime"] = datetime.strftime(details["order_date_pickup"], '%Y-%m-%dT%H:%M')

    return render_template("admin/collect_details.html",page_title="Reservation details",details=details)


@app.route("/admin/categories")
def admin_categories():
    """
    Render categories for route "/categories" and set page title
    Categories are already fetched with context providers
    """

    if not confirm_admin(): return redirect(url_for('logout'))

    return render_template("admin/categories.html",page_title="Categories")


@app.route("/admin/category/<category_id>", methods=['GET','POST'])
def admin_category(category_id=None):
    """
    Render category from id for route "/category/id" and set page title
    """

    if not confirm_admin(): return redirect(url_for('logout'))

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

    if category_id == "new":
        id = mongo.db.categories.insert_one({"name": ""}).inserted_id

        return redirect(url_for("admin_category",category_id=id))


    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    return render_template("admin/category.html",page_title="Category",category=category)


@app.route("/admin/products")
def admin_products():

    if not confirm_admin(): return redirect(url_for('logout'))

    products = list(mongo.db.products.find())

    for product in products:
        for category in product["categories"]:
            product["categories"] = mongo.db.categories.find_one({"_id": ObjectId(category)})

    return render_template("admin/products.html",page_title="Products",products=products)


@app.route("/admin/product/<product_id>", methods=['GET','POST'])
def admin_product(product_id=None):

    if not confirm_admin(): return redirect(url_for('logout'))

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



    return render_template("admin/product.html",page_title=product["name"],product=product)


@app.route("/admin/users")
def admin_users():

    if not confirm_admin(): return redirect(url_for('logout'))

    users = list(mongo.db.users.find())

    return render_template("admin/users.html",page_title="Users",users=users)


@app.route("/admin/user/<user_id>", methods=['GET','POST'])
def admin_user(user_id=None):

    if not confirm_admin(): return redirect(url_for('logout'))

    if request.method == "POST":
        if "save" in request.form:
            data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "isAdmin": bool(request.form.get("isadmin"))
            }
            mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": data})
            flash("User saved")

        if "delete" in request.form:
            mongo.db.users.delete_one({"_id": ObjectId(user_id)})
            flash("User deleted")
            return redirect(url_for("admin_users"))

    edituser = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if (not edituser): return redirect(url_for("admin_users"))

    return render_template("admin/user.html",page_title=edituser["name"],edituser=edituser)


# All Context Processors
@app.context_processor
def inject_user():
    """
    inject current user information
    """
    return {"user": get_user()}


@app.context_processor
def inject_categories():
    """
    inject all categories
    """
    categories = list(mongo.db.categories.find())
    return {"categories": categories}


@app.context_processor
def inject_basket():
    """
    inject basket and the total items count in basket
    """

    basket = get_basket()
    basketItems = 0
    for product in basket:
        basketItems += int(product["amount"])

    return {"basket": basket,"basketItems": basketItems}


@app.context_processor
def inject_year():
    """
    inject today year and today form datetime input
    """
    return {"year": datetime.today().year,"now": datetime.today().strftime('%Y-%m-%dT%H:%M')}


# All Local helpers
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
        # Product is already in basket, lets update the quantity
        basket[index]["amount"] += amount
    else:
        # Product missing in basket, let's add it
        item = {
        "id": str(product["_id"]),
        "name": product["name"],
        "amount": amount,
        "price":product["price"],
        "image_url":product["image_url"]
        }
        basket.append(item)

    session["basket"] = basket
    storeBasket()
    flash("Basket item added")


def get_user():
    """
    Return available user information based on the current cookie.
    Ensure sensitive data is removed.
    """
    if not session:
        return {}

    if not "user" in session:
        return {}

    email = session["user"]

    if not email:
        return {}

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return {}

    # Remove data we don't want to share
    user.pop('password', None)
    #user.pop('isAdmin', None)
    user.pop('_id', None)
    user.pop('basket', None)

    return user


def storeBasket():
    """
    Store basket on user record if user is signed in
    """

    user = get_user()

    if "email" in user:
        mongo.db.users.update_one({"email": user["email"]}, {"$set": {"basket": session["basket"]}})


def indexOf(array,key,value):
    """
    Return the first index of a specific key with a specific value in an array of objects.
    Nothing found returns index -1
    """
    for index, element in enumerate(array):
        if element[key] == value:
            return index
    return -1


def getDateTime(timestamp):
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


def get_reservations():
    """
    returns all user reservations based on the current session cookie email.
    injects reservation calculations and current reservation status
    """
    user = get_user()
    reservations = list(mongo.db.reservations.find(filter={"client_email": user["email"]},sort=[( "order_date_pickup", -1 )]))

    # inject calculations & status
    for reservation in reservations:
        reservation = inject_reservation(reservation)

    return reservations


def inject_reservation(reservation):
    """
    injects and returns reservation calculations and current reservation status
    """
    order_total = 0
    for product in reservation["products"]:
        sum = int(product["amount"]) * float(product["price"])
        product["sum"] = sum
        order_total += sum
    reservation["reservation_total"] = order_total

    return reservation


def inject_basket(basket):
    """
    injects calculations to basket items and returns the total
    """
    total = 0
    for product in basket:
         sum = int(product["amount"]) * float(product["price"])
         product["sum"] = sum
         total += sum

    return total


def confirm_admin():
    user = get_user()
    if not user["isAdmin"]:
        flash('You are not allowed here!')
    return user["isAdmin"]


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
