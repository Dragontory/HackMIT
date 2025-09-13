import React from 'react';
import Header from './Header';

const LandingPage = ({ onTryNow }) => (
    <>
        <Header />
        <main className="text-center py-20 md:py-32">
            <div className="max-w-4xl mx-auto">
                <h2 className="text-5xl md:text-7xl font-extrabold tracking-tight">
                    Transform Your Notes into
                    <span className="gradient-text block mt-2 md:mt-4">Engaging Video Lessons</span>
                </h2>
                <p className="mt-8 max-w-2xl mx-auto text-lg text-slate-300">
                    Stop re-reading boring notes. Upload your study materials, and let our AI create dynamic, narrated video summaries with visuals and animations in minutes. Learning just got an upgrade.
                </p>
                <div className="mt-12">
                    <button onClick={onTryNow} className="main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg">
                        Try EduVid AI Now
                    </button>
                </div>
            </div>
        </main>

        <section id="about" className="py-24">
            <div className="max-w-5xl mx-auto">
                <div className="text-center mb-16">
                    <h3 className="text-4xl font-extrabold tracking-tight">How It Works</h3>
                    <p className="mt-4 text-slate-400">A revolutionary approach to studying.</p>
                </div>
                <div className="grid md:grid-cols-3 gap-10">
                    <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
                        <h4 className="text-xl font-bold mb-3 gradient-text">1. Upload Anything</h4>
                        <p className="text-slate-300">Start with your class notes, a textbook chapter, or even a research paper. Our smart parser handles PDFs, text files, and more, extracting the key information.</p>
                    </div>
                    <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
                        <h4 className="text-xl font-bold mb-3 gradient-text">2. AI-Powered Generation</h4>
                        <p className="text-slate-300">Our AI director analyzes your content, writes a script, generates a human-like voiceover, and creates custom animations and visuals to explain complex topics.</p>
                    </div>
                    <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
                        <h4 className="text-xl font-bold mb-3 gradient-text">3. Learn Visually</h4>
                        <p className="text-slate-300">Receive a polished, high-quality video that brings your notes to life. Reinforce your learning through a medium that's more engaging and effective than static text.</p>
                    </div>
                </div>
            </div>
        </section>

        <footer className="text-center py-8 border-t border-slate-800">
            <p className="text-slate-400">&copy; 2025 EduVid AI - A HackMIT Project.</p>
        </footer>
    </>
);

export default LandingPage;