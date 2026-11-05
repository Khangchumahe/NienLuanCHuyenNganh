/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
        display: ['"Playfair Display"', "ui-serif", "Georgia", "serif"],
      },
      boxShadow: {
        soft: "0px 1px 2px 0px rgba(0,0,0,0.05)",
        float: "0px 16px 40px -12px rgba(17,17,17,0.12)",
      },
      maxWidth: { shell: "1440px" },
      keyframes: {
        "fade-up": { "0%": { opacity: 0, transform: "translateY(8px)" }, "100%": { opacity: 1, transform: "none" } },
        "fade-in": { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        "slide-in": { "0%": { opacity: 0, transform: "translateX(16px)" }, "100%": { opacity: 1, transform: "none" } },
      },
      animation: {
        "fade-up": "fade-up .35s ease-out both",
        "fade-in": "fade-in .2s ease-out both",
        "slide-in": "slide-in .25s ease-out both",
      },
    },
  },
  plugins: [],
};
