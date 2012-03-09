# -*- coding: utf-8 -*-
"""
    flask.ext.datastore.sqlalchemy
    ~~~~~~~~~~~~~~

    Defines a SQLAlchemy datastore.

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
from flaskext.sqlalchemy import Pagination
import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound
from wtforms import validators, widgets
from wtforms.ext.sqlalchemy.orm import model_form, converts, ModelConverter
from wtforms.ext.sqlalchemy import fields as sa_fields

from flask.ext.admin.wtforms import *
from flask.ext.admin.datastore import AdminDatastore


class SQLAlchemyDatastore(AdminDatastore):
    """A datastore class for accessing SQLAlchemy models.

    The `models` parameter should be either a module or an iterable
    (like a tuple or a list) that contains the SQLAlchemy models that
    will be made available through the admin interface.

    `db_session` should be the SQLAlchemy session that the datastore
    will use to access the database. The session should already be
    bound to an engine. See the `SQLAlchemy in Flask`_ documentation
    for more information on how to configure the session.

    By default, a form for adding and editing data will be
    automatically generated for each SQLAlchemy model. You can also
    create custom forms if you need more control over what the forms
    look like or how they behave. To use custom forms, set the
    `model_forms` parameter to be a dict with model names as keys
    matched to custom forms for the forms you want to override. Forms
    should be WTForms form objects; see the `WTForms documentation`_
    for more information on how to configure forms.

    Finally, the `exclude_pks` parameter can be used to specify
    whether or not to automatically exclude fields representing the
    primary key in auto-generated forms. The default is True, so the
    generated forms will not expose the primary keys of your
    models. This is usually a good idea if you are using a primary key
    that doesn't have any meaning outside of the database, like an
    auto-incrementing integer, because changing a primary key changes
    the nature of foreign key relationships. If you want to expose the
    primary key, set this to False.

    .. _SQLAlchemy in Flask: http://flask.pocoo.org/docs/patterns/sqlalchemy/
    .. _WTForms documentation: http://wtforms.simplecodes.com/
    """
    def __init__(self, models, db_session, model_forms=None, exclude_pks=True):
        self.model_classes = {}
        self.model_forms = model_forms
        self.db_session = db_session

        if not self.model_forms:
            self.model_forms = {}

        #XXX: fix base handling so it will work with non-Declarative models
        if type(models) == types.ModuleType:
            self.model_classes = dict(
                [(k, v) for k, v in models.__dict__.items()
                 if isinstance(v, sa.ext.declarative.DeclarativeMeta)
                 and k != 'Base'])
        else:
            self.model_classes = dict(
                [(model.__name__, model)
                 for model in models
                 if isinstance(model, sa.ext.declarative.DeclarativeMeta)
                 and model.__name__ != 'Base'])

        if self.model_classes:
            self.form_dict = dict(
                [(k, _form_for_model(v, db_session,
                                     exclude_pk=exclude_pks))
                 for k, v in self.model_classes.items()])
            for model_name, form in self.model_forms.items():
                if model_name in self.form_dict:
                    self.form_dict[model_name] = form

    def create_model_pagination(self, model_name, page, per_page=25):
        """Returns a pagination object for the list view."""
        model_class = self.model_classes[model_name]
        model_instances = self.db_session.query(model_class)
        offset = (page - 1) * per_page
        items = model_instances.limit(per_page).offset(offset).all()
        return Pagination(model_instances, page, per_page,
                          model_instances.count(), items)

    def delete_model_instance(self, model_name, model_keys):
        """Deletes a model instance. Returns True if model instance
        was successfully deleted, returns False otherwise.
        """
        model_instance = self.find_model_instance(model_name, model_keys)
        if not model_instance:
            return False
        self.db_session.delete(model_instance)
        self.db_session.commit()
        return True

    def find_model_instance(self, model_name, model_keys):
        """Returns a model instance, if one exists, that matches
        model_name and model_keys. Returns None if no such model
        instance exists.
        """
        model_class = self.get_model_class(model_name)
        pk_query_dict = {}

        for key, value in zip(_get_pk_names(model_class), model_keys):
            pk_query_dict[key] = value

        try:
            return self.db_session.query(model_class).filter_by(
                **pk_query_dict).one()
        except NoResultFound:
            return None

    def get_model_class(self, model_name):
        """Returns a model class, given a model name."""
        return self.model_classes[model_name]

    def get_model_form(self, model_name):
        """Returns a form, given a model name."""
        return self.form_dict[model_name]

    def get_model_keys(self, model_instance):
        """Returns the keys for a given a model instance."""
        return [getattr(model_instance, value)
                for value in _get_pk_names(model_instance)]

    def list_model_names(self):
        """Returns a list of model names available in the datastore."""
        return self.model_classes.keys()

    def save_model(self, model_instance):
        """Persists a model instance to the datastore. Note: this
        could be called when a model instance is added or edited.
        """
        self.db_session.add(model_instance)
        self.db_session.commit()

    def update_from_form(self, model_instance, form):
        """Returns a model instance whose values have been updated
        with the values from a given form.
        """
        for name, field in form._fields.iteritems():
            field.populate_obj(model_instance, name)

        return model_instance


def _form_for_model(model_class, db_session, exclude=None, exclude_pk=True):
    """Return a form for a given model. This will be a form generated
    by wtforms.ext.sqlalchemy.model_form, but decorated with a
    QuerySelectField for foreign keys.
    """
    if not exclude:
        exclude = []

    model_mapper = sa.orm.class_mapper(model_class)
    relationship_fields = []

    pk_names = _get_pk_names(model_class)

    if exclude_pk:
        exclude.extend(pk_names)

    # exclude any foreign_keys that we have relationships for;
    # relationships will be mapped to select fields by the
    # AdminConverter
    exclude.extend([relationship.local_side[0].name
                    for relationship in model_mapper.iterate_properties
                    if isinstance(relationship,
                                  sa.orm.properties.RelationshipProperty)
                    and relationship.local_side[0].name not in pk_names])
    form = model_form(model_class, exclude=exclude,
                      converter=AdminConverter(db_session))

    return form


def _get_pk_names(model):
    """Return the primary key attribute names for a given model
    (either instance or class).
    """
    model_mapper = model.__mapper__

    return [prop.key for prop in model_mapper.iterate_properties
            if isinstance(prop, sa.orm.properties.ColumnProperty) and \
                prop.columns[0].primary_key]


def _query_factory_for(model_class, db_session):
    """Return a query factory for a given model_class. This gives us
    an all-purpose way of generating query factories for
    QuerySelectFields.
    """
    def query_factory():
        return sorted(db_session.query(model_class).all(), key=repr)

    return query_factory


class AdminConverter(ModelConverter):
    """Subclass of the wtforms sqlalchemy Model Converter that handles
    relationship properties and uses custom widgets for date and
    datetime objects.
    """
    def __init__(self, db_session, *args, **kwargs):
        self.db_session = db_session
        super(AdminConverter, self).__init__(*args, **kwargs)

    def convert(self, model, mapper, prop, field_args):
        if not isinstance(prop, sa.orm.properties.ColumnProperty) and \
               not isinstance(prop, sa.orm.properties.RelationshipProperty):
            # XXX We don't support anything but ColumnProperty and
            # RelationshipProperty at the moment.
            return

        if isinstance(prop, sa.orm.properties.ColumnProperty):
            if len(prop.columns) != 1:
                raise TypeError('Do not know how to convert multiple-'
                                'column properties currently')

            column = prop.columns[0]

#            default_value = None
#            if hasattr(column, 'default'):      #always is True
#                default_value = column.default 

            default_value = getattr(column, 'default', None)

            if default_value is not None and \
                    not callable(default_value.arg):
                # for the default value such as number or string
                default_value = default_value.arg

            kwargs = {
                'validators': [],
                'filters': [],
                'default': default_value,
            }
            if field_args:
                kwargs.update(field_args)
            if hasattr(column, 'nullable') and column.nullable:
                kwargs['validators'].append(validators.Optional())
            if self.use_mro:
                types = inspect.getmro(type(column.type))
            else:
                types = [type(column.type)]

            converter = None
            for col_type in types:
                type_string = '%s.%s' % (col_type.__module__,
                                         col_type.__name__)
                if type_string.startswith('sqlalchemy'):
                    type_string = type_string[11:]
                if type_string in self.converters:
                    converter = self.converters[type_string]
                    break
            else:
                for col_type in types:
                    if col_type.__name__ in self.converters:
                        converter = self.converters[col_type.__name__]
                        break
                else:
                    return
            return converter(model=model, mapper=mapper, prop=prop,
                             column=column, field_args=kwargs)

        if isinstance(prop, sa.orm.properties.RelationshipProperty):
#            if prop.direction == sa.orm.interfaces.MANYTOONE and \
#                   len(prop.local_remote_pairs) != 1:
#                raise TypeError('Do not know how to convert multiple'
#                                '-column properties currently')
#            elif prop.direction == sa.orm.interfaces.MANYTOMANY and \
#                     len(prop.local_remote_pairs) != 2:
#                raise TypeError('Do not know how to convert multiple'
#                                '-column properties currently')

            local_column = prop.local_remote_pairs[0][0]
            foreign_model = prop.mapper.class_

            if prop.direction == sa.orm.properties.MANYTOONE:
                return sa_fields.QuerySelectField(
                    prop.key,
                    query_factory=_query_factory_for(foreign_model,
                                                     self.db_session),
                    allow_blank=local_column.nullable)
            if prop.direction == sa.orm.properties.MANYTOMANY:
                return sa_fields.QuerySelectMultipleField(
                    prop.key,
                    query_factory=_query_factory_for(foreign_model,
                                                     self.db_session),
                    allow_blank=local_column.nullable)

    @converts('Date')
    def conv_Date(self, field_args, **extra):
        field_args['widget'] = DatePickerWidget()
        return wtf_fields.DateField(**field_args)

    @converts('DateTime')
    def conv_DateTime(self, field_args, **extra):
        # XXX: should show disabled (greyed out) w/current value,
        #      indicating it is updated internally?
        if field_args['default']:
            if inspect.isfunction(field_args['default'].arg):
                return None
        field_args['widget'] = DateTimePickerWidget()
        return wtf_fields.DateTimeField(**field_args)

    @converts('Time')
    def conv_Time(self, field_args, **extra):
        field_args['widget'] = TimePickerWidget()
        return TimeField(**field_args)
