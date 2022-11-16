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


    <!-- Copy/ package logic -->
    <v-dialog max-width="700" v-model="dialog">
        <template v-slot:activator="{ props }">


        <v-btn v-if="this.promote!==undefined" 
               @click="resetDialog();" 
               :disabled="this.selected_pkgs.length == 0 || this.repo_promote_uid == null" 
               v-bind="props" variant="text" icon color="primary">
            <v-icon>mdi-star</v-icon>
            <v-tooltip activator="parent" location="top">Promote</v-tooltip>
        </v-btn>
        <v-btn v-else
               @click="resetDialog(); loadRepoList();" 
               :disabled="this.selected_pkgs.length == 0" 
               v-bind="props" variant="text" icon color="primary">
            <v-icon>mdi-content-copy</v-icon>
            <v-tooltip activator="parent" location="top">Copy</v-tooltip>
        </v-btn>
        </template>
        <v-card>
            <v-card-title> 
                <span class="text-h5" v-if="this.promote!==undefined">Promote Package</span>
                <span class="text-h5" v-else>Copy to Another Repository</span>
            </v-card-title>
            <v-card-text>
            <v-container>
                <v-row>
                <v-col v-if="this.promote!==undefined" cols="12">

                    Promote {{this.selected_pkgs.length}} packages to {{this.repo_promote_uid}}
                </v-col>
                <v-col v-else cols="12">
                    <v-autocomplete
                        v-model="copy_to_repo_uid"
                        :items="all_repos"
                        outlined
                        dense
                        label="Destination"
                    ></v-autocomplete>
                </v-col>
                </v-row>
            </v-container>
            <v-progress-linear v-model="dialog_progress" buffer-value=0 color="green"></v-progress-linear>
            <div class="text-red">{{dialog_error_messages}}</div>
            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn  color="blue-darken-1"  text  @click="dialog = false">Cancel</v-btn>
            <v-btn  color="blue-darken-1"  text  @click="copyPackages()">
                <span v-if="this.promote!==undefined">Promote</span>
                <span v-else>Copy</span>
            </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>


<script lang="ts">

    import PackageDataService from "../services/package_service";
    import RepoDataService from "../services/repo_service";
    import {logger} from '@/logger.ts'

    export default {
        name: "add-repo",
        props: ['selected_pkgs', 'repo_uid', 'repo_type', 'promote', 'repo_promote_uid'],
        data() {
            return {
                dialog: false,
                dialog_progress: 0,
                dialog_error_messages: '',
                all_repos: [],
                copy_to_repo_uid: [],
            
            };
        },
        methods: {
            resetDialog() {

                this.dialog_progress = 0;
                this.dialog_error_messages = '';
                logger.debug("Reset dialog");
            },
            waitFor(conditionFunction) {

                const poll = resolve => {
                    if(conditionFunction()) resolve();
                    else setTimeout(_ => poll(resolve), 400);
                }

                return new Promise(poll);
            },

            loadRepoList() {
                console.log(this.promote)
                this.all_repos = []
                RepoDataService.getAll()
                .then(response => {
                    // Only insert repos that have either the same repo type (e.g., "deb" or "rpm") or
                    // generic file repos.  It wouldn't make sense to copy a deb to an rpm or vice-versa
                    response.data.results.forEach(function(repo) {
                        if ((repo.repo_type == this.repo_type || repo.repo_type == "files") && 
                            repo.repo_uid != this.repo_uid)
                        {
                            this.all_repos.push(repo.repo_uid);
                        }
                    }, this)
                    logger.debug(response.data);
                })
                .catch(e => {
                    logger.debug(e);
                });
            },
            copyPackages() {
                logger.debug("Copy packages");

                let copy_error = false;
                let count = 0;
                this.resetDialog();

                this.selected_pkgs.forEach(function(package_uid) {

                    if (this.promote !== undefined)
                        this.copy_to_repo_uid = [this.repo_promote_uid];

                    PackageDataService.copy(this.repo_uid, package_uid, this.copy_to_repo_uid)
                    .then(response => {
                        count++;
                        logger.debug("Success Copying file");
                        this.dialog_progress = (count / this.selected_pkgs.length) * 100.0;

                    })
                    .catch(e => {
                        count++;
                        logger.debug(e);
                        copy_error = true;
                        if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                            this.dialog_error_messages = e.response.data.detail;
                        else
                            this.dialog_error_messages = 'Error copying file: ' + e.message;

                    });


                }, this);

                // Copies and responses are async.  So, use this function to wait for them to complete
                // using "count" as a proxy for the operations to be done.
                this.waitFor(_ => count >= this.selected_pkgs.length)
                .then(_ => {
                    logger.debug('All copies complete')

                    // If no error, close the dialog
                    if (!copy_error)
                    {
                        this.$emit('copy_success');
                        this.dialog = false;
                    }
                });
            },
            
        }
    };
    
    </script>

    
    
    <style scoped>
 
    </style>