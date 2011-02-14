# -*- coding: utf-8 -*-
"""
    flaskext.admin
    ~~~~~~~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import types

from flask import app, flash, g, Module, render_template, redirect, request, session, url_for
from sqlalchemy.orm.exc import NoResultFound
import sqlalchemy.ext.declarative
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.form import Form

from webhelpers.paginate import Page


def Admin(models, model_forms={}, include_models=[], exclude_models=[], admin_db_session=None):
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

    #XXX: fix base handling
    if type(models) == types.ModuleType:
        if include_models:
            for model in include_models:
                module_dict = models.__dict__
                if model in module_dict and isinstance(module_dict[model], sqlalchemy.ext.declarative.DeclarativeMeta):
                    model_dict[model] = module_dict[model]
        else:
            model_dict = dict([(k,v) for k,v in models.__dict__.items() if isinstance(v, sqlalchemy.ext.declarative.DeclarativeMeta) and k != 'Base'])

    if model_dict:
        form_dict = dict([(k, _form_for_model(v)) for k,v in model_dict.items()])
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
                           admin_models=model_dict.keys())


@admin.route('/list/<model_name>/')
def generic_model_list(model_name, page=1):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)
    model = model_dict[model_name]
    _paginate = dict()
    def get_page_url(page, partial=None):
        url = url_for('generic_model_list', model_name = model_name, page = page,)
        if partial:
            url += "&partial=1"
        return url
    _paginate['url'] = get_page_url
    model_instances = model.query
    page = request.args.get('page','1')
    paged_instance = Page(model_instances, page=page, items_per_page=15, **_paginate)  
    return render_template('admin/list.html',
                           _get_primary_key=_get_primary_key,
                           model_instances=paged_instance,
                           model_name=model_name,
                           pagine_string = paged_instance.pager(),
                           )


@admin.route('/add/<model_name>/', methods=['GET', 'POST'])
def generic_model_add(model_name):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)

    model = model_dict[model_name]
    model_form = form_dict[model_name]
    model_instance = model()

    if request.method == 'GET':
        new_instance = db_session.merge(model_instance)
        form = model_form(new_instance)
        return render_template('admin/add.html',
                               model_name=model_name,
                               form=form)

    elif request.method == 'POST':
        form = model_form(request.form)
        if form.validate():
            form.populate_obj(model_instance)        
            db_session.add(model_instance)
            db_session.commit()
            flash('%s added: %s' % (model_name, model_instance), 'success')
            return redirect(url_for('generic_model_list', model_name=model_name))

        else:
            flash('There are errors, see below!', 'error')
            return render_template('admin/add.html',
                                   model_name=model_name,
                                   form=form)


@admin.route('/delete/<model_name>/<model_key>/')
def generic_model_delete(model_name, model_key):
    if not model_name in model_dict.keys():
        return "%s cannot be accessed through this admin page" % (model_name,)

    model = model_dict[model_name]

    pk = _get_primary_key_column(model).key
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

    pk = _get_primary_key_column(model).key
    pk_query_dict = {pk: model_key}
    
    try:
        model_instance = model.query.filter_by(**pk_query_dict).one()
    except NoResultFound:
        return "%s not found: %s" % (model_name, model_key)

    if request.method == 'GET':
        form = model_form(obj=model_instance)
        return render_template('admin/edit.html',
                               model_instance=model_instance,
                               model_name=model_name,
                               form=form)

    elif request.method == 'POST':
        form = model_form(request.form, obj=model_instance)

        if form.validate():
            form.populate_obj(model_instance)
            db_session.add(model_instance)
            db_session.commit()
            flash('%s updated: %s' % (model_name, model_instance), 'success')
            return redirect(url_for('generic_model_list', model_name=model_name))

        else:
            flash('There are errors, see below!', 'error')
            return render_template('admin/edit.html',
                                   model_instance=model_instance,
                                   model_name=model_name,
                                   form=form)



def _get_primary_key(model):
    """
    Return the primary key value for a given model. Assumes single
    primary key.
    """
    return model.__dict__[_get_primary_key_column(model).key]


def _get_primary_key_column(model):
    """
    Return the primary key column for a given model. Assumes single
    primary key.
    """
    table = model.__table__
    if len(table.primary_key) > 1:
        return NotImplementedError, "This admin doesn't work with multiple-column primary keys"
    
    for primary_key in table.primary_key:
        return primary_key


def _get_model_from_column(column):
    for model in model_dict.values():
        if column.name in model.__table__.c:
            return model


def _form_for_model(model_class):
    """
    Return a form for a given model. This will be a form generated by
    wtforms.ext.sqlalchemy.model_form, but decorated with a
    QuerySelectField for foreign keys.
    """
    form = model_form(model_class)

    for foreign_key in model_class.__table__.foreign_keys:
        foreign_model = _get_model_from_column(foreign_key.column)
        
        if 'descriptive_key' in model_class.__dict__:
            label_key = foreign_model.descriptive_key.fget
        else:
            label_key = foreign_model.__repr__

        select_field = QuerySelectFieldAsPK(foreign_model.__name__,
                                            query_factory=_query_factory_for(foreign_model),
                                            allow_blank=False,
                                            get_label=label_key)

        setattr(form, foreign_key.parent.name, select_field)

    return form


def _query_factory_for(model_class):
    """
    Return a query factory for a given model_class. This looks weird,
    but it gives us an all-purpose way of generating query factories
    for QuerySelectFields.
    """
    def query_factory():
        return model_class.query.all()

    return query_factory



# -----------------------------------------------------------------------------
# Special fields
# -----------------------------------------------------------------------------
class QuerySelectFieldAsPK(QuerySelectField):
    """
    A modified QuerySelectField that returns the primary key of an
    object rather than the SQLAlchemy instance. This makes it possible
    to run form.populate_obj(model_instance) without trouble since the
    primary key is used rather than the model instance itself. There
    may be a better way to do this - but it works for now.
    """
    def post_validate(self, form, stop_validation):
        """
        After validation, switch the model instance into its primary
        key primary_key.
        """
        get_pk = self.get_pk
        self.data = get_pk(self.data)

    def iter_choices(self):
        """
        This overrides QuerySelectField's iter_choices to account for
        making the comparison on the primary_key so that when
        rendering the html widgets, the correct value starts off as
        selected.
        """
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)

        get_pk = self.get_pk
        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), unicode(get_pk(obj)) == unicode(self.data))
