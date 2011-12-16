class AdminDatastore(object):
    """A base class for admin datastore objects. All datastores used
    in Flask-Admin should subclass this object and define the
    following methods.
    """

    def create_model_pagination(self, model_name, page, per_page=25):
        """Returns a pagination object for the list view."""
        raise NotImplementedError()

    def delete_model_instance(self, model_name, model_keys):
        """Deletes a model instance. Returns True if model instance
        was successfully deleted, returns False otherwise.
        """
        raise NotImplementedError()

    def find_model_instance(self, model_name, model_keys):
        """Returns a model instance, if one exists, that matches
        model_name and model_keys. Returns None if no such model
        instance exists.
        """
        raise NotImplementedError()

    def get_model_class(self, model_name):
        """Returns a model class, given a model name."""
        raise NotImplementedError()

    def get_model_form(self, model_name):
        """Returns a form, given a model name."""
        raise NotImplementedError()

    def get_model_keys(self, model_instance):
        """Returns the keys for a given a model instance. This should
        be an iterable (e.g. list or tuple) containing the keys.
        """
        raise NotImplementedError()

    def list_model_names(self):
        """Returns a list of model names available in the datastore."""
        raise NotImplementedError()

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
