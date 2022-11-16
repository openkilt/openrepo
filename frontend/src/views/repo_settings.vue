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
    <SystemMessage 
      :message="this.show_global_error_msg" />

    <v-container class="my-5">

        <v-layout row wrap>
            <v-col cols="12" align="left">
                <v-breadcrumbs :items="breadcrumbs">
                </v-breadcrumbs>
            </v-col>
        </v-layout>
        <v-divider></v-divider>

        <v-layout row wrap >

            <v-col cols="12" >
                
                <v-card >
                    <v-layout row wrap>
                        <v-col class="bg-info" cols="12">
                            <h3>Repo Settings</h3>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12" class="pb-0 mb-6">
                        <strong>Repo UID:</strong> {{this.repo_uid}}
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12" class="py-0 my-0">
                            <v-autocomplete
                                    v-model="this.repo_details.promote_to"
                                    :items="this.all_repos"
                                    item-title="display"
                                    item-value="val"
                                    :disabled="form_disabled"
                                    :error-messages="repo_error_response.promote_to"
                                    outlined
                                    dense
                                    label="Promote Destination Repo"
                                ></v-autocomplete>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12" class="py-0 my-0">
                            <v-checkbox
                                v-model="this.repo_details.keep_only_latest"
                                :disabled="form_disabled"
                                :error-messages="repo_error_response.keep_only_latest"
                                label="Auto-delete older package versions"
                                ></v-checkbox>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12" class="py-0 my-0">
                            <div>
                                <div align="right">
                                    <router-link to="/cfg/signing_keys">Manage Signing Keys</router-link>
                                </div>
                                <v-autocomplete
                                        v-model="this.repo_details.signing_key"
                                        :items="this.all_pgp_keys"
                                        item-title="display"
                                        item-value="val"
                                        :disabled="form_disabled"
                                        :error-messages="repo_error_response.signing_key"
                                        outlined
                                        dense
                                        label="Signing Key"
                                    ></v-autocomplete>
                            </div>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12"  align="right">
                                        
                            <div class="text-red">{{repo_general_error_message}}</div>
                            <v-btn color="success" @click="updateRepoSettings()">Save</v-btn>
                        </v-col>
                    </v-layout>
                </v-card>


                <v-card class="mt-12">
                    <v-layout row wrap>
                        <v-col class="bg-info" cols="12">
                            <h3>Delete Repo</h3>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12" class="pb-0 mb-6">
                            <v-alert
                            color="yellow-darken-4"
                            type="warning"
                            title="Warning"
                            variant="flat"
                            >
                            Deleting the repository will delete all packages and configuration for this repository and cannot be undone.
                            </v-alert>
                        </v-col>
                    </v-layout>
                    <v-layout row wrap>
                        <v-col cols="12"  align="right">

                            <!-- delete button -->
                            <v-dialog v-model="dialog_delete" max-width="400">
                                <template v-slot:activator="{ props }">
                                    <v-btn color="error" v-bind="props">Delete Repository</v-btn>
                                </template>
                                <v-card>
                                    <v-card-title class="text-h5">
                                        Are you sure?
                                    </v-card-title>
                                    <v-card-text>
                                        <div class="mb-5">
                                            Confirm that you wish to delete this repository.
                                        </div>

                                        <div class="text-red">{{dialog_delete_error_messages}}</div>
                                    </v-card-text>
                                    <v-card-actions>
                                        <v-spacer></v-spacer>
                                        <v-btn color="green darken-1" text @click="dialog_delete = false">Cancel</v-btn>
                                        <v-btn color="green darken-1" text @click="deleteRepo();">Yes</v-btn>
                                    </v-card-actions>
                                </v-card>
                            </v-dialog>
                        </v-col>
                    </v-layout>
                </v-card>
                

            </v-col>
        </v-layout>

    </v-container>
    </v-app>
</template>

<script lang="ts">

