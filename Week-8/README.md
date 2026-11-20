# EE471 Week 8 — Aşama 1

**20 Kasım 2026 düzenlemesi:** Task 1'in tüm yeni demo çıktıları, logları ve çalışma önbellekleri `Week-8/task-1/output/` altında toplanır; kayıt PNG'leri `task-1/output/recording/` kullanır. Önceki üretilmiş sonuçlar depo dışına yedeklendi. Aşağıdaki geçmiş ölçümler korunmuştur; bu ölçümlere ait dosyalar temizlendiği için güncel çıktı klasörleri boştur. Komutlar yeni yola göre günceldir. Task 2/3 kendi `outputs/` yollarını kullanmaya devam eder.

Task 1 kapsamındaki **22 bağımsız Python demosu**. İlk üç demo ve ortamı korunarak kalan 19 araç eklendi. Kol/yön sınıflandırması, mikrofon, canlı akış, website, HTTP API, Postman veya Docker yoktur. Task 2 ve Task 3 uygulamaları henüz geliştirilmedi; yalnız kullanıcı tarafından verilen girdi fotoğrafları aşağıdaki konumlara eklendi.

## Task 2 ve Task 3 için verilen fotoğraflar

```text
Week-8/
  task-2/inputs/
    pose-1.jpg
    pose-2.jpg
    pose-3.jpg
  task-3/inputs/
    face-1.png
    face-2.png
    face-3.png
```

Bu altı dosya kullanıcı tarafından sağlanan ödev girdileridir. Downloads içindeki orijinallerden baytları değiştirilmeden kopyalandı; yeniden boyutlandırma, sıkıştırma, kırpma veya yeniden adlandırma yapılmadı. Altısının da kaynak/kopya SHA256 değerleri eşleşti. `inputs/` klasörleri Git ignore kapsamında değildir; indirilen geçici `samples/` dosyalarından ayrı olarak proje kaynaklarına dahil edilebilir. Bu işlem yalnız girdileri hazırlar; sınıflandırma kodu veya doğrulanmamış sonuç etiketi eklemez. Task 1'in betikleri ve mevcut komutları değiştirilmedi.

İlk üç demoya ait aşağıdaki kurulum ve sonuç kaydı korunmuştur. **22 araç için güncel komut/model/girdi/sonuç tablosu belgenin sonundadır.** Hazır ortamı yeniden kurmak yerine `source ./activate.sh` kullanın.

**Ekran kaydı:** İsteğe bağlı PNG çizimleri ve giriş/sonuç kartları eklendi. Bu bölümdeki eski doğrulama kayıtları kendi aşamalarına aittir; güncel kayıt komutları **“Task 1 ekran kaydı”** bölümündedir. Model, dönüşüm ve varsayılan JSON çıktı sözleşmesi korunur.

Branch `week8-mediapipe`, temiz/güncel main `a6978ef` üzerinden oluşturuldu. `git fetch origin main` sonrasında yerel/remote farkı 0/0 idi. Önceki haftaların proje dosyaları/sanal ortamları değiştirilmedi. Commit/push/merge yapılmadı.

## Doğrulanan ortam — 2026-11-16

- Ubuntu/WSL2 x86_64, glibc 2.43; mevcut tek Python **3.14.4**.
- **MediaPipe 1.2.3**, **NumPy 2.5.5**; gerçek import ve aşağıdaki gerçek inference'lar başarılı.
- OpenCV-contrib-python 5.0.0.93, Matplotlib 3.11.2, Pillow 13.0.0. Tüm 19 Python bağımlılığı `requirements.lock.txt` içinde sabittir; temel bağımlılıklar `requirements.txt` içindedir.
- Ayrı sanal ortam **Week-8/.venv**. Python sürümü değiştirilmedi, eski bir venv'e paket kurulmadı.
- CPU inference için native kütüphane yüklenirken gereken **libGLESv2.so.2** başlangıçta eksikti. Ubuntu'nun resmî **libgles2 1.7.0-3 / resolute/main amd64** paketi yalnız **Week-8/.native** içine çıkarıldı. Global apt kurulumu veya eski ortam değişikliği yapılmadı. `activate.sh`, bu yerel yolu LD_LIBRARY_PATH'e ekler.

## Dosyalar ve kapsam

```text
Week-8/
  .gitignore, .gitattributes
  requirements.txt, requirements.lock.txt
  activate.sh
  download_models.py
  README.md, PROMPTS.md
  task-1/
    pose_landmarker.py
    face_landmarker.py
    audio_transcriber.py
    ...                  # aşağıdaki tabloda listelenen 19 ek demo
    _common.py, prepare_assets.py, verify_demos.py
    assets.lock.json
  .venv/                # Git dışında
  .native/              # Git dışında yerel native kütüphane
  models/               # Git dışında model ağırlıkları
  samples/              # Git dışında indirilen konuşma klibi
  outputs/              # Korunan eski kurulum/inceleme kaynakları ve model önbellekleri
  task-1/output/        # Task 1 demo sonuçları, loglar ve yeni cache dosyaları
```

Fotoğraflar **Downloads konumundan doğrudan** okunur. Altı dosya da yerelde bulundu; kopyalanmadı, yeniden boyutlandırılmadı veya kaydedilerek değiştirilmedi. Önce/sonra SHA256 kontrolleri aynıydı. Üç CLI birbirine veya önceki haftalara runtime import/path bağımlılığı oluşturmaz.

## Resmî API kaynakları

