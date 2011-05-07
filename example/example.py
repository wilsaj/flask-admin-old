import datetime
import hashlib
import sys
import platform

from flask import Flask, g, session
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.themes import setup_themes
from flaskext.admin import Admin, _query_factory_for, AdminConverter

from wtforms.fields import FileField, FloatField, PasswordField, SelectField, TextField
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.ext.sqlalchemy.fields import QuerySelectField, \
     QuerySelectMultipleField
from wtforms import validators
from wtforms.form import Form

from geoalchemy import GeometryColumn, GeometryDDL, Point, WKTSpatialElement
from pysqlite2 import dbapi2 as sqlite
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Table
from sqlalchemy.schema import UniqueConstraint,ForeignKey
from sqlalchemy import Column, Boolean, Integer, Text, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy.orm import relationship, backref, synonym
from werkzeug import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///example.db'
app.config['SECRET_KEY'] = 'not secure'
SECRET_KEY = app.config['SECRET_KEY']

if "ARCH" in platform.uname()[2]:
    app.config['LIBSPATIALITE_LOCATION'] = "select load_extension('/usr/lib/libspatialite.so.1')"
else:
    app.config['LIBSPATIALITE_LOCATION'] = "select load_extension('/usr/lib/libspatialite.so.2')"


if app.config['SQLALCHEMY_DATABASE_URI']:
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True, module=sqlite, echo=True)
    connection = engine.raw_connection().connection
    connection.enable_load_extension(True)
    engine.execute(app.config['LIBSPATIALITE_LOCATION'])

else:
    engine = create_engine(app.config['WHATEVER_DATABASE_URI'], convert_unicode=True)


db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


Base = declarative_base()
Base.query = db_session.query_property()


@app.before_request
def spatialite_kludge():
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        from database import engine
        connection = engine.raw_connection().connection
        connection.enable_load_extension(True)
        engine.execute(app.config['LIBSPATIALITE_LOCATION'])






# ----------------------------------------------------------------------
# Association tables
# ----------------------------------------------------------------------
agency_project_association_table = Table('agency_project_association',
                                         Base.metadata,
                                         Column('agency_id', Integer, ForeignKey('agency.id')),
                                         Column('project_id', Integer, ForeignKey('project.id')))

agency_site_association_table = Table('agency_site_association',
                                         Base.metadata,
                                         Column('agency_id', Integer, ForeignKey('agency.id')),
                                         Column('site_id', Integer, ForeignKey('site.id')))

project_site_association_table = Table('project_site_association',
                                       Base.metadata,
                                       Column('project_id', Integer, ForeignKey('project.id')),
                                       Column('site_id', Integer, ForeignKey('site.id')))




# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class Agency(Base):
    __tablename__ = 'agency'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)

    users = relationship('User', backref='affiliated_agency')
    projects = relationship('Project',
                            secondary=agency_project_association_table,
                            backref='agencies')
    sites = relationship('Site',
                         secondary=agency_site_association_table,
                         backref='agencies')

    def __init__(self, name=""):
        self.name = name

    def __repr__(self):
        return self.name

    __mapper_args__ = {
        'order_by': name
        }



class Bay(Base):
    __tablename__ = 'bay'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    estuary_id = Column(Integer, ForeignKey('estuary.id'), nullable=False)

    # populated by backref:
    #   estuary = Estuary

    def __repr__(self):
        return self.name

    __mapper_args__ = {
        'order_by': name
        }



class Estuary(Base):
    __tablename__ = 'estuary'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)

    bays = relationship('Bay', backref='estuary')

    def __repr__(self):
        return self.name

    __mapper_args__ = {
        'order_by': name
        }



