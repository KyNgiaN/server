import os

import psycopg2
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


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
mydb = psycopg2.connect(user='kdjmispwzuqrpa', password='79fabf4112ead809504789c52d5037b2ecdd9967a4a4ef9c64c79df78bf36064', host='ec2-54-74-14-109.eu-west-1.compute.amazonaws.com', database='d8lued2265pr44')
db = mydb.cursor()




@app.route("/")
@login_required
def index():
    #get all stocks properties
    db.execute("SELECT * from cards WHERE usage= " + str(session["user_id"]))
    cards = db.fetchall()

    #get user's cash vccs
    db.execute("SELECT * FROM users WHERE id = " + str(session["user_id"]))
    cash = db.fetchall()[0][3]

    return render_template("index.html", cards = cards, cash = cash)


@app.route("/get", methods=["GET", "POST"])
@login_required
def get():

    if request.method == "POST":
        # Check the validity of the service
        if not request.form.get("service"):
            return apology("Invalid service")

        # variables
        service = request.form.get("service")

        # Select number of vccs cash from database
        db.execute("SELECT * FROM users WHERE id = " + str(session["user_id"]))
        cash = db.fetchall()[0][3]

        # check if available cash is enough
        if cash == 0:
            return apology("You have 0 VCCs left")

        # check if database don't vcc cash
        db.execute("SELECT number FROM cards WHERE usage = 0")
        rows = db.fetchall()
        if len(rows) == 0:
            return apology("VCC not available")

        # get one cardnumber not used
        cardnumber = rows[0][0]


        # Update bought card information
        time = str(datetime.now().strftime("%x")+ ' ' + datetime.now().strftime("%X"))
        db.execute("UPDATE cards SET TIME = '" + time + "' WHERE number = " + str(cardnumber))
        mydb.commit()
        db.execute("UPDATE cards SET usage = " + str(session["user_id"]) + "WHERE number = " + str(cardnumber))
        mydb.commit()
        db.execute("UPDATE cards SET service = '" + service + "' WHERE number = " + str(session["user_id"]))
        mydb.commit()

        # Update cash vccs to users database
        db.execute("UPDATE users SET cash = " + str(cash - 1) + " where id = " + str(session["user_id"]))
        mydb.commit()

        return redirect("/")

    else:
        # Select number of vccs cash from database
        db.execute("SELECT * FROM users WHERE id = " + str(session["user_id"]))
        cash = db.fetchall()[0][3]
        return render_template("get.html", cash = cash)



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
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username")))
        rows = db.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

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
        db.execute("UPDATE users set hash = %s WHERE id = %s", (hashh, session["user_id"]))
        mydb.commit()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Select number of vccs cash from database
        db.execute("SELECT * FROM users WHERE id = " + str(session["user_id"]))
        cash = db.fetchall()[0][3]
        return render_template("changepassword.html", cash = cash)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure username wasn't taken
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username")))
        if db.fetchall():
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
            #search for maximum id
        db.execute("SELECT max(id) FROM users")
        rows = db.fetchall()
        if not rows[0][0]:
            new_id = 1
        else:
            new_id = rows[0][0] + 1
        db.execute("INSERT INTO users (id, username , hash) VALUES (" + str(new_id) + ", '" + username + "', '" + hashh + "')")
        mydb.commit()

        # Query database for information with username
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username")))
        rows = db.fetchall()

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

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
