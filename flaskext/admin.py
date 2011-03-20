# -*- coding: utf-8 -*-
"""
    flaskext.admin
    ~~~~~~~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import inspect
import types

import sqlalchemy as sa
import sqlalchemy.ext.declarative
from flask import app, flash, g, Module, render_template, redirect, request, \
     session, url_for
from flaskext.sqlalchemy import Pagination
from sqlalchemy.orm.exc import NoResultFound
from wtforms.ext.sqlalchemy.orm import model_form, converts, ModelConverter
from wtforms import fields as wtf_fields
from wtforms import widgets, validators
from wtforms.ext.sqlalchemy import fields as sa_fields
from wtforms.form import Form


def Admin(models, model_forms={}, include_models=[], exclude_models=[],
          exclude_pks=False, admin_db_session=None):
    global model_dict
    global form_dict
    global db_session

    try:
        model_dict
    except NameError:
        model_dict = {}

    if admin_db_session:
        db_session = admin_db_session

    for i in include_models:
        if i in exclude_models:
            raise "'%s' is in both include_models and exclude_models" % i

    #XXX: fix base handling so it will work with non-Declarative models
    if type(models) == types.ModuleType:
        if include_models:
            for model in include_models:
                module_dict = models.__dict__
                if model in module_dict and \
                       isinstance(module_dict[model],
                                  sa.ext.declarative.DeclarativeMeta):
                    model_dict[model] = module_dict[model]
        else:
            model_dict = dict([(k, v) for k, v in models.__dict__.items()
                               if isinstance(v,
                                             sa.ext.declarative.DeclarativeMeta) \
                               and k != 'Base'])

    if model_dict:
        form_dict = dict([(k, _form_for_model(v, exclude_pk=exclude_pks))
                          for k, v in model_dict.items()])
        for model, form in model_forms.items():
            if model in form_dict:
                form_dict[model] = form

    return admin


admin = Module(__name__)


@admin.route('/')
def index():
    """
    Admin module views. List available models/tables for this user to
    perform CUID
    """
    return render_template('admin/index.html',
                           admin_models=sorted(model_dict.keys()))


@admin.route('/list/<model_name>/')
def generic_model_list(model_name):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)
    model = model_dict[model_name]
    model_instances = model.query
    per_page = 15
    page = int(request.args.get('page', '1'))
    items = model_instances.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(model_instances, page, per_page,
                            model_instances.count(), items)
    return render_template('admin/list.html',
                           admin_models=sorted(model_dict.keys()),
                           _get_pk_value=_get_pk_value,
                           model_instances=pagination.items,
                           model_name=model_name,
                           pagination=pagination,
                           )


@admin.route('/add/<model_name>/', methods=['GET', 'POST'])
def generic_model_add(model_name):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)

    model = model_dict[model_name]
    model_form = form_dict[model_name]
    model_instance = model()

    if request.method == 'GET':
        form = model_form()
        return render_template('admin/add.html',
                               model_name=model_name,
                               form=form)
    elif request.method == 'POST':
        form = model_form(request.form)
        if form.validate():
            model_instance = _populate_model_from_form(model_instance, form)
            db_session.add(model_instance)
            db_session.commit()
            flash('%s added: %s' % (model_name, model_instance), 'success')
            return redirect(url_for('generic_model_list',
                                    model_name=model_name))

        else:
            flash('There are errors, see below!', 'error')
            return render_template('admin/add.html',
                                   admin_models=sorted(model_dict.keys()),
                                   model_name=model_name,
                                   form=form)


@admin.route('/delete/<model_name>/<model_key>/')
def generic_model_delete(model_name, model_key):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)

    model = model_dict[model_name]

    pk = _get_pk_name(model)
    pk_query_dict = {pk: model_key}

    try:
        model_instance = model.query.filter_by(**pk_query_dict).one()
    except NoResultFound:
        return "%s not found: %s" % (model_name, model_key)

    db_session.delete(model_instance)
    db_session.commit()
    flash('%s deleted: %s' % (model_name, model_instance), 'success')
    return redirect(url_for('generic_model_list', model_name=model_name))


@admin.route('/edit/<model_name>/<model_key>/', methods=['GET', 'POST'])
def generic_model_edit(model_name, model_key):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)

    model = model_dict[model_name]
    model_form = form_dict[model_name]

    pk = _get_pk_name(model)
    pk_query_dict = {pk: model_key}

    try:
        model_instance = model.query.filter_by(**pk_query_dict).one()
    except NoResultFound:
        return "%s not found: %s" % (model_name, model_key)

    if request.method == 'GET':
        form = model_form(obj=model_instance)
        return render_template('admin/edit.html',
                               admin_models=sorted(model_dict.keys()),
                               model_instance=model_instance,
                               model_name=model_name,
                               form=form)

    elif request.method == 'POST':
        form = model_form(request.form, obj=model_instance)

        if form.validate():
            model_instance = _populate_model_from_form(model_instance, form)
            db_session.add(model_instance)
            db_session.commit()
            flash('%s updated: %s' % (model_name, model_instance), 'success')
            return redirect(url_for('generic_model_list',
                                    model_name=model_name))

        else:
            flash('There are errors, see below!', 'error')
            return render_template('admin/edit.html',
                                   admin_models=sorted(model_dict.keys()),
                                   model_instance=model_instance,
                                   model_name=model_name,
                                   form=form)


def _populate_model_from_form(model_instance, form):
    """
    Return a populated model instance from a form.
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


def _form_for_model(model_class, exclude=[], exclude_pk=False):
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

    form = model_form(model_class, exclude=exclude, converter=AdminConverter())

    return form


def _query_factory_for(model_class):
    """
    Return a query factory for a given model_class. This looks weird,
    but it gives us an all-purpose way of generating query factories
    for QuerySelectFields.
    """
    def query_factory():
        return sorted(model_class.query.all(), key=repr)

    return query_factory


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


class AdminConverter(ModelConverter):
    """
    Subclass of the wtforms sqlalchemy Model Converter that handles
    relationship properties and uses custom widgets for date and
    datetime objects.
    """
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
                    query_factory=_query_factory_for(foreign_model),
                    allow_blank=local_column.nullable)

            if prop.direction == sa.orm.properties.MANYTOMANY:
                return sa_fields.QuerySelectMultipleField(
                    foreign_model.__name__,
                    query_factory=_query_factory_for(foreign_model),
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
