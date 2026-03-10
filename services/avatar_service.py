# ---------------------------
# Avatar service
# ---------------------------

import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_SIZE_MB = 5


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_avatar(file):
    if not file:
        return None

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        raise ValueError("invalid_file_type")

    # taille max
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_SIZE_MB * 1024 * 1024:
        raise ValueError("file_too_large")

    # image processing
    img = Image.open(file).convert("RGB")

    # resize max 512px
    img.thumbnail((512, 512))

    new_name = f"{uuid.uuid4().hex}.jpg"

    upload_path = os.path.join(
        current_app.static_folder,
        "uploads",
        "avatars"
    )

    os.makedirs(upload_path, exist_ok=True)

    path = os.path.join(upload_path, new_name)

    img.save(path, "JPEG", quality=85, optimize=True)

    return f"/static/uploads/avatars/{new_name}"