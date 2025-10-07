import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './pages/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#FF6B35',
          dark: '#E55A2B',
          light: '#FF8555'
        },
        dark: {
          DEFAULT: '#0A0A0A',
          secondary: '#1A1A1A',
          tertiary: '#2A2A2A'
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-orange': 'linear-gradient(135deg, #FF6B35 0%, #F7931E 100%)',
        'gradient-dark': 'linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%)',
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography')
  ]
} satisfies Config
