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

import logging

logger = logging.getLogger("openrepo_web")


class RepoFileAdapter:
    def __init__(self, filepath, original_filename):
        pass

    def get_name(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_architecture(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_version(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_description(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_builddate(self):
        logger.warning("This function should never be called directly, only subclasses")

