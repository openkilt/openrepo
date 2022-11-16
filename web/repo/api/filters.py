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


from repo.models import Build, BuildLogLine
from django_filters import rest_framework as df_filters


class BuildFilter(df_filters.FilterSet):
    min_build = df_filters.NumberFilter(field_name="build_number", lookup_expr='gte')
    max_build = df_filters.NumberFilter(field_name="build_number", lookup_expr='lte')
    repo = df_filters.CharFilter(field_name="repo__repo_uid", lookup_expr='exact')
    min_time = df_filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    max_time = df_filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')

    class Meta:
        model = Build
        fields = ['build_number', 'completion_status']


class BuildLogFilter(df_filters.FilterSet):
    min_line = df_filters.NumberFilter(field_name="line_number", lookup_expr='gte')
    max_line = df_filters.NumberFilter(field_name="line_number", lookup_expr='lte')
    repo = df_filters.CharFilter(field_name="build__repo__repo_uid", lookup_expr='exact')
    build = df_filters.NumberFilter(field_name="build__build_number", lookup_expr='exact')
    min_time = df_filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    max_time = df_filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')

    class Meta:
        model = BuildLogLine
        fields = ['loglevel']