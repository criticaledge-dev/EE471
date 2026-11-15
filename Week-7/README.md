# EE471 Week 7 — Görsel sınıflandırıcılar

FashionMNIST baseline eğitimi (Aşama 1), baseline servisi (Aşama 2), kontrollü HPO (Aşama 3) ve iki modelin yan yana Cog/Flask sunumu (Aşama 4) hazırdır. Temel kaynak [PyTorch Quickstart](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html). CIFAR10 baseline eğitimi Aşama 5 ile eklendi; CIFAR10 baseline Cog/website Aşama 6 ile eklendi; CIFAR10 kontrollü HPO Aşama 7, iki modelli Cog/website karşılaştırması Aşama 8 ile tamamlandı. Aşağıdaki Aşama 1–3 kayıtları kendi tarihlerindeki çalışmayı anlatır; güncel servis komutları Aşama 4 bölümündedir.

Branch: `week7-classifiers`. Temiz çalışma ağacında `git fetch origin main` sonrası yerel main/origin/main aynı `6c6d106` commit'indeydi; yeni branch buradan oluşturuldu. Commit/push/merge yapılmadı.

## Aşama 8 — Task 2: CIFAR10 Baseline / Optimized karşılaştırması

İki model aynı runner, orijinal Net CNN, RGB32×32 preprocess ve CIFAR10 sınıf sırasını kullanır. **Yeniden eğitim, HPO veya model/dataset indirme yapılmadı.** Mevcut baseline/optimized checkpoint'leri ve eski ölçüm JSON'ları değişmedi. Aşağıdaki Aşama 5–7 bölümleri ilgili tarihteki eğitim/servis/HPO kayıtlarıdır; güncel CIFAR10 servis komutları bu bölümdedir. FashionMNIST'in güncel komutları Aşama 4'tedir.

| Servis | Image | Host adresi |
| --- | --- | --- |
| CIFAR10 website | `ee471-week7-cifar10-website` | http://localhost:5074 |
| Baseline Cog | `ee471-week7-cifar10-baseline` | http://localhost:5075 |
| Optimized Cog | `ee471-week7-cifar10-optimized` | http://localhost:5076 |

Üç port yalnız **127.0.0.1** üzerinde yayınlanır. Mevcut Compose proje adı `ee471-week7-cifar10-baseline` korunur; optimized servisi eklenir. FashionMNIST 5071–5073 ve Week 6 dosya/servisleri değiştirilmez. Model servisleri yerel image kullanır (`pull_policy: never`); eksik image registry'den otomatik çekilmez.

### İki checkpoint ve build stratejisi

Build öncesi şu dosyalar gereklidir; Git dışındadır:

| Model | Kaynak checkpoint | Boyut | SHA256 |
| --- | --- | --- | --- |
| Baseline | `artifacts/baseline/cifar10_last.pth` | 251.454 bayt | `60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c` |
| Optimized | `artifacts/optimized/cifar10_optimized.pth` | 251.552 bayt | `3afe36d66e686617f7a8628b12607e6e25f4c4cc7e218338d018226943ed4c0e` |

`prepare_build.py` iki dosyayı **herhangi bir context'i değiştirmeden önce** korunmuş baseline/HPO kayıtlarına göre doğrular. Eksik dosya açık README hazırlık hatası verir; yanlış hash ile build reddedilir. `outputs/build/baseline` ve `outputs/build/optimized` içine yalnız aynı `cog_runner.py`, orijinal `model.py/preprocessing.py`, sabit requirements, Cog config, model metadata'sı ve **birer checkpoint** kopyalanır. Her image içinde tek `/src/checkpoint.pth` vardır; doğru modele ait SHA hem build context'te hem final image içinde karşılaştırılır. `model_config.json` model adını, ağırlık hash'ini ve ayrı log yolunu seçer.

Allowlist `.dockerignore` dataset, venv/.env, eğitim/HPO/eval kodu, demo/sonuç/geçici dosyaları model image'larına almaz. Cog'un ürettiği `.cog/` metadata dizini tekrar hazırlamayı engellemez, model girdilerinden hariç kalır. Git'in ignore ettiği checkpoint kontrollü context'e açıkça kopyalanır; Git ignore ile Docker context karıştırılmaz.

Runner setup ağırlığı CPU'ya bir kez yükler, hash'i denetler ve eval uygular. Her tahmin `inference_mode`, aynı RGB32×32 ve kanal mean/std .5 preprocess'i kullanır. Başarı çıktısı değişmedi: `output.class`, `output.score`, `output.top3`. Runtime eğitim/veri indirme yapmaz. Loglar model adı, açık tahmin sınıfı, ilk üç skor ve süre içerir; görsel/base64 yazılmaz.

### Website: tek yükleme, iki bağımsız sonuç

Tek Classify → Flask gerçek PNG/JPEG doğrulaması → **aynı doğrulanmış data URL** ile iki bağımsız, en fazla iki eşzamanlı Cog isteği. Yapılandırmalar `BASELINE_URL` / `OPTIMIZED_URL`; Compose içinde `http://baseline:5000` / `http://optimized:5000`. Container dışında varsayılanlar 5075/5076'dır. Tekrar denemeler otomatik/sınırsız değildir.

Tam **32×32, en fazla 1 MiB PNG/JPEG**, decode/verify, istek boyutu sınırı ve güvenli hata işleme korunur. HTTP200 içindeki Cog status mutlaka kontrol edilir; başarısız sonucu başarı saymaz. İki modelin sonucu `results.baseline` / `results.optimized` içinde ayrı `status/output/error` olarak dönülür. Üst status `succeeded`, `partial` veya `failed` olur; tek servis hatası diğerinin başarılı sonucunu silmez.

Kartlar geniş ekranda yan yana, 640px altında alt alta gelir. Yeni seçim/istek eski sonuç ve hataları temizler; çift gönderim/abort/eski yanıt koruması ve object URL temizliği devam eder. Her kart top-1 ve ilk üç yüzdeyi gösterir; skorlar yeniden normalize edilmez. **Resmi test accuracy** ayrı etiketlidir: baseline **%51,41**, optimized **%54,24**, her biri 10.000 test örneği. Bunlar `results/baseline/metrics.json:test` ve `results/hpo/summary.json:winner_test` kaynaklarından türetilir. Korunmuş ölçümler yeniden yazılmaz; website'in yeni optimized ölçüm kopyası build hazırlığında üretilir.

### Build / başlatma / durdurma

**PowerShell:**

```powershell
wsl -d Ubuntu
```

**Ubuntu/WSL**, Cog 0.23.1 ve çalışan Docker Desktop ile:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-2"
cog --version
docker version
bash build.sh
docker compose --env-file /dev/null up -d --wait
docker compose --env-file /dev/null ps
```

`build.sh` sırası: prepare → her `outputs/build/<model>` dizininden `cog build -t ee471-week7-cifar10-<model> --progress plain --use-cog-base-image=false` → iki `IMAGE_SHA256_OK` kontrolü → website build. Bash dosyası LF satır sonlarıyla tutulur. `--env-file /dev/null` gerçek .env yüklemesini önler. Kaynak bind mount edilmez; image içindeki dosyalar çalışır. Cog READY ve website `/healthz` healthcheck'leri kullanılır.

İş bitince yalnız CIFAR10 projesini durdurmak için **task-2 içinde**:

```bash
docker compose --env-file /dev/null down
```

### İki ayrı canlı log

**Ubuntu task-2**, ayrı terminaller:

```bash
docker compose --env-file /dev/null exec baseline sh
# Baseline container içinde:
tail -f /var/log/ee471/cifar10-baseline.log
```

```bash
docker compose --env-file /dev/null exec optimized sh
# Optimized container içinde:
tail -f /var/log/ee471/cifar10-optimized.log
```

`Ctrl+C`, sonra `exit` ile çıkın. Loglar stdout'a da yazılır; container silinirse dosya kalıcı değildir. `Prediction completed ... class=cat ...` satırı gerçek istekten gelir; örnek/sahte log üretilmez.

### Aynı PNG için gerçek doğrulama — 2026-11-13

Değişmeyen dosya `demo_samples/test_00000_label_3_cat.png`, resmi test index0, gerçek sınıf cat. PNG SHA256 `0d4964922e2463ad0e2b1cd298e03d5627ff7dad1ab1cdd173ce35e9974e204f`.

| Model | Python / Cog / website tahmini | cat | dog | bird |
| --- | --- | --- | --- | --- |
| Baseline | cat / cat / cat | %44,070399 | %18,100601 | %12,535478 |
| Optimized | cat / cat / cat | %43,048623 | %22,625336 | %12,188040 |

Her modelin üç yoldaki sınıfları aynı ve skorları mutlak **1e-7** toleransında eşleşti. JSON sayı serileştirmesinin son basamak farkı dışında anlamlı fark bulunmadı. İki modelin de cat demesi geçerlidir; farklı sonuç göstermek için örnek seçilmedi. Optimized'ın bu tek görselde daha düşük skoru olması, %54,24 genel test accuracy'siyle çelişmez.

- İki gerçek Cog image'ı ve website build edildi; image içi checkpoint SHA, ortak runner/CNN/preprocess kaynak hash'leri, tek checkpoint ve offline CPU/eval setup doğrulandı. Eksik/yanlış hash'li ağırlık açık hata verdi. Her iki çalışan logda website'ten yeni tahmin ve açık class/süre görüldü; base64 yoktu.
- **18 website mock testi**: aynı payload/iki URL/birer istek, her iki yönde tek servis hatası ve toparlanma, format/boyut, status/error/timeout, skor/top-1 tutarlılığı ve resmi accuracy etiketleri. **7 mevcut core/seçim testi** de geçti. Bunlar yeni eğitim veya gerçek inference kanıtı yerine kullanılmaz.
- **Gerçek HTTP/model kontrolleri:** aynı PNG karşılaştırması, eksik/bozuk dosya, her Cog'da bozuk görselin HTTP200 içindeki failed durumu ve ardından geçerli tahmin; ayrıca gerçek JPEG'in her iki Cog/website yolunda çalışması. JPEG ile orijinal PNG'nin birebir aynı skor vereceği iddia edilmez.
- **Gerçek Windows Chrome headless + gerçek model:** beş form gönderimi, preview, her iki kartın Cog ile eşleşmesi, çift submit'in tek isteğe dönüşmesi, yeni seçimde iki eski sonucun temizlenmesi, bozuk dosya sonrası toparlanma, 375px tek sütun/taşma kontrolü geçti. Optimized servisi gerçekten durduruldu: baseline sonucu kaldı, hata yalnız optimized kartına geldi; servis geri başlatılıp üçü healthy olduğunda yeniden başarılı oldu. İki object URL bırakıldı; JS error/unhandledrejection kaydı boştu. Bu kullanıcı tarafından yapılan manuel masaüstü doğrulaması değildir.
- **Postman CLI 1.85.0:** 2 doğrudan Cog isteği, **10 assertion başarılı**, 0 hata, exit0; `--no-report-events`. Login/cloud paylaşımı uyarısı yerel kontrolü engellemedi; login/publish yapılmadı. **Masaüstü Postman kullanılmadı.**
- Başlangıçta Docker motoru kapalıydı ve mevcut beş container durmuştu. Docker Desktop başlatıldı; FashionMNIST'in mevcut üç container'ı aynı kimlikle yeniden açıldı. FashionMNIST kaynak/image'ları değiştirilmedi; ana sayfa200 ve iki Cog READY doğrulandı. Son durumda üç CIFAR10 ve üç FashionMNIST servisi healthy.
- Başlangıçtaki yerel CIFAR10 runner dosyasında Runner/setup bloğu eksik ve sözdizimi bozuktu; mevcut hâli `outputs/stage8-inputs` altında korunup önceki sağlam build bağlamıyla karşılaştırılarak onarıldı. Onarım sırasında kalan yinelenmiş sınıf bloğu Cog'un `Runner must define run() or predict()` hatasıyla yakalandı ve düzeltildi; AST kontrolü tek Runner/setup/run yapısını doğruladı. Windows'ta shell dosyası yazımından kaynaklanan CRLF/pipefail hatası LF ile düzeltildi. Bu başarısız denemeler başarı sayılmadı. Son UTF-8 taraması yeni JS durum metnindeki Windows kodlamalı apostrofu yakaladı; ASCII karakterle düzeltilip yalnız website tekrar build edildi. Son image ile gerçek headless test yeniden geçti.
- Son buildler exit0 verdi. Cog label/schema adımındaki mevcut `no access allowed to dir "context"` satırı yine görüldü; export tamamlandı ve son image'lar gerçek hash/setup/HTTP kontrollerinden ayrıca geçti. Başarılı build tek başına model doğrulaması sayılmadı.

Yeni kayıt `task-2/results/comparison-validation.json`; eski eğitim/HPO/servis ölçüm JSON'ları ve checkpoint'ler korundu. Ayrıntılı geçici çıktılar `outputs/` altında Git dışındadır. Bu aşamada Git add/commit/push/merge yapılmadı.

Kontrolleri yeniden çalıştırmak için **Ubuntu task-2**:

```bash
python3 -B tests/check_comparison_service.py
```

**PowerShell repo kökü:**

```powershell
node Week-7/task-2/tests/check_browser.mjs
```

Headless test kısa süre yalnız CIFAR10 optimized servisini durdurur; finally ile geri açar ve üç CIFAR10 servisini healthy bırakır. FashionMNIST'e durdurma işlemi uygulamaz.

### Aynı gövdeyle iki Postman isteği

**Ubuntu task-2:**

```bash
python3 postman/make_request.py demo_samples/test_00000_label_3_cat.png
curl --fail-with-body http://localhost:5075/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
curl --fail-with-body http://localhost:5076/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
```

Masaüstü Postman'da `postman/classifier.postman_collection.json` ve `outputs/postman-environment.json` dosyalarını import edip ortamı seçin. Baseline ve Optimized için sırayla Send yapın. İki istek aynı `prediction_body` değişkenini kullanır ve doğrudan 5075/5076 `/predictions` adreslerine gider. Uzun base64 elle yazılmaz; pre-request script keyfî dosya sistemi erişimi yapmaz. Üretilen body/environment JSON'ları Git dışında kalır, paylaşılmamalıdır.

**PowerShell repo kökü**, yerel CLI kontrolü:

```powershell
postman collection run Week-7/task-2/postman/classifier.postman_collection.json -e Week-7/task-2/outputs/postman-environment.json --no-report-events
```

Mevcut masaüstü-import edilebilir v2.1 collection biçimi korundu; JSON kontrolü ve gerçek CLI execution yapıldı. v3 directory lint bu dosyaya uygulanmış gibi raporlanmaz.

### Temiz clone'dan iki checkpoint hazırlığı

İki ağırlık Git'te yoktur. Yukarıdaki `artifacts/baseline/cifar10_last.pth` ve `artifacts/optimized/cifar10_optimized.pth` yolları **build öncesi** mevcut olmalıdır. Orijinal deney ağırlık yedeklerini bu konumlara koyup `python3 prepare_build.py` ile SHA kontrolü yapılabilir.

Yedek yoksa Aşama 5/7 protokolüyle ayrı eğitim/HPO hazırlığı gerekir. **Aşağıdaki eğitim/indirme komutları Aşama 8'de çalıştırılmadı**; build veya runtime bunları otomatik çalıştırmaz. Python3.12.11, torch2.6.0+cpu, torchvision0.21.0+cpu, Pillow11.1.0, NumPy2.3.1, seed42/CPU2thread ve aynı veri split'i gereklidir.

**Ubuntu task-2**, Python3.12.11 kurulu ortam:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -c 'import sys; assert sys.version_info[:3] == (3,12,11), sys.version'
python -m pip install -r requirements.txt
# Ayrı run/demo dizinleri eski ölçümleri ezmez:
python -B train.py --run-dir results/reproduced-baseline \
  --checkpoint artifacts/baseline/cifar10_last.pth --demo-dir demo_samples_reproduced
python -B optimize.py --run-dir results/reproduced-hpo --candidate-dir artifacts/reproduced-hpo \
  --optimized artifacts/optimized/cifar10_optimized.pth
python -B prepare_build.py
bash build.sh
```

