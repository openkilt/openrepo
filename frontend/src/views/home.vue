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

        <div v-else class="repo-tree mt-4">
          <template v-for="item in repoTree" :key="item.repo.repo_uid">
            <v-card
              :to="'/cfg/repo/' + item.repo.repo_uid"
              variant="outlined"
              class="repo-card mb-3"
              :class="'depth-' + item.depth"
              :style="{ marginLeft: item.depth * 36 + 'px' }"
            >
              <v-card-item class="py-3">
                <template #prepend>
                  <v-avatar
                    :color="typeColor(item.depth)"
                    variant="tonal"
                    size="40"
                    rounded
                  >
                    <v-icon :icon="repo_type_icons[item.repo.repo_type]" size="22"></v-icon>
                  </v-avatar>
                </template>

                <v-card-title class="text-subtitle-1 font-weight-medium px-2">
                  {{ item.repo.repo_uid }}
                </v-card-title>

                <v-card-subtitle class="px-2 d-flex align-center flex-wrap">
                  <v-chip
                    v-if="item.depth > 0"
                    size="x-small"
                    variant="tonal"
                    color="secondary"
                    class="mr-2"
                    prepend-icon="mdi-arrow-up-bold-circle-outline"
                  >
                    {{ getParentName(item.repo) }}
                  </v-chip>
                  <span class="text-medium-emphasis text-caption">
                    Updated {{ this.timeAgo.format(new Date(item.repo.last_updated)) }}
                  </span>
                </v-card-subtitle>

                <template #append>
                  <div class="text-center ml-2">
                    <div class="text-subtitle-2 font-weight-bold">{{ item.repo.package_count }}</div>
                    <div class="text-caption text-medium-emphasis">packages</div>
                  </div>
                </template>
              </v-card-item>
            </v-card>
          </template>
        </div>

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
        depthColors: ['primary', 'secondary', 'accent', 'warning'],
        title: ""
      };
    },
    computed: {
      repoTree() {
        const map = {};
        this.repos.forEach(r => map[r.repo_uid] = { ...r, children: [] });

        const roots = [];
        this.repos.forEach(r => {
          if (r.promote_to && map[r.promote_to]) {
            map[r.promote_to].children.push(map[r.repo_uid]);
          } else {
            roots.push(map[r.repo_uid]);
          }
        });

        const flat = [];
        const walk = (nodes, depth) => {
          nodes.forEach(n => {
            flat.push({ repo: n, depth });
            walk(n.children, depth + 1);
          });
        };
        walk(roots, 0);

        return flat;
      }
    },
    methods: {
      typeColor(depth) {
        return this.depthColors[depth] || this.depthColors[this.depthColors.length - 1];
      },
      getParentName(repo) {
        return repo.promote_to || '';
      },
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
    .repo-card {
      transition: box-shadow 0.2s ease, transform 0.2s ease;
      border-left: 4px solid rgb(var(--v-theme-primary)) !important;
    }
    .repo-card:hover {
      box-shadow: 0 2px 12px rgba(var(--v-theme-on-surface), 0.12) !important;
      transform: translateY(-2px);
    }

    .repo-card.depth-1 {
      border-left-color: rgb(var(--v-theme-secondary)) !important;
    }
    .repo-card.depth-2 {
      border-left-color: rgb(var(--v-theme-accent)) !important;
    }
    .repo-card.depth-3 {
      border-left-color: rgb(var(--v-theme-warning)) !important;
    }
</style>
