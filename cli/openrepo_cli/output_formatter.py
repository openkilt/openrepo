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
import json
from prettytable import PrettyTable
from prettytable import PLAIN_COLUMNS, SINGLE_BORDER

logger = logging.getLogger('openrepo_cli')


class OutputFormatter:
    def __init__(self, output_json):
        self.output_json = output_json

    def _tabular(self, fields, data, sortby=None):
        out_table = PrettyTable()
        out_table.set_style(SINGLE_BORDER)

        out_table.field_names = fields
        for item in data:
            row = []
            for field in fields:
                row.append(item[field])
            out_table.add_row(row)

        logger.info("\n" + out_table.get_string(sortby=sortby))

    def _properties(self, props):
        # Print properties of an object (e.g., a repo).  Use a table, but each row is an obj from the
        # server JSON response

        out_table = PrettyTable()
        out_table.set_style(SINGLE_BORDER)

        out_table.field_names = ['property', 'value']
        out_table.align["property"] = "r"
        out_table.align["value"] = "l"
        for k,v in props.items():
            out_table.add_row([k,v])

        logger.info("\n" + out_table.get_string(sortby='property'))

    def print(self, data, operation):
        if self.output_json:
            logger.info(json.dumps(data, indent=2))
            return

        if operation == 'repo_details':
            self._properties(data)

        elif operation == 'list_repos':
            fields = ['repo_uid', 'repo_type', 'package_count', 'last_updated']
            self._tabular(fields, data['results'], sortby='repo_uid')

        elif operation == 'list_packages':
            fields = ['package_name', 'filename', 'version', 'architecture', 'upload_date', 'package_uid']
            self._tabular(fields, data['results'], sortby='package_name')

        elif operation == 'list_signingkeys':
            fields = ['name', 'email', 'fingerprint', 'creation_date']
            self._tabular(fields, data['results'], sortby='fingerprint')

        else:
            # Guess what type of data it is and format it appropriately
            if data == {}:
                pass
            elif 'count' in data and 'next' in data and 'previous' in data:
                # This is a list
                if len(data['results']) > 0:
                    fields = data['results'][0].keys()
                    self._tabular(fields, data['results'])
            else:
                # Assume this has properties
                self._properties(data)




