<template>
    <SystemMessage 
      :message="this.show_global_error_msg" />
    <v-container class="my-5">

        <v-layout row>

            <v-col sm="10">
                <h3>Repositories</h3>
            </v-col>

            <v-col sm="2" align="right">

                <!-- Create Repo dialog -->
                <DialogCreateRepo @create_success=this.retrieveRepos />

            </v-col>
        </v-layout>
        <v-card :to="'/cfg/repo/' + repo.repo_uid" flat v-for="repo in repos" :key="repo.repo_uid">

            
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
        RepoDataService.getAll()
          .then(response => {
            this.repos = response.data.results;
            logger.debug(response.data);
          })
          .catch(e => {
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
      border-left: 4px solid #2196f3;
      border-right: 4px solid #2196f3;
    }
</style>
