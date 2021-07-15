import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd


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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL(os.getenv("postgres://oitvllsscccfmv:efd8b4882c1c2aa20e211b327c8685d87ee9c111280d8912e38c6051559094fd@ec2-54-83-82-187.compute-1.amazonaws.com:5432/d8frkjf6a75vnrL"))


@app.route("/")
@login_required
def index():
    #get all stocks properties
    cards = db.execute("SELECT * from cards WHERE usage=? ", str(session["user_id"]))

    #get user's left vccs
    left = db.execute("SELECT left FROM users WHERE id = ?", session["user_id"])[0]["left"]

    return render_template("index.html", cards = cards, left = left)


@app.route("/get", methods=["GET", "POST"])
@login_required
def get():

    if request.method == "POST":
        # Check the validity of the service
        if not request.form.get("service"):
            return apology("Invalid service")

        # variables
        service = request.form.get("service")

        # Select number of vccs left from database
        left = db.execute("SELECT left FROM users WHERE id = ?", session["user_id"])[0]["left"]

        # check if available cash is enough
        if left == 0:
            return apology("You have 0 VCCs left")

        # check if database don't vcc left
        rows = db.execute("SELECT number FROM cards WHERE usage = 0")
        if len(rows) == 0:
            return apology("VCC not available")

        # get one cardnumber not used
        cardnumber = rows[0]["number"]


        # Update bought card information
        time = str(datetime.now().strftime("%x")+ ' ' + datetime.now().strftime("%X"))
        db.execute("UPDATE cards SET TIME = ? WHERE number = ?", time, cardnumber)
        db.execute("UPDATE cards SET usage = ? WHERE number = ?", session["user_id"], cardnumber)
        db.execute("UPDATE cards SET service = ? WHERE number = ?", session["user_id"], service)

        # Update left vccs to users database
        db.execute("UPDATE users SET left = ? WHERE id = ?", (left - 1), session["user_id"])

        return redirect("/")

    else:
        # Select number of vccs left from database
        left = db.execute("SELECT left FROM users WHERE id = ?", session["user_id"])[0]["left"]
        return render_template("get.html", left = left)


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    rows = []
    if request.method == "POST":
        rows = db.execute(request.form.get("query"))
        return render_template("queried.html", rows = rows)
    else:
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
        if username != "admin":
            return redirect("/")
        return render_template("admin.html")



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

        # Query database for information with username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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

@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    if request.method == "POST":

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password")

        # Ensure password was confirmed
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match")

        # save username and password in variables
        password = request.form.get("password")

        # Hash password
        hashh = generate_password_hash(password)

        # save in database
        db.execute("UPDATE users set hash = ? WHERE id = ?", hashh, session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Select number of vccs left from database
        left = db.execute("SELECT left FROM users WHERE id = ?", session["user_id"])[0]["left"]
        return render_template("changepassword.html", left = left)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure username wasn't taken
        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("username taken")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure password was confirmed
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match")

        # save username and password in variables
        username, password = request.form.get("username"), request.form.get("password")

        # Hash password
        hashh = generate_password_hash(password)

        # save in users database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashh)

        # Query database for information with username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Forget any user_id
        session.clear()
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
