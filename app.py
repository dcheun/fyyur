# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import Form
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    genres = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True, order_by='Show.start_time',
                            cascade='all, delete, delete-orphan')
    
    def __repr__(self):
        return f'Venue(id={self.id},name={self.name})'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True, order_by='Show.start_time',
                            cascade='all, delete, delete-orphan')
    
    def __repr__(self):
        return f'Artist(id={self.id},name={self.name})'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(50), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'Show(id={self.id},venue_id={self.venue_id},artist_id={self.artist_id},start_time={self.start_time})'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


def get_past_upcoming_shows(all_shows: list) -> tuple:
    """Split a list of shows into past and upcoming.
    
    Returns a tuple in the form ([past_shows,...], [upcoming_shows,...])
    
    """
    # Find the split between past and upcoming shows.
    # Shows is ordered by start_time based on query configuration in model.
    idx_split = 0
    curr_dt = datetime.now()
    for show in all_shows:
        if dateutil.parser.parse(show.start_time) > curr_dt:
            break
        idx_split += 1
    past = all_shows[:idx_split]
    upcoming = all_shows[idx_split:]
    return past, upcoming


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
    # NOTE: num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    _data = {}
    venues_list = Venue.query.all()
    for venue in venues_list:
        venue_data = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(venue.shows)
        }
        if venue.state in _data:
            if venue.city in _data[venue.state]:
                _data[venue.state][venue.city].append(venue_data)
            else:
                _data[venue.state].update({
                    venue.city: [venue_data]
                })
        else:
            _data.update({
                venue.state: {
                    venue.city: [venue_data]
                }
            })

    # Convert it to a list with supported format for frontend.
    data = [{'state': k, 'city': k2, 'venues': v2} for k, v in _data.items() for k2, v2 in v.items()]
    data = sorted(data, key=lambda x: (x['state'], x['city']))

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        'count': 0,
        'data': []
    }
    search_term = request.form.get('search_term', '')
    matches = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).order_by('name').all()
    if matches:
        # Find upcoming shows.
        for venue in matches:
            _, upcoming = get_past_upcoming_shows(venue.shows)
            response['count'] += 1
            response['data'].append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming)
            })
    
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    past_shows, upcoming_shows = get_past_upcoming_shows(venue.shows)
    past_shows = [
        {
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time
        }
        for show in past_shows
    ]
    upcoming_shows = [
        {
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time
        }
        for show in upcoming_shows
    ]
    data = {
        'id': venue.id,
        'name': venue.name,
        # This comes as a comma separated string from the db.
        # Convert it to an array for the front end.
        'genres': venue.genres.split(','),
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'image_link': venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    if venue.seeking_talent:
        data.update({
            'seeking_description': venue.seeking_description
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
    try:
        venue = Venue(
            name=request.form['name'],
            address=request.form['address'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            # request.form['genres'] only return a single value from the multiselect.
            genres=','.join(request.form.getlist('genres')),
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website_link=request.form['website_link'],
            # seeking_talent is not present if request.form is not selected from UI.
            seeking_talent=True if request.form.get('seeking_talent', False) == 'y' else False,
            seeking_description=request.form['seeking_description'],
        )
        db.session.add(venue)
        db.session.commit()
        flash(f'Venue {venue.name} was successfully listed!', 'success')
    except Exception:
        db.session.rollback()
        flash(f'An error occurred. Venue {request.form.get("name", "UNKNOWN")} could not be listed.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue_submission(venue_id):
    error = False
    data = {}
    try:
        venue = Venue.query.get(venue_id)
        data['name'] = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {data.get("name", venue_id)} successfully deleted.', 'success')
    except Exception:
        db.session.rollback()
        error = True
        flash(f'An error occurred. Venue {data.get("name", venue_id)} could not be deleted.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    # JavaScript in front end will redirect to homepage if delete was successful.
    if error:
        return jsonify({'success': False})
    else:
        return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # Note: data passed to frontend should follow this format.
    # data = [{
    #     "id": 4,
    #     "name": "Guns N Petals",
    # },...]
    data = [{'id': x.id, 'name': x.name} for x in Artist.query.order_by('id').all()]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        'count': 0,
        'data': []
    }
    search_term = request.form.get('search_term', '')
    matches = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).order_by('name').all()
    if matches:
        # Find upcoming shows.
        for artist in matches:
            _, upcoming = get_past_upcoming_shows(artist.shows)
            response['count'] += 1
            response['data'].append({
                'id': artist.id,
                'name': artist.name,
                'num_upcoming_shows': len(upcoming)
            })

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    past_shows, upcoming_shows = get_past_upcoming_shows(artist.shows)
    past_shows = [
        {
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time
        }
        for show in past_shows
    ]
    upcoming_shows = [
        {
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time
        }
        for show in upcoming_shows
    ]
    data = {
        'id': artist.id,
        'name': artist.name,
        # genres comes as a comma separated field from the db.
        # Convert it to an array for the front end.
        'genres': artist.genres.split(','),
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'seeking_venue': artist.seeking_venue,
        'image_link': artist.image_link,
        'facebook_link': artist.facebook_link,
        'website': artist.website_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    if artist.seeking_venue:
        data.update({
            'seeking_description': artist.seeking_description
        })

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    # Multi-select field need to be manually set, doesn't seem to get set otherwise.
    form.genres.data = artist.genres.split(',')
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        # genres is a multi-select field, need to call getlist to get all the selected values.
        artist.genres = ','.join(request.form.getlist('genres'))
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.website_link = request.form['website_link']
        # seeking_venue is not present if request.form if not selected from UI.
        artist.seeking_venue = True if request.form.get('seeking_venue', False) == 'y' else False
        artist.seeking_description = request.form['seeking_description']
        db.session.commit()
        flash(f'Artist {artist.name} was successfully updated!', 'success')
    except Exception:
        db.session.rollback()
        flash(f'An error occurred. Artist {request.form.get("name", artist_id)} could not be updated.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    # Multi-select field need to be manually set, doesn't seem to get set otherwise.
    form.genres.data = venue.genres.split(',')
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.address = request.form['address']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        # genres is a multi-select, need to call getlist to get all selected values.
        venue.genres = ','.join(request.form.getlist('genres'))
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        # seeking_talent is not present if request.form is not selected from UI.
        venue.seeking_talent = True if request.form.get('seeking_talent', False) == 'y' else False
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()
        flash(f'Venue {venue.name} was successfully updated!', 'success')
    except Exception:
        db.session.rollback()
        flash(f'An error occurred. Venue {request.form.get("name", venue_id)} could not be updated.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            # request.form['genres'] only return a single value from the multiselect.
            genres=','.join(request.form.getlist('genres')),
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website_link=request.form['website_link'],
            # seeking_venue is not present if request.form if not selected from UI.
            seeking_venue=True if request.form.get('seeking_venue', False) == 'y' else False,
            seeking_description=request.form['seeking_description'],
        )
        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {artist.name} was successfully listed!', 'success')
    except Exception:
        db.session.rollback()
        flash(f'An error occurred. Artist {request.form.get("name", "UNKNOWN")} could not be listed.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows_list = Show.query.order_by('start_time').all()
    data = [{'start_time': x.start_time,
             'venue_id': x.venue.id,
             'venue_name': x.venue.name,
             'artist_id': x.artist.id,
             'artist_name': x.artist.name,
             'artist_image_link': x.artist.image_link,
             } for x in shows_list]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        show = Show(
            start_time=request.form['start_time'],
            venue_id=request.form['venue_id'],
            artist_id=request.form['artist_id']
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.', 'danger')
        print(sys.exc_info())
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


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
