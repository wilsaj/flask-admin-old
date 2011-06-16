# -*- coding: utf-8 -*-
"""
    flaskext.admin
    ~~~~~~~~~~~~~~

    Description of the module goes here...

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
from flask import (current_app, flash, g, Module, render_template,
                   redirect, request, session, url_for)
from flaskext.sqlalchemy import Pagination
from flaskext import themes
from flaskext.themes import render_theme_template
import jinja2.exceptions
import sqlalchemy as sa
import sqlalchemy.ext.declarative
from sqlalchemy.orm.exc import NoResultFound
from wtforms import widgets, validators
from wtforms import fields as wtf_fields
from wtforms.form import Form
from wtforms.ext.sqlalchemy.orm import model_form, converts, ModelConverter
from wtforms.ext.sqlalchemy import fields as sa_fields


admin = Module(__name__)


class Admin(Module):
    def __init__(self, app, models, db_session, model_forms={},
                 exclude_pks=False, theme='admin_default',
                 pagination_per_page=25, view_decorator=None,
                 append_to_endpoints='', **kwargs):
        """This returns a module that can be registered to your flask
        app. Additional parameters will be passed to the module
        constructor.

        The parameters are:
        `app`
            The app to associate this Admin module with

        `models`
            Either a module or an iterable containing your SQLAlchemy models

        `db_session`
            SQLAlchemy session that has been set up and bound to an
            engine. See the documentation on using Flask with
            SQLAlchemy for more information on how to set that up.

        `model_forms`
            A dict with model names as keys, mapped to WTForm Form objects
            that should be used as forms for creating and editing
            instances of these models

        `exclude_pks`
            Don't include primary keys in the rendered forms

        `theme`
            Theme that should be used for rendering the admin module

        `pagination_per_page`
            If there are a lot of model instances the list view will
            be paginated so that only this number of model instances
            are shown for a given page. Default is 25.

        `view_decorator`
            Each admin views will be decorated with this decorator, if
            set. In particular, you might want to set this to a
            decorator that handles authentication
            (e.g. login_required).

        `append_to_endpoints`
            A string that will be appended to the end of each admin
            view endpoint so that the endpoints are distinct when
            referenced by url_for(). If you are using multiple admin
            modules, this it is necessary to set this value to
            something different for each admin module so the admin
            templates can find the correct views.
        """
        super(Admin, self).__init__(self, __name__, **kwargs)
        self.model_dict = {}
        self.app = app
        self.theme = theme
        self.pagination_per_page = pagination_per_page
        self.db_session = db_session

        if db_session:
            self.db_session = db_session

        self.append_to_endpoints = append_to_endpoints

        #XXX: fix base handling so it will work with non-Declarative models
        if type(models) == types.ModuleType:
            self.model_dict = dict(
                [(k, v) for k, v in models.__dict__.items()
                 if isinstance(v, sa.ext.declarative.DeclarativeMeta)
                 and k != 'Base'])
        else:
            self.model_dict = dict(
                [(model.__name__, model)
                 for model in models
                 if isinstance(model, sa.ext.declarative.DeclarativeMeta)
                 and model.__name__ != 'Base'])

        if self.model_dict:
            self.form_dict = dict(
                [(k, _form_for_model(v, self.db_session,
                                     exclude_pk=exclude_pks))
                 for k, v in self.model_dict.items()])
            for model, form in model_forms.items():
                if model in self.form_dict:
                    self.form_dict[model] = form

        if not view_decorator:
            def view_decorator(f):
                @wraps(f)
                def wrapper(*args, **kwds):
                    return f(*args, **kwds)
                return wrapper

        def create_index_view():
            @view_decorator
            def index():
                """
                Landing page view for admin module
                """
                return self.render_admin_template(
                    'admin/index.html',
                    admin_models=sorted(self.model_dict.keys()),
                    append_to_endpoints=self.append_to_endpoints)
            return index

        def create_list_view():
            @view_decorator
            def list_view(model_name):
                """
                Lists instances of a given model, so they can be selected for
                editing or deletion.
                """
                db_session = self.db_session

                if not model_name in self.model_dict.keys():
                    return "%s cannot be accessed through this admin page" % (
                        model_name,)
                model = self.model_dict[model_name]
                model_instances = db_session.query(model)
                per_page = self.pagination_per_page
                page = int(request.args.get('page', '1'))
                offset = (page - 1) * per_page
                items = model_instances.limit(per_page).offset(offset).all()
                pagination = Pagination(model_instances, page, per_page,
                                        model_instances.count(), items)
                return self.render_admin_template(
                    'admin/list.html',
                    admin_models=sorted(self.model_dict.keys()),
                    _get_pk_value=_get_pk_value,
                    model_instances=pagination.items,
                    model_name=model_name,
                    pagination=pagination,
                    append_to_endpoints=self.append_to_endpoints)
            return list_view

        def create_edit_view():
            @view_decorator
            def edit(model_name, model_key):
                """
                Edit a particular instance of a model.
                """
                db_session = self.db_session

                if not model_name in self.model_dict.keys():
                    return "%s cannot be accessed through this admin page" % (
                        model_name,)

                model = self.model_dict[model_name]
                model_form = self.form_dict[model_name]

                pk = _get_pk_name(model)
                pk_query_dict = {pk: model_key}

                try:
                    model_instance = db_session.query(model).filter_by(
                        **pk_query_dict).one()
                except NoResultFound:
                    return "%s not found: %s" % (model_name, model_key)

                if request.method == 'GET':
                    form = model_form(obj=model_instance)
                    return self.render_admin_template(
                        'admin/edit.html',
                        admin_models=sorted(self.model_dict.keys()),
                        model_instance=model_instance,
                        model_name=model_name, form=form,
                        append_to_endpoints=self.append_to_endpoints)

                elif request.method == 'POST':
                    form = model_form(request.form, obj=model_instance)
                    if form.validate():
                        model_instance = _populate_model_from_form(
                            model_instance, form)
                        db_session.add(model_instance)
                        db_session.commit()
                        flash('%s updated: %s' % (model_name, model_instance),
                              'success')
                        return redirect(
                            url_for('list_view%s' % append_to_endpoints,
                                    model_name=model_name))
                    else:
                        flash('There was an error processing your form. '
                              'This %s has not been saved.' % model_name,
                              'error')
                        return self.render_admin_template(
                            'admin/edit.html',
                            admin_models=sorted(self.model_dict.keys()),
                            model_instance=model_instance,
                            model_name=model_name, form=form,
                            append_to_endpoints=self.append_to_endpoints)
            return edit

        def create_add_view():
            @view_decorator
            def add(model_name):
                """
                Create a new instance of a model.
                """
                db_session = self.db_session
                if not model_name in self.model_dict.keys():
                    return "%s cannot be accessed through this admin page" % (
                        model_name)
                model = self.model_dict[model_name]
                model_form = self.form_dict[model_name]
                model_instance = model()
                if request.method == 'GET':
                    form = model_form()
                    return self.render_admin_template(
                        'admin/add.html',
                        admin_models=sorted(self.model_dict.keys()),
                        model_name=model_name,
                        form=form,
                        append_to_endpoints=self.append_to_endpoints)
                elif request.method == 'POST':
                    form = model_form(request.form)
                    if form.validate():
                        model_instance = _populate_model_from_form(
                            model_instance, form)
                        db_session.add(model_instance)
                        db_session.commit()
                        flash('%s added: %s' % (model_name, model_instance),
                              'success')
                        return redirect(url_for('list_view%s' %
                                                self.append_to_endpoints,
                                                model_name=model_name))
                    else:
                        flash('There was an error processing your form. This '
                              '%s has not been saved.' % model_name, 'error')
                        return self.render_admin_template(
                            'admin/add.html',
                            admin_models=sorted(self.model_dict.keys()),
                            model_name=model_name,
                            form=form,
                            append_to_endpoints=self.append_to_endpoints)
            return add

        def create_delete_view():
            @view_decorator
            def delete(model_name, model_key):
                """
                Delete an instance of a model.
                """
                db_session = self.db_session
                if not model_name in self.model_dict.keys():
                    return "%s cannot be accessed through this admin page" % (
                        model_name,)
                model = self.model_dict[model_name]
                pk = _get_pk_name(model)
                pk_query_dict = {pk: model_key}
                try:
                    model_instance = db_session.query(model).filter_by(
                        **pk_query_dict).one()
                except NoResultFound:
                    return "%s not found: %s" % (model_name, model_key)
                db_session.delete(model_instance)
                db_session.commit()
                flash('%s deleted: %s' % (model_name, model_instance),
                      'success')
                return redirect(url_for(
                    'list_view%s' % self.append_to_endpoints,
                    model_name=model_name))
            return delete

        self.add_url_rule('/', 'index%s' % self.append_to_endpoints,
                          view_func=create_index_view())
        self.add_url_rule('/list/<model_name>/',
                          'list_view%s' % self.append_to_endpoints,
                          view_func=create_list_view())
        self.add_url_rule('/edit/<model_name>/<model_key>/',
                          'edit%s' % self.append_to_endpoints,
                          view_func=create_edit_view(),
                          methods=['GET', 'POST'])
        self.add_url_rule('/delete/<model_name>/<model_key>/',
                          'delete%s' % self.append_to_endpoints,
                          view_func=create_delete_view())
        self.add_url_rule('/add/<model_name>/',
                          'add%s' % self.append_to_endpoints,
                          view_func=create_add_view(),
                          methods=['GET', 'POST'])

    def render_admin_template(self, *args, **kwargs):
        """
        render theme template if using themes, fallback to trying to
        render a regular template if not
        """
        if hasattr(self.app, "theme_manager"):
            try:
                return render_theme_template(
                    self.theme,
                    *args, **kwargs)
            except jinja2.exceptions.TemplateNotFound:
                if default_admin_theme_loader not in self.app.theme_manager.loaders:
                    self.app.theme_manager.loaders.append(
                        default_admin_theme_loader)
                    self.app.theme_manager.refresh()
                return render_theme_template(
                    self.theme,
                    *args, **kwargs)
        else:
            try:
                return render_template(*args, **kwargs)
            except jinja2.exceptions.TemplateNotFound:
                raise jinja2.exceptions.TemplateNotFound(
                    "Flask-Admin cannot find its templates. The most likely "
                    "cause for this is that setup_themes has not been "
                    "run for your app. See the docs or examples for how to "
                    "do that.")



def default_admin_theme_loader(app):
    themes_dir = os.path.join(os.path.dirname(__file__), 'themes')
    if os.path.isdir(themes_dir):
        default_themes = themes.load_themes_from(themes_dir)

        def set_theme_application_to_import_name(theme):
            """
            Set the theme application to the import name of the
            app. The themes extension checks that theme.application
            matches an application's import name when it does things
            like render templates for a theme for example. This is
            usually set in an info.json file but there is no way to
            know what the app's import name will be ahead of time for
            our default theme, so we do it now.
            """
            theme.application = app.import_name
            return theme

        theme_list = [set_theme_application_to_import_name(theme)
                      for theme in default_themes]
        return theme_list
    else:
        return ()


def _populate_model_from_form(model_instance, form):
    """
    Returns a model instance that has been populated with the data
    from a form.
    """
    for name, field in form._fields.iteritems():
        field.populate_obj(model_instance, name)

    return model_instance


def _get_pk_value(model_instance):
    """
    Return the primary key value for a given model_instance
    instance. Assumes single primary key.
    """
    return getattr(model_instance, _get_pk_name(model_instance))


def _get_pk_name(model):
    """
    Return the primary key attribute name for a given model (either
    instance or class). Assumes single primary key.
    """
    model_mapper = model.__mapper__

    for prop in model_mapper.iterate_properties:
        if isinstance(prop, sa.orm.properties.ColumnProperty) and \
               prop.columns[0].primary_key:
            return prop.key

    return None


def _form_for_model(model_class, db_session, exclude=[], exclude_pk=False):
    """
    Return a form for a given model. This will be a form generated by
    wtforms.ext.sqlalchemy.model_form, but decorated with a
    QuerySelectField for foreign keys.
    """
    model_mapper = sa.orm.class_mapper(model_class)
    relationship_fields = []

    if exclude_pk:
        exclude.append(_get_pk_name(model_class))

    # exclude any foreign_keys that we have relationships for;
    # relationships will be mapped to select fields by the
    # AdminConverter
    exclude.extend([relationship.local_side[0].name
                    for relationship in model_mapper.iterate_properties
                    if isinstance(relationship,
                                  sa.orm.properties.RelationshipProperty)])
    form = model_form(model_class, exclude=exclude,
                      converter=AdminConverter(db_session))

    return form


def _query_factory_for(model_class, db_session):
    """
    Return a query factory for a given model_class. This gives us an
    all-purpose way of generating query factories for
    QuerySelectFields.
    """
    def query_factory():
        return sorted(db_session.query(model_class).all(), key=repr)

    return query_factory


class TimeField(wtf_fields.Field):
    """
    A text field which stores a `time.time` matching a format.
    """
    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None,
                 format='%H:%M:%S', **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            time_str = u' '.join(valuelist)
            try:
                timetuple = time.strptime(time_str, self.format)
                self.data = datetime.time(*timetuple[3:6])
            except ValueError:
                self.data = None
                raise


class DatePickerWidget(widgets.TextInput):
    """
    TextInput widget that adds a 'datepicker' class to the html input
    element; this makes it easy to write a jQuery selector that adds a
    UI widget for date picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datepicker %s' % c
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(widgets.TextInput):
    """
    TextInput widget that adds a 'datetimepicker' class to the html
    input element; this makes it easy to write a jQuery selector that
    adds a UI widget for datetime picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datetimepicker %s' % c
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class TimePickerWidget(widgets.TextInput):
    """
    TextInput widget that adds a 'timepicker' class to the html input
    element; this makes it easy to write a jQuery selector that adds a
    UI widget for time picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'timepicker %s' % c
        return super(TimePickerWidget, self).__call__(field, **kwargs)


