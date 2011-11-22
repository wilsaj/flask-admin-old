#!/usr/bin/env python
from __future__ import absolute_import

from unittest import TestCase
from mongoalchemy import fields as ma_fields
from mongoalchemy.document import Document
from flask.ext.admin.datastore.mongoalchemy import model_form
from wtforms import fields as wtf_fields
from wtforms.form import Form


def assert_convert(ma_field, wtf_field):
    """helper function for testing that MongoAlchemy fields get
    converted to proper wtforms fields
    """
    class TestModel(Document):
        required_field = ma_field(required=True)
        not_required_field = ma_field(required=False)

    form = model_form(TestModel)

    assert form.required_field.field_class == wtf_field

    not_required_validator_names = [
        validator.__class__.__name__
        for validator in form.not_required_field.kwargs['validators']]

    assert 'Optional' in not_required_validator_names


def assert_min_max_number_range(ma_field):
    class TestModel(Document):
        min_field = ma_field(min_value=5)
        max_field = ma_field(max_value=19)
        min_max_field = ma_field(min_value=11, max_value=21)

    form = model_form(TestModel)
    min_validator = [
        validator for validator in form.min_field.kwargs['validators']
        if validator.__class__.__name__ == 'NumberRange'][0]
    max_validator = [
        validator for validator in form.max_field.kwargs['validators']
        if validator.__class__.__name__ == 'NumberRange'][0]
    min_max_validator = [
        validator for validator in form.min_max_field.kwargs['validators']
        if validator.__class__.__name__ == 'NumberRange'][0]

    assert min_validator.min == 5
    assert not min_validator.max
    assert max_validator.max == 19
    assert not max_validator.min
    assert min_max_validator.min == 11
    assert min_max_validator.max == 21


def assert_min_max_length(ma_field):
    class TestModel(Document):
        min_field = ma_field(min_length=5)
        max_field = ma_field(max_length=19)
        min_max_field = ma_field(min_length=11, max_length=21)

    form = model_form(TestModel)
    min_validator = [
        validator for validator in form.min_field.kwargs['validators']
        if validator.__class__.__name__ == 'Length'][0]
    max_validator = [
        validator for validator in form.max_field.kwargs['validators']
        if validator.__class__.__name__ == 'Length'][0]
    min_max_validator = [
        validator for validator in form.min_max_field.kwargs['validators']
        if validator.__class__.__name__ == 'Length'][0]

    assert min_validator.min == 5
    assert min_validator.max == -1
    assert max_validator.max == 19
    assert max_validator.min == -1
    assert min_max_validator.min == 11
    assert min_max_validator.max == 21


class ConversionTest(TestCase):
    def test_bool_field_conversion(self):
        assert_convert(ma_fields.BoolField, wtf_fields.BooleanField)

    def test_datetime_field_conversion(self):
        assert_convert(ma_fields.DateTimeField, wtf_fields.DateTimeField)

    def test_enum_field_conversion(self):
        assert False

    def test_float_field_conversion(self):
        assert_convert(ma_fields.FloatField, wtf_fields.FloatField)
        assert_min_max_number_range(ma_fields.IntField)

    def test_int_field_conversion(self):
        assert_convert(ma_fields.IntField, wtf_fields.IntegerField)
        assert_min_max_number_range(ma_fields.IntField)

    def test_objectid_field_conversion(self):
        assert_convert(ma_fields.ObjectIdField, wtf_fields.TextField)

    def test_string_field_conversion(self):
        assert_convert(ma_fields.StringField, wtf_fields.TextField)
        assert_min_max_length(ma_fields.StringField)

    def test_tuple_field_conversion(self):
        # TODO
        assert False


if __name__ == '__main__':
    from unittest import main
    main()
