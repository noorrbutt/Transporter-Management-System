/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        // Core surfaces
        canvas: '#FAFAF9',
        surface: '#FFFFFF',
        // Sidebar / chrome — deep slate, not pure black
        ink: {
          950: '#0B1220',
          50: '#F8FAFC',
          900: '#0F172A',
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
          500: '#64748B',
          400: '#94A3B8',
          300: '#CBD5E1',
          200: '#E2E8F0',
          100: '#F1F5F9',
        },
        // Signature accent — safety-orange, used sparingly for actions/emphasis
        accent: {
          600: '#C2410C',
          500: '#EA580C',
          400: '#F97316',
          100: '#FFEDD5',
          50: '#FFF7ED',
        },
        // Semantic status — compliance/violations are core to this app
        status: {
          good: '#15803D',
          'good-bg': '#DCFCE7',
          'good-border': '#86EFAC',
          warn: '#B45309',
          'warn-bg': '#FEF3C7',
          'warn-border': '#FCD34D',
          bad: '#B91C1C',
          'bad-bg': '#FEE2E2',
          'bad-border': '#FCA5A5',
          info: '#1D4ED8',
          'info-bg': '#DBEAFE',
          'info-border': '#93C5FD',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.06)',
        'card-hover': '0 4px 12px -2px rgba(15, 23, 42, 0.10)',
      },
      borderRadius: {
        card: '10px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
