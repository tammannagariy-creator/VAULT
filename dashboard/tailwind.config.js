/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: { mono: ['JetBrains Mono', 'Fira Code', 'monospace'] },
      colors: {
        vault: {
          bg: '#0a0a0f',
          panel: '#11111b',
          border: '#1e1e2e',
          green: '#a6e3a1',
          red: '#f38ba8',
          yellow: '#f9e2af',
          blue: '#89b4fa',
          purple: '#cba6f7',
          text: '#cdd6f4',
          muted: '#6c7086',
        },
      },
    },
  },
  plugins: [],
};