Train gerektiğinde resmi veriyi indirir; optimize yalnız oluşmuş yerel cache'i download=False ile kullanır. Farklı CPU/runtime'da bayt düzeyinde aynı sonuç garanti edilmez. Hash uyuşmazsa build durur; yeni ağırlıkları eski %51,41/%54,24 ölçümleriyle eşleştirmeyin. Orijinal ağırlıkları temin edin veya yeni deneyin köken/ölçüm kayıtlarını ayrı doğrulayın. Bu tamamlanmış çalışma alanında iki checkpoint zaten mevcut; yeniden eğitim gerekmez.

### Task-2 demo sırası

1. İki checkpoint yolu ve build sonundaki iki `IMAGE_SHA256_OK` satırını gösterin.
2. Compose ps ile üç CIFAR10 healthy servisi ve 5074/5075/5076 adreslerini gösterin.
3. İki container logunu ayrı terminallerde tail-f açın.
4. Website'e aynı cat PNG'sini bir kez yükleyip Classify yapın; cat/cat ve %44,07/%43,05 skorlarını gösterin. Bunları %51,41/%54,24 resmi test accuracy'den ayırın.
5. Aynı PNG gövdesiyle iki doğrudan Postman isteğinin succeeded/top-3 kontrollerini gösterin. CLI sonucu ile masaüstü Send işlemini ayrı anlatın.
6. Bozuk dosya sonrası toparlanmayı veya tek servis hatasında diğer kartın kalmasını gösterebilirsiniz; durdurma yapılırsa üç CIFAR10 servisini tekrar healthy bırakın. FashionMNIST açık kalsın.

---

## Aşama 7 — Task 2: CIFAR10 kontrollü HPO (aşama kaydı)

Bu aşamada yalnız `task-2/optimize.py`, sentetik seçim testleri, yeni `results/hpo` kayıtları ve Git dışındaki aday/optimized ağırlıkları eklendi; ortak belgeler güncellendi. **Website/Cog/build/Compose kodu değiştirilmedi.** Çalışan CIFAR10 servisi baseline checkpoint'i sunmaya devam eder; optimized henüz deploy edilmedi. FashionMNIST ve önceki CIFAR10 kayıtları korundu.

### Protokol ve doğrulanan kontrol değişkenleri

- Aynı Net CNN ve orijinal preprocess/CLASSES: RGB32×32, ToTensor, kanal mean/std .5, augmentation yok. Orijinal eğitim/model/dönüşüm/eval kaynak hash'leri baseline JSON'uyla eşleşti.
- Python 3.12.11, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0, NumPy 2.3.1; aynı mevcut CPU runtime image'ı Python entrypoint'iyle kullanıldı. Yeni Cog image/servis/build yoktur.
- CPU/2 thread, seed42, deterministic algorithms, batch4, num_workers0, **2 tam epoch**. Aynı resmi 50.000 içinden **45.000 train / 5.000 validation** indeksleri; baseline split hash'leriyle eşleşti. Resmi test model/ayar/checkpoint seçimine katılmadı.
- Her aday öncesinde Python/NumPy/torch seed42 sıfırlandı ve yeni Net oluşturuldu. **Dört başlangıç state hash'i aynı**. Train loader generator seed42 ile her aday için yeniden kuruldu ve iki epoch arasında devam etti.
- Gerçekte tüketilen sample indeksleri RNG/tensor değiştirmeyen TrackedSubset ile hash'lendi. **Sekiz epoch sıra hash'i**, baseline'ın değişmemiş loader/seed protokolünden yeniden üretilen iki hash ile eşleşti. Eski baseline'da trace kaydı olmadığı için bunun geçmişte doğrudan ölçülmüş baseline trace'i olduğu iddia edilmez. Baseline başlangıç state hash'i de korunmuş kod/protokolden yeniden türetildi.
- Yerel veri `download=False` ile kullanıldı. HPO container'ında **network none** ve veri klasöründe **readonly** mount vardı; veri indirme başlatılmadı.

Referans SGD lr=.001/momentum=.9 kaydı uyumlu bulundu; yeniden eğitilmedi. Baseline son validation accuracy **%52.08**, loss **1.333564**. İki SGD adayında momentum=.9, dampening=0, weight_decay=0, nesterov=false. Adam'da betas=(.9,.999), eps=1e-8, weight_decay=0, amsgrad=false. Gerçek optimizer defaults her trial JSON'unda yer alır; scheduler/erken durdurma yoktur. `protocol` alanı referans ayarını, trial kayıtları aday optimizer/lr farkını tutar.

### Gerçek aday sonuçları — 2026-11-09

Her aday **2. epoch** üzerinden karşılaştırıldı; ara epoch'un en iyi checkpoint'i alınmadı. Süre train+validation epoch döngülerinin toplamıdır; izlenen indeks hash'lerinin çok küçük maliyeti de bu döngülerdedir. Checkpoint/JSON yazımı ve yükleme gibi işler toplam arama süresinde ayrıca bulunur.

| Aday | Son train loss | Train accuracy | Son val loss | Validation accuracy | Train+val (s) |
| --- | --- | --- | --- | --- | --- |
| SGD 0.003 | 1.422720 | %48.7889 | 1.514985 | %46.5200 | 35.20 |
| SGD 0.01 | 2.027029 | %24.6978 | 1.950872 | %27.8600 | 36.35 |
| Adam 0.0003 | 1.323596 | %52.4800 | 1.294761 | %53.3200 | 45.87 |
| Adam 0.001 | 1.315503 | %52.6444 | 1.327986 | %52.4200 | 46.40 |

Tam epoch kaydı:

| Aday | Epoch | Train loss | Train accuracy | Val loss | Val accuracy | Süre (s) |
| --- | --- | --- | --- | --- | --- | --- |
| sgd_lr_0_003 | 1 | 1.664115 | %39.2333 | 1.511801 | %45.4600 | 17.87 |
| sgd_lr_0_003 | 2 | 1.422720 | %48.7889 | 1.514985 | %46.5200 | 17.33 |
| sgd_lr_0_01 | 1 | 1.999943 | %25.9000 | 2.016611 | %24.1800 | 17.63 |
| sgd_lr_0_01 | 2 | 2.027029 | %24.6978 | 1.950872 | %27.8600 | 18.72 |
| adam_lr_0_0003 | 1 | 1.589842 | %42.1422 | 1.408971 | %49.0800 | 23.12 |
| adam_lr_0_0003 | 2 | 1.323596 | %52.4800 | 1.294761 | %53.3200 | 22.74 |
| adam_lr_0_001 | 1 | 1.558676 | %42.7578 | 1.472023 | %47.0200 | 23.61 |
| adam_lr_0_001 | 2 | 1.315503 | %52.6444 | 1.327986 | %52.4200 | 22.79 |

Seçim: **Adam lr=0.0003**. Kural en yüksek epoch-2 validation accuracy; eşitlikte düşük validation loss, tam eşitlik kalırsa listelenen ilk aday. Sıra: `adam_lr_0_0003, adam_lr_0_001, sgd_lr_0_003, sgd_lr_0_01`. Kazanan validation accuracy **%53.3200**, loss **1.294761**; baseline'a göre **+1.2400 yüzde puan**. Baseline yalnız referanstır; seçimin uygun adayları belirtilen dört yeni koşudur.

`selection.json` **resmi test dataset/loader'ı oluşturulmadan önce** yazılıp donduruldu (`frozen_at_utc`). Seçim JSON'u baseline validation karşılaştırmasını ve validation sıralamasını da içerir. Yalnız kazananın kopyalanmış final CPU state_dict'i test edildi; diğer trial `test` alanları null kalır. Demo PNG seçim sonrasında kullanılır.

| Model | Resmi test loss | Resmi test accuracy (10.000) |
| --- | --- | --- |
| Baseline SGD .001/.9 — önceki ölçüm | 1.3332864619 | %51.41 |
| Seçilen Adam 0.0003 | 1.2751332348 | %54.24 |

Test accuracy farkı **+2.83 yüzde puan**. Test loss farkı optimized−baseline **-0.0581532271**. Test accuracy bu koşuda **iyileşti**. Test sonucuna bakıp kazanan veya aday listesi değiştirilmedi. İki test ölçümünde aynı CPU/2 thread, batch4, shuffle=false ve örnek ağırlıklı CrossEntropyLoss/accuracy kullanıldı; baseline yeniden test edilmedi, korunmuş ölçümü kullanıldı.

Yeni adayların train+validation toplamı **163.817 s**; checkpoint/seçim/kazanan testi ve demo referansı dahil arama süresi **167.378 s**. Baseline denetimi/cache yükleme bu arama sayacından öncedir; indirme süresi yoktur. Kazananın test döngüsü **1.752 s**. Baseline'ın eski süresi yeni toplama eklenmedi.

### Kayıtlar ve ayrı-process inference

```text
task-2/
  optimize.py
  tests/test_selection.py
  results/hpo/summary.json          # tüm epoch'lar, protokol/hash audit, seçim, test ve süreler
  results/hpo/trials/*.json         # her adayın gerçek optimizer/epoch/süre/checkpoint kaydı
  results/hpo/selection.json        # testten önce dondurulan karar
  results/hpo/optimized_reload_reference.json
  results/hpo/optimized_reload_check.json
  results/hpo/execution.json        # koruma ve gerçek doğrulama sonucu
  artifacts/hpo/*_last.pth          # Git dışında dört final aday checkpoint'i
  artifacts/optimized/cifar10_optimized.pth # Git dışında seçilen CPU state_dict
```

