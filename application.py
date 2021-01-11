import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# API_KEY
#export API_KEY=pk_168905a2c3154b8a96a6b54a593dda7e

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET"])
@login_required
def index():
    money = db.execute("SELECT cash FROM users WHERE (id = :id)", id=session["user_id"])
    total_money = money[0]['cash']
    total_money = float(total_money)
    total_cash = money[0]['cash']
    total_cash = usd(float(total_cash))
    user_stocks = db.execute("SELECT ticker, sum(num_of_stocks) AS shares FROM transactions WHERE (user_id = :user_id) GROUP BY ticker HAVING shares > 0",
                user_id=session["user_id"])
    index = 0
    for stock in user_stocks:
        ticker = stock["ticker"]
        num_of_shares = stock["shares"]
        curr_stock = lookup(ticker)
        curr_price = curr_stock["price"]
        stock["price"] = usd(float(curr_price))
        value = float((curr_price * num_of_shares))
        stock["value"] = usd(value)
        index += 1
        total_money += float(value)

    total_money = usd(total_money)
    return render_template("index.html", user_stocks = user_stocks, total_money = total_money, total_cash = total_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    # if User reached route via GET mthod just load the page
    if request.method == "GET":
        return render_template("buy.html")
    else:
        # ensure symbol was submitted and shares are number
        if not request.form.get("symbol"):
            return apology("symbol required")
        elif not request.form.get("shares").isdigit() or float(request.form.get("shares")) <= 0:
            return apology("shares must be an integer greater than 0")

        # look symbol up and check if it was successful
        stock = lookup(request.form.get("symbol"))
        shares = request.form.get("shares")
        if stock:
            Total = float(shares) * stock["price"]
            funds = db.execute("SELECT * FROM users WHERE id = :id",
                          id=session["user_id"])

            if funds[0]["cash"] < Total:
                return apology ("not enough money, you're poor")
            else:
                db.execute("INSERT INTO transactions (user_id, ticker, num_of_stocks, buy_sell_price, time) VALUES (:user_id, :ticker, :num_of_stocks, :buy_sell_price, :time)",
                            user_id=session["user_id"], ticker=request.form.get("symbol").upper(), num_of_stocks=shares, buy_sell_price=stock["price"],time=datetime.now())
                db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=funds[0]["cash"] - Total, id=session["user_id"])
                return redirect("/")
        else:
            return apology("symbol not found")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_stocks = db.execute("SELECT ticker, num_of_stocks AS shares, buy_sell_price AS price, time FROM transactions WHERE (user_id = :user_id)", user_id=session["user_id"])
    # if User reached route via GET method just load the page
    if request.method == "GET":
        for stock in user_stocks:
            if stock["shares"] > 0:
                stock["buy_sell"] = "BOUGHT"
            else:
                stock["buy_sell"] = "SOLD"
        return render_template("history.html", user_stocks = user_stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

 # if User reached route via GET mthod just load the page
    if request.method == "GET":
        return render_template("quote.html")

    else:
        # ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("symbol required")

        # look symbol up and check if it was successful
        stock = lookup(request.form.get("symbol"))
        if stock:
            return render_template("quoted.html", Name=stock["name"], Price=stock["price"], Symbol=stock["symbol"])
        else:
            return apology("symbol not found")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

        # Forget any user_id
    session.clear()


    # if User reached route via GET mthod just load the page
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                        username=request.form.get("username"))

        # Ensure username does not exist
        if len(rows) == 1:
            return apology("username already exists", 403)

        # Otherwise ensure the password and confirmation match and add the user
        else:
            if (len(request.form.get("password")) > 16 or len(request.form.get("password")) < 8):
                return apology("password must be between 8 and 16 characters")
            elif request.form.get("password") == request.form.get("confirmation"):
                pw = request.form.get("password")
                pw_hash = generate_password_hash(pw, method='pbkdf2:sha256')
                username = request.form.get("username")
                db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=pw_hash)
                return render_template("registered.html")
            else:
                return apology("the two passwords provided did not match", 403)


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_stocks = db.execute("SELECT ticker, sum(num_of_stocks) AS shares FROM transactions WHERE (user_id = :user_id) GROUP BY ticker HAVING shares > 0", user_id=session["user_id"])
    # if User reached route via GET mthod just load the page
    if request.method == "GET":
        return render_template("sell.html", user_stocks = user_stocks)
    else:
        # ensure symbol was submitted and shares are number
        if not request.form.get("symbol"):
            return apology("stock selection required")
        elif not request.form.get("shares").isdigit() or float(request.form.get("shares")) <= 0:
            return apology("shares must be an integer greater than 0")
        for stock in user_stocks:
            if stock["ticker"] == request.form.get("symbol") and stock["shares"] < float(request.form.get("shares")):
                return apology("you dont own that many shares")
            else:
                pass

        # look symbol up and check if it was successful
        stock = lookup(request.form.get("symbol"))
        shares = request.form.get("shares")
        if stock:
            Total = float(shares) * stock["price"]
            funds = db.execute("SELECT * FROM users WHERE id = :id",
                          id=session["user_id"])

            db.execute("INSERT INTO transactions (user_id, ticker, num_of_stocks, buy_sell_price, time) VALUES (:user_id, :ticker, :num_of_stocks, :buy_sell_price, :time)",
                        user_id=session["user_id"], ticker=request.form.get("symbol").upper(), num_of_stocks=-float(shares), buy_sell_price=stock["price"],time=datetime.now())
            db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=funds[0]["cash"] + Total, id=session["user_id"])
            return redirect("/")
        else:
            return apology("symbol not found")


@app.route("/password", methods=["GET", "POST"])
def password():
    """change password"""


    # if User reached route via GET mthod just load the page
    if request.method == "GET":
        return render_template("password.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure password was submitted
        if not request.form.get("current_password") or not request.form.get("confirmation") or not request.form.get("new_password"):
            return apology("must fill in all 3 fields", 403)

        # Query database for username
        rows = db.execute("SELECT hash FROM users WHERE id = :id",
                        id=session["user_id"])
        print(rows)
        print(generate_password_hash(request.form.get("new_password"), method='pbkdf2:sha256'))

        if check_password_hash(rows[0]["hash"], request.form.get("new_password")):
            return apology("the new password must be different from the old password")
        elif request.form.get("new_password") != request.form.get("confirmation"):
            return apology("the new passwords entered do not match")
        elif (len(request.form.get("new_password")) > 16 or len(request.form.get("new_password")) < 8):
            return apology("password must be between 8 and 16 characters")
        else:
            pw = request.form.get("new_password")
            pw_hash = generate_password_hash(pw, method='pbkdf2:sha256')
            db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash=pw_hash, id=session["user_id"])
            return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
