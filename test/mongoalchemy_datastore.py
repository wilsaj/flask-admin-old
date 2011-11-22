#!/usr/bin/env python
from __future__ import absolute_import

from unittest import TestCase
from mongoalchemy import fields
from mongoalchemy.document import Document
from flask.ext.admin.datastore.mongoalchemy import model_form
import wtforms
from wtforms.form import Form


def assert_convert(ma_field, wtf_field):
    """helper function for testing that MongoAlchemy fields get
    converted to proper wtforms fields
    """
    class TestModel(Document):
        test_field = ma_field()

    form = model_form(TestModel)

    assert form.test_field.field_class == wtf_field


class ConversionTest(TestCase):
    def test_bool_field_conversion(self):
        assert_convert(fields.BoolField, wtforms.fields.BooleanField)

    def test_datetime_field_conversion(self):
        assert_convert(fields.DateTimeField, wtforms.fields.DateTimeField)

    def test_enum_field_conversion(self):
        # TODO
        assert False

    def test_float_field_conversion(self):
        assert_convert(fields.FloatField, wtforms.fields.FloatField)

    def test_int_field_conversion(self):
        assert_convert(fields.IntField, wtforms.fields.IntegerField)

    def test_objectid_field_conversion(self):
        assert_convert(fields.ObjectIdField, wtforms.fields.TextField)

    def test_string_field_conversion(self):
        assert_convert(fields.StringField, wtforms.fields.TextField)

    def test_tuple_field_conversion(self):
        # TODO
        assert False


if __name__ == '__main__':
    from unittest import main
    main()
