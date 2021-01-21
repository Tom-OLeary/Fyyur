"""
Tom O'Leary
Fyyur app.py - Runs app and handles data modeling
Python 3.7
"""

# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
import logging
from sqlalchemy.exc import SQLAlchemyError
from models import Artist, Venue, Show, setup_db
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from logging import Formatter, FileHandler

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = setup_db(app)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # Displays venues at /venues
    venue_list = Venue.query.group_by(Venue.city, Venue.state, Venue.id).all()
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = []

    for venue in venue_list:
        upcoming_shows = venue.shows.filter(Show.start_time > time).all()

        data.append({
            "city": venue.city,
            "state": venue.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows)
            }]
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # Search on venues with partial string search. Case-insensitive.
    venue_data = Venue.query.filter(Venue.name.ilike('%' + request.form['search_term'] + '%'))
    venue_list = list(map(Venue.title, venue_data))
    data = {
        "count": len(venue_list),
        "data": venue_list
    }

    return render_template('pages/search_venues.html', results=data,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Shows the venue page with the given venue_id
    venue = Venue.query.filter_by(id=venue_id).first_or_404()

    past_shows = db.session.query(Artist, Show).join(Show).join(Venue). \
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time < datetime.now()
    ). \
        all()

    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue). \
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.now()
    ). \
        all()

    data = Venue.detail(venue)

    data.update({
        'past_shows': [Show.artist_detail(show)
                       for artist, show in past_shows],
        'upcoming_shows': [Show.artist_detail(show)
                           for artist, show in upcoming_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    })

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Insert form data as a new Venue record in the db
    form = VenueForm()
    venue = create_new(form)
    add_item(venue)

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Delete a record. Handle cases where the session commit could fail.
    venue_data = Venue.query.get(venue_id)
    Venue.delete(venue_data)
    return None


@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    # Handles delete button
    venue_data = Venue.query.get(item_id)
    Venue.delete(venue_data)
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # Displays artists at /artists
    artist_data = Artist.query.all()

    artist_list = [{"id": art.id, "name": art.name} for art in artist_data]

    return render_template('pages/artists.html', artists=artist_list)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Search on artists with partial string search. Case-insensitive
    artist_data = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%'))
    artist_list = list(map(Artist.title, artist_data))
    data = {
        "count": len(artist_list),
        "data": artist_list
    }

    return render_template('pages/search_artists.html', results=data,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Shows the artist page with the given artist_id
    artist = Artist.query.filter_by(id=artist_id).first_or_404()

    past_shows = db.session.query(Venue, Show).join(Show).join(Artist). \
        filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time < datetime.now()
    ). \
        all()

    upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist). \
        filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time > datetime.now()
    ). \
        all()

    data = Artist.detail(artist)

    data.update({
        'past_shows': [Show.venue_detail(show)
                       for venue, show in past_shows],
        'upcoming_shows': [Show.venue_detail(show)
                           for venue, show in upcoming_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    })

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # Populate form with fields from artist with ID <artist_id>
    form = ArtistForm()
    artist_data = Artist.query.get(artist_id)

    artist_items = Artist.detail(artist_data)
    keys = ["name", "genres", "city", "state", "phone", "website", "facebook_link",
            "seeking_venue", "seeking_description", "image_link"]

    for key in keys:
        getattr(form, key).data = artist_items[key]

    return render_template('forms/edit_artist.html', form=form, artist=artist_items)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # Update existing artist record with ID <artist_id> using the new attributes
    try:
        form_items = request.form
        artist_data = Artist.query.get(artist_id)

        keys = ["name", "genres", "city", "state", "phone", "website", "facebook_link",
                "seeking_description", "image_link"]

        [setattr(artist_data, key, form_items[key]) for key in keys]

        seeking_venue = request.form.get('seeking_venue')

        if seeking_venue == 'y':
            artist_data.seeking_venue = True
        else:
            artist_data.seeking_venue = False

        db.session.commit()
    except SQLAlchemyError as e:
        print(e)
        flash('Error! Form could not be updated')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # Populate form with fields from venue with ID <venue_id>
    form = VenueForm()
    venue_data = Venue.query.get(venue_id)

    venue_items = Venue.detail(venue_data)
    keys = ["name", "city", "state", "address", "phone", "image_link", "facebook_link",
            "genres", "website", "seeking_talent", "seeking_description"]

    for key in keys:
        getattr(form, key).data = venue_items[key]

    return render_template('forms/edit_venue.html', form=form, venue=venue_items)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # Update existing venue record with ID <venue_id> using the new attributes
    try:
        form_items = request.form
        venue_data = Venue.query.get(venue_id)

        keys = ["name", "city", "state", "address", "phone", "image_link", "facebook_link",
                "genres", "website", "seeking_description"]

        [setattr(venue_data, key, form_items[key]) for key in keys]

        seeking_talent = request.form.get('seeking_talent')

        if seeking_talent == 'y':
            venue_data.seeking_talent = True
        else:
            venue_data.seeking_talent = False

        db.session.commit()
    except SQLAlchemyError as e:
        print(e)
        flash('Error! Form could not be updated')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Called upon submitting the new artist listing form
    form = ArtistForm()
    artist = create_new(form)
    add_item(artist)

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # Displays list of shows at /shows
    shows_data = Show.query.all()

    show_list = [Show.detail(show) for show in shows_data]

    return render_template('pages/shows.html', shows=show_list)


@app.route('/shows/create')
def create_shows():
    # Renders form
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # Called to create new shows in the db, upon submitting new show listing form
    try:
        show = Show(
            venue_id=request.form['venue_id'],
            artist_id=request.form['artist_id'],
            start_time=request.form['start_time']
        )
        db.session.add(show)
        db.session.commit()

        # On successful db insert, flash success
        flash('Show was successfully listed!')
    except SQLAlchemyError as e:
        print(e)
        flash('An error occurred. Show could not be listed.')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


def create_new(form):
    """Populate new Artist/Venue form

    Parameters
    ----------
    form : ArtistForm or VenueForm Object
        data found within an Artist or Venue Form

    Returns
    -------
    artist : Artist
        returns Artist data if form == ArtistForm
    venue : Venue
        returns Venue data if form == VenueForm
    """

    keys = ["name", "city", "state", "phone", "genres", "image_link", "facebook_link", "website",
            "seeking_description"]

    results = [getattr(form, key).data for key in keys]

    if isinstance(form, ArtistForm):
        # Get appropriate form
        seeking_venue = form.seeking_venue.data
        artist = Artist(*results, seeking_venue)

        return artist
    else:
        seeking_talent = form.seeking_talent.data
        address = form.address.data

        venue = Venue(*results, address, seeking_talent)

        return venue


def add_item(obj):
    """Add item to database

    Parameters
    ----------
    obj : Artist or Venue Object
        data from an Artist or Venue Object

    Raises
    -------
    Exception :
        raises error if item failed to add to the database
    """

    try:
        db.session.add(obj)
        db.session.commit()

        # on successful db insert, flash success
        flash(request.form['name'] + ' was successfully listed!')
    except Exception as e:
        db.session.rollback()
        db.session.flush()
        flash('An error occurred. ' + obj.name + ' could not be listed.')
        print(e)


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
