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
  