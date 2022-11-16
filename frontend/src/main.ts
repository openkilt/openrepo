/**
 * Copyright 2022 by Open Kilt LLC. All rights reserved.
 * This file is part of the OpenRepo Repository Management Software (OpenRepo)
 * OpenRepo is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License
 * version 3 as published by the Free Software Foundation
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

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

