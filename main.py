#%%
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from config import PHOTO_DIRECTORY, THUMBNAIL_DIRECTORY, AUDIO_DIRECTORY, STATIC_DIRECTORY, TEMPLATES_DIRECTORY

# Import routers from separated modules
from image_gallery import gallery_router
from image_comment import comment_router

# Configuration
app = FastAPI(title="Photo Gallery")

# Mount static directories
app.mount("/photos", StaticFiles(directory=PHOTO_DIRECTORY), name="photos")
app.mount("/thumbnails", StaticFiles(directory=THUMBNAIL_DIRECTORY), name="thumbnails")
app.mount("/audio", StaticFiles(directory=AUDIO_DIRECTORY), name="audio")
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIRECTORY)

# Include routers
app.include_router(gallery_router)
app.include_router(comment_router)

# Add endpoint to serve the comment window template
@app.get("/comment-window", response_class=HTMLResponse)
async def get_comment_window(request: Request):
    return templates.TemplateResponse("image_comment.html", {"request": request})

if __name__ == "__main__":
    # Clear the terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
# %%
