import cv2
from ultralytics import YOLO
import threading

model1 = YOLO('path_to_model1')
model2 = YOLO('path_to_model2')
model3 = YOLO('path_to_model3')

rtsp_streams = ['rtsp://stream1', 'rtsp://stream2', 'rtsp://stream3', 'rtsp://stream4']

def run_inference_on_stream(stream, model):
   video = cv2.VideoCapture(stream)

   while True:
       ret, frame = video.read()

       if not ret:
           break

       results = model.track(frame, persist=True)
       res_plotted = results[0].plot()
       cv2.imshow("Inference Stream", res_plotted)

       key = cv2.waitKey(1)
       if key == ord('q'):
           break

   video.release()
 

for i, stream in enumerate(rtsp_streams):
   model = [model1, model2, model3][i % 3] # cycle through the models
   thread = threading.Thread(target=run_inference_on_stream, args=(stream, model))
   thread.start()