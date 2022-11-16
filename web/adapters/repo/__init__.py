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

from .deb_repo import DepRepoAdapter
from .rpm_repo import RpmRepoAdapter
from .generic_repo import GenericRepoAdapter

def get_repo_adapter(repo_obj):
    if repo_obj.repo_type == 'deb':
        return DepRepoAdapter(repo_obj)
    elif repo_obj.repo_type == 'rpm':
        return RpmRepoAdapter(repo_obj)
    elif repo_obj.repo_type == 'files':
        return GenericRepoAdapter(repo_obj)
    raise Exception("Not implemented")