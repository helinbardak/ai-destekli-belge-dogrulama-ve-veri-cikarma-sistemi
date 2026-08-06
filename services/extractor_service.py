import re

# EasyOCR, düz sans-serif fontlarda rakamları harflerle sıkça karıştırır
# (ör. "0" -> "O", "1" -> "I"/"l", "5" -> "S", "8" -> "B", "2" -> "Z").
# Bu tablo yalnızca zaten sayısal olduğu bilinen alanlarda (T.C. no, IBAN)
# eşleşen karakterleri düzeltmek için kullanılır.
_OCR_DIGIT_FIX = str.maketrans({
    "O": "0", "o": "0",
    "I": "1", "i": "1", "L": "1", "l": "1",
    "S": "5", "s": "5",
    "B": "8", "b": "8",
    "Z": "2", "z": "2",
})


def _fix_ocr_digits(value):
    return value.translate(_OCR_DIGIT_FIX)


def _clean_name(value):
    """OCR'dan gelen ad bilgisini tek satir, okunabilir hale getirir."""
    if not value:
        return None

    value = re.sub(r"\s+", " ", value).strip(" :,-")
    value = re.split(
        r"\b(?:T\.?C\.?|DOGUM|DO[�?G]UM|CINSIYET|UYRUK|SER[Iİ]|NO)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    return value.title() if value else None


def _find_label_value(lines, labels):
    """Bir etiketin ayni veya bir sonraki OCR satirindaki degerini bulur."""
    label_pattern = "|".join(labels)
    for index, line in enumerate(lines):
        match = re.search(rf"(?:{label_pattern})\s*[:\-]?\s*(.*)$", line, re.IGNORECASE)
        if not match:
            continue

        value = match.group(1).strip()
        # Kimlik kartlarinda etiketin yaninda "(Given Name(s))" gibi
        # parantezli Ingilizce ceviri ipucu bulunabilir; OCR bunu ayni
        # satirda deger sanabilir. Bu durumda gercek deger bir alt satirdadir.
        if value and not value.startswith(("(", "{", "[")):
            return value
        if index + 1 < len(lines):
            return lines[index + 1].strip()
    return None


def extract_identity_info(text):
    if not text:
        return {"full_name": None, "tc_no": None, "birth_date": None}

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    tc_match = re.search(r"\b[1-9](?:[\s.-]*[0-9OoIiLlSsBbZz]){10}\b", text)
    tc_no = _fix_ocr_digits(re.sub(r"[\s.-]", "", tc_match.group(0))) if tc_match else None

    birth_match = re.search(r"\b(\d{2})[\s./-](\d{2})[\s./-](\d{4})\b", text)
    birth_date = (
        f"{birth_match.group(1)}.{birth_match.group(2)}.{birth_match.group(3)}"
        if birth_match
        else None
    )

    # Etiketlerin basina "\b" eklenmesi onemli: aksi halde ADI gibi kisa
    # etiketler, OCR'in bozdugu kelimelerin (orn. "Sayadı") icinde tesadufen
    # gecen harf dizileriyle de eslesip yanlis deger yakalayabiliyor.
    combined_name = _clean_name(_find_label_value(lines, [r"\bADI\s*SOYADI", r"\bAD\s*SOYAD"]))
    surname = _clean_name(_find_label_value(lines, [r"\bSOYADI", r"\bSURNAME"]))
    first_name = _clean_name(
        _find_label_value(lines, [r"\bADI(?!\s*SOYADI)", r"\bGIVEN\s*NAMES?", r"\bNAME"])
    )

    if not (surname and first_name) and tc_no:
        for index, line in enumerate(lines):
            if re.sub(r"\D", "", line) == tc_no and index + 2 < len(lines):
                surname = surname or _clean_name(lines[index + 1])
                first_name = first_name or _clean_name(lines[index + 2])
                break

    full_name = combined_name or " ".join(part for part in (first_name, surname) if part) or None
    return {"full_name": full_name, "tc_no": tc_no, "birth_date": birth_date}


def extract_deed_info(text):
    if not text:
        return {"owner_name": None, "property_address": None, "block": None, "parcel": None}

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    block_match = re.search(r"(?:Ada)\s*(?:No)?:?\s*(\d+)", text, re.IGNORECASE)
    parcel_match = re.search(r"(?:Parsel)\s*(?:No)?:?\s*(\d+)", text, re.IGNORECASE)
    # "Malik:" / "Sahibi:" etiketi satir sonunda deger tasir; bazi tapu
    # belgelerinde ise "MALIK BILGILERI" basligindan sonra "Adi Soyadi:"
    # etiketi ve deger bir alt satirda gelir. Ikisini de destekle.
    owner_name = _clean_name(
        _find_label_value(lines, [r"Malik\s*:", r"Sahibi\s*:", r"Ad[ıi]\s*Soyad[ıi]", r"Ad\s*Soyad"])
    )

    return {
        "owner_name": owner_name,
        "property_address": None,
        "block": block_match.group(1) if block_match else None,
        "parcel": parcel_match.group(1) if parcel_match else None,
    }


def extract_statement_info(text):
    if not text:
        return {"insured_name": None, "incident_date": None, "description": None, "address": None}

    date_match = re.search(r"\b(\d{2}[./]\d{2}[./]\d{4})\b", text)
    name_match = re.search(
        r"(?:Ad[ıi]\s*Soyad[ıi]|Ad\s*Soyad|Sigortal[ıi]|Beyan\s*Eden)\s*:?\s*([^\n]+)",
        text,
        re.IGNORECASE,
    )
    return {
        "insured_name": _clean_name(name_match.group(1)) if name_match else None,
        "incident_date": date_match.group(1) if date_match else None,
        "description": "Dahili su hasari beyani",
        "address": None,
    }


def extract_bank_info(text):
    if not text:
        return {"account_holder": None, "iban": None, "bank_name": None}

    # Bosluklar silindigi icin IBAN'dan hemen sonra baska bir kelime
    # gelebilir (ornegin "...0000TESTBELGESI"); bu yuzden sondaki "\b"
    # kelime siniri yerine sabit 24 karakter uzunlugu kullaniliyor.
    compact_text = re.sub(r"[\s._-]+", "", text).upper()
    iban_match = re.search(r"TR[0-9OILSBZ]{24}", compact_text)
    iban = _fix_ocr_digits(iban_match.group(0)) if iban_match else None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    account_holder = _clean_name(
        _find_label_value(lines, [r"HESAP\s*SAHIBI", r"ALICI", r"ADI\s*SOYADI"])
    )
    return {"account_holder": account_holder, "iban": iban, "bank_name": None}
