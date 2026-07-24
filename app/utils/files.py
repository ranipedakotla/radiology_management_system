# # app/utils/files.py
# from pathlib import Path
# from uuid import uuid4
# from fastapi import UploadFile
#
# STATIC_DIR = Path("static")  # ensure exists on startup
#
# def save_upload_to_static(upload: UploadFile, subdir: str = "aadhaar") -> str:
#     if upload is None:
#         return ""
#     target_dir = STATIC_DIR / subdir
#     target_dir.mkdir(parents=True, exist_ok=True)
#     ext = ""
#     if upload.filename and "." in upload.filename:
#         ext = "." + upload.filename.rsplit(".", 1)[-1].lower()
#     fname = f"{uuid4().hex}{ext}"
#     fpath = target_dir / fname
#     with fpath.open("wb") as f:
#         f.write(upload.file.read())
#     return str(fpath.as_posix())
