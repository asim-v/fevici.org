REBUILD_DB = True
FDEBUG = True

import os, re
from sys import stderr
from flask import Flask, g, send_from_directory, flash, render_template, abort, request, redirect, url_for, session, Response
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import or_
from datetime import datetime, timedelta
from dateutil import parser
from random import getrandbits
from models import db, User, Event, populateDB

def create_app():
    app = Flask(__name__)
    DB_NAME = os.path.join(app.root_path, 'catering.db')
    
    app.config.update(dict(
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY='erl67',
        TEMPLATES_AUTO_RELOAD=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///' + DB_NAME
    ))
    
    db.init_app(app)
    
    if REBUILD_DB == True and os.access(DB_NAME, os.W_OK):
        os.remove(DB_NAME)
        print('DB Dropped')
        
    if os.access(DB_NAME, os.W_OK):
        print('DB Exists')
    else:
        app.app_context().push()
        db.drop_all()
        db.create_all()
        print('DB Created')
        populateDB()
    print(app.__str__(), end="  ")
    return app

app = create_app()

@app.cli.command('initdb')
def initdb_command():
    db.drop_all()
    db.create_all()
    populateDB()
    print('Initialized the database.')
    
@app.before_request
def before_request():
    g.user = None
    g.events = None
    if 'uid' in session:
        g.user = User.query.filter_by(id=session['uid']).first()
        if g.user != True:
            g.events = Event.query.order_by(Event.id.asc()).all()
        else:
            g.events = Event.query.filter(Event.client == g.user.id).order_by(Event.date.asc()).all()
    eprint("g.user: " + str(g.user))
    #eprint("g.events: " + str(g.events))
    
@app.before_first_request
def before_first_request():
    eprint("    🥇")
    
@app.context_processor
def utility_processor():
    def getName(id):
        user = User.query.filter(User.id==id).first()
        if user != None:
            return user.username
        else:
            return ""
    return dict(getName=getName)

@app.route("/register/", methods=["GET", "POST"])
def signer():
    if g.user:
        flash("Already logged in!")
        return redirect(url_for("index"))
    #elif request.method == "GET":
        #flash("Complete form to register")
    elif request.method == "POST":
        POST_USER = remove_tags(str(request.form['user']))
        POST_PASS = remove_tags(str(request.form['pass']))
        POST_EMAIL = remove_tags(str(request.form['mail']))
        if POST_USER != None and POST_PASS != None:
            newUser = User(POST_USER, POST_PASS, POST_EMAIL)
            db.session.add(newUser)
            try:
                db.session.commit()
                if User.query.filter(User.username == POST_USER, User.password == POST_PASS):
                    flash("Successfully registered! " + POST_USER + ":" + POST_PASS)
                    session["uid"] = User.query.filter(User.username == POST_USER).first().id
                    return redirect(url_for("index"))
            except Exception as e:
                db.session.rollback()
                eprint(str(e))
                flash("Error adding to database")
        else:
            flash("Error registering new account")
    return Response(render_template("accounts/newAccount.html"), status=200, mimetype='text/html')

@app.route("/registerstaff/", methods=["GET", "POST"])
def signerStaff():
    #if request.method == "GET":
        #flash("Complete form to create new staff account")
    if request.method == "POST":
        POST_USER = str(request.form['user'])
        POST_PASS = str(request.form['pass'])
        POST_EMAIL = str(request.form['mail'])
        if POST_USER != None and POST_PASS != None:
            newUser = User(POST_USER, POST_PASS, POST_EMAIL, True)
            db.session.add(newUser)
            try:
                db.session.commit()
                if User.query.filter(User.username == POST_USER, User.password == POST_PASS):
                    flash("Added account " + POST_USER + ":" + POST_PASS)
                return Response(render_template("accounts/newAccount.html"), status=200, mimetype='text/html')
            except Exception as e:
                db.session.rollback()
                eprint(str(e))
                flash("Error adding user to database. Name Taken.")
        else:
            flash("Error registering new account")
    return Response(render_template("accounts/newAccount.html"), status=200, mimetype='text/html')
        
@app.route("/login/", methods=["GET", "POST"])
def logger():
    if "username" in session:
        flash("Already logged in!")
        return redirect(url_for("index"))
    elif request.method == "POST":
        POST_USER = str(request.form['user'])
        POST_PASS = str(request.form['pass'])
        valid = User.query.filter(User.username == POST_USER, User.password == POST_PASS).first()
        eprint(str(valid))
        if (POST_USER == "owner") and (POST_PASS == "pass"):
            session["uid"] = 1
            flash("Successfully logged in as Mr. Manager")
            return redirect(url_for("owner"))
        elif valid is not None:
            session["uid"] = valid.id
            flash("Successfully logged in!  " + valid.username)
            if valid.staff == True:
                return redirect(url_for("staff", uid=valid.id))
            else:
                return redirect(url_for("customer", uid=valid.id))
            return redirect(url_for("index", uid=valid.id))
        else:
            flash("Error logging you in!")
    return Response(render_template("accounts/loginPage.html"), status=200, mimetype='text/html')