class AdminConverter(ModelConverter):
    """
    Subclass of the wtforms sqlalchemy Model Converter that handles
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
            kwargs = {
                'validators': [],
                'filters': [],
                'default': column.default,
            }
            if field_args:
                kwargs.update(field_args)
            if column.nullable:
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
            if prop.direction == sa.orm.interfaces.MANYTOONE and \
                   len(prop.local_remote_pairs) != 1:
                raise TypeError('Do not know how to convert multiple'
                                '-column properties currently')
            elif prop.direction == sa.orm.interfaces.MANYTOMANY and \
                     len(prop.local_remote_pairs) != 2:
                raise TypeError('Do not know how to convert multiple'
                                '-column properties currently')

            local_column = prop.local_remote_pairs[0][0]
            foreign_model = prop.mapper.class_

            if prop.direction == sa.orm.properties.MANYTOONE:
                return sa_fields.QuerySelectField(
                    foreign_model.__name__,
                    query_factory=_query_factory_for(foreign_model,
                                                     self.db_session),
                    allow_blank=local_column.nullable)
            if prop.direction == sa.orm.properties.MANYTOMANY:
                return sa_fields.QuerySelectMultipleField(
                    foreign_model.__name__,
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
    def conv_Date(self, field_args, **extra):
        field_args['widget'] = TimePickerWidget()
        return TimeField(**field_args)
