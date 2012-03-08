# -*- coding: utf-8 -*-
"""
    flask.ext.admin
    ~~~~~~~~~~~~~~

    Flask-Admin is a Flask extension module that aims to be a
    flexible, customizable web-based interface to your datastore.

    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import datetime
from functools import wraps
import inspect
import os
import time
import types

import flask
from flask import flash, render_template, redirect, request, url_for

from flask.ext.admin.wtforms import has_file_field
from flask.ext.admin.datastore import AdminDatastore


def create_admin_blueprint(*args, **kwargs):
    """Returns a Flask blueprint that provides the admin interface
    views. This blueprint will need to be registered to your flask
    application. The `datastore` parameter should be an set to be an
    instantiated :class:`AdminDatastore`.

    For example, typical usage would look something like this::

        from flask import Flask
        from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore

        from my_application import models, db_session

        app = Flask(__name__)
        datastore = SQLAlchemyDatastore(models, db_session)
        admin = create_admin_blueprint(datastore)
        app.register_blueprint(admin, url_prefix='/admin')


    You can optionally specify the `name` to be used for your
    blueprint. The blueprint name preceeds the view names in the
    endpoints, if for example you want to refer to the views using
    :func:`flask.url_for()`.

    .. note::

       If you are using more than one admin blueprint from within the
       same app, it is necessary to give each admin blueprint a
       different name so the admin blueprints will have distinct
       endpoints.

    The `view_decorator` parameter can be set to a decorator that will
    be applied to each admin view function.  For example, you might
    want to set this to a decorator that handles authentication
    (e.g. login_required). See the authentication/view_decorator.py
    for an example of this.

    The `list_view_pagination` parameter sets the number of items that
    will be listed per page in the list view.

    Finally, the `empty_sequence` keyword can be used to designate a
    sequence of characters that can be used as a substitute for cases
    where part of the key url may be empty.  This should be a rare
    occurance, but might comes up when using composite keys which can
    contain empty parts. By default, `empty_sequence` is set to %1A,
    the substitute control character.
    """
    if not isinstance(args[0], AdminDatastore):
        from warnings import warn
        warn(DeprecationWarning(
            'The interface for creating admin blueprints has changed '
            'as of Flask-Admin 0.3. In order to support alternative '
            'datasores, you now need to configure an admin datastore '
            'object before calling create_admin_blueprint(). See the '
            'Flask-Admin documentation for more information.'),
             stacklevel=2)
        return create_admin_blueprint_deprecated(*args, **kwargs)

    else:
        return create_admin_blueprint_new(*args, **kwargs)


def create_admin_blueprint_deprecated(
    models, db_session, name='admin', model_forms=None, exclude_pks=True,
    list_view_pagination=25, view_decorator=None, **kwargs):

    from flask.ext.admin.datastore.sqlalchemy import SQLAlchemyDatastore
    datastore = SQLAlchemyDatastore(models, db_session, model_forms,
                                    exclude_pks)

    return create_admin_blueprint_new(datastore, name, list_view_pagination,
                                      view_decorator)


def create_admin_blueprint_new(
    datastore, name='admin', list_view_pagination=25, view_decorator=None,
    empty_sequence=u'\x1a', template_folder=None, static_folder=None,
    **kwargs):
    if not template_folder:
        template_folder = os.path.join(
            _get_admin_extension_dir(), 'templates')
    if not static_folder:
        static_folder = os.path.join(
            _get_admin_extension_dir(), 'static')

    admin_blueprint = flask.Blueprint(
        name, 'flask.ext.admin',
        static_folder=static_folder, template_folder=template_folder,
        **kwargs)

    # if no view decorator was assigned, let view_decorator be a dummy
    # decorator that doesn't really do anything
    if not view_decorator:
        def view_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwds):
                return f(*args, **kwds)
            return wrapper

    def get_model_url_key(model_instance):
        """Helper function that turns a set of model keys into a
        unique key for a url.
        """
        values = datastore.get_model_keys(model_instance)
        return '/'.join([unicode(value) if value else empty_sequence
                         for value in values])

    def create_index_view():
        @view_decorator
        def index():
            """Landing page view for admin module
            """
            return render_template(
                'admin/index.html',
                model_names=datastore.list_model_names())
        return index

    def create_list_view():
        @view_decorator
        def list_view(model_name):
            """Lists instances of a given model, so they can
            beselected for editing or deletion.
            """
            if not model_name in datastore.list_model_names():
                return "%s cannot be accessed through this admin page" % (
                    model_name,)
            per_page = list_view_pagination
            page = int(request.args.get('page', '1'))
            pagination = datastore.create_model_pagination(
                model_name, page, per_page)

            return render_template(
                'admin/list.html',
                model_names=datastore.list_model_names(),
                get_model_url_key=get_model_url_key,
                model_name=model_name,
                pagination=pagination)
        return list_view

    def create_edit_view():
        @view_decorator
        def edit(model_name, model_url_key):
            """Edit a particular instance of a model."""
            model_keys = [key if key != empty_sequence else u''
                         for key in model_url_key.split('/')]

            if not model_name in datastore.list_model_names():
                return "%s cannot be accessed through this admin page" % (
                    model_name,)

            model_form = datastore.get_model_form(model_name)
            model_instance = datastore.find_model_instance(
                model_name, model_keys)

            if not model_instance:
                return "%s not found: %s" % (model_name, model_key)

            if request.method == 'GET':
                form = model_form(obj=model_instance)
                form._has_file_field = has_file_field(form)
                return render_template(
                    'admin/edit.html',
                    model_names=datastore.list_model_names(),
                    model_instance=model_instance,
                    model_name=model_name, form=form)

            elif request.method == 'POST':
                form = model_form(request.form, obj=model_instance)
                form._has_file_field = has_file_field(form)
                if form.validate():
                    model_instance = datastore.update_from_form(
                        model_instance, form)
                    datastore.save_model(model_instance)
                    flash('%s updated: %s' % (model_name, model_instance),
                          'success')
                    return redirect(
                        url_for('.list',
                                model_name=model_name))
                else:
                    flash('There was an error processing your form. '
                          'This %s has not been saved.' % model_name,
                          'error')
                    return render_template(
                        'admin/edit.html',
                        model_names=datastore.list_model_names(),
                        model_instance=model_instance,
                        model_name=model_name, form=form)
        return edit

    def create_add_view():
        @view_decorator
        def add(model_name):
            """Create a new instance of a model."""
            if not model_name in datastore.list_model_names():
                return "%s cannot be accessed through this admin page" % (
                    model_name)
            model_class = datastore.get_model_class(model_name)
            model_form = datastore.get_model_form(model_name)
            model_instance = model_class()
            if request.method == 'GET':
                form = model_form()
                form._has_file_field = has_file_field(form)
                return render_template(
                    'admin/add.html',
                    model_names=datastore.list_model_names(),
                    model_name=model_name,
                    form=form)
            elif request.method == 'POST':
                form = model_form(request.form)
                form._has_file_field = has_file_field(form)
                if form.validate():
                    model_instance = datastore.update_from_form(
                        model_instance, form)
                    datastore.save_model(model_instance)
                    flash('%s added: %s' % (model_name, model_instance),
                          'success')
                    return redirect(url_for('.list',
                                            model_name=model_name))
                else:
                    flash('There was an error processing your form. This '
                          '%s has not been saved.' % model_name, 'error')
                    return render_template(
                        'admin/add.html',
                        model_names=datastore.list_model_names(),
                        model_name=model_name,
                        form=form)
        return add

    def create_delete_view():
        @view_decorator
        def delete(model_name, model_url_key):
            """Delete an instance of a model."""
            model_keys = [key if key != empty_sequence else u''
                          for key in model_url_key.split('/')]

            if not model_name in datastore.list_model_names():
                return "%s cannot be accessed through this admin page" % (
                    model_name,)
            model_instance = datastore.delete_model_instance(
                model_name, model_keys)
            if not model_instance:
                return "%s not found: %s" % (model_name, model_keys)
            flash('%s deleted: %s' % (model_name, model_instance),
                  'success')
            return redirect(
                url_for('.list', model_name=model_name))

        return delete

    admin_blueprint.add_url_rule('/', 'index',
                                 view_func=create_index_view())
    list_view = create_list_view()
    admin_blueprint.add_url_rule('/list/<model_name>/',
                                 'list', view_func=list_view)
    admin_blueprint.add_url_rule('/list/<model_name>/',
                                 'list_view', view_func=list_view)
    admin_blueprint.add_url_rule('/edit/<model_name>/<path:model_url_key>/',
                                 'edit', view_func=create_edit_view(),
                                 methods=['GET', 'POST'])
    admin_blueprint.add_url_rule('/delete/<model_name>/<path:model_url_key>/',
                                 'delete', view_func=create_delete_view())
    admin_blueprint.add_url_rule('/add/<model_name>/',
                                 'add', view_func=create_add_view(),
                                 methods=['GET', 'POST'])

    return admin_blueprint


def _get_admin_extension_dir():
    """Returns the directory path of this admin extension. This is
    necessary for setting the static_folder and templates_folder
    arguments when creating the blueprint.
    """
    return os.path.dirname(inspect.getfile(inspect.currentframe()))
