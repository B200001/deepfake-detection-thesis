import React from "react";
import { Link } from "react-router-dom";
import "./homepage.scss";

const HomePage: React.FC = () => {
  return (
    <div className="homepage">
      <nav className="navbar">
        <h2 className="logo">Deepfake Detector</h2>
        <div className="nav-links">
          <Link to="/predict" className="nav-item">Predict</Link>
          <a 
            href="https://github.com/YOUR_GITHUB_REPO" 
            target="_blank" 
            rel="noopener noreferrer"
            className="nav-item"
          >
            GitHub
          </a>
        </div>
      </nav>

      <main className="hero">
        <h1>Welcome to Deepfake Detector</h1>
        <p>Detect deepfake videos with AI-powered technology.</p>
        <Link to="/predict" className="cta-button">Start Detecting</Link>
      </main>
    </div>
  );
};

export default HomePage;
