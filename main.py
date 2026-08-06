from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import builtins
import io
import os
import re
import shutil
import sys
import traceback
import fitz
import unicodedata
from services.ai_service import DocumentAnalysisError, analyze_document_with_ai
from utils.image_utils import encode_image_resized
from services.ocr_service import extract_text
from services.extractor_service import (
    extract_identity_info, 
    extract_deed_info, 
    extract_statement_info, 
    extract_bank_info
)
app = FastAPI(title="KonutHasar API")

# Arka plan gunlukleri ve Windows terminali icin UTF-8 kullan.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def _repair_terminal_text(value):
    """Eski Windows kod sayfasi nedeniyle bozulmus Turkce log metnini onarir."""
    def repair_segment(match):
        text = match.group(0)
        for _ in range(2):
            if not any(marker in text for marker in ("Ã", "Â", "Ä", "Å", "ƒ", "â")):
                break
            try:
                repaired = text.encode("cp1252").decode("utf-8")
            except UnicodeError:
                break
            if repaired == text:
                break
            text = repaired
        return text

    return re.sub(r"[\x00-\xff\u0152\u0153\u0160\u0161\u017d\u017e\u0192\u201a\u201e\u2026\u20ac]+", repair_segment, str(value))


def print(*values, **kwargs):
    """Moduldeki tum terminal loglarini UTF-8 ve okunur Turkce ile yazdirir."""
    builtins.print(*(_repair_terminal_text(value) for value in values), **kwargs)


def normalize_person_name(value):
    if not value:
        return None

    value = value.replace("ı", "i").replace("İ", "I")
    value = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in value if not unicodedata.combining(char)).upper()
    return " ".join(sorted(normalized.split()))


def add_missing_field_warnings(warnings, data, document_label, fields):
    """OCR ile okunamayan zorunlu alanlar icin kullaniciya yonelik uyarilar ekler."""
    for key, field_label in fields.items():
        if not data.get(key):
            warnings.append(f"{document_label} belgesinde {field_label} bilgisi okunamadı veya eksik.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"mesaj": "Backend API başarıyla çalışıyor."}
@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    print(f"\n--- YENİ BELGE GELDİ: {file.filename} ---")
    try:
        contents = await file.read()


        if file.filename.lower().endswith('.pdf'):
            print("PDF formatı algılandı, AI analizi için görsele dönüştürülüyor...")
            doc = fitz.open(stream=contents, filetype="pdf")
            sayfa = doc.load_page(0)
            pix = sayfa.get_pixmap(dpi=150)
            contents = pix.tobytes("png")
            doc.close()
        base64_image = encode_image_resized(io.BytesIO(contents))

        print("1. Adım: Base64 çevrimi başarılı. Yapay Zekaya gönderiliyor...")
        ai_sonucu = analyze_document_with_ai(base64_image)

        print(f"2. Adım: Yapay Zekadan Gelen Yanıt: {ai_sonucu}")
        return {"status": "success", "result": ai_sonucu}
    except DocumentAnalysisError as e:
        print("!!! GROQ ANALIZ HATASI !!!")
        print(traceback.format_exc())
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        hata_mesaji = str(e)
        print("!!! HATA OLU�?TU !!!")
        print(traceback.format_exc())
        return {"status": "error", "message": hata_mesaji}
@app.post("/process-documents")
async def process_documents(
    identity_file: UploadFile = File(...),
    deed_file: UploadFile = File(...),
    statement_file: UploadFile = File(...),
    bank_file: UploadFile = File(...),
    claim_file_number: str = Form(...)
):
    print("\n--- HASAR DOSYASI OLU�?TURULUYOR ---")
    
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)

    def process_single_file(file_obj, prefix):
        file_path = os.path.join(temp_dir, f"{prefix}_{file_obj.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj.file, buffer)
        text = extract_text(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        return text

    try:
        print("1. Belgeler OCR ile taranıyor...")
        identity_text = process_single_file(identity_file, "kimlik")
        deed_text = process_single_file(deed_file, "tapu")
        statement_text = process_single_file(statement_file, "dilekce")
        bank_text = process_single_file(bank_file, "iban")
        print("\n===== KİMLİK HAM METNİ =====")
        print(identity_text)
        print("============================\n")

        print("\n===== IBAN HAM METNİ =====")
        print(bank_text)
        print("==========================\n")
        print("2. OCR metinlerinden veriler Regex ile ayıklanıyor...")
        identity_data = extract_identity_info(identity_text)
        deed_data = extract_deed_info(deed_text)
        statement_data = extract_statement_info(statement_text)
        bank_data = extract_bank_info(bank_text)
        print("Ayiklanan kimlik verisi:", identity_data)
        print("Ayiklanan IBAN verisi:", bank_data)
        print("3. İsim uyuşmazlığı kontrolleri yapılıyor...")
        validation_warnings = []
        add_missing_field_warnings(
            validation_warnings, identity_data, "Kimlik",
            {"tc_no": "T.C. kimlik numarası"},
        )
        add_missing_field_warnings(
            validation_warnings, deed_data, "Tapu",
            {"block": "ada numarası", "parcel": "parsel numarası"},
        )
        add_missing_field_warnings(
            validation_warnings, statement_data, "İmzalı beyan dilekçesi",
            {"incident_date": "hasar tarihi"},
        )
        add_missing_field_warnings(
            validation_warnings, bank_data, "IBAN / banka hesap bilgisi",
            {"iban": "IBAN numarası"},
        )
        base_name = identity_data.get("full_name")

        if base_name:
            if deed_data.get("owner_name") and normalize_person_name(deed_data["owner_name"]) != normalize_person_name(base_name):
                validation_warnings.append("âš  Tapu sahibi ile kimlikteki isim uyuÅŸmuyor.")
            
            if statement_data.get("insured_name") and normalize_person_name(statement_data["insured_name"]) != normalize_person_name(base_name):
                validation_warnings.append("⚠ Dilekçedeki sigortalı ismi ile kimlik uyuşmuyor.")
                
            if bank_data.get("account_holder") and normalize_person_name(bank_data["account_holder"]) != normalize_person_name(base_name):
                validation_warnings.append("âš  IBAN hesap sahibi ile kimlikteki isim uyuÅŸmuyor.")

        claim_data = {
            "claim_type": "Dahili Su Hasarı",
            "file_number": claim_file_number,
            "insured": identity_data,
            "property": deed_data,
            "claim": statement_data,
            "bank_account": bank_data,
            "validation_warnings": validation_warnings,
            "validation_status": "needs_review" if validation_warnings else "validated",
            "status": "Ön İnceleme Bekliyor"
        }

        print("Hasar Dosyası Başarıyla Oluşturuldu!")
        if validation_warnings:
            print(f"Dogrulama tamamlandi: {len(validation_warnings)} uyari bulundu.")
            for warning in validation_warnings:
                print(f" - {warning}")
        else:
            print("Dogrulama tamamlandi: uyari yok.")
        return {"status": "success", "data": claim_data}

    except Exception as e:
        print("!!! HASAR DOSYASI OLU�?TURMA HATASI !!!")
        print(traceback.format_exc())
        return {"status": "error", "message": f"Belge işleme sırasında hata: {str(e)}"}
