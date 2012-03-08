# -*- coding: utf-8 -*-
"""
    flask.ext.datastore.mongoalchemy
    ~~~~~~~~~~~~~~


    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import types

import mongoalchemy as ma
from mongoalchemy.document import Document
from wtforms import fields as f
from wtforms import form, validators, widgets
from wtforms.form import Form

from flask.ext.admin.datastore import AdminDatastore
from flask.ext.admin import wtforms as admin_wtf
from flask.ext.admin import util


class MongoAlchemyDatastore(AdminDatastore):
    """A datastore for accessing MongoAlchemy document models.

    The `models` parameter should be either a module or an iterable
    that contains the MongoAlchemy models that will be made available
    through the admin interface.

    `db_session` should be an initialized MongoAlchemy session
    object. See the `MongoAlchemy documentation`_ for information on
    how to do that.

    By default, a form for adding and editing data will be
    automatically generated for each MongoAlchemy model. Only
    primitive MongoAlchemy types are supported so if you need to
    support other fields you will need to create custom forms. You can
    also use custom forms if you want more control over form behavior.
    To use custom forms, set the `model_forms` parameter to be a dict
    with model names as keys matched to custom forms for the forms you
    want to override. Forms should be WTForms form objects; see the
    `WTForms documentation`_ for more information on how to configure
    forms.

    A dict with model names as keys, mapped to WTForm Form objects
    that should be used as forms for creating and editing instances of
    these models.

    .. _MongoAlchemy documentation: http://www.mongoalchemy.org/api/session.html
    .. _WTForms documentation: http://wtforms.simplecodes.com/
    """
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
        model_class = self.get_model_class(model_name)
        query = self.db_session.query(model_class).skip(
            (page - 1) * per_page).limit(per_page)
        return MongoAlchemyPagination(page, per_page, query)

    def delete_model_instance(self, model_name, model_keys):
        """Deletes a model instance. Returns True if model instance
        was successfully deleted, returns False otherwise.
        """
        model_class = self.get_model_class(model_name)
        try:
            model_instance = self.find_model_instance(model_name, model_keys)
            self.db_session.remove(model_instance)
            return True
        except ma.query.BadResultException:
            return False

    def find_model_instance(self, model_name, model_keys):
        """Returns a model instance, if one exists, that matches
        model_name and model_keys. Returns None if no such model
        instance exists.
        """
        model_key = model_keys[0]
        model_class = self.get_model_class(model_name)
        return self.db_session.query(model_class).filter(
            model_class.mongo_id == model_key).one()

    def get_model_class(self, model_name):
        """Returns a model class, given a model name."""
        return self.model_classes.get(model_name, None)

    def get_model_form(self, model_name):
        """Returns a form, given a model name."""
        return self.form_dict.get(model_name, None)

    def get_model_keys(self, model_instance):
        """Returns the keys for a given a model instance."""
        return [model_instance.mongo_id]

    def list_model_names(self):
        """Returns a list of model names available in the datastore."""
        return self.model_classes.keys()

    def save_model(self, model_instance):
        """Persists a model instance to the datastore. Note: this
        could be called when a model instance is added or edited.
        """
        return model_instance.commit(self.db_session.db)

    def update_from_form(self, model_instance, form):
        """Returns a model instance whose values have been updated
        with the values from a given form.
        """
        for field in form:
            # handle FormFields that were generated for mongoalchemy
            # TupleFields as a special case
            if field.__class__ == f.FormField:
                data_tuple = tuple([subfield.data for subfield in field])
                setattr(model_instance, field.name, data_tuple)
                continue

            # don't use the mongo id from the form - it comes from the
            # key/url and if someone tampers with the form somehow, we
            # should ignore that
            elif field.name != 'mongo_id':
                setattr(model_instance, field.name, field.data)
        return model_instance


class MongoAlchemyPagination(util.Pagination):
    def __init__(self, page, per_page, query, *args, **kwargs):
        super(MongoAlchemyPagination, self).__init__(
            page, per_page, total=query.count(), items=query.all(),
            *args, **kwargs)


def _form_for_model(document_class, db_session):
    """returns a wtform Form object for a given document model class.
    """
    #XXX: needs to be implemented
    return model_form(document_class)


#-----------------------------------------------------------------------
# mongo alchemy form generation: to be pushed upstream
#-----------------------------------------------------------------------
class DisabledTextInput(widgets.TextInput):
    def __call__(self, field, **kwargs):
        kwargs['disabled'] = 'disabled'
        return super(DisabledTextInput, self).__call__(field, **kwargs)


def converts(*args):
    def _inner(func):
        func._converter_for = frozenset(args)
        return func
    return _inner


class ModelConverterBase(object):
    def __init__(self, converters, use_mro=True):
        self.use_mro = use_mro

        if not converters:
            converters = {}

        for name in dir(self):
            obj = getattr(self, name)
            if hasattr(obj, '_converter_for'):
                for classname in obj._converter_for:
                    converters[classname] = obj

        self.converters = converters

    def convert(self, model, ma_field, field_args):
        default = getattr(ma_field, 'default', None)

        if default == ma.util.UNSET:
            default = None

        kwargs = {
            'validators': [],
            'filters': [],
            'default': default,
        }

        if field_args:
            kwargs.update(field_args)

        if not ma_field.required:
            kwargs['validators'].append(validators.Optional())

        types = [type(ma_field)]

        converter = None
        for ma_field_type in types:
            type_string = '%s.%s' % (
                ma_field_type.__module__, ma_field_type.__name__)
            if type_string.startswith('mongoalchemy.fields'):
                type_string = type_string[20:]

            if type_string in self.converters:
                converter = self.converters[type_string]
                break
        else:
            for ma_field_type in types:
                if ma_field_type.__name__ in self.converters:
                    converter = self.converters[ma_field_type.__name__]
                    break
            else:
                return
        return converter(model=model, ma_field=ma_field, field_args=kwargs)


class ModelConverter(ModelConverterBase):
    def __init__(self, extra_converters=None):
        super(ModelConverter, self).__init__(extra_converters)

    @converts('BoolField')
    def conv_Bool(self, ma_field, field_args, **extra):
        return f.BooleanField(**field_args)

    @converts('DateTimeField')
    def conv_DateTime(self, ma_field, field_args, **extra):
        # TODO: add custom validator for date range
        field_args['widget'] = admin_wtf.DateTimePickerWidget()
        return f.DateTimeField(**field_args)

    @converts('EnumField')
    def conv_Enum(self, model, ma_field, field_args, **extra):
        converted_field = self.convert(model, ma_field.item_type, {})
        converted_field.kwargs['validators'].append(
            validators.AnyOf(ma_field.values, values_formatter=str))
        return converted_field

    @converts('FloatField')
    def conv_Float(self, ma_field, field_args, **extra):
        if ma_field.min or ma_field.max:
            field_args['validators'].append(
                validators.NumberRange(min=ma_field.min, max=ma_field.max))
        return f.FloatField(**field_args)

    @converts('IntField')
    def conv_Int(self, ma_field, field_args, **extra):
        if ma_field.min or ma_field.max:
            field_args['validators'].append(
                validators.NumberRange(min=ma_field.min, max=ma_field.max))
        return f.IntegerField(**field_args)

    @converts('ObjectIdField')
    def conv_ObjectId(self, field_args, **extra):
        widget = DisabledTextInput()
        return f.TextField(widget=widget, **field_args)

    @converts('StringField')
    def conv_String(self, ma_field, field_args, **extra):
        if ma_field.min or ma_field.max:
            min = ma_field.min or -1
            max = ma_field.max or -1
            field_args['validators'].append(
                validators.Length(min=min, max=max))
        return f.TextField(**field_args)

    @converts('TupleField')
    def conv_Tuple(self, model, ma_field, field_args, **extra):
        def convert_field(field):
            return self.convert(model, field, {})
        fields = map(convert_field, ma_field.types)
        fields_dict = dict([('%s_%s' % (ma_field._name, i), field)
                            for i, field in enumerate(fields)])

        class ConvertedTupleForm(Form):
            def process(self, formdata=None, obj=None, **kwargs):
                # if the field is being populated from a mongoalchemy
                # TupleField, obj will be a tuple object so we can set
                # the fields by reversing the field name to get the
                # index and then passing that along to wtforms in the
                # kwargs dict
                if type(obj) == tuple:
                    for name, field in self._fields.items():
                        tuple_index = int(name.split('_')[-1])
                        kwargs[name] = obj[tuple_index]
                super(ConvertedTupleForm, self).process(
                    formdata, obj, **kwargs)

        fields_form = type(ma_field._name + 'Form', (ConvertedTupleForm,), fields_dict)
        return f.FormField(fields_form)


def model_fields(model, only=None, exclude=None, field_args=None,
                 converter=None):
    """
    Generate a dictionary of fields for a given MongoAlchemy model.

    See `model_form` docstring for description of parameters.
    """
    if not issubclass(model, Document):
        raise TypeError('model must be a mongoalchemy document model')

    converter = converter or ModelConverter()
    field_args = field_args or {}

    ma_fields = ((name, field) for name, field in model.get_fields().items())
    if only:
        ma_fields = (x for x in ma_fields if x[0] in only)
    elif exclude:
        ma_fields = (x for x in ma_fields if x[0] not in exclude)

    field_dict = {}
    for name, field in ma_fields:
        wtfield = converter.convert(model, field, field_args.get(name))
        if wtfield is not None:
            field_dict[name] = wtfield

    return field_dict


def model_form(model, base_class=Form, only=None, exclude=None,
               field_args=None, converter=None):
    """
    Create a wtforms Form for a given MongoAlchemy model class::

        from wtforms.ext.mongoalchemy.orm import model_form
        from myapp.models import User
        UserForm = model_form(User)

    :param model:
        A MongoAlchemy mapped model class.
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param only:
        An optional iterable with the property names that should be included in
        the form. Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to keyword arguments used
        to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """
    field_dict = model_fields(model, only, exclude, field_args, converter)
    return type(model.__name__ + 'Form', (base_class, ), field_dict)
