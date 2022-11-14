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

                <v-dialog v-model="dialog_instructions" max-width="600">
                    <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" variant="text" icon color="primary">
                            <v-icon>mdi-information-outline</v-icon>
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
                          curl to grab user information using your user account's unique authentication Token:

                        </div>

                            <pre class="block bg-grey-darken-4 text-grey-lighten-3 pa-5 whitespace-pre overflow-auto">{{user_info.instructions}}</pre>
                        </v-card-text>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn color="green darken-1" @click="copyCurlInstructionsToClipboard();" text>Copy to Clipboard</v-btn>
                            <v-btn color="green darken-1" @click="dialog_instructions = false;" text>Close</v-btn>
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
        dialog_instructions: false,

        user_info: {},
      };
    },
    methods: {
      get_user_info() {

        UserDataService.whoAmI()
        .then(response => {
              this.user_info = response.data;
              this.user_info.instructions = "curl -s -X GET " + window.location.origin + 
                                            "/api/whoami -H 'Authorization: Token " + 
                                            this.user_info.api_key + "'"
              logger.debug(this.user_info);
          })
          .catch(e => {
              logger.debug(e);
              show_global_error_msg = "Error retrieving user information";

          });
      },
      copyCurlInstructionsToClipboard () {
          navigator.clipboard.writeText(this.user_info.instructions);
      },
    },
    mounted() {
      this.get_user_info();
    }
  };
  </script>
  

