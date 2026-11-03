# EE471 Week 6 — Docker uygulamaları

Task 2, mevcut CPU Cog sınıflandırıcısı ve ayrı bir Flask website container'ından oluşur. Tarayıcı görseli website'e yükler; website doğruladıktan sonra aynı görseli Cog'a JSON/data URL ile gönderir. Task 1 Speech Studio ve sesli hesap makinesi kopyaları `task-1/` altındadır; kurulumu bu belgenin **Task 1** bölümündedir. İki görev ayrı Compose projeleri ve portları kullanır. PDF daha geniş teslim kapsamını anlatır; bu aşamanın kapsamını kullanıcının isteği belirler.

## Güncel çalıştırma — Compose

PowerShell'de Docker Desktop açıkken Ubuntu'ya geçin:

```powershell
wsl -d Ubuntu
```

Sonraki build/Compose komutları **Ubuntu WSL terminalindedir**:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-6/task-2"
cd classifier
cog build -t ee471-week6-classifier --progress plain --use-cog-base-image=false
cd ..
bash start.sh
docker compose ps
```

Önce Cog image'ı, sonra website build edilir. Mevcut model image'ı hazırsa Cog build'i tekrarlamak gerekmez. `start.sh` eksik model image'ında açık talimatla durur; registry'den çekmez. Website image'ını build eder ve `docker compose up -d --no-build --pull never --wait --wait-timeout 120` çalıştırır. Aynı işlemler elle:

```bash
docker image inspect ee471-week6-classifier:latest
# Yukarıdaki komut başarısızsa önce classifier klasöründe cog build çalıştırın.
docker compose build website
docker compose up -d --no-build --pull never --wait --wait-timeout 120
```

- Website: **http://localhost:5063**
- Cog: **http://localhost:5064**; tahmin yolu `/predictions`.
- İki port da `127.0.0.1` host arayüzüne bağlıdır.
- Website içinden `COG_URL=http://classifier:5000` kullanılır. Container içindeki `localhost`, diğer servisi göstermez.
- İki servis Compose'un `ee471-week6-task2` ağı üzerindedir. Classifier mevcut `ee471-week6-classifier:latest` image'ını kullanır; ikinci model Dockerfile'ı yoktur. `pull_policy: never` iki servis için de tanımlıdır.
- Cog sağlık kontrolü gerçek `/health-check` endpoint'inde `READY` bekler. Website `/healthz` kendi HTTP erişimini kontrol eder; Cog için startup bağımlılığı `service_healthy` kullanılır.
- Website gunicorn ile container içinde `0.0.0.0:5000` dinler ve root olmayan kullanıcıyla çalışır. Python 3.12.9; Flask 3.1.2, requests 2.32.5, Pillow 11.1.0, gunicorn 23.0.0 sabittir. `.env` gerekmez veya yüklenmez.

Port çakışması varsa önce `docker ps --format 'table {{.Names}}\t{{.Ports}}'` ile sahibini bulun. Yalnız bu çalışmanın eski `ee471-week6-classifier-demo` container'ı 5064'ü kullanıyorsa onu `docker stop` ve `docker rm` ile kaldırın; başka proje container'larını durdurmayın. Bu aşamanın başlangıcında çalışan/eski doğrulama container'ı yoktu.

Durdurma/yeniden açma (**Ubuntu**, `task-2` içinde):

```bash
docker compose stop
docker compose start --wait
# Container ve bu projenin ağını kaldırmak için:
docker compose down
```

`down` image'ları silmez. Model logu classifier container dosya sistemindedir; `down` ile container silindiğinde log silinir. Yeniden `bash start.sh` ile açabilirsiniz. Diğer projeler etkilenmez.

## Website kullanımı ve sınırlar

JPEG veya PNG seçin, önizlemeyi kontrol edin ve **Classify** düğmesine basın. En yüksek sınıf ve üç sınıfın skorları yüzde olarak gösterilir. Diğer görseller kedi sınıfına zorlanmaz; modelin gerçek ImageNet sınıfları aynen korunur.

- Dosya en fazla **5 MiB**, görsel en fazla **12.000.000 piksel** ve her kenar en fazla **6000 piksel** olabilir. Multipart istek üst sınırı dosya sınırı + 64 KiB'dir.
- Sunucu Pillow ile gerçek formatı, yapıyı ve piksel verisini kontrol eder; uzantı/MIME'a güvenmez. Kullanıcı dosya adı sunucu yolu yapılmaz; görsel bellekte işlenir. GIF ve bozuk/truncated görseller reddedilir.
- Tarayıcı `POST /api/classify` multipart `image` gönderir. Website, Cog'a `POST /predictions` **JSON** `{"input":{"image":"data:image/jpeg;base64,..."}}` gönderir; Cog'a multipart gitmez.
- Cog'un gerçek yanıtı `id`, `logs`, `metrics`, `output`, `status` alanlarını içerir; başarısızlıkta `error` gelebilir. Website yalnız `status: succeeded` ve üç geçerli 0–1 skorunu kabul eder. HTTP 200 içindeki `failed` başarı değildir. Ham Cog hata/log alanları istemciye aktarılmaz.
- Eksik/bozuk görsel 400; büyük yükleme 413; bağlantı/hazır değil/busy 503; timeout 504; model/geçersiz yanıt 502 döner. Hata mesajları ayrı gösterilir. Connect/read timeout 3/60 saniye, Cog yanıt üst sınırı 64 KiB; otomatik retry yoktur.
- Yeni dosya seçiminde eski sonuç ve önizleme temizlenir; eski object URL serbest bırakılır. İşlem sırasında tekrar gönderim engellenir. Sayfadan ayrılırken istek iptal edilir ve preview URL temizlenir. Tarayıcı isteğini iptal etmek, başlamış model tahminini sunucuda geri alma garantisi vermez.
- Görsel/base64 loglanmaz. Website bağımlılıkları model bağımlılıklarını değiştirmez.

