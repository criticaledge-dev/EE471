# Week 8 — İstem ve gerçek çalışma kaydı

Bu belge bu projenin kullanıcı istemini ve gerçekten yapılan kurulum/doğrulama sonuçlarını kaydeder. Önceki haftaların geçmişi yeni çalışma geçmişi olarak kopyalanmadı. Tam bir ham sohbet transkripti olduğu iddia edilmez.

## Aşama 1 — Tam kullanıcı istemi

Kopyalanan metindeki satır sonu/HTML boşluk kaçışları okunabilirlik için düzenlendi.

EE471 Week 8 — Aşama 1: MediaPipe kurulumu ve ilk üç Python demosu.

Önce mevcut Git durumunu kontrol et. Çalışma alanı uygunsa güncel main'den
week8-mediapipe branch'ini oluştur; varsa mevcut branch'i inceleyerek devam et.
Kullanıcının değişikliklerini koru. Yalnızca Week-8 altında proje dosyası ekle.
Commit, push veya merge yapma.

1. Python ortamı
- Ubuntu/WSL'de mevcut Python sürümlerini kontrol et. MediaPipe ile uyumlu
  bir sürüm seç ve Week-8 için ayrı bir sanal ortam kullan.
- Google'ın resmî Python belgelerindeki API'leri kullan. İlk amaç,
  paketin import edilmesi ve aşağıdaki üç aracın gerçek girdiyle çalışması.
- Çalıştığını doğruladığın paket sürümlerini kaydet. Model dosyalarının
  resmî indirme bağlantılarını ve beklenen yerel yollarını README'ye yaz.
- Sanal ortamı, indirilen model ağırlıklarını ve üretilen çıktıları
  .gitignore ile dışarıda tut. Önceki haftaların ortamını değiştirme.

2. Week-8/task-1 altında üç kısa, bağımsız Python demosu oluştur
- pose_landmarker.py: Tek bir pose JPG al. Tespit edilen poz sayısını ve
  omuz/dirsek/bilek gibi birkaç landmark'ı yazdır. Henüz left/right/both
  etiketi üretme; burada MediaPipe'ın kendi çıktısını gösteriyoruz.
- face_landmarker.py: Tek bir face PNG al. Tespit edilen yüz sayısını ve
  birkaç yüz landmark'ını yazdır. Henüz baş yönü sınıflandırması yapma.
- audio_transcriber.py: Resmî Python örneğiyle uyumlu, kısa bir yerel
  konuşma klibini al ve gerçek transkripti yazdır. Mikrofon veya
  canlı yayın akışı ekleme. Gerçek inference çalışmazsa hata nedenini
  bildir; sahte transkript ya da başka servisin çıktısını kullanma.

Verilen fotoğraflar yerel Codex ortamında bulunuyorsa örnek olarak kullan.
Bulunmuyorsa hangi dosyayı nereye koymam gerektiğini bildir. Ödev
fotoğraflarını değiştirme.

3. Bana kısa bir sonuç raporu ver
- Kullanılan Python ve MediaPipe sürümü.
- Hangi demoların gerçek modelle çalıştığı ve ne döndürdüğü.
- Ubuntu'dan çalıştırabileceğim üç komut.
- Kalan kurulum veya model sorunları.

Task 1 için website, Postman, HTTP API, Docker veya arayüz ekleme.
Task 2 ve Task 3'ün sınıflandırma kurallarını bu aşamada yazma.

## Gerçek geliştirme sonuçları — 2026-11-16

