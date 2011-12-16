from flask import Flask,  redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from flaskext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Address(db.Model):
    __tablename__ = 'address'

    shortname = db.Column(db.Unicode(100), primary_key=True, unique=True,
                          index=True)

    name = db.Column(db.UnicodeText)
    street = db.Column(db.UnicodeText)
    zipcode = db.Column(db.Integer)
    city = db.Column(db.UnicodeText)
    country = db.Column(db.UnicodeText)

    # backref
    location = db.relationship('Location', backref='address')

    def __repr__(self):
        return self.shortname


class Location(db.Model):
    __tablename__ = 'location'

    address_shortname = db.Column(db.Unicode(100),
                                  db.ForeignKey('address.shortname'),
                                  primary_key=True)
    room = db.Column(db.Unicode(100), primary_key=True)
    position = db.Column(db.Unicode(100), primary_key=True)

    db.PrimaryKeyConstraint('address_shortname', 'room', 'position',
                            name='location_key')

    asset = db.relationship(
        'Asset', backref='location',
        lazy='select',
        primaryjoin='(Location.room==Asset.location_room) &'\
            '(Location.address_shortname==Asset.address_shortname) &'\
            '(Location.position==Asset.location_position)')

    # additional fields in real world example

    def __repr__(self):
        return u"%s|%s|%s" % (self.address_shortname, self.room,
                              self.position)


class Asset(db.Model):
    __tablename__ = 'asset'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.UnicodeText)

    # 1*n relation to location-table
    address_shortname = db.Column(db.Unicode(100))
    location_room = db.Column(db.Unicode(100))
    location_position = db.Column(db.Unicode(100))

    __table_args__ = (
        db.ForeignKeyConstraint(['address_shortname', 'location_room',
                                 'location_position'],
                                ['location.address_shortname',
                                 'location.room',
                                 'location.position'],
                                use_alter=True,
                                name='fk_location_asset'),)

    def __repr__(self):
        return self.name


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SECRET_KEY'] = 'not secure'
    db.init_app(app)
    datastore = SQLAlchemyDatastore(
        (Address, Location, Asset), db.session, exclude_pks=False)
    admin_blueprint = admin.create_admin_blueprint(datastore)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    db.create_all(app=app)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')
    return app


if __name__ == '__main__':
    app = create_app('sqlite:///multi_pks.db')
    app.run(debug=True)
