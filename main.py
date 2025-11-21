# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uuid
import os
import shutil

app = FastAPI()

# Allow frontend (Vite dev server) to call this API
origins = [
    "https://senderplus.netlify.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory "database" for MVP
packages = {}

# Status lifecycle
STATUSES = [
    "Waiting for package to reach bus station",
    "Package in our van en route to campus",
    "Package at our campus hub",
    "Package delivered to recipient",
]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve uploaded files (optional, useful later for showing images)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.post("/submit-package")
async def submit_package(
    sender_name: str = Form(...),
    sender_phone: str = Form(...),
    sender_email: Optional[str] = Form(None),
    sender_address: str = Form(...),

    recipient_name: str = Form(...),
    recipient_phone: str = Form(...),
    recipient_email: Optional[str] = Form(None),
    recipient_address: str = Form(...),

    package_name: str = Form(...),
    package_type: str = Form(...),
    weight: float = Form(...),
    value: Optional[float] = Form(None),
    description: Optional[str] = Form(None),

    photo: Optional[UploadFile] = File(None),
):
    tracking_id = str(uuid.uuid4())[:8]

    photo_url = None
    if photo is not None:
        # Save the uploaded photo
        filename = f"{tracking_id}_{photo.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        # URL that frontend can use (http://localhost:8000/uploads/filename)
        photo_url = f"/uploads/{filename}"

    packages[tracking_id] = {
        "tracking_id": tracking_id,
        "sender_name": sender_name,
        "sender_phone": sender_phone,
        "sender_email": sender_email,
        "sender_address": sender_address,
        "recipient_name": recipient_name,
        "recipient_phone": recipient_phone,
        "recipient_email": recipient_email,
        "recipient_address": recipient_address,
        "package_name": package_name,
        "package_type": package_type,
        "weight": weight,
        "value": value,
        "description": description,
        "photo_url": photo_url,
        "status": STATUSES[0],  # "Waiting for package to reach bus station"
    }

    return {
        "message": "Package submitted successfully",
        "tracking_id": tracking_id,
    }


@app.get("/track/{tracking_id}")
def track_package(tracking_id: str):
    pkg = packages.get(tracking_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return pkg

@app.post("/advance-status/{tracking_id}")
def advance_status(tracking_id: str):
    pkg = packages.get(tracking_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    current_status = pkg.get("status")
    try:
        idx = STATUSES.index(current_status)
    except ValueError:
        # If somehow status isn't in STATUSES, reset to first
        idx = -1

    if idx < len(STATUSES) - 1:
        pkg["status"] = STATUSES[idx + 1]
    # If it's already at the last status, keep it there

    return pkg
