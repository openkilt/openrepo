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

from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'repos', views.ReposViewSet)
router.register(r'signingkeys', views.PGPKeysViewSet)
router.register(r'builds', views.BuildViewSet)
router.register(r'buildlogs', views.BuildLogViewSet)
#router.register(r'packages', views.PackageViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('whoami', views.WhoAmIViewSet.as_view({'get': 'retrieve'})),
    path(r'<slug:repo_uid>/', views.RepoViewSet.as_view({'get': 'retrieve',
                                                         'put': 'update',
                                                         'delete': 'destroy'}), name='repo-detail'),
    path(r'<slug:repo_uid>/packages/', views.PackagesViewSet.as_view({'get':'list'}), name='package-list'),
    path(r'<slug:repo_uid>/upload/', views.UploadViewSet.as_view({'post':'create'}), name='upload'),
    path(r'<slug:repo_uid>/pkg/<slug:package_uid>/', views.PackageViewSet.as_view({'get':'retrieve',
                                                                                   'put':'update',
                                                                                   'delete': 'destroy'}), name='package-detail'),
    path(r'<slug:repo_uid>/pkg/<slug:package_uid>/copy/', views.CopyViewSet.as_view({'post':'create'}), name='package-copy'),

]