@app.route("/owner/")
def owner():
    if g.user.id != 1:
        return redirect(url_for("index"))
    elif g.user.id == 1:
        if Event.query.count() < 1: 
            flash("no events scheduled")
        else:
            next = Event.query.order_by(Event.date.asc()).first()  # filter by now to avoid dates in past
            days = str((next.date - datetime.now()).days)
            flash("next event: " + str(next.eventname))
            flash("in " + days + " days")
        return Response(render_template("types/owner.html", user=g.user, events=g.events), status=200, mimetype='text/html')
    else:
        abort(404)
        
@app.route("/staff/<int:uid>")
def staff(uid=None):
    if not g.user:
        flash("Must login first")
        return redirect(url_for("index"))
    if not uid:
        flash("Not authorized")
        return redirect(url_for("index"))
    elif g.user.staff == True and g.user.id == int(uid):
        uid = int(uid)
        events = [g for g in g.events if g.staff1==uid or g.staff2==uid or g.staff3 == uid]
        openEvents = Event.query.filter(or_(Event.staff1==None, Event.staff2==None, Event.staff3==None)).order_by(Event.date.asc()).all()
        openEvents = [o for o in openEvents if o.staff1!=uid and o.staff2!=uid and o.staff3!=uid]
        eprint(str(openEvents)) 
        return Response(render_template("types/staff.html", user=g.user, events=events, openevents=openEvents), status=200, mimetype='text/html')
    else:
        abort(404)
        
        
@app.route("/customer/")
def customers(uid=None):
    if not g.user:
        flash("must be logged in")
        return(url_for("index"))
    return Response(render_template("types/customer.html", user=g.user, items=g.events), status=200, mimetype='text/html')


@app.route("/customer/<uid>")
def customer(uid=None):
    if not uid:
        return redirect(url_for("customers"))
    elif (g.user.staff == False) and (int(g.user.id) == int(uid)):
        return redirect(url_for("customers"))
    elif (g.user.id == 1):
        flash("Viewing customer page as owner")
        return redirect(url_for("customers"))
    elif (g.user.staff == True):
        flash("Viewing customer page as staff")
        return redirect(url_for("customers"))
    else:
        abort(404)
        
@app.route("/logout/")
def unlogger():
    if "uid" in session:
        session.clear()
        flash("Successfully logged out!")
        return redirect(url_for("index"))
    else:
        session.clear()
        flash("Not currently logged in!")
        return redirect(url_for("logger"))

@app.route("/events/")
def events():
    if g.user.staff != True:
        flash("Access to events denied.")
        return redirect(url_for("index"))
    elif g.user.staff == True:
        flash("List of all events.")
        return render_template("events/events.html", events=Event.query.order_by(Event.date.asc()).all())
    else:
        abort(404)
        
@app.route("/events/<int:eid>")
def event(eid=None):
    if g.user.staff != True:        
        flash("Access to events denied.")
        return redirect(url_for("index"))
    elif g.user.staff == True:
        eprint("staff")
        eventRS = Event.query.filter(Event.id == int(eid)).first()
        eprint("\n" + str(eventRS) + "\n")
        if eventRS == None:
            flash("Event Id not found")
            return redirect(url_for("events"))
        else:
            staff = (User.query.filter(User.id==eventRS.staff1).first(), User.query.filter(User.id==eventRS.staff2).first(), User.query.filter(User.id==eventRS.staff3).first())
            return render_template("events/event.html", event=eventRS, staff=staff)
    else:
        abort(404)
        

@app.route("/deleteevent/", methods=["GET", "POST"])
def rmevent():
    if g.user.id != 1:
        flash("Access to deleting events denied.")
        return redirect(url_for("index"))
    if request.method == "POST":
        eventId = request.form.get("events", None)
    if eventId != None:
        event = Event.query.filter(Event.id==int(eventId)).first()
        db.session.delete(event)
        try:
            db.session.commit()
            flash("Deleted event: " + str(event.eventname))
        except Exception as e:
            db.session.rollback()
            eprint(str(e))
            flash("Error deleting event " + event.eventname)
        return redirect(url_for("owner"))
    else:
        abort(404)
        