## Container içinden canlı log gösterimi

**Ubuntu**, `task-2` içinde:

```bash
docker compose exec classifier sh
```

Artık **classifier container shell'i** içindesiniz:

```sh
tail -f /var/log/ee471/classifier.log
```

Tarayıcıda yeni bir Classify işlemi yapın; gerçek `Prediction completed ... top3=...` satırı görünür. `Ctrl+C` ile tail'den, `exit` ile shell'den çıkın. Yeni satırlar bir sonraki tahminde gelir; örnek/sahte log üretilmez. Modelin rotasyonlu log ayrıntıları aşağıdadır.

## Postman — doğrudan Cog doğrulaması

Collection: `task-2/postman/classifier.postman_collection.json`. İstek doğrudan `http://localhost:5064/predictions` adresine gider; website'e gitmez.

**Ubuntu**, `task-2` içinde (yalnız Python standart kütüphanesi gerekir):

```bash
python3 postman/make_request.py classifier/test-data/input.jpg
```

Kendi JPEG/PNG dosyanız için dosyanın tırnaklı WSL yolunu verin. Alternatif **PowerShell** komutları:

```powershell
Set-Location 'C:\Users\LENOVO\OneDrive\Masaüstü\EE 471 Soft-Tech\Hafta 1\EE471\Week-6\task-2'
py -3 postman\make_request.py 'C:\resimler\ornek.jpg'
```

`py` yoksa Ubuntu komutunu kullanın. Yardımcı dosyanın boyut/signature kontrolünü yapar; tam görsel doğrulayıcı değildir. Şu iki yerel dosyayı üretir, base64'ü terminale yazdırmaz:

- `outputs/postman-request.json`: `input.image` data URL'sini içeren JSON gövdesi.
- `outputs/postman-environment.json`: aynı JSON'u `prediction_body` değişkeninde tutan içe aktarılabilir Postman environment.

**Windows Postman uygulamasında:**

1. Collection JSON'unu ve üretilen environment JSON'unu **Import** ile açın.
2. Environment listesinden **EE471 Week 6 - local image (do not share)** seçin.
3. **Classify local JPEG or PNG** isteğini açın. URL `{{cog_url}}/predictions`, header `Content-Type: application/json`, raw body `{{prediction_body}}` olsun.
4. **Send** düğmesine basın. Test Results'ta HTTP 200, `status: succeeded` ve üç gerçek skor kontrollerini görün. Yanıt gövdesini ve canlı container logunu gösterin.
5. Environment kullanmak istemezseniz **Body → binary → Select File** ile **postman-request.json** seçebilirsiniz; Content-Type yine `application/json` olmalıdır. Burada dosya bir JSON gövdesidir; doğrudan JPEG/binary veya multipart gönderilmez.

Postman pre-request script'i yerel dosyayı keyfî okumaz; hazırlanmış environment değişkenini kontrol eder. Üretilen JSON/environment görsel içeriği taşır: paylaşmayın, Git'e eklemeyin. `outputs/`, `test-data/` ve üretilen dosya adları `.gitignore` ile dışlanır. Website build context'i de yalnız runtime kaynaklarını alır.

**Postman uygulaması bu geliştirme sırasında kullanılmadı.** Aynı yardımcıdan çıkan JSON gövdesi Python ile gerçek Cog'a gönderilip doğrulandı; bu, Postman uygulamasında yapılmış test olarak sunulmaz. Kullanıcıya kalan işlem import, environment seçimi, Send ve Test Results kontrolüdür.

## Bu aşamanın gerçek doğrulaması

2026-11-03:

