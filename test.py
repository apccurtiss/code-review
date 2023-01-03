import hashlib
import logging
from flask import Flask, make_response, redirect, render_template, request
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
        return render_template("login.html")

    hashed_password = hashlib.md5(password)
    if get_user(username).password != hashed_password:
        logging.info(f"Failed log in: {username}")
        return render_template("login.html", error=True)
    else:
        response = make_response(redirect("/"))
        response.set_cookie("username", username)
        return response


@app.route("/purchase", methods=["POST"])
def purchase():
    username = request.form["user"]
    item_id = request.form["item"]
    quantity = int(request.form["quantity"])
    price = int(request.form["price"])

    user = get_user(username)

    total = price * quantity

    if total <= user.balance:
        make_purchase(user, item_id, quantity, price)
        set_balance(user.balance - total)
    else:
        logging.info(f"User attempted to overdraw: {username}")

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