class File(Base):
    __tablename__ = 'file'

    id = Column(Integer, primary_key=True)
    file_names = Column(String(256))
    file_type_id = Column(Integer, ForeignKey('file_type.id'), nullable=False)
    site_id = Column(Integer, ForeignKey('site.id'))
    instrument_id = Column(Integer, ForeignKey('instrument.id'))
    upload_staff_id = Column(Integer, ForeignKey('user.id'))
    is_primary = Column(Boolean)
    is_qaqc = Column(Boolean)
    date_uploaded = Column(DateTime, default=datetime.datetime.now)
    date_last_updated = Column(DateTime, onupdate=datetime.datetime.now)

    # populated by backref:
    #   file_type = FileType
    #   site = Site
    #   instrument = Instrument


    def __repr__(self):
        return self.file_names

    __mapper_args__ = {
        'order_by': file_names
        }



class FileType(Base):
    __tablename__ = 'file_type'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    file_extension = Column(String(80), nullable=False)

    files = relationship('File', backref='file_type')

    __mapper_args__ = {
        'order_by': name
        }



class FieldTrip(Base):
    __tablename__ = 'field_trip'

    id = Column(Integer, primary_key=True)
    time_start = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'))
    leader_user_id = Column(Integer, ForeignKey('user.id'))
    created_by_user_id = Column(Integer, ForeignKey('user.id'))
    comments = Column(Text)

    __mapper_args__ = {
        'order_by': id
        }



class Instrument(Base):
    __tablename__ = 'instrument'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String(256), nullable=False)
    twdb_inventory_id = Column(String(128))
    instrument_model_id = Column(Integer, ForeignKey('instrument_model.id'))

    calibration_records = relationship('InstrumentCalibrationRecord', backref='instrument')
    repair_records = relationship('InstrumentRepairRecord', backref='instrument')
    files = relationship('File', backref='instrument')

    # populated by backref:
    #   instrument_model = InstrumentModel

    def __repr__(self):
        return "%s %s (%s)" % (self.instrument_model.instrument_manufacturer.instrument_manufacturer_name,
                               self.instrument_model.instrument_model_name,
                               self.serial_number)

    __mapper_args__ = {
        'order_by': instrument_model_id
        }



class InstrumentCalibrationRecord(Base):
    __tablename__ = 'instrument_calibration_record'

    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('instrument.id'))
    # we need pre and post... what else?

    # populated by backref:
    #   instrument = Instrument

    __mapper_args__ = {
        'order_by': instrument_id
        }



class InstrumentManufacturer(Base):
    __tablename__ = 'instrument_manufacturer'

    id = Column(Integer, primary_key=True)
    instrument_manufacturer_name = Column(String(256), unique=True, nullable=False)

    models = relationship('InstrumentModel', backref='instrument_manufacturer')

    def __repr__(self):
        return self.instrument_manufacturer_name

    __mapper_args__ = {
        'order_by': instrument_manufacturer_name
        }



class InstrumentModel(Base):
    __tablename__ = 'instrument_model'
    __table_args__ = (
        UniqueConstraint('instrument_model_name', 'instrument_manufacturer_id'),
        {}
        )

    id = Column(Integer, primary_key=True)
    instrument_model_name = Column(String(256), nullable=False)
    instrument_manufacturer_id = Column(Integer, ForeignKey('instrument_manufacturer.id'))

    instruments = relationship('Instrument', backref='instrument_model')

    # populated by backref:
    #   instrument_manufacturer = InstrumentManufacturer

    def __repr__(self):
        return self.instrument_model_name

    __mapper_args__ = {
        'order_by': instrument_model_name
        }



class InstrumentRepairRecord(Base):
    __tablename__ = 'instrument_repair_record'

    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('instrument.id'))
    record_date = Column(DateTime)
    record_entry = Column(Text, nullable=False)

    # populated by backref:
    #   instrument = Instrument

    def __repr__(self):
        return self.instrument_manufacturer_name

    __mapper_args__ = {
        'order_by': instrument_id
        }



class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)

    sites = relationship('Site',
                         secondary=project_site_association_table,
                         backref='projects')

    # populated by backref:
    #   agencies = Agency   (many to many)

    def __repr__(self):
        return self.name

    __mapper_args__ = {
        'order_by': name
        }



