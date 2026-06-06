/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        capsule: {
          50: '#f0f4ff',
          100: '#dce8ff',
          200: '#bdd4ff',
          300: '#90b4ff',
          400: '#6190fc',
          500: '#3d6ef8',
          600: '#2850ed',
          700: '#1f3dd9',
          800: '#2033b0',
          900: '#1e308a',
          950: '#161e55',
        },
      },
    },
  },
  plugins: [],
};
