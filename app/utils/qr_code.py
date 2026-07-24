import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse

def generate_qr(url: str):
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
