/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sp: {
          black:    '#0d0d0d',
          dark:     '#121212',
          surface:  '#1a1a1a',
          surface2: '#252525',
          surface3: '#2e2e2e',
          green:    '#1db954',
          greenhov: '#1ed760',
          text:     '#e4e4e4',
          sub:      '#b3b3b3',
          muted:    '#666666',
          border:   '#2a2a2a',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