# class QAQCedDataValue(Base):
#     """
#     After QA/QC, Data value stored in this table
#     Note: is_spotCheck field is not needed, because all data will be no-spotCheck
#     """
#     __tablename__ = 'qaqced_data_value'

#     id = Column(Integer, primary_key=True)
#     site_id = Column(Integer, ForeignKey('site.id'))
#     parameter_id = Column(Integer, ForeignKey('parameter.id'))
#     file_id = Column(Integer, ForeignKey('file.id'))
#     data_value = Column(Float(precision=15), nullable=False)
#     datetime_utc = Column(DateTime, nullable=False)
#     origin_utc_offset = Column(Integer, default=0, nullable=False)
#     #vector_info = Column(String)



class QAQCRule(Base):
    __tablename__ = 'qaqc_rule'

    id = Column(Integer, primary_key=True)
    rule_type_id = Column(Integer, ForeignKey('qaqc_rule_type.id'))
    rule_parameters = Column(String(256))
    last_modified_by_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    last_modified_by = relationship('User')

    # populated by backref:
    #   rule_type = QAQCRuleType

    __mapper_args__ = {
        'order_by': rule_type_id
        }




class QAQCRuleType(Base):
    __tablename__ = 'qaqc_rule_type'

    id = Column(Integer, primary_key=True)
    rule_name = Column(String(256), unique=True)
    rule_description = Column(Text, nullable=False)
    rules = relationship('QAQCRule', backref='rule_type')

    __mapper_args__ = {
        'order_by': rule_name
        }



class RawDataValue(Base):
    __tablename__ = 'raw_data_value'
    __table_args__ = (
        UniqueConstraint('datetime_utc', 'site_id', 'parameter_id', 'instrument_id', 'vertical_offset'),
        {}
        )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.id'), nullable=False)
    parameter_id = Column(Integer, ForeignKey('parameter.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.id'))
    data_value = Column(Float(precision=15), nullable=False)
    datetime_utc = Column(DateTime)
    origin_utc_offset = Column(Integer)
    vertical_offset = Column(Float(precision=15))
    is_spot_check = Column(Boolean)
    instrument_id = Column(Integer, ForeignKey('instrument.id'))

#    vector_info = Column(String)

    def __init__(self, site_id=None, parameter_id=None, file_id=None, data_value=None, datetime_utc=None, origin_utc_offset=None, vector_info=None, is_spot_check=None):
        self.site_id = site_id
        self.parameter_id = parameter_id
        self.file_id = file_id
        self.data_value = data_value
        self.datetime_utc = datetime_utc
        self.origin_utc_offset = origin_utc_offset
        self.vector_info = vector_info
        self.is_spot_check = is_spot_check

    __mapper_args__ = {
        'order_by': datetime_utc
        }



class Site(Base):
    __tablename__ = 'site'

    id = Column(Integer, primary_key=True)
    site_code = Column(String, unique=True)
    name = Column(String)
    description = Column(Text)
    bay_id = Column(Integer, ForeignKey('bay.id'))
    status_id = Column(Integer, ForeignKey('site_status.id'))
    geom = GeometryColumn(Point(2))

    files = relationship('File', backref='site')

    # populated by backref:
    #   status = SiteStatus
    #   agencies = Agency    (many to many)
    #   projects = Project   (many to many)


    @property
    def latitude(self):
        x, y = self.geom.coords(db_session)
        return y
    @latitude.setter
    def latitude(self, latitude):
        wkt_point = "POINT(%f %f)" % (self.longitude, latitude)
        self.geom = WKTSpatialElement(wkt_point)

    @property
    def longitude(self):
        x, y = self.geom.coords(db_session)
        return x
    @longitude.setter
    def longitude(self, longitude):
        wkt_point = "POINT(%f %f)" % (longitude, self.latitude)
        self.geom = WKTSpatialElement(wkt_point)

    def __init__(self, site_code="", site_name="", latitude=0, longitude=0):
        self.site_code = site_code
        self.name = site_name
        self.geom = WKTSpatialElement("POINT(%f %f)" % (latitude, longitude))

    def __repr__(self):
        return "%s: %s" % (self.site_code, self.name)

    __mapper_args__ = {
        'order_by': site_code
        }

