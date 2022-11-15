<template>


    <v-dialog max-width="700" v-model="dialog">
        <template v-slot:activator="{ props }">


        <v-btn @click="resetDialog();" v-bind="props" variant="text" icon color="primary">
            <v-icon>mdi-plus-thick</v-icon>
            <v-tooltip activator="parent" location="top">Create Repository</v-tooltip>
        </v-btn>
        </template>
        <v-card>
            <v-card-title>
            <span class="text-h5">Create New Repository</span>
            </v-card-title>
            <v-card-text>
            <v-container>
                <v-row>
                <v-col cols="12">

                    <v-text-field v-model="repo.repo_uid" 
                        :error-messages="repo_error_response.repo_uid"
                        label="Repo Unique ID"></v-text-field>
                        <v-select
                        v-model="repo.repo_type"
                        :error-messages="repo_error_response.repo_type"
                        :items="option_repo_types"
                        item-title="text"
                        item-value="value"
                        label="Select"
                        persistent-hint
                        single-line
                        ></v-select>

                </v-col>
                </v-row>

                <v-row wrap>
                    <v-col cols="12" class="py-0 my-0">
                        <div>
                            <div align="right">
                                <router-link to="/cfg/signing_keys">Manage Signing Keys</router-link>
                            </div>
                            <v-autocomplete
                                    v-model="repo.signing_key"
                                    :items="all_pgp_keys"
                                    item-title="display"
                                    item-value="val"
                                    :error-messages="repo_error_response.signing_key"
                                    outlined
                                    dense
                                    label="Signing Key"
                                ></v-autocomplete>
                        </div>
                    </v-col>
                </v-row>
            </v-container>

            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn  color="blue-darken-1"  text  @click="dialog = false">Cancel</v-btn>
            <v-btn  color="blue-darken-1"  text  @click="create_repo()">Create Repo</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>


<script lang="ts">

    import {logger} from '@/logger.ts'
    import RepoDataService from "../services/repo_service";
    import SigningKeyDataService from "../services/signingkey_service";

    export default {
    name: "add-repo",
    data() {
        return {
            dialog: false,
            repo: {
                repo_uid: "",
                repo_type: "deb",
                signing_key: ""
            },
            repo_error_response: {
                repo_uid: "",
                repo_type: "",
            },
            all_pgp_keys: [ ],
            //option_repo_type: { text: 'Debian/APT', value: 'deb' },
            option_repo_types: [
                { text: 'Debian/APT', value: 'deb' },
                { text: 'Red Hat/RPM', value: 'rpm' },
                { text: 'Generic Files', value: 'files' },
            ],
            //submitted: false
        };
    },
    methods: {
        resetDialog() {
            this.repo_uid = ''
            this.repo_type = 'deb'
            this.signing_key = ''
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
                this.pgp_keys = response.data.results;
                logger.debug(response.data);
            })
            .catch(e => {
                logger.debug(e);
            });
        },
        create_repo() {
            var data = {
                repo_uid: this.repo.repo_uid,
                repo_type: this.repo.repo_type,
                signing_key: this.repo.signing_key
            };

            RepoDataService.create(data)
            .then(response => {
                this.repo.repo_uid = response.data.repo_uid;
                console.log(response.data);
                //this.submitted = true;

                // Tell the parent we are successful and dialog is closing
                this.$emit('create_success');
                this.dialog = false;
            })
            .catch(e => {
                this.repo_error_response = e.response.data
                console.log(e);
            });
        },
        
    },
    mounted() {
        this.loadPgpKeys();
    }
    };
    
    </script>

    
    
    <style scoped>
 
    </style>