import type { Config } from "tailwindcss";
export default {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "#27272a",
        background: "#09090b",
        foreground: "#fafafa",
        primary: "#7c3aed",
      },
    },
  },
  plugins: [],
} satisfies Config;
