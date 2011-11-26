# -*- coding: utf-8 -*-
"""
    flask.ext.wtforms
    ~~~~~~~~~~~~~~


    :copyright: (c) 2011 by wilsaj.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import datetime
import time

from wtforms import fields as wtf_fields
from wtforms import widgets, validators


class TimeField(wtf_fields.Field):
    """A text field which stores a `time.time` matching a format."""
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
    """TextInput widget that adds a 'datetimepicker' class to the html
    adds a UI widget for datetime picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datetimepicker %s' % c
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class TimePickerWidget(widgets.TextInput):
    """TextInput widget that adds a 'timepicker' class to the html
    input element; this makes it easy to write a jQuery selector that
    adds a UI widget for time picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'timepicker %s' % c
        return super(TimePickerWidget, self).__call__(field, **kwargs)


def has_file_field(form):
    """Test whether or not a form has a FileField in it. This is used
    to know whether or not we need to set enctype to
    multipart/form-data.
    """
    for field in form:
        if isinstance(field, wtf_fields.FileField):
            return True

    return False