- Repo/ancestor AGENTS.md kontrolünde uygulanabilir talimat dosyası bulunmadı. Başlangıç branch'i main, çalışma ağacı temiz, son commit a6978ef idi. `git fetch origin main` sonrasında main/origin-main farkı 0/0; week8-mediapipe yoktu ve buradan oluşturuldu. Kullanıcı değişikliği silinmedi/taşınmadı. Proje dosyaları yalnız Week-8 içinde yazıldı; commit/push/merge yapılmadı.
- PDF yerelde okundu. Ödev Task 1'de daha fazla araç, Task 2'de kol ve Task 3'te baş yönü sınıflandırması istediği görüldü; belge içindeki geniş kapsam kullanıcı istemi yerine geçmedi. Bu aşamada yalnız belirtilen üç bağımsız Python demosu yapıldı.
- Altı fotoğraf Downloads altında bulundu: pose-1/2/3.jpg ve face-1/2/3.png. Girişler doğrudan okundu; fotoğraf dosyaları değiştirilmedi. Çalışma öncesi/sonrası altı SHA256 eşleşti. Kaynaklar veya fotoğraflar diğer proje klasörlerine kopyalanmadı.
- Ubuntu/WSL'de yalnız Python3.14.4 vardı. Güncel MediaPipe1.2.3 Linux x86_64 py3 wheel'i/PyPI metadata'sı incelendi. Ayrı Week-8/.venv oluşturuldu. İlk normal venv girişimi ensurepip eksikliğiyle yarım kaldı; resmî PyPA get-pip yalnız bu venv içinde kullanıldı. Eski haftaların ortamlarına paket kurulmadı.
- İlk pip download'u bağlantı kesilmeleriyle yavaştı. 19 wheel PyPI'den sınırlı dört paralel Range bağlantısıyla alındı; tüm dosya SHA256'ları PyPI kayıtlarıyla doğrulandı. Yalnız bu Week-8 venv pip indirme süreci durdurulup doğrulanmış yerel wheel'lerle offline kurulum yapıldı. Paketler global Python'a kurulmadı.
- Doğrulanan ana sürümler: Python3.14.4, MediaPipe1.2.3, NumPy2.5.5, OpenCV-contrib-python5.0.0.93, Matplotlib3.11.2, Pillow13.0.0; tam 19 paket requirements.lock.txt içinde. Import başarılı oldu. Kurulu paketin Pose/Face options ve AudioTranscriberOptions/transcribe imzaları inspect.signature ile doğrudan incelendi; cache_dir/end_of_stream alanlarının varlığı doğrulandı. Resmî Google Python belgelerindeki Tasks API'leri kullanıldı; eski solutions API'si veya başka konuşma servisi eklenmedi.
- Model indirmeleri resmî Google Storage pose/face v1 bağlantılarından ve Google Audio Transcriber belgelerinin yönlendirdiği LiteRT-community Parakeet modelinden yapıldı. Audio ana dosya adı korundu. Büyük audio indirmesi yaklaşık294MB'da, sonra yaklaşık368MB'da zaman aşımına uğradı; tamamlanan prefix korundu, kalan veri sınırlı dört paralel Range bağlantısıyla tamamlandı. Bütün 614.588.752 baytlık dosyanın SHA256'sı HF sabit revision cd95f7bb97fd0757ab1bd6d5eff513cfcd7a2a10 LFS kaydıyla eşleşti. Eksik model tam sayılmadı. Reusable download_models.py bu revision/hash'e sabitlendi ve mevcut dosyaları doğrular; geçici dosyalar Git dışındadır.
- Pose lite: 5.777.746 bayt, SHA256 59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a. Face: 3.758.596 bayt, SHA256 64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff. Parakeet: SHA256 66c5a74cf6c2c1d2b990901f6cece5bb53e3214dbceafa0989900a6f0eeb3504. README'de kaynak linkleri ve models altındaki beklenen yollar yazıldı.
- İlk gerçek altı görsel inference'ı OSError: libGLESv2.so.2 eksikliğiyle başarısızdı. Bu import başarısı inference başarısı gibi sunulmadı. Ubuntu resolute/main amd64 libgles2_1.7.0-3 paketi apt download ile alınıp yalnız Week-8/.native içine dpkg-deb ile çıkarıldı. Sistem genelinde apt install yapılmadı. Proje LD_LIBRARY_PATH'iyle altı inference gerçekten tekrar çalıştırıldı.

| Gerçek girdi | Tespit | Landmark sayısı |
| --- | --- | --- |
| pose-1.jpg | 1 poz | 33 |
| pose-2.jpg | 1 poz | 33 |
| pose-3.jpg | 1 poz | 33 |
| face-1.png | 1 yüz | 478 |
| face-2.png | 1 yüz | 478 |
| face-3.png | 1 yüz | 478 |

- Pose demosu altı anatomik omuz/dirsek/bilek noktasının x/y/z/visibility/presence değerlerini, face demosu beş gerçek indeksin x/y/z değerlerini JSON olarak yazdırdı. İsimlerde left/right geçmesi MediaPipe'ın anatomik landmark adıdır; kol hangi yönde/yukarıda veya baş yönü sınıflandırması yapılmadı. Örneğin face-3 landmark1 x0.5116988420/y0.6147482395/z-0.1121810377 idi.
- Audio girişi Google MediaPipe assets/speech_16000_hz_mono.wav: gerçek yerel dosya, mono/PCM16/16kHz, 4.2725s. WAV örnekleri float32[-1,1]'e dönüştürüldü; BaseOptions CPU, sample_rate_hz16000 ve transcribe(end_of_stream=True) kullanıldı. Native cache çıktısı Week-8/outputs/audio-cache altında. Mikrofon, canlı akış, sahte metin veya başka API yoktur.

