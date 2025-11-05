/** @type {import('tailwindcss').Config} */
module.exports = {
  // =============================================================================
  // Content - Files to scan for classes
  // =============================================================================
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/src/js/**/*.js",
  ],

  // =============================================================================
  // Dark mode - Class-based strategy
  // =============================================================================
  darkMode: 'class', // Toggle with class on <html> element

  // =============================================================================
  // Theme customization
  // =============================================================================
  theme: {
    extend: {
      // Colors - KeePassXC Web Manager color palette
      colors: {
        // Primary brand colors
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Success states
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // Warning states
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Danger/Error states
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // Security score colors
        security: {
          excellent: '#22c55e',
          good: '#84cc16',
          fair: '#eab308',
          weak: '#f97316',
          critical: '#ef4444',
        }
      },

      // Spacing
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },

      // Typography
      fontSize: {
        'xxs': '0.625rem',
      },

      // Border radius
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },

      // Animations
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'fade-out': 'fadeOut 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 2s linear infinite',
      },

      // Keyframes
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },

      // Box shadow
      boxShadow: {
        'inner-lg': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.1)',
      },

      // Z-index layers
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
    },
  },

  // =============================================================================
  // Plugins
  // =============================================================================
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],

  // =============================================================================
  // Safelist - Classes to always include
  // =============================================================================
  safelist: [
    // Security score colors
    'bg-security-excellent',
    'bg-security-good',
    'bg-security-fair',
    'bg-security-weak',
    'bg-security-critical',
    'text-security-excellent',
    'text-security-good',
    'text-security-fair',
    'text-security-weak',
    'text-security-critical',
    // Dynamic grid columns
    'grid-cols-1',
    'grid-cols-2',
    'grid-cols-3',
    'grid-cols-4',
    'grid-cols-6',
    'grid-cols-12',
  ],
}
