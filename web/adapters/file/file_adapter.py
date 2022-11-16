# Copyright 2022 by Open Kilt LLC. All rights reserved.
# This file is part of the OpenRepo Repository Management Software (OpenRepo)
# OpenRepo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License
# version 3 as published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


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