Gerçek MediaPipe transkripti:

```text
Send a text to Mike, I'll be home late tomorrow.
```

- İlk activation smoke denemesinde yarım kalan venv kurulumunun bin/activate oluşturmadığı görüldü. Mevcut venv üzerinde `python3 -m venv --without-pip` ile aktivasyon dosyasını tamamlama denemesi **otomatik izin incelemesi tarafından**, kurulu paketlere zarar verme riski gerekçesiyle reddedildi; komut çalıştırılmadı ve ret dolaylı yoldan aşılmadı. Daha güvenli alternatif olarak yalnız yeni activate.sh değiştirildi: mevcut shell'de VIRTUAL_ENV/PATH/native kütüphane yolu ayarlanır, venv dosyalarına dokunulmaz. Sonra bu helper üzerinden README'deki üç gerçek komut tekrar başarıyla çalıştı; pip check: No broken requirements found.
- Ağ metadatası/uzak wheel kaynak yüzeyi incelemesinde bazı web cache-miss/timeout sonuçları ve WSL shell kaçış hataları oldu. Bunlar çalışan SDK yüzeyi kanıtı sayılmadı; son doğrulama kurulu paketin gerçek imzaları ve gerçek inference üzerinden yapıldı. Başarısız denemelerde sonuç uydurulmadı.
- Üretilen koordinat/transkript/cache/log/model/venv/native paket/indirme çıktıları .gitignore ile dışarıda; ayrıntılı gerçek kayıt outputs/validation.json içinde. Paket lock'u, kurulum helper'ı ve README/PROMPTS kaynak olarak tutulur. Kalan model veya inference hatası yoktur; yeni terminalde Week-8 içinde source ./activate.sh gerekir. Website/Postman/HTTP API/Docker/Task2/Task3 sınıflandırması eklenmedi.

## Task 1'in 22 araca tamamlanması — kullanıcı istemi

Aşağıdaki metin bu geliştirme adımının istemidir; önceki üç demo kaydı yukarıda korunmuştur.

> EE471 Week 8 — Önce yalnızca Task 1'i tamamla.
>
> week8-mediapipe branch'inde devam et. Mevcut Week-8/README.md, activate.sh, Python 3.14.4 / MediaPipe 1.2.3 ortamı ve çalışan üç betiği incele: pose_landmarker.py, face_landmarker.py, audio_transcriber.py. Bunların çalışma davranışını koru.
>
> Yalnızca Week-8/task-1, gerekli örnek girdiler ve Week-8'in ortak dokümantasyon/ignore dosyalarında çalış. Task 2 ve Task 3'e geçme. Website, Postman, HTTP API, Docker veya canlı kamera arayüzü ekleme. Commit, push ve merge yapma.
>
> Kalan 19 kısa Python demosunu şu gruplarla tamamla:
>
> 1. Text — language_detector, text_classifier, text_embedder, text_proofreader, text_summarizer.
> 2. Vision — face_detector, gesture_recognizer, hand_landmarker, holistic_landmarker, image_classifier, image_embedder, image_segmenter, interactive_segmenter, object_detector.
> 3. Audio — audio_classifier, text_to_speech.
> 4. Decision ve Retrieval — decision_maker, semantic_retriever, universal_embedder.
>
> Her araç için:
> - Google'ın resmî MediaPipe Python örneğini ve uyumlu modelini kullan. Özellikle TTS, Proofreader, Summarizer, Decision Maker ve Retrieval araçlarında mevcut paketteki API ile model uyumunu erkenden kontrol et.
> - Kısa bir komutla çalışabilen, araç adıyla eşleşen bir .py betiği yaz. Mümkünse tek metin, kısa WAV veya tek görselle gerçek inference yap. Embedder demosunda uzun vektörün tamamı yerine boyutu ve kısa bir benzerlik örneğini göster. Semantic Retriever'da küçük bir örnek koleksiyonundan sorguya en iyi eşleşen kaydı göster.
> - Terminal çıktısını videoda kolay okunacak kadar kısa tut. Segmenter için yerel PNG maske, TTS için dinlenebilir yerel WAV üret. Interactive Segmenter'da arayüz yerine seçilecek noktayı CLI argümanı olarak al veya örnek görsel için belgelediğin bir nokta kullan.
> - Mevcut örnek görselleri uygun oldukları yerlerde yeniden kullan. El veya nesne tespiti için uygun girdi yoksa resmî ya da kullanımına izin verilen bir örnek seç ve kaynağını README'ye yaz.
> - Her demoyu gerçek modelle çalıştır. Bir demo takılırsa diğerlerine devam et; sonunda hata nedenini ve gereken adımı bildir. Import başarısını veya modelin hiç tespit yapmadığı uygunsuz örneği tamamlanmış demo sayma. Sahte çıktı kullanma.
>
> README'ye 22 aracın her biri için betiği, Ubuntu'da çalıştırma komutunu, kullanılan modeli, örnek girdiyi ve videoda gösterilecek çıktıyı yaz. Sanal ortamı, indirilen ağırlıkları ve üretilen çıktıları Git dışında tut.
>
> Son raporda 22 aracı listele: gerçek girdide doğrulandı / engelli. Doğrulanan her araç için kısa sonuç, engelli her araç için gerçek nedeni ve çözüm adımını bildir. Mevcut üç demoyu da yeniden kontrol et.

