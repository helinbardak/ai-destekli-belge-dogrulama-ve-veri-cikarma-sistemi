import os
import easyocr
import fitz 
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

print("OCR Modeli yÃ¼kleniyor, lÃ¼tfen bekleyin...")
reader = easyocr.Reader(['tr', 'en'], gpu=False)

def test_belgesini_oku(file_path):
    print(f"\n===== OCR TESTÄ° BAÅ�?LIYOR: {file_path} =====")
    
    if not os.path.exists(file_path):
        return "HATA: Dosya bulunamadÄ±! Dosya adÄ±nÄ± veya yolunu kontrol edin."

    okunacak_dosya = file_path
    gecici_dosya_ismi = "gecici_test_resmi.jpg"

    try:
        if file_path.lower().endswith('.pdf'):
            print("PDF dosyasÄ± algÄ±landÄ±. Resme Ã§evriliyor...")
            doc = fitz.open(file_path)
            sayfa = doc.load_page(0) 
            pix = sayfa.get_pixmap(dpi=150)
            pix.save(gecici_dosya_ismi)
            doc.close()
            okunacak_dosya = gecici_dosya_ismi

        print("Metinler analiz ediliyor... (CPU kullanÄ±ldÄ±ÄŸÄ± iÃ§in 10-20 saniye sÃ¼rebilir, arkanÄ±za yaslanÄ±n!)")
        
        result = reader.readtext(okunacak_dosya, detail=0)
        raw_text = "\n".join(result)

        if okunacak_dosya == gecici_dosya_ismi and os.path.exists(gecici_dosya_ismi):
            os.remove(gecici_dosya_ismi)

        return raw_text

    except Exception as e:
        return f"Ä°ÅŸlem sÄ±rasÄ±nda bir hata oluÅŸtu: {str(e)}"

test_belgesi = r"C:\PYTHON\KonutHasarOCR\uploads\3kimlik.jpg" 
sonuc = test_belgesini_oku(test_belgesi)

print("\n===== Ã‡IKARILAN HAM METÄ°N (OCR SONUCU) =====")
if sonuc.strip() == "":
    print("Belge okundu ancak iÃ§inde bir metin bulunamadÄ±!")
else:
    print(sonuc)
print("============================================")
