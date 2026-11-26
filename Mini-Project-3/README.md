# EE471 Mini Project 3 · Image & Chat

[Figma tasarımı](https://www.figma.com/design/8hzmJx2sCtstQ6jEN8yUtc?node-id=1-2)

Tek ekranda yerel Whisper ile İngilizce mikrofon girişi, yerel SmolLM2-360M-Instruct
ile sohbet ve Stable Diffusion 1.5 ile yerel görsel üretimi. Mikrofondan gelen
yazı düzenlenebilir mesaj kutusuna gelir; Gönder'e basılana kadar chatbot'a
iletilmez. Sohbetteki görsel açıklamasını ayrı prompt kutusuna yapıştırın.

## Ubuntu/WSL'de çalıştırma

EE471 deponuzun kökünden mevcut sanal ortamı kontrol edin:

```bash
cd Mini-Project-3
.venv/bin/python -c 'import torch, transformers, numpy; print(torch.__version__, transformers.__version__, numpy.__version__)'
.venv/bin/python -m pip check
```

Temiz bir kurulumda `python3 -m venv .venv` ve ardından
`.venv/bin/python -m pip install -r requirements.txt` çalıştırın. Mevcut
uyumlu ortamı kullanıyorsanız doğrudan model hazırlığına geçin.

İlk mikrofon isteğinden önce modeli bir defa hazırlayın. Bu adım gerekli
dosyaları Hugging Face önbelleğine alır ve modelin yerelden açıldığını
kontrol eder. İlk hazırlıkta internet erişimi gerekir. [Whisper modeli](https://huggingface.co/openai/whisper-base.en).

```bash
HF_HUB_DISABLE_XET=1 HF_HUB_DOWNLOAD_TIMEOUT=90 .venv/bin/python -B whisper_service.py
```

Sunucuyu yerel Whisper ile başlatın:

```bash
MP3_SPEECH_BACKEND=whisper .venv/bin/python -B app.py
```

`whisper` varsayılan değerdir. Mikrofon kaydı tarayıcıdan yerel Flask
sunucusuna gider. İngilizce `openai/whisper-base.en` modeli yalnız
önbellekten, CPU üzerinde ilk geçerli konuşma isteğinde yüklenir ve aynı
sunucu sürecinde sonraki isteklerde kullanılır. Whisper için `.env` ve
Azure anahtarı gerekmez. Model ağırlıkları repo dışındaki Hugging Face
önbelleğinde tutulur.
Windows diski üzerinden çalışan WSL ortamında ilk model yüklemesi sonraki
isteklerden daha uzun sürebilir. Tarayıcı bu aşama için beş dakikaya kadar bekler.

Azure’u kullanmak isterseniz `SPEECH_KEY` ve `SPEECH_REGION` değerlerini
ortam değişkenleri olarak veya proje klasörünün yerel `.env` dosyasında
ayarlayıp `MP3_SPEECH_BACKEND=azure .venv/bin/python -B app.py` çalıştırın.
Azure ancak bu seçimle çağrılır ve internet bağlantısı gerektirir.

İlk sohbet ve ilk görsel isteği ilgili model dosyalarını indirip yükler;
masaya oturmadan önce ikisini de bir kez çalıştırın. Görsel modeli PyTorch
CUDA gördüğünde CUDA/FP16, aksi halde CPU/FP32 kullanır. Sohbet CPU'da
çalışır. CUDA testi için:

```bash
nvidia-smi
.venv/bin/python -c 'import torch; print("CUDA:", torch.cuda.is_available())'
```

`nvidia-smi` GPU'yu gösterse de PyTorch CUDA görmüyorsa ortamınıza uygun
CUDA destekli Torch paketini kurun. CPU üretimi yavaş olabilir;
gerçek 512×512 görseli oluşturmadan çekime başlamayın.

## Kendi makinenizde son kontrol

1. Tarayıcıda [127.0.0.1:5003](http://127.0.0.1:5003/) adresini açın,
   mikrofon düğmesine basıp izin verin. Örneğin “Add northern
   lights to the prompt.” deyin ve kaydı bitirmek için tekrar basın.
   Metnin düzenlenebilir sohbet kutusuna geldiğini ve otomatik
   gönderilmediğini kontrol edin.
2. Metni isterseniz düzenleyin. Gönder'e basıp chatbot yanıtını kontrol edin.
3. Modelin önerdiği promptu görsel açıklamasına yapıştırın. Görsel Üret'e
   basıp yeni görselin panelde göründüğünü doğrulayın.

Demo kaydı bu akışı göstermeli. Kod anlatımında
`app.py`, `generation.py`, `speech_service.py` ve `static/app.mjs`
dosyalarını sırayla gösterin. Mikrofon ve WAV dönüştürme kodu
Mini-Project-2'deki ses akışından uyarlanmıştır.

## Ses endpoint’i doğrulaması

```bash
.venv/bin/python -B -m unittest -v test_voice
MP3_TEST_WAV=../Week-8/samples/speech_16000_hz_mono.wav .venv/bin/python -B -m unittest -v test_voice
```

İkinci komut mevcut Week 8 WAV dosyasını yerinden okuyup aynı Flask
endpoint’ine gönderir. Bu adım için Whisper modeli hazırlanmış olmalıdır.

25 Kasım 2026 WSL doğrulamasında altı test geçti. Gerçek WAV isteği
HTTP 200 ve `language: en-US` ile “Send a text to Mike. I'll be home late tomorrow.”
metnini döndürdü. Bozuk WAV HTTP 400 aldı. Model yükleyicisinin iki geçerli
istekte bir kez çağrıldığı test edildi. Bu doğrulama Flask test istemcisiyle
yapıldı. Tarayıcı mikrofonu için yukarıdaki manuel adımları uygulayın.