### Gerçek geliştirme ve doğrulama sonuçları — 2026-11-16

- Başlangıç branch'i `week8-mediapipe`; durum `?? Week-8/`. Kullanıcının mevcut Week-8 çalışması korundu. Repo/üst dizinlerde uygulanabilir AGENTS.md bulunmadı. Git yazma işlemi yapılmadı; diğer haftaların dosyaları değiştirilmedi.
- Mevcut Python 3.14.4 / MediaPipe 1.2.3 ortamındaki 19 yeni sınıfın options/metot imzaları ve Python kaynak yüzeyi incelendi. Google'ın 19 araç sayfasındaki Python örnekleri/model bağlantıları indirilen dokümanlardan kontrol edildi. Eski API'lerin körlemesine kopyası kullanılmadı: Interactive Segmenter 1.2.3'te Magic Touch v2, `set_image`, `Stroke`, `StrokePoint` ve `segment(strokes)` kullanır; eski ROI örneği değildir.
- İlk üç betik, activate.sh, requirements.txt ve requirements.lock.txt hiç değiştirilmedi. Son SHA256 kontrolü bu altı kaynak ve altı orijinal fotoğraf için **12/12 aynı** sonucu verdi. Paket kurulumu/sürüm değişikliği yapılmadı. Önceki haftanın Windows Python'u yalnız stdlib dosya/hash kontrolü için `-B` ile kullanıldı; o ortama paket/dosya yazılmadı. Gerçek inference'ların tamamı Week-8'in WSL venv'inde çalıştı.
- 19 adlandırılmış betik, `_common.py`, `prepare_assets.py`, `verify_demos.py` ve `assets.lock.json` eklendi. Yeni 18 farklı resmî model (1.251.859.915 bayt) indirildi; Retrieval araçları ortak text-270M modelini kullanır. HF modelleri Google sayfalarının verdiği LiteRT-community bağlantılarıdır. TTS için GPU örneği yerine resmî listedeki CPU'da gerçekten çalışan Phonon 31M kullanıldı. Decision Maker Laya s256 ile gerçekten çalıştı. Proofreader ve Summarizer 200M modelleri uyumlu çıktı.
- Yeni el örneği için ilk `mediapipe-tasks/gesture_recognizer/thumb_up.jpg` adresi **404** verdi. Çalışan resmî `mediapipe-assets/thumb_up.jpg` kullanıldı. İkinci girdi resmî `mediapipe-tasks/object_detector/cat_and_dog.jpg`; ikisinin tam kaynağı, boyutu ve SHA256'sı lock dosyasında. Orijinal ödev fotoğrafları yeniden kaydedilmedi.
- İlk LM denemeleri `Cache directory does not exist or is not writable` ile başarısızdı. Yeni helper cache dizinini önce oluşturacak şekilde düzeltildi ve ilgili gerçek inference'lar yeniden başarıyla yapıldı. Bu ara hatalar son başarı gibi raporlanmadı.
- Selfie maskesinin H×W×1 NumPy görünümü PIL'de TypeError verdi; gerçek tek kanal H×W olarak kaydedildi. Geçici MediaPipe Image üzerinden zincirleme `.numpy_view().copy()` Interactive Segmenter'da 1,34e34 gibi geçersiz değer üretti. Image nesnesinin referansı kopya tamamlanana kadar korundu; son aralık gerçek 0–1. Selfie category yolunda 0/255 değerleri görüldü; bunlar 0/1 kategori varsayımıyla çarpılmadı. Bunun yerine modelin resmî float foreground confidence-mask çıktısı kullanıldı. Son kod sonlu değer/aralık ve gerçek ön/arka plan ayrımını doğrular; maskeyi uydurmaz.
- PowerShell üzerinden boşluklu yolu içeren bir `bash -c` denemesi shell quoting nedeniyle `cd .../EE: No such file or directory` verdi. Aynı komut, yolu dosya konumundan çözen ignored shell helper ile çalıştırıldı. Bu yol hatası MediaPipe inference hatası olarak raporlanmadı.
- Son toplu kontrol **22/22 gerçek demo başarılı, 0 engelli**. Her araç ayrı süreçte en fazla 180 saniye sınırıyla çalıştırıldı. Sonuç/süre/komut ve native stderr dosyaları `outputs/task-1-verification/` altında, Git dışında. `pip check`: **No broken requirements found**. Kaynak AST/son boşluk kontrolü başarılı; `git diff --check` hata vermedi. Week-8 untracked olduğu için diff kontrolü tek başına yeni dosyaların doğrulaması sayılmadı.

