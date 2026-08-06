import os
import json
from groq import Groq
from dotenv import load_dotenv
from rules.settings import VISION_MODEL

load_dotenv()


class DocumentAnalysisError(RuntimeError):
    """Raised when a document cannot be analyzed by Groq."""


def analyze_document_with_ai(base64_image):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise DocumentAnalysisError("Groq API anahtari yapilandirilmamis.")

    client = Groq(api_key=api_key)

    system_prompt = """Sen kıdemli bir sigorta operasyonları, hasar yönetimi ve belge doğrulama uzmanısın.
Görev: Yüklenen sigorta hasar dosyası görselini incelemek ve aşağıdaki adımları SIRAYLA uygulayarak sınıflandırmak.
 
Görsel bulanık, karanlık, aşırı kırpılmış, yırtık veya yazıların büyük kısmı okunamayacak durumdaysa:
→ document_type = "Belge tipi tespit edilemedi. Lütfen tekrar yükleyiniz"
Bu durumda 2. ve 3. adımlara geçme.
 
Belge net okunabiliyorsa, aşağıdaki 4 kategoriden SADECE BİRİNE, o kategorinin "Tanımlayıcı işaretleri" bölümündeki kriterlere göre eşleştir. Bir belgeyi sırf birkaç anahtar kelime veya alan adı ortak diye bir kategoriye sokma — belgenin RESMİ BA�?LI�?INA ve asıl AMACINA bak.
 
1. **Tapu Belgesi**
   Tanımlayıcı işaretleri: Başlıkta "TAPU SENEDİ" veya "TAPU KAYDI"; ada/parsel no, mülkiyet bilgisi, Tapu Müdürlüğü kaşesi.
 
2. **Kimlik Belgesi**
   Tanımlayıcı işaretleri: T.C. Kimlik Kartı, Nüfus Cüzdanı veya Pasaport — kişinin FOTO�?RAFI ve kimlik doğrulama amaçlı resmi kart/kitapçık formatı.
   ❌ HARİÇ TUTULUR: "Kimlik No", "Adı", "Soyadı" gibi alanlar içeren ama başlığı farklı olan belgeler (örn. "YERLE�?İM YERİ VE Dİ�?ER ADRES BELGESİ" / İkametgah Belgesi) bu kategoriye SOKULMAZ, çünkü bu bir ADRES belgesidir, kimlik belgesi değildir. Böyle bir belge geldiğinde ADIM 3'e geç.
 
3. **İmzalı Beyan Dilekçesi**
   Tanımlayıcı işaretleri: Sigorta şirketine hitaben yazılmış (el yazısı veya bilgisayar çıktısı), olayı anlatan, talepte bulunan, imza içeren bir metin/dilekçe.
 
4. **IBAN / Banka Hesap Bilgisi**
   Tanımlayıcı işaretleri: "TR" ile başlayan 26 haneli IBAN numarası ve/veya banka adı-logosu içeren ekran görüntüsü, "dekont" ibaresi içeren veya içermeyen form.
 
Belge net okunabiliyor ama yukarıdaki 4 kategoriden hiçbirinin "Tanımlayıcı işaretleri"ne uymuyorsa (örn. manzara fotoğrafı, market fişi, ikametgah belgesi, sürücü belgesi, öğrenci belgesi vb.):
→ document_type = "Yanlış belge yüklediniz. Lütfen doğru belgeyi yükleyiniz."
 
SADECE aşağıdaki JSON formatında çıktı ver. JSON dışında hiçbir açıklama, selamlama veya markdown yazma:
 
{
    "document_type": "<yukarıdaki 4 kategori adından biri (tam olarak, ek ifade eklemeden) YA DA 'Belge tipi tespit edilemedi. Lütfen tekrar yükleyiniz' YA DA 'Yanlış belge yüklediniz. Lütfen doğru evrakı yükleyiniz'>",
    "confidence": <0-100 arası tam sayı>,
    "reason": "<Bu sonuca varmandaki en önemli 1-2 somut kanıt (belgede gördüğün başlık/alan/ifade), tek cümle, en fazla 25 kelime>"
}"""

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Aşağıda analizi yapılacak olan belge görseli bulunmaktadır. Belgeyi kurallara göre sınıflandır."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0,
            max_completion_tokens=1024,
            reasoning_effort="none",
        )
        raw_output = response.choices[0].message.content
        if not raw_output:
            raise ValueError("Groq returned an empty response.")

        cleaned_output = raw_output.replace('```json', '').replace('```', '').strip()
        json_start = cleaned_output.find("{")
        json_end = cleaned_output.rfind("}")
        if json_start == -1 or json_end == -1:
            raise ValueError("Groq yanitinda JSON nesnesi bulunamadi.")

        return json.loads(cleaned_output[json_start : json_end + 1])
    except Exception as e:
        print(f"Groq analysis failed: {e}")
        raise DocumentAnalysisError(
            "Belge yapay zeka ile analiz edilemedi. Groq baglantisini ve API ayarlarini kontrol edin."
        ) from e
        print(f"Groq Analiz Hatası: {str(e)}")
        return {
            "document_type": "Belge tipi tespit edilemedi. Lütfen tekrar yükleyiniz",
            "confidence": 0,
            "reason": f"Sistem hatası: {str(e)}"
        }
