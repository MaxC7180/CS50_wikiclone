import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, login_check
# Configure application
app = Flask(__name__)

#email config
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '73aa9c473d5ce2'
app.config['MAIL_PASSWORD'] = 'c17e353b36a193'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Ensure templates are auto reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)


@app.route("/", methods=["GET","POST"])
def first_index():
    login = login_check()
    return render_template("index.html",login = login)

@app.route("/index", methods=["GET","POST"])
def index():
    login = login_check()
    if not request.form.get("search"):
        render_template("index.html", login = login,)
    return render_template("index.html", login = login,)

@app.route("/login", methods=["GET","POST"])
def login():
    login = login_check()
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("login.html", login = login)

        username = request.form.get("username")
        password = request.form.get("password")
        user_check = db.execute("SELECT * FROM users WHERE username = ?", username)
        #user does not exist or passwords do not match
        if len(user_check) != 1 or not check_password_hash(user_check[0]["password"], password):
            return render_template("login.html", login = login)

        session["id"] = user_check[0]["id"]
        return render_template("index.html", login = username)

    return render_template("login.html", login = login)

@app.route("/become", methods=["GET","POST"])
def become():
    login = login_check()
    if request.method == "POST":
        if not request.form.get("become"):
            return render_template("login.html", login = login)
        email = request.form.get("become")
        email_check = db.execute("SELECT * FROM users WHERE email=?", email)
        cur_user = db.execute("SELECT username FROM users WHERE id = ?", session['id'])
        if len(email_check) != 1 or email_check[0]['username'] != cur_user[0]['username']:
            return render_template("login.html", login = login, error2="Email does not exist/ does not match user")
        msg = Message('WikiClone Contributer Request', sender='WikicloneProject@gmail.com', recipients = [email])
        msg.html = "<b>{email} wants to become a contrributor</b><br>".format(email=email)
        mail.send(msg)

    return render_template("login.html")

@app.route("/logout", methods=["GET","POST"])
def logout():
    session.clear()
    return redirect("/index")


@app.route("/create", methods=["GET","POST"])
def create_account():
    #to do
    login = login_check()
    if request.method == "POST":
        #user did not put any required information in the form and messed with the HTML that prevents them from doing this
        email = None
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("Cpassword"):
            return render_template("create.html", login = login)
        if request.form.get("password") != request.form.get("Cpassword"):
            pCon = "Passwords do not match"
            return render_template("create.html", pCon = pCon)
        #user decided to put an email and we must check if its in use
        if request.form.get("email"):
            used_email = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))
            #email is already in use
            if len(used_email) != 0:
                return render_template("create.html", em = "Email already in use")
            else:
                email = request.form.get("email")

        user = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        user_ID_num = db.execute("SELECT id FROM users")
        if len(user_ID_num) > 0:
            user_ID = user_ID_num[len(user_ID_num) - 1]["id"] + 1
        else:
            user_ID = 1

        #Check if the username is taken
        user_check = db.execute("SELECT * FROM users WHERE username = ?", user)
        if len(user_check) != 0:
            return render_template("create.html", taken = "Username is already in use")

        db.execute("INSERT INTO users VALUES (?, ?, ?, f, ?)", user_ID, user, password, email)
        return render_template("create.html", login = login)
    return render_template("create.html")

@app.route("/about", methods=["GET", "POST"])
def about_me():
    return render_template("about_me.html")

@app.route("/contribute", methods=["GET", "POST"])
@login_required
def contribute():
    login = login_check()
    user = db.execute("SELECT contributor FROM users WHERE id = ?", session["id"])
    if user[0]["contributor"] != 1:
        return redirect("/login")
    if request.method == "POST":
        if not request.form.get("title") or not request.form["body"]:
            error1 = "You did not input all of the perameters"
            return render_template("contribute.html", error1 = error1, login=login)
        title, body = request.form.get("title"), request.form.get("body")
        check = db.execute("SELECT title FROM article WHERE title=?", title)
        #title is already in use
        if len(check) != 0:
            error2 = "Title is already in use"
            return render_template("contribute.html", error2 = error2, login=login)

        db.execute("INSERT INTO article VALUES (?, ?)", title, body)

    return render_template("contribute.html", login=login)


@app.route("/article", methods=["GET","POST"])
def article():
    login = login_check()
    if request.method == "POST":
        if not request.form.get("search"):
                return render_template("index.html", login = login)
        if request.form.get("search"):
            search = request.form.get("search")
            article = db.execute("SELECT * FROM article WHERE title LIKE ?","%" + search + "%")
            if len(article) == 0:
                return render_template("index.html", login = login)
            title, body = article[0]["title"], article[0]["body"]
            return render_template("article.html", title = title, body = body, login = login)

        perms_check = db.execute("SELECT contributor FROM users WHERE id = ?", session["id"])
        if perms_check[0]["contributor"] == 1:
            info = request.data
            tt, text, count = [], [], 0
            for c in info:
                if c == ord('+'):
                    count += 1
                    if count == 3:
                        count = 0
                        text.pop(0)
                        text.pop(len(text)-1)
                        tt.append(''.join(text))
                        text = []
                else:
                    text.append(chr(c))
                    count = 0
            title1, edited_text = tt[0], tt[1]
            db.execute("UPDATE article SET body = ? WHERE title = ?", edited_text, title1)

    title, body, pic = "Such empty", "Many vacancies, use the search bar and type something in it :p", True
    return render_template("article.html", title=title, body=body, pic=pic, login=login)