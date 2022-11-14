<template>



    <v-dialog max-width="700" v-model="dialog">
        <template v-slot:activator="{ props }">

            <v-btn @click="resetDialog()" variant="text" v-bind="props" icon color="primary">
                <v-icon>mdi-cloud-upload-outline</v-icon>
                <v-tooltip activator="parent" location="top">Upload Package</v-tooltip>
            </v-btn>
        </template>
        <v-card>
            <v-card-title>
            <span class="text-h5">Upload Package Files</span>
            </v-card-title>
            <v-card-text>
            <v-container>
                <v-row>
                <v-col cols="12">
                    <v-file-input :accept=FILE_TYPES[this.repo_type] 
                        v-model="upload_file_list" counter  multiple 
                        chips  show-size truncate-length="32" ></v-file-input>
                </v-col>
                </v-row>
                <v-row>
                <v-col cols="12">
                    <v-checkbox label="Overwrite duplicate package" v-model="overwrite" value="overwrite"></v-checkbox>
                </v-col>
                </v-row>
            </v-container>
            <v-progress-linear v-model="dialog_progress" buffer-value=0 color="green"></v-progress-linear>
            <div class="text-red">{{dialog_error_messages}}</div>
            </v-card-text>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn  color="blue-darken-1"  text  @click="dialog = false">Cancel</v-btn>
            <v-btn  color="blue-darken-1"  text  @click="uploadPackages()">Upload</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>


<script lang="ts">

    import RepoDataService from "../services/repo_service"; 
    import {logger} from '@/logger.ts'

    export default {
        name: "add-repo",
        props: [ 'repo_uid', 'repo_type'],
        data() {
            return {
                dialog: false,
                dialog_progress: 0,
                dialog_error_messages: '',
                overwrite: false,
            
                upload_file_list: [],
                FILE_TYPES: {
                    'deb': '.deb',
                    'rpm': '.rpm',
                    'generic': '*'
                },
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
                
            uploadPackages() {
                logger.debug("Do upload");
                let upload_error = false;
                let count = 0;
                this.resetDialog();

                this.upload_file_list.forEach(function(upload_file) {

                    RepoDataService.upload(this.repo_uid, upload_file, this.overwrite)
                    .then(response => {
                        count++;
                        logger.debug("Success Uploading file");
                        this.dialog_progress = (count / this.upload_file_list.length) * 100.0;

                    })
                    .catch(e => {
                        count++;
                        logger.debug(e);
                        upload_error = true;
                        if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                            this.dialog_error_messages = e.response.data.detail;
                        else
                            this.dialog_error_messages = 'Error uploading file: ' + e.message;
                    });


                    logger.debug(upload_file);
                }, this);

                // Uploads and responses are async.  So, use this function to wait for them to complete
                // using "count" as a proxy for the operations to be done.
                this.waitFor(_ => count >= this.upload_file_list.length)
                .then(_ => {
                    logger.debug('All uploads complete')

                    this.$emit('uploads_complete')
                    // If no error, close the dialog
                    if (!upload_error)
                    {
                        this.dialog = false;
                    }
                });

            },
            
        }
    };
    
    </script>

    
    
    <style scoped>
 
    </style>