from flask import flash
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ARRAY, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()


def setup_db(app):
    # Connect to postgresql
    app.config.from_object('config')
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    return db
# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    """Holds data for Venues"""
    __tablename__ = 'venue'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String(120))
    state = Column(String(120))
    phone = Column(String(120))
    image_link = Column(String(500))
    facebook_link = Column(String(120))
    genres = Column(ARRAY(String))
    website = Column(String(120))
    seeking_talent = Column(Boolean, default=False)
    seeking_description = Column(String(120))
    address = Column(String(120))

    shows = db.relationship('Show', backref='venue', lazy='dynamic')

    def __init__(self, name, city, state, phone, image_link,
                 facebook_link, genres, website, seeking_description="",
                 address=address, seeking_talent=False):
        """__init__ for Venue Class

        Values stored represent the attributes of a Venue

        Parameters
        ----------
        name : String
            name of venue
        city : String
            name of city
        state : String
            name of state
        address : String
            address of venue
        phone : String
            phone number of venue
        image_link : String
            image link for venue
        facebook_link : String
            facebook link for venue
        genres : list (String)
            list of genres for venue
        website : String
            website link for venue
        seeking_talent : Boolean
            seeking talent (yes/no)
        seeking_description : String
            venue description
        """

        self.name = name
        self.city = city
        self.state = state
        self.phone = phone
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.genres = genres
        self.website = website
        self.seeking_description = seeking_description
        self.address = address
        self.seeking_talent = seeking_talent

    def delete(self):
        """Deletes Venue item from database

        Raises
        ------
        SQLAlchemyError :
            raises error on failed delete attempt
        """

        try:
            db.session.delete(self)
            db.session.commit()
            flash(self.name + ' was successfully deleted!')
        except SQLAlchemyError as e:
            flash('Error! Venue could not be deleted')
            db.session.rollback()
        finally:
            db.session.close()

    def title(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def detail(self):
        return {
            'id': self.id,
            'name': self.name,
            'genres': self.genres,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'website': self.website,
            'facebook_link': self.facebook_link,
            'seeking_talent': self.seeking_talent,
            'seeking_description': self.seeking_description,
            'image_link': self.image_link
        }


class Artist(db.Model):
    """Holds data for Artist"""

    __tablename__ = 'artist'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String(120))
    state = Column(String(120))
    phone = Column(String(120))
    genres = Column(ARRAY(String))
    image_link = Column(String(500))
    facebook_link = Column(String(120))
    website = Column(String(120))
    seeking_venue = Column(Boolean, default=False)
    seeking_description = Column(String(120))

    shows = db.relationship('Show', backref='artist', lazy=True)

    def __init__(self, name, city, state, phone, genres, image_link, facebook_link, website,
                 seeking_description="", seeking_venue=False):
        """__init__ for Artist Class

        Values stored represent the attributes of an Artist

        Parameters
        ----------
        name : String
            name of venue
        city : String
            name of city
        state : String
            name of state
        phone : String
            phone number of venue
        genres : list (String)
            list of genres for venue
        image_link : String
            image link for venue
        facebook_link : String
            facebook link for venue
        website : String
            website link for venue
        seeking_venue : Boolean
            seeking venue (yes/no)
        seeking_description : String
            venue description
        """

        self.name = name
        self.city = city
        self.state = state
        self.phone = phone
        self.genres = genres
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.website = website
        self.seeking_description = seeking_description
        self.seeking_venue = seeking_venue

    def title(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def detail(self):
        return {
            'id': self.id,
            'name': self.name,
            'genres': self.genres,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'website': self.website,
            'facebook_link': self.facebook_link,
            'seeking_venue': self.seeking_venue,
            'seeking_description': self.seeking_description,
            'image_link': self.image_link
        }


class Show(db.Model):
    """Holds data for Show"""

    __tablename__ = 'show'

    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey('artist.id'))
    venue_id = Column(Integer, ForeignKey('venue.id'))
    start_time = Column(DateTime, nullable=False)

    def __init__(self, artist_id, venue_id, start_time):
        """__init__ for Show

        Parameters
        ----------
        artist_id : int
            holds corresponding Artist.id value
        venue_id : int
            holds corresponding Venue.id value
        start_time : DateTime value
            holds a show's start time, format yyyy-MM-ddTHH:mm:ss
        """

        self.artist_id = artist_id
        self.venue_id = venue_id
        self.start_time = start_time

    def detail(self):
        return {
            'venue_id': self.venue_id,
            'venue_name': self.venue.name,
            'artist_id': self.artist_id,
            'artist_name': self.artist.name,
            'artist_image_link': self.artist.image_link,
            'start_time': str(self.start_time)
        }

    def artist_detail(self):
        return {
            'artist_id': self.artist_id,
            'artist_name': self.artist.name,
            'artist_image_link': self.artist.image_link,
            'start_time': self.start_time.strftime("%m/%d/%Y, %H:%M")
        }

    def venue_detail(self):
        return {
            'venue_id': self.venue_id,
            'venue_name': self.venue.name,
            'venue_image_link': self.venue.image_link,
            'start_time': self.start_time.strftime("%m/%d/%Y, %H:%M")
        }

