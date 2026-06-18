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

class RepoFileAdapter:
    def __init__(self, filepath, original_filename):
        pass

    def get_name(self):
        raise NotImplementedError("Subclasses must implement get_name()")

    def get_architecture(self):
        raise NotImplementedError("Subclasses must implement get_architecture()")

    def get_version(self):
        raise NotImplementedError("Subclasses must implement get_version()")

    def get_description(self):
        raise NotImplementedError("Subclasses must implement get_description()")

    def get_builddate(self):
        raise NotImplementedError("Subclasses must implement get_builddate()")

