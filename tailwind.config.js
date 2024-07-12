/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./templates/**/*.{html,js}"],
    plugins: [
        // include Flowbite as a plugin in your Tailwind CSS project
        require("@tailwindcss/typography"),
        require("daisyui"),
    ],
    daisyui: {
        themes: [
            {
                light: {
                    primary: "#0069D9",

                    secondary: "#4d77b7",

                    accent: "#4ca80b",

                    neutral: "#312442",

                    "base-100": "#F4F6F9",

                    info: "#17A2B8",

                    success: "#218838",

                    warning: "#E0A800",

                    error: "#DC3545",
                },

                dark: {
                    primary: "#0069D9",

                    secondary: "#257c7c",

                    accent: "#a59a24",

                    neutral: "#23392f",

                    "base-100": "#36383f",

                    info: "#17A2B8",

                    success: "#218838",

                    warning: "#E0A800",

                    error: "#DC3545",
                },
            },
            "cupcake",
            "bumblebee",
            "emerald",
            "corporate",
            "synthwave",
            "retro",
            "cyberpunk",
            "valentine",
            "halloween",
            "garden",
            "forest",
            "aqua",
            "lofi",
            "pastel",
            "fantasy",
            "wireframe",
            "black",
            "luxury",
            "dracula",
            "cmyk",
            "autumn",
            "business",
            "acid",
            "lemonade",
            "night",
            "coffee",
            "winter",
            "dim",
            "nord",
            "sunset",
            // "light",
            // "dark",
        ], // true: all themes | false: only light + dark | array: specific themes like this ["light", "dark", "cupcake"]
        // darkTheme: "dark", // name of one of the included themes for dark mode
        base: true, // applies background color and foreground color for root element by default
        styled: true, // include daisyUI colors and design decisions for all components
        utils: true, // adds responsive and modifier utility classes
        rtl: false, // rotate style direction from left-to-right to right-to-left. You also need to add dir="rtl" to your html tag and install `tailwindcss-flip` plugin for Tailwind CSS.
        prefix: "", // prefix for daisyUI classnames (components, modifiers and responsive class names. Not colors)
        logs: true, // Shows info about daisyUI version and used config in the console when building your CSS
        themeRoot: ":root",
    },
};
