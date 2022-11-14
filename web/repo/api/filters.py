
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