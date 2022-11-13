# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
from shared import db


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
