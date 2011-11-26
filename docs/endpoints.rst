Flask-Admin Endpoints
---------------------
If you want to refer to views in Flask-Admin, the following endpoints
are available:

:meth:`url_for('admin.index')`
    returns the url for the index view

:meth:`url_for('admin.list_view', model_name='some_model')`
    returns the list view for a given model

:meth:`url_for('admin.edit', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for editing a specific model
    instance

:meth:`url_for('admin.add', model_name='some_model')`
    returns the url for the adding a new model instance

:meth:`url_for('admin.delete', model_name='some_model', model_key=primary_key)`
    returns the url for the page used for deleting a specific model
    instance


.. note::

  You can use the ``name`` argument in
  :func:`create_admin_blueprint()` to set the name of the
  blueprint. For example if ``name="my_named_admin"``, then the
  endpoint for the index becomes ``'my_named_admin.index'``. This is
  necessary if you are going to use more than one admin blueprint
  within the same app.


