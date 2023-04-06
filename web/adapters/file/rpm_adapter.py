import rpmfile
from datetime import datetime
from .base_adapter import RepoFileAdapter
from dateutil import parser
from django.conf import settings

class RpmFileAdapter(RepoFileAdapter):

    def __init__(self, filepath):
        self.filepath = filepath

        with rpmfile.open(self.filepath) as rpm:
            headers_titles = {
                "name": "Name",
                "version": "Version",
                "release": "Release",
                "arch": "Architecture",
                "group": "Group",
                "size": "Size",
                "copyright": "License",
                "signature": "Signature",
                "sourcerpm": "Source RPM",
                "buildtime": "Build Date",
                "buildhost": "Build Host",
                "url": "URL",
                "summary": "Summary",
                "description": "Description",
            }
            self.fields = {}
            for header in headers_titles:
                value = rpm.headers.get(header)
                if isinstance(value, bytes):
                    value = value.decode()
                if header == "buildtime":
                    value = datetime.fromtimestamp(value).strftime("%c")
                if header == "description":
                    value = "\n" + value

                self.fields[header] = value
                #line = "%s: %s" % (headers_titles.get(header).ljust(12), value)
                #print(line)

    def get_name(self):
        return self.fields['name']

    def get_architecture(self):
        return self.fields['arch']

    def get_version(self):
        if settings.RPM_VERSION_IGNORE_BUILD_NUM:
            return self.fields['version']
        else:
            return self.fields['version'] + "." + self.fields['release']


    def get_description(self):
        return self.fields['description']

    def get_builddate(self):
        return parser.parse(self.fields['buildtime'])

