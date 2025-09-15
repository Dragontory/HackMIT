import React from 'react';

// This component injects the global, non-Tailwind styles into your app.
const GlobalStyles = () => (
    <style>{`
        body {
            font-family: 'Inter', sans-serif;
            background-color: #0F172A; /* Slate 900 */
            color: #F8FAFC; /* Slate 50 */
            overflow-x: hidden;
        }
        .gradient-text {
            background: linear-gradient(to right, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .main-button {
            transition: all 0.3s ease;
        }
        .main-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(56, 189, 248, 0.2), 0 4px 6px -2px rgba(56, 189, 248, 0.1);
        }
        /* Toggle switch styling */
        .toggle-checkbox:checked {
            right: 0;
            border-color: #38bdf8;
        }
        .toggle-checkbox:checked + .toggle-label {
            background-color: #38bdf8;
        }
        /* Page transition styles */
        .page {
            transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;
            width: 100%;
        }
        .page-hidden {
            opacity: 0;
            transform: scale(0.98);
            pointer-events: none;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
        }
    `}</style>
);

export default GlobalStyles;