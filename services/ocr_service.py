import os
import easyocr
import fitz 
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

reader = None

def get_ocr_reader():
    """
    OCR motorunu sadece gerçekten ihtiyaç duyulduğunda (butona basılınca) yükler.
    """
    global reader
    if reader is None:
        print("\n[BİLGİ] EasyOCR Motoru ilk defa çalıştırılıyor, belleğe yükleniyor (Bu işlem 10-15 sn sürebilir)...")
        reader = easyocr.Reader(['tr', 'en'], gpu=False)
    return reader

def extract_text(file_path):
    """
    Frontend'den API aracılığıyla gelen dosya yolunu okur ve ham metni döndürür.
    """
    ocr_motoru = get_ocr_reader()
        
    if not os.path.exists(file_path):
        return f"HATA: Dosya bulunamadı ({file_path})"

    okunacak_dosya = file_path
    base_name = os.path.basename(file_path)
    gecici_dosya_ismi = f"temp_ocr_{base_name}.jpg"

    try:
        if file_path.lower().endswith('.pdf'):
            doc = fitz.open(file_path)
            sayfa = doc.load_page(0) 
            pix = sayfa.get_pixmap(dpi=150)
            pix.save(gecici_dosya_ismi)
            doc.close()
            okunacak_dosya = gecici_dosya_ismi

        result = ocr_motoru.readtext(okunacak_dosya, detail=0)
        raw_text = "\n".join(result)

        if okunacak_dosya == gecici_dosya_ismi and os.path.exists(gecici_dosya_ismi):
            os.remove(gecici_dosya_ismi)

        return raw_text

    except Exception as e:
        print(f"OCR Servis Hatası: {str(e)}")
        return ""