GeometryDDL(Site.__table__)



class SiteEvent(Base):
    __tablename__ = 'site_event'

    id = Column(Integer, primary_key=True)
    comment = Column(Text)
    event_date = Column(DateTime)
    site_id = Column(Integer, ForeignKey('site.id'))

    __mapper_args__ = {
        'order_by': site_id
        }



class SiteStatus(Base):
    __tablename__ = 'site_status'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    description = Column(Text)
    sites = relationship('Site', backref='status')

    def __repr__(self):
        return self.type

    __mapper_args__ = {
        'order_by': type
        }



class Parameter(Base):
    __tablename__ = 'parameter'

    id = Column(Integer, primary_key=True)
    parameter_code = Column(String(10), unique=True)
    parameter_description = Column(String)
    parameter_units = Column(String)

    def __repr__(self):
        return self.parameter_code

    __mapper_args__ = {
        'order_by': parameter_code
        }



class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True)
    role_name = Column(String(256), unique=True)
    role_description = Column(Text)
    users = relationship('User', backref='role')

    def __repr__(self):
        return self.role_name

    __mapper_args__ = {
        'order_by': role_name
        }



class User(Base):
    __tablename__ = 'user'

    priority_list = ["Site Admin",
                     "QAQC Supervisor",
                     "QAQC Staff",
                     "Data Upload Staff"]

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    fullname = Column(String(80), nullable=False)
    _password_hash = Column('password', String(80), nullable=False)
    email = Column(String(80), nullable=False)
    agency_id = Column(Integer, ForeignKey('agency.id'),
                       default=1)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    date_last_login = Column(DateTime)
    date_last_updated = Column(DateTime, onupdate=datetime.datetime.now)
    date_created = Column(DateTime, default=datetime.datetime.now)

    uploaded_files = relationship('File', backref='upload_staff')

    # populated by backref:
    #   affiliated_agency = Agency
    #   role = Role


    #constructor
    def __init__(self, username="", fullname="", email="", password="", priority="", is_superuser=False):
        self.username = username
        self.fullname = fullname
        self.email = email
        self.password = password
        self.priority = priority
        self.is_superuser = is_superuser
        self.date_joined = datetime.datetime.now()


    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    @property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, password):
        self._password_hash = generate_password_hash(password)

    password = synonym('_password_hash', descriptor=password)

    def __repr__(self):
        return "%s (%s)" % (self.fullname, self.username)

    __mapper_args__ = {
        'order_by': fullname
        }


class UserFormBase(Form):
    """
    Form for creating or editting User object (via the admin). Define
    any handling of fields here. This form class also has precedence
    when rendering forms to a webpage, so the model-generated fields
    will come after it.
    """
    username = TextField(u'User name', [validators.required(), validators.length(max=80)])
    fullname = TextField(u'Full name', [validators.required()])
    password = PasswordField('', [validators.optional(), validators.equal_to('confirm_password')])
    confirm_password = PasswordField()
    affiliated_agency = QuerySelectField('Agency',
                                         query_factory=_query_factory_for(Agency),
                                         allow_blank=False,
                                         get_label='name')
    role = QuerySelectField('Role',
                            query_factory=_query_factory_for(Role),
                            allow_blank=False,
                            get_label='role_name')


class UserForm(UserFormBase, model_form(User, exclude=['id', 'role_id', 'agency_id', 'date_last_updated', 'date_created'], converter=AdminConverter())):
    """
    User form, as a mixin of UserFormBase and the form generated from
    the User SQLAlchemy model
    """
    pass


admin_mod = Admin(app, sys.modules[__name__], model_forms={'User': UserForm},
                  admin_db_session=db_session, exclude_pks=True)
app.register_module(admin_mod, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True)