@app.route("/cancelevent/", methods=["POST"])
def rmeventCust():
    if request.method == "POST":
        eventId = int(request.form.get("cancel", None))
    else:
        flash("Must use POST to delete event")
        return redirect(url_for("customers"))
    if (eventId != None):
        event = Event.query.filter(Event.id==int(eventId)).first()
        if event.client == g.user.id:
            db.session.delete(event)
            try:
                db.session.commit()
                flash("Deleted event: " + str(event.eventname))
            except Exception as e:
                db.session.rollback()
                eprint(str(e))
                flash("Error deleting event" + event.eventname)
            return redirect(url_for("customers"))
    else:
        abort(404)
        
@app.route("/eventsignup/<int:eid>", methods=["GET", "POST"])
def eventsign(eid=None):
    if not g.user:
        flash("Must login first")
        return redirect(url_for("index"))
    if g.user.staff != True:
        flash("Access to events denied.")
        return redirect(url_for("index"))
    if eid == None:
        flash("Event ID not provided")
        return redirect(url_for("staff", uid=g.user.id))
    if g.user.staff == True:
        id = g.user.id
        eventRS = Event.query.filter(Event.id == int(eid)).first()
        if eventRS == None:
            flash("Event not found")
            return redirect(url_for("staff", uid=g.user.id))
        elif eventRS.staff1==id or eventRS.staff2==id or eventRS.staff3==id:
            flash("Already registered for this event")
            return redirect(url_for("staff", uid=g.user.id))
        else:
            if eventRS.staff1==None:
                eventRS.staff1 = g.user.id
            elif eventRS.staff2==None:
                eventRS.staff1 = g.user.id
            elif eventRS.staff3==None:
                eventRS.staff1 = g.user.id
            else:
                flash("Event is already fully staffed")
            try:
                db.session.commit()
                flash("Registered for " + str(eventRS.eventname))
                return redirect(url_for("staff", uid=g.user.id))
            except Exception as e:
                db.session.rollback()
                eprint(str(e))
                flash("Error registering for " + str(eventRS.eventname))
                return redirect(url_for("eventsign", eid=eid))
            return redirect(url_for("index"))
    else:
        abort(404)
        
@app.route("/newevent/", methods=["GET", "POST"])
def newEvent():
    if g.user and request.method == "GET":
        now = datetime.utcnow().date()+timedelta(days=1)
        return render_template("events/newEvent.html", now=now, later=now+timedelta(days=366))
    elif g.user==None: 
        flash("Not logged in")
        return redirect(url_for("index"))
    elif request.method == "POST":
        POST_EVENT = remove_tags(str(request.form['ename']))
        POST_DATE = parser.parse(request.form['edate'])
        if Event.DateBooked(POST_DATE):
            flash("Date already booked")
            return redirect(url_for("newEvent"))
        elif POST_EVENT != None and POST_DATE != None:
            newEvent = Event(eventname=POST_EVENT, email=g.user.email, created=None, client=g.user.id, date=POST_DATE)
            db.session.add(newEvent)
            try:
                db.session.commit()
                flash("Successfully added event: " + POST_EVENT)
            except Exception as e:
                db.session.rollback()
                eprint(str(e))
                flash("Error adding event to database")
                return redirect(url_for("newEvent"))
            if g.user.id == 1:
                return redirect(url_for("owner"))
            else:
                return redirect(url_for("customers"))
        else:
            flash("Error adding event. Field left blank")
            return redirect(url_for("newEvent"))
    else:
        abort(404)

@app.route("/db/")
def rawstats():
    msg = ""
    msg += User.Everything()
    msg += "\n\n"
    msg += Event.Everything()
    return Response(render_template('test.html', testMessage=msg), status=203, mimetype='text/html')

@app.route('/')
def index():
    return Response(render_template('base.html'), status=203, mimetype='text/html')

@app.errorhandler(403)
@app.errorhandler(404)
def page_not_found(error):
    return Response(render_template('404.html', errno=error), status=404, mimetype='text/html')

@app.errorhandler(405)
def wrong_method(error):
    return Response("You shouldn't have done that", status=405, mimetype='text/html')

@app.route('/418/')
def err418(error=None):
    return Response(render_template('404.html', errno=error), status=418, mimetype='text/html')

@app.route('/favicon.ico') 
def favicon():
    if bool(getrandbits(1))==True:
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    else:
        return send_from_directory(os.path.join(app.root_path, 'static'), 'faviconF.ico', mimetype='image/vnd.microsoft.icon')

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)
    
TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)
    
if __name__ == "__main__":
    print('Starting......')
    if FDEBUG==True:
        app.config.update(dict(
            DEBUG=True,
            DEBUG_TB_INTERCEPT_REDIRECTS=False,
            SQLALCHEMY_TRACK_MODIFICATIONS=True,
            TEMPLATES_AUTO_RELOAD=True,
        ))
        app.jinja_env.auto_reload = True
        toolbar = DebugToolbarExtension(app) 
        app.run(use_reloader=True, host='0.0.0.0')
    else:
        app.run()
