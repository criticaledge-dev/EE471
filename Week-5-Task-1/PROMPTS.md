# Geliştirme istemi

```text
EE471 Week 5 Task 1 Part 1: Azure Text to Speech uygulamasını oluştur.

Önce AGENTS.md varsa oku ve aktif branch'i kontrol et.
Branch text-to-speech değilse dosya değiştirmeden dur.
Yalnızca Week-5-Task-1 klasörü içinde çalış.
Week3, Week4 ve diğer projeleri değiştirme.

Bu aşamada yalnızca çalışan TTS özelliğini geliştir.
STT, diarization, çeviri veya telaffuz değerlendirmesi ekleme.

Dosya yapısı:
Week-5-Task-1/
  app.py
  speech_service.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  PROMPTS.md
  templates/index.html
  static/style.css
  static/script.js
  tests/

Backend:
- Flask kullan; GET / ile index.html sun.
- POST /api/tts JSON kabul et:
  {"text":"Hello world","language":"en-US"}
- Azure Speech Python SDK ile gerçek ses üret.
- Dil seçenekleri en-US ve tr-TR olsun.
- Seçilen dil için uygun standart neural voice kullan;
  HD/özel ses gerektirme.
- Başarıda WAV dosyası baytlarını audio/wav yanıtıyla döndür.
- RIFF başlığı içeren PCM WAV çıktı biçimini açıkça seç.
- Ses üretimini speech_service.py içinde tut.
- Ses sunucunun hoparlöründen çalmasın; tarayıcıya gönderilsin.
- Mümkünse bellek içi çıktı kullan; ortak output.wav dosyası
  üzerinden istekleri birbirine karıştırma.
- Metin boş olmayan string olsun; en fazla 1000 karakter.
- Dil desteklenmiyorsa veya JSON geçersizse 400 ve
  {"error":"..."} döndür.
- Eksik yapılandırma için açıklayıcı JSON hata yanıtı ver.
- Azure iptal/kimlik doğrulama/kota/bağlantı hatalarında
  sahte başarı döndürme; kullanıcıya anlaşılır hata göster.
- Ham exception veya gizli bilgileri istemciye aktarma.
- Azure ayarları eksik olsa da ana sayfa açılabilsin.

Yapılandırma:
- requirements.txt içine flask, python-dotenv ve
  azure-cognitiveservices-speech ekle.
- .env dosyasını proje klasörüne göre açık bir yoldan yükle.
- Bu aşamada SpeechConfig için SPEECH_KEY ve SPEECH_REGION kullan.
- .env.example:
  SPEECH_KEY=
  SPEECH_REGION=eastus
- Gerçek .env oluşturma, mevcut .env içeriğini okuma/yazdırma.
- Anahtarı kod, HTML, JavaScript, log veya belgelerde gösterme.
- .gitignore: .env, .venv/, __pycache__/, *.pyc ve geçici sesler.
- .env.example izlenebilir kalsın.

Arayüz:
- Başlık: Speech Studio — Text to Speech.
- Metin alanı, dil seçimi ve Generate Speech butonu.
- Ses üretildiğinde audio controls ile oynatma.
- Üretilen WAV için indirme bağlantısı.
- Bekleme sırasında tekrar gönderimi engelle.
- Hata mesajını görünür bir alanda göster.
- Başarısız yeni istekte eski sesi yeni sonuç gibi sunma.
- Yenilenen sesler için eski object URL'lerini serbest bırak.
- Açık renkli, ortalanmış, maksimum genişliği sınırlı,
  dar ekranlarda taşmayan sade bir tasarım yap.
- API çağrısı yalnızca kendi Flask backend'ine yapılsın;
  tarayıcıya Azure anahtarı gönderme.

Doğrulama:
- Azure çağrısını mock ederek başarılı WAV yanıtını,
  geçersiz girdileri, eksik yapılandırmayı ve servis hatasını test et.
- Mock testlerini gerçek Azure bağlantı testi olarak tanımlama.
- Gerçek Azure isteği yapma; bunu kullanıcı yerelde deneyecek.
- Ana sayfa ve statik dosyaların sunulduğunu kontrol et.

README'ye PowerShell kurulum/çalıştırma adımlarını,
.env hazırlığını ve test komutunu ekle.
Bu istemi PROMPTS.md'ye kaydet.
Commit, push, merge veya branch işlemi yapma.
Bitince değişiklikleri ve test sonuçlarını özetle.
```
