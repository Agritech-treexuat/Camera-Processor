import os
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
from moviepy.editor import ImageSequenceClip
import cloudinary
import cloudinary.uploader


class VideoMakerProcessor:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def download_images(self, image_urls):
        image_files = []
        for i, url in enumerate(image_urls):
            response = requests.get(url)
            image_path = f'image_{i}.jpg'
            with open(image_path, 'wb') as file:
                file.write(response.content)
            image_files.append(image_path)
        return image_files

    def create_video_from_images(self, image_files, output_path):
        clip = ImageSequenceClip(image_files, fps=24)
        clip.write_videofile(output_path, codec='libx264')
        return output_path

    def upload_video_to_cloudinary(self, video_path):
        response = cloudinary.uploader.upload_large(video_path, 
        resource_type="video",
        folder="videos",
        public_id=video_path.split('.')[0],
        chunk_size=6000000,
        overwrite=True,
        )
        print("Uploaded video to Cloudinary...")
        return response['secure_url']

    def clean_up_files(self, files):
        for file in files:
            os.remove(file)

    def process_projects(self):
        projects = self.db_handler.get_projects_in_progress()

        for project in projects:
            project_id = project['_id']
            camera_ids = project['cameraId']
            start_date = project['startDate']
            project_video_urls = []
            print(f"Processing project {project_id} with cameraId: {camera_ids}...")

            for camera_id in camera_ids:
                image_urls = self.db_handler.get_image_urls(camera_id, start_date)

                if image_urls:
                    image_files = self.download_images(image_urls)
                    video_path = self.create_video_from_images(image_files, f'{project_id}.mp4')
                    video_url = self.upload_video_to_cloudinary(video_path)
                    project_video_urls.append(video_url)

                    self.clean_up_files(image_files + [f'{project_id}.mp4'])

            self.db_handler.insert_video_urls(project_id, project_video_urls)

