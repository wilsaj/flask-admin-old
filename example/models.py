"""
SQLAlchemy models, using the pattern described here:
http://flask.pocoo.org/docs/patterns/sqlalchemy/#declarative
"""
import datetime
import hashlib

from geoalchemy import GeometryColumn, GeometryDDL, Point, WKTSpatialElement
from sqlalchemy import create_engine
from sqlalchemy.schema import UniqueConstraint,ForeignKey
from sqlalchemy import Column, Boolean, Integer, Text, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy.orm import relationship, backref, synonym
from werkzeug import check_password_hash, generate_password_hash


from database import Base, db_session, engine

SECRET_KEY = 'not secure'

class Agency(Base):
    __tablename__ = 'agency'
    
    agency_id = Column(Integer, primary_key=True)
    agency_name = Column(String(80), unique=True)
    users = relationship('User', backref='affiliated_agency')

    def __init__(self, agency_name=""):
        self.agency_name = agency_name

    def __repr__(self):
        return "<Agency(%d, %s)>" % (self.agency_id, self.agency_name)



class BayEstuary(Base):
    __tablename__ = 'bay_estuary'
    
    bay_estuary_id = Column(Integer, primary_key=True)
    bay_estuary_name = Column(String(80), unique=True)

    def __repr__(self):
        return self.bay_estuary_name



class File(Base):
    __tablename__ = 'file'
    
    file_id = Column(Integer, primary_key=True)
    file_names = Column(String(256), unique=True)
    file_type_id = Column(Integer, ForeignKey('file_type.file_type_id'), nullable=False)
    site_id = Column(Integer, ForeignKey('site.site_id'))
    instrument_id = Column(Integer, ForeignKey('instrument.instrument_id'))
    upload_staff_id = Column(Integer, ForeignKey('user.user_id'))
    is_primary = Column(Boolean)
    is_qaqc = Column(Boolean)
    date_uploaded = Column(DateTime, default=datetime.datetime.now)
    date_last_updated = Column(DateTime, onupdate=datetime.datetime.now)

    # populated by backref:
    #   file_type = FileType
    #   site = Site
    #   instrument = Instrument


    def __init__(self, file_names, file_type, archive_name, upload_date, upload_staff, is_primary, is_qaqc):
        self.file_names = file_names
        self.file_type = file_type
        self.archive_name = archive_name
        self.upload_date = upload_date
        self.upload_staff = upload_staff
        self.is_primary = is_primary
        self.is_qaqc = is_qaqc

    def __repr__(self):
        return self.file_names



class FileType(Base):
    __tablename__ = 'file_type'
    
    file_type_id = Column(Integer, primary_key=True)
    file_type_name = Column(String(256), nullable=False)
    file_extension = Column(String(80), nullable=False)

    files = relationship('File', backref='file_type')
        


class FieldTrip(Base):
    __tablename__ = 'field_trip'

    field_trip_id = Column(Integer, primary_key=True)
    time_start = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=False)



class Instrument(Base):
    __tablename__ = 'instrument'

    instrument_id = Column(Integer, primary_key=True)
    serial_number = Column(String(256), nullable=False)
    twdb_inventory_id = Column(String(128))
    instrument_model_id = Column(Integer, ForeignKey('instrument_model.instrument_model_id'))
    
    calibration_records = relationship('InstrumentCalibrationRecord', backref='instrument')

    files = relationship('File', backref='instrument')

    # populated by backref:
    #   instrument_model = InstrumentModel

    def __repr__(self):
        return "%s %s (%s)" % (self.instrument_model.instrument_manufacturer.instrument_manufacturer_name,
                               self.instrument_model.instrument_model_name,
                               self.serial_number)



class InstrumentCalibrationRecord(Base):
    __tablename__ = 'instrument_calibration_record'

    instrument_calibration_record_id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('instrument.instrument_id'))
    # we need pre and post... what else?

    # populated by backref:
    #   instrument = Instrument



class InstrumentManufacturer(Base):
    __tablename__ = 'instrument_manufacturer'

    instrument_manufacturer_id = Column(Integer, primary_key=True)
    instrument_manufacturer_name = Column(String(256), unique=True, nullable=False)

    models = relationship('InstrumentModel', backref='instrument_manufacturer')

    def __repr__(self):
        return self.instrument_manufacturer_name



class InstrumentModel(Base):
    __tablename__ = 'instrument_model'
    __table_args__ = (
        UniqueConstraint('instrument_model_name', 'instrument_manufacturer_id'),
        {}
        )

    instrument_model_id = Column(Integer, primary_key=True)
    instrument_model_name = Column(String(256), nullable=False)
    instrument_manufacturer_id = Column(Integer, ForeignKey('instrument_manufacturer.instrument_manufacturer_id'))

    instruments = relationship('Instrument', backref='instrument_model')

    # populated by backref:
    #   instrument_manufacturer = InstrumentManufacturer

    def __repr__(self):
        return self.instrument_model_name



