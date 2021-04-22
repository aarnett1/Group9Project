import os                 # os is used to get environment variables IP & PORT
   # Flask is the web app that we will customize
from flask import Flask, render_template

app = Flask(__name__)     # create an app

# @app.route is a decorator. It gives the function "index" special powers.
# In this case it makes it so anyone going to "your-url/" makes this function
# get called. What it returns is what is shown as the web page
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from database import db
from models import Event as Event
from models import User as User
from forms import RegisterForm
from flask import session
import bcrypt
from forms import LoginForm
from models import Rsvp as Rsvp
from forms import RegisterForm
from forms import LoginForm


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.config['SECRET_KEY'] = 'SE3155'
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()   # run under the app context

# LOGIN PAGE #  
@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):

            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            return redirect(url_for('index'))

        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        return render_template("login.html", form=login_form)

@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return redirect(url_for('login'))
  
# REGISTRATION PAGE #
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate_on_submit():
        # salt and hash password
        h_password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())
        # get entered user data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        # create user model
        new_user = User(first_name, last_name, request.form['email'], h_password)
        # add user to database and commit
        db.session.add(new_user)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        session['user_id'] = new_user.id  # access id value from user model of this newly added user
        # show user dashboard view
        return redirect(url_for('index'))

    # something went wrong - display register view
    return render_template('register.html', form=form)

# EVENTS (HOME) PAGE #
@app.route('/index')
def index():
    # retrieve user from database
    # check if a user is saved in session
    if session.get('user'):
        events = db.session.query(Event).all()
        #users = db.session.query(User).all
        #rsvps = db.session.query(Rsvp).all
        #rsvp = db.session.query(Rsvp).get(Rsvp.event_id).filter_by(user_id=session['user_id']).all()
        my_event = db.session.query(Event).filter_by(user_id=session['user_id']).all()
        my_rsvp = db.session.query(Rsvp).filter_by(user_id=session['user_id']).all()
        return render_template("index.html", index=events, my_events = my_event, my_rsvps = my_rsvp, user=session['user'])
    else:
        return redirect(url_for('login'))

# CREATE PAGE #
@app.route('/event/new', methods=['GET', 'POST'])
def new():
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['eventText']
            date = request.form['date']
            new_record = Event(title, text, date, session['user_id'], report_count=0)
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('index'))
        else:
            return render_template('new.html', user=session['user'])
    else:
        return redirect(url_for('login'))

# INDIVIDUAL EVENT (EDIT) PAGE #
@app.route('/index/edit/<event_id>', methods = ['GET', 'POST'])
def edit(event_id):
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            date = request.form['date']
            text = request.form['eventText']
            edit_event = db.session.query(Event).filter_by(id=event_id).one()
            edit_event.title = title
            edit_event.date = date
            edit_event.text = text
            db.session.add(edit_event)
            db.session.commit()

            return redirect(url_for('index'))
        else:
            my_event = db.session.query(Event).filter_by(id=event_id).one()

            return render_template("new.html", event=my_event, user=session['user'])
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))

# INDIVIDUAL EVENT PAGE #
@app.route('/index/<event_id>')
def event(event_id):
# check if a user is saved in session
    if session.get('user'):
        # retrieve event from database
        a_event = db.session.query(Event).filter_by(id=event_id).one()

        return render_template("event.html", event=a_event, user=session['user'])
    else:
        return redirect(url_for('login'))

# ACCOUNT INFO PAGE #
@app.route('/edit/list/<event_id>', methods = ['POST'])
def list(event_id):
    listed = request.form['listed']
    event = db.session.query(Event).filter_by(id=event_id).one()
    event.listed = True
    return render_template("index.html")

# ACCOUNT INFO PAGE #
@app.route('/profile/userID')
def profile():
#insert code
    return render_template("profile.html")

# Delete event
@app.route('/index/delete/<event_id>', methods=['POST'])
def delete_event(event_id):
    if session.get('user'):
        # Retrieve event from database
        my_event = db.session.query(Event).filter_by(id=event_id).one()

        # Delete the event
        db.session.delete(my_event)
        db.session.commit()

        # Go to events page after event is deleted
        return redirect(url_for('index'))
    else:
        # User is not in session, redirect to login
        return redirect(url_for('login'))

# RSVP to an event
@app.route('/index/<event_id>/rsvp', methods=['GET', 'POST'])
def rsvp (event_id):
    if session.get('user'):
        # Retrieve event from database
        my_rsvp = db.session.query(Event).filter_by(id=event_id).one()

        # Add the event to RSVP'd events
        new_rsvp = Rsvp(my_rsvp.id, session['user_id'])
        db.session.add(new_rsvp)
        db.session.commit()

        # Go to events page after event has been RSVP'd
        return redirect(url_for('index'))
    else:
        # User is not in session, redirect to login
        return redirect(url_for('login'))

@app.route('/index/<event_id>/report', methods=['GET','POST'])
def report(event_id, report_count):
    if session.get('user'):
        # Retrieve event from database and the amount of times it was reported
        reported_event = db.session.query(Event).filter_by(id=event_id).one()
        report_count = db.session.query(Event).filter_by(count=report_count).one()
        # Increment amount of times it has been reported by 1
        report_count = report_count + 1

        # Delete event if it has been reported 3 times
        if report_count == 3:
            delete_event(reported_event)

            # Return to home page after event is deleted
            return redirect(url_for('index'))

        # Return to event's page
        return render_template("event.html", event=reported_event, user=session['user'])
    else:
        # User is not in session, redirect to login
        return redirect(url_for('login'))


app.run(host=os.getenv('IP', '127.0.0.1'),port=int(os.getenv('PORT', 5000)),debug=True) 
