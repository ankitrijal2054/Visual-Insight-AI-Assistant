import base64
from PIL import Image
import io

def image_to_base64(file_bytes, max_size=(1024, 1024)) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    image.thumbnail(max_size)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
