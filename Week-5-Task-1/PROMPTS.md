# Geliştirme istemi

```text
EE471 Week 5 Task 1 Part 2: Azure Speech to Text uygulaması oluştur.

Önce AGENTS.md varsa oku.
Aktif branch speech-to-text değilse dosya değiştirmeden dur.
Yalnızca Week-5-Task-1 içinde çalış.

Bu branch, TTS geliştirmesinden önceki başlangıçtan geliyor.
main veya text-to-speech branch'inden dosya alma, merge yapma.
Bu aşamada yalnızca STT geliştir; TTS ekleme.

Dosya yapısı:
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
  tests/test_stt.py

Özellik:
- Flask GET / üzerinden Speech Studio — Speech to Text sayfası sun.
- Kullanıcı WAV dosyası yükleyip dil seçebilsin:
  en-US veya tr-TR.
- POST /api/stt multipart/form-data kabul et:
  audio: dosya
  language: dil
- Azure Speech Python SDK ile sesi metne dönüştür.
- Başarıda {"text":"..."} JSON yanıtı döndür.
- Bu sürüm kısa kayıtlar için olsun; tek seferlik tanımayı kullan
  ve yaklaşık 30 saniyelik/tek ifadeli kullanım sınırını README
  ve arayüzde açıkla.
- İlk sürümde mikrofon zorunlu değil; WAV yükleme yeterli.

Ses doğrulama:
- Desteklenen formatı açıkça sınırla:
  sıkıştırılmamış PCM WAV, 16-bit, mono, 16 kHz.
- Yalnızca dosya uzantısına güvenme; WAV başlığını doğrula.
- Dosya boyutuna ve süresine sunucuda sınır koy.
- Boş/eksik dosya, bozuk WAV, desteklenmeyen format veya dil
  için açıklayıcı JSON hata yanıtı ver.
- Konuşma tanınamazsa bunu başarılı metin sonucu gibi gösterme.
- Azure iptal/kimlik doğrulama/kota/bağlantı hatalarını yönet.
- Geçici dosya kullanırsan her istek için benzersiz olsun ve
  başarı/hata sonrasında temizlensin.

Yapılandırma:
- flask, python-dotenv, azure-cognitiveservices-speech kullan.
- Yerel .env dosyasını proje klasörüne göre yükle.
- SPEECH_KEY ve SPEECH_REGION kullan.
- Gerçek .env dosyasını okuma, değiştirme veya çıktılama;
  uygulama çalışırken dotenv üzerinden yüklenmesi yeterli.
- .env.example içine boş anahtar ve eastus bölgesi koy.
- .gitignore ile .env, .venv/, __pycache__/, *.pyc ve geçici
  ses dosyalarını Git dışında tut.
- Anahtarları istemciye veya loglara aktarma.
- Ayarlar eksik olsa da ana sayfa açılabilsin.

Arayüz:
- WAV seçme, dil seçimi ve Transcribe butonu.
- Bekleme, hata ve sonuç alanları.
- Sonuç metnini kopyalama ve TXT olarak indirme.
- İstek sürerken tekrar gönderimi engelle.
- Başarısız yeni istekte önceki metni yeni sonuç gibi gösterme.
- Kullanıcı metinlerini textContent ile yerleştir.
- Sade, açık renkli ve dar ekrana uyumlu tasarım kullan.

Testler:
- Azure çağrısını mock ederek başarı, tanınmayan konuşma,
  servis hatası ve geçersiz dosya/dil durumlarını kontrol et.
- Gerçek anahtarı okuma veya gerçek Azure isteği yapma.
- Mock testlerini gerçek Azure doğrulaması olarak sunma.
- Ana sayfanın ve statik dosyaların sunulduğunu kontrol et.

README'ye PowerShell kurulum/çalıştırma, desteklenen ses
formatı ve test komutlarını ekle.
Bu istemi PROMPTS.md'ye kaydet.
Commit, push veya merge yapma.
Sonunda değişiklikleri ve test sonuçlarını özetle.

Branch değişiminden kalan yerel .env ve .venv dosyaları var.
Önce Week-5-Task-1/.gitignore dosyasını oluşturup bunları
yok say. İçeriklerini okuma, silme veya Git'e ekleme.
Mevcut sanal ortamı koru.
```

## Gerçek Azure doğrulaması ve Part 3 entegrasyon notu istemi

```text
Yalnızca Week-5-Task-1 içinde README.md ve PROMPTS.md'yi güncelle.

Gerçek Azure STT denemesi başarılı:
Türkçe WAV doğru metne dönüştürüldü; kopyalama, TXT indirme
ve hata sonrası tekrar kullanım kullanıcı tarafından doğrulandı.

Entegrasyon notu:
TTS branch'inin mevcut WAV çıktısı 24 kHz, 16-bit, mono PCM.
STT 16 kHz, 16-bit, mono PCM kabul ediyor.
Part 3 birleşiminde TTS çıktı formatı 16 kHz PCM WAV olarak
ayarlanacak ve üretilen dosyanın doğrudan STT'ye yüklenmesi
test edilecek.

Bu aşamada STT davranışını değiştirme.
Diğer branch'lerden dosya alma ve merge yapma.
Dönüştürme denemesi için yerelde kurulan scipy'yi,
uygulama kullanmıyorsa requirements.txt'ye ekleme.
Commit veya push yapma.
```
