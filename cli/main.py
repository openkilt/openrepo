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
import logging
from pathlib import Path
from openrepo_cli.rest_interface import RestInterface
from openrepo_cli.errors import ORUnauthorizedException, ORNon200ResponseException
from openrepo_cli.output_formatter import OutputFormatter

def main():
    parser = argparse.ArgumentParser(description="OpenRepo Command Line Interface")

    subparsers = parser.add_subparsers(dest='command', help='Available OpenRepo Operations')
    subparsers.required = True

    parser.add_argument("-k", "--key", default=os.getenv('OPENREPO_APIKEY', ''), help='API key')
    parser.add_argument("-s", "--server", default=os.getenv('OPENREPO_SERVER', 'http://localhost:7376'), help="OpenRepo Server")

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug info'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Print output to JSON'
    )

    # Create a dummy interface in order to inspect the functions
    all_possible_args = {}
    dummy_interface = RestInterface('', '')
    cli_functions = dummy_interface.get_cli_functions()

    # For each API function decorated with "cli_method" create a corresponding CLI option
    for func in cli_functions:
        if func['doc'] is None:
            docstring = ''
        else:
            docstring = func['doc'].strip().partition("\n")[0]
        subparser = subparsers.add_parser(func['function_name'], help=docstring)
        for subarg in func['args'].parameters:
            if subarg not in all_possible_args:
                all_possible_args[subarg] = True
            subparser.add_argument( f"--{subarg}", required=True, type=str)


    ## Upload CLI options
    # Upload is handled specially because the arguments (e.g., multiple file paths) is a little different
    subparser_upload = subparsers.add_parser("upload", help="Upload package file to OpenRepo")

    subparser_upload.add_argument("-r", "--repo_uid", help="Unique ID of repo to upload to", required=True, type=str)

    subparser_upload.add_argument("filepath", help="path of file(s) to upload", nargs='+',
                                  type=str)


    args = parser.parse_args()

    # create logger
    logger = logging.getLogger('openrepo_cli')
    ch = logging.StreamHandler(stream=sys.stdout)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')

    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    interface = RestInterface(args.server, args.key)

    try:
        response_content = ''
        if args.command == 'upload':
            count = 0
            for filepath in args.filepath:
                count += 1
                logger.debug(f"Uploading file {filepath} ({count} of {len(args.filepath)})")

                if not Path(filepath).is_file():
                    logger.warning(f"File does not exist {filepath}")
                    continue
                response_content = interface.upload(repo_uid=args.repo_uid, filepath=filepath)

        else:
            # CLI args were auto generated from rest_interface function names
            # Apply the kwargs and exec the functions based on the string name
            function = getattr(interface, args.command)
            func_args = vars(args).copy()
            # Delete global args so it won't confuse function
            for k,v in func_args.copy().items():
                if k not in all_possible_args:
                    del func_args[k]

            response_content = function(**func_args)


        output_format = OutputFormatter(args.json)
        output_format.print(response_content, args.command)

    except ORUnauthorizedException:
        logger.error("Unauthorized request.  Are you sure your API key is correct?")
        return False

    except ORNon200ResponseException as e:
        logger.error(f"Error.  Received response code {e.response_code}")
        logger.error(e.error_content)
        return False

    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)