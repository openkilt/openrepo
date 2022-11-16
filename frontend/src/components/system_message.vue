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
  
    <v-snackbar
    v-model="this.show"
    :timeout="timeout_ms"
    >  
    {{ message }}

    <template v-slot:actions>
        <v-btn
        color="blue"
        variant="text"
        @click="this.show = false"
        >
        Close
        </v-btn>
    </template>
    </v-snackbar>
      
  </template>
  
  <script lang="ts">
  import NavBar from '@/components/nav_bar.vue'
  import { defineComponent } from 'vue'
  
  export default {
    name: 'App',
    props: [ 'message'],
    components: {
      NavBar
    },
    watch: { 
        message: function(newVal, oldVal) { // watch it
            this.show = true;
        }
    },
    data() {
      return {
        show: false,
        timeout_ms: 5000,
      }
    },
    methods: {
    }
  
  }
  </script> 
  