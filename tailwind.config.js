/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#eef7f6',
          100: '#d5ece9',
          200: '#aedad5',
          300: '#7cc1ba',
          400: '#4ba29a',
          500: '#2d857f',
          600: '#1f6a67',
          700: '#1a5453',
          800: '#174443',
          900: '#143838',
          950: '#082525',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(15, 42, 40, 0.06), 0 1px 2px rgba(15, 42, 40, 0.04)',
      },
      keyframes: {
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.35s ease-out both',
      },
    },
  },
  plugins: [],
};
