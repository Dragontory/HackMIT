import React from 'react';
import Header from './Header';
import Uploader from './Uploader';

const ProductPage = ({ onBack }) => (
    <>
        <Header onBack={onBack} />
        <main className="flex flex-col items-center justify-center py-20 px-4">
            <Uploader />
        </main>
    </>
);

export default ProductPage;

