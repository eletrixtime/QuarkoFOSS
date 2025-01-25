'''
QuarkoFOSS - Main

This is the original Quarko code
Under the MIT license a copy is available in the LICENSE file

(some code is changed for privacy reasons.. (tokens etc))
'''


from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy import or_
import traceback
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///data/data.db', echo=False)
Base = declarative_base()
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    bio = Column(String,default="Hi :D")
    certified = Column(String,default=False)
    staff = Column(String,default=False)
    premium = Column(String,default=False)
    ban = Column(String,default=False)
    ban_raison = Column(String,default="Banned by a operator !")
    token = Column(String)
    join_date = Column(Integer)
    ip = Column(String)
    profile_url = Column(String)
    show_username = Column(String)
    devmode = Column(String,default=False)
    followers = Column(Integer,default=0)
    who_followed = Column(String,default='{"who_followed":[]}')
    data = Column(String,default='')
    background_url = Column(String,default='null')
class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True,unique=True)
    author = Column(String, unique=False)    
    views = Column(Integer)
    likes = Column(Integer,default=0)
    text = Column(String)
    title = Column(String)
    attachements = Column(String)
    who_liked = Column(String,default='{"who_liked":[]}')
class Stats(Base):
    __tablename__ = 'qstats'
    txt = Column(String,primary_key=True)
    total_users = Column(Integer)
    total_post = Column(Integer)
class ChatDB(Base):
    __tablename__ = 'chat'
    msg_id = Column(Integer,primary_key=True)
    username = Column(String)
    author_id = Column(Integer)
    message = Column(String)
    room = Column(String,default="com")
    timestamp = Column(Integer)
    post_id = Column(String,default="null")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
sessiondb = Session()