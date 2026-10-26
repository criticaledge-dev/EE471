# Speech Studio — Text to Speech ve Speech to Text

Tek Flask uygulamasında İngilizce (`en-US`) ve Türkçe (`tr-TR`) TTS ve STT.
TTS standart `en-US-JennyNeural` / `tr-TR-EmelNeural` seslerini kullanır;
STT dosyadan tek seferlik tanıma yapar. Mikrofon erişimi gerekmez.

## Windows PowerShell kurulumu ve çalıştırma

Python 3.10 veya üzeri kurulu olmalıdır. Repo kökünden:

```powershell
cd .\Week-5-Task-1
if (!(Test-Path -LiteralPath .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Mevcut `.env` ve `.venv` korunur. Yerelde ayar dosyası yoksa kullanıcı
aşağıdaki komutla hazırlayabilir; mevcut dosyanın üzerine yazılmaz:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe app.py
```

Editörde `SPEECH_KEY` alanına Azure Speech kaynağınızın anahtarını,
`SPEECH_REGION` alanına aynı kaynağın bölgesini girin. Örnekteki `eastus`
yerine gerektiğinde kendi bölgenizi kullanın. Ayarlardan sonra sunucuyu
yeniden başlatın. http://127.0.0.1:5000 adresini açın; `Ctrl+C` ile durdurun.
Sanal ortamı etkinleştirmek gerekmez. Import işlemi sunucuyu başlatmaz.

## Ortak yapılandırma ve sırayla çalışma

`speech_service.py`, her iki konuşma işlemi için ortak yapılandırmayı
`Path(__file__).resolve().parent / ".env"` açık yolundan python-dotenv ile
yükler. `override=False` sayesinde mevcut ortam değişkenleri önceliklidir.
SDK `subscription=SPEECH_KEY`, `region=SPEECH_REGION` kullanır; endpoint
kullanılmaz. Ayarlar yalnızca konuşma isteğinde yüklenip doğrulanır.
Ana sayfa ve statik dosyalar eksik Azure ayarlarıyla da açılır.

Anahtarlar, kullanıcı metni ve ham SDK hataları istemciye veya loglara
aktarılmaz. Bu merge çözümünde gerçek `.env` okunmamış veya değiştirilmemiştir.

F0 üzerinde eşzamanlı istekleri önlemek için arayüzde bir işlem sürerken
iki gönderim butonu da devre dışı kalır. Sunucuda ortak kilit TTS ve STT
SDK işlemlerini farklı istemcilerden gelseler bile sırayla çalıştırır.
Bu kilit tek Python süreci kapsamındadır: yerel uygulamayı tek süreçle
çalıştırın. Birden fazla worker/sunucu için ortak dış kuyruk gerekir.
Hata sonrasında kilit ve arayüz kontrolleri serbest bırakılır.

## TTS — metinden WAV

`POST /api/tts`, `application/json` olarak
`{"text":"Hello world","language":"en-US"}` kabul eder. Metin boş olmayan
string olmalı ve ham uzunluğu 1000 karakteri aşmamalıdır. Dil `en-US` veya
`tr-TR` olmalıdır. Başarı yanıtı `audio/wav` baytlarıdır; tarayıcıda
oynatılabilir ve `speech.wav` olarak indirilebilir.

SDK çıktı biçimi açıkça `SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm`
olarak seçilir: RIFF başlıklı, 16 kHz, 16-bit, mono PCM WAV. Azure sesi bu
biçimde üretir; mevcut 24 kHz sesin başlığını değiştirme veya yerelde yeniden
örnekleme yapılmaz. Önceki TTS branch'indeki 24 kHz seçimi birleşimde
16 kHz olarak düzeltildi. `scipy` kullanılmaz ve bağımlılıklara eklenmez.

`audio_config=None` ile sunucunun hoparlöründen ses çalınmaz. Her isteğin
`result.audio_data` baytları bellekte işlenir; ortak çıktı dosyası kullanılmaz.

## STT — WAV'dan metin

`POST /api/stt`, `multipart/form-data` olarak `audio` dosyası ve
`language` (`en-US` / `tr-TR`) alanını alır. Başarıda `{"text":"..."}` döner.

- Yalnızca klasik RIFF/WAVE, sıkıştırılmamış PCM (format kodu 1), signed
  16-bit, mono, 16.000 Hz desteklenir. Float, stereo, sıkıştırılmış ve
  WAVE_FORMAT_EXTENSIBLE dosyaları kabul edilmez; otomatik dönüştürme yoktur.
- En fazla 1 MiB (1.048.576 bayt) dosya ve 30 saniye PCM örneği kabul edilir.
  Multipart isteğinin tamamı için ek 64 KiB pay vardır.
