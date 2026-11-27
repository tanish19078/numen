/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        numen: {
          canvas: '#F7FAF8',
          surface: '#FFFFFF',
          subtle: '#F1F6F3',
          line: '#E2EBE5',
          pine: '#0B1F16',
          sage: '#526B5D',
          stone: '#849B8E',
          emerald: '#059669',
          mintWash: '#ECFDF5',
          cardPine: '#0D261C',
          cardMint: '#6EE7B7',
          threat: '#DC2626',
          threatWash: '#FEF2F2',
          review: '#D97706',
          reviewWash: '#FFFBEB',
          cobalt: '#2563EB',
          cobaltWash: '#EFF6FF',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