| Gerçek girdide doğrulanan araç | Gerçek kısa sonuç |
| --- | --- |
| language_detector | en, 0,99915 |
| text_classifier | model etiketi 1: 0,95913; 0: 0,04087 |
| text_embedder | 100 boyut; cosine 0,96342 |
| text_proofreader | There are several typos in this sentence. |
| text_summarizer | Okuma odası metninin TLDR özeti üretildi; çıktı JSON'da. |
| pose_landmarker | pose-1: 1 poz, 33 nokta; eski betik yeniden çalıştı. |
| face_landmarker | face-1: 1 yüz, 478 nokta; eski betik yeniden çalıştı. |
| face_detector | face-3: 1 yüz, 0,94006 |
| gesture_recognizer | Thumb_Up, 0,74360 |
| hand_landmarker | 1 Right el, 21 nokta |
| holistic_landmarker | Pose 33, face 478, her iki elde 21'er nokta |
| image_classifier | Cardigan 0,01953; wallaby 0,01172; Border terrier 0,00781. Düşük güven; doğru sınıf garantisi veya özel kedi ırkı modeli iddiası yok. |
| image_embedder | 1024 boyut; cosine 0,90741 |
| image_segmenter | 264×408 gerçek confidence PNG; 0–1 |
| interactive_segmenter | (0,5;0,45) noktası, 264×408 confidence PNG; 0–1 |
| object_detector | dog 0,88672; cat 0,81641; gerçek kutular |
| audio_transcriber | Send a text to Mike, I'll be home late tomorrow. |
| audio_classifier | 5 pencere; ilkinde Speech 0,91797 |
| text_to_speech | 24 kHz, mono PCM16, 3,6 saniye gerçek WAV |
| decision_maker | library 0,86805; weather 0,13195 |
| semantic_retriever | Üç kayıt arasında library, 0,84573; 768 boyut |
| universal_embedder | Text modality 768 boyut; cosine 0,91557 |

- İki maske yerel image viewer ile açılıp fotoğraftaki insanın ayrıldığı görüldü. WAV başlığı **mono/PCM16/24.000 Hz/86.400 frame**, peak PCM16=17.248 olarak doğrulandı. Dosya gerçekten üretildi; hoparlörde dinleme yapılmadı. Universal Embedder için yalnız text modality denenmiştir; image/audio modality doğrulaması eklenmedi.
- `git check-ignore`: .venv, .native, model, sample, output ve __pycache__ yolları dışarıda. Mevcut ignore kuralları yeterli olduğu için değiştirilmedi. Git, kullanıcı global ignore dosyasına erişim uyarısı verdi; yerel proje ignore kontrolleri başarılıydı. .env okunmadı. Website/API/Postman/Docker/kamera/Task2/Task3 eklenmedi; commit/push/merge yapılmadı.
- Son sürüm `prepare_assets.py` mevcut indirmeler üzerinde tekrar çalıştırıldı: **20/20 asset** (18 model + 2 görsel) boyut ve lock SHA256 kontrolünü geçti; 404 kalan bağlantı yok. Modeller/örnekler uygulama kaynağı olarak Git'e eklenmedi.

## Task 2 ve Task 3 girdi fotoğraflarının projeye eklenmesi

