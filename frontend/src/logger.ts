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

import VueLogger from 'vuejs3-logger'
import { createApp } from 'vue'

const isProduction = process.env.NODE_ENV === 'production';

const vlOptions = {
    isEnabled: true,
    logLevel : isProduction ? 'info' : 'debug',
    stringifyArguments : false,
    showLogLevel : true,
    showMethodName : true,
    separator: '|',
    showConsoleColors: true
};

// create a dummy app that can be used as logger in other js modules
const app = createApp({})
app.use(VueLogger, vlOptions);
const logger = app.config.globalProperties.$log;

export {VueLogger, vlOptions, logger};
