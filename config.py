import os
import shutil
import json

# Get absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIRECTORY = os.path.join(current_dir, 'photos')
THUMBNAIL_DIRECTORY = os.path.join(current_dir, 'thumbnails')
COMMENTS_DIRECTORY = os.path.join(current_dir, 'comments')
STATIC_DIRECTORY = os.path.join(current_dir, 'static')
TEMPLATES_DIRECTORY = os.path.join(current_dir, 'templates')
AUDIO_DIRECTORY = os.path.join(current_dir, 'audio')
TEMP_DIRECTORY = os.path.join(current_dir, 'temp')
FACES_DETECTIONS_DIRECTORY = os.path.join(current_dir, 'faces_detections')
FACES_EMBEDDING_DIRECTORY = os.path.join(current_dir, 'faces_embeddings')

FACES_EMBEDDINGS = {}
for filename in os.listdir(FACES_EMBEDDING_DIRECTORY):
    embed_file=os.path.join(FACES_EMBEDDING_DIRECTORY,filename)    
    with open(embed_file, 'r') as f:
        data = json.load(f)    
    FACES_EMBEDDINGS[filename]=data



# Create directories if they don't exist
os.makedirs(PHOTO_DIRECTORY, exist_ok=True)
os.makedirs(THUMBNAIL_DIRECTORY, exist_ok=True)
os.makedirs(COMMENTS_DIRECTORY, exist_ok=True)
os.makedirs(AUDIO_DIRECTORY, exist_ok=True)
if os.path.exists(TEMP_DIRECTORY):
    shutil.rmtree(TEMP_DIRECTORY)
os.makedirs(TEMP_DIRECTORY)
os.makedirs(FACES_DETECTIONS_DIRECTORY, exist_ok=True)
os.makedirs(FACES_EMBEDDING_DIRECTORY, exist_ok=True)