Kullanıcı istemi:

> Bu gönderdiğim fotoğraflar task2 ve task3te kullanılacak olan fotoğraflardır. Bunları projeye eklemeni istiyorum doğru şekilde.

Verilen dosyalar: pose-1.jpg, pose-2.jpg, pose-3.jpg, face-1.png, face-2.png, face-3.png; kaynakları kullanıcının Downloads klasörüdür.

Gerçek sonuç: `week8-mediapipe` üzerinde üç pose JPG `Week-8/task-2/inputs/`, üç face PNG `Week-8/task-3/inputs/` altına orijinal dosya adlarıyla kopyalandı. Kaynak ve kopya SHA256 karşılaştırmaları **6/6 eşleşti**. Dosyalar değiştirilmedi; orijinaller korundu. Altı hedef dosyanın ignore edilmediği kontrol edildi. Task 1 kodu/ortamı değiştirilmedi; Task 2/3 uygulaması veya sınıflandırma etiketi eklenmedi. Yalnız dosya kopyalama ve hash/Git ignore kontrolleri yapıldı; yeni inference testi çalıştırılmadı. Git add/commit/push/merge yapılmadı.

## Task 1 — ekran kaydı hazırlığı

### Kullanıcı istemi

> Week 8 Task 1 — Çalışan 22 Python demosunu ekran kaydına hazırla.
>
> Mevcut Week-8/task-1 betiklerini, verify_demos.py ve README'yi incele. 22 aracın mevcut gerçek inference davranışı ve varsayılan CLI çıktıları korunsun. Yalnızca Task 1 üzerinde çalış; Task 2 ve 3'e geçme.
>
> 1. Önce Pose Landmarker ve Face Landmarker ile başla. Resmî Google MediaPipe Python Sample code örneklerindeki çizim yaklaşımını incele. Mevcut betiklere isteğe bağlı --output ekle. Pose için vücut noktalarını ve bağlantılarını, Face için yüz hatlarını orijinal fotoğrafın kopyası üzerine çiz. pose-1.jpg ve face-1.png ile gerçek PNG çıktısı üret ve açıp kontrol et.
>
> 2. Aynı düzeni diğer Vision demolarına uygula:
> - Hand/Holistic: landmark ve bağlantılar.
> - Face/Object Detector: kutu ve skor; nesne için sınıf adı.
> - Gesture Recognizer: el noktaları ve hareket etiketi/skoru.
> - Image Classifier: görsel ve küçük top-3 paneli; düşük skoru gizleme.
> - Image Embedder: iki görsel ve gerçek benzerlik skoru.
> - Segmenter'lar: mevcut maskeyi koru, ayrıca fotoğraf üzerine renkli maske bindir. Interactive Segmenter'ın seçilen noktasını göster.
> Görseli aynalama veya orijinal dosyanın üzerine yazma. Çizimleri modelin gerçek sonucundan üret.
>
> 3. Diğer demoları da kayıt için okunur hale getir:
> - Audio: kullanılan WAV, ses etiketi/transkript veya üretilen WAV açıkça belli olsun. Ses oynatmayı otomatik başlatma.
> - Text, Decision ve Retrieval: örnek girdiyi ve kısa, gerçek sonucu birlikte göster. Uzun embedding dizilerini ekrana dökme.
>
> 4. Üretilen PNG/WAV dosyalarını Git dışında kalan outputs/ altında tut. Python çıktıyı dosyaya kaydetsin; cv2.imshow, WSLg, website, Postman, HTTP API veya Docker gerektirmesin. README'ye her araç için kayıt komutunu ve Windows'ta açılacak çıktıyı yaz. Özellikle Pose ve Face için kopyalanabilir tam komutları ver.
>
> 5. Mevcut 22 demo doğrulamasını yeniden çalıştır. Yeni görsel çıktıların boş olmadığını ve doğru fotoğrafın üzerinde çizildiğini kontrol et. Sonuçta çalışan komutları ve oluşturulan dosya yollarını bildir. Commit/push/merge yapma.

### Yapılan değişiklikler ve gerçek kontroller

