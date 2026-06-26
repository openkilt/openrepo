<template>
  <v-app>
    <template v-if="auth_loading">
      <v-main class="d-flex align-center justify-center" style="min-height: 100vh">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-main>
    </template>
    <template v-else>
      <NavBar />
      <v-main>
        <router-view />
      </v-main>
    </template>
  </v-app>
</template>

<script lang="ts">
import NavBar from '@/components/nav_bar.vue'
import {logger} from '@/logger.ts'
import UserDataService from '@/services/user_service'

export default {
  name: 'App',
  components: {
    NavBar
  },
  data() {
    return {
      user_info: {},
      auth_loading: true,
    }
  },
    methods: {
      get_user_info() {

        UserDataService.whoAmI()
        .then(response => {
              this.user_info = response.data;
              this.$store.commit('set_user', response.data);
              this.auth_loading = false;
              logger.debug(this.user_info);
          })
          .catch(e => {
              logger.debug(e);
              if (e.response.status == 401)
              {
                logger.info("User is not authenticated.  Redirecting to login page")
                window.location.href = "/admin/login/?next=" + window.location.pathname;
              }
              else
              {
                this.auth_loading = false;
              }
          });
      }
  },
  mounted() {
    this.get_user_info();
  }

}
</script>
