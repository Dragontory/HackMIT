import React, { useState } from "react";

const DemoSection = () => {
  // State to track the current gif index
  const [currentGifIndex, setCurrentGifIndex] = useState(0);
  const gifs = [
    require("../assets/demo1.gif"),
    require("../assets/demo2.gif"),
  ];

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

  return (
    <section id="demo" className="py-24 px-4 md:px-8 scroll-mt-header-tight">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h3 className="text-4xl font-extrabold tracking-tight">See it in action</h3>
          <p className="mt-4 text-slate-400">A quick look at ClarifY turning notes into a video.</p>
        </div>

        <div className="relative">
          {/* Display GIF */}
          <img
            src={gifs[currentGifIndex]}
            alt="demo gif"
            className="w-full h-auto rounded-xl transition-all duration-500 ease-in-out"
          />
          {/* Navigation arrows */}
          <div className="absolute top-1/2 left-0 right-0 flex justify-between px-4">
            <button
              onClick={goToPrevious}
              className="bg-black/50 text-white p-2 rounded-full"
            >
              &#8592;
            </button>
            <button
              onClick={goToNext}
              className="bg-black/50 text-white p-2 rounded-full"
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
              className={`w-3 h-3 rounded-full bg-gray-500 cursor-pointer ${
                index === currentGifIndex ? "bg-blue-500" : ""
              }`}
              onClick={() => setCurrentGifIndex(index)}
            ></div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default DemoSection;
