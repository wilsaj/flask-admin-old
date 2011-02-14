from pysqlite2 import dbapi2 as sqlite
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


from example import app


# to use geoalchemy with spatialite, the libspatialite library has to
# be loaded as an extension
if app.config['SQLALCHEMY_DATABASE_URI']:
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True, module=sqlite, echo=True)
    connection = engine.raw_connection().connection
    connection.enable_load_extension(True)
    import platform
    if "ARCH" in platform.uname()[2]:
        engine.execute("select load_extension('/usr/lib/libspatialite.so.1')")
    else: 
        engine.execute("select load_extension('/usr/lib/libspatialite.so.2')")
    
else:
    engine = create_engine(app.config['WHATEVER_DATABASE_URI'], convert_unicode=True)


db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import swis.models

    # see above note about geoalchemy + spatialite
    if app.config['SQLALCHEMY_DATABASE_URI']:
        db_session.execute("SELECT InitSpatialMetaData()")
        db_session.execute("INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, ref_sys_name, proj4text) VALUES (4326, 'epsg', 4326, 'WGS 84', '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs');")

    Base.metadata.create_all(bind=engine)
