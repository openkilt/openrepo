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

from apt.debfile import DebPackage
from .base_adapter import RepoFileAdapter


class DebFileAdapter(RepoFileAdapter):
    def __init__(self, filepath):
        self.filepath = filepath

        pkg = DebPackage(self.filepath)
        # import pprint
        #pprint.pprint(pkg.filelist)
        #pprint.pprint(pkg.control_filelist)

        self.control = pkg.control_content('control')
        self.pkgname = pkg._sections["Package"]
        self.architecture = pkg._sections["Architecture"]
        self.version = pkg._sections["Version"]
        self.description = pkg._sections["Description"]

        #print(pkg._sections)
        #print(f"{pkgname} {architecture} {debver}")

    def get_name(self):
        return self.pkgname

    def get_architecture(self):
        return self.architecture

    def get_version(self):
        return self.version

    def get_description(self):
        return self.description

    def get_builddate(self):
        return None


# t = DebFileAdapter('/home/mhill/Downloads/teamviewer_15.11.6_amd64.deb')
# t.info()
#
# print("--------------------")
# t = DebFileAdapter('/home/mhill/Downloads/libcudnn8_8.2.0.53-1+cuda11.3_amd64.deb')
# t.info()