import React from 'react';

const Header = ({ onBack }) => (
    <header className="py-6 flex justify-between items-center px-4 md:px-8">
        <h1 className="text-2xl font-bold gradient-text">EduVid AI</h1>
        <nav>
            {onBack ? (
                <button onClick={onBack} className="text-slate-300 hover:text-white transition">&larr; Back to Home</button>
            ) : (
                <a href="#about" className="text-slate-300 hover:text-white transition">About</a>
            )}
        </nav>
    </header>
);

export default Header;