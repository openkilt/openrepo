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
from .deb_adapter import DebFileAdapter
from .rpm_adapter import RpmFileAdapter
from .file_adapter import GenericFileAdapter
import logging

logger = logging.getLogger("openrepo_web")


def create_adapter(repo_type, filepath, original_filename):
    if repo_type == 'deb':
        return DebFileAdapter(filepath)
    elif repo_type == 'rpm':
        return RpmFileAdapter(filepath)
    elif repo_type == 'files':
        return GenericFileAdapter(filepath, original_filename)
    else:
        logger.warning(f"Unable to determine file adapter from repo type {repo_type}")
        return None