- Uzantıya veya MIME bilgisine güvenilmez: RIFF boyutu, bölüm sınırları,
  fmt/data alanları, örnek hizalaması ve gerçek örnek süresi doğrulanır.
- `recognize_once_async()` tek ifadeyi tanır; ilk sessizlikte veya yaklaşık
  30 saniyede biter. Birden fazla ifadenin tamamının tanınacağı garanti edilmez.

Doğrulanan ham PCM, isteğe özel `PushAudioInputStream` ile gönderilir;
WAV başlığı SDK akışına yazılmaz. Akış başarı ve hata sonrasında kapatılır.
Uygulama ortak veya geçici ses dosyası oluşturmaz.

TTS'den indirilen WAV dosyası biçim bakımından doğrudan STT'ye yüklenebilir.
Ancak uzun TTS kayıtları STT'nin 30 saniye / 1 MiB sınırlarını aşabilir ve
reddedilir. Uzun kayıtların tamamının kabul edileceği iddia edilmez.

## Arayüz ve hatalar

`GET /` aynı sayfada ayrı TTS ve STT bölümlerini sunar. DOM kimlikleri,
sonuç, hata ve bekleme alanları bölüm bazında ayrıdır. Yeni istekte ilgili
bölümün önceki sonucu temizlenir; başarısız istek eski sonucu göstermez.
Eski WAV/TXT object URL'leri bırakılır. STT metni `textContent` ile yerleştirilir;
kopyalanabilir veya UTF-8 TXT indirilebilir. Kopyalama için localhost/güvenli
bağlam ve tarayıcı izni gerekir; izin yoksa indirme veya elle kopyalama yapılabilir.

Hata yanıtları `{"error":"..."}` biçimindedir:

| Durum | HTTP |
| --- | --- |
| Geçersiz JSON, metin, dosya, biçim, süre veya dil | 400 |
| Dosya/istek boyut sınırı aşıldı | 413 |
| STT konuşmayı tanıyamadı veya boş sonuç döndü | 422 |
| Azure ayarları eksik | 503 |
| Azure iptal, kimlik doğrulama, kota veya bağlantı sorunu | 502 |
| Beklenmeyen uygulama hatası | 500 |

## Mock testleri ve gerçek doğrulama

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node --test tests/test_ui.cjs
```

Node.js yalnızca bağımlılıksız arayüz mock testleri içindir; uygulamayı
çalıştırmak için gerekli değildir. Python testleri iki branch'in testlerini
korur. TTS'nin SDK'da 16 kHz çıktı biçimini seçmesi, STT biçim/süre kontrolleri,
başarı/hata yanıtları, ana sayfa/statik dosyalar ve ortak sunucu kilidi sınanır.
Mock TTS WAV yanıtı doğrudan STT route'una yüklenerek birleşik akış da kontrol edilir.
Arayüz testleri ortak gönderim engeli, ayrı sonuç/hata alanları, yeniden kullanım,
kopyalama, indirme ve object URL temizliğini sahte DOM/fetch ile doğrular.

Bu testler gerçek `.env` okumaz veya Azure çağrısı yapmaz. Mock WAV'ın
doğrudan yüklenebilmesi gerçek Azure TTS→STT doğrulaması değildir.
Gerçek tarayıcıda görsel/etkileşim kontrolü bu merge çözümünde yapılmadı.

Birleşim kontrol sonucu: 28 Python mock testi ve 3 Node.js arayüz mock testi
geçti. Kaynak dosyalarda merge işareti kalmadığı ve `.env.example` dosyasının
yok sayılmadığı kontrol edildi.

Kullanıcının daha önce STT branch'inde yerelde yaptığı gerçek Azure denemesi
başarılıdır: Türkçe WAV doğru metne dönüştürülmüş; kopyalama, TXT indirme ve
hata sonrası yeniden kullanım kullanıcı tarafından doğrulanmıştır.
Birleşik uygulamada gerçek Azure TTS→WAV→STT denemesi henüz yapılmadı;
kullanıcı kısa bir kayıtla bu akışı yerelde doğrulayabilir.

`.env`, `.venv/`, `.test-deps/`, Python önbellekleri ve geçici sesler Git dışında
tutulur; `.env.example` izlenebilir. Mevcut sanal ortamı korumak için önceki
kontrollerde kullanılan `.test-deps/` normal çalıştırmada gerekli değildir.
`PROMPTS.md` iki branch'in istem geçmişini ve birleşim isteğini saklar.

SDK kaynakları: [ses üretimi ve çıktı biçimi](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis),
[tek seferlik tanıma](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer),
[ses akışları](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-use-audio-input-streams).
