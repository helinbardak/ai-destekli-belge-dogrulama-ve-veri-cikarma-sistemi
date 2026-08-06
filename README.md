\# AI Destekli Belge Doğrulama ve Veri Çıkarma Sistemi



Sigorta hasar dosyalarına belge ekleme sürecini otomatikleştiren, yapay zeka destekli bir doküman işleme platformu. Sistem; belge türü doğrulaması, OCR ile metin çıkarımı ve belgeler arası (kimlik, tapu, dilekçe, banka belgesi) çapraz bilgi tutarlılığı kontrolünü otomatik olarak gerçekleştirir.



\## Özellikler



\- Yapay zeka destekli görsel sınıflandırma ile belge türü doğrulama

\- OCR ile belgelerden otomatik metin ve veri çıkarımı

\- Belgeler arası çapraz bilgi tutarlılığı kontrolü (ör. kimlikteki ad-soyad ile diğer belgelerin karşılaştırılması)

\- Hataya dayanıklı, kural tabanlı veri ayrıştırma katmanı

\- Web tabanlı kullanıcı arayüzü ile belge yükleme ve sonuç görüntüleme



\## Kullanılan Teknolojiler



\*\*Backend:\*\* Python, FastAPI, EasyOCR, Groq Vision API, PyMuPDF, Uvicorn



\*\*Frontend:\*\* React, TypeScript, TanStack, Tailwind CSS



\## Kurulum



\### Backend



```bash

pip install -r requirements.txt

uvicorn main:app --reload

```



Groq API ile çalışabilmesi için proje kök dizininde bir `.env` dosyası oluşturup kendi API anahtarınızı eklemeniz gerekir.

\### Frontend



```bash

cd konuthasar

npm install

npm run dev

```



\## Not



Bu proje, Anadolu Sigorta'daki staj sürecimde edindiğim gözlemlerden yola çıkarak bireysel imkanlarımla geliştirdiğim bir demo çalışmasıdır. Şirkete ait herhangi bir gerçek veri veya iç kaynak kullanılmamıştır; sistemde yer alan tüm test belgeleri yapay zeka ile üretilmiş sentetik örneklerdir.

