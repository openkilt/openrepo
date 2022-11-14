
import { createStore } from 'vuex'


// Create a new store instance for app-wide data
export default createStore({
    state () {
      return {
        username: '',
        is_superuser: false,
      }
    },
    mutations: {
      set_user (state, userdata) {
        state.username = userdata.username;
        state.is_superuser = userdata.is_superuser;
      }
    }
  })