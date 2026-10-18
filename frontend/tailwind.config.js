/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0B1620',
          panel: '#101E2B',
          border: '#1E3040',
        },
        signal: {
          teal: '#33D6B0',
          tealDim: '#1D8A72',
          amber: '#F2A93B',
          coral: '#FF6B6B',
        },
        text: {
          primary: '#EAF3F1',
          muted: '#7E93A0',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
