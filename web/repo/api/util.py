
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse
from django.urls import NoReverseMatch
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
import hashlib

class ParameterisedHyperlinkedIdentityField(HyperlinkedIdentityField):
    """
    Represents the instance, or a property on the instance, using hyperlinking.

    lookup_fields is a tuple of tuples of the form:
        ('model_field', 'url_parameter')
    """
    lookup_fields = (('pk', 'pk'),)

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', self.lookup_fields)
        super(ParameterisedHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        kwargs = {}
        for model_field, url_param in self.lookup_fields:
            attr = obj
            for field in model_field.split('.'):
                attr = getattr(attr,field)
            kwargs[url_param] = attr

        try:
            return reverse(view_name, kwargs=kwargs, request=request, format=format)
        except NoReverseMatch:
            pass

        raise NoReverseMatch()

class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            # Handle foreign key lookups (e.g., repo__repo_uid)
            if "__" in field:
                actual_field = field.split("__")[1]
                filter[field] = self.kwargs[actual_field]
            elif self.kwargs[field]: # Ignore empty fields.
                filter[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter)  # Lookup the object
        self.check_object_permissions(self.request, obj)
        return obj



def reduce_to_uid(full_name):
    """
    Takes a string value and removes special characters and spaces, drops all to lowercase
    :param full_name:
    :return:
    """

    cleaned = slugify(full_name)
    return cleaned

def compute_sha512(filepath):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha512 = hashlib.sha512()

    with open(filepath, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha512.update(data)

    return sha512.hexdigest()
