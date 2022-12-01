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
    <SystemMessage 
      :message="this.show_global_error_msg" />
    <v-container class="my-5">

        <v-layout row>

            <v-col sm="12">
                <h3>User Info</h3>
                <v-divider></v-divider>
            </v-col>

        </v-layout>

        <v-layout row>

            <v-col sm="1">
            </v-col>
            <v-col sm="11">
              <div>
                <strong>User:</strong> <span>{{user_info.username}}</span>
              </div>
              <div>
                <strong>API Key:</strong> <span>{{user_info.api_key}}</span>

                <v-dialog v-model="dialog_instructions_api" max-width="800">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" variant="text" icon color="primary">
                            <v-icon>mdi-api</v-icon>
                            <v-tooltip activator="parent" location="top">Repo Instruction</v-tooltip>
                        </v-btn>
                    </template>
                    <v-card>
                        <v-card-title class="text-h5">
                            Repo Instructions
                        </v-card-title>
                        <v-card-text>
                          <div>
                            All repo operations available in the Web UI are also available via REST API.  Below is an example using 
                          curl to list all repositories using your user account's unique authentication Token:

                        </div>

                            <pre class="block bg-grey-darken-4 text-grey-lighten-3 pa-5 whitespace-pre overflow-auto">{{user_info.instructions_api}}</pre>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="green darken-1" @click="copyInstructionsToClipboard(this.instructions_api);" text>Copy to Clipboard</v-btn>
                            <v-btn color="green darken-1" @click="dialog_instructions_api = false;" text>Close</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>


                <v-dialog v-model="dialog_instructions_cli" max-width="800">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" variant="text" icon color="primary">
                            <v-icon>mdi-console</v-icon>
                            <v-tooltip activator="parent" location="top">Repo Instruction</v-tooltip>
                        </v-btn>
                    </template>
                    <v-card>
                        <v-card-title class="text-h5">
                            Repo Instructions
                        </v-card-title>
                        <v-card-text>
                          <div>
                            All repo operations available in the Web UI are also available via the OpenRepo Command Line Utility.  
                            Below is an example using the CLI program to list all repositories using your user account's unique authentication Token:

                        </div>

                            <pre class="block bg-grey-darken-4 text-grey-lighten-3 pa-5 whitespace-pre overflow-auto">{{user_info.instructions_cli}}</pre>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="green darken-1" @click="copyInstructionsToClipboard(this.instructions_cli);" text>Copy to Clipboard</v-btn>
                            <v-btn color="green darken-1" @click="dialog_instructions_cli = false;" text>Close</v-btn>
                        </v-card-actions>
                    </v-card>
                </v-dialog>

              </div>
              <div><a href="/back/change-password/">Change Password</a></div>
            </v-col>

        </v-layout>


    </v-container>
</template>
  
  <script>
  import {logger} from '@/logger.ts'
  
  import SystemMessage from '@/components/system_message.vue'
  import UserDataService from '@/services/user_service'

  export default {
    name: "User Info",
    components: {
      SystemMessage
    },
    data() {
      return {
        repos: [],
        show_global_error_msg: '',
        dialog_instructions_cli: false,
        dialog_instructions_api: false,

        user_info: {},
      };
    },
    methods: {
      get_user_info() {

        UserDataService.whoAmI()
        .then(response => {
              this.user_info = response.data;
              this.user_info.instructions_api = "curl -s -X GET " + window.location.origin + "/api/repos/ \\\n" + 
                                                "     -H 'Authorization: Token " + this.user_info.api_key + "'";
              this.user_info.instructions_cli = "export OPENREPO_SERVER=" + window.location.origin + "\n" +
                                                "export OPENREPO_APIKEY=" + this.user_info.api_key + "\n" +
                                                "openrepo list_repos" ;
              logger.debug(this.user_info);
          })
          .catch(e => {
              logger.debug(e);
              show_global_error_msg = "Error retrieving user information";

          });
      },
      copyInstructionsToClipboard (instructions) {
          navigator.clipboard.writeText(instructions);
      },
    },
    mounted() {
      this.get_user_info();
    }
  };
  </script>
  

