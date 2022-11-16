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

from django.db import models
import logging
from django.contrib.auth.models import User

logger = logging.getLogger("openrepo_web")


class PGPSigningKey(models.Model):

    def __str__(self):
        return f'{self.name} <{self.email}> - {self.fingerprint[-16:]}'

    name = models.CharField(max_length=65536)
    email = models.CharField(max_length=2048)

    fingerprint = models.CharField(db_index=True, unique=True, max_length=65535)
    private_key_pem = models.CharField(max_length=65536)
    public_key_pem = models.CharField(max_length=65536)

    creation_date = models.DateTimeField(auto_now_add=True, blank=True)


class Repository(models.Model):

    REPO_TYPES = [
        ('deb', 'Debian/APT'),
        ('rpm', 'Red Hat/RPM'),
        ('files', 'Generic Files')
    ]


    class Meta:
        verbose_name_plural = "repositories"

    def __str__(self):
        return self.repo_uid

    repo_uid = models.CharField(db_index=True, unique=True, max_length=1024)

    write_access = models.ManyToManyField(User)

    # e.g., apt, rpm, simple, etc.
    repo_type = models.CharField(max_length=128, choices=REPO_TYPES, db_index=True)

    signing_key = models.ForeignKey(PGPSigningKey, blank=True, null=True, on_delete=models.PROTECT)
    promote_to = models.ForeignKey("self", blank=True, null=True, on_delete=models.CASCADE)

    # When a newer package of the same name is uploaded, delete the older versions
    keep_only_latest = models.BooleanField(default=False)

    package_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now_add=True, blank=True)

    # Flag to indicate that a change to a package was made and the repo needs to be regenerated
    is_stale = models.BooleanField(default=False, db_index=True)
    # When a repo is updated, rather than delete the current repo and regenerate, we create a new folder
    # and swap out the symlink when the regen is completed.
    # Naming convention would be repo_uid-refresh_count
    refresh_count = models.BigIntegerField(default=0)


# Packages are copied whenever they're moved to a new repo
# On delete of packages, check if there are any other references with the same "package_uid" if not, delete the file from disk
class Package(models.Model):

    # Package UID refers to a single file on disk.  The reference can exist in many repos
    # repo + package_uid is guaranteed unique
    package_uid = models.CharField(db_index=True, max_length=65536)

    repo = models.ForeignKey(Repository, on_delete=models.CASCADE)

    # Original name of package
    filename = models.CharField(max_length=65536)

    # The name of the package without the version string
    package_name = models.CharField(db_index=True, max_length=65536)

    architecture = models.CharField(max_length=256, db_index=True)

    version = models.CharField(db_index=True, max_length=65536)
    build_date = models.DateTimeField(null=True, blank=True)
    upload_date = models.DateTimeField()
    checksum_sha512 = models.CharField(db_index=True, max_length=512)

    # Where the file is located on disk relative to the base pool dir (e.g., aa/axbpoiergm)
    def relative_path(self):
        return self.package_uid.replace("-", "/")

    class Meta:
        unique_together = (('package_uid', 'repo',),
                           ('repo', 'package_name', 'version', ))


class Mirror(models.Model):
    # Don't allow the repo to be deleted without first deleting the mirror(s)
    repo = models.ForeignKey(Repository, on_delete=models.PROTECT)


class Build(models.Model):
    repo = models.ForeignKey(Repository, db_index=True, on_delete=models.CASCADE)
    build_number = models.BigIntegerField(db_index=True)

    timestamp = models.DateTimeField(db_index=True, auto_now_add=True, blank=True)

    STATUS_RUNNING = 'running'
    STATUS_COMPLETE_SUCCESS = 'complete_success'
    STATUS_COMPLETE_ERROR = 'complete_fail'
    completion_status = models.CharField(default='running',
                                         db_index=True,
                                         max_length=128,
                                         choices=[(STATUS_RUNNING, "Running"),
                                                  (STATUS_COMPLETE_SUCCESS, "Completed Successfully"),
                                                  (STATUS_COMPLETE_ERROR, "Failed")])

    class Meta:
        unique_together = ('repo', 'build_number',)


class BuildLogLine(models.Model):
    build = models.ForeignKey(Build, db_index=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(db_index=True, auto_now_add=True, blank=True)
    command = models.TextField()
    message = models.TextField(default='')
    loglevel = models.CharField(db_index=True, max_length=128)
    line_number = models.IntegerField(db_index=True)
    execution_time_sec = models.FloatField(blank=True, null=True)
    exec_complete = models.BooleanField(default=False)


