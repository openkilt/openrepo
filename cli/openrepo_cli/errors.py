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


class OpenRepoApiException(Exception):
    def __init__(self, msg, error_content=''):
        self.error_content = error_content
        return super().__init__(msg)

class ORNon200ResponseException(OpenRepoApiException):
    def __init__(self, msg, response_code, error_content=''):
        self.response_code = response_code
        return super().__init__(msg, error_content=error_content)

class ORUnauthorizedException(OpenRepoApiException):
    pass

class ORConnectionException(OpenRepoApiException):
    pass

class ORInvalidRequestException(OpenRepoApiException):
    pass