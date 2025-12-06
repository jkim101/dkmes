/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#2563eb', // Blue 600
                    hover: '#1d4ed8',   // Blue 700
                },
                secondary: '#64748b', // Slate 500
                background: '#f8fafc', // Slate 50
                sidebar: '#ffffff',
                card: '#ffffff',
                text: {
                    primary: '#020617', // Slate 950
                    secondary: '#475569', // Slate 600
                },
                border: '#cbd5e1', // Slate 300
                divider: '#e2e8f0', // Slate 200
                success: '#10b981', // Emerald 500
                warning: '#f59e0b', // Amber 500
                error: '#ef4444', // Red 500
                accent: '#3b82f6', // Blue 500
            },
            borderRadius: {
                DEFAULT: '12px',
            },
            boxShadow: {
                card: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                hover: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025)',
            }
        },
    },
    plugins: [],
}
