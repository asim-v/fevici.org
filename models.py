from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime, timedelta
from random import randrange

db = SQLAlchemy()

staffers = db.Table('staffers',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(64), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=False, nullable=True)
    staff = db.Column(db.Boolean, default=False)
    
    def __init__(self, username, password, email, staff=None):
        self.username = username
        self.password = password
        self.email = email
        self.staff = False if staff == None else True

    def __repr__(self):
        return "<User {} {} {}>".format(repr(self.id), repr(self.username), repr(self.staff))
    
    def Everything():
        txt = "\t" + str(User.__table__) + "\n"
        cols = User.__table__.columns.keys()
        txt += (str(cols) + "\n")
        resultSet = User.query.order_by(User.id.asc()).all()
        for item in resultSet:
            txt += ' '.join([str(getattr(item, col)) for col in cols]) +  "\n"
        return txt
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    eventname = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    client = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    staff1 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    staff2 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    staff3 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    staffers = db.relationship('User', secondary=staffers, lazy='subquery', backref=db.backref('users', lazy=True))
#     clientID = db.relationship('User', backref=db.backref('events', lazy=True))
    
    def __init__(self, eventname, email, date, created, client, staff1=None, staff2=None, staff3=None):
        self.eventname = eventname
        self.email = None if email == None else email
        self.date = date
        self.client = 1 if client == None else client 
        self.created = datetime.utcnow() if created == None else created 
        self.staff1 = None if staff1 == None else staff1 
        self.staff2 = None if staff2 == None else staff2
        self.staff3 = None if staff3 == None else staff3

    def __repr__(self):
        return "<Event {}>".format(repr(self.eventname))
    
    def Everything():
        txt = "\t" + str(Event.__table__) + "\n"
        cols = Event.__table__.columns.keys()
        txt += (str(cols) + "\n")
        resultSet = Event.query.order_by(Event.id.asc()).all()
        for item in resultSet:
            txt += ' '.join([str(getattr(item, col)) for col in cols]) +  "\n"
        return txt
    
    def DateBooked(newEvent):
        rs = Event.query.order_by(Event.date.asc())
        for item in rs:
            if item.date.date() == newEvent.date():
                return True
        return False
 
 

def populateDB():
    db.session.add(User(username="owner", password="pass", email="owner@catering.py", staff=True))
    db.session.add(User(username="customer", password="pass", email="customer@catering.py", staff=None))
    db.session.add(User(username="staff", password="pass", email="staff@catering.py", staff=True))
    db.session.add(User(username="admin", password="admin", email="admin@example.com", staff=None))
    db.session.add(User(username="staff1", password="pass", email="staff1@catering.py", staff=True))
    db.session.add(User(username="staff2", password="pass", email="staff2@catering.py", staff=True))
    db.session.add(User(username="staff3", password="pass", email="staff3@catering.py", staff=True))
    db.session.add(User(username="staff4", password="pass", email="staff4@catering.py", staff=True))
    db.session.add(User(username="staff5", password="pass", email="staff5@catering.py", staff=True))
    db.session.add(User(username="customer1", password="pass", email="customer1@catering.py", staff=None))
    db.session.add(User(username="customer2", password="pass", email="customer2@catering.py", staff=None))
    db.session.add(User(username="customer3", password="pass", email="customer3@catering.py", staff=None))
    db.session.add(User(username="customer4", password="pass", email="customer4@catering.py", staff=None))
    db.session.add(User(username="customer5", password="pass", email="customer5@catering.py", staff=None))
    db.session.add(User(username="customer6", password="pass", email="customer6@catering.py", staff=None))
    db.session.add(Event(eventname="🎉Grand Opening🍾", email="test@email", client=1, staff1=5, staff2=6, staff3=7, date=datetime.utcnow()+timedelta(days=2), created=None))
    db.session.add(Event(eventname="🎆Grand Closing🎆", email="test2@email", client=1, staff1=5, date=datetime.utcnow()+timedelta(days=420), created=datetime.utcnow()-timedelta(days=420)))
    db.session.add(Event(eventname="🕶️Test Party🕶️", email="test2@email", client=4, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🍸Cocktail Party🍸", email="test2@email", client=10, staff1=8, staff2=9, staff3=7, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🎊Confetti Event🎊", email="test2@email", client=11, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🥂Champagne Testing🥂", email="test2@email", staff1=7, staff2=5, staff3=6, client=12, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🎂 Birthday Party 🎂", email="test2@email", staff3=9, client=13, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🎁 Birthday Party 🎁", email="test2@email", client=13, date=datetime.utcnow()+timedelta(days=randrange(100)), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.add(Event(eventname="🎃Halloween Party🎃", email="test2@email", client=14, date=datetime(2018, 10, 31, 20, 0), created=datetime.utcnow()-timedelta(days=randrange(100))))
    db.session.commit()
    print('DB Populated...') 
    return True

print('Model loaded...')
