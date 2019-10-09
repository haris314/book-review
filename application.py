import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#initialize goodreads api key
api_key_goodreads = "ROu9HMXKnCA6LsHndTpHDw"

#Home page
@app.route("/")
def home():

    #if the user is already logged in, redirect to the search page
    if session.get("login") is True:
        return redirect(url_for('login'))

    #Render the login page
    return render_template("home.html")
   

#When user tries to register
@app.route("/register", methods=["POST"])
def register():

    #Get the data of the registration form
    name = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    #If any field is null
    if(name is "" or password is "" or confirm_password is ""):
        return render_template("fail.html", detail="None of the field can be empty", message="Registration failed")

    #If paswords don't match
    if(password != confirm_password):
        return render_template("fail.html", detail="Passwords don't match", message="Registration failed")
    
    #Check if username already exists
    existing_user = db.execute("SELECT * FROM _user where name= LOWER(:name)", {"name": name}).fetchone()
    if(existing_user != None):
        return render_template("fail.html", detail="The entered username already exists. Please try again with a different username", message="Registration failed")

    #Check if any value is too long
    if(len(name) > 20 or len(password) > 20):
        return render_template("fail.html", detail="The username or password can't be more than 20 characters", message="Registration failed") 
    
    #Else, register
    db.execute("INSERT INTO _user VALUES (LOWER(:name), :password)", {"name":name, "password":password})
    db.commit()

    return render_template("success_register.html")


#Confusing name. This function is called when someone tries to login
#This function should have been called search or something. My bad! Now it's too late
@app.route("/books", methods=["POST", "GET"])
def login():

    #If someone gets here from GET just give him/her the search page
    if(request.method=="GET"):
        return render_template("books.html")

    #If someone comes here by POST, this means someone is trying to login
    #Get form data
    name = request.form.get('username')
    password = request.form.get('password')

    #Get the user's record from the database
    user = db.execute("SELECT * FROM _user WHERE name=LOWER(:name) AND password=:password", {"name": name, "password":password}).fetchone()

    #If no record exists, given information is not valid. Hence login fails
    if(user is None):
        return render_template("fail.html", message="Login Failed", detail="The username and/or password is incorrect")

    #Tell session that the user is logged in and also the username
    session["login"] = True
    session["username"] = name.lower()

    return render_template("books.html")


#When the user clicks logout
@app.route("/logout")
def logout():

    #Tell session that the user is not logged in now
    session["login"] = False

    return render_template("home.html")


#Displays the search result
@app.route("/books/search?", methods=["GET"])
def search():

    #Get what the user typed
    raw_search = request.args.get('search')
    
    #Ready it for the database query
    search = "%"
    search =search + raw_search + "%"
    
    #Get the criteria which the user specified
    criteria = request.args.get('criteria')
    
    #Get results according to the criteria
    if criteria == "title":
        books_by_title = db.execute("SELECT * FROM book WHERE LOWER(title) LIKE LOWER(:search)", {"search": search})
    elif criteria == "isbn":
        books_by_title = db.execute("SELECT * FROM book WHERE LOWER(isbn) LIKE LOWER(:search)", {"search": search})
    elif criteria== "author":
        books_by_title = db.execute("SELECT * FROM book WHERE LOWER(author) LIKE LOWER(:search)", {"search": search})
    else:
        return ("<h1>404 Page Doesn't exist</h1>")

    return render_template('search.html', result=books_by_title, search=raw_search, criteria=criteria)


#To show the details of a particular book by isbn
#Also shows reviews and allows the user to write a review
@app.route("/books/book_details/<string:isbn>", methods=["GET", "POST"])
def book_details(isbn):

    #If the method is POST, the user has tried to submit a review
    if(request.method == "POST"):

        #If the user tried to submit a review without logging in
        #Give error
        if(session.get("login") == False or session.get("login") == None):
            return render_template("fail.html", message="Login required", detail="Please login before submitting a review")

        #Get the information required to push the review in the database
        name = session["username"]
        rating = request.form.get("rating")
        review = request.form.get("review_given")

        #Don't allow the user to review if it's too short or empty
        if(len(review) < 3):
            return render_template("fail.html", message="Review too short", detail="Review must be at least 3 characters long", was_reviewing=True, isbn=isbn)

        #Check if a review by the user for this isbn already exists
        current_review = db.execute("SELECT * FROM review WHERE name=:name AND isbn=:isbn", {"name": name, "isbn":isbn}).fetchone()

        #If it exists, delete it
        if(current_review != None):
            db.execute("DELETE FROM review WHERE name=:name AND isbn=:isbn", {"name": name, "isbn": isbn})
            db.commit()
        
        #Insert the new review
        db.execute("INSERT INTO review (name, isbn, review, rating) VALUES (:name, :isbn, :review, :rating)", {"name": name, "isbn": isbn, "review": review, "rating": rating})
        db.commit()
    
    #Get the book from the database
    book = db.execute("SELECT * FROM book WHERE isbn=:isbn",{"isbn": isbn} ).fetchone()  

    #If book does not exist in the database
    if(book is None):
        return render_template("fail.html", message="404 Not Found", error="The requested ISBN does not exist in the database"), 404

    #Get reviews for the ISBN
    reviews = db.execute("Select * FROM review WHERE isbn=:isbn ORDER BY number DESC", {"isbn": isbn})
    count = reviews.rowcount
    reviews = reviews.fetchall() 

    #calculatung average rating from the result of the above query
    avg_rating = 0
    if count != 0:
        for review in reviews:
            avg_rating += review.rating
        avg_rating /= count

    #To prevent avg_rating from having a None value
    if(avg_rating is None):
        avg_rating = 0 

    #Round avg_rating to 2 decimal places
    avg_rating = round(avg_rating, 2)

    #Get how many stars to be printed by the html tempelate
    full_stars = int(avg_rating)
    half_star = False
    if(avg_rating - full_stars >= .80):
        full_stars+=1
    elif(avg_rating - full_stars >= .20):
        half_star = True

    #Get data from Goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key_goodreads, "isbns": isbn})
    data = res.json()
    gr_count = int(data["books"][0]["work_ratings_count"])
    gr_avg_rating = float(data["books"][0]["average_rating"])
    
    #Get how many stars to be printed by the html tempelate for Goodreads data
    gr_full_stars = int(gr_avg_rating)
    gr_half_star = False
    if(gr_avg_rating - gr_full_stars >= .80):
        gr_full_stars+=1
    elif(gr_avg_rating - gr_full_stars >= .20):
        gr_half_star = True
    
    return render_template("book_details.html", book=book, reviews=reviews, avg_rating=avg_rating, full_stars=full_stars, half_star=half_star, count=count, gr_avg_rating=gr_avg_rating, gr_full_stars=gr_full_stars, gr_half_star=gr_half_star, gr_count=gr_count)