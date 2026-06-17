import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createVuetify } from 'vuetify'

export default createVuetify({
  theme: {
    defaultTheme: 'openRepoLight',
    themes: {
      openRepoLight: {
        dark: false,
        colors: {
          background: '#F5F5F5',
          surface: '#FFFFFF',
          primary: '#1565C0',
          secondary: '#00897B',
          accent: '#7C4DFF',
          error: '#E53935',
          info: '#039BE5',
          success: '#43A047',
          warning: '#FB8C00',
        }
      },
      openRepoDark: {
        dark: true,
        colors: {
          background: '#121212',
          surface: '#1E1E1E',
          primary: '#42A5F5',
          secondary: '#4DB6AC',
          accent: '#B388FF',
          error: '#EF5350',
          info: '#29B6F6',
          success: '#66BB6A',
          warning: '#FFA726',
        }
      }
    }
  },
})
