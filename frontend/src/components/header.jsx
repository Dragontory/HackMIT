import React from 'react';

/** @param {{ onBack?: () => void, isLoggedIn?: boolean, onLogout?: () => void }} props */
const Header = ({ onBack, isLoggedIn, onLogout }) => {
  const goHome = (e) => {
    e.preventDefault();
    if (onBack) {
      onBack();
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/70 backdrop-blur">
      <div className="font-roboto mx-auto max-w-6xl px-4 md:px-6 lg:px-8 py-4 flex items-center justify-between">
        <a
          href="#home"
          onClick={goHome}
          className="text-2xl font-extrabold gradient-text leading-none focus:outline-none focus:ring focus:ring-sky-500/40 rounded"
          aria-label="Go to home"
        >
          ClarifY
        </a>

        <nav>
          {onBack ? (
            <button
              onClick={onBack}
              className="text-slate-300 hover:text-white transition focus:outline-none focus:ring focus:ring-sky-500/30 rounded px-3 py-1"
            >
              &larr; Back to Home
            </button>
          ) : (
            <ul className="flex items-center gap-6 text-slate-300">
              <li><a href="#home" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">Home</a></li>
              <li><a href="#about" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">About</a></li>
              <li><a href="#why" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">Why ClarifY</a></li>
              <li><a href="#demo" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">Demo</a></li>
              {isLoggedIn && (
                <li><a href="#my-videos" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">My Videos</a></li>
              )}
              {!isLoggedIn ? (
                <li><a href="#login" className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30">Login</a></li>
              ) : (
                <li>
                  <button
                    onClick={onLogout}
                    className="hover:text-white transition px-1 py-1 rounded focus:outline-none focus:ring focus:ring-sky-500/30"
                  >
                    Logout
                  </button>
                </li>
              )}
            </ul>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;
