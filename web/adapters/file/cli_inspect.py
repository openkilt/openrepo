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