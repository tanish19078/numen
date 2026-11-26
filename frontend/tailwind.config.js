/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        numen: {
          bg: '#F6FBF5',
          card: '#FFFFFF',
          mint: '#8CE563',
          mintSoft: '#E8F8E2',
          green: '#15803D',
          forest: '#0D2616',
          sage: '#4A6653',
          border: '#CDE4C8',
        },
      },
      fontFamily: {
        sans: ['"Segoe UI"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Consolas', '"Cascadia Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
