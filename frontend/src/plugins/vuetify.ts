import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createVuetify } from 'vuetify'

const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('openrepo_theme') : null;

export default createVuetify({
  theme: {
    defaultTheme: savedTheme || 'openRepoLight',
    themes: {
      openRepoLight: {
        dark: false,
        colors: {
          background: '#F5F5F5',
          surface: '#FFFFFF',
          primary: '#3B6CB7',
          secondary: '#4E8A7B',
          accent: '#7E6B9E',
          error: '#C94A4A',
          info: '#3686B3',
          success: '#4A8C6A',
          warning: '#BD863C',
        }
      },
      openRepoDark: {
        dark: true,
        colors: {
          background: '#121212',
          surface: '#1E1E1E',
          primary: '#7BA3D4',
          secondary: '#7DB8A8',
          accent: '#B09FD4',
          error: '#D46969',
          info: '#5D99C4',
          success: '#6DAE89',
          warning: '#CCA04A',
        }
      }
    }
  },
})
