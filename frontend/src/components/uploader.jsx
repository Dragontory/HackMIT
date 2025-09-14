import React, { useState, useCallback } from "react";

// Import all 8 faces for use
import face1 from "../assets/face1.png";
import face2 from "../assets/face2.png";
import face3 from "../assets/face3.png";
import face4 from "../assets/face4.png";
import face5 from "../assets/face5.png";
import face6 from "../assets/face6.png";
import face7 from "../assets/face7.png";
import face8 from "../assets/face8.png";

const UploadIcon = () => (
  <svg
    className="w-16 h-16 text-slate-500 mb-4"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      d="M7 16a4 4 0 01-4-4V6a4 4 0 014-4h10a4 4 0 014 4v6a4 4 0 01-4 4H7z"
    ></path>
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      d="M10 9v6m3-3H7"
    ></path>
  </svg>
);

const Uploader = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [goDeeper, setGoDeeper] = useState(false);
  const [extractedText, setExtractedText] = useState("");
  const [imageHashes, setImageHashes] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null); // State for voice selection
  const [uploading, setUploading] = useState(false);

  const handleFile = useCallback((file) => {
    if (file && file.type === "application/pdf") {
      setUploadedFile(file);
      setError("");
    } else {
      setUploadedFile(null);
      setError("Invalid file type. Please upload a PDF.");
    }
  }, []);

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const onDragLeave = () => {
    setIsDragOver(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const onFileChange = (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleGenerate = async () => {
    if (uploadedFile && selectedVoice !== null) {
      setIsGenerating(true);
      setError("");
      setUploading(true);
      console.log("Generating video for:", uploadedFile.name);
      console.log("Selected voice ID:", selectedVoice);

      // Create FormData and send to the backend API
      const formData = new FormData();
      formData.append("file", uploadedFile);
      formData.append("voice", selectedVoice); // Send selected voice to backend

      try {
        // Send file to backend API
        const response = await fetch("http://127.0.0.1:8000/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to upload PDF.");
        }

        const data = await response.json();
        setExtractedText(data.extracted_text);
        setImageHashes(data.extracted_images);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsGenerating(false);
        setUploading(false);
      }
    }
  };

  const dropZoneClasses = `bg-slate-800 border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
    isDragOver ? "border-sky-500 bg-slate-700" : "border-slate-600"
  } ${error ? "border-red-500" : ""}`;

  const voiceNames = [
    "Alice", "Bob", "Charlie", "Dana", "Eva", "Frank", "Grace", "Hank"
  ];

  return (
    <div className="w-full max-w-2xl">
      <div
        className={dropZoneClasses}
        onClick={() => document.getElementById("file-input").click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input
          type="file"
          id="file-input"
          className="hidden"
          accept=".pdf"
          onChange={onFileChange}
        />
        {!uploadedFile && !error && (
          <div className="flex flex-col items-center justify-center">
            <UploadIcon />
            <p className="text-xl font-semibold text-slate-200">
              Drag & Drop Your Notes Here
            </p>
            <p className="text-slate-400 mt-2">
              or{" "}
              <span className="text-sky-400 font-medium">click to browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-4">PDF supported</p>
          </div>
        )}
        {uploadedFile && (
          <div>
            <p className="text-xl font-semibold text-slate-200" id="filename">
              {uploadedFile.name}
            </p>
            <p className="text-slate-400 mt-2" id="file-status">
              {isGenerating ? "Uploading and processing..." : "Ready to generate!"}
            </p>
          </div>
        )}
        {error && (
          <div>
            <p className="text-xl font-semibold text-red-400">Invalid file type</p>
            <p className="text-slate-400 mt-2">{error}</p>
          </div>
        )}
      </div>

      {/* Voice Selection Section */}
      <div className="mt-8">
        <h3 className="font-bold text-lg text-white">Choose Your Voice</h3>
        <p className="text-slate-400 text-sm">Pick a voice for the video narration.</p>
        <div className="grid grid-cols-4 gap-6 mt-4">
          {[
            face1,
            face2,
            face3,
            face4,
            face5,
            face6,
            face7,
            face8,
          ].map((face, index) => (
            <div
              key={index}
              className={`cursor-pointer p-4 rounded-lg transition-all duration-300 ${
                selectedVoice === index
                  ? "border-4 border-blue-500"
                  : "border"
              }`}
              onClick={() => {
                // Toggle selection on click (deselect if already selected)
                setSelectedVoice(selectedVoice === index ? null : index);
              }}
            >
              <div className="relative">
                <img
                  src={face}
                  alt={`Voice ${index + 1}`}
                  className="w-full h-full object-contain rounded-xl"
                />
                <div className="text-center mt-2 text-slate-300 font-semibold">
                  {voiceNames[index]}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Go Deeper Toggle */}
      <div className="mt-8 bg-slate-800 border border-slate-700 rounded-xl p-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg text-white">Go Deeper</h3>
          <p className="text-slate-400 text-sm">
            Let the AI research topics to provide more context.
          </p>
        </div>

        <label
          htmlFor="go-deeper-toggle"
          className="relative inline-flex items-center w-14 h-7 cursor-pointer"
        >
          <input
            id="go-deeper-toggle"
            type="checkbox"
            className="sr-only peer"
            checked={goDeeper}
            onChange={() => setGoDeeper(!goDeeper)}
          />
          <span className="absolute inset-0 rounded-full bg-slate-600 transition-colors peer-checked:bg-sky-500" />
          <span className="absolute left-1 top-1 h-5 w-5 rounded-full bg-white transition-transform duration-200 transform-gpu peer-checked:translate-x-7" />
        </label>
      </div>

      {/* Generate Button */}
      <div className="mt-8 text-center">
        <button
          id="generate-button"
          onClick={handleGenerate}
          className="w-full main-button bg-sky-500 hover:bg-sky-600 text-white font-bold py-4 px-10 rounded-full text-lg shadow-lg disabled:bg-slate-600 disabled:shadow-none disabled:cursor-not-allowed"
          disabled={!uploadedFile || isGenerating || selectedVoice === null}
        >
          {isGenerating ? "Generating..." : "Generate Video"}
        </button>
      </div>

      {/* Display Extracted Data */}
      {extractedText && (
        <div className="mt-8">
          <h4 className="text-xl font-bold">Extracted Text:</h4>
          <pre className="mt-4 whitespace-pre-wrap text-left bg-gray-800 p-4 rounded-md">
            {extractedText}
          </pre>
        </div>
      )}

      {imageHashes.length > 0 && (
        <div className="mt-8">
          <h4 className="text-xl font-bold">Extracted Images:</h4>
          <div className="grid grid-cols-2 gap-4 mt-4">
            {imageHashes.map((hash) => (
              <div key={hash} className="bg-gray-800 p-4 rounded-md">
                <p className="text-sm text-gray-400">Image Hash: {hash}</p>
                <img
                  src={`http://127.0.0.1:8000/temp_uploads/${hash}.png`}
                  alt={`Extracted image ${hash}`}
                  className="mt-2 rounded-md"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Uploader;
