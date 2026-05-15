from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from ..config import settings
from ..deps import get_current_user


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/images")
def upload_images(files: list[UploadFile] = File(...), current_user=Depends(get_current_user)):
    del current_user
    results: list[dict[str, str]] = []
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    for file in files:
        suffix = Path(file.filename or "").suffix.lower() or ".jpg"
        filename = f"{uuid4().hex}{suffix}"
        target = settings.upload_dir / filename
        with target.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        results.append({"filename": filename, "url": f"/uploads/{filename}"})
    return JSONResponse({"files": results})

