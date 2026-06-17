<template>
    <SystemMessage
      :message="this.show_global_error_msg" />

    <v-container class="my-5">

        <v-layout row wrap>
            <v-col cols="6" align="left">
                <v-breadcrumbs :items="breadcrumbs">
                </v-breadcrumbs>
            </v-col>
            <v-col cols="6" align="right">
                <v-chip variant="outlined" v-if="is_readonly">
                    <v-icon start icon="mdi-pencil-lock-outline"></v-icon> read-only
                </v-chip>

                <v-dialog v-model="dialog_instructions" max-width="600">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" variant="text" icon color="primary"
                               aria-label="Repo instructions">
                            <v-icon>mdi-information-outline</v-icon>
                            <v-tooltip activator="parent" location="top">Repo Instruction</v-tooltip>
                        </v-btn>
                    </template>
                    <v-card>
                        <v-card-title class="text-h5">
                            Repo Instructions
                        </v-card-title>
                        <v-card-text>
                            <pre class="block bg-grey-darken-4 text-grey-lighten-3 pa-5 whitespace-pre overflow-auto">{{repo_details.repo_instructions}}</pre>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="green darken-1" @click="copyRepoInstructionsToClipboard();" text>Copy to Clipboard</v-btn>
                            <v-btn color="green darken-1" @click="dialog_instructions = false;" text>Close</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>

                <v-btn :to="this.status_href" icon variant="text" color="primary"
                       aria-label="Build status">
                        <v-icon>mdi-progress-wrench</v-icon>
                        <v-tooltip activator="parent" location="top">Build Status</v-tooltip>
                </v-btn>

                <v-btn :to="this.settings_href" icon variant="text" color="primary"
                       aria-label="Repo settings">
                        <v-icon>mdi-cog</v-icon>
                        <v-tooltip activator="parent" location="top">Repo Settings</v-tooltip>
                </v-btn>

            </v-col>
        </v-layout>
            <v-divider></v-divider>

        <v-layout row wrap>

            <v-col cols="8" align="left">
                <div>
                    <v-btn @click="selectAll(true)" icon variant="text" color="primary"
                           aria-label="Select all packages">
                        <v-icon>mdi-checkbox-multiple-outline</v-icon>
                        <v-tooltip activator="parent" location="top">Select All</v-tooltip>
                    </v-btn>
                    <v-btn @click="selectAll(false)" icon variant="text" color="primary"
                           aria-label="Unselect all packages">
                        <v-icon>mdi-checkbox-multiple-blank-outline</v-icon>
                        <v-tooltip activator="parent" location="top">Unselect All</v-tooltip>
                    </v-btn>
                    <span class="text-caption ml-4">{{selected_pkgs.length}} selected</span>
                </div>
            </v-col>
            <v-col align="right" cols="4" >

                <DialogCopyPackages
                :repo_uid="this.repo_uid"
                :selected_pkgs="this.selected_pkgs"
                :repo_type="this.repo_details.repo_type" />

                <DialogDeletePackages
                :repo_uid="this.repo_uid"
                :selected_pkgs="this.selected_pkgs"
                @delete_success="this.selected_pkgs = []; this.retrievePackages()" />

                <DialogCopyPackages
                promote
                :repo_promote_uid="this.repo_details.promote_to"
                :repo_uid="this.repo_uid"
                :selected_pkgs="this.selected_pkgs"
                :repo_type="this.repo_details.repo_type" />

                <DialogUploadPackages
                :repo_uid="this.repo_uid"
                :repo_type="this.repo_details.repo_type"
                @uploads_complete="this.retrievePackages" />

            </v-col>
        </v-layout>



        <v-card flat>

            <v-layout class="font-weight-bold" row wrap>

                <v-col cols="4">
                    <div>Package Name</div>
                </v-col>

                <v-col  align="left" cols="3">
                    <div>Version</div>
                </v-col>

                <v-col  align="left" cols="3">
                    <div>Architecture</div>
                </v-col>

                <v-col  align="right" cols="2">
                    <div>Upload Date</div>
                </v-col>

            </v-layout>
            <v-divider></v-divider>
            </v-card>
        <v-card flat v-for="pkg in packages" :key="pkg.package_uid">

            <v-layout row wrap class="package" 
                    :class="pkg.promotable ? 'promotable' : 'not-promotable'">
                <v-col  class="text-left  " cols="4">

                    <v-checkbox-btn inline
                    density="compact"
                    v-model="selected_pkgs"
                    :label=pkg.package_name
                    color="primary"
                    :value=pkg.package_uid
                    hide-details
                    ></v-checkbox-btn>

                </v-col>

                <v-col  align="left" cols="3">
                    <div>{{ pkg.version }}</div>
                </v-col>
                <v-col  align="left" cols="3">
                    <div>{{ pkg.architecture }}</div>
                </v-col>
                <v-col  align="right" cols="2">
                    <div>{{ this.format_date(pkg.upload_date )}}</div>
                </v-col>
            </v-layout>
            <v-divider></v-divider>
        </v-card>
    </v-container>

