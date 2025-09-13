import React from 'react';
import Header from './Header';

const LandingPage = ({ onTryNow }) => (
  <>
    <Header />
    <main className="text-center py-20 md:py-32 px-4 md:px-8">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-5xl md:text-7xl font-extrabold tracking-tight">
          Transform Your Notes into
          <span className="gradient-text block mt-2 md:mt-4">Engaging Video Lessons</span>
        </h2>
        <p className="mt-8 max-w-2xl mx-auto text-lg text-slate-300">
          Stop re-reading boring notes. Upload your study materials, and let our AI create dynamic, narrated video
          summaries with visuals and animations in minutes. Learning just got an upgrade.
        </p>
        <div className="mt-12">
          <button
            onClick={onTryNow}
            className="main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg"
          >
            Try ClarifY Now
          </button>
        </div>
      </div>
    </main>

    {/* About */}
    <section id="about" className="py-24 px-4 md:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h3 className="text-4xl font-extrabold tracking-tight">How It Works</h3>
          <p className="mt-4 text-slate-400">A revolutionary approach to studying.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-10">
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h4 className="text-xl font-bold mb-3 gradient-text">1. Upload Anything</h4>
            <p className="text-slate-300">
              Start with your class notes, a textbook chapter, or even a research paper. Our smart parser handles PDFs,
              text files, and more, extracting the key information.
            </p>
          </div>
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h4 className="text-xl font-bold mb-3 gradient-text">2. AI-Powered Generation</h4>
            <p className="text-slate-300">
              Our AI director analyzes your content, writes a script, generates a human-like voiceover, and creates
              custom animations and visuals to explain complex topics.
            </p>
          </div>
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h4 className="text-xl font-bold mb-3 gradient-text">3. Learn Visually</h4>
            <p className="text-slate-300">
              Receive a polished, high-quality video that brings your notes to life. Reinforce learning through a medium
              that’s more engaging than static text.
            </p>
          </div>
        </div>
      </div>
    </section>

    {/* Why ClarifY (stats) */}
    <section id="why" className="py-24 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h3 className="text-4xl font-extrabold tracking-tight">Why ClarifY</h3>
          <p className="mt-4 text-slate-400">Learn faster, retain more, and study with confidence.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
            <div className="text-5xl font-extrabold">3×</div>
            <p className="mt-2 text-slate-400">Faster review vs. re-reading notes</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
            <div className="text-5xl font-extrabold">+70%</div>
            <p className="mt-2 text-slate-400">Better concept retention with visuals</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
            <div className="text-5xl font-extrabold">Minutes</div>
            <p className="mt-2 text-slate-400">From upload to a polished video</p>
          </div>
        </div>

        <div className="mt-12 grid md:grid-cols-2 gap-8">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
            <h4 className="text-xl font-bold mb-3 gradient-text">Clarity through visuals</h4>
            <p className="text-slate-300">
              Complex topics become intuitive with diagrams, motion, and narration that mirror how you actually learn.
            </p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
            <h4 className="text-xl font-bold mb-3 gradient-text">Context when you need it</h4>
            <p className="text-slate-300">
              Toggle “Go Deeper” to enrich lessons with curated background and definitions so you never lose the plot.
            </p>
          </div>
        </div>
      </div>
    </section>

    {/* See it in action (video placeholder) */}
    <section id="demo" className="py-24 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h3 className="text-4xl font-extrabold tracking-tight">See It In Action</h3>
          <p className="mt-4 text-slate-400">A quick look at ClarifY turning notes into a video.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="aspect-video w-full rounded-xl bg-slate-800 border border-slate-700 relative overflow-hidden">
            {/* Placeholder content */}
            <div className="absolute inset-0 flex items-center justify-center">
              <button
                type="button"
                aria-label="Play demo (placeholder)"
                className="flex items-center gap-3 px-6 py-3 rounded-full bg-white/10 hover:bg-white/15 text-white font-semibold backdrop-blur transition"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Demo coming soon
              </button>
            </div>
          </div>
        </div>

        <div className="text-center mt-10">
          <button
            onClick={onTryNow}
            className="main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg"
          >
            Try ClarifY Now
          </button>
        </div>
      </div>
    </section>

    <footer className="text-center py-8 border-t border-slate-800">
      <p className="text-slate-400">&copy; 2025 ClarifY.</p>
    </footer>
  </>
);

export default LandingPage;
