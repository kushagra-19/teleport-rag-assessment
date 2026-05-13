/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#080810',
          surface: '#0f0f1a',
          elevated: '#161625',
          hover: '#1c1c2e',
        },
        border: {
          DEFAULT: '#1e1e3a',
          bright: '#2d2d52',
        },
        accent: {
          violet: '#7c3aed',
          'violet-dim': '#5b21b6',
          'violet-glow': '#9f67ff',
          cyan: '#06b6d4',
          'cyan-dim': '#0891b2',
          'cyan-glow': '#22d3ee',
          green: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
        },
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        violet: '0 0 20px rgba(124, 58, 237, 0.3)',
        cyan: '0 0 20px rgba(6, 182, 212, 0.3)',
        'inner-violet': 'inset 0 0 20px rgba(124, 58, 237, 0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-violet': 'glowViolet 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glowViolet: {
          '0%': { boxShadow: '0 0 5px rgba(124,58,237,0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(124,58,237,0.6)' },
        },
      },
    },
  },
  plugins: [],
}