- Website image'ı gerçekten build edildi; mevcut model image'ı, sürümleri ve ağırlık stratejisi değiştirilmedi. Compose ile iki servis başlatıldı.
- **14 Python testi** ağsız website container'ında mock Cog yanıtlarıyla geçti: upload/format/dosya-piksel sınırları, PNG/JPEG, HTTP 200/failed, bozuk şema/skorlar, busy, timeout/bağlantı ve tekrar kullanım. Bunlar gerçek model kanıtı değildir.
- Ayrı gerçek HTTP testinde website upload sonucu doğrudan Cog sonucuyla tam eşleşti. Model logundaki tamamlanan tahmin sayısı website isteğiyle bir arttı; logda base64 yoktu.
- Gerçek eksik/bozuk/büyük upload kontrolleri geçti. Yalnız bu Compose projesinin classifier'ı durdurularak website'in 503 bağlantı hatası verdiği doğrulandı; classifier tekrar açıldı ve tahmin başarılı oldu.
- **Gerçek Chrome headless + gerçek website + gerçek Cog** kontrolünde üç form gönderimi yapıldı: geçerli görsel, bozuk görsel ve geçerli görselle toparlanma. Önizleme, tüm yüzde skorlarının doğrudan Cog ile eşleşmesi, çift gönderim engeli, eski sonucu temizleme, iki preview URL'sinin serbest bırakılması, eksik dosya backend hatası ve 375 piksel görünümde taşmama kontrol edildi. JavaScript error/unhandledrejection yoktu. İnsan tarafından yapılmış görsel tarayıcı değerlendirmesi iddia edilmez.
- Postman helper gerçek örnek görseli dönüştürdü; üretilen request ve environment aynı JSON'u içeriyordu. JSON ile doğrudan Cog HTTP 200 / succeeded alındı. Gerçek Postman uygulamasıyla doğrulama kullanıcıya kaldı.
- Başlangıç testinde eksik Cog status alanının yanlışlıkla tamamlanmamış tahmin sayılması yakalandı; geçersiz yanıt olarak düzeltildi. Test upload kaynaklarını temizlerken iki geçici test-yardımcısı hatası oluştu (EnvironBuilder context-manager desteği ve gerçek WSGI input'un yeri); finally/closing kullanılarak düzeltildi. Son 14 test ve gerçek stack kontrolü başarılı, uyarısız tamamlandı.
- Son durumda **classifier ve website Compose servisleri çalışır durumda** bırakıldı. Headless Chrome kapatıldı. Gerçek `.env` okunmadı; başka proje değişikliği, Git stage/commit/push/merge veya registry push yapılmadı.

Testleri yeniden çalıştırmak için (**Ubuntu**, `task-2` içinde, servisler açıkken):

```bash
python3 tests/check_stack.py
```

Bu test yalnız kendi classifier servisini kısa süre durdurup yeniden açar; demo kaydı sırasında çalıştırmayın. Modelin resmi örnek görseli `classifier/test-data/input.jpg` yoksa aşağıdaki indirme komutuyla hazırlayın. Gerçek tarayıcı testi **Windows PowerShell**'de repo kökünden Node.js 22 ve Chrome ile:

```powershell
node Week-6/task-2/tests/check_browser.mjs
```

## Task-2-demo.avi için kısa sıra

1. Ubuntu'da `cog --version`, classifier build ve `bash start.sh` komutlarını, ardından `docker compose ps` çıktısını gösterin. Cache kullanılırsa bunu açıkça söyleyin.
2. Tarayıcıda `http://localhost:5063` açın; JPEG/PNG seçin, önizlemeyi ve Classify sonrası gerçek ilk üç yüzdeyi gösterin. Genel ImageNet sınıflandırıcısı olduğunu belirtin.
3. Başka terminalde `docker compose exec classifier sh` → `tail -f /var/log/ee471/classifier.log` açın. Web sitesinden yeni tahmin yaptırıp yeni log satırını gösterin.
4. Hazırlanmış collection/environment'i Postman'a import edin; doğrudan 5064'e JSON/data URL isteği gönderin. `succeeded`, üç skor ve test sonuçlarını gösterin. Base64'ün tamamını ekranda gezdirmeye gerek yoktur.
5. Bozuk dosya hatasını ve ardından geçerli görselle tekrar kullanımı gösterin. Sonunda `docker compose stop` ile yalnız bu servisleri durdurun.

## Model ve sürümler

| Bileşen | Sabit sürüm |
| --- | --- |
| Cog CLI / container SDK | 0.23.1 |
| Container Python | 3.12.9 |
| torch | 2.6.0+cpu |
| torchvision | 0.21.0+cpu |
| Pillow | 11.1.0 |

`Runner(BaseRunner).setup()` gerçek ResNet50 `IMAGENET1K_V1` ağırlıklarını bir kez CPU'ya yükler ve `eval()` uygular. `run()` görseli RGB'ye çevirir; ağırlığın kendi `transforms()` ve `meta["categories"]` bilgilerini kullanır. `torch.inference_mode()` içinde softmax sonrası en yüksek üç sınıfı `{sınıf: skor}` olarak döndürür. Skorlar 0–1 aralığındadır; yalnızca ilk üç gösterildiği için toplamları 1 olmak zorunda değildir. Bozuk görsele açık hata verir.

Bu 1000 sınıflı genel ImageNet modelidir; tüm kedi ırklarını ayıran özel veya yeniden eğitilmiş bir model değildir.

Sürüm kaynakları: [Cog başlangıç](https://github.com/replicate/cog/blob/v0.23.1/docs/getting-started.md), [Python](https://github.com/replicate/cog/blob/v0.23.1/docs/python.md), [YAML](https://github.com/replicate/cog/blob/v0.23.1/docs/yaml.md). Bu üç dosyanın **v0.23.1** içerikleri okunmuştur. torch/torchvision eşleşmesi ve CPU index'i [resmi PyTorch sürüm tablosuyla](https://pytorch.org/get-started/previous-versions/#v260) karşılaştırılmıştır. Gereksiz torchaudio/CUDA eklenmemiştir. Ana bağımlılıklar sabittir; tüm transitif paketler için ayrı lock dosyası yoktur.

## Terminal ve çalışma dizini

PowerShell — Docker Desktop açıkken Ubuntu'ya geçin:

```powershell
wsl -d Ubuntu
```

Aşağıdaki komutların tamamı **Ubuntu WSL terminalinde** çalışır. Windows/OneDrive yolu boşluk ve Türkçe karakter içerdiği için tırnaklar önemlidir:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-6/task-2/classifier"
uname -m
cog --version
docker version
cog build --help
cog run --help
```

Ubuntu içine ikinci Docker Engine kurmayın; Docker Desktop'ın WSL entegrasyonunu kullanın. `.env` veya API anahtarı gerekmez.

## Build ve ağırlık stratejisi

```bash
cog build -t ee471-week6-classifier --progress plain --use-cog-base-image=false
```

`gpu: false`, CPU wheel sürümleri ve Python slim tabanı kullanılır. `sdk_version` container SDK'sını da 0.23.1'e sabitler. `--use-cog-base-image=false` ile `--use-cuda-base-image=false` birlikte verilemez; CLI bunu reddeder. Yukarıdaki tek seçenekli komutu kullanın.

`build.run` model ağırlığını `/opt/ee471/torch/hub/checkpoints/resnet50-0676ba61.pth` yoluna indirir. torchvision indirme sırasında ağırlığın URL'deki hash önekini kontrol eder. Kaynak kod build.run sırasında bulunmadığından komut kendi kısa Python kodunu içerir; ayrı kaynak yardımcısına bağımlı değildir.

Runtime `torch.hub.set_dir('/opt/ee471/torch/hub')` ile aynı cache'i kullanır; eksik checkpoint için setup hata verir. Ağırlık image içinde olduğundan yeni container açılması yeniden indirme gerektirmez. Değişmeyen build katmanı Docker cache'inden tekrar kullanılır; `--no-cache`, cache temizleme, bağımlılık/build komutu değişikliği veya yeni makine yeniden indirmeye neden olabilir. Image'ı korumak için `docker save/load` da kullanılabilir.

Ağırlık Git'e yazılmaz. `.dockerignore` yerel `.env`, ortamlar, cache ve test çıktılarını dışlar. Build'de oluşturulan `/opt` ağırlıkları kaynak context'inden kopyalanmadığı için bu kurallar onları silmez. Bu yolu boş volume ile örtmeyin. Cog CLI'nin `/src` kaynak mount'u da `/opt` ağırlıklarını gizlemez.

## Gerçek CLI tahmini

Resmi başlangıç belgesindeki örnek görsel:

```bash
mkdir -p test-data outputs
curl --fail --location --output test-data/input.jpg \
  'https://gist.githubusercontent.com/bfirsh/3c2115692682ae260932a67d93fd94a8/raw/56b19f53f7643bb6c0b822c410c366c3a6244de2/mystery.jpg'
cog run ee471-week6-classifier -i image=@test-data/input.jpg
```

`cog run` kurulu 0.23.1 yardımında doğrulanmıştır (`predict` uyumluluk komutu da vardır). Hazır image adını vermek yeniden build gerektirmez.

## Alternatif: standalone Cog HTTP (Compose kapalıyken)

```bash
docker run -d --name ee471-week6-classifier-demo \
  -p 127.0.0.1:5064:5000 ee471-week6-classifier
docker logs -f ee471-week6-classifier-demo
```

Model hazır olduktan sonra başka Ubuntu terminalinde:

```bash
curl --fail http://127.0.0.1:5064/health-check
curl --fail-with-body http://127.0.0.1:5064/predictions \
  -H 'Content-Type: application/json' \
  -d '{"input":{"image":"https://gist.githubusercontent.com/bfirsh/3c2115692682ae260932a67d93fd94a8/raw/56b19f53f7643bb6c0b822c410c366c3a6244de2/mystery.jpg"}}'
docker exec ee471-week6-classifier-demo cat /var/log/ee471/classifier.log
```

Yerel dosya Cog CLI'de `@` ile gönderilir. HTTP JSON'unda Cog bir görsel URL'si veya data URI bekler; `@yerel-dosya` JSON içinde upload anlamına gelmez. Dosyayı URL'ye çıkarmadan HTTP testi yapmak için:

```bash
python3 -c 'import base64,json; from pathlib import Path; print(json.dumps({"input":{"image":"data:image/jpeg;base64,"+base64.b64encode(Path("test-data/input.jpg").read_bytes()).decode()}}))' > outputs/request.json
curl --fail-with-body http://127.0.0.1:5064/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/request.json
```

Üretilen request dosyasını terminale yazdırmayın; görsel içerir. Uygulama görsel/base64 loglamaz. Kısa model yükleme ve tahmin kayıtları stdout'a ve `/var/log/ee471/classifier.log` dosyasına gider; tahmin kaydı sınıf/skorları içerir. Dosya 1 MiB'de döner, iki yedek tutulur. `docker stop` sonrasında aynı container dosyası kalır; container silinirse log da silinir. Kalıcılık istenirse çalıştırmada `-v ee471-week6-logs:/var/log/ee471` eklenebilir.

```bash
docker stop ee471-week6-classifier-demo
docker rm ee471-week6-classifier-demo
```

## Önceki aşama: Cog temelinin gerçek doğrulama kaydı

2026-11-03 tarihinde bu ortamda yapılan **gerçek** kontroller:

- Branch `week6-containers`; WSL x86_64, Cog CLI 0.23.1 ve Docker Desktop Client/Server erişimi doğrulandı.
- `ee471-week6-classifier:latest` build edildi. Tekrar build başarılı oldu; bağımlılık ve ağırlık hazırlama katmanları `CACHED` çıktı, ağırlık yeniden indirilmedi.
- Resmi örnek görselle `cog run` ve host `127.0.0.1:5064` üzerinden gerçek `POST /predictions` başarılı oldu. İkisinde de aynı değerler alındı:

  | Sınıf | Skor |
  | --- | --- |
  | tiger cat | 0.4597228467 |
  | Egyptian cat | 0.3693339229 |
  | tabby | 0.1657565683 |

- `/health-check` `READY` ve Python 3.12.9 / Cog SDK-Coglet 0.23.1 döndürdü. `/` ise endpoint dizinidir; hazır durumu buradan beklenmez.
- Bozuk dosya için HTTP yanıtı **200**, tahmin gövdesi **`status: failed`**, `output: null` ve `Invalid or unreadable image` hatası döndü. Cog'da yalnızca HTTP 200 görmek tahmin başarısı kanıtı değildir; gövdenin durumunu kontrol edin. Ardından geçerli görselle yeniden tahmin başarılı oldu.
- `docker exec ... cat /var/log/ee471/classifier.log` ile gerçek model yükleme, sınıf/skor ve bozuk görsel kayıtları okundu. Görsel/base64 bu dosyada yoktu. Model logger'ı stdout'a yazar; Cog bunu yakalayıp yapılandırılmış container loglarına aktarır. `docker logs` kaydı da doğrulandı.
- `docker run --rm --network none --entrypoint python ...` ile **yeni** container'da gerçek checkpoint yüklendi, `eval()` ve runtime cache yolu kontrol edildi. CUDA runtime ve `nvidia-*` dağıtımı yoktu; kurulu dört Python paketinin sürümleri yukarıdaki tabloyla eşleşti.
- Python kaynak sözdizimi, yeni dosyaların satır sonu boşlukları ve Git ignore kuralları kontrol edildi. Gerçek ağırlık ve tahmin kontrolleri mock değildir.

Karşılaşılan ve saklanmayan hatalar: İki base-image seçeneği ilk komutta birlikte verildiğinde CLI reddetti; komut düzeltildi. Her iki başarılı build'in son etiketleme aşamasında BuildKit `no access allowed to dir "context"` satırı görüldü; build exit kodu 0 oldu, etiketli image CLI/HTTP/ağsız kontrollerinden geçti. Bu satırın iç nedenine ilişkin doğrulanmış teşhis yoktur. Geçici HTTP kontrol yardımcısı önce yanlışlıkla `/` altında READY beklediği için zaman aşımına uğradı; `/health-check` kullanılarak düzeltildi. Container log kontrolü de Cog'un stderr'e yönlendirdiği yapılandırılmış kaydı okuyacak şekilde düzeltildi; bunlar model davranışı değişiklikleri değildi.

Yerel doğrulama görseli ve test çıktıları `test-data/` ve `outputs/` altında Git/build context dışında kaldı. Test container'ları durdurulup kaldırıldı; image ve Docker build cache korundu. Gerçek `.env` okunmadı; diğer projeler değiştirilmedi. Commit/push/merge veya registry push yapılmadı.

Task 2 için kalan teslim işleri: kullanıcının gerçek Postman uygulamasında kontrolü ve demo videosu. Önceki Task 2 aşamasında kapsam dışında kalan Task 1 aşağıda ayrı olarak uygulanmıştır.

## Task 1 — Speech Studio ve sesli hesap makinesi

Kaynaklar `Week-5-Task-1` ve `Week-5-Task-2` içinden yalnız gerekli uygulama kaynakları ve mevcut Python/Node testleri seçilerek kopyalandı. Kaynak projeler değişmedi. `app.py`, servisler, Calculator sınıfı, templates/static ve kopyalanan testler kaynaklarla byte düzeyinde aynıdır. Eski README/PROMPTS veya konsol örnekleri yeni geliştirme geçmişi diye taşınmadı. Gerçek `.env`, sanal ortamlar, node_modules, önbellekler ve üretilen sesler kopyalanmadı.

```text
task-1/
  compose.yaml
  .env.example
  .gitignore
  speech-studio/
    Dockerfile, .dockerignore, constraints.txt, container_server.py
    app.py, speech_service.py, diarization_service.py, requirements.txt
    templates/, static/, tests/
  voice-calculator/
    Dockerfile, .dockerignore, constraints.txt, container_server.py
    app.py, speech_service.py, custom_classes.py, requirements.txt
    templates/, static/, test_*.py, test_*.mjs
  tests/
    compose.offline.yaml, check_containers.py
    native_probe.py, probe_websocket.py, ws_transport.py
```

### Runtime ve bağımlılık seçimi

İki Dockerfile da glibc tabanlı resmi `python:3.12.9-slim-bookworm` (Debian 12) image'ını kullanır. Microsoft'un [Python Speech SDK Linux gereksinimleri](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/quickstarts/setup-platform?pivots=programming-language-python) Debian 12, Python 3.8+ ve glibc/pthreads, OpenSSL 1/3, CA sertifikaları ve ALSA'yı belirtir. Debian tabanında mevcut glibc/pthreads/libstdc++ kullanılır; `ca-certificates`, `libssl3`, `libasound2` kurulur. Hazır Python wheel'i kullanıldığından derleyici, geliştirme başlıkları ve wget eklenmez. Gerçek SDK/native yükleme kontrolü aşağıda kayıtlıdır.

Kaynak requirements dosyaları değiştirilmeden korundu. `constraints.txt`, kaynak projelerin kurulu ortamlarından yalnız paket metadata'sı okunarak doğrulanan doğrudan sürümleri korur:

| Paket | İki uygulama |
| --- | --- |
| Flask | 3.1.3 |
| python-dotenv | 1.2.4 |
| azure-cognitiveservices-speech | 1.53.0 |
| flask-sock | 0.7.0 — yalnız Speech Studio |

Transitif paketlerin tamamına ayrı lock eklenmedi. Önce requirements/constraints kurulup sonra kaynaklar kopyalanır; uygulama değişiklikleri pip katmanını gereksiz yere yenilemez. Docker context allowlist'i ve açık COPY talimatları runtime kaynakları dışında dosya almaz. Anahtar için Dockerfile/ARG/ENV kullanılmaz.

`container_server.py` mevcut Flask uygulamasını **tek process**, `threaded=True`, `0.0.0.0:5000`, `debug=False`, `use_reloader=False` ile başlatır. Kaynak `app.py` başlangıcını değiştirmeye gerek kalmadı. Bu yerel ders demosu için Flask geliştirme sunucusudur; internete production deployment iddiası yoktur. Speech Studio'nun HTTP/WebSocket istekleri thread'lerde aynı süreçteki işlem kilidini paylaşır. Birden çok worker/process eklemeyin.

SDK'nın opsiyonel `extension.codec.so` eklentisi GStreamer ister. Bu kopyalar yalnız ham PCM/PCM WAV işlediğinden eklenti kullanılmaz ve GStreamer kurulmadı. Bu ayrım [Microsoft sıkıştırılmış ses belgeleriyle](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-use-codec-compressed-audio-input-streams) karşılaştırıldı. Kontrolde bu opsiyonel eklentinin eksik GStreamer bağlantıları açıkça raporlanır; diğer gerekli native kütüphaneler için eksik bağlantı kabul edilmez. MP3/OGG/FLAC desteği eklenmiş gibi sunulmaz.

### Yerel ayarlar, build ve çalıştırma

**Windows PowerShell** (Docker Desktop açık olmalı):

```powershell
wsl -d Ubuntu
```

Sonraki komutlar **Ubuntu WSL terminalinde**:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-6/task-1"
# Yalnız .env henüz yoksa örneği kopyala; mevcut ayarları ezme:
if [ ! -e .env ]; then cp .env.example .env; fi
```

Yerel editörde `.env` içindeki `SPEECH_KEY` değerini kendi anahtarınızla doldurun, `SPEECH_REGION` değerini kaynağınıza göre ayarlayın. Örnek anahtar boştur, örnek bölge `eastus`'tır. Ayarları video kaydından önce hazırlayın; dosya içeriğini terminale veya kayda dökmeyin. Bu geliştirme sırasında gerçek `.env` oluşturulmadı veya okunmadı.

```bash
docker compose build
docker compose up -d --no-build --pull never --wait --wait-timeout 90
docker compose ps
docker compose logs --tail=50 speech-studio voice-calculator
```

- Speech Studio: **http://localhost:5081**
- Alternatif aynı-host adresi: **http://127.0.0.1:5081/**. Eski 5061 portunu kullanmayın; tarayıcı bu portta `ERR_UNSAFE_PORT` bildirdi.
- Sesli hesap makinesi: **http://localhost:5062**
- İki port da host `127.0.0.1` arayüzüne bağlıdır; container içinde port 5000 kullanılır.
- Compose projesi `ee471-week6-task1`; Task 2 projesi `ee471-week6-task2` ve 5063/5064 servisleri bağımsızdır.
- Kaynak bind mount'u, ses cihazı, privileged yetki veya tarayıcıya Azure anahtarı aktarımı yoktur. Container'lar root olmayan kullanıcıyla çalışır.
- Ortak `.env`, yalnız `env_file` ile container ortamına aktarılır. Kaynaklardaki python-dotenv açık `/app/.env` yolu ve `override=False` davranışı korunur; image'da böyle bir dosya bulunmadığında runtime ortam değerleri kullanılır. `.env` mount edilmez/kopyalanmaz. Eksik ortak dosyada Compose açık dosya hatası verir; örnekteki boş anahtarla sayfalar açılır, konuşma isteği açıklayıcı 503 hatası verir.
- Healthcheck yalnız `GET /` çağırır; Azure'a istek yapmaz. Ortamı/anahtarı dökebilen `docker compose config` veya ortam çıktıları gösterilmez.
- Mikrofon ve hoparlör tarayıcıdadır. Tarayıcıyı Docker'ın iç IP'si yerine **localhost** adresinden açın; localhost mikrofon için güvenilir geliştirme bağlamıdır. Mikrofon iznini tarayıcıda verin.

**Ubuntu**, aynı Task 1 dizininde durdurma/temizleme:

```bash
docker compose stop
# Container ve yalnız Task 1 ağını kaldırmak isterseniz:
docker compose down
```

Task 2 klasöründe `down` çalıştırmayın. Yukarıdaki Task 1 komutları Task 2 container'larını durdurmaz.

### Korunan özellikler ve Origin

Speech Studio'da TTS, çok segmentli continuous STT/çeviri, pronunciation assessment ve canlı diarization kaynakları korunur. TTS 16 kHz, 16-bit mono PCM WAV üretir; upload doğrulaması 1 MiB / 30 saniye sınırını korur. Pronunciation en-US ve en fazla 500 karakter referans kullanır; diarization ham PCM ile en fazla 60 saniyedir. Frontend'in göreli API yolları ve `location.host` kullanan `/ws/diarization` adresi yeni portta çalışır.

Origin koruması kaldırılmadı: `http://localhost:5081` yalnız `Host: localhost:5081` ile, `http://127.0.0.1:5081` kendi aynı host'u ile uyumludur. Başka port/host reddedilir. Aynı sayfada localhost ile 127.0.0.1 adreslerini karıştırmayın. Diarization boyunca ortak kilit diğer konuşma isteklerine busy yanıtı verir; WebSocket kapanınca stream/dinleyiciler/kilit temizlenir.

Hesap makinesinin Calculator sınıfı, elle hesaplama API'si, 15 saniye en-US mikrofon/STT girişi, sembol/kelime komut ayrıştırması ve Azure TTS modülleri aynıdır. Kuyruk, sabit ses önbelleği, iptal ve mikrofon başlangıcında sesleri durdurma davranışları korunur. TTS hatası hesaplama sonucunu değiştirmez.

### Speech Studio port düzeltmesi — 5061 → 5081

Kullanıcı, container healthy ve curl HTTP 200 olduğu halde tarayıcının 5061 için `ERR_UNSAFE_PORT` verdiğini bildirdi. Speech Studio host eşlemesi `127.0.0.1:5081:5000` olarak değiştirildi. Container içi 5000, hesap makinesinin 5062'si ve Task 2'nin 5063/5064 portları korundu. Başlatma komutları aynıdır; sunucu kodu/image içeriği değişmediği için rebuild gerekmedi.

Yalnız `speech-studio` yeniden oluşturuldu. Gerçek `.env` okunmadı: var olan container'ın etkin runtime ortamı yalnız bellekte tutulup stdin üzerinden Compose override olarak aktarıldı; değerler dosyaya/loga/komut argümanına yazılmadı. Ortamın ve image kimliğinin korunduğu, diğer container kimliklerinin değişmediği karşılaştırıldı. Bu tek seferlik taşıma adımıdır; normal başlatma yukarıdaki ortak `.env` / Compose komutlarıyla yapılır.

Doğrulama: `http://127.0.0.1:5081/` HTTP 200; gerçek Chrome headless sayfayı unsafe-port hatası olmadan açtı. Gerçek yayınlanan portta localhost/127.0.0.1 için WebSocket upgrade ve Azure başlamadan geçersiz start mesajının güvenli reddi/kapanma kontrol edildi. Yanlış Origin'ler 403 aldı. Ayrı ağsız container'da SDK mock'larıyla güncel 5081 Origin, eşzamanlı HTTP/busy, sıralı final/tail, tamamlanma ve kopma sonrası temizlik kontrolü geçti. Origin algoritması gevşetilmedi; tam host/port eşleşmesini zaten destekliyordu. Gerçek Azure/mikrofon/ses denemesi yapılmadı.

Servis açıkken yalnız HTTP/Origin kontrolünü tekrar etmek için **Ubuntu**, `task-1` içinde:

```bash
python3 tests/check_studio_port.py
```

Son durumda Speech Studio 5081'de healthy bırakıldı; hesap makinesi ve Task 2 servisleri korunarak açık kaldı. Aşağıdaki ilk Task 1 doğrulama kaydındaki 5061 referansları eski test portunu anlatır; güncel kullanım adresi 5081'dir.

### Bu aşamada gerçekten yapılan kontroller

2026-11-03:

- İki image gerçek Docker build ile üretildi. Yerel kaynak ortamlarının doğrudan sürümleri metadata ile doğrulandı; gerçek `.env` okunmadı. Seçilen 44 kaynak/test dosyası kopyalandı.
- İki image ağ kapalıyken Azure SDK 1.53.0 import edildi; OpenSSL/ALSA `ctypes` ile yüklendi, gerekli native kütüphanelerin `ldd` bağlantıları kontrol edildi. Yalnız opsiyonel sıkıştırılmış-audio eklentisinin GStreamer eksikliği görüldü; PCM kapsamı resmi belgeden doğrulandı. Açıkça sahte değerlerle SpeechRecognizer, SpeechSynthesizer, TranslationRecognizer, PronunciationAssessmentConfig/apply_to ve ConversationTranscriber nesneleri oluşturuldu; start/speak/recognize çağrılmadı.
- Kopyanın mevcut testleri gerçek Linux image'ları içinde SDK mock'larıyla çalıştırıldı: **Speech Studio 80 Python**, **hesap makinesi 21 Python** testi geçti. Eski testlerde kapanmayan test istemcisi dosyalarına ilişkin `ResourceWarning` görüldü; test başarısızlığı değildi, kaynak testler bu uyarıları gizlemek için değiştirilmedi.
- Windows Node.js ile kopya kaynaklarda **Speech Studio 14**, **hesap makinesi 40** çevrimdışı test geçti. PCM dönüşümü, konuşma UI durumları, komut ayrıştırma, TTS sırası/önbellek/iptal/mikrofon etkileşimi mevcut testlerle korundu.
- Gerçek Flask-Sock WebSocket taşıması + SDK mock kontrolünde localhost:5061 (ilk doğrulamadaki eski port) ve aynı portlu Origin kabul edildi; yanlış host/port 403 aldı. WebSocket açıkken HTTP ana sayfası çalıştı ve konuşma isteği 409 busy aldı. Kesinleşmiş sonuç ve stop sırasında gelen son sonuç sırayla iletildi; completed ancak temizlik sonrası geldi. Kopma sonrasında stream/dinleyici/kilit yeniden kullanılabildi.
- WebSocket testinin ilk 403 yanıtı, testte kullanılan simple-websocket Client'ın handshake Host başlığından portu çıkarmasından kaynaklandı; kurulu istemci kaynağıyla doğrulandı. Uygulama Origin kontrolü gevşetilmedi; standart kütüphaneli test istemcisi tarayıcı gibi tam Host:port gönderdi.
- Gerçek `.env` devre dışıyken Compose ile iki servis açıldı ve healthy oldu. ilk yapılandırmadaki 5061/5062 ana sayfaları, tüm gerekli statik JS/MJS/CSS dosyaları, JavaScript MIME tipleri ve elle `4 × 6 = 24` / sıfıra bölme kontrol edildi. Konuşma API'leri boş ayarlarda 503 verdi. İlk yapılandırmada Host localhost:5061 üzerinden gerçek WebSocket upgrade → eksik ayar mesajı → kapanma kontrol edildi; Azure'a gidilmedi.
- Test yapılandırması `.env` yüklemez: `--env-file /dev/null` ve `env_file: !reset []` override kullanır. Task 1 test servisleri finally içinde durdurulup kaldırıldı; Task 2 container kimlikleri aynı kaldı ve servisleri çalışmayı sürdürdü.
- Son hash kontrolünde 44 özgün dosya ve kopyaları aynıydı. `git diff --check` geçti; yeni Docker/test/belge dosyalarında satır sonu boşluğu yoktu. Kaynaktan aynen taşınan `custom_classes.py` satır 8'deki eski boşluk biçimi kodu gereksiz değiştirmemek için korundu. `.env` ignore ve `.env.example` izlenebilirlik kontrolü geçti.

Bu kontroller **gerçek Azure, gerçek mikrofon veya hoparlörden ses duyulması doğrulaması değildir**. Eski Week 5 kullanıcı doğrulamaları yeni Docker kopyasının manuel testi olarak aktarılmaz. Bu aşamada gerçek tarayıcı/donanım denemesi yapılmadı; kullanıcı aşağıdaki listeyi kendi ayarlarıyla deneyecek.

Testleri tekrar çalıştırmak için **Ubuntu**, `task-1` içinde, gerçek ayarlar yüklenmeden:

```bash
docker compose --env-file /dev/null -f compose.yaml -f tests/compose.offline.yaml build
python3 tests/check_containers.py
```

Bu test Task 1 Compose projesini kendisi açıp kaldırır; gerçek ayarlarla çalışan Task 1 demo oturumu sırasında çalıştırmayın. Task 2'ye dokunmaz. Node kontrolleri **Windows PowerShell**, repo kökünden:

```powershell
node --test Week-6/task-1/speech-studio/tests/*.cjs
node --test Week-6/task-1/voice-calculator/test_*.mjs
```

### Gerçek Azure manuel deneme listesi

Speech Studio — `http://localhost:5081`:

1. en-US/tr-TR kısa TTS üretin, tarayıcıda dinleyin ve WAV indirin.
2. En fazla 30 saniye, 1 MiB, 16 kHz/16-bit/mono PCM WAV ile çok cümleli STT deneyin. Uygun uzunlukta TTS WAV'ını doğrudan yükleyin.
3. Kısa WAV ile İngilizce↔Türkçe çeviriyi, ardından kendi İngilizce kaydınız ve referans metinle pronunciation değerlendirmesini deneyin. TTS kaydı kendi telaffuzunuzun ölçümü değildir.
4. Mikrofon izni verip canlı diarization başlatın; konuşma sırasında geçici/kesin ve konuşmacı etiketli sonuçları görün. Durdur'a basınca son sonuçlar ve tamamlanma gelsin. Konuşmacı ID'leri kişi adı değildir.
5. Diarization açıkken başka konuşma işleminin busy davranışını ve Durdur sonrası yeniden kullanımı deneyin. Azure kimlik/kota/servis hatalarının başarı diye gösterilmediğini kontrol edin.

Sesli hesap makinesi — `http://localhost:5062`:

1. Elle dört işlem ve sıfıra bölmeyi deneyin.
2. Mikrofonla `five plus two is`, `one point five plus two is` söyleyin; özgün metin, işlem ve API sonucu görünsün.
3. Sesli çıkışı açın; fiziksel tuş seslerini ve başarılı eşittir sonucunu dinleyin. Hızlı tuşlarda sıra/önbelleği kontrol edin.
4. Sesli çıkışı kapatma, temizleme ve mikrofonu başlatmada eski seslerin kesilmesini; hata/iptal sonrası yeniden kullanımı deneyin. Sesli komutun programatik tuşları tek tek seslendirilmemelidir.

### Task-1-demo.avi için sıra

1. Ayarları önceden hazırlayın; Ubuntu'da doğru Task 1 dizinini ve iki Dockerfile/Compose portlarını gösterin.
2. `docker compose build` çalıştırın. Cache kullanılıyorsa bunu söyleyin; build sonucunu gösterin.
3. `docker compose up -d --no-build --pull never --wait` ve `docker compose ps` ile iki healthy container'ı ve 5081/5062 portlarını gösterin.
4. Tarayıcıda Speech Studio için kısa TTS/STT, çeviri/pronunciation ve canlı diarization akışından uygun örnekleri gösterin.
5. Hesap makinesinde elle hesaplama, mikrofon komutu ve Azure TTS sonucunu gösterin.
6. `docker compose stop` ile yalnız Task 1 servislerini durdurun. Gerçek Azure/donanım kontrollerini ancak gerçekten yaptığınız ölçüde anlatın.
