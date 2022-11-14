from django.conf import settings
import random
import string
import os

class RepoFileManager:

    def __init__(self):
        pass

    def _generate_random_filename(self):
        letters = string.ascii_lowercase
        path_prefix = ''.join(random.choice(letters) for i in range(settings.STORAGE_PREFIX_DEPTH))
        filename = ''.join(random.choice(letters) for i in range(settings.STORAGE_FILENAME_LENGTH))

        return os.path.join(path_prefix, filename)

    def delete(self, relative_path):

        full_filepath = os.path.join(settings.STORAGE_PATH, relative_path)
        if os.path.isfile(full_filepath):
            os.remove(full_filepath)

    def get_filepath(self):

        filepath = self._generate_random_filename()
        # On the exceedingly rare chance there is a file name collision from random generation, retry
        while os.path.isfile(os.path.join(settings.STORAGE_PATH, filepath)):
            filepath = self._generate_random_filename()

        # Check if the directory exists, create it if not
        fulldir = os.path.dirname(os.path.join(settings.STORAGE_PATH, filepath))
        if not os.path.isdir(fulldir):
            os.makedirs(fulldir)

        return filepath
