import os

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def save_bytes(dir_path: str, filename: str, data: bytes) -> str:
    ensure_dir(dir_path)
    full = os.path.join(dir_path, filename)
    with open(full, "wb") as f:
        f.write(data)
    return full