class Project(Base):
    __tablename__ = 'project'
    
    project_id = Column(Integer, primary_key=True)
    project_name = Column(String(256), nullable=False)
    


# class QAQCedDataValue(Base):
#     """
#     After QA/QC, Data value stored in this table
#     Note: is_spotCheck field is not needed, because all data will be no-spotCheck
#     """
#     __tablename__ = 'qaqced_data_value'
    
#     value_id = Column(Integer, primary_key=True)
#     site_id = Column(Integer, ForeignKey('site.site_id'))
#     parameter_id = Column(Integer, ForeignKey('parameter.parameter_id'))
#     file_id = Column(Integer, ForeignKey('file.file_id'))
#     data_value = Column(Float(precision=15), nullable=False)
#     datetime_utc = Column(DateTime, nullable=False)
#     origin_utc_offset = Column(Integer, default=0, nullable=False)
#     #vector_info = Column(String)



class QAQCRule(Base):
    __tablename__ = 'qaqc_rule'
    
    rule_id = Column(Integer, primary_key=True)
    rule_type_id = Column(Integer, ForeignKey('qaqc_rule_type.rule_type_id'))
    rule_parameters = Column(String(256))
    last_modified_by_user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)

    last_modified_by = relationship('User')


class QAQCRuleType(Base):
    __tablename__ = 'qaqc_rule_type'
    
    rule_type_id = Column(Integer, primary_key=True)
    rule_name = Column(String(256), unique=True)
    rule_description = Column(Text, nullable=False)
    
    

class RawDataValue(Base):
    __tablename__ = 'raw_data_value'
    __table_args__ = (
        UniqueConstraint('datetime_utc', 'site_id', 'parameter_id', 'instrument_id', 'vertical_offset'),
        {}
        )
    
    value_id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site.site_id'), nullable=False)
    parameter_id = Column(Integer, ForeignKey('parameter.parameter_id'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.file_id'))
    data_value = Column(Float(precision=15), nullable=False)
    datetime_utc = Column(DateTime) 
    origin_utc_offset = Column(Integer)
    vertical_offset = Column(Float(precision=15))
    is_spot_check = Column(Boolean)
    instrument_id = Column(Integer, ForeignKey('instrument.instrument_id'))
    
#    vector_info = Column(String)


    def __init__(self, site_id, parameter_id, file_id, data_value, datetime_utc, origin_utc_offset, vector_info, is_spot_check):
        self.site_id = site_id
        self.parameter_id = parameter_id
        self.file_id = file_id
        self.data_value = data_value
        self.datetime_utc = datetime_utc
        self.origin_utc_offset = origin_utc_offset
        self.vector_info = vector_info
        self.is_spot_check = is_spot_check



class Site(Base):
    __tablename__ = 'site'    
    
    site_id = Column(Integer, primary_key=True)
    site_code = Column(String, unique=True)
    site_name = Column(String)
    county = Column(String)
    comment = Column(String)
    status = Column(Boolean, default=True)
    agency_id = Column(Integer, ForeignKey('agency.agency_id'))
    bay_estuary_id = Column(Integer, ForeignKey('bay_estuary.bay_estuary_id'))
    project_id = Column(Integer, ForeignKey('project.project_id'))
    geom = GeometryColumn(Point(2))

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
    

    files = relationship('File', backref='site')
    
    def __init__(self, site_code="", site_name="", latitude=0, longitude=0, agency_id=1):
        self.site_code = site_code
        self.site_name = site_name
        self.agency_id = agency_id
        self.geom = WKTSpatialElement("POINT(%f %f)" % (latitude, longitude))

    def __repr__(self):
        return self.site_name

GeometryDDL(Site.__table__)


class SiteEvent(Base):
    __tablename__ = 'site_event'
    
    event_id = Column(Integer, primary_key=True)
    comment = Column(Text)
    event_date = Column(DateTime)
    site_id = Column(Integer, ForeignKey('site.site_id'))
    


class Parameter(Base):
    __tablename__ = 'parameter'
    
    parameter_id = Column(Integer, primary_key=True)
    parameter_code = Column(String(10), unique=True)
    parameter_description = Column(String)
    parameter_units = Column(String)

    def __repr__(self):
        return self.parameter_code



class Role(Base):
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(256), unique=True)
    role_description = Column(Text)
    users = relationship('User', backref='role')

    def __repr__(self):
        return self.role_name



class User(Base):
    __tablename__ = 'user'


    user_id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    fullname = Column(String(80), nullable=False)
    _password = Column('password', String(256), nullable=False)
    email = Column(String(80), nullable=False)
    agency_id = Column(Integer, ForeignKey('agency.agency_id'),
                       default=1)
    role_id = Column(Integer, ForeignKey('role.role_id'), nullable=False)
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
        return self.password == hashlib.sha1(SECRET_KEY+password).hexdigest()

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = hashlib.sha1(SECRET_KEY+password).hexdigest()

    password = synonym('_password', descriptor=password)

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.username, self.fullname,
                                            self.role.role_name)

