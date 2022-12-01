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

import argparse
import os
import sys
from adapters.file import create_adapter

parser = argparse.ArgumentParser(
                    prog = 'OpenRepo File Inspector',
                    description = 'Used to test File Adapters given a particular file',)

parser.add_argument('-r', '--repo_type', type=str, choices=['deb', 'rpm', 'files'], required=True)

parser.add_argument('filename')

args = parser.parse_args()

if not os.path.isfile(args.filename):
    print(f"File does not exist {args.filename}")
    sys.exit(1)

adapter = create_adapter(args.repo_type, args.filename, os.path.basename(args.filename))

print(f"File info:")
print(f"  - Name:       {adapter.get_name()}")
print(f"  - Version:    {adapter.get_version()}")
print(f"  - Build Date: {adapter.get_builddate()}")
print(f"  - Arch:       {adapter.get_architecture()}")
print(f"  - Desc:       {adapter.get_description()}")