import RepoDataService from "../services/repo_service";
import SigningKeyDataService from "../services/signingkey_service";
import {logger} from '@/logger.ts'
import SystemMessage from '@/components/system_message.vue'

export default {
    name: "Repo Settings View",
    components: {
      SystemMessage
    },
    data() {
        return {
            show_global_error_msg: '',
            dialog_delete: false,
            dialog_delete_error_messages: '',
            repo_uid: this.$route.params.repo_uid,
            repo_details: {},
            repo_error_response: {
                repo_uid: "",
                signing_key: "",
                promote_to: "",
                keep_only_latest: ""
            },
            repo_general_error_message: '',
            all_repos: [],
            all_pgp_keys: [ ],
            form_disabled: true,
            breadcrumbs: [
                {
                title: 'Repositories',
                disabled: false,
                to: '/',
                },
                {
                title:  this.$route.params.repo_uid,
                disabled: false,
                to: '/cfg/repo/' + this.$route.params.repo_uid,
                },
                {
                title:  "Settings",
                disabled: true,
                to: this.$route.path,
                },
            ],
        };
    },
    methods: {

        retrieveRepoDetails() {
            RepoDataService.get(this.repo_uid)
            .then(response => {
                this.repo_details = response.data;
                logger.debug(response.data);

                this.repo_data_retrieved();
            })
            .catch(e => {   
                logger.debug(e);
            });
        },
        repo_data_retrieved(event)
        {
            this.form_disabled = false;
            this.loadRepoList();
        },
        loadRepoList() {
            this.all_repos = []
            RepoDataService.getAll()
            .then(response => {
                // Only insert repos that have either the same repo type (e.g., "deb" or "rpm") or
                // generic file repos.  It wouldn't make sense to copy a deb to an rpm or vice-versa
                this.all_repos = [
                    {'display': 'No Promotion', 'val': ''}
                ]
                response.data.results.forEach(function(repo) {
                    if ((repo.repo_type == this.repo_details.repo_type || repo.repo_type == "files") && 
                        repo.repo_uid != this.repo_uid)
                    {
                        this.all_repos.push({'display': repo.repo_uid, 'val': repo.repo_uid});
                    }
                }, this)
                logger.debug(response.data);
            })
            .catch(e => {
                logger.debug(e);
            });
        },
        loadPgpKeys() {
            this.all_pgp_keys = []
            SigningKeyDataService.getAll()
            .then(response => {

                this.all_pgp_keys = [
                    {'display': 'No signing key', 'val': ''}
                ]
                response.data.results.forEach(element => {
                    let display_text = element.name + ' <' + element.email + '> - ' + element.fingerprint.substr(0, 10);
                    let value = element.fingerprint;

                    this.all_pgp_keys.push({'display': display_text, 'val': value});
                }, this);
                
                logger.debug(response.data);
            })
            .catch(e => {
                logger.debug(e);
            });
        },
        deleteRepo() {
            
            RepoDataService.delete(this.repo_uid)
            .then(response => {
                this.dialog_delete = false;

                // Now that the repo is deleted, there's no reason to stay on this page
                this.$router.push({ name: 'home' });

            })
            .catch(e => { 
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                    this.dialog_delete_error_messages = e.response.data.detail;
                else
                    this.dialog_delete_error_messages = 'Error deleting repo: ' + e.message;
            });
        },
        updateRepoSettings() {

            RepoDataService.update(this.repo_uid, this.repo_details)
            .then(response => {
                console.log(response.data);
                //this.submitted = true;
                this.show_global_error_msg = "Repo settings updated"

            })
            .catch(e => {
                this.repo_error_response = e.response.data
                logger.error(e);
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                    this.repo_general_error_message = e.response.data.detail;
                else
                    this.repo_general_error_message = 'Error saving repo settings: ' + e.message;
            });
        },
    },
    mounted() {
        this.retrieveRepoDetails();
        this.loadPgpKeys();
    }
}

</script>

<style>

</style>