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
  <v-app>

    <NavBar />
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script lang="ts">
import NavBar from '@/components/nav_bar.vue'
import { defineComponent } from 'vue'
import {logger} from '@/logger.ts'
import UserDataService from '@/services/user_service'
import { provide } from 'vue'

export default {
  name: 'App',
  components: {
    NavBar
  },
  data() {
    return {
      user_info: {},
    }
  },
    methods: {
      get_user_info() {

        UserDataService.whoAmI()
        .then(response => {
              this.user_info = response.data;
              this.$store.commit('set_user', response.data);
              logger.debug(this.user_info);
          })
          .catch(e => {
              logger.debug(e);
              if (e.response.status == 401)
              {
                logger.info("User is not authenticated.  Redirecting to login page")
                window.location.href = "/admin/login/?next=" + window.location.pathname;
              }
          });
      }
  },
  mounted() {
    this.get_user_info();
  }

}
</script> 
