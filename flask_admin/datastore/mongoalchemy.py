# -*- coding: utf-8 -*-
"""
    flask.ext.datastore.mongoalchemy
    ~~~~~~~~~~~~~~


    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import types

from mongoalchemy.document import Document
from wtforms import fields, form

from flask.ext.admin.datastore import AdminDatastore


class MongoAlchemyDatastore(AdminDatastore):
    def __init__(self, models, db_session, model_forms=None):
        self.model_classes = {}
        self.model_forms = model_forms
        self.db_session = db_session

        if not self.model_forms:
            self.model_forms = {}

        if type(models) == types.ModuleType:
            self.model_classes = dict(
                [(k, v) for k, v in models.__dict__.items()
                 if issubclass(v, Document)])
        else:
            self.model_classes = dict(
                [(model.__name__, model)
                 for model in models
                 if issubclass(model, Document)])

        if self.model_classes:
            self.form_dict = dict(
                [(k, _form_for_model(v, db_session,))
                 for k, v in self.model_classes.items()])
            for model_name, form in self.model_forms.items():
                if model_name in self.form_dict:
                    self.form_dict[model_name] = form

    def create_model_pagination(self, model_name, page, per_page=25):
        """Returns a pagination object for the list view."""
        raise NotImplementedError()

    def delete_model_instance(self, model_name, model_key):
        """Deletes a model instance. Returns True if model instance
        was successfully deleted, returns False otherwise.
        """
        raise NotImplementedError()

    def find_model_instance(self, model_name, model_key):
        """Returns a model instance, if one exists, that matches
        model_name and model_key. Returns None if no such model
        instance exists.
        """
        raise NotImplementedError()

    def get_model_class(self, model_name):
        """Returns a model class, given a model name."""
        return self.model_classes.get(model_name, None)

    def get_model_form(self, model_name):
        """Returns a form, given a model name."""
        return self.model_forms.get(model_name, None)

    def get_model_key(self, model_instance):
        """Returns the primary key for a given a model instance."""
        raise NotImplementedError()

    def list_model_names(self):
        """Returns a list of model names available in the datastore."""
        return self.model_classes.keys()

    def save_model(self, model_instance):
        """Persists a model instance to the datastore. Note: this
        could be called when a model instance is added or edited.
        """
        raise NotImplementedError()

    def update_from_form(self, model_instance, form):
        """Returns a model instance whose values have been updated
        with the values from a given form.
        """
        raise NotImplementedError()


def _form_for_model(document_class, db_session):
    """returns a wtform Form object for a given document model class.
    """
    #XXX: needs to be implemented
    return None
