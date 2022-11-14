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
