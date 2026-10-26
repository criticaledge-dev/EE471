# Speech Studio — Speech to Text

Flask ve Azure Speech Python SDK ile WAV yükleyerek en-US veya tr-TR konuşmayı
metne dönüştürme. Yalnızca STT içerir; mikrofon erişimi gerekmez.

## Windows PowerShell kurulumu

Python 3.10 veya üzeri kurulu olmalıdır. Repo kökünden:

```powershell
cd .\Week-5-Task-1
# Mevcut .venv varsa koruyun; yalnızca yoksa oluşturun.
if (!(Test-Path -LiteralPath .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

http://127.0.0.1:5000 adresini açın. Sunucuyu `Ctrl+C` ile durdurun.
Import edildiğinde sunucu başlamaz; sanal ortamı etkinleştirmek gerekmez.

## Yerel Azure ayarları

Mevcut `.env` ve `.venv` bu geliştirme sırasında korunmuştur; içerikleri
okunmamış, silinmemiş veya Git'e eklenmemiştir. Yerel gerçek denemede `.env`
yoksa kullanıcı `.env.example` dosyasını kopyalayabilir:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
```

`SPEECH_KEY` alanına kendi Azure Speech kaynağınızın anahtarını,
`SPEECH_REGION` alanına aynı kaynağın bölgesini girin. Örnekte `eastus`
bulunur; kendi kaynağınız farklıysa değiştirin. Değerleri loglara, tarayıcıya
veya Git'e aktarmayın. Ayarları girdikten sonra sunucuyu yeniden başlatın.

`speech_service.py`, yalnızca geçerli bir tanıma isteğinde python-dotenv ile
`Path(__file__).resolve().parent / ".env"` açık yolunu yükler. Mevcut ortam
değişkenleri önceliklidir (`override=False`). SDK yapılandırması yalnızca
`subscription=SPEECH_KEY` ve `region=SPEECH_REGION` kullanır. Ayarlar
eksikken ana sayfa ve statik dosyalar yine açılır.

## Desteklenen ses ve sınırlar

- Klasik RIFF/WAVE, sıkıştırılmamış PCM (format kodu 1), signed 16-bit,
  mono, 16.000 Hz. Float, stereo, sıkıştırılmış ve WAVE_FORMAT_EXTENSIBLE
  dosyaları desteklenmez; otomatik dönüştürme yapılmaz.
- Dosya en fazla 1 MiB (1.048.576 bayt), gerçek PCM örnek süresi en fazla
  30 saniye olabilir. Multipart isteğinin tamamı için ek 64 KiB pay vardır.
- Uzantı ve istemcinin MIME bilgisine güvenilmez: RIFF boyutu, bölüm
  sınırları, fmt/data alanları, örnek hizalaması ve süre sunucuda doğrulanır.
- `recognize_once_async()` yalnızca tek ifadeyi tanır; ilk sessizlikte
  veya yaklaşık 30 saniyede biter. 30 saniyelik dosya kabul edilmesi,
  içindeki birden fazla ifadenin tamamının yazıya döküleceği anlamına gelmez.

Doğrulanmış ham PCM bellekte, her isteğe özel `PushAudioInputStream` ile
SDK'ya gönderilir. WAV başlığı akışa gönderilmez. Mikrofon, ortak dosya veya
geçici ses dosyası kullanılmaz; akış başarı ve hata sonrasında kapatılır.

SDK referansları: [tek seferlik tanıma sınırı](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer),
[ses akışı biçimi](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-use-audio-input-streams).

## API ve arayüz

`GET /` başlangıç sayfasını sunar. `POST /api/stt`, `multipart/form-data`
olarak `audio` dosyası ve `language` (`en-US` veya `tr-TR`) alır. Başarıda
`{"text":"..."}`, hatada `{"error":"..."}` döner.

| Durum | HTTP |
| --- | --- |
| Geçersiz dosya, biçim, süre veya dil | 400 |
| Dosya/istek boyut sınırı aşıldı | 413 |
| Konuşma tanınamadı veya boş sonuç | 422 |
| Eksik sunucu ayarları | 503 |
| Azure iptal, kimlik doğrulama, kota veya bağlantı sorunu | 502 |
| Beklenmeyen uygulama hatası | 500 |

Ham SDK hata ayrıntıları veya sırlar döndürülmez ve loglanmaz. Yeni istekte
eski metin temizlenir, beklerken tekrar gönderim engellenir. Sonuç
`textContent` ile yerleştirilir; kopyalanabilir veya UTF-8 TXT olarak
indirilebilir. Kopyalama için tarayıcı izni ve localhost/güvenli bağlam gerekir;
izin yoksa metin seçilebilir veya indirilebilir. Eski indirme URL'leri bırakılır.

## Testler

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_stt.py -v
```

Testler SDK nesnelerini ve dotenv yüklemesini mock eder; gerçek `.env` okumaz,
anahtar kullanmaz veya Azure isteği yapmaz. Bunlar gerçek Azure doğrulaması
değildir. Başarı, tanınmayan konuşma, servis hataları, geçersiz dosya/dil,
boyut/süre sınırları, akış kapatma, ana sayfa ve statik dosyalar kontrol edilir.
Gerçek Azure denemesinin kullanıcı tarafından bildirilen sonucu aşağıdadır;
bu sonuç mock testlerinden ayrıdır.

### Kullanıcı tarafından doğrulanan gerçek Azure STT denemesi

Türkçe WAV dosyası Azure STT ile doğru metne dönüştürüldü. Kullanıcı ayrıca
metni kopyalamayı, TXT olarak indirmeyi ve hata sonrasında uygulamayı tekrar
kullanmayı doğruladı. Bu deneme kullanıcı tarafından yerelde yapıldı.

### Part 3 entegrasyon notu

TTS branch'inin mevcut WAV çıktısı 24 kHz, 16-bit, mono PCM; bu STT sürümü
ise 16 kHz, 16-bit, mono PCM kabul eder. Mevcut TTS çıktısı bu nedenle
doğrudan STT giriş biçimiyle uyumlu değildir.

Part 3 birleşiminde TTS çıktı formatı 16 kHz, 16-bit, mono PCM WAV olarak
ayarlanacak ve üretilen dosyanın doğrudan STT'ye yüklenmesi test edilecektir.
Bu entegrasyon testi henüz yapılmadı; mevcut STT doğrulama kuralları korunur.
Yerel dönüştürme denemesi için kurulan `scipy` uygulama tarafından
kullanılmadığından `requirements.txt` bağımlılıklarına eklenmez.

Mevcut sanal ortamı korumak için geliştirme kontrollerinde kullanılan ayrı
`.test-deps/` bağımlılık klasörü de Git dışında tutulur. Normal yerel kullanımda
bu klasöre ihtiyaç yoktur. `.env.example` Git tarafından izlenebilir.