Optimized checkpoint **251,552 bayt**, SHA256 `3afe36d66e686617f7a8628b12607e6e25f4c4cc7e218338d018226943ed4c0e`. Baseline checkpoint/ölçümleri değişmedi; aynı Net/load_model/predict biçiminde yüklenir.

Seçim ve test sonrasında ayrı yeni Python sürecinde **mevcut `predict.py`** ile `test_00000_label_3_cat.png` yüklendi. Gerçek **3/cat**, tahmin **3/cat**, skor **%43.0486**; sonuç **doğru**. Hash ve logitler seçim sonrası kaydedilen referansla 1e-6 toleransında eşleşti (`reference_verified=true`). Bu tek PNG model seçiminde kullanılmadı ve skoru test accuracy değildir.

Üç yeni sentetik seçim testi ve dört mevcut core testi (**7 toplam**) geçti: test skorunun/ara-epoch zirvesinin kararı etkilememesi, accuracy eşitliğinde loss kuralı ve eksik/nonfinite final metrik reddi. Bunlar gerçek HPO ölçümlerinden ayrıdır. Önceden var olan tüm koruma snapshot dosyalarının hash'leri ve beş Compose container kimliği/healthy durumu son kontrolde doğrulandı. Website/Cog testleri bu aşamada değişmedi; geçmiş test sayıları yeni koşu gibi sunulmaz.

### Yeniden çalıştırma

**Ubuntu**, Aşama 5'in sabit Python ortamında, task-2 içinde:

```bash
python -B -m unittest discover -s tests -p 'test_*.py' -v
# Yalnız ilk/yeni HPO çıktıları yoksa:
python -B -u optimize.py
python -B predict.py --checkpoint artifacts/optimized/cifar10_optimized.pth \
  --reference results/hpo/optimized_reload_reference.json
```

Mevcut çıktılar varsa optimize durur; hiçbir eski sonucu ezmez. Ayrı tekrar koşusu:

```bash
python -B -u optimize.py --run-dir results/hpo-repeat --candidate-dir artifacts/hpo-repeat \
  --optimized artifacts/optimized/cifar10_optimized_repeat.pth
python -B predict.py --checkpoint artifacts/optimized/cifar10_optimized_repeat.pth \
  --reference results/hpo-repeat/optimized_reload_reference.json
```

Bu makinede gerçekten kullanılan yol, **Ubuntu/WSL** (`wsl -d Ubuntu` ile geçin):

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-2"
docker run --rm --network none --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" \
  --mount "type=bind,source=$PWD/data,target=/work/data,readonly" --workdir /work \
  ee471-week7-cifar10-baseline:latest -B -u optimize.py \
  --run-dir results/hpo-repeat --candidate-dir artifacts/hpo-repeat \
  --optimized artifacts/optimized/cifar10_optimized_repeat.pth
docker run --rm --network none --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work \
  ee471-week7-cifar10-baseline:latest -B predict.py \
  --checkpoint artifacts/optimized/cifar10_optimized.pth \
  --reference results/hpo/optimized_reload_reference.json
```

İlk Docker komutu bir tekrar eğitimidir; tamamlanmış mevcut sonucu yalnız doğrulamak için son predict komutu yeterlidir. Veri cache'i eksikse download=False açık hata verir; bu aşamada indirme yapmayın. Kaynak/sürüm/split/baseline hash uyumsuzsa HPO başlamadan durur. Dataset/ortam/aday ve optimized ağırlıkları ortak ignore kurallarıyla Git dışında kalır. Commit/push/merge yapılmadı.

---

## Aşama 6 — Task 2: CIFAR10 baseline Cog ve website

Mevcut CIFAR10 CNN, 32×32 RGB dönüşümü ve final checkpoint **yeniden eğitim/veri indirme/HPO yapılmadan** servisleştirildi. FashionMNIST kaynakları/checkpoint'leri/ölçümleri/image'ları ve çalışan servisleri korundu. Bu bölüm güncel CIFAR10 servis komutlarıdır; Aşama 5 aşağıda eğitim geçmişi olarak tutulur.

| Servis | Image | Host adresi |
| --- | --- | --- |
| CIFAR10 website | `ee471-week7-cifar10-website` | http://localhost:5074 |
| CIFAR10 baseline Cog | `ee471-week7-cifar10-baseline` | http://localhost:5075 |

Compose projesi **`ee471-week7-cifar10-baseline`**, Task 1'den bağımsızdır. Portlar yalnız `127.0.0.1` üzerinde yayınlanır. **5076 ileride optimized için planlanmıştır; bu aşamada servis/image/kart eklenmedi.** FashionMNIST 5071–5073 ve Week 6 değiştirilmez.

### Build bağlamı, ağırlık ve inference

`prepare_build.py`, `artifacts/baseline/cifar10_last.pth` dosyasını `results/baseline/metrics.json` içindeki hash ile doğrular. Eksik dosyada README'deki açık `train.py` hazırlığına yönlendirir; kendisi eğitim veya indirme yapmaz. Beklenen **SHA256 `60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c`**, boyut **251.454 bayt**.

Üretilen `outputs/build/baseline` bağlamında yalnız Cog config, sabit CPU requirements, `cog_runner.py`, **orijinal `model.py` / `preprocessing.py`**, tek `checkpoint.pth` ve model metadata'sı bulunur. `.dockerignore` allowlist dataset, eğitim/eval kodu, venv, .env, demo/sonuç/geçici dosyaları hariç tutar. Cog'un kendi ürettiği `.cog/` metadata dizini tekrar hazırlamayı engellemez, model girdilerine alınmaz. Git'te ignore edilen checkpoint bu sınırlı bağlama açıkça kopyalanır.

`build.sh` Cog 0.23.1 ile önce model image'ını, sonra website'i build eder. Image içindeki `/src/checkpoint.pth` SHA256 değerini orijinal kayıtla karşılaştırır. Runner setup hash'i tekrar kontrol eder, modeli **CPU'ya bir kez**, eval modunda yükler. Tahmin `torch.inference_mode` kullanır. Orijinal sınıf sırası ve `preprocess` doğrudan import edilir: RGB 32×32, ToTensor, kanal mean/std=(0.5,0.5,0.5). Resize/invert/augmentation veya dataset indirme yoktur. Eksik/yanlış hash'li ağırlıkta açık hata verilir.

Cog `POST /predictions`, `Content-Type: application/json`, `{"input":{"image":"data:image/png;base64,..."}}` veya JPEG data URL kabul eder. Gerçek `status` kontrol edilmelidir. Başarılı `output` biçimi:

```json
{"class":"cat","score":0.44070398807525635,"top3":{"cat":0.44070398807525635,"dog":0.18100601434707642,"bird":0.12535478174686432}}
```

JSON anahtar sırası bir skor sırası sözleşmesi değildir; website skorları azalan sıraya dizer. HTTP 200 içindeki `failed` sonuç başarı sayılmaz. Website top-1 ile top-3 tutarlılığını, sınıf kümesini ve sonlu [0,1] skorları doğrular; ham Cog hata/loglarını kullanıcıya iletmez.

### Website akışı

Tek PNG/JPEG seçimi, gerçek önizleme ve Classify düğmesi → Flask `/api/classify` → Cog'a JSON/data URL. MIME/dosya adı tek başına kullanılmaz: PIL verify + gerçek decode, **tam 32×32 piksel ve en fazla 1 MiB**, toplam multipart istek sınırı 1 MiB+64 KiB. Kullanıcı dosya adı sunucu yolu yapılmaz; dosya kaydedilmeden işlenir.

`BASELINE_URL` yapılandırılabilir; Compose içinde `http://baseline:5000`, containersız varsayılan `http://127.0.0.1:5075`. Tek Baseline kartında en yüksek tahmin ve ilk üç yüzde gösterilir. **Resmi test accuracy %51,41 (10.000 test örneği)** mevcut metrics JSON'undan türetilen `website/baseline_metrics.json` üzerinden ayrı etiketlenir; PNG tahmininin %44,07 skoruyla karıştırılmaz.

Yükleniyor/başarı/hata durumları, çift gönderim engeli, yeni seçimde eski sonucun temizlenmesi, AbortController/eski yanıt koruması ve preview object URL temizliği vardır. Ağ/timeout/busy/başarısız veya bozuk Cog yanıtı açık hata üretir; sınırsız retry yoktur. Backend yanıtı `status` ve `results.baseline` içerir; bu bir model sonucu için de status/error kontrolü gerektirir. Henüz optimized için boş veya sahte alan gösterilmez.

### Build, başlatma ve log

**PowerShell:**

```powershell
wsl -d Ubuntu
```

**Ubuntu/WSL**, mevcut Cog 0.23.1 ve Docker Desktop erişimiyle:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-2"
bash build.sh
docker compose --env-file /dev/null up -d --wait
docker compose --env-file /dev/null ps
```

`build.sh` sırası: `python3 prepare_build.py` → `outputs/build/baseline` içinde `cog build -t ee471-week7-cifar10-baseline --progress plain --use-cog-base-image=false` → image SHA kontrolü → `docker compose --env-file /dev/null build website`. Model servisi `pull_policy: never` kullanır; yerel image yoksa önce build gerekir. Kaynak bind mount edilmez. Website Gunicorn ile container içinde 0.0.0.0:5000 dinler. Cog `/health-check` READY, website `/healthz` 200 healthcheck'leri kullanılır.

**Ubuntu task-2**, ayrı terminalde container içinden canlı log:

```bash
docker compose --env-file /dev/null exec baseline sh
# Container içinde:
tail -f /var/log/ee471/cifar10-baseline.log
# Ctrl+C, sonra exit
```

Setup hash'i, `model=cifar10-baseline`, tahmin başlangıcı, sonuç/ilk üç skor ve süre stdout ile bu dönen log dosyasına yazılır; base64/görsel yazılmaz. Container silinirse dosya kalıcı değildir. İş bitince yalnız CIFAR10 projesini durdurmak için task-2 içinde:

```bash
docker compose --env-file /dev/null down
```

### Aynı PNG ile gerçek kontroller — 2026-11-09

`test_00000_label_3_cat.png` değişmedi. Gerçek etiket **3/cat**; PNG SHA256 `0d4964922e2463ad0e2b1cd298e03d5627ff7dad1ab1cdd173ce35e9974e204f`.

| Yol | Tahmin | cat skoru | dog skoru | bird skoru |
| --- | --- | --- | --- | --- |
| Yerel Python, orijinal checkpoint/modüller | cat | %44,070399 | %18,100601 | %12,535478 |
| Doğrudan Cog HTTP | cat | %44,070399 | %18,100601 | %12,535478 |
| Website backend ve gerçek Chrome kartı | cat | %44,070399 | %18,100601 | %12,535478 |

Skorlar mutlak **1e-7** toleransında eşleşti. HTTP'deki dog skorunun son basamağındaki fark (0.1810060143470764 / Python 0.18100601434707642) JSON sayı serileştirmesinin hassasiyet farkıdır; anlamlı model farkı yoktur. UI iki ondalık yüzde gösterir.

- Gerçek iki image build'i ve Compose up tamamlandı. Cog'un label/schema ekleme adımında `no access allowed to dir "context"` satırı görüldü; image export edildi ve build **exit 0** verdi. Ağırlık SHA'sı, offline CPU/eval setup, aynı model/dönüşüm kaynak hash'leri, eksik/yanlış hash'te hata ve gerçek HTTP tahmini son image'da ayrıca doğrulandı. Dataset/eğitim/geçici dosyaları model image'ında yoktu.
- **17 website mock testi**: yükleme, boyut/format, yapılandırılabilir tek URL, status/error/timeout, geçersiz yanıt ve skor/top-1 tutarlılığı, resmi test etiketi. İlk uyarlamada eski 28×28 kontrolü kaldığı için testler hata verdi; 32×32 düzeltilip tümü geçti.
- **4 mevcut sentetik test** tekrar geçti. İlk test komutundaki yinelenen `python` argümanı düzeltilerek gerçek testler çalıştırıldı; hatalı komut başarı olarak sayılmadı. Bunlar yeniden eğitim veya gerçek accuracy ölçümü değildir.
- **Gerçek model:** yerel Python/Cog/website karşılaştırması, eksik/bozuk yükleme, Cog'da bozuk görselin `failed` durumu ve ardından geçerli tahmin doğrulandı. Website tahmini çalışan container loguna yeni satır ekledi.
- **Gerçek Windows Chrome headless:** gerçek sayfa/model ile üç form gönderimi; önizleme, tek Baseline kartının Cog ile eşleşmesi, çift submit'in tek isteğe dönüşmesi, bozuk görsel sonrası eski sonucu temizleme ve tekrar başarılı kullanım, eksik upload, 375px taşma kontrolü geçti. İki object URL bırakıldı; JS error/unhandledrejection yoktu. Bu kullanıcı tarafından yapılmış manuel masaüstü kontrolü olarak sunulmaz.
- **Postman CLI:** 1 doğrudan Cog isteği, **5 assertion başarılı, 0 hata, exit 0**. `--no-report-events`; login/cloud raporu yok. CLI'nin login uyarısı yerel koşuyu engellemedi. **Masaüstü Postman kullanılmadı.**
- FashionMNIST dahil **85 korunan dosyanın** hash'i aynı kaldı; FashionMNIST'in üç image ID'si ve üç container ID'si değişmedi. FashionMNIST ana sayfa HTTP 200, iki Cog READY kontrolü geçti. Son durumda CIFAR10'un iki servisi ve FashionMNIST'in üç servisi healthy.

Ayrıntılar `task-2/results/service-validation.json`. Ham geçici build/karşılaştırma/tarayıcı dosyaları Git dışındaki `outputs/` içindedir; Aşama 5 ölçümleri korunur.

Tekrar doğrulama, **Ubuntu task-2**:

```bash
python3 -B tests/check_service.py
```

Gerçek sayfa/Chrome kontrolü, **PowerShell repo kökü**:

```powershell
node Week-7/task-2/tests/check_browser.mjs
```

### Postman

**Ubuntu task-2:**

```bash
python3 postman/make_request.py demo_samples/test_00000_label_3_cat.png
curl --fail-with-body http://localhost:5075/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
```

Helper yalnız yerel dosyadan JSON `input.image` data URL gövdesini ve `prediction_body` ortamını üretir; uzun base64 yazdırmaz. `outputs/postman-request.json` ve `outputs/postman-environment.json` Git dışındadır. Pre-request script'in dosya sisteminden keyfî dosya okuduğu varsayılmaz.

**Masaüstü Postman:** `task-2/postman/classifier.postman_collection.json` ve üretilen environment JSON'unu import edin, ortamı seçip Send yapın. İstek doğrudan **5075/predictions** adresine gider; website endpoint'i değildir. `succeeded`, ilk üç sınıf/skor ve top-1 tutarlılığı testlerini gösterin. Bu masaüstü adım henüz yapılmadı.

**PowerShell repo kökü**, CLI kuruluysa:

```powershell
postman collection run Week-7/task-2/postman/classifier.postman_collection.json -e Week-7/task-2/outputs/postman-environment.json --no-report-events
```

### Temiz clone'dan checkpoint hazırlığı

Checkpoint Git'te yoktur; build öncesi **`task-2/artifacts/baseline/cifar10_last.pth`** bulunmalıdır. Önce aynı deneye ait yedeği bu konuma koyup `python3 prepare_build.py` ile SHA doğrulayabilirsiniz. Yedek yoksa Aşama 5 eğitimi build dışında açıkça yeniden üretilir; **aşağıdaki eğitim/veri indirme komutları Aşama 6'da çalıştırılmadı**.

**Ubuntu task-2**, Python 3.12.11 kurulu ortam:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B train.py --run-dir results/reproduced-baseline \
  --checkpoint artifacts/baseline/cifar10_last.pth --demo-dir demo_samples_reproduced
python -B prepare_build.py
bash build.sh
```

