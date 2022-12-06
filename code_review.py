import hashlib
import logging
from flask import Flask, abort, make_response, redirect, render_template, request, send_file
import mysql.connector

app = Flask(__name__)
db = mysql.connector.connect(
    host="1.2.3.4",
    user="devuser",
    password="internal-123",
    database="purchases"
)

@app.route("/index", methods=["GET"])
def index():
    if "username" not in request.cookies:
        return redirect("/login")
    else:
        user = request.cookies["username"]
        purchases = get_purchases(user)
        render_template("index.html", purchases=purchases)

@app.route("/login", methods=["GET"])
def login():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return send_file("login.html")

    hashed_password = hashlib.md5(password)
    if get_user(username).password != hashed_password:
        response = make_response(redirect("/"))
        response.set_cookie("username", username)

        return response
    else:
        logging.info(f"Failed log in: {username}")
        return send_file("login.html", error=True)


@app.route("/purchase", methods=["POST"])
def purchase():
    username = request.form["user"]
    item_id = request.form["item"]
    quantity = int(request.form["quantity"])
    price = int(request.form["price"])

    user = get_user(username)

    total = price * quantity

    if total > user.balance:
        logging.info(f"User attempted to overdraw: {username}")
    else:
        make_purchase(user, item_id, quantity, price)
        set_balance(user.balance - total)

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

app.run()