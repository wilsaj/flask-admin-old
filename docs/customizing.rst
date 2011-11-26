Custom Templates and Static Files
---------------------------------

Using Flask blueprints makes customizing the admin interface really
easy. Flask-Admin comes with a default set of templates and static
files. You can customize as much of the interface as you'd like by
just overriding any files you'd like to change. Just create your own
version of the files in the templates and/or static directories of
your app. Refer to the documentation on Flask blueprints for
more. There is also an example of this in the `view decorator
example`_.


Custom Forms
------------

Flask-Admin uses the WTForms library to automatically generate the
form that will be used to add a new instance of a model or edit an
existing model instance. There may be cases where the automatically
generated form isn't what you want, so you can also create a custom
form for Flask-Admin to use for a given model.

For example, consider the following model of a User that stores hashed
passwords::

    from sqlalchemy import Boolean, Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class User(Base):
        __tablename__ = 'user'

        id = Column(Integer, primary_key=True)
        username = Column(String(80), unique=True)
        _password_hash = Column('password', String(80), nullable=False)
        is_active = Column(Boolean, default=True)

        def __init__(self, username="", password="", is_active=True):
            self.username = username
            self.password = password
            self.is_active = is_active

        def check_password(self, password):
            return check_password_hash(self.pw_hash, password)

        @property
        def password(self):
            return self._password_hash

        @password.setter
        def password(self, password):
            self._password_hash = generate_password_hash(password)

        password = synonym('_password_hash', descriptor=password)

        def __repr__(self):
            return self.username


To allow this model to be used with a typical password and
confirmation field form, you could create the following form::

    from wtforms import Form, validators
    from wtforms.fields import BooleanField, TextField, PasswordField

    class UserForm(Form):
        """
        Form for creating or editting User object (via the admin). Define
        any handling of fields here. This form class also has precedence
        when rendering forms to a webpage, so the model-generated fields
        will come after it.
        """
        username = TextField(u'User name',
                             [validators.required(),
                              validators.length(max=80)])
        password = PasswordField('Change Password',
                                 [validators.optional(),
                                  validators.equal_to('confirm_password')])
        confirm_password = PasswordField()
        is_active = BooleanField(default=True)


And just use the model_forms argument when calling
:func:`SQLAlchemyDatastore` to associate this form with the User
model::

    admin_blueprint = admin.datastore.SQLAlchemyDatastore(
        (User,), db_session, model_forms={'User': UserForm})


Now the :class:`UserForm` will be used for editing and adding a new
user. If the form passes the validation checks, then password will
propagate to the User model and will be hashed and stored the password
in the database.

.. note::
   Due to the way that forms are generated, the order of input fields
   is difficult to control. This is something that is expected to
   improve in future versions, but for now a custom form is also the
   only way to specify the order of form fields.


.. _view decorator example: https://github.com/wilsaj/flask-admin/tree/master/example/authentication/view_decorator.py
