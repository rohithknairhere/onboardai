/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "var(--color-base)",
        "surface-main": "var(--color-surface-main)",
        "surface-nested": "var(--color-surface-nested)",
        primary: "var(--color-primary)",
        "accent-gold": "var(--color-accent-gold)",
        "accent-light": "var(--color-accent-light)",
        "text-secondary": "var(--color-text-secondary)",
        "text-main": "var(--color-text-main)",
        "status-progress": "var(--color-status-progress)",
        "status-success": "var(--color-status-success)",
        "status-error": "var(--color-status-error)",
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'serif'],
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
      },
      borderColor: {
        'subtle': 'var(--color-border)',
        'accent-hover': 'rgba(212, 175, 55, 0.5)',
      }
    },
  },
  plugins: [],
}
