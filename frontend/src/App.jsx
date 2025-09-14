import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import ProductPage from './components/ProductPage.jsx';
import GlobalStyles from './components/GlobalStyles';
import Header from './components/Header';

function App() {
    const [currentPage, setCurrentPage] = useState('landing');
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [user, setUser] = useState(null);

    const showProductPage = () => setCurrentPage('product');
    const showLandingPage = () => setCurrentPage('landing');

    const handleLogin = (userData) => {
        console.log('Login successful, setting user data', userData);
        setUser(userData);
        setIsLoggedIn(true);
        setCurrentPage('product'); 
    };


    const handleLogout = () => {
        setUser(null);
        setIsLoggedIn(false);
    };

    return (
        <>
            <GlobalStyles />
            <div className="relative z-10 min-h-screen">
                <div className={`page ${currentPage === 'landing' ? '' : 'page-hidden'}`}>
                    <LandingPage onTryNow={showProductPage} onLogin={handleLogin} />
                </div>
                <div className={`page ${currentPage === 'product' ? '' : 'page-hidden'}`}>
                    {currentPage === 'product' && (
                        <ProductPage 
                            onBack={showLandingPage} 
                            isLoggedIn={isLoggedIn} 
                            onLogout={handleLogout}
                        />
                    )}
                </div>
            </div>
        </>
    );
}


export default App;
