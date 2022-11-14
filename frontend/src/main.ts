import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import vuetify from './plugins/vuetify'
import { router } from './router'
import { loadFonts } from './plugins/webfontloader'
import {VueLogger, vlOptions} from './logger.js'
import TimeAgo from 'javascript-time-ago'
import en from 'javascript-time-ago/locale/en'

loadFonts()



const app = createApp(App)
app
.use(vuetify)
.use(router)
.use(VueLogger, vlOptions)
.use(store)
.mount('#app')

// Setup "TimeAgo" module globally with english locale
TimeAgo.addDefaultLocale(en)
app.config.globalProperties.timeAgo = new TimeAgo('en-US');

