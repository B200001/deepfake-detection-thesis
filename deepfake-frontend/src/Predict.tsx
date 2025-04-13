import React, { useState, useEffect } from "react";
import { createFFmpeg } from "@ffmpeg/ffmpeg";
import { fetchFile } from "@ffmpeg/util";

import axios from "axios";
import './styles.scss';
import { Link } from "react-router-dom";

const Predict: React.FC = () => {
    const [video, setVideo] = useState<File | null>(null);
    const [result, setResult] = useState<{ output: string; confidence: number; frames: string[] } | null>(null);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [frames, setFrames] = useState<string[]>([]);
    const [videoPreview, setVideoPreview] = useState<string | null>(null);
    const ffmpeg = createFFmpeg({log: true});

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const file = event.target.files[0];
            const fileType = file.type;
            if(fileType === "video/mp4"){
                setVideo(file);
                setVideoPreview(URL.createObjectURL(file));
            }
            else{
                alert("Unsupported format. Converting to MP4... ")
                await convertToMp4(file);
            }
           
        }
    };
    const convertToMp4 = async (file: File) =>{
        if(!ffmpeg.isLoaded()){
            await ffmpeg.load();
        }
        const inputName = file.name;
        const outputName = "converted.mp4";
        ffmpeg.FS("writeFile", inputName, await fetchFile(file));
        await ffmpeg.run("-i", inputName, outputName);
        const data = ffmpeg.FS("readFile", outputName);

        const videoBlob = new Blob([data.buffer], {type: "video/mp4"});
        const convertedUrl = URL.createObjectURL(videoBlob);

        setVideoPreview(convertedUrl);
    }

    const handleSubmit = async () => {
        if (!video) {
            alert("Please select a video file.");
            return;
        }

        setLoading(true);
        setProgress(0);
        setFrames([]); // Clear frames

        const formData = new FormData();
        formData.append("video", video);

        try {
            const response = await axios.post("http://localhost:5000/Detect", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setProgress(percentCompleted);
                    }
                }
            });

            const parsedData = JSON.parse(response.data);
            setResult(parsedData);
            setFrames(parsedData.frames || []);

        } catch (error: any) {
            console.error("Error detecting deepfake:", error);
            alert(error.response?.data?.message || "An error occurred while processing the video.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="homepage">
            <div className="glass-container">
                <Link to="/" className="back-button">⬅ Back</Link>
                <h1>Deepfake Video Detector</h1>
                <input type="file" accept="video/*" onChange={handleFileChange} />
                <button onClick={handleSubmit}>Upload & Detect</button>
            </div>

            {videoPreview && (
                <div className="videoPlayer">
                    <h3>Original Video</h3>
                    <video controls width= "100%" src={videoPreview}/>
                </div>
            )}

            {loading && (
                <div className="loading-screen">
                    <div className="progress-bar">
                        <div className="progress" style={{ width: `${progress}%` }}></div>
                    </div>
                    <p>Processing: {progress}%</p>
                </div>
            )}

            {!loading && result && (
                <div className="result">
                    <h2>Result: {result.output}</h2>
                    <p>Confidence: {result.confidence.toFixed(2)}%</p>
                </div>
            )}

            <div className="frames-container">
                {frames.map((frame, index) => (
                    <img
                        key={index}
                        src={`http://localhost:5000/${frame}?t=${new Date().getTime()}`}
                        alt={`Frame ${index + 1}`}
                        className="frame-img"
                        loading="lazy"
                    />
                ))}
            </div>
        </div>
    );
};

export default Predict;
