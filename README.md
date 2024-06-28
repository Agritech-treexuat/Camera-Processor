# Important
- The input images are directly resized to match the input size of the model. I skipped adding the pad to the input image, it might affect the accuracy of the model if the input image has a different aspect ratio compared to the input size of the model. Always try to get an input size with a ratio close to the input images you will use.

# Requirements

 * Check the **requirements.txt** file.
 * For ONNX, if you have a NVIDIA GPU, then install the **onnxruntime-gpu**, otherwise use the **onnxruntime** library.

# Installation
```shell
pip install -r requirements.txt
```
# Run
## Object detect real time using Yolo and connection loss detect from camera
```shell
python run_rtsp_procesor.py
```
## Random capture image from camera
```shell
python run_image_capture_upload.py
```
## Upload video and connection info to Blockchain
```shell
python run_blockchain_upload.py
```
## Make overview video from image
```shell
python run_video_maker.py
```
## Fake capture image from video
```shell
python run_fake_data_image.py
```
## Fake capture image hash and weather
```shell
python run_fake_image_hash_weather.py
```
### ONNX Runtime
For Nvidia GPU computers:
`pip install onnxruntime-gpu`

Otherwise:
`pip install onnxruntime`

# ONNX model
Use the Google Colab notebook to convert the model: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1-yZg6hFg27uCPSycRCRtyezHhq_VAHxQ?usp=sharing)

You can convert the model using the following code after installing ultralitics (`pip install ultralytics`):
```python
from ultralytics import YOLO

model = YOLO("yolov8m.pt") 
model.export(format="onnx", imgsz=[480,640])
```

# Reference
https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection
