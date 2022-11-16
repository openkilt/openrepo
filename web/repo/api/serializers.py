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

from django.contrib.auth.models import User
from rest_framework import serializers
from adapters.repo import get_repo_adapter
from repo.models import Repository, Package, PGPSigningKey, Build, BuildLogLine
from .util import ParameterisedHyperlinkedIdentityField
import string

class UserSerializer(serializers.HyperlinkedModelSerializer):
    api_key = serializers.StringRelatedField(source='auth_token', read_only=True, many=False)


    class Meta:
        model = User
        fields = ['href', 'username', 'is_superuser', 'email', 'api_key']


class RepoSummarySerializer(serializers.HyperlinkedModelSerializer):
    href_repo = ParameterisedHyperlinkedIdentityField(view_name='repo-detail', lookup_fields=([ ('repo_uid', 'repo_uid')]),
                                                read_only=True)
    href_packages = ParameterisedHyperlinkedIdentityField(view_name='package-list', lookup_fields=([ ('repo_uid', 'repo_uid')]),
                                                read_only=True)

    class Meta:
        model = Repository
        fields = ['href_repo', 'href_packages', 'repo_uid', 'repo_type', 'package_count', 'last_updated']

class PGPKeySerializer(serializers.HyperlinkedModelSerializer):

    #href_key = ParameterisedHyperlinkedIdentityField(view_name='signing-keys', lookup_fields=([ ('fingerprint', 'fingerprint')]),
    #                                            read_only=True)
    #href_key = serializers.HyperlinkedIdentityField(view_name='pgp-keys', format='html')

    class Meta:
        model = PGPSigningKey
        lookup_field = 'fingerprint'
        extra_kwargs = {
            'href': {'lookup_field': 'fingerprint'}
        }
        fields = ['name', 'email', 'fingerprint', 'creation_date', 'href']
        read_only_fields = ['creation_date']

class RepoDetailSerializer(serializers.HyperlinkedModelSerializer):
    href_packages = ParameterisedHyperlinkedIdentityField(view_name='package-list', lookup_fields=([ ('repo_uid', 'repo_uid')]),
                                                read_only=True)
    href_upload = ParameterisedHyperlinkedIdentityField(view_name='upload', lookup_fields=([ ('repo_uid', 'repo_uid')]),
                                                read_only=True)

    signing_key = serializers.SlugRelatedField(slug_field='fingerprint', queryset=PGPSigningKey.objects.all(),
                                               read_only=False, required=False, allow_null=True)
    promote_to = serializers.SlugRelatedField(slug_field='repo_uid', queryset=Repository.objects.all(),
                                              read_only=False, required=False, allow_null=True)

    write_access = serializers.StringRelatedField( read_only=True, many=True)

    repo_instructions = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = ['href_packages', 'href_upload', 'repo_uid', 'repo_type', 'package_count', 'signing_key', 'keep_only_latest', 'last_updated', 'promote_to', 'repo_instructions', 'write_access']

    def get_repo_instructions(self, obj):
        repo_adapter = get_repo_adapter(obj)
        return repo_adapter._get_repo_instructions()

    def validate(self, attrs):
        # Apply custom validation either here, or in the view.
        allowed_uid_chars = set(string.ascii_letters + string.digits + '-_')

        uuid_is_valid = set(attrs['repo_uid']) <= allowed_uid_chars
        if not uuid_is_valid:
            raise serializers.ValidationError(
                {'repo_uid': 'repo_uid may only contain alphanumeric characters, dashes, and underscores'})

        disallowed_names = ["back", "api", "admin", "api-auth", "static"]
        if attrs['repo_uid'] in disallowed_names:
            raise serializers.ValidationError({'repo_uid': "Repo UID cannot be any of the following special words: " + ", ".join(disallowed_names)})
        return attrs

class PackageSummarySerializer(serializers.HyperlinkedModelSerializer):
    href_package = ParameterisedHyperlinkedIdentityField(view_name='package-detail', lookup_fields=([ ('repo.repo_uid', 'repo_uid'), ('package_uid', 'package_uid')]),
                                                read_only=True)

    class Meta:
        model = Package
        fields = ['href_package', 'package_uid', 'package_name', 'filename', 'architecture', 'upload_date', 'version']


class PackageDetailSerializer(serializers.HyperlinkedModelSerializer):
    repo_uid = serializers.StringRelatedField(source='repo', read_only=True)

    class Meta:
        model = Package
        fields = ['package_uid', 'repo_uid', 'filename', 'version', 'architecture', 'checksum_sha512', 'build_date', 'upload_date']


class CopySerializer(serializers.Serializer):
    package_file = serializers.FileField()
    class Meta:
        fields = ['dest_repo_uid']

class UploadSerializer(serializers.Serializer):
    package_file = serializers.FileField()
    class Meta:
        fields = ['package_file']


class BuildSerializer(serializers.ModelSerializer):
    repo_uid = serializers.CharField(source='repo.repo_uid')
    class Meta:
        model = Build
        fields = ['repo_uid', 'timestamp', 'build_number', 'completion_status']

class BuildLogSerializer(serializers.ModelSerializer):
    build = serializers.SlugRelatedField(slug_field='build_number', queryset=Build.objects.all(), required=False, allow_null=True)

    class Meta:
        model = BuildLogLine
        fields = ['build', 'timestamp', 'command', 'message', 'loglevel', 'line_number', 'execution_time_sec', 'exec_complete']