- [Pose Landmarker Python](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker?tab=Python): IMAGE modu ve `detect`.
- [Face Landmarker Python](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker?tab=Python): IMAGE modu ve `detect`.
- [Audio Transcriber Python](https://developers.google.com/edge/mediapipe/solutions/audio/audio_transcriber/index#python): CPU, mono float32 örnekler ve tam klip için `transcribe(..., end_of_stream=True)`.
- [MediaPipe PyPI](https://pypi.org/project/mediapipe/1.2.3/): kullanılan Linux x86_64 paketi. Kurulu paketin gerçek options/transcribe imzaları ayrıca `inspect.signature` ile kontrol edildi.

### Resmî modeller ve beklenen yollar

| Araç | Yerel yol | Doğrulanan boyut |
| --- | --- | --- |
| Pose lite, float16 sürüm 1 | `models/pose_landmarker_lite.task` | 5.777.746 bayt |
| Face, float16 sürüm 1 | `models/face_landmarker.task` | 3.758.596 bayt |
| Parakeet TDT 0.6B v3, INT8 stateful | `models/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm` | 614.588.752 bayt |

İndirme bağlantıları:

- [Google Pose lite](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task), SHA256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
- [Google Face Landmarker](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task), SHA256 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`.
- [Google belgelerinin yönlendirdiği LiteRT community Parakeet modeli, sabit revision](https://huggingface.co/litert-community/parakeet-tdt-0.6b-v3/resolve/cd95f7bb97fd0757ab1bd6d5eff513cfcd7a2a10/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm), SHA256 `66c5a74cf6c2c1d2b990901f6cece5bb53e3214dbceafa0989900a6f0eeb3504`.

Audio modeli NVIDIA Parakeet TDT 0.6B v3 tabanlıdır; Google'ın model sayfasında CC-BY-4.0 atfıyla sunulur. Model dosya adını değiştirmeyin; otomatik model türü seçimi bunu kullanabilir. `download_models.py` hash kontrolü, geçici `.part` ve HTTP Range destekli devam etme kullanır; her çalıştırmada en fazla üç ağ denemesi yapar. Eksik/bozuk dosyada sahte sonuç üretmez. Mevcut dosyaları SHA doğrulamasıyla kullanır.

## Ubuntu/WSL kurulumu

PowerShell'den önce `wsl -d Ubuntu` ile geçin. Aşağıdaki komutlar **Ubuntu terminalinde** çalışır:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-8"
python3 --version
mkdir -p outputs models samples
python3 -m venv --without-pip .venv
curl -fL --retry 2 https://bootstrap.pypa.io/get-pip.py -o outputs/get-pip.py
.venv/bin/python outputs/get-pip.py
.venv/bin/python -m pip install -r requirements.lock.txt
```

Bu makinede `python3 -m venv .venv` ensurepip bulunmadığı için tamamlanmadı; PyPA'nın resmî get-pip bootstrap'ı **yalnız .venv içine** kullanıldı. Yukarıdaki `--without-pip` yöntemi bu gereksinimi açıkça karşılar. Aynı sürümleri yeniden kullanmak için Python 3.14.4 ortamıyla başlayın. Kurulum komutlarını, zaten hazır olan mevcut ortamda tekrar çalıştırmanız gerekmez.

Yerel native GLES bağımlılığı (bu makinede gereken çözüm; sistemde paket zaten varsa buna ihtiyaç olmayabilir):

```bash
mkdir -p outputs/native-packages .native
(
  cd outputs/native-packages
  apt download libgles2
  dpkg-deb -x libgles2_*.deb ../../.native
)
source ./activate.sh
```

Bu komut `apt install` yapmaz; indirilen resmî paketi proje içine çıkarır. `activate.sh` yalnız mevcut shell'in sanal ortamını ve native arama yolunu ayarlar; ~/.bashrc veya diğer venv'leri değiştirmez. Task 1, `_paths.py` üzerinden Matplotlib cache yolunu `task-1/output/matplotlib` olarak ayarlar; ortak activate.sh ve Task 2/3 davranışı korunur. Yeni terminalde **Week-8 içinde `source ./activate.sh`** kullanın.

Modeller ve kısa örnek ses:

```bash
python download_models.py pose face audio
curl -fL --retry 2 https://storage.googleapis.com/mediapipe-assets/speech_16000_hz_mono.wav \
  -o samples/speech_16000_hz_mono.wav
```

Ses kaynağı Google MediaPipe'ın yerel örnek WAV dosyasıdır; 16 kHz, mono, PCM16, 4,2725 saniye. Bu aşamada kullanıcının mikrofonundan kayıt yapılmadı. Audio indirmesi büyük olduğu için ağ zaman aşımı oluşursa `.part` korunur; aynı model indirme komutuyla devam edilebilir.

## İlk üç demo komutu (korundu)

Ubuntu'da **Week-8 içinde**, `source ./activate.sh` sonrasında:

```bash
python task-1/pose_landmarker.py "/mnt/c/Users/LENOVO/Downloads/pose-1.jpg"
python task-1/face_landmarker.py "/mnt/c/Users/LENOVO/Downloads/face-1.png"
python task-1/audio_transcriber.py samples/speech_16000_hz_mono.wav
```

İlk iki komutta dosya adını diğer verilen fotoğraflarla değiştirebilirsiniz. Model yolları script konumuna göre hesaplanır; istenirse `--model` ile açık yol verilir. Eksik giriş/model açık CLI hatası üretir.

`pose_landmarker.py` poz sayısını, landmark sayısını ve MediaPipe'ın omuz/dirsek/bilek koordinatları ile visibility/presence değerlerini yazar. `left_shoulder` vb. isimler API'nin anatomik landmark adlarıdır; kol hangi yönde/yukarıda sınıflandırması değildir. `face_landmarker.py` yüz sayısını ve 1/33/263/61/291 indekslerinin gerçek x/y/z değerlerini gösterir; baş yönü hesaplamaz.

Audio demosu sıkıştırılmamış 16 kHz mono PCM16 WAV'ı doğrular, gerçek signed PCM örneklerini float32 [-1,1] aralığına dönüştürür ve tam klibi MediaPipe'a verir. Bu basit demoda en fazla 30 saniye kabul edilir; başka örnekleme hızını yalnız başlık değiştirerek kabul etmez. Mikrofon/stream modu veya başka transkripsiyon servisi yoktur. Boş metin dönerse başarı diye sunulmaz.

## İlk üç demonun gerçek sonuçları — 2026-11-16

| Girdi | Gerçek sonuç |
| --- | --- |
| pose-1.jpg | 1 poz, 33 landmark |
| pose-2.jpg | 1 poz, 33 landmark |
| pose-3.jpg | 1 poz, 33 landmark |
| face-1.png | 1 yüz, 478 landmark |
| face-2.png | 1 yüz, 478 landmark |
| face-3.png | 1 yüz, 478 landmark |

Her sonuçta seçili gerçek koordinatlar JSON olarak yazdırıldı. Örneğin face-3.png landmark 1: x=0.5116988420, y=0.6147482395, z=-0.1121810377. Bunlar yön sınıfları değildir.

Audio Transcriber'ın gerçek çıktısı:

```text
Send a text to Mike, I'll be home late tomorrow.
```

Üç araç da gerçek yerel ağırlıklarla, verilen fotoğraflar/indirilen kısa WAV üzerinde çalıştı; mock veya alternatif servis kullanılmadı. Ayrıntılı koordinatlar, model SHA'ları, sürümler ve ses sonucu `task-1/output/validation.json` ve diğer outputs dosyalarındadır; üretilmiş çıktılar Git dışında tutulur. README/PROMPTS yalnız gerçek sonuçların çalışma kaydıdır.

Kurulum sırasında pip ve büyük audio indirmelerinde kesilme/zaman aşımı oldu. Paketler sınırlı paralel PyPI Range indirmeleriyle hazırlanıp 19 wheel'in SHA256'sı PyPI kayıtlarıyla kontrol edildi ve ardından offline kuruldu. Audio'nun tamamlanan kısmı korundu, kalan parçalar indirilip **tüm dosyanın** SHA256'sı sabit HF revision'ının LFS kaydıyla eşleştirildi. Eksik modelle inference başarısı iddia edilmedi.

İlk altı inference denemesi libGLESv2.so.2 eksikliğiyle başarısızdı; yerel native bağımlılık ve aktivasyon sonrasında altısı da gerçekten yeniden çalıştırılıp başarılı oldu. Kalan bir model/API hatası yoktur. Gereken koşullar: `.native` kütüphane yolu için `source ./activate.sh`, üç yerel model dosyası ve uygun WAV formatı. Tüm fotoğraf SHA'ları aynı kaldı. Website/API/Docker/Task2/Task3 sınıflandırması bu aşamada yapılmadı.

## Task 1'in 22 araca tamamlanması — 2026-11-16

Python **3.14.4 / MediaPipe 1.2.3** ortamı ve ilk üç betik değiştirilmedi. Yeni API'ler için Google'ın her aracın sayfasındaki **Python** örneği ile kurulu paketin gerçek options/metot/sonuç alanları birlikte incelendi. Tüm inference'lar CPU'da, gerçek ağırlıklarla ve yerel girdilerle yapıldı; aşağıdaki sonuçlar import veya mock testi değildir. TTS dosyası üretildi ve WAV yapısı incelendi; hoparlörde dinleme yapılmadı.

### Hazır ortamda modeller ve örnekler

**Ubuntu terminalinde**, mevcut Week-8 klasöründe:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-8"
source ./activate.sh
python task-1/prepare_assets.py
```

Bu yardımcı yalnız yeni 19 demo için gereken **18 farklı modeli** ve iki resmî görseli indirir (Semantic Retriever ve Universal Embedder aynı modeli paylaşır). İlk üç model için yukarıdaki `download_models.py` komutu geçerlidir. Yeni ağırlıklar **1.251.859.915 bayt (yaklaşık 1,25 GB)** yer kaplar; Laya tek başına yaklaşık 678 MB'dır. Modeller Git'e girmez. İndirme en fazla dört işçi kullanır; kesilen dosya `.part` olarak kalır, tekrar aynı komutla HTTP Range destekleniyorsa devam eder. Sonsuz retry yoktur. Belirli bir indirme için örneğin `python task-1/prepare_assets.py text_to_speech` kullanılabilir.

`task-1/assets.lock.json`, indirilen yeni modellerin ve görsellerin **tam resmî URL, yerel yol, boyut ve gerçekten ölçülen SHA256** kayıtlarını içerir. İndirme yardımcısı tamamlanan dosyanın SHA256'sını bu kayıtla kontrol eder. `latest`/HF `main` ileride değişirse uyuşmazlığı başarı diye kabul etmez; doğru resmî sürüm incelenmelidir. `--model` ile farklı bir dosya seçmek model/API uyumluluğunu garanti etmez. Google model kartlarında ve bağlantı verilen HF kartlarında belirtilen kullanım koşulları geçerlidir; özellikle 200M dil modellerinin Gemma koşullarını inceleyin.

Yeni örnekler:

- El/jest: [Google thumb_up.jpg](https://storage.googleapis.com/mediapipe-assets/thumb_up.jpg) → `samples/thumb_up.jpg`. Resmî MediaPipe örnek girdisi; ilk denenen `mediapipe-tasks/gesture_recognizer/thumb_up.jpg` URL'si 404 verdi, çalışan assets bağlantısı kullanıldı.
- Nesne/sınıflandırma: [Google cat_and_dog.jpg](https://storage.googleapis.com/mediapipe-tasks/object_detector/cat_and_dog.jpg) → `samples/cat_and_dog.jpg`. Google'ın Object Detector örneği.
- Diğer görseller verilen Downloads fotoğraflarıdır; orijinaller değiştirilmedi. Ses, yukarıda kaynaklandırılan 4,2725 saniyelik resmî WAV'dır.

### 22 aracın kısa komut ve sonuç listesi

Aşağıdaki komutlar **Ubuntu'da Week-8 içinden**, aktivasyon sonrasında çalışır. Önce fotoğraf yolunu tanımlayın:

```bash
PHOTO="/mnt/c/Users/LENOVO/Downloads"
```

Her satırın araç adı aynı zamanda resmî Google dokümanına bağlantıdır. Model sütunundaki adlar `models/` altındaki dosyalardır; tam indirme bağlantıları yeni modeller için `assets.lock.json`, ilk üçü için yukarıdaki kaynak listesindedir. Metin demosunun varsayılan metni betikte görünür; `--text "..."` ile değiştirilebilir. Tüm 22 satır **gerçek girdide doğrulandı**; engelli araç yoktur.

| Araç / betik | Ubuntu komutu | Model | Girdi ve videoda gösterilecek gerçek çıktı |
| --- | --- | --- | --- |
| [Language Detector](https://developers.google.com/edge/mediapipe/solutions/text/language_detector) — `language_detector.py` | `python task-1/language_detector.py` | `language_detector.tflite` | İngilizce kütüphane cümlesi → `en`, 0,99915 |
| [Text Classifier](https://developers.google.com/edge/mediapipe/solutions/text/text_classifier) — `text_classifier.py` | `python task-1/text_classifier.py` | `average_word_classifier.tflite` | “This movie was wonderful and I loved it.” → model etiketi `1`: 0,95913; `0`: 0,04087. Sentiment modeli; konu sınıflandırması değildir. |
| [Text Embedder](https://developers.google.com/edge/mediapipe/solutions/text/text_embedder) — `text_embedder.py` | `python task-1/text_embedder.py` | `universal_sentence_encoder.tflite` | İki kütüphane cümlesi → boyut 100, cosine 0,96342; vektörün tamamı yazılmaz. |
| [Text Proofreader](https://developers.google.com/edge/mediapipe/solutions/text/text_proofreader) — `text_proofreader.py` | `python task-1/text_proofreader.py` | `proofread_quant_200m.litertlm` | “Their are severel typos in this sentance.” → “There are several typos in this sentence.” |
| [Text Summarizer](https://developers.google.com/edge/mediapipe/solutions/text/text_summarizer) — `text_summarizer.py` | `python task-1/text_summarizer.py` | `summarization_quant_200m_2modes.litertlm` | Yeni okuma odası hakkındaki dört cümle → TLDR modunda gerçek, daha kısa özet. |
| [Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) — `pose_landmarker.py` | `python task-1/pose_landmarker.py "$PHOTO/pose-1.jpg"` | `pose_landmarker_lite.task` | 1 poz, 33 nokta; omuz/dirsek/bilek koordinatları. Eski betik korundu. |
| [Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker) — `face_landmarker.py` | `python task-1/face_landmarker.py "$PHOTO/face-1.png"` | `face_landmarker.task` | 1 yüz, 478 nokta; seçili indekslerin koordinatları. Eski betik korundu. |
| [Face Detector](https://developers.google.com/edge/mediapipe/solutions/vision/face_detector) — `face_detector.py` | `python task-1/face_detector.py "$PHOTO/face-3.png"` | `blaze_face_short_range.tflite` | 1 yüz kutusu; skor 0,94006, kutu x/y/w/h=69/77/141/141. Model kategori adı vermediği için `null` korunur. |
| [Gesture Recognizer](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer) — `gesture_recognizer.py` | `python task-1/gesture_recognizer.py samples/thumb_up.jpg` | `gesture_recognizer.task` | 1 el, `Thumb_Up`, 0,74360. |
| [Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) — `hand_landmarker.py` | `python task-1/hand_landmarker.py samples/thumb_up.jpg` | `hand_landmarker.task` | 1 `Right` el, 21 landmark; bilek yaklaşık (0,6388; 0,6713). |
| [Holistic Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker) — `holistic_landmarker.py` | `python task-1/holistic_landmarker.py "$PHOTO/pose-3.jpg"` | `holistic_landmarker.task` | Pose 33, face 478, sol el 21, sağ el 21 nokta. Özel kol/baş sınıfı yoktur. |
| [Image Classifier](https://developers.google.com/edge/mediapipe/solutions/vision/image_classifier) — `image_classifier.py` | `python task-1/image_classifier.py samples/cat_and_dog.jpg` | `efficientnet_lite0.tflite` (int8) | İlk üç gerçek ImageNet sonucu: `Cardigan` 0,01953; `wallaby` 0,01172; `Border terrier` 0,00781. Skorlar düşüktür; iki hayvanlı görselde doğru/emin sınıflandırma iddiası yoktur. |
| [Image Embedder](https://developers.google.com/edge/mediapipe/solutions/vision/image_embedder) — `image_embedder.py` | `python task-1/image_embedder.py "$PHOTO/face-1.png" --compare "$PHOTO/face-2.png"` | `mobilenet_v3_small.tflite` | İki farklı fotoğraf → boyut 1024, cosine 0,90741; kişi kimlik doğrulaması değildir. |
| [Image Segmenter](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter) — `image_segmenter.py` | `python task-1/image_segmenter.py "$PHOTO/pose-3.jpg"` | `selfie_segmenter.tflite` | Gerçek foreground confidence mask → `task-1/output/selfie-mask.png`, 264×408. PNG'yi açarak ön/arka planı gösterin. |
| [Interactive Segmenter](https://developers.google.com/edge/mediapipe/solutions/vision/interactive_segmenter) — `interactive_segmenter.py` | `python task-1/interactive_segmenter.py "$PHOTO/pose-3.jpg" --x 0.5 --y 0.45` | `interactive_segmentation.task` (Magic Touch v2) | Gövde üzerindeki normalize nokta → `task-1/output/interactive-mask.png`, 264×408; gerçek confidence aralığı 0–1. Arayüz gerekmez. |
| [Object Detector](https://developers.google.com/edge/mediapipe/solutions/vision/object_detector) — `object_detector.py` | `python task-1/object_detector.py samples/cat_and_dog.jpg` | `efficientdet_lite0.tflite` | `dog` 0,88672 ve `cat` 0,81641; iki gerçek bounding box. |
| [Audio Transcriber](https://developers.google.com/edge/mediapipe/solutions/audio/audio_transcriber) — `audio_transcriber.py` | `python task-1/audio_transcriber.py samples/speech_16000_hz_mono.wav` | `parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm` | “Send a text to Mike, I'll be home late tomorrow.” Eski betik korundu ve yeniden çalıştı. |
| [Audio Classifier](https://developers.google.com/edge/mediapipe/solutions/audio/audio_classifier) — `audio_classifier.py` | `python task-1/audio_classifier.py` | `yamnet.tflite` | Aynı kısa WAV → 5 pencere; ilkinde `Speech` 0,91797. Yalnız ilk pencerenin ilk iki etiketi gösterilir. |
| [Text to Speech](https://developers.google.com/edge/mediapipe/solutions/audio/text_to_speech) — `text_to_speech.py` | `python task-1/text_to_speech.py` | `phonon_int8.litertlm` (Phonon 31M en) | “Hello. Welcome to the library.” → `task-1/output/speech.wav`, mono PCM16, 24 kHz, 3,6 s. Dosyayı videoda kendiniz dinletebilirsiniz. |
| [Decision Maker](https://developers.google.com/edge/mediapipe/solutions/decision/decision_maker) — `decision_maker.py` | `python task-1/decision_maker.py` | `laya_s256.task` | Kitap arama isteği ve iki açık ölçüt → `library` 0,86805; `weather` 0,13195. Sonuç modelden gelir, kelime eşleştirme kuralı değildir. |
| [Semantic Retriever](https://developers.google.com/edge/mediapipe/solutions/retrieval/semantic_retriever) — `semantic_retriever.py` | `python task-1/semantic_retriever.py` | `embeddinggemma-2-text-270m.litertlm` | Üç kayıtlık bellek içi koleksiyon; “Where can I borrow books?” → `library`, skor 0,84573; boyut 768. Her çalıştırmada yeni koleksiyon. |
| [Universal Embedder](https://developers.google.com/edge/mediapipe/solutions/retrieval/universal_embedder) — `universal_embedder.py` | `python task-1/universal_embedder.py` | `embeddinggemma-2-text-270m.litertlm` | Text modality: iki kütüphane cümlesi → boyut 768, cosine 0,91557. Bu demo image/audio modality desteğini doğruladığını iddia etmez. |

Model skorları farklı araçlar arasında aynı anlamda değildir: cosine similarity, detection confidence ve decision probability ayrı kavramlardır. Yukarıdaki rakamlar ölçülen demo çıktılarıdır; tüm yeni girdiler için doğruluk garantisi değildir.

### Toplu gerçek doğrulama ve çıktıların kullanımı

```bash
source ./activate.sh
python task-1/verify_demos.py --photos "/mnt/c/Users/LENOVO/Downloads"
python -m pip check
```

Doğrulayıcı her aracı ayrı süreçte çalıştırır, **araç başına 180 saniye** sınırı koyar ve hata olsa bile diğer araçlara devam eder. Sonuç JSON'ları, native stderr logları ve süreler `task-1/output/task-1-verification/` altındadır. Eksik model/girdi veya boş tespitte başarı uydurmaz. Kısa terminal çıktıları videoya uygundur; `2>task-1/output/tool.stderr.log` ile native tanı loglarını terminalden ayırabilirsiniz.

Geliştirme sırasında çözülen gerçek sorunlar: LiteRT-LM cache dizinlerinin oluşturulmadan verilmesi yükleme hatası doğurdu; yeni helper dizini önce oluşturur. Maskelerde NumPy view kopyalanana kadar MediaPipe `Image` nesnesi canlı tutulmalıdır; geçici nesne üzerinden zincirlenen çağrı Interactive Segmenter'da geçersiz sayılar üretti. Son kod nesne referansını korur ve sonlu 0–1 confidence aralığını doğrular. Selfie modelinin category yolunda 0/255 değerleri görüldüğü için bunları sınıf ID'si varsayarak dönüştürmek yerine resmî confidence-mask çıktısı kullanılır. Tek kanallı H×W×1 çıktı PNG için H×W yapılır; maske yeniden çizilmez veya sahte olarak doldurulmaz.

Son toplu çalıştırmada **22/22 gerçek demo başarılı, 0 engelli**; `pip check`: **No broken requirements found**. İki PNG açılıp kişinin maskelendiği görsel olarak da kontrol edildi. WAV başlığı 24 kHz / mono / PCM16 / 86.400 frame ve peak=17.248 olarak doğrulandı; dinleme yapılmadı.

Eski üç kaynak, activate.sh, iki requirements dosyası ve altı orijinal fotoğraf için **12/12 önce/sonra SHA256 aynı**. Sanal ortam, `.native`, modeller, indirilen örnekler ve üretilmiş PNG/WAV/cache/logların mevcut `.gitignore` ile Git dışında kaldığı `git check-ignore` ile doğrulandı. Model dosyaları indirilmeden yalnız kaynak kopyası çalışmaz; yukarıdaki hazırlık komutları gereklidir. `git diff --check` hata vermedi; Week-8 mevcut durumda untracked olduğu için yeni Python dosyaları ayrıca AST/satır sonu boşluk kontrolünden geçirildi. Git'in kullanıcıya ait global ignore yoluna erişim uyarısı yerel ignore kontrolünün başarı sonucundan ayrı tutuldu.

## Task 1 ekran kaydı

Yeni seçenekler yalnız sunum içindir: Vision için `--output` çizimli PNG, segmenter'larda mevcut `--output` ham maske ve yeni `--overlay` renkli bindirme, diğer araçlarda `--report` giriş/gerçek sonuç kartı üretir. **Seçenekler verilmezse eski JSON çıktısı aynı kalır.** Inference her komutta bir kez yapılır; görüntü ve kart aynı gerçek sonuçtan hazırlanır. Embedding vektörleri yazdırılmaz. Dosya yazmak dışında pencere veya ses oynatma başlatılmaz.

Çizim yaklaşımı Google'ın [Pose Python Sample code](https://colab.research.google.com/github/google-ai-edge/mediapipe-samples/blob/main/examples/pose_landmarker/python/%5BMediaPipe_Python_Tasks%5D_Pose_Landmarker.ipynb) ve [Face Python Sample code](https://colab.research.google.com/github/google-ai-edge/mediapipe-samples/blob/main/examples/face_landmarker/python/%5BMediaPipe_Python_Tasks%5D_Face_Landmarker.ipynb) örnekleri incelenerek uyarlandı. Kurulu 1.2.3'te `mp.tasks.vision.drawing_utils`, `drawing_styles` ve resmî bağlantı listeleri kullanılır; eski `mp.solutions`/protobuf yüzeyi varsayılmaz. Notebook'un pencere gösterme çağrıları alınmadı. Face için tessellation, kontur ve iris bağlantıları; Pose için görünürlük kontrollerini kullanan vücut noktaları/bağlantıları çizilir. RGB/BGR dönüşümü açık yapılır, fotoğraf aynalanmaz.

### Pose ve Face — kopyalanabilir tam Ubuntu komutları

Mevcut modeller/ortam hazırken **Ubuntu/WSL terminalinde**:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-8"
source ./activate.sh
mkdir -p task-1/output/recording

python task-1/pose_landmarker.py "/mnt/c/Users/LENOVO/Downloads/pose-1.jpg" \
  --output task-1/output/recording/pose_landmarker.png

python task-1/face_landmarker.py "/mnt/c/Users/LENOVO/Downloads/face-1.png" \
  --output task-1/output/recording/face_landmarker.png
```

**Windows PowerShell'de**, repo klasöründe:

```powershell
Invoke-Item .\Week-8\task-1\output\recording\pose_landmarker.png
Invoke-Item .\Week-8\task-1\output\recording\face_landmarker.png
```

PNG'ler Windows'taki mevcut repo altında bulunur:
`C:\Users\LENOVO\OneDrive\Masaüstü\EE 471 Soft-Tech\Hafta 1\EE471\Week-8\task-1\output\recording\`.
Windows Fotoğraflar uygulamasında gerekirse yakınlaştırın; asıl fotoğrafın çözünürlüğü korunur.

### Her araç için kayıt komutu ve Windows'ta açılacak dosya

**Ubuntu'da Week-8 içinde**, `source ./activate.sh` ardından:

```bash
PHOTO="/mnt/c/Users/LENOVO/Downloads"
```

Tablodaki tüm PNG dosyaları yukarıdaki **task-1/output/recording/** klasöründedir. Her satır gerçek girdiyi ve mevcut gerçek sonucu gösterir; hiçbir sınıf/skor yeniden hesaplanmaz veya tahmin edilmez.

| Araç | Ubuntu kayıt komutu | Windows'ta açılacak PNG / ek çıktı |
| --- | --- | --- |
| Pose Landmarker | `python task-1/pose_landmarker.py "$PHOTO/pose-1.jpg" --output task-1/output/recording/pose_landmarker.png` | `pose_landmarker.png`: orijinal kopyası üzerinde vücut noktaları/bağlantılar |
| Face Landmarker | `python task-1/face_landmarker.py "$PHOTO/face-1.png" --output task-1/output/recording/face_landmarker.png` | `face_landmarker.png`: yüz ağı/konturlar/iris |
| Hand Landmarker | `python task-1/hand_landmarker.py samples/thumb_up.jpg --output task-1/output/recording/hand_landmarker.png` | `hand_landmarker.png`: el noktaları/bağlantılar |
| Holistic Landmarker | `python task-1/holistic_landmarker.py "$PHOTO/pose-3.jpg" --output task-1/output/recording/holistic_landmarker.png` | `holistic_landmarker.png`: pose, face, iki el |
| Face Detector | `python task-1/face_detector.py "$PHOTO/face-3.png" --output task-1/output/recording/face_detector.png` | `face_detector.png`: yüz kutusu ve gerçek skor |
| Object Detector | `python task-1/object_detector.py samples/cat_and_dog.jpg --output task-1/output/recording/object_detector.png` | `object_detector.png`: sınıf/skor/kutu |
| Gesture Recognizer | `python task-1/gesture_recognizer.py samples/thumb_up.jpg --output task-1/output/recording/gesture_recognizer.png` | `gesture_recognizer.png`: el bağlantıları ve Thumb_Up/skor |
| Image Classifier | `python task-1/image_classifier.py samples/cat_and_dog.jpg --output task-1/output/recording/image_classifier.png` | `image_classifier.png`: fotoğraf ve top-3 paneli; düşük skorlar aynen görünür |
| Image Embedder | `python task-1/image_embedder.py "$PHOTO/face-1.png" --compare "$PHOTO/face-2.png" --output task-1/output/recording/image_embedder.png` | `image_embedder.png`: iki fotoğraf, gerçek cosine ve boyut |
| Image Segmenter | `python task-1/image_segmenter.py "$PHOTO/pose-3.jpg" --overlay task-1/output/recording/image_segmenter.png` | `image_segmenter.png`: renkli bindirme; ham maske `task-1/output/selfie-mask.png` olarak korunur |
| Interactive Segmenter | `python task-1/interactive_segmenter.py "$PHOTO/pose-3.jpg" --x 0.5 --y 0.45 --overlay task-1/output/recording/interactive_segmenter.png` | `interactive_segmenter.png`: bindirme ve sarı seçili nokta; ham maske `task-1/output/interactive-mask.png` |
| Language Detector | `python task-1/language_detector.py --report task-1/output/recording/language_detector.png` | `language_detector.png`: girdi cümlesi ve dil/olasılık |
| Text Classifier | `python task-1/text_classifier.py --report task-1/output/recording/text_classifier.png` | `text_classifier.png`: cümle ve sentiment etiketleri/skorları |
| Text Embedder | `python task-1/text_embedder.py --report task-1/output/recording/text_embedder.png` | `text_embedder.png`: iki cümle, boyut/cosine |
| Text Proofreader | `python task-1/text_proofreader.py --report task-1/output/recording/text_proofreader.png` | `text_proofreader.png`: hatalı cümle ve modelin düzeltmesi |
| Text Summarizer | `python task-1/text_summarizer.py --report task-1/output/recording/text_summarizer.png` | `text_summarizer.png`: özgün metin ve gerçek TLDR özeti |
| Audio Transcriber | `python task-1/audio_transcriber.py samples/speech_16000_hz_mono.wav --report task-1/output/recording/audio_transcriber.png` | `audio_transcriber.png`: kullanılan WAV ve gerçek transkript |
| Audio Classifier | `python task-1/audio_classifier.py --report task-1/output/recording/audio_classifier.png` | `audio_classifier.png`: WAV, hız/süre ve ilk pencerenin gerçek ses etiketleri |
| Text to Speech | `python task-1/text_to_speech.py --report task-1/output/recording/text_to_speech.png` | `text_to_speech.png`: girdi ve üretilen WAV bilgisi; ses `task-1/output/speech.wav` |
| Decision Maker | `python task-1/decision_maker.py --report task-1/output/recording/decision_maker.png` | `decision_maker.png`: girdi, açık kriterler ve model kararı/olasılıklar |
| Semantic Retriever | `python task-1/semantic_retriever.py --report task-1/output/recording/semantic_retriever.png` | `semantic_retriever.png`: sorgu, üç kayıt ve gerçek en iyi eşleşme |
| Universal Embedder | `python task-1/universal_embedder.py --report task-1/output/recording/universal_embedder.png` | `universal_embedder.png`: iki metin, modality, boyut/cosine |

TTS sesi otomatik çalınmaz. İsterseniz **Windows PowerShell** üzerinden yalnız üretilen sesi açın:

```powershell
Invoke-Item .\Week-8\task-1\output\speech.wav
```

### Toplu hazırlık ve kontrol

```bash
# Ubuntu / Week-8
source ./activate.sh
python task-1/verify_demos.py --recording
python task-1/verify_demos.py
python -m unittest discover -s task-1 -p test_presentation.py -v
python -m pip check
```

`--recording` bütün 22 PNG'yi üretir; gerçek model komutları, süreler ve çıktı kontrolleri `task-1/output/task-1-recording-verification/` altına yazılır. Varsayılan doğrulama yine `task-1/output/task-1-verification/` kullanır. Görsel PNG'lerinin yanındaki `.png.json` dosyaları kaynak fotoğraf SHA256/konum/boyut ve çizilen gerçek sonuç bilgisini tutar. Böylece boş dosya, yanlış konum/yön, değişen kaynak ve çizim eksikliği kontrol edilir. Karşılaştırma/sınıflandırma panellerindeki fotoğraf pikselleri birebir korunur; diğerlerinde yalnız çizim/bindirme alanları değişir.

PNG/WAV ve tanı dosyaları yalnız Git dışında kalan **task-1/output/** altında tutulur. Sunum çıktılarında dışarı çıkan yol veya PNG yerine farklı uzantı reddedilir; mevcut WAV/maske çıktıları da task-1/output içinde olmalıdır. Eski `Week-8/outputs/` yolu Task 1 çıktı doğrulayıcıları tarafından kabul edilmez. Orijinal girdilerin üzerine yazılmaz. Pillow/OpenCV zaten mevcut ortamın bağımlılıklarıdır; yeni paket kurulmadı. `cv2.imshow`, WSLg veya başka GUI servisi gerekmez. Ekran görüntüsü için Windows'tan dosyayı açmak yeterlidir.

Son gerçek kayıt hazırlığı kontrolü:

- **22/22** varsayılan CLI inference ve **22/22** kayıt modu inference/PNG kontrolü başarılı.
- Değişiklik öncesi, yeni varsayılan ve yeni kayıt modu **22 aracın JSON içeriklerinin tamamında eşleşti**. Özel `--output`/`--report` seçenekleri stdout'a ek alan/metin basmaz.
- **4/4** sunum regresyon testi başarılı; `pip check`: **No broken requirements found**.
- Pose/Face ayrı açıldı, 11 Vision çıktısı iki önizleme sayfasında kontrol edildi; seçili metin/ses/retrieval kartları da ayrı açıldı. Tüm 22 PNG ayrıca programatik kontrol edildi. WAV hâlâ mono PCM16, 24 kHz, 86.400 frame (3,6 s); ses oynatılmadı.
- Altı orijinal fotoğraf, activate.sh ve iki requirements dosyası SHA256 kontrolünden değişmeden geçti. Task 2/3'ün altı girdi kopyası da orijinalleriyle aynı kaldı. Kaynak AST/son boşluk kontrolü ve `git diff --check` başarılı; PNG/WAV yollarının ignore edildiği doğrulandı. Kontrol özeti `task-1/output/recording/final-checks.json` içindedir.

## Çıktı temizliği ve tek Task 1 çıktı klasörü — 20 Kasım 2026

- Kod/README incelemesiyle Task 1'in eski ortak `Week-8/outputs/` konumu, Task 2'nin `task-2/outputs/` ve Task 3'ün `task-3/outputs/` konumları doğrulandı. Task 2/3 kaynakları, çıktı argümanları ve çalışma şekilleri değiştirilmedi.
- **241** eski üretilmiş dosya (PNG, ham maske, WAV, JSON sonuçları ve demo tanı logları) silinmeden önce depo dışına taşındı; yedek SHA256'ları kontrol edildi. Task 2 ve Task 3'te üçer üretilmiş PNG de bu kapsamdadır.
- Yedek: `C:\Users\LENOVO\AppData\Local\Temp\EE471-Week8-output-backup-20261120-ce99447b`. `before-cleanup/` eski sonuçları, `manifest-before.json` dosya listesi/boyut/hash kayıtlarını içerir. Doğrulama sırasında üretilen **6** dosya da `validation-generated/` altına taşındı; `manifest-validation.json` ve doğrulama raporları aynı yedektedir. Bu geçici yedeğin saklama süresi Windows geçici dosya temizliğine bağlıdır.
- Yeni `_paths.py` Task 1 için tek `OUTPUT` sabiti tanımlar. Varsayılan WAV/maske yolları, PNG/rapor doğrulayıcıları, SDK cache dizinleri, Matplotlib cache'i, model hazırlama raporu, testler ve toplu demo logları bu kökü kullanır. Eski ortak `outputs/` yolu Task 1 dosya doğrulayıcılarında reddedilir. Yeni bytecode üretimi Task 1 sürecinde kapalıdır. Model ve örnek girdi yolları değişmedi.
- Gerçek doğrulama: Pose-1 ile yeni konumda **267×397 çizimli PNG** üretildi, açılıp kontrol edildi. TTS varsayılanı yeni konuma **24 kHz / mono / PCM16 / 86.400 frame / 3,6 s WAV** yazdı; PCM tepe değeri 17.248. Bir TTS kayıt kartı da üretildi. Ses oynatılmadı. **5/5** ilgili dosya/yol testi geçti. Bu temizlik adımında tüm 22 araç yeniden çalıştırılmadı; önceki 22/22 kayıtları önceki aşamalara aittir.
- Doğrulama çıktıları ve yeni font cache dosyası da yedeğe taşındı. Son durumda `task-1/output/` (içindeki `recording/` dahil), `task-2/outputs/` ve `task-3/outputs/` altında **0 dosya** vardır. Yeniden çıktı almak için yukarıdaki komutları çalıştırın.
- Eski `Week-8/outputs/` klasörü kurulum dosyaları, tarihsel yardımcı kaynak kodlar, indirilen resmî dokümanlar ve model ağırlık önbellekleriyle karışıktı; topluca silinmedi. Korunan bu içerikler demo sonucu değildir; eski inceleme yardımcıları güncel demo komutlarının yerine kullanılmaz. Gerçek model dosyaları, örnek sesler, girdi fotoğrafları, sanal ortam ve Docker imajlarına dokunulmadı. Korunan modeller/girdiler/Task 2-3 dosyaları ile ortak ortam dosyalarının **57/57 SHA256** kontrolü geçti. Model indirme, Docker build, commit/push/merge yapılmadı.
