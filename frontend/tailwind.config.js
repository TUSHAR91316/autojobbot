/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--bg-main)",
        surface: "var(--bg-surface)",
        surfaceHover: "var(--bg-surface-hover)",
        card: "var(--bg-card)",
        border: "var(--border-subtle)",
        borderHover: "var(--border-hover)",
        primary: {
          DEFAULT: "var(--accent-primary)",
          hover: "var(--accent-primary-hover)",
          subtle: "var(--accent-primary-subtle)",
        },
        success: {
          DEFAULT: "#10b981",
          subtle: "rgba(16, 185, 129, 0.15)",
        },
        warning: {
          DEFAULT: "#f59e0b",
          subtle: "rgba(245, 158, 11, 0.15)",
        },
        danger: {
          DEFAULT: "#ef4444",
          subtle: "rgba(239, 68, 68, 0.15)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
        }
      },
      borderRadius: {
        fluent: "8px",
        card: "12px",
      },
      boxShadow: {
        fluent: "0 4px 16px rgba(0, 0, 0, 0.2)",
        subtle: "0 1px 3px rgba(0, 0, 0, 0.1)",
      }
    },
  },
  plugins: [],
}
