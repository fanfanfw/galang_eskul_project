/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2E7D32',
        secondary: '#4CAF50',
        accent: '#FFC107',
        'light-green': '#E8F5E8',
      }
    },
  },
  plugins: [],
  // Optimize build performance
  important: false,
  future: {
    hoverOnlyWhenSupported: true,
  },
}