- Branch `week8-mediapipe`; başlangıçta Week-8 untracked idi. Çalışma yalnız Task 1 ve ortak README/PROMPTS ile Git dışında kalan çıktı kayıtlarında yapıldı. Task 2/3 koduna, fotoğraflarına veya diğer haftalara dokunulmadı. Model, dönüşüm, cihaz, dil modeli ayarları ve bağımlılık sürümleri değiştirilmedi.
- Önce Google'ın güncel Pose/Face sayfalarının **Sample code** bağlantıları incelendi. İlk sade notebook dosya adları 404 verdi; sayfaların gösterdiği `[MediaPipe_Python_Tasks]_Pose_Landmarker.ipynb` ve `[MediaPipe_Python_Tasks]_Face_Landmarker.ipynb` indirildi ve çizim hücreleri okundu. Kurulu 1.2.3 paketindeki gerçek `drawing_utils`, `drawing_styles`, Pose/Face/Hand bağlantı sınıfları incelendi. `mp.solutions` veya varlığı doğrulanmamış protobuf/metot kullanılmadı.
- Önce Pose ve Face'e yalnız isteğe bağlı `--output` eklendi. pose-1.jpg ve face-1.png ile gerçek PNG üretildi, iki dosya ayrı ayrı açılıp kontrol edildi. Resmî drawing_utils/styles ile pose noktaları/bağlantıları; face tessellation, kontur ve iris bağlantıları çizildi. Fotoğraf boyutu/yönü korunur; RGB/BGR açık dönüştürülür.
- Diğer Vision araçlarında aynı gerçek sonuç nesnesinden çizimler üretildi. Sınıflandırma ve benzerlik panelleri orijinal pikselleri korur; top-3 düşük skorları filtrelemez. Segmenter'ların eski ham maske yolları korunur; `--overlay` ek renklendirilmiş PNG üretir. Interactive Segmenter normalize seçili noktayı sarı olarak işaretler.
- Text/Decision/Retrieval ve Audio araçlarına isteğe bağlı `--report` eklendi: girdi metni/koleksiyon/ölçütler veya kullanılan WAV ile gerçek sonuç aynı PNG kartında görünür. Mevcut JSON sözleşmesine alan eklenmedi; kart ikinci inference çalıştırmaz. Uzun embedding dizileri yoktur. TTS dosyası üretilir, ses otomatik oynatılmaz.
- Ortak `_presentation.py` yalnız dosyaya çizim/kayıt yapar. Tüm sunum PNG'leri `outputs/recording/<araç_adı>.png`, gerçek WAV `outputs/speech.wav`; ham maskeler `outputs/selfie-mask.png` ve `outputs/interactive-mask.png`. Sunum PNG'leri yanında kaynak SHA/boyut/konum ve gerçek çizim verilerini içeren `.png.json` kayıtları vardır. Yeni çıktı yolları outputs dışına çıkamaz; orijinal girdi üzerine yazma reddedilir.
- `verify_demos.py --recording` 22 aracı gerçek modellerle yeniden çalıştırır ve PNG biçimi, boş olmaması, doğru kaynak SHA/boyut/konumu, fotoğraf pikselleri ve gerçek çizim varlığını kontrol eder. Kaynak fotoğraf üzerinde çizim yapılması ile kartlarda fotoğrafın aynen korunması ayrı kontrol edilir. Varsayılan doğrulama ayrı klasörde ve eski argümanlarla çalışır.
- Dört dosya tabanlı regresyon testi başarılı: dışarı taşan/yanlış uzantılı çıktı yolu reddi; rapor yokken payload nesnesinin aynen kalması; panelde orijinal piksel/yön/renk ve düşük skorların korunması; raporda gerçek giriş/sonuç eşleşmesi. Bunlar ML doğrulaması olarak sunulmadı; gerçek modeller ayrıca çalıştırıldı.
- Kayıt modunda **22/22** gerçek inference ve **22/22** PNG kontrolü başarılı. Vision PNG'lerinin tamamı iki önizleme sayfasında açılarak incelendi; Pose/Face ayrıca orijinal boyutlarında, Audio Transcriber, Semantic Retriever, Summarizer, TTS ve Decision kartları da ayrı açıldı. Modelden gelmeyen koordinat, sınıf, skor veya transkript eklenmedi. Hoparlörde dinleme yapılmadı.
- README'ye 22 kayıt komutu ve Windows'ta açılacak dosyalar, Pose/Face için tam kopyalanabilir Ubuntu/PowerShell komutları eklendi. Ekran hazırlığı için yeni paket, pencere/WSLg, servis veya arayüz kurulmadı. Eski üç kaynak için daha önceki aşamalarda verilen “değişmedi” kayıtları o aşamalara aittir; bu adımda isteğe bağlı sunum bayrakları bilinçli olarak eklendi.
- Son varsayılan yeniden çalıştırma da **22/22** başarılı; önceki JSON / yeni varsayılan JSON / kayıt modu JSON karşılaştırması **22/22 aynı içerik, sıfır fark**. `pip check`: **No broken requirements found**. WAV mono PCM16/24 kHz/86.400 frame olarak yeniden doğrulandı. Dokuz korunan ortam/orijinal dosyası (activate.sh, iki requirements ve altı fotoğraf) ve Task 2/3'ün altı fotoğraf kopyası hash kontrolünü geçti. Kaynak AST/son boşluk kontrolleri başarılı. Son özet `outputs/recording/final-checks.json`; commit/push/merge yapılmadı.

