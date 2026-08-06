from PIL import Image
import base64
import io

def encode_image_resized(file_stream, max_size=(800, 800), quality=85):
    try:
        img = Image.open(file_stream)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    except Exception as e:
        raise Exception(f"Görsel işleme hatası: {str(e)}")
