<!--
 Copyright 2022 by Open Kilt LLC. All rights reserved.
 This file is part of the OpenRepo Repository Management Software (OpenRepo)
 OpenRepo is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License
 version 3 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
-->

<template>
    <nav>
        <v-toolbar color="indigo-darken-4" flat app>
            <v-toolbar-title class="text-uppercase grey--text">
                <!--<span class="font-weight-light">Open</span>
                <span>Repo</span>-->
                <span><router-link to="/"><v-img
                    
                    width="120"
                    src="/assets/openrepo_logo.svg"
                ></v-img></router-link></span>
            </v-toolbar-title>
            <v-spacer></v-spacer>

            <span>{{username}}</span>
            <v-menu>
                <template v-slot:activator="{ props }">
                    <v-btn
                    v-bind="props"
                    icon
                    >
                        <v-icon>mdi-dots-vertical</v-icon>
                    </v-btn>
                </template>
                <v-list>
                    <v-list-item
                    v-for="(item, index) in items"
                    :key="index"
                    :value="index"
                    :href="item.href"
                    :to="item.to"
                    >
                        <template v-slot:prepend>
                        <v-icon :icon="item.icon"></v-icon>
                        </template>
                        <v-list-item-title>{{ item.title }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>

        </v-toolbar>
    </nav>
</template>

<script lang="ts">
    import { mapState } from 'vuex'

    export default {
        data: () => ({
            raw_items: [
                { title: 'User Info', icon: 'mdi-account', to: '/cfg/userinfo/', for_superuser: false},
                { title: 'System Admin', icon: 'mdi-database-cog-outline', href: "/admin/", for_superuser: true},
                { title: 'Log Out', icon: 'mdi-exit-to-app', href: "/admin/logout/", for_superuser: false },
            ],
        }),
        computed: {
            ...mapState({
                username: 'username',
                is_superuser: 'is_superuser'
            }),
            items() {
                if (this.is_superuser)
                    return this.raw_items;
                
                // If the user is not a superuser, filter out those menu items
                return this.raw_items.filter(it=>!it.for_superuser);
            },
        }
    }
</script>