## 20 Kasım 2026 — çıktı temizliği ve Task 1 output düzeni

### İstem özeti

Yalnız Week-8 kapsamında Git durumu ve AGENTS talimatları kontrol edilecek. Task 1/2/3'ün gerçek çıktı klasörleri kod ve README'den doğrulanacak; yalnız üretilmiş demo sonuçları depo dışında geçici bir klasöre taşınarak temizlenecek. Girdiler, modeller, kaynaklar, ortam ve Docker imajları korunacak. Task 1'in yeni çıktıları tam olarak `Week-8/task-1/output/`, kayıt PNG'leri `output/recording/` altında olacak; varsayılanlar, doğrulayıcılar, toplu demo, README ve ignore kuralı güncellenecek. Task 2/3 yolları değişmeyecek. En az bir gerçek görsel ve ses çıktısıyla kontrol yapılacak; kontrol dosyaları da kaldırılarak çıktı klasörleri boş bırakılacak. Model indirme, Docker build veya commit/push/merge yapılmayacak.

### Gerçek sonuçlar

- Branch `week8-mediapipe`, Git durumu `?? Week-8/`; uygulanabilir AGENTS.md bulunmadı. Mevcut kullanıcı dosyaları korundu.
- Kod ve README ile eski Task 1 ortak çıktıları `Week-8/outputs/`, Task 2/3 çıktıları kendi `outputs/` klasörleri olarak doğrulandı. Ortak klasördeki kurulum dosyaları, kaynak yardımcılar, indirilmiş dokümanlar ve model önbellekleri demo çıktısı olarak seçilmedi; yerinde korundu.
- Seçilmiş **241 eski dosya**, kaynak/kopya SHA256 kontrolüyle `C:\Users\LENOVO\AppData\Local\Temp\EE471-Week8-output-backup-20261120-ce99447b\before-cleanup\` altına taşındı. Yedek manifesti `manifest-before.json`. Altı Task 2/3 çıktı PNG'si dahil; kaynaklar ve girdiler taşınmadı.
- Task 1 `_paths.py` ile ortak çıktı kökü, çalışma cache'i ve Matplotlib konumu tanımlandı; Task 1 yeni bytecode üretimi kapatıldı. Varsayılan WAV/maskeler, sunum ve ortak çıktı doğrulayıcıları, prepare_assets raporu, verify_demos log/kayıt dizinleri, ilgili testler, README komutları ve `/task-1/output/` ignore kuralı güncellendi. Model/örnek girdi dizinleri değişmedi; activate.sh ve Task 2/3 kaynakları değişmedi.
- **5/5** dosya/yol testi başarılı. Gerçek Pose-1 inference yeni dizine 267×397 PNG yazdı; dosya açılıp çizim/fotoğraf eşleşmesi kontrol edildi. Gerçek Phonon TTS varsayılan olarak yeni köke 24 kHz, mono PCM16, 86.400 frame (3,6 saniye), peak=17.248 WAV yazdı. TTS PNG kartı da doğrulandı. Ses oynatılmadı. Eski ortak WAV yolu yeniden oluşmadı.
- Doğrulamanın **6** dosyası (PNG, yan JSON'lar, WAV ve font cache) aynı yedekte `validation-generated/` altına taşındı; dosya/hash manifesti `manifest-validation.json`. Doğrulama raporu ve test logları da depo dışındaki yedektedir. Son Task 1 output/recording, Task 2 outputs ve Task 3 outputs dosya sayıları sıfırdır.
- Korunan model/girdi/Task 2-3/ortak ortam dosyalarının **57/57 SHA256** kontrolü başarılı. Bu adımda tüm 22 inference tekrar çalıştırılmadı; önceki 22/22 sonuçları tarihsel kayıttır. Model indirme, Docker işlemi, .env okuma, git add/commit/push/merge yapılmadı.
