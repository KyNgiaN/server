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


from helpers import apology

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



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # check the validity of key
        if not request.form.get("key"):
            return apology("invalid key")

        # info about vccs lelft
            # Select number of vccs cash from database
        key = request.form.get("key")
        db.execute("SELECT * FROM users WHERE username = %s", key)
        rows = db.fetchall()
        if len(rows) == 0:
            return apology("Invalid key")
        cash = rows[0][3]

        # info about cards
            #get all stocks properties
        db.execute("SELECT * from cards WHERE usage = %s", key)
        cards = db.fetchall()



        return render_template("indexed.html", info = 'VCCs left : ' + str(cash), cash = cash, cards = cards)

    else:
        return render_template("index.html")

@app.route("/get", methods=["GET", "POST"])
def get():
    if request.method == "POST":
        # Check the validity of the service and key
        if not request.form.get("key"):
            return apology("invalid key")
        if not request.form.get("service"):
            return apology("invalid service")

        # variables
        service = request.form.get("service")
        key = request.form.get("key")

        # Select number of vccs cash from database
        db.execute("SELECT * FROM users WHERE username = %s", key)
        rows = db.fetchall()
        if len(rows) == 0:
            return apology("Invalid key")
        cash = rows[0][3]
            # check the validity of the key

        # check if available cash is enough
        if cash == 0:
            return apology("You have 0 VCCs left")

        # check if database don't vcc cash
        db.execute("SELECT number FROM cards WHERE usage = 'walo'")
        rows = db.fetchall()
        if len(rows) == 0:
            return apology("VCC not available")

        # get one cardnumber not used
        cardnumber = rows[0][0]


        # Update bought card information
        time = str(datetime.now().strftime("%x")+ ' ' + datetime.now().strftime("%X"))
        db.execute("UPDATE cards SET TIME = '" + time + "' WHERE number = " + str(cardnumber))
        mydb.commit()
        db.execute("UPDATE cards SET usage = '" + key + "' WHERE number = " + str(cardnumber))
        mydb.commit()
        db.execute("UPDATE cards SET service = '" + service + "' WHERE number = " + str(cardnumber))
        mydb.commit()

        # Update cash vccs to users database
        db.execute("UPDATE users SET cash = " + str(cash - 1) + " where username = %s", key)
        mydb.commit()

        return redirect("/")

    else:
        mydb.commit()
        return render_template("get.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
