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

from .base_repo import BaseRepoAdapter
from django.conf import settings


class GenericRepoAdapter(BaseRepoAdapter):
    def _get_repo_instructions(self):
        return f'{self.base_url}'


    def _generate_repo_structure(self, repo_path):

        # Symlink all files in the repo
        self._copy_packages(repo_path)

        # TODO:
        # 1. Build a single-page HTML that lists all files with attributes and is searchable via JS
        # 2. Sign the index file with PGP key
        # 3. Write the PGP key to the directory
        # 4. Write a .md5 file for each generic file in the repo containing the MD5 hash

        return True