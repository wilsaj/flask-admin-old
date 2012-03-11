import sys

from flask import Flask,  redirect
from flask.ext import admin
from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
from sqlalchemy import create_engine, Table
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
import wtforms as wtf

Base = declarative_base()


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class TestModel(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    int_value = Column(Integer, default="2194112")
    str_value = Column(String, default="128uasdn1uinvuio12ioj!!@Rfja")
    num_value = Column(Numeric, default=22341.29)


def create_app(database_uri='sqlite://'):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'not secure'
    engine = create_engine(database_uri, convert_unicode=True)
    app.db_session = scoped_session(sessionmaker(
        autocommit=False, autoflush=False, bind=engine))
    datastore = SQLAlchemyDatastore(
        (TestModel,), app.db_session)
    admin_blueprint = admin.create_admin_blueprint(datastore)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    Base.metadata.create_all(bind=engine)

    @app.route('/')
    def go_to_admin():
        return redirect('/admin')

    return app


if __name__ == '__main__':
    app = create_app('sqlite://')
    app.run(debug=True)
