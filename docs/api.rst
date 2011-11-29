.. module:: flask.ext.admin

API
---

.. autofunction:: create_admin_blueprint(datastore, name='admin', list_view_pagination=25, view_decorator=None, **kwargs)


Datastores
----------

.. autoclass:: flask.ext.admin.datastore.core.AdminDatastore
   :members:

.. autoclass:: flask.ext.admin.datastore.sqlalchemy.SQLAlchemyDatastore

.. autoclass:: flask.ext.admin.datastore.mongoalchemy.MongoAlchemyDatastore
