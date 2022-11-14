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
                        <v-col cols="12" class="pb-0 mb-6">
                        <v-select
                        v-model="selected_build"
                        :items="build_list"
                        item-title="build_number"
                        item-value="build_number"
                        label="Build Number"
                        return-object
                        ></v-select>
                        </v-col>
                    </v-layout>
                    
                    <v-layout row wrap>
                            <v-col  class="text-left  " cols="6">
                                <strong>Build {{build_details.build_number}}</strong> - {{build_details.completion_status}}
                            </v-col>

                            <v-col  class="text-right  " cols="6">
                                {{this.build_summary.num_errors}} errors and {{this.build_summary.num_warnings}} warnings
                            </v-col>

                    </v-layout>
                    
                    <v-layout row wrap>
                        <v-col  class="text-left mt-0 pt-0 mb-5 " cols="12">
                            <span class="text-caption">Started {{this.moment(build_details.timestamp).fromNow() }}</span>
                        </v-col>
                    </v-layout>
                    <v-divider></v-divider>

                    <v-card flat v-for="log_line in this.log_lines" :key="log_line.line_number"
                      class="log_line" :class="log_line.loglevel">

                        <v-layout row wrap>
                            <v-col  class="text-left  " cols="10">

                                <span class="line_number mr-3">{{log_line.line_number}}</span> 
                                <span>{{log_line.command}}</span>
                            </v-col>
                            <v-col  align="right" cols="2">
                                <div v-if="log_line.exec_complete" class="text-caption">
                                    {{  parseFloat(log_line.execution_time_sec * 1000.0).toFixed(2) }} ms
                                </div>
                                <div v-else>
                                    <v-progress-circular
                                    indeterminate
                                    color="primary"
                                    ></v-progress-circular>
                                </div>
                            </v-col>
                        </v-layout>

                        <v-layout row wrap v-if="log_line.message != ''">
                            <v-col align="left" class="mt-0 pt-3 log_message" cols="12">
                                <pre class="ml-8 mt-0  pa-2 ">{{ log_line.message }}</pre>
                            </v-col>
                        </v-layout>
                        <v-divider></v-divider>
                    </v-card>


                    
                </v-card>

            </v-col>
        </v-layout>

    </v-container>
    </v-app>
</template>

<script lang="ts">

import BuildLogDataService from "../services/buildlog_service";
import {logger} from '@/logger.ts'
import SystemMessage from '@/components/system_message.vue'
import moment from 'moment'

export default {
    name: "Repo Settings View",
    components: {
      SystemMessage
    },
    data() {
        return {
            repo_uid: this.$route.params.repo_uid,
            repo_details: {},
            build_list: [],
            selected_build: '',
            build_details: '',
            moment: moment,
            lines_already_retrieved: 0,
            build_summary: {
                'summary_loaded': false,
                'num_errors': 0,
                'num_warnings': 0,
                'num_logentries': 0,
                'in_progress': false
            },
            log_lines: [],
            show_global_error_msg: '',
            all_pgp_keys: [ ],
            form_disabled: true,
            active_timer: 0,
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
                title:  "Build Status",
                disabled: true,
                to: this.$route.path,
                },
            ],
        };
    },
    methods: {

        retrieveBuildList() {
            BuildLogDataService.getBuildList(this.repo_uid)
            .then(response => {
                this.lines_already_retrieved = 0;
                this.build_list = response.data.results.reverse();
                if (this.build_list.length > 0)
                    this.selected_build = this.build_list[0];
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
        refresh_build()
        {
            BuildLogDataService.getBuild(this.repo_uid, this.selected_build.build_number)
            .then(response => {
                logger.debug(response.data);

                this.build_details = response.data.results[0];
                if (this.build_details.completion_status == 'running')
                {
                    this.loadLogLines();
                    this.active_timer = setTimeout(this.refresh_build, 2000);
                }
                else if (this.log_lines.length == 0)
                {
                    this.loadLogLines();
                }
            })
            .catch(e => {   
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                this.show_global_error_msg = e.response.data.detail;
                else
                this.show_global_error_msg = 'Error loading repos: ' + e.message;
                
                logger.debug(e);
            });
        },
        updateSummary() {

            this.build_summary.summary_loaded = true;
            this.build_summary.num_errors = 0;
            this.build_summary.num_warnings = 0;
            this.build_summary.num_logentries = 0;
                
            this.log_lines.forEach(log_line => {
                this.build_summary.num_logentries++;
                if (log_line.loglevel == "warning")
                    this.build_summary.num_warnings++;
                else if (log_line.loglevel == "error")
                    this.build_summary.num_errors++;  
            }, this);
        },
        loadLogLines() {
            logger.debug("Load Log Lines")
            BuildLogDataService.getBuildLogLines(this.repo_uid, this.selected_build.build_number, this.lines_already_retrieved)
            .then(response => {

                this.log_lines = this.log_lines.concat(response.data.results);
                this.lines_already_retrieved += response.data.results.length;
                logger.debug(this.log_lines);
                this.updateSummary();
            })
            .catch(e => {   
                if (typeof e.response != 'undefined' && typeof e.response.data.detail != 'undefined')
                this.show_global_error_msg = e.response.data.detail;
                else
                this.show_global_error_msg = 'Error loading repos: ' + e.message;
                
                logger.debug(e);
            });
        },
    },
    watch: {
        selected_build(old_selection, new_selection)
        {
            this.lines_already_retrieved = 0;
            this.log_lines = [];
            clearTimeout(this.active_timer);
            this.refresh_build();
        }
    },
    mounted() {
        this.retrieveBuildList();
        
    },
    unmounted() {
        console.log("UNMOUNTED");
        clearTimeout(this.active_timer);
    }
}

</script>

<style>


    .log_line.debug {
      border-left: 8px solid #b9b9b9;
    }
    .log_line.info {
      border-left: 8px solid #3a96d3;
    }
    .log_line.warning {
      border-left: 8px solid #d48529;
      background-color: #d4852922;
    }
    .log_line.error {
      border-left: 8px solid #df3f3f;
      background-color: #df3f3f22;
    }
    .line_number {
        color: gray;
    }
    .log_message {
        border-top:1px dashed gray;
    }
    .log_message pre {
        background-color: #eeeeee;
    }
</style>