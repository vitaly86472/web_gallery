import os
import glob
import json
import subprocess
import shutil
from tqdm import tqdm
from scipy.spatial.distance import cosine

from fastapi import APIRouter, HTTPException, Form, UploadFile, File,Request
from fastapi.responses import JSONResponse
from datetime import datetime
from audio_processor import VoskProcessor
from config import COMMENTS_DIRECTORY,PHOTO_DIRECTORY, AUDIO_DIRECTORY, TEMP_DIRECTORY, FACES_DETECTIONS_DIRECTORY,FACES_EMBEDDING_DIRECTORY, FACES_EMBEDDINGS

# Initialize Vosk processor
processor = VoskProcessor(model_path=r'C:\my\codes\gallery_web\vosk-model-small-ru-0.22\vosk-model-small-ru-0.22')

def get_faces_detections(json_file):
    """Get face detections from JSON file"""
    with open(json_file, "r") as f:
        data = json.load(f)
    
    return [face['box'] for face in data['faces']]

def convert_webm_to_wav(webm_path, wav_path):
    """Convert WebM audio to WAV using ffmpeg"""
    try:
        command = [
            'ffmpeg',
            '-i', webm_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            wav_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            return False, result.stderr
        return True, wav_path
    except Exception as e:
        print(f"Conversion error: {e}")
        return False, str(e)

def get_comments_for_photo(filename: str):
    """Get comments for a specific photo"""
    comment_files = glob.glob(os.path.join(COMMENTS_DIRECTORY, f'{filename}.*.json'))
    comments = []

    for comment_file in comment_files:
        try:
            with open(comment_file, 'r') as f:
                comment = json.load(f)
            comments.append(comment)
        except Exception as e:
            print(f"❌ Error reading comment {comment_file}: {e}")
    
    return comments

def get_next_comment_index(filename: str) -> int:
    """Get the next comment index for a photo"""
    comment_files = glob.glob(os.path.join(COMMENTS_DIRECTORY, f'{filename}.*.json'))
    if not comment_files:
        return 1
    
    indices = []
    for comment_file in comment_files:
        try:
            # Extract index from filename (format: filename.XXX.json)
            index = int(comment_file.split('.')[-2])
            indices.append(index)
        except (ValueError, IndexError):
            print(f"⚠️ Invalid comment filename format: {comment_file}")
            continue

    return (max(indices) + 1) if indices else 1

def save_comment(filename: str, comment_data: dict):
    """Save a comment for a photo"""
    index = str(get_next_comment_index(filename)).zfill(3)
    comment_file = os.path.join(COMMENTS_DIRECTORY, f"{filename}.{index}.json")
    
    comment_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(comment_file, 'w') as f:
            json.dump(comment_data, f, indent=2)
        return comment_data
    except Exception as e:
        print(f"❌ Error saving comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to save comment")

# Create router for comment endpoints
comment_router = APIRouter()

@comment_router.get("/api/comments/{filename}")
async def get_comments_api(filename: str):
    """Get comments for a specific photo"""
    try:
        comments = get_comments_for_photo(filename)
        return JSONResponse({"comments": comments})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@comment_router.post("/api/comments/{filename}")
async def add_comment_api(filename: str, comment: str = Form(...)):
    """Add a text comment to a photo"""
    if not comment.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    try:
        comment_data = {"text": comment.strip()}
        saved_comment = save_comment(filename, comment_data)
        return JSONResponse({"success": True, "comment": saved_comment})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@comment_router.post("/api/audio/{filename}")
async def upload_audio_api(filename: str, audio_file: UploadFile = File(...)):
    """Upload audio comment for a photo"""
    try:
        # Save audio file
        index = str(get_next_comment_index(filename)).zfill(3)
        audio_filename = f"{filename}.{index}.wav"
        audio_path = os.path.join(AUDIO_DIRECTORY, audio_filename)
        
        with open(audio_path, "wb") as f:
            f.write(await audio_file.read())
        
        # Transcribe audio
        comment_text = audio_filename
        temp_wav = os.path.join(TEMP_DIRECTORY, audio_filename)
        conversion_success, _ = convert_webm_to_wav(audio_path, temp_wav)
        
        if conversion_success:
            recognition_success, text = processor.process_audio(temp_wav)
            if recognition_success:
                comment_text = text
        
        # Save comment
        comment_data = {
            "audio_url": f"/audio/{audio_filename}",
            "text": comment_text,
            "audio_recognizer": "vosk"
        }
        
        saved_comment = save_comment(filename, comment_data)
        
        return JSONResponse({
            "success": True,
            "comment": saved_comment
        })
    except Exception as e:
        print(f"❌ Error saving audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@comment_router.get("/api/faces/{filename}")
async def get_faces_api(filename: str):
    """Get face detections for a specific photo"""
    try:
        face_json_path = os.path.join(FACES_DETECTIONS_DIRECTORY, f"{filename}.json")
        
        if not os.path.exists(face_json_path):
            return JSONResponse({"faces": []})
        
        face_boxes = get_faces_detections(face_json_path)
        
        return JSONResponse({
            "faces": face_boxes,
            "count": len(face_boxes)
        })
    except Exception as e:
        print(f"❌ Error reading face detections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


def get_similar_images(query_embedding):
    #query_embedding=embeddings[face_index]
    indices_with_distances=[]

    for i,embed in enumerate(FACES_EMBEDDINGS):    
        distance = cosine(query_embedding, embed)    
        indices_with_distances.append((i,distance))
        
    indices_with_distances.sort(key=lambda x:x[1])    

def get_processed_face_embedding(filename,face_index):
    filename_no_ext,file_ext=os.path.splitext(filename)
    embed_filename=f"{filename_no_ext}_{face_index}{file_ext}"+'.json'
    return FACES_EMBEDDINGS[embed_filename]


def get_face_imageinfo(json_name):
    #00007_1.jpg.json
    image_name=json_name[:-5]
    image_name_no_ext,img_ext=os.path.splitext(image_name)
    full_imagename_noext,index=image_name_no_ext.split("_")
    full_imagename=full_imagename_noext+img_ext
    img_path=os.path.join(PHOTO_DIRECTORY,full_imagename)
    det_path=os.path.join(FACES_DETECTIONS_DIRECTORY,full_imagename+'.json')
    return img_path,det_path,index

def search_similar_faces(filename,face_index):
    query_embedding=get_processed_face_embedding(filename=filename,face_index=face_index)    
    items=[]
    
    for i,(embed_filename,embed) in enumerate(FACES_EMBEDDINGS.items()):    
        distance = cosine(query_embedding, embed)    
        items.append((i,embed_filename,distance))        
        
    items.sort(key=lambda x:x[-1]) 
    info=[get_face_imageinfo(x[1]) for x in items]   

    
    return info

@comment_router.post("/api/search-face")
async def search_face(request: Request):
    """Endpoint to handle face search requests"""
    try:
        data = await request.json()
        filename = data.get('filename')
        face_coordinates = data.get('face_coordinates')
        face_index = data.get('face_index')
        
        # Print the data for now (you can replace this with actual face search logic)
        print(f"🔍 Search face request received:")
        print(f"   File: {filename}")
        print(f"   Face index: {face_index}")
        print(f"   Coordinates: {face_coordinates}")
        #File: 00004.jpg
        #Face index: 1
        #Coordinates: [0.64402, 0.25918, 0.67756, 0.32505]

        # Here you can call your search_selected_face function
        # search_selected_face(filename, face_coordinates, face_index)
        indices_with_distances=search_similar_faces(filename,face_index)
        
        
        return JSONResponse({
            "success": True,
            "message": "Face search initiated",
            "data": {
                "filename": filename,
                "face_index": face_index,
                "coordinates": face_coordinates
            }
        })
    except Exception as e:
        print(f"❌ Error in face search: {e}")
        raise HTTPException(status_code=500, detail=str(e))