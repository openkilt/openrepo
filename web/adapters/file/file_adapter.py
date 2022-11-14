
from .base_adapter import RepoFileAdapter
import re

class GenericFileAdapter(RepoFileAdapter):
    def __init__(self, filepath, original_filename):
        self.filepath = filepath
        self.original_filename = original_filename


    def get_name(self):
        return self.original_filename

    def get_architecture(self):
        return "any"

    def get_version(self):
        # Try finding the first "x.y.z" value from the filename to guess the version number
        matches = re.findall('\d+\.\d+\.\d+', self.original_filename)
        if len(matches) > 0:
            return matches[0]
        return ""

    def get_description(self):
        return ""

    def get_builddate(self):
        return None
