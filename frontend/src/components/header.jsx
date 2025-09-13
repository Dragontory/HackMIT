import React from 'react';

/** @param {{ onBack?: () => void }} props */
const Header = ({ onBack }) => (
  <header className="py-6 flex justify-between items-center">
    <h1 className="text-2xl font-bold gradient-text">ClarifY</h1>
    <nav>
      {onBack ? (
        <button onClick={onBack} className="text-slate-300 hover:text-white transition">
          &larr; Back to Home
        </button>
      ) : (
        <ul className="flex gap-6 text-slate-300">
          <li><a href="#about" className="hover:text-white transition">About</a></li>
          <li><a href="#why" className="hover:text-white transition">Why ClarifY</a></li>
          <li><a href="#demo" className="hover:text-white transition">Demo</a></li>
        </ul>
      )}
    </nav>
  </header>
);

export default Header;
