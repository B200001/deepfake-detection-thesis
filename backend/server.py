from flask import Flask, render_template, redirect, request, url_for, send_file
from flask import jsonify, json
from werkzeug.utils import secure_filename
from flask_cors import CORS  # Import CORS

# Interaction with the OS
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Used for DL applications, computer vision related processes
import torch
import torchvision

# For image preprocessing
from torchvision import transforms

# Combines dataset & sampler to provide iterable over the dataset
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset

import numpy as np
import cv2

# To recognise face from extracted frames
import face_recognition

# Autograd: PyTorch package for differentiation of all operations on Tensors
# Variable are wrappers around Tensors that allow easy automatic differentiation
from torch.autograd import Variable

import time

import sys

# 'nn' Help us in creating & training of neural network
from torch import nn

# Contains definition for models for addressing different tasks i.e. image classification, object detection e.t.c.
from torchvision import models

from skimage import img_as_ubyte
import warnings
warnings.filterwarnings("ignore")

UPLOAD_FOLDER = 'Uploaded_Files'
video_path = ""

detectOutput = []

app = Flask("__main__", template_folder="templates")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)



class Model(nn.Module):
  def __init__(self, num_classes, latent_dim= 2048, lstm_layers=1, hidden_dim=2048, bidirectional=False):
    super(Model, self).__init__()


    model = models.resnext50_32x4d(pretrained= True)

   
    self.model = nn.Sequential(*list(model.children())[:-2])

    
    self.lstm = nn.LSTM(latent_dim, hidden_dim, lstm_layers, bidirectional)

    
    self.relu = nn.LeakyReLU()

    self.dp = nn.Dropout(0.4)


    self.linear1 = nn.Linear(2048, num_classes)


    self.avgpool = nn.AdaptiveAvgPool2d(1)



  def forward(self, x):
    batch_size, seq_length, c, h, w = x.shape

 
    x = x.view(batch_size*seq_length, c, h, w)

    fmap = self.model(x)
    x = self.avgpool(fmap)
    x = x.view(batch_size, seq_length, 2048)
    x_lstm,_ = self.lstm(x, None)
    return fmap, self.dp(self.linear1(x_lstm[:,-1,:]))




im_size = 112


mean = [0.485, 0.456, 0.406]


std = [0.229, 0.224, 0.225]


sm = nn.Softmax()


inv_normalize = transforms.Normalize(mean=-1*np.divide(mean, std), std=np.divide([1,1,1], std))

# For image manipulation
def im_convert(tensor):
  image = tensor.to("cpu").clone().detach()
  image = image.squeeze()
  image = inv_normalize(image)
  image = image.numpy()
  image = image.transpose(1,2,0)
  image = image.clip(0,1)
  cv2.imwrite('./2.png', image*255)
  return image


def predict(model, img, path='./'):
   
  # fmap, logits = model(img.to('cuda'))
  fmap, logits = model(img.to())
  params = list(model.parameters())
  weight_softmax = model.linear1.weight.detach().cpu().numpy()
  logits = sm(logits)
  _, prediction = torch.max(logits, 1)
  confidence = logits[:, int(prediction.item())].item()*100
  print('confidence of prediction: ', logits[:, int(prediction.item())].item()*100)
  return [int(prediction.item()), confidence]



class validation_dataset(Dataset):
  def __init__(self, video_names, sequence_length = 60, transform=None):
    self.video_names = video_names
    self.transform = transform
    self.count = sequence_length


  def __len__(self):
    return len(self.video_names)

  def __getitem__(self, idx):
    video_path = self.video_names[idx]
    frames = []
    a = int(100 / self.count)
    first_frame = np.random.randint(0,a)
    for i, frame in enumerate(self.frame_extract(video_path)):
      faces = face_recognition.face_locations(frame)
      try:
        top,right,bottom,left = faces[0]
        frame = frame[top:bottom, left:right, :]
      except:
        pass
      frames.append(self.transform(frame))
      if(len(frames) == self.count):
        break
    frames = torch.stack(frames)
    frames = frames[:self.count]
    return frames.unsqueeze(0)


  def frame_extract(self, path):
    vidObj = cv2.VideoCapture(path)
    success = 1
    while success:
      success, image = vidObj.read()
      if success:
        yield image





