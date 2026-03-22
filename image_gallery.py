import os
import glob
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageFile
from datetime import datetime
import hashlib
from config import PHOTO_DIRECTORY, THUMBNAIL_DIRECTORY, AUDIO_DIRECTORY, COMMENTS_DIRECTORY, TEMPLATES_DIRECTORY
# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Configuration
THUMBNAIL_SIZE = (200, 200)
ITEMS_PER_PAGE = 20

# Cache for thumbnails
thumbnail_cache = {}

def get_file_hash(filepath: str) -> str:
    """Get MD5 hash of a file to detect changes"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return str(os.path.getsize(filepath)) + str(os.path.getmtime(filepath))

def generate_thumbnail(image_path: str) -> str:
    """Generate thumbnail if it doesn't exist or is outdated"""
    filename = Path(image_path).name
    thumbnail_filename = f"thumb_{filename}"
    thumbnail_path = os.path.join(THUMBNAIL_DIRECTORY, thumbnail_filename)
    
    # Check cache first
    file_hash = get_file_hash(image_path)
    if image_path in thumbnail_cache and thumbnail_cache[image_path] == file_hash:
        if os.path.exists(thumbnail_path):
            return f"/thumbnails/{thumbnail_filename}"
    
    # Generate thumbnail if needed
    if not os.path.exists(thumbnail_path) or os.path.getmtime(image_path) > os.path.getmtime(thumbnail_path):
        try:
            with Image.open(image_path) as img:
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.thumbnail(THUMBNAIL_SIZE)
                img.save(thumbnail_path, "JPEG", quality=85)
            print(f"✅ Created/Updated thumbnail: {thumbnail_filename}")
        except Exception as e:
            print(f"❌ Error creating thumbnail for {filename}: {e}")
            return f"/photos/{filename}"
    
    thumbnail_cache[image_path] = file_hash
    return f"/thumbnails/{thumbnail_filename}"

def get_photo_files():
    """Get all photo files from the photos directory"""
    extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    return [os.path.join(PHOTO_DIRECTORY, f) for f in os.listdir(PHOTO_DIRECTORY) 
            if f.lower().endswith(extensions)]

def get_comment_counts(filename: str):
    """Get comment and audio counts for a photo"""
    comment_count = len(glob.glob(os.path.join(COMMENTS_DIRECTORY, f"{filename}.*.json")))
    audio_count = len(glob.glob(os.path.join(AUDIO_DIRECTORY, f"{filename}.*.wav")))
    return comment_count, audio_count

def get_photos_batch(offset: int = 0, limit: int = ITEMS_PER_PAGE):
    """Get a batch of photos with metadata"""
    all_photos = get_photo_files()
    batch = all_photos[offset:offset + limit]
    
    photos_data = []
    for photo_path in batch:
        filename = os.path.basename(photo_path)
        stats = os.stat(photo_path)
        comment_count, audio_count = get_comment_counts(filename)
        
        photos_data.append({
            "original": f"/photos/{filename}",
            "thumbnail": generate_thumbnail(photo_path),
            "filename": filename,
            "size": stats.st_size,
            "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
            "comment_count": comment_count,
            "audio_count": audio_count
        })
    
    return {
        "photos": photos_data,
        "total": len(all_photos),
        "has_more": offset + limit < len(all_photos)
    }

# Create router
gallery_router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIRECTORY)

@gallery_router.get("/", response_class=HTMLResponse)
async def gallery_page(request: Request):
    """Main gallery page"""
    photos_data = get_photos_batch(offset=0, limit=ITEMS_PER_PAGE)
    
    return templates.TemplateResponse(
        "image_gallery.html",
        {
            "request": request,
            "photos": photos_data["photos"],
            "has_more": photos_data["has_more"],
            "next_offset": ITEMS_PER_PAGE,
            "total_photos": photos_data["total"]
        }
    )

@gallery_router.get("/api/photos")
async def get_photos_api(offset: int = 0, limit: int = ITEMS_PER_PAGE):
    """API endpoint for loading more photos"""
    return get_photos_batch(offset=offset, limit=limit)