</template>

<script lang="ts">

import PackageDataService from "../services/package_service";
import RepoDataService from "../services/repo_service";
import DialogCopyPackages from "@/components/dialog_copy_packages.vue"
import DialogDeletePackages from "@/components/dialog_delete_packages.vue"
import DialogUploadPackages from "@/components/dialog_upload_packages.vue"
import SystemMessage from '@/components/system_message.vue'
import {logger} from '@/logger.ts'
import moment from 'moment'
import semver from 'semver'
import { mapState } from 'vuex'

export default {
    name: "Repo View",
    components: {
        DialogCopyPackages,
        DialogDeletePackages,
        DialogUploadPackages,
        SystemMessage
    },
    data() {
        return {
            selected_pkgs: [],
            repo_uid: this.$route.params.repo_uid,
            packages: [],
            repo_details: {},
            show_global_error_msg: '',
            dialog_instructions: false,
            is_readonly: false,
            loading: true,
            page: 1,
            totalItems: 0,
            itemsPerPage: 100,
            search: '',
            searchTimer: null,
            settings_href: '/cfg/repo/' + this.$route.params.repo_uid + '/settings/',
            status_href:   '/cfg/repo/' + this.$route.params.repo_uid + '/status/',
            breadcrumbs: [
                {
                title: 'Repositories',
                disabled: false,
                to: '/',
                },
                {
                title:  this.$route.params.repo_uid,
                disabled: true,
                to: '/',
                },
            ],
        };
    },
    computed: {
      ...mapState({
        username: 'username',
        is_superuser: 'is_superuser'
      }),
      totalPages() {
        return Math.ceil(this.totalItems / this.itemsPerPage);
      },
    },
    methods: {
        retrieveRepoDetails() {
            RepoDataService.get(this.repo_uid)
            .then(response => {
                this.repo_details = response.data;
                this.repo_details.repo_instructions = this.repo_details.repo_instructions.replaceAll("<origin>", window.location.origin);
                this.is_readonly = !this.is_superuser && this.repo_details.write_access.indexOf(this.username) === -1;
            })
            .catch(e => {
                logger.debug(e);
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                this.show_global_error_msg = e.response.data.detail;
                else
                this.show_global_error_msg = 'Error loading repo: ' + e.message;
            });
        },
        format_date(value:Date) {
            return moment(value).format('YYYY-MM-DD HH:mm:ss');
        },
        waitFor(conditionFunction) {
            const poll = resolve => {
                if(conditionFunction()) resolve();
                else setTimeout(_ => poll(resolve), 10);
            }
            return new Promise(poll);
        },
        flagPromotables(pkgs_here: Array<any>, pkgs_promote: Array<any>)
        {
            let highest_promotes = {}

            pkgs_promote.forEach(pkg => {
                try {
                    let cur_ver = semver.coerce(pkg.version, true);
                    if (cur_ver == null)
                        return;

                    if (highest_promotes[pkg.package_name] === undefined)
                    {
                        highest_promotes[pkg.package_name] = cur_ver;
                    }
                    if (semver.gt(cur_ver, highest_promotes[pkg.package_name], true))
                    {
                        highest_promotes[pkg.package_name] = cur_ver;
                    }
                } catch (error)
                {
                    logger.warn(error);
                }
            }, this)

            pkgs_here.forEach(pkg => {
                let cur_ver = semver.coerce(pkg.version, true);
                if (highest_promotes[pkg.package_name] === undefined ||
                    semver.gt(cur_ver, highest_promotes[pkg.package_name], true))
                {
                    pkg.promotable = true;
                    logger.debug("Promotable package: " + pkg.package_name);
                }
                else
                {
                    pkg.promotable = false;
                }
            }, this)

            this.packages = pkgs_here;
        },
        copyRepoInstructionsToClipboard () {
            navigator.clipboard.writeText(this.repo_details.repo_instructions);
        },
        buildParams(extra?: any) {
            let params: any = { page: this.page, page_size: this.itemsPerPage };
            if (this.search) params.search = this.search;
            if (extra) Object.assign(params, extra);
            return params;
        },
        fetchPage(newPage?: number) {
          this.loading = true;
          if (newPage) this.page = newPage;
          PackageDataService.getAll(this.repo_uid, this.buildParams())
            .then(response => {
              this.packages = response.data.results;
              this.totalItems = response.data.count;
              this.loading = false;
            })
            .catch(e => {
              logger.debug(e);
              this.loading = false;
            });
        },
        retrievePackages() {
            let completion_count = 0;
            let repo_pkgs = [];
            let is_promotable = this.repo_details.promote_to != null && this.repo_details.promote_to != '';

            this.loading = true;
            PackageDataService.getAll(this.repo_uid, this.buildParams())
            .then(response => {
                repo_pkgs = response.data.results;
                this.totalItems = response.data.count;

                if (!is_promotable)
                {
                    this.packages = repo_pkgs;
                    this.loading = false;
                }

                completion_count++;
                logger.debug(response.data);
            })
            .catch(e => {
                completion_count++;
                this.loading = false;
                logger.debug(e);
            })

            if (is_promotable)
            {
                let promote_pkgs = [];
                PackageDataService.getAll(this.repo_details.promote_to, { page_size: 2000 })
                .then(response => {
                    promote_pkgs = response.data.results;
                    completion_count++;
                    logger.debug(response.data);
                })
                .catch(e => {
                    completion_count++;
                    this.loading = false;
                    logger.debug(e);
                });

                this.waitFor(_ => completion_count >= 2)
                .then(_ => {
                    logger.debug('All package list requests complete')
                    this.flagPromotables(repo_pkgs, promote_pkgs);
                    this.loading = false;
                });
            }
        },
        selectAll(enable: boolean) {
            this.selected_pkgs = [];
            if (enable)
            {
                this.packages.forEach(pkg => {
                    this.selected_pkgs.push(pkg.package_uid)
                })
            }
        },
    },
    watch: {
        repo_details(old_details, new_details)
        {
            this.retrievePackages();
        },
        page()
        {
            if (this.repo_details.repo_uid)
              this.retrievePackages();
        },
        itemsPerPage()
        {
            this.page = 1;
            if (this.repo_details.repo_uid)
              this.retrievePackages();
        },
        search()
        {
            if (this.searchTimer) clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(() => {
                this.page = 1;
                if (this.repo_details.repo_uid)
                  this.retrievePackages();
            }, 300);
        }
    },
    mounted() {
        this.retrieveRepoDetails();
    },
}

</script>

<style>

    .package.promotable{
      border-left: 8px solid rgb(var(--v-theme-secondary));
    }
    .package.not-promotable {
      border-left: 8px solid rgba(var(--v-theme-on-surface), 0.12);
    }
    .page-size-select {
      max-width: 130px;
      display: inline-block;
    }
</style>
