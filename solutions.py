# THIS IS THE SOLUTION FILE. For best results, do not read this until you look at test.py.

import hashlib
import logging
from flask import Flask, make_response, redirect, render_template, request
import mysql.connector

# [Easy] Secrets in code
# These credentials should not be in source code, where they will be visible to every engineer.
# They should be in a designated secret manager or stored in environment variables.
app = Flask(__name__)
db = mysql.connector.connect(
    host="1.2.3.4",
    user="devuser",
    password="internal-123",
    database="purchases"
)

@app.route("/", methods=["GET"])
def index():
    if "username" not in request.cookies:
        return redirect("/login")
    else:
        user = request.cookies["username"]
        purchases = get_purchases(user)
        render_template("index.html", purchases=purchases)

# [Hard] Credentials passed in GET request
# GET requests pass arguments in the URL query string
# (e.g. https://example.com/login?username=alice&password=swordfish) which will make them visible
# in the URL bar and cause them to be stored in the browser history. Because these arguments are
# sensitive, they should be passed via POST request.
@app.route("/login", methods=["GET"])
def login():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return render_template("login.html")

    # [Easy] Bad hash algorithm
    # MD5 is too fast, and should not be used to hash passwords. These passwords should be hashed
    # with a designated password hash function like bcrypt or PBKDF2.
    hashed_password = hashlib.md5(password)

    # [Medium] Insecure defaults (informational)
    # This if/else statement is confusing: it tests a negative, and logs the user in if that fails.
    # While it is secure at the moment, it would be easy for a small change to introduce a
    # vulnerability. For example, modifying the if statement to check if the user exists in the
    # database would cause unknown users to be logged in by default. To lower the risk of an
    # accident, the conditional should be flipped.
    if get_user(username).password != hashed_password:
        logging.info(f"Failed log in: {username}")
        return render_template("login.html", error=True)
    else:
        response = make_response(redirect("/"))
        # [Medium] Guessable cookies
        # The user session cookies are just their usernames: it would be trivial for an attacker
        # to log in as another user by changing this cookie to the victim's username. These session
        # cookies should be long, unguessable UUIDs.
        response.set_cookie("username", username)
        return response


@app.route("/purchase", methods=["POST"])
def purchase():
    # [Easy] Trusting user input
    # The `username` and `price` values should not be provided as user input. If an attacker
    # changes the username, they could make purchases as another user, and if they modify the price
    # they could choose the amount they pay for an item. Instead, the username should be derived
    # from the session cookie, while the price should be stored in a server-side database.
    username = request.form["user"]
    item_id = request.form["item"]
    quantity = int(request.form["quantity"])
    price = int(request.form["price"])

    # [Hard] Missing CSRF token
    # Even if the username is fixed so it is not passed in as a form parameter, an attacker could
    # still trick a user into making a purchase through CSRF. This function should check for a
    # CSRF token.
    user = get_user(username)

    # [Medium] Lack of data validation
    # An attacker could provide a negative quantity, which would result in their balance going up
    # by the purchase amount rather than down. The code should check that the quantity is always a
    # positive number.
    total = price * quantity

    # [Hard] Race condition
    # If an attacker makes multiple purchases at the same time, it is possible that each request
    # checks the condition and begins running make_purchase before any request calls set_balance.
    # In this case, each request would add a purchase to the database but the user's balance would
    # get overwritten by each request so only the final one would count. To fix this, the code
    # should use an atomic lock so that only one purchase can be in progress at a time.
    if total <= user.balance:
        make_purchase(user, item_id, quantity, price)
        set_balance(user.balance - total)
    else:
        logging.info(f"User attempted to overdraw: {username}")

# [Easy] SQL injection
# Every one of these SQL queries is vulnerable to SQL injection. Ideally they should use an ORM
# instead of writing their own SQL strings, but at the very least they must escape the user input.
def get_purchases(username):
    query = "SELECT * FROM purchases WHERE user = " + username
    return db.cursor().execute(query).fetchall()

def get_user(username):
    query = "SELECT * FROM users WHERE user = " + username
    return db.cursor().execute(query).fetchall()

def set_balance(username, balance):
    query = "UPDATE users SET balance = " + balance + " WHERE user = " + username
    cursor = db.cursor()
    cursor.execute(query)
    cursor.commit()

def make_purchase(username, item_id, quantity, price):
    query = "INSERT INTO purchases VALUES (" + ",".join([username, item_id, quantity, price]) + ")"
    cursor = db.cursor()
    cursor.execute(query)
    cursor.commit()

# [Medium] Debug mode
# Running this app with debug=True causes it to send debugging information to the client on errors,
# which leaks source code and allows attackers to get remote code execution if they are able to
# guess the debug PIN.
app.run(debug=True)