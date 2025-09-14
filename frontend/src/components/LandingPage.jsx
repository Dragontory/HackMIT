import React, { Suspense, lazy, useState } from 'react';
import Header from './Header';
import TiltCard from './TiltCard';
import LearningImpactChart from './LearningImpactChart';
import Background from './Background';
import demo1 from '../assets/demo1.gif';
import demo2 from '../assets/demo2.gif';

// Lazy load Notebook3D component
const Notebook3D = lazy(() => import('./Notebook3D'));

const LandingPage = ({ onTryNow }) => {
  const [currentGifIndex, setCurrentGifIndex] = useState(0);
  const gifs = [demo1, demo2];

  // Function to go to the next GIF
  const goToNext = () => {
    setCurrentGifIndex((prevIndex) => (prevIndex + 1) % gifs.length); // Loop to the first gif after the last one
  };

  // Function to go to the previous GIF
  const goToPrevious = () => {
    setCurrentGifIndex(
      (prevIndex) => (prevIndex - 1 + gifs.length) % gifs.length
    ); // Loop to the last gif if we are at the first one
  };

  const handleTryNow = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    onTryNow();
  };

  return (
    <>
      <Header />

      {/* Hero */}
      <main id="home" className="relative text-center py-20 md:py-32 px-4 md:px-8 ">
        <Background />
        <div className="max-w-4xl mx-auto animate-fade-up relative">
          <h2 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.15]">
            Transform Your Notes into
            <span className="gradient-text mt-2 md:mt-4 inline-block pb-1">
              Engaging Video Lessons
            </span>
          </h2>
          <p className="mt-8 max-w-2xl mx-auto text-lg text-slate-300">
            Stop re-reading boring notes. Upload your study materials, and let ClarifY create dynamic,
            narrated video summaries with visuals and animations in minutes.
          </p>
          <div className="mt-12">
            <button
              onClick={handleTryNow}
              className="main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg"
            >
              Try ClarifY Now
            </button>
          </div>
        </div>
      </main>

      {/* About */}
      <section id="about" className="py-24 px-4 md:px-8 scroll-mt-header">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-4xl font-extrabold tracking-tight">How It Works</h3>
            <p className="mt-4 text-slate-400">A revolutionary approach to studying.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            <TiltCard className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
              <h4 className="text-xl font-bold mb-3 gradient-text">1. Upload Anything</h4>
              <p className="text-slate-300">
                Start with your class notes, a textbook chapter, or even a research paper. Our smart parser
                handles PDFs and more, extracting the key information.
              </p>
            </TiltCard>

            <TiltCard className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
              <h4 className="text-xl font-bold mb-3 gradient-text">2. AI-Powered Generation</h4>
              <p className="text-slate-300">
                ClarifY analyzes your content, drafts a script, generates a human-like voiceover, and creates
                supporting visuals to explain complex topics.
              </p>
            </TiltCard>

            <TiltCard className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
              <h4 className="text-xl font-bold mb-3 gradient-text">3. Learn Visually</h4>
              <p className="text-slate-300">
                Receive a polished, high-quality video that brings your notes to life—more engaging than static text.
              </p>
            </TiltCard>
          </div>
        </div>
      </section>

      {/* Why ClarifY (structured, visual, contextual) */}
      <section id="why" className="py-24 px-4 md:px-8 scroll-mt-header">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h3 className="text-4xl font-extrabold tracking-tight">Why ClarifY</h3>
            <p className="mt-4 text-slate-400">Turn dense notes into visual, memorable understanding.</p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
              <h4 className="text-xl font-bold mb-3 gradient-text">Retention over time</h4>
              <LearningImpactChart />
              <p className="mt-4 text-sm text-slate-400">
                Visual storytelling sustains recall vs. passive re-reading.
              </p>
            </TiltCard>

            <Suspense fallback={<div className="h-80 w-full rounded-2xl bg-slate-800 border border-slate-700 animate-pulse" />}>
              <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-4">
                <h4 className="text-xl font-bold mb-3 gradient-text">Your notes, brought to life</h4>
                <Notebook3D />
                <ul className="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-300">
                  <li>• Pages auto-summarized</li>
                  <li>• Animated explanations</li>
                  <li>• Clear voiceover</li>
                  <li>• Ready to revisit</li>
                </ul>
              </TiltCard>
            </Suspense>
          </div>

          <div className="mt-10 grid md:grid-cols-2 gap-8">
            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
              <h4 className="text-xl font-bold mb-3 gradient-text">Clarity through visuals</h4>
              <p className="text-slate-300">
                Complex topics become intuitive with diagrams, motion, and narration that mirror how you actually learn.
              </p>
            </TiltCard>

            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
              <h4 className="text-xl font-bold mb-3 gradient-text">Context when you need it</h4>
              <p className="text-slate-300">
                Toggle “Go Deeper” to enrich lessons with curated background and definitions so you never lose the plot.
              </p>
            </TiltCard>
          </div>

          <div className="mt-10 grid md:grid-cols-3 gap-8">
            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
              <div className="text-5xl font-extrabold">3×</div>
              <p className="mt-2 text-slate-400">Faster review vs. re-reading notes</p>
            </TiltCard>
            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
              <div className="text-5xl font-extrabold">+70%</div>
              <p className="mt-2 text-slate-400">Better concept retention with visuals</p>
            </TiltCard>
            <TiltCard className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
              <div className="text-5xl font-extrabold">Minutes</div>
              <p className="mt-2 text-slate-400">From upload to a polished video</p>
            </TiltCard>
          </div>

          <div className="text-center mt-12">
            <button
              onClick={handleTryNow}
              className="main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg"
            >
              Try ClarifY Now
            </button>
          </div>
        </div>
      </section>

      {/* Demo Section with Slideshow */}
      <section id="demo" className="py-24 px-4 md:px-8 scroll-mt-header-tight">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h3 className="text-4xl font-extrabold tracking-tight">See it in action</h3>
            <p className="mt-4 text-slate-400">A quick look at ClarifY turning notes into a video.</p>
          </div>

          <div className="relative">
            {/* Display GIF with smoother transitions */}
            <div className="transition-all duration-500 ease-in-out">
              <img
                src={gifs[currentGifIndex]}
                alt="demo gif"
                className="w-full h-auto rounded-xl"
              />
            </div>

            {/* Navigation arrows */}
            <div className="absolute top-1/2 left-0 right-0 flex justify-between px-4">
              <button
                onClick={goToPrevious}
                className="bg-black/50 text-white p-3 rounded-full transform hover:scale-110 transition duration-300"
              >
                &#8592;
              </button>
              <button
                onClick={goToNext}
                className="bg-black/50 text-white p-3 rounded-full transform hover:scale-110 transition duration-300"
              >
                &#8594;
              </button>
            </div>
          </div>

          {/* Dots for navigation */}
          <div className="flex justify-center gap-2 mt-4">
            {gifs.map((_, index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full cursor-pointer transition-all duration-300 ease-in-out ${
                  index === currentGifIndex ? 'bg-blue-500' : 'bg-gray-500'
                }`}
                onClick={() => setCurrentGifIndex(index)}
              ></div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-8 border-t border-slate-800">
        <p className="text-slate-400">&copy; 2025 ClarifY - A HackMIT Project.</p>
      </footer>
    </>
  );
};

export default LandingPage;


