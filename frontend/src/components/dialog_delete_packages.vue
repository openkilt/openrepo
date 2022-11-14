<template>



    <v-dialog v-model="dialog" max-width="400">
        <template v-slot:activator="{ props }">
            <v-btn @click="resetDialog()" :disabled="selected_pkgs.length == 0" v-bind="props" variant="text" icon color="error">
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
                    Confirm that you wish to delete {{selected_pkgs.length}} package<span v-if="selected_pkgs.length > 1">s</span>.
                </div>

                <v-progress-linear v-model="dialog_progress" buffer-value=0 color="red"></v-progress-linear>
                <div class="text-red">{{dialog_error_messages}}</div>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="green darken-1" text @click="dialog = false">Cancel</v-btn>
                <v-btn color="green darken-1" text @click="deletePackages();">Yes</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>


<script lang="ts">

    import PackageDataService from "../services/package_service";
    import {logger} from '@/logger.ts'

    export default {
        name: "add-repo",
        props: ['selected_pkgs', 'repo_uid'],
        data() {
            return {
                dialog: false,
                dialog_progress: 0,
                dialog_error_messages: '',
            
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
            
            deletePackages() {
                logger.debug("DO DELETE");
                let delete_error = false;
                let count = 0
                this.resetDialog();

                for (let i = this.selected_pkgs.length - 1; i >= 0; i--) {
                    let pkg_uid = this.selected_pkgs[i];

                    PackageDataService.delete(this.repo_uid, pkg_uid)
                    .then(response => {
                        count++;
                        logger.debug("Success deleting " + pkg_uid);
                        this.dialog_progress = (count / this.selected_pkgs.length) * 100.0;

                    })
                    .catch(e => {
                        count++;
                        logger.debug(e);
                        delete_error = true;
                        if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                            this.dialog_error_messages = e.response.data.detail;
                        else
                            this.dialog_error_messages = 'Error deleting file: ' + e.message;
                    });
                }


                // http requests and responses are async.  So, use this function to wait for them to complete
                // using "count" as a proxy for the operations to be done.
                this.waitFor(_ => count >= this.selected_pkgs.length)
                .then(_ => {
                    logger.debug('All deletes complete');

                    // If no error, close the dialog
                    if (!delete_error)
                    {
                        this.dialog  = false;
                        this.$emit('delete_success');
                    }
                });

            },
            
        }
    };
    
    </script>

    
    
    <style scoped>
 
    </style>