def detectFakeVideo(videoPath):
    im_size = 112
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    train_transforms = transforms.Compose([
                                        transforms.ToPILImage(),
                                        transforms.Resize((im_size,im_size)),
                                        transforms.ToTensor(),
                                        transforms.Normalize(mean,std)])
    path_to_videos= [videoPath]

    video_dataset = validation_dataset(path_to_videos,sequence_length = 20,transform = train_transforms)
    
    # model = Model(2).cuda()
    model = Model(2)
    path_to_model = 'model/checkpoint.pt'
    model.load_state_dict(torch.load(path_to_model, map_location=torch.device('cpu')))
    model.eval()
    for i in range(0,len(path_to_videos)):
        print(path_to_videos[i])
        prediction = predict(model,video_dataset[i],'./')
        output_label = ""
        if prediction[0] == 1:
            print("REAL")
            output_label = "Deepfake Detected"
        else:
            print("FAKE")
            output_label = "Real Video"

    processed_video_path = process_video_with_labels(videoPath, output_label)
    return prediction, processed_video_path

def process_video_with_labels(videoPath, label):
    cap = cv2.VideoCapture(videoPath)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_to_capture = np.linspace(0, frame_count - 1, 5, dtype=int)  # Capture 5 frames evenly
    
    output_path = os.path.join("Uploaded_Files", "processed_" + os.path.basename(videoPath))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' instead of 'mpv4'
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_index = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index in frames_to_capture:  # Process only selected frames
            face_locations = face_recognition.face_locations(frame)
            
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        out.write(frame)  # Write all frames, even those without boxes
        frame_index += 1  

    cap.release()
    out.release()

    return output_path  # Return processed video path


def extract_frames(video_path, label, output_folder="static/frames"):
    """Extract frames from a processed video and save them as images."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    processed_video_path = process_video_with_labels(video_path, label)  # Process video first

    cap = cv2.VideoCapture(processed_video_path)
    frame_count = 0
    frame_list = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame_count >= 5:  # Stop after extracting 5 frames
            break

        frame_filename = os.path.join(output_folder, f"frame_{frame_count}.jpg")
        cv2.imwrite(frame_filename, frame)
        frame_list.append(frame_filename)
        frame_count += 1

    cap.release()
    return frame_list 


def process_video(video_path, label, output_folder="static/frames", processed_video_path="Uploaded_Files/processed_video.mp4"):
    """Extracts frames with faces, draws bounding boxes, and reconstructs the processed video."""
    
    # Ensure output directory exists and clear any old frames
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Open video file
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Define codec and create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))
    
    # Colors for different labels
    box_color, text_color = ((0, 255, 0), (0, 255, 0)) if label.lower() == "real" else ((0, 0, 255), (0, 0, 255))  # Green for "real", Red otherwise
    
    frames_to_capture = np.linspace(0, frame_count - 1, 5, dtype=int)  # Capture 5 frames evenly
    frame_list = [""] * 5  # Predefine list with 5 slots
    frame_index = 0
    frame_counter = 0  # Track index for saving frames

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process only selected frames
        if frame_index in frames_to_capture:
            face_locations = face_recognition.face_locations(frame)
            
            if face_locations:  # If faces are detected
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                    cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
                
                # Save processed frame, replacing the previous one
                frame_filename = os.path.join(output_folder, f"frame_{frame_counter}.jpg")
                cv2.imwrite(frame_filename, frame)
                frame_list[frame_counter] = frame_filename  # Replace frame in list
                frame_counter += 1
        
        # Write frame (processed or unprocessed) into output video
        out.write(frame)
        frame_index += 1

    cap.release()
    out.release()
    
    return frame_list
@app.route('/', methods=['POST', 'GET'])
def homepage():
  if request.method == 'GET':
	  return render_template('index.html')
  return render_template('index.html')


@app.route('/Detect', methods=['POST', 'GET'])
def DetectPage():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        video = request.files['video']
        print(video.filename)
        video_filename = secure_filename(video.filename)
        video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
        video_path = "Uploaded_Files/" + video_filename
        prediction, processed_video = detectFakeVideo(video_path)
        print(prediction)
        if prediction[0] == 0:
              output = "FAKE"
        else:
              output = "REAL"
        confidence = prediction[1]
        frame_list = process_video(video_path, output)
        data = {'output': output, 'confidence': confidence, 'video_url': url_for('download_video', filename = os.path.basename(processed_video)), "frames": frame_list}
        data = json.dumps(data)
        os.remove(video_path)
        # return render_template('index.html', data=data)
        return jsonify(data) 


@app.route('/download/<filename>')
def download_video(filename):
  return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), mimetype = 'video/mp4')

app.run(port=5000)