Sabit CPU torch 2.6.0+cpu / torchvision 0.21.0+cpu / Pillow 11.1.0 / NumPy 2.3.1, seed42, 45k/5k split, batch4, 2epoch ve SGD(.001,.9) korunmalıdır. Eski ölçüm JSON'ları ve demo dizini ezilmez. Farklı runtime/donanımda bayt düzeyinde aynı checkpoint varsayılmaz: SHA eşleşmezse build durur; yeni ağırlığı eski %51,41 metrik kaydıyla eşleştirmeyin. Yeni deney kökenini ayrı doğrulayın veya orijinal ağırlık yedeğini kullanın. Mevcut checkpoint'i olan bu çalışma alanında yeniden eğitim gerekmez.

### Demo sırası

Build sonundaki `CIFAR10 IMAGE_SHA256_OK` → Compose ps ile iki healthy servis → container logunu tail-f açma → 5074'te aynı cat PNG'siyle Classify → %51,41 resmi test accuracy ile %44,07 tek-PNG skorunu ayırma → 5075'e doğrudan Postman isteği → bozuk dosya/yeniden kullanım. FashionMNIST 5071–5073 çalışmaya devam eder.

---

## Aşama 5 — Task 2: CIFAR10 baseline (eğitim aşaması kaydı)

Bu aşamada yalnız `task-2/` eklendi ve ortak belgeler güncellendi. FashionMNIST dosyaları, iki checkpoint, ölçümler ve üç çalışan servisin kimlikleri/durumları korundu. Yeni HPO, Cog build/servis veya website yoktur; Git add/commit/push/merge yapılmadı.

