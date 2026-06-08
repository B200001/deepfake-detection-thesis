
---

### 3. Deepfake Detection (Master’s Thesis)

```markdown
# 🕵️ Deepfake Detection — Master’s Thesis

**ResNeXt-50 + LSTM** hybrid model for detecting temporally manipulated deepfake videos. Achieved **88.4% test accuracy** on FaceForensics++ and DFDC datasets, outperforming pure CNN baselines on temporally manipulated clips.

Fully containerized and deployed with a real-time video analysis UI.

## 🎯 Problem
Existing deepfake detection models struggle with temporal inconsistencies in manipulated videos. Most approaches rely only on spatial (frame-level) features.

## ✅ Solution
A hybrid architecture combining:
- **ResNeXt-50** for spatial feature extraction
- **LSTM** for modeling temporal dependencies across frames
- End-to-end training and evaluation on large-scale deepfake datasets

## ✨ Key Features

- Hybrid CNN + RNN architecture for spatio-temporal analysis
- Strong performance on temporally manipulated content
- Real-time inference via Flask API
- Modern React + TypeScript frontend for video upload and analysis
- Deployed on AWS EC2 with containerized setup

## 🛠️ Tech Stack

| Layer              | Technology                          |
|--------------------|-------------------------------------|
| **Model**          | ResNeXt-50 + LSTM (PyTorch)         |
| **Datasets**       | FaceForensics++, DFDC               |
| **Backend**        | Flask, Python                       |
| **Frontend**       | React, TypeScript                   |
| **Deployment**     | Docker, AWS EC2                     |
| **Computer Vision**| OpenCV                              |

## 📊 Results

- **88.4% test accuracy** on combined FaceForensics++ and DFDC datasets
- Outperformed pure CNN baselines on videos with temporal manipulation
- Successfully deployed as a real-time video analysis service


## 🚀 Getting Started

```bash
git clone https://github.com/B200001/deepfake-detection.git
cd deepfake-detection

# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install && npm start
