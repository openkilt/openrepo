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
import os
import shutil
import time
import subprocess
from django.conf import settings
from repo.models import Repository, Package, Build, BuildLogLine
from repo.storage.keyring import PGPKeyring
logger = logging.getLogger("openrepo_web")


class BuildLogEntry():
    '''
    Used to annotate sections of work during the build process.  Execution time is recorded,
    and messages are updated on the db after the command is written so that the web ui can display
    in real-time
    '''
    def __init__(self, command, log_line, repo_uid):
        self.start_timestamp = time.time()
        self.command = command
        self.log_line = log_line
        self.repo_uid = repo_uid

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.log_line.execution_time_sec = time.time() - self.start_timestamp
        self.log_line.exec_complete = True

        self.log_line.save()

    def set_message(self, message):
        self.log_line.message = message
        logger.info(f"build {self.repo_uid}: {message}")

    def set_loglevel(self, loglevel):
        self.log_line.loglevel = loglevel



class BaseRepoAdapter:

    BUILDLOG_DEBUG = 'debug'
    BUILDLOG_INFO = 'info'
    BUILDLOG_WARNING = 'warning'
    BUILDLOG_ERROR = 'error'

    def __init__(self, repo_db_obj):

        self.repo_uid = repo_db_obj.repo_uid
        self.pgp_key = repo_db_obj.signing_key

        self.build = None
        self.log_number = 0



    def _copy_packages(self, dest_dir):

        with self._buildlog_section(f"Symlinking {len(self.packages)} packages") as log_entry:
            for package in self.packages:
                src_sym = os.path.join(settings.STORAGE_PATH, package.relative_path())
                dst_sym = os.path.join(dest_dir, package.filename)
                logger.debug(f"Symlinking {src_sym} to {dst_sym}")
                if not os.path.isfile(src_sym):
                    log_entry.set_message(f"Unable to find source package file {src_sym}")

                os.symlink(src_sym, dst_sym)

    def _buildlog_write(self, command, message='', loglevel=BUILDLOG_INFO, is_complete=True):
        '''
        Write a message to the build log so that the status can be monitored
        :param command: The CLI command, or the intention of the operatoin
        :param message: The CLI response or outcome from the operation
        :param loglevel: level of log message.  Controls filtering/coloring in web output
        :return:
        '''

        log_line = BuildLogLine()
        log_line.build = self.build
        log_line.command = command
        log_line.message = message
        log_line.loglevel = loglevel
        log_line.line_number = self.log_number
        log_line.exec_complete = is_complete
        self.log_number += 1
        log_line.save()

        logger.info(f"build {self.repo_uid}: {loglevel} {command} {message}")

        return log_line

    def _buildlog_section(self, command, loglevel=BUILDLOG_INFO):
        '''
        Meant to be run as a "with" statement to auto log start of sections
        :param command: Section name
        :param loglevel:
        :return:
        '''
        log_line = self._buildlog_write(command, loglevel=loglevel, is_complete=False)
        return BuildLogEntry(command, log_line, self.repo_uid)

    def _generate_repo_structure(self, repo_path):
        '''
        Implement this for each repo adapter.  The task should fully generate the repository metadata
        to 'copy' files into the repo folders, call self._copy_packages()
        :param repo_path: The path to the repo folder to generate the metadata
        :return:
        '''
        raise Exception("This function should always be implemented in child class for a particular repo")

    def _get_repo_instructions(self):
        '''
        Return a relevant address for the Repo.  Ideally this would be the full config option that can be copied/pasted
        to configure the repo.
        :return:
        '''
        raise Exception("This function should always be implemented in child class for a particular repo")

    def _clean_old_dirs(self, cur_repo_dir):

        alldirs = os.listdir(settings.REPO_WWW_PATH)
        prefix = f'{self.repo_uid}.'
        for d in alldirs:
            if d.startswith(prefix) and d != cur_repo_dir:
                fullpath = os.path.join(settings.REPO_WWW_PATH, d)
                logger.debug(f"Removing old repo dir {fullpath}")
                shutil.rmtree(fullpath)

    def _save_public_key(self, repo_path):

        # Export the public key to the repo for convenience
        with self._buildlog_section("Updating PGP keys") as log_entry:
            pgp_output_path = os.path.join(repo_path, 'public.gpg')
            with open(pgp_output_path, 'w') as outf:
                self._buildlog_write(f"Writing PGP key to {pgp_output_path}")
                outf.write(self.pgp_key.public_key_pem)

    def _execute_commands(self, commands, repo_path):

        working_dir = repo_path
        custom_env = os.environ.copy()
        custom_env['GNUPGHOME'] = settings.KEYRING_PATH

        for command in commands:
            with self._buildlog_section(command) as log_entry:
                proc_status = subprocess.run(command, cwd=working_dir, env=custom_env, stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, text=True, shell=True)
                message_output = proc_status.stdout

                log_entry.set_message(message_output)
                if proc_status.returncode != 0:
                    # Error code
                    log_entry.set_loglevel(self.BUILDLOG_WARNING)
                    return False

        return True

    def setup_repo(self):

        # Ensure PGP key is prepped and ready
        if self.pgp_key is not None:
            self.gpg = PGPKeyring()
            self.gpg.ensure_key(self.pgp_key)

        self.packages = Package.objects.filter(repo__repo_uid=self.repo_uid)

        # First increment the count for this repo
        repo_db_obj = Repository.objects.get(repo_uid=self.repo_uid)
        repo_db_obj.refresh_count = repo_db_obj.refresh_count + 1
        repo_db_obj.save()

        self.log_number = 0
        self.build = Build()
        self.build.repo = repo_db_obj
        self.build.build_number = repo_db_obj.refresh_count
        self.build.completion_status = Build.STATUS_RUNNING
        self.build.save()

        success = False
        try:
            # Format is repo_uid.refresh_count with 9 digits of 0 padding
            dirname = f'{self.repo_uid}.{repo_db_obj.refresh_count:=09}'
            dest_dir = os.path.join(settings.REPO_WWW_PATH, dirname)

            if os.path.exists(dest_dir):
                with self._buildlog_section(f"Removing old directory path {dest_dir}") as log_entry:
                    shutil.rmtree(dest_dir)

            # Create directory path for repo
            os.makedirs(dest_dir)

            self._buildlog_write(f"Generating repo structure {dest_dir}")
            success = self._generate_repo_structure(dest_dir)
            self._buildlog_write(f"Create repo complete {dest_dir}", success)

            # In the case of a refresh, assuming this is refresh num 2 then we now have 3 directories:
            # 1. the repo_uid.000001 directory
            # 2. the repo_uid.000002 directory
            # 3. the repo_uid directory symlinked to repo_uid.000001
            #
            # We need to update the symlink, and delete all old directories earlier than 00002

            if success:
                self.build.completion_status = Build.STATUS_COMPLETE_SUCCESS
                self.build.save()
                with self._buildlog_section(f"Updating repo symlink to point to {dirname}") as log_entry:
                    repo_uid_symlink = os.path.join(settings.REPO_WWW_PATH, self.repo_uid)
                    if os.path.exists(repo_uid_symlink):
                        os.unlink(repo_uid_symlink)

                    os.symlink(dirname, repo_uid_symlink)

                with self._buildlog_section(f"Cleaning old directories in {settings.REPO_WWW_PATH}") as log_entry:
                    self._clean_old_dirs(dirname)
            else:
                self.build.completion_status = Build.STATUS_COMPLETE_ERROR

        except Exception as e:
            self._buildlog_write(f"Exception processing repo {self.repo_uid}", e, loglevel=self.BUILDLOG_ERROR)
            success = False

        if success:
            self.build.completion_status = Build.STATUS_COMPLETE_SUCCESS
        else:
            self.build.completion_status = Build.STATUS_COMPLETE_ERROR
        self.build.save()

        return success
