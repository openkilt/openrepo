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
    <v-container class="my-5">

        <v-layout row wrap>
            <v-col cols="12" align="left">
                <v-breadcrumbs :items="breadcrumbs">
                </v-breadcrumbs>
            </v-col>
        </v-layout>
        <v-divider></v-divider>

        <v-card  flat v-for="pgp_key in pgp_keys" :key="pgp_key.email">

            
            <v-layout row wrap class="pgp_key">
                <v-col sm="9">
                    <strong>{{pgp_key.name}} &lt;{{ pgp_key.email }}&gt;</strong>
                    <div class="text-caption">{{pgp_key.fingerprint}}</div>
                    <div class="text-caption">Created {{ this.timeAgo.format(new Date(pgp_key.creation_date)) }}</div>
                </v-col>

                <v-col  align="right" sm="3">

                    <!-- delete button -->
                    <v-dialog v-model="dialog_delete" max-width="400">
                        <template v-slot:activator="{ props }">
                            <v-btn @click="resetDialog()" v-bind="props" variant="text" icon color="error">
                                <v-icon>mdi-delete</v-icon>
                                <v-tooltip activator="parent" location="top">Delete</v-tooltip>
                            </v-btn>
                        </template>
                        <v-card>
                            <v-card-title class="text-h5">
                                Are you sure?
                            </v-card-title>
                            <v-card-text>
                                <div class="mb-5">
                                    Confirm that you wish to delete this signing key.
                                </div>

                                <div class="text-red">{{dialog_delete_error_messages}}</div>
                            </v-card-text>
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn color="green darken-1" text @click="dialog_delete = false">Cancel</v-btn>
                                <v-btn color="green darken-1" text @click="deleteKey(pgp_key.fingerprint);">Yes</v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>

                </v-col>
            </v-layout>
            <v-divider></v-divider>
        </v-card>

        <v-layout row wrap>
            <v-col cols="12" align="right">


                <v-dialog max-width="700" v-model="dialog_newkey">
                    <template v-slot:activator="{ props }">

                    <v-btn @click="resetDialog();" v-bind="props" color="primary">
                        New Signing Key
                    </v-btn>
                    </template>
                    <v-card>
                        <v-card-title>
                        <span class="text-h5">Create New Key</span>
                        </v-card-title>
                        <v-card-text>
                        <v-container>
                            <v-row>
                            <v-col cols="12">

                                <v-text-field v-model="dialog_create_key_data.name" 
                                    :error-messages="newkey_error_response.name"
                                    label="Name"></v-text-field>

                                <v-text-field v-model="dialog_create_key_data.email" 
                                    :error-messages="newkey_error_response.email"
                                    label="E-Mail"></v-text-field>

                            </v-col>
                            </v-row>
                            <v-row>
                            <v-col cols="12">
                                <em>* Existing PGP keys can be imported manually via CLI command: <strong>manage.py import_pgp_private_key</strong></em>
                            </v-col>
                            </v-row>
                            <v-row>
                            <v-col cols="12">
                                <v-progress-linear
                                indeterminate
                                :hidden="dialog_newkey_isidle"
                                color="grey"
                                ></v-progress-linear>
                            </v-col>
                            </v-row>
                        </v-container>

                        </v-card-text>
                        <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn  color="blue-darken-1"  text  @click="dialog_newkey = false">Cancel</v-btn>
                        <v-btn  color="blue-darken-1"  text  @click="create_key()">Create Key</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>
            </v-col>
        </v-layout>
    </v-container>
    </v-app>
</template>

<script lang="ts">

import {logger} from '@/logger.ts'
import SigningKeyDataService from "../services/signingkey_service";

export default {
    name: "Manage Signing Keys",
    components: {
    },
    data() {
        return {
            dialog_newkey: false,
            dialog_newkey_isidle: true,
            dialog_delete: false,
            dialog_delete_error_messages: '',
            dialog_create_key_data: {
                name: '',
                email: ''
            },
            newkey_error_response: {
                name: '',
                email: ''
            },
            form_disabled: true,
            pgp_keys: [],

            breadcrumbs: [
                {
                title: 'Repositories',
                disabled: false,
                to: '/',
                },
                {
                title:  "Manage Signing Keys",
                disabled: true,
                to: this.$route.path,
                },
            ],
        };
    },
    methods: {
        resetDialog() {
            this.dialog_newkey_isidle = true;
            this.dialog_create_key_data.name = '';
            this.dialog_create_key_data.email = '';
        },
        loadPgpKeys() {
            this.keys = []
            SigningKeyDataService.getAll()
            .then(response => {
                // Only insert repos that have either the same repo type (e.g., "deb" or "rpm") or
                // generic file repos.  It wouldn't make sense to copy a deb to an rpm or vice-versa
                this.pgp_keys = response.data.results;
                logger.debug(response.data);
            })
            .catch(e => {
                logger.debug(e);
            });
        },
        create_key() {

            this.dialog_newkey_isidle = false;
            SigningKeyDataService.create(this.dialog_create_key_data.name, this.dialog_create_key_data.email)
            .then(response => {
                this.loadPgpKeys();

                this.dialog_newkey = false;
            }) 
            .catch(e => {
                this.newkey_error_response = e.response.data
                this.dialog_newkey_isidle = false;  
                console.log(e);
            });
        },

        deleteKey(fingerprint: string) {


            SigningKeyDataService.delete(fingerprint)
            .then(response => {
                this.loadPgpKeys();
                this.dialog_delete = false;

            })
            .catch(e => { 
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                    this.dialog_delete_error_messages = e.response.data.detail;
                else
                    this.dialog_delete_error_messages = 'Error deleting key: ' + e.message;
            });
            
        },
    },
    mounted() {
        this.loadPgpKeys();
    }
}

</script>

<style>

</style>