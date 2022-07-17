from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps


db = SQL("sqlite:///users.db")
def login_required(f):
    """Decorate routes to require login when attempting to edit something on the page"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login_check():
    try:
        if session["id"]:
            id = session["id"]
            name = db.execute("SELECT username FROM users WHERE id=?",id)
            login = name[0]["username"]
            return login
    except:
        login = "Not logged in"
        return login