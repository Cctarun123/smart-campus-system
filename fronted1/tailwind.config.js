/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#FFF8E1",
          100: "#FFECB3",
          400: "#FFC107",
          500: "#FFB300",
          700: "#F57C00"
        },
        ui: {
          bg: "#F5F6FA",
          ink: "#1f2937"
        }
      },
      borderRadius: {
        xl2: "1.2rem",
        xl3: "1.5rem"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(17, 24, 39, 0.08)",
        card: "0 6px 20px rgba(17, 24, 39, 0.07)"
      },
      fontFamily: {
        sans: ["Poppins", "DM Sans", "ui-sans-serif", "system-ui", "sans-serif"]
      }
    },
  },
  plugins: [],
};