Kaynak: [resmî PyTorch CIFAR10 tutorial](https://docs.pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html). `model.Net` tutorial'ın küçük CNN'idir: Conv2d(3,6,5) → ReLU → MaxPool(2,2) → Conv2d(6,16,5) → ReLU → MaxPool(2,2) → Flatten → Linear(400,120) → ReLU → Linear(120,84) → ReLU → Linear(84,10), **62.006 parametre**.

`preprocessing.preprocess` hem torchvision veri kümesinde hem PNG inference'ta kullanılır: **32×32 RGB**, ToTensor ile [0,1], kanal başına mean=(0.5,0.5,0.5), std=(0.5,0.5,0.5) ile [-1,1]. Güncel tutorial'daki v2.ToImage/ToDtype(scale=True)/Normalize ile aynı ölçekleme amaçlanır; mevcut sabit torchvision ortamında ToTensor/Normalize kullanıldı. Resize, augmentation, grayscale veya rastgele demo dönüşümü yoktur. Yanlış boyut açıkça reddedilir.

Sınıf sırası gerçek `CIFAR10.classes` ile hem train hem test tarafında assert edildi ve JSON'a kaydedildi: `airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck`. Tutorial'daki plane/car gösterim adları yerine veri kümesinin gerçek airplane/automobile adları kullanılır.

### Sabit deney ve dosyalar

- Resmi 50.000 eğitim örneği, bağımsız `torch.Generator().manual_seed(42)` ile `torch.randperm(50000)`; ilk 45.000 train, son 5.000 validation. NumPy little-endian int64 indeks hash'leri `results/baseline/split.json` ve metrics JSON içinde bulunur. Aynı sıra `common.split_indices(50000,42)` ile yeniden üretilir.
- Python/NumPy/torch seed 42, deterministic algorithms, **CPU / 2 thread**, num_workers=0. Train shuffle için ayrıca seed 42 generator; epoch'lar arasında generator devam eder. Validation/test shuffle=false.
- **2 tam epoch, batch size 4, CrossEntropyLoss, SGD lr=0.001, momentum=0.9**, weight_decay=0, dampening=0, nesterov=false. Scheduler, erken durdurma veya en iyi checkpoint seçimi yoktur. Son epoch CPU state_dict kaydedilir. Test veri kümesi ilk kez bu kayıt sonrasında instantiate edilip ölçülür; test örnekleri indirilen ortak arşivde bulunsa da loader/seçim/eğitimde kullanılmaz.
- Eğitim accuracy/loss'u epoch boyunca değişen ağırlıklarla görülen mini-batch'lerden hesaplanır; validation sabit epoch-sonu modelini kullanır. Loss örnek sayısıyla ağırlıklıdır.
- Mevcut uyumlu runtime: **Python 3.12.11, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0, NumPy 2.3.1**. CPU bağımlılıkları `task-2/requirements.txt` içinde sabittir. Mevcut FashionMNIST image'ı yalnız Python entrypoint'iyle kullanıldı; yeni Cog servisi/build çalıştırılmadı ve model/transform Task 1'den runtime import edilmez.

```text
task-2/
  model.py, preprocessing.py       # ileride Cog'dan import edilebilir
  common.py, engine.py             # seed/split ve örnek ağırlıklı ölçümler
  train.py, evaluate.py            # tam eğitim ve bağımsız test değerlendirme
  predict.py, export_samples.py    # yeniden yükleme ve tahmine göre seçilmeyen PNG'ler
  requirements.txt, tests/test_core.py
  results/baseline/                # ölçüm/split/reload/gerçek çalışma kayıtları
  demo_samples/                   # 10 RGB PNG + manifest
  data/                           # Git dışında veri kümesi
  artifacts/baseline/cifar10_last.pth # Git dışında final checkpoint
  outputs/                        # Git dışında loglar/geçici indirme dosyaları
```

Mevcut ortak `.gitignore` içindeki data/, artifacts/, outputs/, .venv/, *.pth ve önbellek kuralları Task 2'yi de kapsar; gereksiz yeni kural eklenmedi. PNG'ler/manifest ve ölçüm JSON'ları izlenebilir kalır.

### Gerçek tam eğitim sonuçları — 2026-11-09

Bu tablo tam 45.000 train / 5.000 validation koşusudur; smoke test değildir.

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy | Train (s) | Validation (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.708827 | %36.7533 | 1.450157 | %46.9800 | 15.02 | 0.86 |
| 2 | 1.351540 | %51.5000 | 1.333564 | %52.0800 | 15.67 | 0.82 |

Resmi **10.000 test**: loss **1.3332864619**, accuracy **%51.4100**. Checkpoint son epoch'tur; validation/test sonucuna göre değiştirilmedi.

- Yalnız eğitim döngüleri: **30.696 s**.
- Eğitim + validation: **32.379 s**.
- Son test yükleme/değerlendirme: **3.544 s**.
- Doğrulanmış arşiv cache'iyle tam eğitim script'i (cache doğrulama/yükleme, eğitim, validation, son test, PNG export dahil): **56.711 s**.
- İlk indirme başlangıcından eğitim/test/export bitimine gerçek duvar süresi, indirme hazırlığı dahil: **965.755 s**. Veri hazırlığı ile eğitim süresi ayrı tutulur; bağımsız reload/test doğrulaması bu eğitim toplamına dahil değildir.

İlk standart indirme yavaş ilerledi; henüz epoch başlamadan aynı resmî arşiv sınırlı paralel Range istekleriyle hazırlandı. Arşiv MD5'i torchvision 0.21.0'ın `CIFAR10.tgz_md5` değeriyle doğrulandı: `c58f30108f718f92721af3b95e74349a`. İlk indirme denemesindeki yalnız `started` kaydı geçici outputs içine alındı; tam eğitim yeni süreçte doğrulanmış cache ile yalnız bir kez yapıldı. Bu nedenle cache'li script süresi, indirme dahil duvar süresi olarak sunulmaz. Ayrıntılar `results/baseline/execution.json` içindedir.

Checkpoint: **`task-2/artifacts/baseline/cifar10_last.pth`**, **251,454 bayt**, SHA256 `60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c`. Yalnız CPU state_dict; sınıf sırası/dönüşüm/model kaynakları ayrı modüllerdedir.

### PNG export ve ayrı süreçte reload

Resmi test setinde her gerçek sınıfın **ilk indeksli** örneği seçildi; modelin doğru/yanlış tahmini seçime katılmadı. 10 PNG toplam **23,628 bayt**; RGB 32×32. Manifest gerçek etiket/sınıf/test indeksi/dosya/hash/boyut içerir. Her PNG yeniden açılıp aynı test örneğinin normalize edilmiş tensor'uyla birebir karşılaştırıldı.

Ayrı Python süreci `test_00000_label_3_cat.png` dosyasını ve final state_dict'i yeniden yükledi:

- Test indeksi **0**, gerçek etiket **3 / cat**.
- Model tahmini **3 / cat**, softmax skoru **%44.0704**; sonuç **doğru**.
- Checkpoint hash'i ve logitler eğitim sonu referansıyla rtol/atol=1e-6 içinde eşleşti (`reference_verified=true`). Bu skor resmi test accuracy'si değildir.

Dört sentetik birim testi geçti: tutorial normalizasyonu/PNG roundtrip/boyut kontrolü, tekrarlanabilir ayrık split, CNN boyutu/state_dict reload, kısmi batch'te örnek ağırlıklı metrik. Gerçek FashionMNIST/CIFAR10 accuracy kanıtı olarak sunulmaz. Tam eğitim/test ve gerçek ayrı-process reload yukarıda ayrıca kaydedildi.

### Kurulum ve tekrar üretim

**PowerShell**, Ubuntu'ya geçiş:

```powershell
wsl -d Ubuntu
```

**Ubuntu**, uyumlu Python 3.12.11 kuruluysa:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-2"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
# Yalnız temiz/yeni çıktılarda ilk tam koşu:
python -B -u train.py
python -B evaluate.py --checkpoint artifacts/baseline/cifar10_last.pth
python -B predict.py --checkpoint artifacts/baseline/cifar10_last.pth \
  --reference results/baseline/reload_reference.json
```

Bu makinede gerçekten kullanılan mevcut Docker CPU runtime yolu (**Ubuntu task-2 içinde**):

```bash
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work \
  ee471-week7-fashion-baseline:latest -B -u train.py
docker run --rm --network none --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work \
  ee471-week7-fashion-baseline:latest -B evaluate.py
docker run --rm --network none --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work \
  ee471-week7-fashion-baseline:latest -B predict.py \
  --reference results/baseline/reload_reference.json
```

İlk komut eğitim yapar, sonraki iki komut yapmaz. Mevcut sonuçlar varken train.py açık hata ile durur; bu tamamlanmış çalışma alanında eğitimi yeniden başlatmanız gerekmez. İstenirse eski çıktıları ezmeden:

```bash
python -B -u train.py --run-dir results/baseline-repeat \
  --checkpoint artifacts/baseline/cifar10_last_repeat.pth --demo-dir demo_samples_repeat
python -B export_samples.py --output-dir demo_samples_export_repeat
```

Bağımsız evaluate/predict komutları cache'i `download=False` ile açar. Checkpoint, manifest ve model modülleri korunmalıdır. PNG örneği doğrulanmadan etiket veya sonucu değiştirmeyin. Bu aşamada CIFAR10 için HPO/Cog/website yoktur.

---

## Aşama 4 — Baseline / Optimized yan yana servis

İki image **aynı `cog_runner.py`, `model.py`, sınıf sırası ve `preprocessing.py`** kullanır. CPU, 28×28 gri/ToTensor dönüşümü, eval ve inference_mode korunur. Bu aşamada eğitim/HPO yapılmadı; iki checkpoint ve `results/baseline/` ile `results/hpo/` ölçüm JSON'larının SHA256 değerleri değişmedi.

`prepare_build.py` iki checkpoint'i deney kayıtlarındaki SHA256 ile doğrular. Sadece runner, model, dönüşüm, sabit bağımlılıklar, model metadata'sı ve **tek checkpoint** içeren ayrı `outputs/build/baseline` / `optimized` bağlamları hazırlar. Bu dizinler Git dışında kalır. Dataset, eğitim/HPO kodu, .env, venv ve website model image'larına girmez. Git'te ignore edilen ağırlıklar bu kontrollü build bağlamlarına açıkça kopyalanır; `.dockerignore` onları dışlamaz. `build.sh` iki Cog image'ını oluşturduktan sonra her image içindeki `/src/checkpoint.pth` SHA256 değerini yeniden karşılaştırır. Runner setup da metadata hash'ini doğrular; eksik/yanlış ağırlıkta açık hata verir, eğitimi başlatmaz.

| Model | Image | Yerel Cog adresi | Checkpoint SHA256 |
| --- | --- | --- | --- |
| Baseline | `ee471-week7-fashion-baseline` | http://localhost:5072 | `17f629876a1f204cf7bc10d50e0b362c2a2eb12d09fd2cd527f596bb5702e7b2` |
| Optimized | `ee471-week7-fashion-optimized` | http://localhost:5073 | `2b86c814881244614eff20f10a37c2b87a5dceb959d129000e136833016a3409` |

Website: **http://localhost:5071**. Üç port yalnız `127.0.0.1` üzerinde yayınlanır. Mevcut Compose proje adı `ee471-week7-fashion-baseline` korunur; üçüncü servis `optimized` olarak eklenmiştir. Week 6 servislerine dokunulmaz. Model image'ları `pull_policy: never` kullanır; önce yerel Cog build gereklidir.

### Build / başlatma / durdurma

**PowerShell:** Ubuntu terminaline geçin:

```powershell
wsl -d Ubuntu
```

**Ubuntu/WSL:** Cog 0.23.1 ve Docker Desktop erişiminin bulunduğu terminal:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-1"
cog --version
docker version
bash build.sh
docker compose --env-file /dev/null up -d --wait
docker compose --env-file /dev/null ps
# İş bitince yalnız bu Compose projesini durdurur:
docker compose --env-file /dev/null down
```

`build.sh` içinde her model için `outputs/build/<model>` dizininden `cog build -t ee471-week7-fashion-<model> --progress plain --use-cog-base-image=false` çalışır; ardından website build edilir. Python/torch/torchvision/Pillow sürümleri değiştirilmedi. `--env-file /dev/null` yerel gerçek .env yüklemesini önler. Her iki modelin `/health-check` durumu READY, website'in `/healthz` yanıtı 200 olmalıdır. Başka servislerin tuttuğu portları kullanmak için onları durdurmayın.

### Temiz clone ve ağırlıkların hazırlanması

Checkpoint'ler Git'te değildir. Build **öncesi** şu iki dosya bulunmalıdır; her biri 2.681.462 bayttır:

```text
artifacts/baseline/fashion_mnist_last.pth
artifacts/optimized/fashion_mnist_optimized.pth
```

Elinizde bu deneylere ait yerel ağırlık yedeği varsa bu yollara kopyalayın ve `python3 prepare_build.py` ile hash'leri kontrol edin. Model dosyaları yoksa eğitim/HPO, build'in parçası olarak değil **ayrı bir hazırlık işlemi** olarak yeniden üretilebilir. Aşağıdaki komutlar bu Aşama 4 çalışmasında çalıştırılmadı. Aşama 1/3 protokolü ve **Python 3.12.11, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0, NumPy 2.3.1** gereklidir. Python 3.12.11 kurulu Ubuntu ortamında, task-1 içinde:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -c 'import sys; assert sys.version_info[:3] == (3,12,11), sys.version'
python -m pip install -r requirements.txt
# Yeni run dizinleri: korunmuş eski ölçümler ezilmez.
python -B train.py --run-dir results/reproduced-baseline \
  --checkpoint artifacts/baseline/fashion_mnist_last.pth
python -B optimize.py --run-dir results/reproduced-hpo \
  --candidate-dir artifacts/reproduced-hpo \
  --optimized artifacts/optimized/fashion_mnist_optimized.pth
python -B prepare_build.py
```

Train veri kümesini indirir; optimize aynı cache'i kullanır. Seed 42, CPU/2 thread, aynı split/batch sırası ve beş epoch korunmalıdır. Optimize mevcut baseline kayıtlarıyla uyumu denetler; mevcut çıktı dosyalarını ezmez. Başka runtime/donanımdaki tekrarın bayt düzeyinde aynı olacağı varsayılmaz: hash uyuşmazsa build durur. Yeni bir checkpoint'i eski test accuracy'siyle eşleştirmeyin; orijinal ağırlıkları temin edin veya yeni deneyin checkpoint/ölçüm kökenini ayrı doğrulayın. Bu demo build'i korunmuş orijinal deneylerin hash'lerini gerektirir. Mevcut dosyaları olan bu çalışma alanında bu yeniden üretim komutlarını çalıştırmanız gerekmez.

### Website veri akışı ve sonuç sözleşmesi

Tek dosya/tek Classify → Flask doğrulaması → **aynı data URL** ile iki bağımsız, en fazla iki eşzamanlı Cog isteği. `BASELINE_URL` ve `OPTIMIZED_URL` yapılandırılabilir; Compose içinde `http://baseline:5000` / `http://optimized:5000` kullanılır. Her modelin JSON `status/output/error` sonucu ayrı kontrol edilir. HTTP 200 tek başına tahmin başarısı sayılmaz.

Website `/api/classify` yanıtı `status: succeeded|partial|failed` ve `results.baseline`, `results.optimized` içerir. Her kart sonucu `{status: succeeded, output: {sınıf: skor, ...}}` veya `{status: failed, error: güvenli mesaj, http_status: kaynak hata kodu}` olur. Karşılaştırma tamamlandıysa HTTP 200 içinde kart durumları okunur; yükleme doğrulaması 400/413 JSON hata döndürür. Tek servis hatası başarılı kartı silmez. Her yeni seçim/istek eski sonuç ve hataları temizler; aynı anda tekrar gönderim engellenir, eski istekler iptal edilir ve preview URL'leri bırakılır.

PNG/JPEG gerçek içerikten doğrulanır; **tam 28×28 piksel, en fazla 1 MiB**. Resize/invert yoktur. Kartlar masaüstünde yan yana, dar ekranda alt alta görünür. İlk üç skor yüzdeye çevrilir; yeniden normalize edilmez. **Resmi test accuracy** ayrı etiketlidir: baseline %63,37 (`results/baseline/metrics.json:test`), optimized %87,34 (`results/hpo/summary.json:winner_test`), her biri 10.000 test örneği. Website için ölçümlerin küçük türetilmiş kopyaları kullanılır; optimized kopyası build hazırlığında kaynaktan üretilir. Bunlar yüklenen tek PNG'nin tahmin skoru değildir.

### İki canlı log

**Ubuntu**, task-1 içinde ayrı terminaller:

```bash
docker compose --env-file /dev/null exec baseline sh
# Container içinde:
tail -f /var/log/ee471/fashion-baseline.log
```

```bash
docker compose --env-file /dev/null exec optimized sh
# Container içinde:
tail -f /var/log/ee471/fashion-optimized.log
```

Loglar stdout ve bu dosyalara yazılır; model adı, setup checkpoint hash'i, tahmin/süre/ilk üç skor bulunur. Görsel/base64 yazılmaz. Log dosyaları container katmanındadır, container silinirse kalıcı kalmaz. `Ctrl+C`, sonra `exit` ile çıkılır.

### Aynı PNG ile gerçek doğrulama — 2026-11-09

Örnek değiştirilmedi: `demo_samples/test_00000_label_9_ankle_boot.png`, resmi test index 0, gerçek sınıf Ankle boot. Görsel SHA256: `cc22f44180c393601df7c2b9e5946b59e431ea747aff0d7bc223f8896a71548e`.

| Model | Ankle boot | Sneaker | Sandal | Python / Cog / website |
| --- | --- | --- | --- | --- |
| Baseline | %36,585566 | %26,088428 | %18,198948 | Aynı ilk üç sınıf; mutlak tolerans 1e-7 içinde |
| Optimized | %99,072087 | %0,730217 | %0,197075 | Aynı ilk üç sınıf; mutlak tolerans 1e-7 içinde |

İki modelin aynı sınıfı tahmin etmesi geçerlidir; farklı sonuç elde etmek için örnek aranmadı. Gerçek build çıkış kodu 0; image içi hash kontrolleri geçti. Cog'un label/schema ekleme adımında `no access allowed to dir "context"` satırı görüldü; buna rağmen iki image export edildi, build 0 döndü. Bu satır gizlenmedi; son image'larda offline CPU setup, kaynak/ağırlık hash'leri ve gerçek HTTP tahminleri ayrıca doğrulandı.

- **16 website testi:** Cog HTTP mock; giriş doğrulaması, iki adres/aynı payload, kısmi hata, güvenli hatalar, timeout ve tekrar kullanım. Gerçek inference kanıtı değildir.
- **7 mevcut çekirdek/seçim testi:** sentetik veriler/politika. FashionMNIST yeniden eğitimi/HPO yapılmadı.
- **Gerçek Docker/model:** her image'da yalnız doğru checkpoint; ortak kaynak SHA'ları aynı; dataset/eğitim kodu hariç; network kapalı setup, CPU/eval, eksik ve hash'i yanlış ağırlıkta hata. Yerel Python/Cog/website karşılaştırması ve her iki logda yeni tahmin doğrulandı. Eksik/bozuk yükleme sonrası başarılı istek alındı.
- **Gerçek Chrome headless:** gerçek sayfa ve gerçek Cog ile beş form gönderimi; preview, her iki kartın gerçek Cog skorları, çift gönderim engeli, bozuk dosya sonrası toparlanma, optimized servisini gerçekten durdurunca baseline sonucunun kalması ve modele özel hata, servisi yeniden başlatınca iki kartın toparlanması. 375 pikselde tek sütun/taşma yok; iki preview URL bırakıldı; JS error/unhandledrejection yok.
- **Postman CLI 1.85.0:** iki doğrudan Cog isteği, **8 assertion geçti**, 0 hata, exit 0, `--no-report-events`; masaüstü Postman kullanılmadı. CLI'nin login/cloud yayın uyarısı yerel doğrulamayı engellemedi; login/publish yapılmadı.
- Son durumda website/baseline/optimized **healthy** bırakıldı. Week 6 servislerine dokunulmadı. Ayrıntılar `results/comparison-validation.json`; Aşama 2/3 ölçüm kayıtları korunur.

Tekrar doğrulama, **Ubuntu task-1**:

```bash
python3 -B tests/check_comparison_service.py
# Windows Chrome kontrolü, repo kökünde PowerShell:
```

```powershell
node Week-7/task-1/tests/check_browser.mjs
```

Yerel Python karşılaştırma yardımcısı bu makinedeki `ee471-week6-classifier:latest` image'ını yalnız CPU Python runtime olarak kullanır; Week 6 servislerini başlatmaz/değiştirmez. Uygulama image'larının Week 6'ya çalışma zamanı bağımlılığı yoktur. Bu image yoksa Aşama 1'in sabit Python ortamında `python -B tests/local_prediction.py --model baseline` ve `--model optimized` ile aynı kontrol yapılabilir. Headless kontrol kısa süre yalnız bu projenin optimized servisini durdurur ve finally içinde geri başlatır.

### Postman ve doğrudan HTTP

**Ubuntu task-1:** tek PNG'den iki isteğin paylaşacağı gövde/ortamı üretin:

```bash
python3 postman/make_request.py demo_samples/test_00000_label_9_ankle_boot.png
curl --fail-with-body http://localhost:5072/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
curl --fail-with-body http://localhost:5073/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
```

**Masaüstü Postman:** `postman/classifier.postman_collection.json` ve `outputs/postman-environment.json` dosyalarını içe aktarın, ortamı seçin. Baseline ve Optimized isteklerini Send ile sırayla çalıştırın. İkisi de aynı `prediction_body` değişkenini kullanır; hedefler doğrudan 5072/5073 `/predictions` adresleridir, website endpoint'i değildir. Uzun base64 elle yazılmaz; pre-request script yerel dosya okumaz. Üretilen iki JSON `outputs/` altında Git dışındadır, paylaşmayın. Masaüstü adımı kullanıcıya kalmıştır.

CLI kuruluysa **PowerShell repo kökü:**

```powershell
postman collection run Week-7/task-1/postman/classifier.postman_collection.json -e Week-7/task-1/outputs/postman-environment.json --no-report-events
```

### Task-1-demo.avi sırası

1. İki checkpoint yolunu ve `bash build.sh` sonundaki iki `IMAGE_SHA256_OK` satırını gösterin; yeniden eğitim başlatmayın.
2. Compose up/ps ile üç healthy servisi ve 5071/5072/5073 adreslerini gösterin.
3. İki container içindeki logları ayrı terminallerde `tail -f` açın.
4. Website'e aynı ankle boot PNG'sini yükleyip tek Classify ile iki kartı gösterin. %63,37/%87,34 resmi test accuracy'si ile bu PNG'nin %36,59/%99,07 skorlarını ayırın.
5. Aynı gövdeyi kullanan iki Postman isteğinin succeeded/ilk üç skorunu gösterin. CLI doğrulamasını masaüstü Send işlemi yerine anlatmayın.
6. İsterseniz bozuk dosya/hata sonrası geçerli PNG ile tekrar kullanımı gösterin. Durdurma demosu yapılırsa üç servisi tekrar healthy bırakın.

---

## Aşama 3 — Kontrollü hiperparametre optimizasyonu (aşama kaydı)

`task-1/optimize.py` yalnız belirtilen dört adayı sıfırdan eğitir. Baseline kaydı uyumlu bulunduğu için SGD lr=0.001 yeniden eğitilmedi; mevcut epoch-5 validation ve test ölçümü referans alındı. Website/Cog dosyaları veya çalışan servisler bu aşamada değiştirilmedi. Optimizasyon sonucu henüz siteden sunulmaz.

### Kontrol edilen protokol

- Aynı orijinal `NeuralNetwork` MLP, `preprocess`, CrossEntropyLoss ve `engine.run_epoch` kullanıldı; augmentation/resize/invert/normalization eklenmedi.
- Resmi eğitim setinden aynı seed 42 ile üretilen **54.000 train / 6.000 validation** indeksleri, baseline `split.json` hash'leriyle eşleşti. Resmi test aday eğitimi veya karar sırasında kullanılmadı.
- Her aday başlangıcında Python/NumPy/torch seed 42 ve deterministic algorithms yeniden uygulandı; model sıfırdan oluşturuldu. Aynı başlangıç state hash'i dört adayda doğrulandı.
- Her adayın shuffle generator'ı seed 42 ile yeniden oluşturuldu; generator epoch'lar arasında devam etti. CPU/2 thread, batch 64, num_workers=0 ve **5 tam epoch** sabit kaldı.
- Gerçek tüketilen train indeksleri RNG'yi değiştirmeyen `TrackedSubset` ile kaydedildi. **20 epoch sıra hash'i** baseline'ın aynı loader/seed protokolünden yeniden türetilen beş sıra hash'iyle eşleşti. Eski baseline eğitiminde batch trace'i kaydedilmediğinden bu geçmişte ölçülmüş bir baseline hash'i gibi sunulmaz.
- Python 3.12.11, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0, NumPy 2.3.1; aynı mevcut CPU image'ı Python entrypoint'iyle kullanıldı. Image build/Cog çalıştırma/deploy yapılmadı. Baseline konfigürasyonu, kaynak hash'leri, sürümler, split ve checkpoint SHA kontrolü `baseline_audit` alanındadır.

SGD adayları: momentum=0, dampening=0, weight_decay=0, nesterov=false. Adam adayları: betas=(0.9,0.999), eps=1e-8, weight_decay=0, amsgrad=false. Gerçek optimizer defaults (`foreach`, `fused` vb. dahil) her trial JSON'unda bulunur. `summary.json` içindeki `protocol` referans baseline ayarlarını tutar; adayların farklı optimizer/lr değerleri kendi trial kayıtlarındadır. Scheduler/erken durdurma yoktur.

### Ölçülen sonuçlar — 2026-11-09

Karşılaştırılan değerler her adayın **5. epoch** metrikleridir; en iyi ara epoch seçilmedi. Süreler train + validation döngülerini içerir.

| Ayar | Epoch-5 train loss | Train accuracy | Validation loss | Validation accuracy | Süre (s) |
| --- | --- | --- | --- | --- | --- |
| SGD 0.001 — mevcut referans | 1.243355 | %63.5519 | 1.165968 | %63.4167 | 14.34 — önceki koşu |
| SGD 0.01 | 0.495864 | %82.7000 | 0.501816 | %83.0000 | 14.27 |
| SGD 0.05 | 0.368976 | %86.7204 | 0.375805 | %86.8333 | 14.42 |
| Adam 0.0003 | 0.290397 | %89.2333 | 0.323389 | %87.9000 | 19.16 |
| **Adam 0.001** | **0.281395** | **%89.4222** | **0.330351** | **%88.1000** | **22.03** |

Dört yeni adayın toplam train+validation süresi **69.8757 s**; aday checkpoint'leri, seçim ve kazananın test ölçümü dahil arama süresi **70.8226 s** idi (ön denetim/veri yükleme bu arama sayacından önceydi). Baseline'ın önceki 14.3382 saniyesi yeni toplamın parçası değildir.

Seçim kuralı: en yüksek epoch-5 validation accuracy; eşitlikte daha düşük epoch-5 validation loss. Tam eşitlik kalırsa listedeki ilk aday korunur. **Adam lr=0.001** %88.10 ile seçildi. Adam 0.0003 daha düşük validation loss verse de accuracy'si %87.90 olduğu için seçilmedi. `selection.json` kararı **resmi test loader'ı oluşturulmadan önce** yazılıp donduruldu. Ankle boot demo görseli de seçime katılmadı.

Yalnız kazanan aday, seçimden sonra resmi **10.000** test örneğinde CPU/batch 64/shuffle=false ve aynı örnek ağırlıklı eval fonksiyonuyla ölçüldü:

| Model | Resmi test loss | Resmi test accuracy |
| --- | --- | --- |
| Baseline SGD 0.001 — mevcut kayıt | 1.1639250301 | %63.37 |
| Seçilen Adam 0.001 | 0.3484593021 | %87.34 |

**Test accuracy artışı: +23.97 yüzde puan** (%63.37 → %87.34). Validation accuracy artışı +24.6833 yüzde puandır. Test loss farkı optimized − baseline = **−0.8154657280**. Bu koşuda hem validation hem test accuracy iyileşti. Test sonuçları kazananı değiştirmek veya yeni bir aday eklemek için kullanılmadı; bu sonuç dört belirtilen adayın seed 42 koşusuna aittir.

### Kayıtlar ve optimized checkpoint

```text
task-1/
  optimize.py
  tests/test_selection.py
  results/hpo/
    summary.json                      # protokol/audit, tüm epoch'lar, süreler, karşılaştırma
    selection.json                    # test öncesi dondurulmuş validation seçimi
    trials/sgd_lr_0_01.json
    trials/sgd_lr_0_05.json
    trials/adam_lr_0_0003.json
    trials/adam_lr_0_001.json
    optimized_reload_reference.json
    optimized_reload_check.json
  artifacts/hpo/*_last.pth             # adayların 5. epoch state_dict'leri; Git dışında
  artifacts/optimized/fashion_mnist_optimized.pth
```

Her trial JSON'u beş epoch'un train/validation loss/accuracy'sini, epoch sürelerini, toplam süreyi, son epoch metriklerini, ayarları, başlangıç/sıra/checkpoint hash'lerini kaydeder. Trial `test` alanları null kalır; tek kazanan test ölçümü `summary.json/winner_test` içindedir. Küçük JSON sonuçları izlenebilir; dataset ve tüm ağırlıklar Git dışındadır.

Optimized checkpoint: **`task-1/artifacts/optimized/fashion_mnist_optimized.pth`**, **2.681.462 bayt**, CPU `state_dict only`. SHA-256: `2b86c814881244614eff20f10a37c2b87a5dceb959d129000e136833016a3409`. Kazananın epoch-5 checkpoint'i buraya byte olarak kopyalandı; baseline dosyası değişmedi. Mevcut `evaluate.load_model()` ve `predict.py` doğrudan yükleyebilir.

Ayrı yeni süreçte orijinal ankle boot PNG'siyle optimized inference doğrulandı: gerçek sınıf **9 / Ankle boot**, tahmin **9 / Ankle boot**, softmax skoru **0.9907208681 (%99.0721)**. Checkpoint hash'i ve logits seçim sonrası referansla eşleşti (`reference_verified=true`). Bu tek örneğin skoru, genel test accuracy'si değildir ve model seçimi için kullanılmadı.

### Tekrar çalıştırma komutları

Yerel Aşama 1 venv ortamı kuruluysa, **Ubuntu**, `Week-7/task-1` içinde ilk/yeni koşu:

```bash
python -B tests/test_selection.py -v
python -B -u optimize.py
python -B predict.py --checkpoint artifacts/optimized/fashion_mnist_optimized.pth \
  --image demo_samples/test_00000_label_9_ankle_boot.png \
  --reference results/hpo/optimized_reload_reference.json \
  --output results/hpo/optimized_reload_check.json
```

Mevcut deneyler bulunduğunda optimize.py durur; önceki sonuçları/checkpoint'leri silmez veya ezmez. Yeniden tam koşu için **yeni yollar** verin:

```bash
python -B -u optimize.py --run-dir results/hpo-repeat --candidate-dir artifacts/hpo-repeat \
  --optimized artifacts/optimized/fashion_mnist_optimized_repeat.pth
```

Gerçekte kullanılan **Ubuntu/WSL Docker** yolu (PowerShell'den `wsl -d Ubuntu` ile geçin):

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7"
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work/task-1 \
  ee471-week6-classifier:latest -B -u optimize.py \
  --run-dir results/hpo-repeat --candidate-dir artifacts/hpo-repeat \
  --optimized artifacts/optimized/fashion_mnist_optimized_repeat.pth
```

Burada mevcut image yalnız Python/CPU ortamıdır; Cog server/build yoktur. Optimize komutu cached dataset'i `download=False` ile kullanır; cache eksikse önce Aşama 1 veri hazırlığını tamamlayın. Bir baseline uyumsuzluğu varsa deney başlamadan durur. Tekrar koşunun demo kontrolünde `--reference results/hpo-repeat/optimized_reload_reference.json` kullanın; mevcut deneyin doğrulaması için yukarıdaki normal checkpoint/reference yollarını kullanın.

Üç sentetik seçim testi geçti: test skoru/ara-epoch zirvesinin seçimi etkilememesi, accuracy eşitliğinde loss kuralı ve eksik/nonfinite metrik reddi. Gerçek koşuda dört başlangıç hash'i ve 20 batch sıra hash'i eşleşti. Baseline dahil önceden var olan 48 task-1 dosyasının hash'i değişmedi; iki Compose container kimliği aynı ve healthy kaldı. Yeni HPO için website/Cog/CIFAR10 veya Git commit/push/merge yapılmadı.

## Aşama 2 — Cog baseline servisi ve website (aşama kaydı)

Yeni dosyalar `task-1/` altında: `cog.yaml`, `cog_runner.py`, `.dockerignore`, `build.sh`, `compose.yaml`, `website/`, `postman/`, servis/tarayıcı kontrolleri ve `results/service-validation.json`. Aşağıdaki Aşama 1 dosyaları ve ölçümleri korunmuştur.

### Build ve başlatma

**PowerShell:** Docker Desktop açıkken Ubuntu'ya geçin:

```powershell
wsl -d Ubuntu
```

**Ubuntu terminali:**

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-1"
bash build.sh
docker compose --env-file /dev/null up -d --no-build --pull never --wait --wait-timeout 120
docker compose --env-file /dev/null ps
```

- Website: **http://localhost:5071**
- Cog API: **http://localhost:5072/predictions**
- Health: `http://localhost:5072/health-check`; READY beklenir.
- Host bind'leri yalnız `127.0.0.1`; iki container içinde port 5000.
- Compose projesi `ee471-week7-fashion-baseline`; Week 6 projeleri ve portlarıyla bağımsızdır. Geliştirme başında 5071/5072 boştu; bu portlarla gerçek başlatma başarılı oldu.

`build.sh` önce mevcut `artifacts/baseline/fashion_mnist_last.pth` dosyasını kontrol eder, sonra `cog build -t ee471-week7-fashion-baseline --progress plain --use-cog-base-image=false` ve website Docker build'i çalıştırır. Eksik dosyada açık hata/README üretim talimatıyla durur; eğitim veya indirme başlatmaz. Checkpoint başka makinede yoksa Aşama 1 üretimini ayrı `results/reproduced-baseline` run diziniyle yapabilirsiniz; mevcut baseline metriklerini ezmeyin. Build/servis başlangıcında eğitim yapılmaz.

Cog bağlamı **task-1 köküdür**. `.dockerignore` yalnız Cog config/requirements, `model.py`, `preprocessing.py`, `cog_runner.py` ve final checkpoint'i dahil eder. Git'te ignore edilen checkpoint, Docker allowlist'inde açıkça dahil edilmiştir; Git ignore, Docker ignore değildir. Dataset, train/evaluate script'leri, sanal ortamlar, sonuçlar, demo örnekleri ve website Cog image'ına girmez. Image içinde gerçek dosya SHA-256'sı orijinal `17f629...5702e7b2` ile eşleştirilerek doğrulandı. Model/dönüşüm dosyaları kopya bir ikinci tanımdan değil, orijinal modüllerden import edilir.

Cog 0.23.1 CLI/SDK, Python 3.12.11 ve mevcut CPU requirements sürümleri kullanılır. `Runner.setup()` state_dict'i CPU'ya bir kez yükler ve `eval()` yapar. `run()` orijinal preprocess'i ve `inference_mode()` kullanır; softmax'ten en yüksek üç sınıf/skoru `{sınıf: skor}` olarak döndürür. Dataset sınıf sırası korunur. Eksik checkpoint için servis de açık hata verir; rastgele ağırlık veya runtime eğitim yoktur.

Website ayrı bir Flask/gunicorn image'ıdır; model/Torch bağımlılığı taşımaz. `BASELINE_URL` yapılandırılabilir; Compose içinde `http://baseline:5000`, standalone varsayılanı `http://127.0.0.1:5072` olur. Sonraki aşamada ikinci servis eklenebilir; şu anda optimized sonuç veya sahte skor yoktur.

### Görsel ve sonuç sözleşmesi

`demo_samples/test_00000_label_9_ankle_boot.png` gibi dataset'e uygun **28×28 FashionMNIST PNG** kullanın. Website gerçek PNG/JPEG yapı/decode kontrolü, tam 28×28 boyut ve **1 MiB** sınırı uygular. Uzantı/MIME tek başına kabul edilmez; kullanıcı dosya adı sunucu yoluna dönüşmez. Tarayıcıda büyütülmüş önizleme sadece görsel sunumdur; model girdisi yeniden boyutlandırılmaz/invert edilmez. Griye dönüşüm ve ToTensor eğitimle aynı modüldedir. Normal kıyafet fotoğrafı aynı veri dağılımı sayılmaz.

Tarayıcı `POST /api/classify` multipart `image` gönderir. Website Cog'a **JSON** `input.image` data URL gönderir; Cog'a multipart gitmez. Cog HTTP 200 döndürse bile `status: failed` başarı değildir. Website succeeded ve üç geçerli 0–1 skorunu doğrular; raw Cog error/log alanlarını istemciye yansıtmaz. Timeout/bağlantı/hazır değil/bozuk yanıt hataları ayrı görünür; sınırsız veya otomatik retry yoktur. Yeni seçim eski sonucu/preview URL'sini temizler, işlem sırasında çift gönderim engellenir.

Sayfadaki **Recorded official test accuracy: 63.37% (10000 images)** değeri korunmuş `results/baseline/metrics.json` kaydından türetilen `website/baseline_metrics.json` içindedir. Bu held-out test ölçümüdür. **Baseline prediction** altındaki yüzde ise yüklenen tek görselin softmax skorudur; bu iki sayı ayrı etiketlenir. İlk üç skor toplamı 1 olmak zorunda değildir; skorlar yeniden normalize edilmez.

### Doğrudan HTTP ve Postman

**Ubuntu**, `task-1` içinde aynı PNG'den yerel JSON/environment üretin:

```bash
python3 postman/make_request.py demo_samples/test_00000_label_9_ankle_boot.png
curl --fail-with-body http://localhost:5072/predictions \
  -H 'Content-Type: application/json' --data-binary @outputs/postman-request.json
```

Yardımcı standart Python kütüphanesini kullanır, base64'ü terminale yazdırmaz. `outputs/postman-request.json` JSON gövdesidir; `outputs/postman-environment.json` aynı gövdeyi `prediction_body` değişkeninde tutar. Boyut/signature kontrolü yapar; tam görsel doğrulaması website/Cog'dadır. Üretilen payload/environment ve JPEG test dönüşümü Git dışındadır.

Postman masaüstünde:

1. `postman/classifier.postman_collection.json` ve üretilen environment JSON'unu import edin.
2. **EE471 Week 7 FashionMNIST - local image (do not share)** environment'ini seçin.
3. **Classify 28x28 FashionMNIST image** isteğinde URL `http://localhost:5072/predictions`, Content-Type `application/json`, raw body `{{prediction_body}}` olsun.
4. Send ile `status: succeeded`, gerçek üç skor ve dört assertion sonucunu gösterin. İstek website'e gitmez.

Alternatif olarak Body → binary ile `postman-request.json` seçilebilir; bu dosya data URL içeren **JSON**'dur, doğrudan PNG veya multipart değildir. Postman script'i bilgisayardan keyfî dosya okumaz.

Bu aşamada **Postman CLI 1.85.0** gerçek localhost endpoint'inde çalıştırıldı: 1 request, 4 assertion, 0 failure, exit 0. **Masaüstü Postman uygulamasında Send yapılmadı.** CLI kullanılacaksa **PowerShell**, `Week-7/task-1` içinde:

```powershell
postman collection run postman/classifier.postman_collection.json -e outputs/postman-environment.json --no-report-events
```

CLI `--output` seçeneği oturum açma istedi; kullanılmadan yerel run başarılı oldu. Login, workspace publish veya CLI upgrade yapılmadı; buluta raporlama kapalıydı. Import edilebilir önceki v2.1 JSON collection biçimi korundu; kurulu CLI'nin v3-only lint'i bu JSON biçimi için kullanılmadı. JSON sözdizimi ve gerçek collection assertions ayrı doğrulandı.

### Container içinde canlı log

**Ubuntu**, `task-1` içinde:

```bash
docker compose --env-file /dev/null exec baseline sh
```

**Container shell'inde:**

```sh
tail -f /var/log/ee471/fashion-baseline.log
```

Website'ten yeni tahmin yaptırınca başlangıç, sınıf/skor ve süre içeren gerçek satır gelir. Örnek gerçek satır:

```text
Prediction completed in 0.002276s; top3={"Ankle boot": 0.3658556640148163, "Sneaker": 0.26088428497314453, "Sandal": 0.18198947608470917}
```

`Ctrl+C`, sonra `exit` ile çıkın. Kayıt stdout'a ve bu rotasyonlu dosyaya gider (1 MiB, iki yedek); görsel/base64 loglanmaz. Container kaldırılırsa bu dosya da kaldırılır. Salt görüntüleme: `docker compose --env-file /dev/null exec -T baseline tail -n 10 /var/log/ee471/fashion-baseline.log`.

### Gerçek karşılaştırma — 2026-11-09

PNG: `test_00000_label_9_ankle_boot.png`, resmi test indeksi **0**, gerçek etiket **9 / Ankle boot**. Değerler aynı PNG, aynı checkpoint ve aynı dönüşüm içindir:

| Sınıf | Yerel Python | Cog HTTP | Website API |
| --- | --- | --- | --- |
| Ankle boot | 0.3658556640 | 0.3658556640 | 0.3658556640 |
| Sneaker | 0.2608842850 | 0.2608842850 | 0.2608842850 |
| Sandal | 0.1819894761 | 0.1819894761 | 0.1819894761 |

Üç akışın etiketleri/skorları eşleşti (`atol=1e-7`); UI aynı değerleri **%36.59 / %26.09 / %18.20** gösterdi. Yeni kayıt `results/service-validation.json` içindedir; Aşama 1 `results/baseline/` dosyaları değiştirilmedi.

- Her iki image gerçekten build edildi; Compose'da baseline ve website healthy olarak **açık bırakıldı**.
- Ağsız yeni image'da checkpoint SHA, CPU/eval setup, eksik checkpoint hatası ve dataset/eğitim kaynaklarının image'da bulunmadığı kontrol edildi.
- Website için **14 mock HTTP testi** geçti (28×28 JPEG/PNG, upload boyutu, invalid schema/status, timeout/busy ve toparlanma). Bunlar gerçek model testi olarak sunulmaz.
- Gerçek HTTP'de bozuk/boş website upload'ı 400 verdi. Doğrudan Cog bozuk data URL'yi HTTP 200 / `status: failed` olarak reddetti; sonraki geçerli tahmin başarılı oldu. JPEG desteği de gerçek 28×28 JPEG ile kontrol edildi; kayıplı JPEG'in skorlarının orijinal PNG ile aynı olduğu iddia edilmez.
- Website isteğiyle çalışan model logundaki tamamlanan tahmin sayısı tam bir arttı; dosyada base64 yoktu. Gösterilen log satırı gerçek container'dan okundu.
- **Gerçek Windows Chrome headless**, CDP üzerinden gerçek file input ve form olaylarını kullandı: preview, üç gerçek form submit (geçerli/bozuk/toparlanma), Cog ile yüzde eşleşmesi, ayrı test accuracy etiketi, çift gönderimi engelleme, eski sonucu temizleme, iki object URL'nin serbest bırakılması, eksik upload ve 375 px görünüm kontrol edildi; JavaScript hata/unhandledrejection listesi boştu. Bu headless otomasyon olup insanın yaptığı manuel UI incelemesi değildir.
- Postman CLI'de dört kontrol geçti: HTTP 200, gerçekten succeeded, üç geçerli skor ve eğitim sınıf kümesi. Masaüstü Postman kontrolü kullanıcıya kaldı.
- Aşama 2'nin başlangıç hash snapshot'ı ile Week 6 kaynakları, baseline kaynakları, checkpoint, metrikler ve demo dosyaları korunmuştu. O aşamada yeniden eğitim, HPO, CIFAR10, commit/push/merge veya registry push yapılmamıştı. HPO devamı üstteki Aşama 3 kaydındadır.

Kontrolleri tekrar etmek için (**Ubuntu**, servisler açıkken `task-1` içinde):

```bash
python3 tests/check_baseline_service.py
```

Bu kontrol yeni skor üretir; eğitim yapmaz ve Week 6 servislerini durdurmaz. Gerçek tarayıcı kontrolü (**Windows PowerShell**, repo kökünden Node.js 22/Chrome ile):

```powershell
node Week-7/task-1/tests/check_browser.mjs
```

Durdurma (**Ubuntu**, `task-1` içinde):

```bash
docker compose --env-file /dev/null stop
# Yalnız bu projenin container/ağını kaldırmak için:
docker compose --env-file /dev/null down
```

Demo sırası: build → compose ps → website'ten aynı PNG ile tahmin → container shell'de canlı log → aynı PNG JSON'u ile Postman Send → bozuk dosya ve toparlanma. Base64 metninin tamamını ekranda gezdirmeye gerek yoktur.

## Aşama 1 — Korunan eğitim dosyaları

```text
Week-7/
  .gitignore
  README.md
  PROMPTS.md
  task-1/
    requirements.txt
    model.py                 # import edilebilir Quickstart MLP
    preprocessing.py         # eğitim ve inference için aynı dönüşüm/sınıflar
    common.py                # seed, split, hash ve metadata
    engine.py                # eğitim/eval ve örnek ağırlıklı metrikler
    train.py
    evaluate.py
    predict.py
    export_samples.py
    tests/test_core.py
    results/baseline/         # ölçülen sonuçlar ve yeniden yükleme kanıtı
    demo_samples/            # 10 küçük PNG ve gerçek etiket manifest'i
    data/                    # Git dışında, torchvision veri cache'i
    artifacts/baseline/      # Git dışında, final state_dict
```

`model.py` ve `preprocessing.py` import etmek eğitim, indirme veya sunucu başlatmaz. Aşama 1'de Cog runner/build, website veya yeni image oluşturulmamıştı; Aşama 2 runner'ı bu modülleri aynen kullanır.

## Deney sözleşmesi

| Ayar | Değer |
| --- | --- |
| Girdi | 28×28, L/grayscale, float32 `[1,28,28]`, `[0,1]` |
| Dönüşüm | grayscale + `ToTensor`; normalize/augmentation/invert yok |
| Model | Flatten → Linear(784,512) → ReLU → Linear(512,512) → ReLU → Linear(512,10) |
| Loss / optimizer | CrossEntropyLoss / SGD |
| Learning rate | 0.001 |
| Batch size / epoch | 64 / 5 |
| Momentum / weight decay | 0 / 0 |
| Seed | 42; Python/NumPy/torch, deterministic algorithms |
| Bölme | Resmi 60.000 eğitim örneğinden %90 = 54.000 train, %10 = 6.000 validation |
| Split yöntemi | bağımsız seed'li `torch.randperm`; ilk %90 train, kalanı validation |
| Resmi test | ayrı 10.000 örnek; epoch/hiperparametre/checkpoint seçimine katılmadı |
| Checkpoint | beşinci/son epoch; best validation veya test seçimi yok |
| Cihaz | CPU, 2 torch thread, DataLoader workers=0 |

Train loader ayrı seed'li generator ile shuffle edilir; validation/test shuffle edilmez. Split için kullanılan generator model initialization RNG'sini tüketmez. Ayrık split indekslerinin hash'leri `results/baseline/split.json` içinde tutulur; aynı sürüm/seed/yöntemle yeniden oluşturulur.

`engine.py`, son kısa batch dahil loss'u örnek sayısıyla ağırlıklandırır. Train metrikleri epoch boyunca güncellenen modelin batch sonuçlarından hesaplanır; validation/test `eval()` ve `inference_mode()` ile hesaplanır. Validation her epoch sonunda, test ise eğitim bittikten sonra ölçülür. Bağımsız CLI kontrolünde aynı final checkpoint test setinde tekrar değerlendirilmiştir; bu ikinci ölçüm seçim/yeniden eğitim için kullanılmamıştır.

Inference aynı `preprocess()` fonksiyonunu kullanır: griye dönüşüm ve ToTensor. 28×28 olmayan görsel açık hata verir; bu ilk sürüm yeniden boyutlandırma, merkezleme veya arka plan düzeltmesi uygulamaz. Kendi kıyafet fotoğrafınızın FashionMNIST test örneğiyle aynı dağılımda olduğu varsayılmaz.

## Uyumlu ortam ve kurulum

[Resmi PyTorch sürüm tablosu](https://pytorch.org/get-started/previous-versions/#v260) torch 2.6.0 / torchvision 0.21.0 eşleşmesini ve CPU index'ini doğrular. `requirements.txt` CPU wheel'lerini açık `+cpu` sürümleriyle sabitler; CUDA paketleri gerekmez.

Gerçek çalıştırılan ortam:

| Bileşen | Ölçülen sürüm |
| --- | --- |
| Python | 3.12.11 |
| torch | 2.6.0+cpu |
| torchvision | 0.21.0+cpu |
| Pillow | 11.1.0 |
| NumPy | 2.3.1 |
| OS | Linux / WSL2 x86_64, glibc 2.36 |

Python 3.12 ve venv kuruluysa **Ubuntu terminalinde**, bağımsız kurulum:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7/task-1"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B tests/test_core.py -v
python -B -u train.py
python -B export_samples.py
python -B predict.py --checkpoint artifacts/baseline/fashion_mnist_last.pth \
  --image demo_samples/test_00000_label_9_ankle_boot.png \
  --reference results/baseline/reload_reference.json \
  --output results/baseline/reload_check.json
```

**PowerShell** alternatifi (Python 3.12 kurulu olmalı):

```powershell
Set-Location 'C:\Users\LENOVO\OneDrive\Masaüstü\EE 471 Soft-Tech\Hafta 1\EE471\Week-7\task-1'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B -u train.py
.\.venv\Scripts\python.exe -B export_samples.py
```

Bu yerel venv kurulumları geliştirme sırasında yapılmış gibi raporlanmaz. Gerçek çalışma, yeniden bağımlılık indirmek yerine hazır Week 6 CPU image'ı **yalnız Python ortamı** olarak kullanılarak yürütüldü. Image'ın gerçek Python sürümü 3.12.11 idi; eski Week 6 raporundaki Python patch sürümü buraya kopyalanmadı.

### Bu makinede kullanılan Docker/WSL yolu

PowerShell'de `wsl -d Ubuntu` ile geçin. Docker Desktop açıkken **Ubuntu terminalinde**:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-7"
docker image inspect ee471-week6-classifier:latest --format '{{.Id}}'
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work/task-1 \
  ee471-week6-classifier:latest -B tests/test_core.py -v
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work/task-1 \
  ee471-week6-classifier:latest -B -u train.py
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work/task-1 \
  ee471-week6-classifier:latest -B export_samples.py
docker run --rm --entrypoint python \
  --mount "type=bind,source=$PWD,target=/work" --workdir /work/task-1 \
  ee471-week6-classifier:latest -B predict.py \
  --checkpoint artifacts/baseline/fashion_mnist_last.pth \
  --image demo_samples/test_00000_label_9_ankle_boot.png \
  --reference results/baseline/reload_reference.json \
  --output results/baseline/reload_check.json
```

Burada Cog servisi veya Cog build çalışmaz; mevcut image'ın entrypoint'i Python olarak değiştirilir. ResNet modeli çalıştırılmaz. Yalnız Week-7 bind mount edilir. Eğitim ortamı/provenance bilgisi `results/baseline/execution.json` içindedir. Image yoksa registry'den çekmek/build etmek yerine yukarıdaki bağımsız venv kurulumunu kullanın.

Veri ilk `download=True` çağrısında torchvision FashionMNIST downloader'ı ile indirilir. Downloader arşivlerin hash kontrolünü yapar; fiziksel olarak train/test arşivlerini birlikte indirebilir, ancak test örnekleri eğitim/validation döngüsüne girmez. Cache sonraki çalıştırmalarda kullanılır. İlk eğitim komutu sonuçlar mevcutsa durur. Kendi baseline çıktılarını bilinçli yeniden üretmek için `train.py --overwrite` kullanın; yeni run/checkpoint yolu da verebilirsiniz. Bu aşamada yalnız bir tam baseline eğitimi yapıldı.

## Gerçek tam eğitim sonucu — 2026-11-09

**Smoke eğitimi değildir:** 5 epoch boyunca 54.000 train ve 6.000 validation örneği tam işlendi. Aşağıdakiler ölçülen değerlerdir; tutorial'ın örnek çıktısından alınmadı.

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy | Süre (s) |
| --- | --- | --- | --- | --- | --- |
| 1 | 2.244592 | %35.6296 | 2.182337 | %52.1167 | 2.85 |
| 2 | 2.091173 | %55.8870 | 1.977203 | %57.8833 | 2.81 |
| 3 | 1.818272 | %58.8870 | 1.649887 | %59.6333 | 2.79 |
| 4 | 1.487877 | %61.2222 | 1.356281 | %61.3167 | 2.89 |
| 5 | 1.243355 | %63.5519 | 1.165968 | %63.4167 | 2.88 |

- Resmi test: **10.000 örnek**, **accuracy %63.37**, **loss 1.1639250301361084**.
- Eğitim + validation süresi: **14.3382 saniye**.
- Veri indirme/hazırlama, eğitim/validation, checkpoint ve final test dahil toplam: **60.1573 saniye**. Demo export ve ayrı süreç kontrolleri bu toplamın dışında.
- Tam hassasiyetli kayıt: `results/baseline/metrics.json`; split/seed/hash: `split.json`.
- Bağımsız `evaluate.py` işlemi aynı checkpoint ile yine %63.37 / 1.1639250301361084 verdi (`independent_evaluation.json`).

Bağımsız değerlendirmeyi tekrar etmek için task-1 dizininden:

```bash
python -B evaluate.py --checkpoint artifacts/baseline/fashion_mnist_last.pth \
  --output results/baseline/independent_evaluation.json
```

Docker ortamında aynı `docker run ... --entrypoint python` kalıbında `evaluate.py` ve bu argümanları kullanabilirsiniz.

## Checkpoint ve demo görselleri

Final checkpoint: **`task-1/artifacts/baseline/fashion_mnist_last.pth`**.

- Boyut: **2.681.462 bayt**, yaklaşık **2.56 MiB**.
- Format: yalnız CPU `state_dict`; optimizer veya Python model nesnesi serialize edilmez.
- SHA-256: `17f629876a1f204cf7bc10d50e0b362c2a2eb12d09fd2cd527f596bb5702e7b2`.
- `load_model()` sabit mimariyi kurar, `torch.load(..., weights_only=True, map_location=...)` ve strict `load_state_dict()` kullanır, `eval()` çağırır.
- Ağırlık Git dışında yerelde saklanır; yeniden üretim komutu yukarıdaki sabit ayarlı `train.py`dır. Başka makineye geçerken ya yerel checkpoint'i ayrıca taşıyın ya da yeniden eğitin; repoda varmış gibi varsaymayın.

**10 PNG toplam 4.506 bayt** (yaklaşık 4.40 KiB). Bunlar `task-1/demo_samples/` altında küçük teslim örnekleri olarak izlenebilir; tam dataset Git dışındadır. Dosya adları `test_<index>_label_<id>_<class>.png` biçimindedir. `manifest.json` dosya adı, resmi test indeksi, gerçek sınıf, boyut ve SHA-256 eşlemesini içerir:

| Label | Gerçek sınıf | Resmi test indeksi |
| --- | --- | --- |
| 0 | T-shirt/top | 19 |
| 1 | Trouser | 2 |
| 2 | Pullover | 1 |
| 3 | Dress | 13 |
| 4 | Coat | 6 |
| 5 | Sandal | 8 |
| 6 | Shirt | 4 |
| 7 | Sneaker | 9 |
| 8 | Bag | 18 |
| 9 | Ankle boot | 0 |

Her sınıfın testteki ilk örneği seçildi; doğru tahmin edilene göre örnek seçilmedi. Veri kaynağı [resmi FashionMNIST deposudur](https://github.com/zalandoresearch/fashion-mnist). Görseller L/28×28 PNG'dir, orijinal pikseller korunur.

Eğitimden ayrı yeni süreçte test örneği 0 PNG olarak yüklenip tahmin edildi: **Ankle boot (9)**, olasılık **0.3658556640**, gerçek etiket **Ankle boot (9)**. Checkpoint hash'i ve logits eğitim sonunda ayrılan referansla `rtol=atol=1e-6` içinde eşleşti; `reference_verified: true` sonucu `reload_check.json` içinde. Tek örneğin doğru tahmini tüm örneklerin doğru olduğu anlamına gelmez; genel sonuç yukarıdaki %63.37'dir.

## Kontroller ve kalan kapsam

- 4 sentetik smoke/unit kontrolü geçti: CPU paket sürümleri/dönüşüm/PNG roundtrip, ayrık-tekrarlanabilir split, gradient+state_dict yükleme ve son kısa batch'in örnek ağırlıklı metriği. Bu kontroller dataset eğitimi veya gerçek accuracy ölçümü olarak sunulmaz.
- Tam eğitim, bağımsız test değerlendirmesi, ayrı süreçte PNG inference ve hash doğrulaması gerçekten yapıldı. İndirme/eğitim tamamlandı; uydurulmuş veya eksik epoch yok.
- `data/`, `.venv/`, araç/cache/çıktılar ve `artifacts/` Git dışında. Ölçülen küçük JSON kayıtları ve demo PNG'leri izlenebilir.
- Docker Desktop başlangıçta kapalıydı; kurulu uygulama arka planda açıldı. Mevcut CPU image'ı kullanıldı, Cog/Docker build veya registry push yapılmadı. Geçici eğitim/eval container'ları `--rm` ile kapandı.
- Aşama 1 sonunda yalnız Week-7 dosyaları eklenmişti; `.env` okunmamış, eski projeler değiştirilmemişti. O aşamada HPO, Cog runner/build, website ve CIFAR10 yapılmamıştı. Cog/website devamı Aşama 2, HPO devamı Aşama 3 kaydındadır; CIFAR10 hâlâ yapılmadı.
