import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import ProductPage from './components/ProductPage.jsx';
import GlobalStyles from './components/GlobalStyles';

function App() {
    const [currentPage, setCurrentPage] = useState('landing'); // 'landing' or 'product'

    const showProductPage = () => setCurrentPage('product');
    const showLandingPage = () => setCurrentPage('landing');

    return (
        <>
            <GlobalStyles />
            <div className="relative z-10 min-h-screen ">
                <div className={`page ${currentPage === 'landing' ? '' : 'page-hidden'}`}>
                    <LandingPage onTryNow={showProductPage} />
                </div>
                <div className={`page ${currentPage === 'product' ? '' : 'page-hidden'}`}>
                    {/* We only render the product page when needed to ensure smooth transitions */}
                    {currentPage === 'product' && <ProductPage onBack={showLandingPage} />}
                </div>
            </div>
        </>
    );
}

export default App;