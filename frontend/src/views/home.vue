<template>
    <SystemMessage
      :message="this.show_global_error_msg" />
    <v-container class="my-5">

        <v-layout row>

            <v-col sm="10">
                <h3>Repositories</h3>
            </v-col>

            <v-col sm="2" align="right">

                <DialogCreateRepo @create_success=this.retrieveRepos />

            </v-col>
        </v-layout>

        <v-skeleton-loader
          v-if="loading"
          type="list-item-three-line@4"
          class="mt-4"
        ></v-skeleton-loader>

        <v-layout row v-else-if="repos.length == 0">
          <v-col cols="12">

            <v-alert
              density="compact"
              type="info"
            >
              No repositories have been created yet.  Click the "+" button to create a new repo.
            </v-alert>

          </v-col>
        </v-layout>

        <v-card :to="'/cfg/repo/' + repo.repo_uid" flat v-for="repo in repos" :key="repo.repo_uid" v-else>

            <v-layout row wrap :class="`repo complete    ${repo.repo_uid}`">
                <v-col sm="9">
                    <div class="text-h5">{{ repo.repo_uid }}</div>
                    <div class="text-caption">Updated: {{ this.timeAgo.format(new Date(repo.last_updated)) }}</div>
                </v-col>

                <v-col  class="text-center" sm="2">
                    <div>{{ repo.package_count }}</div>
                    <div class="text-caption">Packages</div>
                </v-col>
                <v-col sm="1">
                    <v-icon>{{ repo_type_icons[repo.repo_type] }}</v-icon>
                </v-col>
            </v-layout>
            <v-divider></v-divider>
        </v-card>

    </v-container>
</template>

  <script>
  import RepoDataService from "../services/repo_service";
  import {logger} from '@/logger.ts'

  import DialogCreateRepo from '@/components/dialog_create_repo.vue'
  import SystemMessage from '@/components/system_message.vue'

  export default {
    name: "Home",
    components: {
      DialogCreateRepo,
      SystemMessage
    },
    data() {
      return {
        repos: [],
        show_global_error_msg: '',
        loading: true,
        repo_type_icons: {
            deb: "mdi-ubuntu",
            rpm: "mdi-redhat",
            files: "mdi-file-multiple-outline"
            },

        title: ""
      };
    },
    methods: {
      retrieveRepos() {
        this.loading = true;
        RepoDataService.getAll()
          .then(response => {
            this.repos = response.data.results;
            this.loading = false;
            logger.debug(response.data);
          })
          .catch(e => {
            this.loading = false;
            if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
              this.show_global_error_msg = e.response.data.detail;
            else
              this.show_global_error_msg = 'Error loading repos: ' + e.message;

            logger.debug(e);
          });
      },

      refreshList() {
        this.retrieveRepos();
      },


    },
    mounted() {

      this.retrieveRepos();
    }
  };
  </script>


  <style>
    .repo{
      border-left: 4px solid rgb(var(--v-theme-primary));
      border-right: 4px solid rgb(var(--v-theme-primary));
    }
</style>
