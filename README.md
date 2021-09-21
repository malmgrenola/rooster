# Purple Rooster Farm Shop

The local farm shop site that promotes their products online with the ability to reserve goods in advance.

Live site location:

[Purple Rooster Farm Shop Website](https://purple-rooster.herokuapp.com/)

![badge](https://img.shields.io/w3c-validation/html?style=plastic&targetUrl=https%3A%2F%2Fpurple-rooster.herokuapp.com)

Live site screenshot:
![Purple Rooster Farm Shop layout](wireframes/rooster-site.png)

#### Table of Contents

[UX](#ux)

[Features](#features)

- [Existing Features](#existing-features)
  - [Site content](#site-content)
  - [Style Information](#style-information)
- [Features Left to Implement](#features-left-to-implement)

[Technologies Used](#technologies-used)

[Testing](#testing)

- [Known issues](#known-issues)

- [Deployment](#deployment)
- [Development](#development)

- [Credits](#credits)

## UX

The typical website user is interested in sourcing local farm products.

The site owners goal is to promote products that is for sale in the local farm shop and administrator reservations from website users.

- As an admin user, I would like to [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) my products to the website so my customers can see what the farm shop currently sells.
- As a user, I would like to click and collect items for later pickup in the farm shop, so I know items are available when I visit the shop on site.
- As an admin, I would like to [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) all click and collect so I can see all reservations and remove reservations.
- As a user, I would like to login to the site and see my click and collect, so I can follow up on what I have for pickups.
- As an admin, I would like to login to the site, so I can administer products, click and collects & users.
- As an admin, I would like to comment on the click and collect, so I can let other admins know if there is anything to mention.

Site screenshots are found in the project folder [/wireframes](wireframes).

Site wireframes:

- [Front page](wireframes/front.png) search meal page, showing search results. Also acts as site index page
- [Product detail page](wireframes/product.png) displays product details.
- [basket page](wireframes/basket.png) displays selected items prepared for reservation.
- [admin page](wireframes/admin.png) displays user details including clicks and collects.

## Features

The website contains a clear navigation on every page.
The site is based on a navigational hierarchical tree structure.
Navigation bar is responsive and will fold down to a burger menu when it wont fit the size.

**Navigation items:**
Home
Category navigation
Click and collect basket
Sign in _(only anonymous users)_
My page _(only signed in users)_
Admin _(only signed in admins)_

Each page includes a footer element containing copyright information about the site.
[Footer wireframe example](wireframes/footer.png)

### Existing Features

- Sign in/out - allows users to sign in to see reservations made and sign out when the user would like to leave.
- Sign up - allows users to sign up for an account so users don't have to fill out the information again.
- Find products by category - allows users to find products based on category.
- Add to click and collect basket - allows users to add product to a basket while navigating on the site.
- Create click and collect reservation - send current click and collect basket to the farm shop.
- Set requested pickup date
- Administrate users - CRUD
- Administrate products - CRUD
- Administrate categories - CRUD
- Administrate reservations - CRUD
- Upload product images to external CDN for use on this website.
- Front page shows random products

#### Database model

[MongoDB](https://www.mongodb.com/) is used to store all data. Within one cluster ("Cluster0") the database "roosterDB'' contain the following collections:

- [Users collection](#users-collection)
- [Categories collection](#categories-collection)
- [Products collection](#products-collection)
- [Reservations collection](#reservations-collection)
  - [Products Array of objects](#products-array-of-objects)

##### Users collection

Users collection holds client contact and access information.

| field    | type     | description                |
| -------- | -------- | -------------------------- |
| \_id     | ObjectId | unique record id           |
| name     | string   | Holds client Full name     |
| email    | string   | Holds client email address |
| password | string   | user hashed password       |
| isAdmin  | Boolean  | Gives user admin access    |

##### Categories collection

Categories collection holds a list of the different product categories.

| field | type     | description         |
| ----- | -------- | ------------------- |
| \_id  | ObjectId | unique record id    |
| name  | string   | Holds Category name |

##### Products collection

Products collection holds information about each product.

| field       | type       | description                |
| ----------- | ---------- | -------------------------- |
| \_id        | ObjectId   | unique record id           |
| name        | string     | Holds product name         |
| description | string     | Holds product description  |
| price       | Decimal128 | product item price         |
| image-url   | string     | Holds url to product image |
| categories  | Array      | Array of categories id's   |

##### Reservations collection

Reservation collection holds each reservation in separate records.

| field                                  | type     | description                         |
| -------------------------------------- | -------- | ----------------------------------- |
| \_id                                   | ObjectId | unique record id                    |
| client_id                              | ObjectId | Client id                           |
| client-name                            | string   | Holds client Full name              |
| client-email                           | string   | Holds client email address          |
| [products](#products-array-of-objects) | Array    | Holds an array of product objects   |
| order-comment                          | string   | Client order comment                |
| order-date-pickup                      | Date     | Date when client pickups order      |
| order_placed                           | Boolean  | True when customer placed the order |

###### Products Array of objects

Each product client would like to reserve.

| field  | type       | description                                  |
| ------ | ---------- | -------------------------------------------- |
| id     | string     | products id reference                        |
| name   | string     | Holds product name                           |
| amount | Int32      | Number of items client would like to reserve |
| price  | Decimal128 | product item price                           |
| sum    | Decimal128 | the product of the amount and prices         |

#### Site content

The sample products, information and images is provided from Product [daylesford.com](https://www.daylesford.com/online-shop/)

About text is used from [Tapnell farm](https://tapnellfarm.com/about-tapnell-farm)

#### Style Information

##### Selected Typefaces

Site uses sans-serif to stay clean on all supported platforms.

##### Color Scheme

The site color scheme is wooden and high contrast, with user information text and navigation bar in light color

### Features Left to Implement

- ...

## Technologies Used

In this section, all of the languages, frameworks, libraries, and any other tools that are used to construct this project are listed with its name, a link to its official site and a short sentence of why it was used.

- [HTML5](https://www.w3.org/TR/html52/)
  - Used to render the DOM
- [CSS](https://www.w3.org/Style/CSS/Overview.en.html)
  - Used to layout the site.
- [Javascript](https://developer.mozilla.org/en/JavaScript)
  - Used to handle site code logic and API integrations
- [Python+Flask](https://flask.palletsprojects.com/en/2.0.x/)
  - used to render site and connect to database
- [MongoDB](https://www.mongodb.com/)
  - Used to store all data.
- [Bootstrap](https://getbootstrap.com/docs/5.0/getting-started/introduction/)
  - used to make site responsive
- [Fontawesome](https://fontawesome.com/)
  - Used to display icons on website
- [JQuery](https://jquery.com)
  - The project uses **JQuery** to simplify DOM manipulation.
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html#)
  - Used to create, configure, and manage AWS services.

## Testing

Site is tested on the following platforms and browsers

- Mac
  - Google Chrome (91.0.4472.106)
  - Safari (14.1.1)
  - Firefox (89.0.1)
- Windows 10
  - Google Chrome (91.0.4472.114)
  - Edge (91.0.864.53)
  - Firefox (89.0.1)
- Iphone 12
  - Safari
  - Google Chrome
- Android Samsung S12
  - Google Chrome

All tests pass on all platforms.

### Test users

#### Test sign in

1. feature test:
   1. Go to a https://purple-rooster.herokuapp.com/signin
   2. use username `user@rooster.com` and password `bad`
   3. Confirm incorrect Username and/or Password.
   4. use username `user@rooster.com` and password `123456`
   5. Confirm successful sign in.
   6. change your user name and press `Save name`

Feature passed this test

#### Test sign up

1. feature test:
   1. When signed out, Go to http://purple-rooster.herokuapp.com/register
   2. register with name `My name` and email `user@rooster.com` use any password
   3. confirm username already exists message
   4. register with name `Your Name` and email `anythingrandom@rooster.com` use password `123456`
   5. Confirm Registration Successful!
   6. sign in with new username
   7. confirm successful login

Feature passed this test

#### Test sign out

1. feature test:
   1. When signed in, Go to http://purple-rooster.herokuapp.com/me/overview
   2. click `sign out` next to username in header
   3. confirm you are signed out and redirected to sign in page

Feature passed this test

### Test Click and Collect

The site has a click and collect feature by adding items to a basket and from basket click click and collect.
The user can select a pickup date and place the order.

The feature handles errors & success in the UI.

#### Test basket Click and collect

The feature handles errors & success in the UI.

1. feature test:
   1. Go to front page
   2. Click `Add to basket` on any product
   3. Click `Add to basket` on another product
   4. Confirm by click on cart in top menu
   5. step up a couple of steps on product row and press update
   6. press the trash icon on one of the rows and confirm the item is removed.

Feature passed this test

#### Test place click and collect

1. feature test:
   1. with items in basket
   2. go to http://purple-rooster.herokuapp.com/basket
   3. click `Click and Collect` button in the bottom of the form
   4. select Select your prefered pickup date in the date time field and press `set pickup date button`
   5. modify your items and confirm functions update and remove
   6. click the `Place Click and collect`
   7. confirm your order is placed

Feature passed this test

### Test Administrator

The site has an administrator section where the site can be controlled.

The feature handles errors & success in the UI.

#### Test Admin Click and collect

The feature handles errors & success in the UI.

1. feature test:
   1. When signed out, Sign in as `admin@rooster.com` and password `123456`
   2. In the navbar click the toolbox (http://purple-rooster.herokuapp.com/admin/collect)
   3. Click on any sample Click & Collect made to open up details
   4. confirm pickup date, comment and items row can update on request using `Save changes`
   5. confirm a sample click and collect can be deleted by clicking `delete`

Feature passed this test

#### Test Admin Categories

The feature handles errors & success in the UI.

1. feature test:
   1. in the admin section click `Categories` in the horizontal toolbar.
   2. Press `create new`
   3. Give the new category the name `Test` and press `Save`
   4. Confirm toolbar get the new category `Test`
   5. Go back to Category `Test` and click `Delete category`
   6. Confirm `Test` is removed from toolbar

Feature passed this test

#### Test Admin Products

The feature handles errors & success in the UI.

1. feature test:

   1. in the admin section click `Products` in the horizontal toolbar.
   2. Press `create new` at the bottom of the page.
   3. Give the new product the name `Test product`
   4. Give the new product the description `A test description`
   5. Give the new product the price `10`
   6. Select category `Meat`
   7. Press `Save`
   8. Download sample image to your local desktop from https://purple-rooster.herokuapp.com/static/assets/testproduct.jpg
   9. click choose file and select the sample image from your local desktop
   10. Press upload and confirm `file uploaded` message
   11. In the top navbar click `Meat section` and confirm `Test product` is there.
   12. Go back to http://purple-rooster.herokuapp.com/admin/products and click on test product
   13. Press `Delete product` and confirm the product is deleted in the list.

Feature passed this test

#### Test Admin Users

The feature handles errors & success in the UI.

1. feature test:

   1. sign out and register a test user.
   2. Sign in as `admin@rooster.com` and password `123456`
   3. In the admin section click `Users` in the horizontal toolbar.
   4. Click on the user created in step 1
   5. confirm name change, email change and set as admin change when `Save` is clicked
   6. Confirm the user is removed when `delete` is clicked.

Feature passed this test

### Confirm Page not found

1. Goto "https://purple-rooster.herokuapp.com/nothing"
2. Confirm you get a "Page not found" Page

Feature passed this test

### HTML & CSS Validator tests

Each page should return no errors & warnings using [validator.w3.org](https://validator.w3.org/)

#### Pages to test

1. [index.html](https://validator.w3.org/nu/?checkerrorpages=yes&useragent=Validator.nu%2FLV+http%3A%2F%2Fvalidator.w3.org%2Fservices&acceptlanguage=&doc=https%3A%2F%2Fpurple-rooster.herokuapp.com%2F)
2. [Product Fruits Page](https://validator.w3.org/nu/?doc=https%3A%2F%2Fpurple-rooster.herokuapp.com%2Fproducts%2FFruits)

Pages are validated without errors or warnings.

### CSS Validation

Site CSS should return no errors or warnings.

1. [CSS Validator testing style.css](https://jigsaw.w3.org/css-validator/validator?uri=https%3A%2F%2Fpurple-rooster.herokuapp.com%2Fstatic%2Fcss%2Fstyles.css&profile=css3svg&usermedium=all&warning=1&vextwarning=&lang=sv)
2. [CSS Validator testing rooster.css](https://jigsaw.w3.org/css-validator/validator?uri=https%3A%2F%2Fpurple-rooster.herokuapp.com%2Fstatic%2Fcss%2Frooster.css&profile=css3svg&usermedium=all&warning=1&vextwarning=&lang=sv)

CSS files passed the test. Note that there are Bootstrap warnings.

### Known issues

1. When clicking the navbar and a new route is made, style is flickering before landing on the correct style.
2. Admin section products table is wider than the width of most small screens portrait mode.

## Deployment

Site is deployed to https://purple-rooster.herokuapp.com/ using [Heruko](https://heruko.com).

Heroku is connected to the Github repository with automatic deployment from the branch `main`.
Every push or merge to main will trigger a new deployment.

make sure you run `pip3 freeze > requirements.txt` for all dependencies used.

## Development

Versioning of this project uses [Github](https://github.com/)

1. Fork the [rooster repo](https://github.com/malmgrenola/rooster)
2. In the terminal run `git clone https://github.com/{your-own-gituser-here}/rooster.git` - to fetch code
3. In the terminal run `cd rooster` - to place yourself in the root of the project.
4. In the terminal run `python3 app.py` - to start a dev environment.

A `python3` should start using the file `app.py` serving the Flask app and the site is now available on `http://localhost:3000`.

## Credits

### Template

The template shop-homepage used on this site is from [Start Bootstrap](https://startbootstrap.com/template/shop-homepage)

### Media

The photos used in this site were obtained from:

- [daylesford.com](https://www.daylesford.com/online-shop/)
- [background](https://www.rawpixel.com/image/578551/brown-wood-texture-high-resolution-image)
  - Modified with [Adobe Photoshop](https://www.adobe.com/products/photoshop.html)
- [rooster in logo](https://www.rawpixel.com/image/2603952/free-illustration-png-chicken-rooster-cock)
  - Modified with [Adobe Photoshop](https://www.adobe.com/products/photoshop.html)
- [testproduct.jpeg](https://purple-rooster.herokuapp.com/static/assets/testproduct.jpg)
  - Produced with [Adobe Photoshop](https://www.adobe.com/products/photoshop.html)

### Acknowledgements

- I received inspiration from [code institute](https://codeinstitute.net/)
- https://www.chromium.org/developers/design-documents/create-amazing-password-forms
- https://farmorslycka.se/en/farmshop/
- https://www.beckettsfarm.co.uk/farm-shop/click-and-collect/
