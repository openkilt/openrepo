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
