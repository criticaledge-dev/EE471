# Speech Studio — Text to Speech

Flask ve Azure Speech Python SDK ile en-US (`en-US-JennyNeural`) ve tr-TR
(`tr-TR-EmelNeural`) metinden ses üretimi. STT veya diğer konuşma özellikleri içermez.

## Windows PowerShell

Python 3.10 veya üzeri kurulu olmalıdır. Repo kökünden:

```powershell
cd .\Week-5-Task-1
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Bu çalışma sırasında gerçek `.env` oluşturulmadı veya okunmadı. Yerelde gerçek
Azure denemesi için `.env` henüz yoksa aşağıdaki komutla hazırlayın; mevcut
dosyanızın üzerine yazmayın:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe app.py
```

Editörde `SPEECH_KEY` alanını kendi Azure Speech anahtarınızla, `SPEECH_REGION`
alanını aynı kaynağın bölgesiyle doldurun. Örnekteki `eastus` yalnızca varsayılan
bölgedir. Anahtarı terminale, Git'e, loglara veya tarayıcıya aktarmayın.
http://127.0.0.1:5000 adresini açın; sunucuyu `Ctrl+C` ile durdurun.
Sanal ortamı etkinleştirmek gerekmez. Import işlemi sunucuyu başlatmaz.

## Davranış ve yapılandırma

`GET /` ayarlar eksikken de açılır. `POST /api/tts`, JSON olarak
`{"text":"Hello world","language":"en-US"}` kabul eder. Metin boş olmayan
string olmalı ve ham uzunluğu 1000 karakteri aşmamalıdır. Desteklenmeyen dil,
geçersiz JSON veya girdiler 400; eksik ayarlar 503; Azure iptal veya servis
hataları 502; beklenmeyen uygulama hataları güvenli bir mesajla 500 döndürür.
Hatalar `{"error":"..."}` biçimindedir; SDK hata ayrıntıları istemciye verilmez.

`speech_service.py`, `.env` dosyasını `Path(__file__).resolve().parent / ".env"`
açık yolundan `python-dotenv` ile yalnızca ses istendiğinde yükler. Mevcut ortam
değişkenleri önceliklidir (`override=False`). SpeechConfig yalnızca
`subscription=SPEECH_KEY` ve `region=SPEECH_REGION` kullanır; endpoint kullanılmaz.

SDK açıkça `Riff24Khz16BitMonoPcm` seçer: RIFF başlıklı, 24 kHz, 16 bit, mono
PCM WAV. `audio_config=None` sayesinde sunucunun hoparlörü kullanılmaz.
Her isteğin `result.audio_data` baytları bellekte işlenir ve `audio/wav` olarak
döndürülür; ortak dosya veya geçici ses dosyası oluşturulmaz. Tarayıcı oynatma
ve indirme için object URL kullanır, yenisinden önce eskisini serbest bırakır.
Yeni istek başladığında önceki sonuç temizlenir.

SDK kaynakları: [ses üretimi ve çıktı biçimi](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis),
[desteklenen sesler](https://learn.microsoft.com/azure/cognitive-services/speech-service/language-support?tabs=tts).

## Testler

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Testler SDK çağrılarını ve dotenv yüklemesini mock eder. Gerçek `.env` okumaz,
Azure'a bağlanmaz; bunlar gerçek Azure bağlantı testleri değildir. WAV yanıtı,
girdi doğrulaması, eksik ayarlar, servis hataları, ana sayfa ve statik dosyalar
kontrol edilir. Gerçek ses üretimini kullanıcı yerelde kendi Azure kaynağıyla
dener; kaynak kullanımı Azure kotasına ve ücretlendirmesine tabidir.

`.env`, `.venv/`, Python önbellekleri ve geçici sesler `.gitignore` kapsamındadır;
`.env.example` izlenebilir. `PROMPTS.md` geliştirme istemini içerir.
