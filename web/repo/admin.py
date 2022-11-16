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

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Repository

class CustomUserAdmin(UserAdmin):
    # ...
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (('Permissions'), {
        'fields': ('is_active', 'is_staff', 'is_superuser','user_permissions',),
        }),
        (('Important dates'), {'fields': ('date_joined','last_login',),}),
)

class RepositoryAdmin(admin.ModelAdmin):
    pass
    fields = ('is_stale', 'write_access','package_count', 'refresh_count', 'last_updated',)
    readonly_fields = ( 'package_count', 'refresh_count', 'last_updated',)
    list_display = ('repo_uid', 'package_count', 'last_updated',)
    #list_display = ('name', 'title', 'view_birth_date')

    #@admin.display(empty_value='???')
    #def view_birth_date(self, obj):
    #    return obj.birth_date

admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register your models here.
admin.site.register(Repository, RepositoryAdmin)
