# EE471 Week 7 çalışma kaydı

Bu belge bu aşamanın tam kullanıcı istemi ve gerçek geliştirme sonuçlarını içerir. Önceki projelerin geçmişi aktarılmadı. Ekli PDF daha geniş ders teslimini anlatır; aşağıdaki kullanıcı isteği bu aşamayı yalnız FashionMNIST baseline ile sınırlar.

## 2026-11-09 — Aşama 1 istemi (tam metin)

EE471 Week 7 – Aşama 1: FashionMNIST baseline eğitimi.

Önce repo talimatlarını, git durumunu ve Week-6/task-2 yapısını incele.
Çalışma alanı temizse güncel main'den week7-classifiers branch'ini oluştur.
Branch zaten varsa geçmişini kontrol edip onunla devam et. Kullanıcıya ait
değişiklikleri silme veya taşıma. Yalnızca Week-7 altında dosya ekle/değiştir.
Commit, push veya merge yapma.

Week-7/task-1/ altında PyTorch Quickstart'a dayalı bir FashionMNIST
eğitim ve değerlendirme akışı oluştur:
https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html

- FashionMNIST'i torchvision ile indir. Tutorial'daki 28×28 gri girdi,
  ToTensor eşdeğeri dönüşüm, Flatten → 512 → 512 → 10 MLP,
  CrossEntropyLoss ve SGD'yi başlangıç noktası al. Baseline ayarları:
  learning rate 0.001, batch size 64, 5 epoch.
- Resmi eğitim setini sabit seed ile train/validation olarak ayır.
  Resmi test setini hiperparametre veya checkpoint seçimine katma.
  Bölme oranını, seed'i, cihazı ve sürümleri kaydet.
- Her epoch için train ve validation loss/accuracy yaz. Baseline'ın
  son checkpoint'ini kaydet ve resmi test setinde loss/accuracy ölç.
  Bir smoke test yaparsan bunu tam eğitimden açıkça ayır.
- Model tanımı ve inference dönüşümü daha sonra Cog runner'ın import
  edebileceği modüllerde olsun. Yeniden yüklenebilir state_dict kaydet;
  ayrı bir süreçte yükleyip örnek üzerinde tahmini doğrula.
- Demo için test setinden birkaç etiketli PNG dışa aktar. Doğru sınıfı
  ve hangi dosyanın hangi örneğe ait olduğunu kaydet.
- Tam veri setini, sanal ortamı ve geçici dosyaları Git dışında tut.
  Demo örnekleriyle final ağırlıkların boyutunu ve yeniden üretim
  komutunu bildir. Eğitim ve inference için uyumlu torch/torchvision
  sürümlerini doğrula; CPU ile başlayabilmeli.
- Week-7/README.md ve PROMPTS.md'ye kurulum, komutlar, deney ayarları
  ve gerçekten ölçülen sonuçları yaz. İndirilemeyen veri veya
  tamamlanmayan eğitim varsa açıkça bildir; sonuç uydurma.

Bu aşamada yalnızca FashionMNIST baseline var. Hiperparametre taraması,
Cog build, website ve CIFAR10 sonraki aşamalarda yapılacak.

Sonuçta aktif branch'i, oluşturulan dosyaları, epoch sonuçlarını,
test accuracy/loss değerlerini, eğitim süresini ve checkpoint yolunu bildir.

## Gerçek geliştirme ve ölçüm sonuçları

- Çalışma başlangıcında main ve temiz çalışma ağacı vardı; week7-classifiers branch'i henüz yoktu. Repo/ata dizinlerinde uygulanabilir AGENTS.md bulunmadı. Week-6/task-2'nin mevcut Cog model/config/CPU sürümleri incelendi; değiştirilmedi.
- `git fetch origin main` başarılı oldu; main ve origin/main aynı `6c6d106` commit'indeydi. Kullanıcının açık talimatıyla `git switch -c week7-classifiers main` çalıştırıldı. Branch oluşturuldu; kullanıcı değişikliği silinmedi/taşınmadı, merge yapılmadı.
- PyTorch Quickstart ve resmi önceki sürüm/torchvision kaynakları incelendi. PDF geçici pypdf wheel'iyle okundu; bu araç runtime bağımlılığına eklenmedi, Week-7/.test-deps altında Git dışında tutuldu. PDF'deki HPO/website/Cog/CIFAR10 bu aşamada uygulanmadı.
- Başlangıçta Docker Desktop motoru kapalıydı. İlk kontrol eski standart kurulum yolunu bulmadı; gerçek kurulum `AppData/Local/Programs/DockerDesktop` altında bulundu ve hidden başlatıldı. Sonra mevcut ee471-week6-classifier image'ı Python entrypoint'iyle eğitim ortamı olarak kullanıldı. Yeni image/Cog build veya inference servisi oluşturulmadı; yalnız Week-7 bind mount edildi.
- Gerçek ortam Python 3.12.11, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0, NumPy 2.3.1, Linux/WSL2 x86_64/glibc 2.36 idi. Önceki projedeki Python patch sürümü bu rapora aynen kopyalanmadı. Ana Python bağımlılıkları requirements.txt ile sabitlendi; CPU torch/torchvision eşleşmesi resmi kaynak ve gerçek import/çalışma ile doğrulandı.
- Import edilebilir `model.py` Quickstart MLP'yi, `preprocessing.py` ortak 28×28 grayscale/ToTensor dönüşümünü içerir. train/evaluate/predict/export CLI'ları ve ortak engine/seed/split/JSON araçları eklendi. Import sırasında eğitim veya veri indirme yoktur.
- Seed 42; resmi 60.000 eğitim örneği bağımsız seed'li randperm ile 54.000 train/6.000 validation olarak ayrıldı. Ayrık indekslerin hash'i split.json içinde. SGD lr=.001, batch=64, epoch=5, momentum=0, weight decay=0; CPU 2 thread, num_workers=0. Model veya ayarlar test sonucuna göre değiştirilmedi; checkpoint beşinci/son epoch'tur.
- Önce 4 sentetik smoke/unit kontrolü geçti (0.442 s): dönüşüm/sürümler/PNG roundtrip, split ayrıklığı/tekrar üretimi, gradient/state_dict yükleme ve kısa son batch'in loss ağırlığı. Bu kontroller tam veri eğitimi veya accuracy kanıtı sayılmadı.
- FashionMNIST torchvision `download=True` ile başarıyla indirildi. Tam baseline eğitimi bir kez çalıştırıldı; her epoch 54.000 train ve 6.000 validation örneğini kullandı. Metrikler console ve metrics.json'a yazıldı:

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy | Saniye |
| --- | --- | --- | --- | --- | --- |
| 1 | 2.244592 | %35.6296 | 2.182337 | %52.1167 | 2.85 |
| 2 | 2.091173 | %55.8870 | 1.977203 | %57.8833 | 2.81 |
| 3 | 1.818272 | %58.8870 | 1.649887 | %59.6333 | 2.79 |
| 4 | 1.487877 | %61.2222 | 1.356281 | %61.3167 | 2.89 |
| 5 | 1.243355 | %63.5519 | 1.165968 | %63.4167 | 2.88 |

- Son checkpoint resmi test setinde 10.000 örnekle değerlendirildi: loss **1.1639250301361084**, accuracy **0.6337 / %63.37**. Eğitim+validation süresi **14.338224947 s**, ilk veri indirme/hazırlama/checkpoint/final test dahil toplam **60.157260692 s**. Smoke veya tutorial örnek çıktısı bu değerlerin yerine kullanılmadı.
- Final `artifacts/baseline/fashion_mnist_last.pth`, CPU state_dict-only olarak yazıldı: **2.681.462 bayt**, SHA-256 `17f629876a1f204cf7bc10d50e0b362c2a2eb12d09fd2cd527f596bb5702e7b2`. Dataset/ortam/ağırlıklar Git dışında; küçük metrik JSON kayıtları izlenebilir.
- Test setinden model tahminlerine bakmadan her sınıfın ilk örneği seçilip 10 L/28×28 PNG çıkarıldı. Toplam PNG boyutu **4.506 bayt**. Manifest, dosya/test index/label/class/size/hash eşlemesini kaydeder. Sınıf sırasına göre resmi test indeksleri: 19, 2, 1, 13, 6, 8, 4, 9, 18, 0. Tam test seti Git'e eklenmedi.
- Eğitimden ayrı yeni süreçte `predict.py` checkpoint'i weights_only=True ile yükledi. `test_00000_label_9_ankle_boot.png` için gerçek sınıf 9/Ankle boot, tahmin 9/Ankle boot, olasılık 0.3658556640148163 idi. Checkpoint SHA ve logits eğitim sonrası referansla rtol=atol=1e-6 içinde eşleşti; reload_check.json reference_verified=true.
- Bağımsız evaluate.py komut yolu da aynı final checkpoint üzerinde çalıştırıldı; test loss/accuracy orijinal son ölçümle tam eşleşti. Bu tekrar test ölçümü hiperparametre/checkpoint seçimine veya yeni eğitime dönüştürülmedi. Demo dosya boyutları/hash'leri ve 10 sınıf etiketi manifest üzerinden tekrar kontrol edildi.
- README'ye yerel venv ve gerçekten kullanılan Docker/WSL ortamı için ayrı komutlar, seed/split/cihaz/sürümler, ölçülen epoch/test/süreler, checkpoint/demo boyutları ve yeniden üretim eklendi. Yerel venv kurulumunun yapılmış olduğu iddia edilmedi.
- Yalnız Week-7 altında dosya eklendi; gerçek .env okunmadı, eski projeler değiştirilmedi. Commit/push/merge yapılmadı. HPO, Cog build, website ve CIFAR10 sonraki aşamalara kaldı.

## 2026-11-09 — Aşama 2 istemi (tam metin)

EE471 Week 7 – Aşama 2: FashionMNIST baseline Cog servisi ve website.

week7-classifiers branch’inde devam et. Önce Week-7/task-1’deki model,
dönüşüm, checkpoint, metrik ve demo manifestini; ardından Week-6/task-2’deki
Cog, Flask, Compose ve Postman akışını incele. Yalnızca Week-7 altında
değişiklik yap. Week 6’yı, baseline eğitim sonuçlarını ve checkpoint’i koru.
Yeniden eğitim, HPO, CIFAR10, commit/push/merge yapma.

1. Cog servisi
- Mevcut fashion_mnist_last.pth checkpoint’ini kullan. Eğitimi image
  build veya servis başlangıcında çalıştırma. Model dosyası yoksa README’deki
  üretim komutuna yönlendiren açık bir hata ver.
- Cog build bağlamını model tanımı, dönüşüm ve checkpoint image’a girecek
  şekilde düzenle. Dataset, sanal ortamlar ve geçici çıktılar image’a girmesin.
  Git’te ignore edilen checkpoint’in Docker bağlamına gerçekten dahil
  edildiğini doğrula.
- Runner setup’ında modeli CPU’ya bir kez yükle ve eval moduna al.
  Tahminde eğitimdeki sınıf sırasını ve mevcut inference dönüşümünü kullan:
  28×28 gri girdi. inference_mode ile en yüksek skorlu sınıfları döndür.
- /predictions endpoint’i yerel PNG/JPEG’in JSON data URL olarak
  gönderilmesini desteklesin. Container içinde tahmin başlangıcı, sonucu
  ve süresi loglansın. Base64 içeriğini loglama.

2. Website ve Compose
- Week 6’daki Flask yükleme, önizleme ve hata yönetimini FashionMNIST’e
  uyarla. Arayüzde dataset’e uygun örnek PNG kullanılmasını açıkla.
- Yüklenen görseli baseline servisine gönder. Tahmin sınıfını ve skorunu
  göster. Ölçüm JSON’undaki resmi test accuracy’sini gösterirsen bunu
  tek görselin tahmin skorundan ayrı etiketle.
- Flask website için Dockerfile ve bağımsız Compose projesi oluştur.
  Host portları boşsa website için 5071, Cog için 5072 kullan; yalnızca
  localhost’a aç. Week 6 servislerini değiştirme veya durdurma.
- Baseline servis adresini yapılandırılabilir yap; ileride ikinci servisi
  ekleyebilelim. Henüz optimized sonuç veya sahte skor gösterme.

3. Gerçek doğrulama ve belgeler
- Image’ları build et ve Compose servislerini çalıştır. Demo manifestinden
  aynı PNG’yi seçerek yerel Python inference, doğrudan Cog HTTP isteği ve
  website sonuçlarını karşılaştır. Etiketlerin ve skorların uyuştuğunu
  doğrula. Gerçek tarayıcı kontrolü yapabilirsen yöntemini belirt.
- Bozuk dosyanın anlaşılır hata verdiğini ve ardından geçerli tahmin
  yapılabildiğini kontrol et. Tahmin satırının çalışan container içindeki
  log dosyasına yazıldığını göster.
- Postman collection ve yerel görselden istek üreten yardımcıyı uyarla.
  Üretilen Base64 çıktılar Git dışında kalsın. HTTP isteğini doğrula;
  Postman uygulamasında denenmediyse bunu ayrıca belirt.
- README/PROMPTS’a Ubuntu’dan build/başlatma, website ve API adresleri,
  canlı log komutu, aynı PNG ile Postman adımları ve gerçek test
  sonuçlarını ekle.

Sonuçta değişen dosyaları, çalıştırma komutlarını ve aynı PNG için
Python/Cog/website karşılaştırmasını bildir.

## Aşama 2 gerçek geliştirme ve kontrol sonuçları

- Branch week7-classifiers idi; mevcut Week-7 untracked kaynakları korundu. Repo talimatları ve Week 6 Cog/Flask/Compose/Postman akışı incelendi. Başlangıç Docker servis listesi boştu; 5071/5072 ile yeni Compose başlatma başarılı oldu. Week 6 servislerine stop/up uygulanmadı.
- Başlangıçta baseline kaynakları, checkpoint, results/baseline JSON'ları, demo örnekleri ve ilgili Week 6 kaynakları hash snapshot'ına alındı. İlk karşılaştırmada korunan 41 dosya aynıydı. Yeni servis kanıtları eski metrik klasörüne değil results/service-validation.json ve ignore edilen outputs içine yazıldı.
- Cog CLI 0.23.1 help ve v0.23.1 YAML kuralları kontrol edildi. Web aracı raw dosyayı açamadığında resmi etiketli belge WSL curl ile okundu; güncel main belgesiyle değiştirilmedi.
- Cog context task-1 kökü seçildi; orijinal model.py/preprocessing.py ve Git'te ignore edilen final checkpoint açık .dockerignore allowlist'iyle dahil edildi. Context yaklaşık 2.69 MB oldu. Dataset, train/evaluate kodları, ortamlar, demo/sonuçlar ve website model image'ına alınmadı. Build veya setup eğitim/indirme yapmaz; build.sh ve Runner eksik dosya için README/üretim komutlu hata verir.
- Runner CPU state_dict yükler, eval yapar, 2 thread ve inference_mode kullanır. Mevcut sınıf sırası ve 28×28 gri/ToTensor dönüşümü korunur; en yüksek üç gerçek softmax skoru döner. Başlangıç/sonuç/süre stdout ve /var/log/ee471/fashion-baseline.log dosyasına kaydedilir; base64 loglanmaz.
- Week 6 akışı yalnız Week 7 altına kopyalanıp uyarlandı. İlk uzun Python -c uyarlama komutu PowerShell tırnaklaması nedeniyle derlenemedi; dosya değişikliği başlamadan başarısız oldu. Aynı uyarlama ignore edilen Python yardımcı dosyası üzerinden yapıldı; uygulama davranışı bu kabuk hatası için gevşetilmedi.
- Cog image ee471-week7-fashion-baseline ve Flask image ee471-week7-fashion-website gerçek build ile üretildi. Cog SDK 0.23.1 / Python 3.12.11 ve eski torch 2.6.0+cpu / torchvision 0.21.0+cpu / Pillow 11.1.0 / NumPy 2.3.1 sürümleri kullanıldı. Website kendi Flask/requests/Pillow/gunicorn bağımlılıklarını taşır; Torch/model taşımaz.
- Compose projesi ee471-week7-fashion-baseline; baseline host 127.0.0.1:5072, website 127.0.0.1:5071, iç portlar 5000. Yapılandırılabilir BASELINE_URL Compose içinde http://baseline:5000. Gerçek /health-check READY ve website /healthz ile iki servis healthy oldu. Registry pull/push veya Week 6 image değişikliği yapılmadı.
- Website doğrulaması JPEG/PNG gerçek yapı+decode, tam 28×28 ve 1 MiB sınırı kullanır. Görseli yeniden boyutlandırmadan JSON data URL olarak Cog'a yollar; HTTP 200/failed başarı değildir. Önizleme/busy/hata/yeniden kullanım, object URL/iptal yönetimi korunur. Resmi %63.37/10000 test ölçümü gerçek metrics.json'dan türetilen ayrı baseline_metrics.json ile gösterilir; tek görselin skoru ayrı etikettedir. Optimized/sahte sonuç yoktur.
- Ağsız yeni model image'ında gerçek checkpoint SHA-256 `17f629876a1f204cf7bc10d50e0b362c2a2eb12d09fd2cd527f596bb5702e7b2`, CPU/eval modu, mevcut paket sürümleri, dataset/eğitim dosyalarının dışlanması ve eksik dosyanın açık hatası doğrulandı. Git ignore edilen checkpoint'in gerçekten image'a girdiği yalnız mock ile değil bu dosya/hash kontrolüyle gösterildi.
- Website için ağsız container'da **14 mock HTTP testi** geçti: PNG/JPEG, boyut/28×28, eksik/bozuk dosya, geçersiz schema/status/skor, timeout/busy/connection ve toparlanma. Bunlar gerçek model sonuçları olarak sunulmadı.
- Gerçek demo PNG `test_00000_label_9_ankle_boot.png`, resmi test indeksi 0, gerçek sınıf 9/Ankle boot seçildi. Orijinal yerel checkpoint ile ayrı Python inference, doğrudan gerçek Cog data URL isteği ve gerçek website multipart upload sonucu karşılaştırıldı:

| Sınıf | Python | Cog HTTP | Website |
| --- | --- | --- | --- |
| Ankle boot | 0.3658556640148163 | 0.3658556640148163 | 0.3658556640148163 |
| Sneaker | 0.26088428497314453 | 0.26088428497314453 | 0.26088428497314453 |
| Sandal | 0.18198947608470917 | 0.18198947608470917 | 0.18198947608470917 |

- Etiketler ve skorlar atol=1e-7 içinde eşleşti; UI yuvarlaması %36.59, %26.09, %18.20 idi. Baseline'ın önceki resmi test accuracy/loss değeri değiştirilmedi veya yeniden eğitimle güncellenmedi.
- Gerçek website bozuk/boş dosya istekleri 400 verdi. Doğrudan Cog bozuk data URL için HTTP 200/status=failed verdi; hem Cog hem website sonra geçerli tahmin yaptı. Gerçek 28×28 JPEG de başarılıydı; kayıplı JPEG skorunun orijinal PNG ile aynı olduğu iddia edilmedi.
- Website tahminiyle çalışan container logunda başarılı tahmin sayısı tam bir arttı; başlangıç/sonuç/süre satırları gerçek dosyadan okundu ve base64 bulunmadığı kontrol edildi. Sonraki gerçek log tail'i de gösterildi; sahte log üretilmedi.
- Gerçek Windows Chrome headless + CDP ile gerçek file input/form kullanıldı: üç submit (geçerli/bozuk/yeniden geçerli), gerçek model skorları ve ayrı test accuracy etiketi, önizleme, çift gönderim engeli, eski sonucu temizleme, iki URL temizliği, eksik upload ve 375 px görünüm kontrol edildi. JavaScript error/unhandledrejection listesi boştu. Headless otomasyon, insanın manuel görsel değerlendirmesi gibi raporlanmadı.
- Postman api-testing skill'i ve v3 biçim rehberi okundu. Kullanıcının önceki import edilebilir v2.1 JSON akışı korundu; v3-only collection lint'i bu dosya biçiminde uygulanmadı. Yeni collection doğrudan localhost:5072/predictions, application/json ve helper'ın hazırladığı input.image data URL'sini kullanır. Script'ler yerel dosyayı keyfî okumaz. Payload/environment/base64 çıktıları outputs ve isim kurallarıyla Git dışında tutuldu.
- Postman CLI 1.85.0 ilk --output denemesinde login istedi (exit 1); login veya cloud workspace değişikliği yapılmadı. --output kaldırılıp --no-report-events ile gerçek yerel endpoint'e tekrar çalıştırıldı: **1 request, 4 assertion passed, 0 failed, exit 0**. Kontroller HTTP 200, succeeded, üç geçerli skor ve FashionMNIST sınıf kümesidir. CLI oturum/cloud raporlama uyarısı verse de yerel request ve script'ler gerçekten çalıştı; CLI upgrade edilmedi.
- Postman masaüstü uygulamasında Send yapılmadı; README'de import/environment seçimi/Send/Test Results adımları ayrı verildi. HTTP veya CLI sonucu masaüstü testi diye sunulmadı.
- Son durumda iki Week 7 servis healthy/açık bırakıldı; headless Chrome kapatıldı. README'de Ubuntu build/up/down, iki adres, canlı log, aynı PNG Postman ve test komutları güncellendi. Son kontrolde 41 korunan dosyanın hash'i aynıydı; Python/JSON/JavaScript sözdizimi, ignore ve whitespace kontrolleri ile git diff --check geçti. Yeniden eğitim, HPO, CIFAR10, commit/push/merge veya registry push yapılmadı; değişiklikler yalnız Week-7 içindedir.

## 2026-11-09 — Aşama 3 istemi (tam metin)

EE471 Week 7 – Aşama 3: FashionMNIST hiperparametre optimizasyonu.

week7-classifiers branch’inde ve yalnızca Week-7 içinde çalış.
Önce mevcut eğitim/eval komutlarını, baseline metrik JSON’larını,
checkpoint biçimini ve train/validation bölme yöntemini incele.
Baseline checkpoint’ini, metriklerini ve çalışan Compose servislerini koru.
Bu aşamada website, Cog, CIFAR10 ve Git commit/push/merge yok.

1. Kontrollü deneyleri çalıştır
- Aynı MLP mimarisi, aynı 54.000/6.000 train/validation indeksleri,
  aynı transform, seed 42, batch size 64 ve 5 epoch kullan.
- CPU, başlangıç seed’i ve batch sırası adaylar arasında tutarlı olsun.
- Referans: SGD, lr=0.001. Mevcut baseline kaydının bu protokolle
  uyumunu doğrula; uyumluysa mevcut sonucu kullan.
- Adaylar: SGD lr=0.01, SGD lr=0.05, Adam lr=0.0003 ve Adam lr=0.001.
  Optimizer ayarlarını kaydet. Her adayı sıfırdan eğit.
- Adayların her epoch için train/validation loss ve accuracy değerlerini,
  toplam eğitim süresini ve son epoch metriklerini kaydet.
  Karşılaştırma için her adayın 5. epoch checkpoint’ini kullan.

2. Kazananı seç ve doğrula
- En yüksek validation accuracy’ye göre seç; eşitlikte daha düşük
  validation loss’u kullan. Test setini aday seçimine katma.
- Seçimden sonra yalnızca kazanan adayı resmi 10.000 test örneğinde
  ölç. Mevcut baseline test sonucuyla aynı değerlendirme koşullarında
  karşılaştır. Test accuracy farkını yüzde puan olarak yaz.
- Seçilen checkpoint’i artifacts/optimized/ altında mevcut inference
  kodunun yükleyebileceği biçimde sakla. Baseline dosyasını değiştirme.
- Ayrı bir süreçte optimized checkpoint’i yükle ve mevcut ankle boot
  demo PNG’siyle tahmini doğrula. Bu tek görseli model seçiminde kullanma.
- Validation veya testte iyileşme yoksa bunu açıkça bildir.

3. Sonuçları kaydet
- Aday ayarlarını ve ölçümlerini makinece okunabilir JSON’a yaz.
  Seçilen ayarı, seçim ölçütünü, test loss/accuracy değerini ve checkpoint
  yolunu kaydet. Dataset ve geçici checkpoint’ler Git dışında kalsın.
- README ve PROMPTS’a yeniden çalıştırma komutlarını ve sonuçları ekle.
- Son raporda tüm adayların validation accuracy/loss tablosunu,
  baseline ile seçilen modelin test karşılaştırmasını, eğitim sürelerini
  ve optimized checkpoint yolunu ver.

## Aşama 3 gerçek geliştirme ve ölçüm sonuçları

- Branch week7-classifiers; önceki Week-7 untracked kaynakları korundu. Uygulanabilir AGENTS.md bulunmadı. Mevcut train/eval/predict, state_dict formatı, split metodu ve baseline JSON'ları incelendi. Başlangıçta baseline website ve Cog container'ları healthy idi; kimlikleri kaydedildi.
- Önceden var olan 48 task-1 dosyası (baseline ağırlık/metrik/demo/model kaynakları ile website/Cog kaynakları dahil) hash snapshot'ına alındı. Yeni optimize.py, tests/test_selection.py ve sonuçlar ayrı eklendi; mevcut eğitim veya inference kodları değiştirilmedi.
- Baseline lr=.001/SGD, batch64,5epoch,seed42,CPU2thread,num_workers0,54.000/6.000 protokolü ve örnek sayıları uyumlu bulundu. Mevcut checkpoint SHA ve split indeks hash'leri doğrulandı. Python/torch/torchvision/Pillow/NumPy sürümleri baseline ortamıyla eşleşti. Baseline yeniden eğitilmedi veya testte tekrar ölçülmedi; önceki test sonucu referans alındı.
- Dört aday sıfırdan eğitildi; her aday öncesi seed_everything(42,2) ve shuffle generator seed42 yeniden kuruldu. Başlangıç ağırlık hash'i dört adayda aynıydı. TrackedSubset yalnız gerçek tüketilen indeksleri hash'ledi; RNG veya model girdisi değiştirmedi. 20 gözlenen epoch sıra hash'i baseline'ın aynı DataLoader/seed protokolünden yeniden oluşturulan sırayla eşleşti. Tarihsel baseline'da ölçülmüş batch trace varmış gibi raporlanmadı.
- SGD adaylarında momentum0/dampening0/weight_decay0/nesterovfalse; Adam betas(.9,.999)/eps1e-8/weight_decay0/amsgradfalse kullanıldı. Gerçek optimizer defaults tüm trial JSON'larına yazıldı. Model/transform/loss/batch/epoch/CPU sabit kaldı; scheduler veya erken durdurma eklenmedi.
- Üç sentetik seçim testi geçti: test accuracy veya önceki epoch zirvesi seçimde kullanılmıyor; validation accuracy eşitliğinde düşük validation loss seçiliyor; eksik/nonfinite final metrik reddediliyor. Bunlar eğitim ölçümü olarak sunulmadı.
- Aynı mevcut CPU image'ı Python entrypoint'iyle kullanıldı; image build/Compose değişikliği/Cog çalıştırma veya deployment yapılmadı. Dataset download=False ile mevcut cache'ten yüklendi. Dört gerçek koşunun beşer epoch train/validation loss/accuracy/süreleri results/hpo/trials/*.json ve summary.json içine kaydedildi. Adayların yalnız epoch-5 state_dict dosyaları artifacts/hpo altında Git dışında tutuldu.

| Ayar | Final train loss | Final train accuracy | Final val loss | Final val accuracy | Train+val saniye |
| --- | --- | --- | --- | --- | --- |
| Baseline SGD .001 — önceki kayıt | 1.243355 | %63.5519 | 1.165968 | %63.4167 | 14.3382 |
| SGD .01 | 0.495864 | %82.7000 | 0.501816 | %83.0000 | 14.2673 |
| SGD .05 | 0.368976 | %86.7204 | 0.375805 | %86.8333 | 14.4201 |
| Adam .0003 | 0.290397 | %89.2333 | 0.323389 | %87.9000 | 19.1588 |
| Adam .001 | 0.281395 | %89.4222 | 0.330351 | %88.1000 | 22.0295 |

- Dört yeni adayın train+validation toplamı 69.875675842 s; checkpoint/seçim/kazanan testi dahil arama süresi 70.822590686 s idi. Ön denetim/veri yükleme arama sayacından önceydi; baseline'ın eski süresi yeni toplama eklenmedi.
- Kazanan yalnız epoch-5 validation accuracy üzerinden **Adam lr=.001** oldu. Accuracy eşitliğinde düşük loss kuralı uygulanacaktı; bu koşuda eşitlik yoktu. Adam .0003'ün loss'u daha düşük olsa da accuracy'si düşük olduğu için seçilmedi. Seçim dosyası test loader'ı oluşturulmadan önce frozen_at_utc ile yazıldı. Trial test alanları null bırakıldı; kazanan test sonucu ayrı summary/winner_test alanına yazıldı.
- Yalnız seçilen checkpoint resmi 10.000 test örneğinde aynı CPU/batch64/shufflefalse/örnek ağırlıklı engine ile değerlendirildi: **accuracy .8734 / %87.34**, **loss .34845930209159853**. Mevcut baseline %63.37 / 1.1639250301361084 karşılaştırması **+23.97 yüzde puan** test accuracy artışı verdi. Test loss farkı -0.8154657280445099; validation accuracy artışı +24.6833333333 yüzde puandır. Her iki accuracy iyileşti; test sonucu aday kararını değiştirmedi.
- Kazananın 5. epoch checkpoint'i artifacts/optimized/fashion_mnist_optimized.pth dosyasına byte olarak kopyalandı. CPU state_dict-only, **2.681.462 bayt**, SHA-256 `2b86c814881244614eff20f10a37c2b87a5dceb959d129000e136833016a3409`. Baseline dosyası değiştirilmedi; mevcut load_model/predict biçimi korundu.
- Demo, seçimden ve test ölçümünden sonra kullanıldı. Ayrı yeni süreçte mevcut predict.py optimized checkpoint'i ve test_00000_label_9_ankle_boot.png dosyasını yükledi: tahmin9/Ankle boot, gerçek9/Ankle boot, skor **0.9907208681106567**, reference_verified=true. Hash ve logitler seçim sonrası referansla eşleşti. Bu tek görsel seçimde kullanılmadı ve skoru genel test accuracy diye sunulmadı.
- Son kontrollerde 48 korunan dosya hash'i aynıydı; dört başlangıç hash'i ve tüm 20 batch sıra hash'i eşleşti. Baseline website container'ı 3f54dfacc3b2 ve model container'ı ca679486a5f9 aynı kimlikle healthy kaldı. Yeni eğitim container'ları --rm ile sonlandı; hiçbir Compose stop/up/recreate yapılmadı.
- README'ye kontrollü protokol, referans uyumu, optimizer ayarları, sonuç tabloları/süreler, JSON/checkpoint yolları ve önceki run'ı ezmeyen yeniden çalıştırma komutları eklendi. Dataset/aday/optimized ağırlıkları Git dışında tutuldu. Yalnız Week-7 değişti; website/Cog/CIFAR10 veya Git commit/push/merge yapılmadı.

## Aşama 4 — FashionMNIST optimized Cog servisi ve yan yana karşılaştırma

### Tam kullanıcı istemi

EE471 Week 7 – Aşama 4: FashionMNIST optimized Cog servisi ve yan yana karşılaştırma.

week7-classifiers branch’inde, yalnızca Week-7 içinde çalış. Önce
Week-7/task-1’in mevcut build.sh, Compose, Cog runner, Flask/JS,
Postman ve doğrulama dosyalarını incele. Yeniden eğitim veya HPO yapma.
Baseline ve optimized checkpoint’lerini ve ölçüm JSON’larını değiştirme.
Week 6 servislerine dokunma. CIFAR10, commit, push veya merge yapma.

1. Optimized Cog servisi
- artifacts/optimized/fashion_mnist_optimized.pth dosyasını kullanan
  ayrı bir Cog image ve Compose servisi ekle. İki image aynı runner,
  model tanımı, sınıf sırası ve inference dönüşümünü kullansın;
  her image kendi checkpoint’ini içersin.
- Website 5071 ve baseline Cog 5072 portlarını koru. Boşsa optimized
  Cog’u yalnızca localhost:5073 üzerinden erişilebilir yap.
- Build sırasında her checkpoint’in doğru image’a girdiğini SHA256
  ile doğrula. Build veya runtime’da eğitim çalıştırma.
- Optimized tahminleri ayrı container içi log dosyasına yaz.
  Loglarda model adı, tahmin ve süre olsun; görsel verisini yazma.

2. Website
- Tek yükleme ve tek Classify düğmesiyle aynı görseli iki servise gönder.
  Sonuçları Baseline / Optimized kartlarında yan yana göster;
  dar ekranda kartlar alt alta gelsin.
- Her kart en yüksek skorlu sınıfı ve ilk üç sonucu göstersin.
  Resmi test accuracy’sini mevcut metrik JSON’larından al ve
  tahmin skorundan ayrı etiketle. İki modelin aynı sınıfı tahmin etmesi
  geçerli bir sonuç; farklı sonuç göstermek için örnek seçmeye çalışma.
- Bir model hata verirse diğerinin başarılı sonucunu göster ve
  hatayı ilgili karta yaz. Yeni istekte eski sonuçları temizle.
  Mevcut dosya doğrulamasını ve çift gönderim korumasını sürdür.

3. Doğrulama ve demo hazırlığı
- Gerçek image’ları build et ve Compose’u çalıştır. Aynı demo PNG’siyle
  her model için yerel Python, doğrudan Cog HTTP ve website sonuçlarının
  eşleştiğini doğrula. İki container’ın logunda yeni tahmini göster.
- Bozuk dosya ve tek servis hatasından sonra arayüzün tekrar
  kullanılabildiğini doğrula. Durdurma testi yaparsan sonunda
  her iki modeli ve website’i healthy bırak.
- Postman collection’a iki doğrudan Cog isteği ekle. İki istek aynı
  PNG’den üretilen gövdeyi kullansın; Base64 çıktılar Git dışında kalsın.
  CLI ve masaüstü Postman doğrulamalarını birbirinden ayrı raporla.
- README ve PROMPTS’a tam build/başlatma komutlarını, portları, iki
  canlı log komutunu ve Task-1 demosunun sırasını ekle.
- Temiz clone’dan demo için checkpoint’lerin nasıl üretileceğini ve
  build öncesi nerede bulunmaları gerektiğini açıkça belgele.

Sonuçta üç servisin durumunu, aynı PNG için iki modelin tahmin ve
skorlarını, yapılan kontrolleri ve benim çalıştıracağım komutları bildir.

### Gerçek geliştirme sonuçları — 2026-11-09

- Aktif branch `week7-classifiers`; başlangıçta yalnız Week-7 untracked idi. Başlangıçtaki baseline/website healthy idi, 5073 dinleyicisi görülmedi. Yalnız Week-7 içinde çalışıldı; gerçek .env okunmadı. Eğitim/HPO/CIFAR10 veya Git add/commit/push/merge yapılmadı.
- `prepare_build.py` orijinal baseline ve HPO JSON'larından beklenen hash'leri okur. İki checkpoint'i **önce** denetler; ayrı, allowlist uygulanmış `outputs/build/baseline` ve `optimized` bağlamlarına aynı runner/model/transform ve yalnız kendi checkpoint'ini kopyalar. `model_config.json` model adını, ağırlık hash'ini ve log yolunu seçer. Eksik ağırlıkta README üretim talimatı verir, kendisi eğitim çalıştırmaz. Beklenmeyen eski build dosyaları varsa silmek yerine durur.
- `build.sh` iki Cog image'ını ve website'i gerçekten build etti; çıkış kodu 0. Her image içindeki `/src/checkpoint.pth` SHA256 kontrol edildi: baseline `17f629876a1f204cf7bc10d50e0b362c2a2eb12d09fd2cd527f596bb5702e7b2`, optimized `2b86c814881244614eff20f10a37c2b87a5dceb959d129000e136833016a3409`. İki image'ın runner/model/transform hash'leri kaynaklarla aynıydı ve her birinde tek .pth vardı. Dataset/eğitim/HPO kodu, sonuçlar, .env, venv ve website model image'larına girmedi. Network kapalı CPU/eval setup ve eksik/yanlış hash hatası kontrolleri geçti.
- İlk port kontrolü/build sarmalayıcısındaki PowerShell–bash tırnaklaması syntax error verdi; bu denemede build başlamadı. Daha sade WSL çağrısıyla build tamamlandı. Cog 0.23.1 label/schema aşamasında iki kez `no access allowed to dir "context"` satırı basıldı; her iki image export edildi ve komut 0 döndü. Bu satır başarı kaydından saklanmadı: doğru ağırlıklar, offline setup ve gerçek HTTP tahminleri son image'larda ayrıca doğrulandı. PowerShell stderr yönlendirmesi ayrıca NativeCommandError biçiminde tanılama ekledi; gerçek process exit kodu 0 idi.
- Compose mevcut proje adını, website 127.0.0.1:5071 ve baseline 127.0.0.1:5072 eşlemelerini korur. Ayrı optimized servisi/image'ı 127.0.0.1:5073'e eklendi. Modeller container içinde 5000 dinler, yalnız yerel image kullanılır. Ortak runner setup CPU'ya bir kez yükler, eval uygular ve metadata hash'ini denetler. Baseline logu `/var/log/ee471/fashion-baseline.log`, optimized logu `/var/log/ee471/fashion-optimized.log`; stdout ve dosyada model adı/tahmin/süre vardır, görsel/base64 yoktur.
- Website tek doğrulanmış yüklemenin aynı data URL'sini iki servise en fazla iki eşzamanlı istekle gönderir. Her servisin Cog status/output/error doğrulaması bağımsızdır. Yeni `/api/classify` sonuç sözleşmesi `status` ve `results.baseline/optimized` içerir; kısmi hata ayrı kartta kalır. Yeni seçim/istek eski sonuçları temizler; çift gönderim, abort/eski yanıt koruması, 1 MiB/tam 28×28 PNG-JPEG doğrulaması ve preview URL temizliği korunur. Resmi test accuracy %63,37/%87,34 ilgili korunmuş ölçüm kayıtlarından türetilir ve tahmin skorundan ayrı etiketlenir. Kartlar dar ekranda alt alta gelir.
- Aynı mevcut örnek kullanıldı: `test_00000_label_9_ankle_boot.png`, resmi test index 0, gerçek Ankle boot. PNG SHA256 `cc22f44180c393601df7c2b9e5946b59e431ea747aff0d7bc223f8896a71548e`. Yeni örnek arama/model seçimi yapılmadı.

| Model | Ankle boot | Sneaker | Sandal |
| --- | --- | --- | --- |
| Baseline | 0.3658556640148163 | 0.26088428497314453 | 0.18198947608470917 |
| Optimized — Python | 0.9907208681106567 | 0.007302166894078255 | 0.0019707477185875177 |

- Her model için ayrı yerel Python süreci, doğrudan Cog HTTP ve website sonucu aynı üç sınıfı verdi; tüm skorlar mutlak `1e-7` toleransında eşleşti (optimized HTTP serialization değeri 0.9907208681106568). İki modelin de Ankle boot demesi geçerli bir sonuçtur. Website tahmini iki logda yeni `Prediction completed` satırını birer kez artırdı; loglarda model adı, süre ve gerçek skorlar görüldü.
- **16 website mock testi** geçti: PNG/JPEG ve sınırlar, gerçek içerik doğrulaması, güvenli Cog hata/timeout/bozuk yanıt, iki ayrı URL'ye aynı payload, kısmi başarısızlık ve toparlanma, ölçüm etiketleri. Bunlar gerçek model tahmini yerine sunulmaz. **7 mevcut sentetik çekirdek/seçim testi** de geçti; bunlar FashionMNIST yeniden eğitimi veya yeni HPO değildir.
- **Gerçek Windows Chrome headless + çalışan gerçek Compose/model:** beş form gönderimi, gerçek preview, her iki kartın doğrudan Cog ile skor eşleşmesi, tek isteğe indirgenen çift submit, bozuk dosyada eski sonucun temizlenmesi ve geçerli dosyada toparlanma doğrulandı. Yalnız optimized servisi gerçekten durduruldu: baseline sonucu kaldı, optimized kartında hata gösterildi; yeni istek başlatılabildi. Servis tekrar başlatılıp healthy olduktan sonra iki kart da başarılı oldu. 375px genişlikte tek sütun/taşma yok; iki object URL bırakıldı; JS error/unhandledrejection kaydı boştu. Bu gerçek headless kontrolüdür, kullanıcının masaüstünde yaptığı manuel demo olarak yazılmaz.
- Collection'da baseline/optimized için iki doğrudan JSON `/predictions` isteği vardır. İkisi de aynı PNG'den stdlib helper ile üretilen `prediction_body` ortam değişkenini kullanır. Üretilen body/environment `outputs/` altında Git dışındadır; base64 terminale yazılmadı. **Postman CLI 1.85.0: 2 istek, 8 assertion, 0 başarısız, exit 0**; `--no-report-events` ile buluta rapor gönderilmedi. Login/cloud paylaşımı uyarıları yerel koşuyu engellemedi; giriş/publish yapılmadı. **Masaüstü Postman uygulaması kullanılmadı**; import/environment seçimi/iki Send adımı kullanıcıya kaldı.
- `results/comparison-validation.json` yeni aşamanın makinece okunabilir doğrulama kaydıdır. Eski `results/service-validation.json`, baseline/HPO ölçümleri ve checkpoint'ler korundu. Son hash kontrolünde **16 korunan dosyanın** (iki checkpoint + baseline/HPO JSON'ları) tamamı aynıydı. Week 6 kaynak/servislerine dokunulmadı.
- README'ye iki image için build, üç servis için başlatma/durdurma, localhost portları, iki canlı log, aynı PNG/Postman gövdesi ve Task-1-demo.avi sırası eklendi. Temiz clone'da ignore edilen checkpoint'lerin build öncesi yerleri ve ayrı eğitim/HPO ile yeniden üretim komutları belgelendi; bu komutlar bu aşamada çalıştırılmadı. Yeniden üretilen ağırlık farklı hash verirse eski metrikle eşleştirmek yerine build'in duracağı açıklandı.
- Son gerçek `docker compose ps`: **baseline healthy:5072, optimized healthy:5073, website healthy:5071**. Durdurma testinden sonra üçü de çalışır durumda bırakıldı.

### Son tekrar-build kontrol?

Son eksik-checkpoint mesaj? modele g?re a??kl??a kavu?turuldu: baseline i?in train.py, optimized i?in optimize.py haz?rl???na ve README temiz-clone b?l?m?ne y?nlendirir. Sonraki tekrar build denemesinde haz?rl?k korumas? Cog?un kendisinin ?nceki build?de olu?turdu?u `.cog/` dizinini beklenmeyen i?erik sayarak a??k hata verdi. Yaln?z bu bilinen, symlink olmayan metadata dizini kabul edildi; allowlist `.dockerignore` onu image girdilerinden hari? tutmaya devam eder. Di?er beklenmeyen dosya/dizin/symlink kontrolleri korundu; hi?bir dizin silinmedi. Ger?ek tekrar build ??k?? kodu 0 ve iki IMAGE_SHA256_OK ile ge?ti; son image?lar Compose ?zerinden yeniden olu?turulup ?? servis healthy oldu. Son image?larda offline setup/hash/eksik dosya kontrolleri ve ayn? PNG?nin Python/Cog/website kar??la?t?rmas? yeniden ?al??t?r?ld?. E?itim veya HPO yap?lmad?.

## Aşama 5 — CIFAR10 baseline eğitimi

### Tam kullanıcı istemi

EE471 Week 7 – Aşama 5: CIFAR10 baseline eğitimi.

week7-classifiers branch’inde devam et. Yalnızca Week-7/task-2 ve
Week-7’nin ortak belgeleri/ignore kuralları içinde değişiklik yap.
FashionMNIST dosyalarını, checkpoint’lerini ve çalışan servislerini koru.
Bu aşamada HPO, Cog, website, commit, push veya merge yapma.

1. Baseline’ı oluştur
- Resmi PyTorch CIFAR10 tutorial’ındaki küçük CNN’i kullan:
  https://docs.pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html
- 32×32 RGB girdi, tutorial’daki kanal başına mean=0.5 ve std=0.5,
  CrossEntropyLoss ve SGD (lr=0.001, momentum=0.9) kullan.
  Tutorial’daki 2 epoch ve batch size 4 ayarlarını baseline olarak al.
- CIFAR10 sınıf sırasını torchvision veri setiyle doğrula.
  Model tanımı ve inference dönüşümü ileride Cog’dan import edilebilsin.
  Demo PNG’leri için eğitim ve inference normalizasyonu eşleşsin.
- FashionMNIST’teki çalışan torch/torchvision ortamını uyumluysa kullan.
  Eğitim CPU’da çalışabilsin. Kullanılan cihazı ve sürümleri kaydet.

2. Tam eğitimi çalıştır ve ölç
- Resmi 50.000 eğitim örneğini seed 42 ile 45.000 train / 5.000
  validation olarak ayır. İndeksleri kaydet veya aynı ayrımı yeniden
  üretmek için gereken bilgiyi belgeye ve sonuç JSON’una yaz.
- Her epoch için train ve validation loss/accuracy, ayrıca eğitim süresi
  kaydet. Son epoch state_dict’ini artifacts/baseline/ altında sakla.
- Son checkpoint’i resmi 10.000 test örneğinde ölç; test setini
  eğitim veya checkpoint seçimi için kullanma.
- Eğitim süresi ile veri indirme ve final test dahil toplam süreyi ayrı
  raporla. Smoke test varsa sonuçlarını tam eğitimle karıştırma.

3. Sonraki aşama için hazırla
- Resmi test setinden her sınıf için bir PNG dışa aktar. Örnekleri
  tahminin doğru olup olmadığına göre seçme. Gerçek etiket, dosya adı
  ve test indeksini manifestte kaydet.
- Checkpoint’i ayrı bir süreçte yükle ve manifestteki bir PNG üzerinde
  tahmini doğrula. Doğru etiket ile model tahminini ayrı bildir;
  tahmin yanlışsa örneği değiştirme.
- Dataset, sanal ortam, checkpoint ve geçici dosyaları Git dışında tut.
  Week-7/README.md ve PROMPTS.md’ye kurulum, eğitim, değerlendirme,
  inference komutlarını ve gerçekten ölçülen sonuçları ekle.

Sonuçta epoch tablosunu, resmi test accuracy/loss değerlerini,
eğitim süresini, checkpoint yolunu ve örnek PNG’nin tahminini bildir.

### Gerçek geliştirme sonuçları — 2026-11-09

Aktif branch week7-classifiers doğrulandı; uygulanabilir AGENTS.md bulunmadı. Yalnız task-2 ve ortak README/PROMPTS değiştirildi. Task 1 runtime koduna/servislerine dokunulmadı. Resmî tutorial incelenerek aynı 62.006 parametreli küçük CNN, CrossEntropyLoss ve SGD(.001,momentum=.9), 2 epoch/batch4 kullanıldı. Model ve preprocess bağımsız modüllerdir; runtime'da Task 1 kaynaklarına import/path bağımlılığı yoktur. Mevcut yerel CPU image'ı yalnız Python entrypoint'iyle kullanıldı; yeni Cog image/servis veya website yoktur.

Sürümler: {"python": "3.12.11", "platform": "Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.41", "torch": "2.6.0+cpu", "torchvision": "0.21.0+cpu", "Pillow": "11.1.0", "numpy": "2.3.1"}. Seed42, CPU2threads, deterministic algorithms ve num_workers0. Gerçek CIFAR10 sınıf sırası doğrulandı: airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck. 50.000 örnekten bağımsız seed42 randperm ile ilk45.000 train/son5.000 validation; yöntem ve iki little-endian int64 indeks hash'i split.json/metrics.json'dadır. Test örnekleri eğitim/validation/checkpoint seçimine katılmadı; final epoch kaydından sonra 10.000 test örneğinde ölçüm yapıldı.

İlk normal indirme yavaştı; epoch başlamadan aynı resmî Toronto arşivi 8 bağlantıyla sınırlı Range istekleri üzerinden hazırlandı. Torchvision0.21.0 ile URL/MD5 doğrulandı: c58f30108f718f92721af3b95e74349a, 170.498.071 bayt. Ara indirme çıktıları Git dışındadır. İlk indirmedeki yalnız started kaydı outputs içinde tutuldu; tam eğitim yeni süreçte doğrulanmış arşivle bir kez yapıldı. Alternatif iki dosya URL'sinin küçük erişim denemeleri 404/403 verdi; onlar veri kaynağı olarak kullanılmadı. Bir ilk HEAD denemesinde PowerShell/WSL tırnaklaması nedeniyle SyntaxError alındı; bunun yerine dosya tabanlı güvenli helper kullanıldı. Bunlar eğitim başarısı sayılmadı.

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy | Train(s) | Validation(s) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.708827 | %36.7533 | 1.450157 | %46.9800 | 15.02 | 0.86 |
| 2 | 1.351540 | %51.5000 | 1.333564 | %52.0800 | 15.67 | 0.82 |

Resmi test10000 loss 1.333286461931467, accuracy 0.5141 (%51.4100). Eğitim döngüleri 30.696080s; train+validation 32.379301s; son test yükleme/değerlendirme 3.543753s; doğrulanmış cache ile tüm script 56.710636s. İlk indirme başlangıcından tam eğitim/test/export bitimine indirme dahil gerçek duvar süresi 965.754854s; cache'li script süresi ile karıştırılmadı. Smoke eğitim yapılmadı; dört sentetik birim testi eğitim sonuçlarından ayrıldı.

Final checkpoint artifacts/baseline/cifar10_last.pth: CPU state_dict-only, 251454 bayt, SHA256 60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c. Son epoch kaydedildi; en iyi validation/test checkpoint'i seçilmedi. Her sınıfın test setindeki ilk örneği, hiçbir tahmin kullanılmadan RGB PNG olarak dışa aktarıldı; 10PNG toplam 23628 bayt. Gerçek test indeksi/sınıf/dosya/hash/boyut manifestte; PNG normalize tensor'ları dataset tensor'larıyla birebir eşleşti.

Ayrı süreç test_00000_label_3_cat.png dosyasını ve checkpoint'i yükledi: gerçek 3/cat, tahmin 3/cat, skor 0.44070398807525635, sonuç doğru. Reference_verified=true; checkpoint SHA ve logitler eğitim sonu referansıyla 1e-6 toleransında eşleşti. Örnek yanlış tahmin edildiyse değiştirilmedi. Bu tek PNG skoru test accuracy değildir.

Dört sentetik test geçti: normalizasyon/PNG roundtrip/boyut, ayrık tekrarlanabilir split, CNN parametre/çıktı/state_dict reload, örnek ağırlıklı kısmi batch metrikleri. Gerçek tam eğitim, bağımsız evaluate ve ayrı-process predict kontrolleri sonuç kayıtlarında ayrıdır. FashionMNIST koruma hash'leri ve üç container kimliği/healthy durumları son kontrolde doğrulandı. Dataset, ağırlık ve geçici dosyalar ortak ignore kurallarıyla Git dışında; demo PNG'leri ve ölçüm JSON'ları izlenebilir. .env okunmadı; HPO/Cog build/website/Git add/commit/push/merge yapılmadı.

## Aşama 6 — CIFAR10 baseline Cog servisi ve website

### Tam kullanıcı istemi

EE471 Week 7 – Aşama 6: CIFAR10 baseline Cog servisi ve website.

week7-classifiers branch’inde devam et. Yalnızca Week-7/task-2 ve
Week-7’nin ortak README/PROMPTS/ignore dosyaları içinde değişiklik yap.
Önce task-2’deki model, inference dönüşümü, checkpoint, ölçüm JSON’u
ve demo manifestini incele. Ardından task-1’de doğrulanmış Cog, Flask,
Compose, build ve Postman düzenini örnek al.

FashionMNIST’in dosyalarını, image’larını ve çalışan servislerini koru.
Bu aşamada yeniden eğitim, veri indirme, HPO veya Git commit/push/merge yok.

1. CIFAR10 Cog servisi
- artifacts/baseline/cifar10_last.pth checkpoint’ini kullan.
  Image build veya başlangıç sırasında eğitim/veri indirme yapma.
  Checkpoint yoksa README’deki üretim komutuna yönlendiren açık hata ver.
- Modeli CPU’da bir kez yükle, eval moduna al ve inference_mode kullan.
  Mevcut 32×32 RGB dönüşümünü, kanal normalizasyonunu ve CIFAR10 sınıf
  sırasını doğrudan mevcut modüllerden kullan.
- /predictions JSON isteğinde PNG/JPEG data URL kabul et. En yüksek
  skorlu sınıfı ve ilk üç sonucu döndür. Tahmin başlangıcı, sonucu
  ve süresini container içindeki ayrı log dosyasına yaz; Base64 yazma.
- Build bağlamına checkpoint’i dahil et ve image içindeki SHA256’nın
  orijinalle eşleştiğini doğrula. Dataset ve geçici dosyaları dışarıda tut.

2. Website ve Compose
- Task 1’in Flask yükleme, önizleme, dosya doğrulama ve hata yönetimini
  CIFAR10’a uyarla. Bir Baseline kartında tahmin ve ilk üç skoru göster.
  Resmi test accuracy’yi mevcut metrik JSON’undan al ve tek görselin
  tahmin skorundan ayrı etiketle.
- Baseline servis adresi yapılandırılabilir olsun. Sonraki aşamada
  optimized kartı eklenecek; şimdilik boş kart veya sahte sonuç gösterme.
- Website Dockerfile’ı, build komutu ve ayrı bir Compose proje adı kullan.
  Boşsa website için 5074, baseline Cog için 5075 kullan; yalnızca
  localhost’a aç. Optimized için 5076’yı planla ama henüz servis ekleme.
  FashionMNIST’in 5071–5073 portları ve Week 6 değişmesin.

3. Doğrula ve belgele
- Image’ları build et ve CIFAR10 servislerini başlat. Aynı
  test_00000_label_3_cat.png dosyasıyla yerel Python, doğrudan Cog HTTP
  ve website’in sınıf ve skorlarını karşılaştır. Referans: cat, ~%44,07.
  Sayısal fark varsa nedenini incele.
- Bozuk görsel sonrası geçerli tahmin yapılabildiğini ve yeni tahminin
  çalışan container içindeki log dosyasına yazıldığını doğrula.
  Uygunsa gerçek tarayıcı kontrolü de yap.
- Doğrudan CIFAR10 Cog’a giden Postman collection ve görselden istek
  gövdesi üreten yardımcıyı hazırla. Base64 çıktıları Git dışında tut.
  Postman CLI ve masaüstü uygulama kontrollerini ayrı raporla.
- README ve PROMPTS’a build/başlatma, portlar, canlı log, Postman ve
  temiz clone’dan checkpoint üretimi adımlarını ekle.

Sonuçta CIFAR10 servis durumunu, aynı PNG için Python/Cog/website
karşılaştırmasını ve çalıştırma komutlarını bildir. FashionMNIST’in
çalışmaya devam ettiğini kontrol et.

### Gerçek geliştirme sonuçları — 2026-11-09

- Branch `week7-classifiers` doğrulandı; uygulanabilir AGENTS.md bulunmadı. Task 2'nin orijinal Net modeli, preprocessing, checkpoint, ölçüm JSON'ları ve demo manifesti okundu; Task 1'in Cog/Flask/Compose/build/Postman ve test düzeni örnek alındı. Yalnız task-2 ve ortak README/PROMPTS değişti. Mevcut ortak ignore kuralları yeterliydi. Gerçek .env okunmadı; yeniden eğitim/dataset indirme/HPO veya Git add/commit/push/merge yapılmadı.
- `cog_runner.py`, `cog.yaml`, `prepare_build.py`, `build.sh`, `.dockerignore`, ayrı `compose.yaml`, website, Postman helper/collection ve servis/tarayıcı kontrolleri eklendi. Model image'ı `ee471-week7-cifar10-baseline`, website image'ı `ee471-week7-cifar10-website`, Compose projesi `ee471-week7-cifar10-baseline`. Portlar boş görüldükten sonra yalnız 127.0.0.1:5074/5075 yayınlandı. 5076 ileride optimized için planlandı; optimized image/servis/kart eklenmedi.
- Mevcut `artifacts/baseline/cifar10_last.pth` kullanıldı; 251.454 bayt, SHA256 `60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c`. Hazırlık script'i kaydı doğrulayıp izole allowlist context'e tek checkpoint, orijinal model/transform, ortak runner ve metadata'yı kopyalar. Dataset, train/evaluate/sonuç/demo/.env/venv/geçici dosyalar model image'ına girmedi. Cog'un kendi `.cog` metadata dizini tekrar hazırlıkta tanınır ama context girdilerinden dışlanır. Eksik checkpoint README'deki açık train.py komutuna yönlendiren hatayla durur; otomatik eğitim/indirme yoktur.
- Runner gerçek Net ve preprocess/CLASSES modüllerini doğrudan import eder. CPU/2 thread, bir kez setup, eval ve inference_mode; RGB32×32 ve kanal mean/std .5 korunur. Image ve runtime metadata SHA kontrolü, ağ kapalı CPU/eval setup, orijinal model/dönüşüm kaynak hash'leri, tek .pth ve eksik/yanlış hash'li checkpoint'te açık hata gerçek image içinde doğrulandı.
- Cog başarılı output biçimi `{"class":"cat","score":...,"top3":{"cat":...,"dog":...,"bird":...}}`. PNG/JPEG JSON/data URL; multipart Cog'a gönderilmez. Model logu ayrı `/var/log/ee471/cifar10-baseline.log`; stdout ve dosyada model adı, başlangıç, gerçek sonuç/ilk üç ve süre vardır. Görsel/base64 yazılmaz.
- Flask upload proxy gerçek decode/verify, tam32×32 ve 1MiB dosya/1MiB+64KiB toplam istek sınırı uygular. MIME/dosya adına güvenmez; kullanıcı dosya adını path yapmaz. `BASELINE_URL` yapılandırılabilir; Compose `http://baseline:5000`. Cog HTTP200 tek başına başarı değildir; status, sonlu/geçerli CIFAR sınıf skorları ve top-1/top-3 tutarlılığı kontrol edilir. Ağ/timeout/busy/servis/bozuk yanıt güvenli hata üretir. Tek Baseline kartı, preview, çift submit/abort/eski yanıt koruması, hata sonrası kullanım ve object URL temizliği korunur. Resmi %51,41 test accuracy, korunmuş metrics JSON'undan türetilir ve PNG skorundan ayrı gösterilir.
- İlk mock koşusu eski website 28×28 tuple kontrolünün kaldığını yakaladı; 32×32 düzeltildikten sonra testler geçti. Ek top-1/NaN/bool/bilinmeyen sınıf regresyonlarıyla son **17 website mock testi** başarılı. **4 mevcut sentetik core testi** de geçti; ilk core çağrısında yinelenmiş python argümanı yüzünden komut hata verdi, düzeltilen çağrı gerçekten dört testi çalıştırdı. Bunlar model accuracy kanıtı olarak sunulmadı.
- Gerçek model/website image build'leri exit0 ile tamamlandı ve image içi SHA orijinalle eşleşti. Cog label/schema adımında `no access allowed to dir "context"` satırı görüldü; export/build0 sonrasında offline setup ve gerçek HTTP kontrolleri ayrıca geçti. FashionMNIST image'ları değiştirilmedi.

| Aynı test_00000_label_3_cat.png | Tahmin | cat | dog | bird |
| --- | --- | --- | --- | --- |
| Yerel Python | cat | 0.44070398807525635 | 0.18100601434707642 | 0.12535478174686432 |
| Doğrudan Cog HTTP | cat | 0.44070398807525635 | 0.1810060143470764 | 0.12535478174686432 |
| Website | cat | 0.44070398807525635 | 0.1810060143470764 | 0.12535478174686432 |

- Gerçek etiket3/cat; aynı manifest PNG SHA256 `0d4964922e2463ad0e2b1cd298e03d5627ff7dad1ab1cdd173ce35e9974e204f`. Python/Cog/website aynı sınıfı ve 1e-7 toleransında aynı skorları verdi. Dog skorundaki son basamak farkı JSON sayı serileştirmesi düzeyindedir; anlamlı tahmin farkı yoktur. Referans ~%44,07 korunmuştur; %51,41 resmi test accuracy ile karıştırılmadı.
- Eksik/boş/bozuk upload, Cog'da bozuk görselin HTTP200 içindeki failed sonucu ve ardından geçerli tahmin doğrulandı. Website'ten gelen gerçek tahmin container loguna yeni Prediction completed satırı ekledi; logda base64/data:image bulunmadı. Gerçek JPEG data URL de Cog ve website'te başarılı oldu; aynı JPEG'in iki yoldaki skorları eşleşti. JPEG sıkıştırması nedeniyle PNG ile birebir skor eşitliği iddia edilmedi.
- **Gerçek Windows Chrome headless ve gerçek çalışan Cog/model:** üç gerçek form gönderimi, preview, Baseline kartının Cog sonuçlarıyla eşleşmesi, iki submit olayının tek HTTP isteğine indirgenmesi, bozuk görselde eski sonucun temizlenmesi ve ardından başarılı kullanım, eksik upload ve 375px dar ekran kontrolleri geçti. İki object URL bırakıldı; JavaScript error/unhandledrejection kaydı boştu. Bu kullanıcı tarafından yapılmış manuel tarayıcı testi değildir.
- **Postman CLI:** doğrudan 5075/predictions adresine JSON/data URL; 1 istek, 5 assertion, 0 başarısız, exit0. `--no-report-events`, login/cloud yayınlama yok. CLI login uyarısı yerel testi engellemedi. **Masaüstü Postman uygulaması kullanılmadı.** Collection/yerel ortam importu ve Send işlemi kullanıcıya kaldı. Helper uzun base64 yazdırmadan outputs altında yerel body/environment üretir; ikisi de Git dışında. Yerel dosyayı pre-request script ile keyfî okumaya çalışmaz.
- 85 korunan dosyanın hash'i aynı kaldı: FashionMNIST dosyaları ve CIFAR10'un önceden var olan checkpoint/ölçüm/demo kayıtları. FashionMNIST'in üç image ID'si, üç container ID'si ve healthy durumları korundu; 5071 ana sayfa200, 5072/5073 READY doğrulandı. Son durumda beş servis healthy: CIFAR10 website5074/baseline5075 ve FashionMNIST website5071/baseline5072/optimized5073. Week 6'ya dokunulmadı.
- `results/service-validation.json` yeni aşamanın gerçek doğrulama kaydıdır. README'ye Ubuntu build/up/ps/down, host/container adresleri, canlı log, Postman, demo sırası ve temiz clone'da build öncesi ağırlık yolu/ayrı eğitim hazırlığı eklendi. Temiz clone eğitim komutları bu aşamada çalıştırılmadı; yeni hash eski deneyle eşleşmezse eski accuracy'yi sahiplenmeden build'in duracağı belgelendi.

## Aşama 7 — CIFAR10 hiperparametre optimizasyonu

### Tam kullanıcı istemi

EE471 Week 7 – Aşama 7: CIFAR10 hiperparametre optimizasyonu.

week7-classifiers branch’inde devam et. Yalnızca Week-7/task-2 ve
Week-7’nin ortak README/PROMPTS/ignore dosyalarında çalış. Önce mevcut
CIFAR10 eğitim, değerlendirme ve inference kodunu; baseline sonuç JSON’unu
ve FashionMNIST HPO akışını incele.

Mevcut yerel CIFAR10 verisini kullan; yeniden indirme başlatma.
Baseline checkpoint ve metriklerini, FashionMNIST’i ve çalışan
Compose servislerini koru. Website/Cog değişikliği veya Git işlemi yapma.

1. Kontrollü adayları eğit
- Aynı CNN, 45.000/5.000 train/validation ayrımı, RGB normalizasyonu,
  seed 42, CPU, batch size 4 ve 2 epoch kullan. Başlangıç ağırlıklarını
  ve batch sırasını adaylar arasında aynı tut ve doğrula.
- Referans: SGD lr=0.001, momentum=0.9. Mevcut baseline kaydı bu
  protokolle uyumluysa yeniden eğitme. Uyumlu değilse farkı açıkça kaydet;
  mevcut baseline checkpoint’inin veya metriklerinin üzerine yazma.
- Dört adayı sıfırdan eğit: SGD lr=0.003 ve lr=0.01 (ikisi de
  momentum=0.9), Adam lr=0.0003 ve lr=0.001.
- Her epoch için train/validation loss ve accuracy kaydet.
  Her adayın eğitim + validation süresini ayrı ölç. Sonuçları
  results/hpo/ altında JSON olarak sakla.

2. Seç ve resmi testte ölç
- Adayları 2. epoch validation accuracy’ye göre sırala; eşitlikte
  daha düşük validation loss’u kullan. Kazananı baseline ile validation’da
  da karşılaştır. Seçimi testten önce kaydet.
- Yalnızca seçilen adayı resmi 10.000 test örneğinde değerlendir.
  Baseline’ın %51,41 accuracy ve 1,333286 loss değerleriyle aynı
  değerlendirme koşullarında karşılaştır. Accuracy farkını yüzde puan
  olarak ver. İyileşme yoksa bunu açıkça bildir; teste bakıp aday değiştirme.
- Seçilen CPU state_dict’i
  artifacts/optimized/cifar10_optimized.pth olarak kaydet.
  Ayrı bir süreçte mevcut inference koduyla yükle ve
  test_00000_label_3_cat.png üzerinde doğrula. Bu örneği seçimde kullanma.

3. Belgele
- README/PROMPTS’a yeniden çalıştırma komutlarını, aday tablosunu,
  seçim kuralını, test karşılaştırmasını ve süreleri ekle.
- Dataset, geçici ağırlıklar ve ortam dosyaları Git dışında kalsın.
- Son raporda seçilen ayarı, validation tablosunu, baseline/optimized
  test sonuçlarını, checkpoint yolunu ve demo PNG tahminini ver.

### Gerçek geliştirme sonuçları — 2026-11-09

Branch week7-classifiers ve talimatlar kontrol edildi; uygulanabilir AGENTS.md bulunmadı. CIFAR10 train/evaluate/predict, baseline metrics ve FashionMNIST HPO kodu incelendi. Yeni optimize.py ve üç seçim testi Task 2 içinde oluşturuldu. Ön denetimde kaynak/sürüm/checkpoint/split protokolü baseline ile eşleşti; SGD .001/momentum .9 baseline yeniden eğitilmedi. Baseline son validation %52.08 / loss 1.3335635150909424, test %51.41 / loss 1.333286461931467 korunmuş referans olarak alındı.

Aynı CNN/preprocess/CLASSES, seed42, CPU2threads/deterministic, batch4, num_workers0, 45000/5000 split ve 2epoch. Tüm orijinal baseline eğitim kaynak hash'leri denetlendi. Her aday yeni model/optimizer ile sıfırdan başladı. Dört başlangıç state hash'i eşleşti; gerçekte tüketilen sekiz epoch indeks sıra hash'i korunmuş baseline loader/seed protokolünden yeniden üretilen iki hash'e eşitti. Eski baseline doğrudan trace kaydı tutmadığından yeniden türetilmiş hash'ler geçmişte ölçülmüş trace gibi sunulmadı. Dataset download=False, network none ve readonly data mount ile kullanıldı; indirme yapılmadı. Gerçek optimizer defaults trial JSON'larında kayıtlı; iki SGD momentum.9, Adam betas(.9,.999)/eps1e-8/wd0/amsgradfalse.

| Aday | Son train loss | Train accuracy | Son val loss | Validation accuracy | Train+val(s) |
| --- | --- | --- | --- | --- | --- |
| SGD 0.003 | 1.422720 | %48.7889 | 1.514985 | %46.5200 | 35.20 |
| SGD 0.01 | 2.027029 | %24.6978 | 1.950872 | %27.8600 | 36.35 |
| Adam 0.0003 | 1.323596 | %52.4800 | 1.294761 | %53.3200 | 45.87 |
| Adam 0.001 | 1.315503 | %52.6444 | 1.327986 | %52.4200 | 46.40 |

Her adayın iki epoch train/validation ölçümleri results/hpo/trials/*.json ve summary.json içinde kayıtlı. Son epoch CPU state_dict'leri artifacts/hpo içinde Git dışındadır. Üç sentetik seçim testi ve dört mevcut core testi toplam7 geçti; bunlar gerçek eğitim sonuçları yerine kullanılmadı. Kaynak uyarlamasındaki örnek sayısı kontrolü çalıştırmadan önce incelenip 45000 olarak düzeltildi; gerçek koşu her epoch45000 örnek tüketimini hash ile doğruladı.

Kazanan Adam lr=0.0003, final validation %53.3200, loss 1.2947612596273421. Validation sıralaması adam_lr_0_0003, adam_lr_0_001, sgd_lr_0_003, sgd_lr_0_01; baseline'a validation farkı +1.2400 yüzde puan. En yüksek epoch2 accuracy, eşitlikte düşük validation loss kuralı kullanıldı; baseline dört yeni aday arasına eklenmedi, referansla karşılaştırıldı. selection.json test loader'ından önce frozen_at_utc ile yazıldı. Diğer adayların test alanları null kaldı; test/demo seçimde kullanılmadı.

Yalnız kazanan 10000 resmi test örneğinde CPU/batch4/shufflefalse ve aynı örnek ağırlıklı engine ile ölçüldü: loss 1.2751332348048687, accuracy 0.5424 (%54.24). Baseline karşısında accuracy farkı +2.83 yüzde puan, loss farkı -0.0581532271; sonuç iyileşti. Teste bakıp aday değiştirilmedi. Aday train+val toplamı 163.817111s; arama toplamı 167.378311s; kazanan test döngüsü 1.752236s. Baseline denetimi/cache yüklemesi arama sayacından öncedir, indirme süresi yoktur.

Final optimized artifacts/optimized/cifar10_optimized.pth: CPU state_dict, 251552 bayt, SHA256 3afe36d66e686617f7a8628b12607e6e25f4c4cc7e218338d018226943ed4c0e. Ayrı süreçte mevcut predict.py final checkpoint'i ve sabit test_00000_label_3_cat.png dosyasını yükledi: gerçek 3/cat, tahmin 3/cat, skor 0.4304862320423126; sonuç doğru. Reference_verified=true, SHA/logitler seçim/test sonrası referansla 1e-6 içinde eşleşti. Bu PNG seçimde kullanılmadı ve yanlış tahminde örnek değiştirilmedi.

Baseline checkpoint/ölçümleri, önceki Task2 website/Cog/build/Compose ve tüm FashionMNIST dosyaları koruma snapshot'ıyla kontrol edildi. Beş çalışan Compose servisi aynı container ID'leriyle healthy kaldı; HPO geçici container'ı --rm ile sonlandı. Yeni website/Cog entegrasyonu/build/deploy yapılmadı. README/PROMPTS'a protokol, aday/epoch tabloları, validation/test farkları, süreler ve eski çıktıyı ezmeyen tekrar komutları eklendi. Ortam/dataset/geçici ve final optimized ağırlıkları ortak ignore kurallarıyla Git dışında. .env okunmadı; Git add/commit/push/merge yapılmadı.

## Aşama 8 — CIFAR10 optimized Cog ve karşılaştırma ekranı

### Tam kullanıcı istemi

Kopyalanan istemdeki satır sonu ve HTML boşluk kaçışları okunabilirlik için düzenlendi; kapsam korunmuştur.

EE471 Week 7 – Aşama 8: CIFAR10 optimized Cog servisi ve karşılaştırma ekranı.

week7-classifiers branch’inde devam et. Yalnızca Week-7/task-2 ve ortak
README/PROMPTS/ignore dosyalarında çalış. Task 1’de doğrulanan iki modelli
yapıyı örnek al. FashionMNIST, Week 6, mevcut checkpoint’ler ve ölçüm
JSON’ları korunsun. Yeniden eğitim, HPO, indirme veya Git işlemi yapma.

1. Optimized Cog servisini ekle
- artifacts/optimized/cifar10_optimized.pth dosyasını ayrı bir Cog image’a
  yerleştir. İki image aynı runner, CNN, 32×32 RGB dönüşümü ve sınıf sırasını
  kullansın; her biri kendi checkpoint’ini yüklesin.
- Website 5074 ve baseline Cog 5075’i koru. Optimized Cog’u
  127.0.0.1:5076 üzerinden yayınla.
- Image içindeki her checkpoint’in SHA256’sını kaynak dosyayla karşılaştır.
  Build ve runtime’da eğitim veya veri indirme olmasın.
- Optimized tahminleri ayrı container içi loga yaz. Tahmin sınıfını ve
  süreyi kaydet; Base64 görsel verisini loglama.

2. Website’i iki modele bağla
- Bir yükleme ve bir Classify işlemi aynı görseli iki servise göndersin.
  Baseline ve Optimized kartları geniş ekranda yan yana, dar ekranda
  alt alta görünsün. Her kart en iyi sınıfı ve ilk üç skoru göstersin.
- Resmi test accuracy değerlerini ölçüm JSON’larından al: baseline
  %51,41, optimized %54,24. Bunları görselin tahmin skorundan ayrı göster.
- Bir servis başarısız olduğunda diğer kartın sonucunu koru; hatayı
  ilgili kartta göster. Yeni istekte eski sonuçları temizle.
  Dosya doğrulaması ve çift gönderim koruması sürsün.

3. Gerçek akışı doğrula ve belgele
- Build et, Compose’u çalıştır ve üç CIFAR10 servisini healthy bırak.
- Aynı test_00000_label_3_cat.png ile iki model için yerel Python,
  doğrudan Cog HTTP ve website sonuçlarını karşılaştır. Beklenen:
  iki model de cat; baseline yaklaşık %44,07, optimized yaklaşık %43,05.
  Sınıf ve skor uyumunu kontrol et, iki container’da yeni logu doğrula.
- Bozuk dosyadan sonra tekrar tahmin, dar ekran ve tek servis hatasında
  diğer kartın korunmasını kontrol et. FashionMNIST servisleri açık kalsın.
- Postman collection’a iki doğrudan Cog isteği ekle. İkisi de aynı
  PNG’den üretilen istek gövdesini kullansın; çıktılar Git dışında kalsın.
  CLI ile masaüstü Postman doğrulamalarını ayrı raporla.
- README/PROMPTS’a temiz clone’dan iki checkpoint’i hazırlama,
  build/başlatma, iki canlı log komutu ve Task-2 demo sırasını yaz.

Sonuçta üç CIFAR10 servisinin durumunu, aynı PNG’nin iki modeldeki
sonuçlarını, testleri ve benim çalıştıracağım komutları bildir.

### Gerçek geliştirme sonuçları — 2026-11-13

- Aktif branch week7-classifiers; uygulanabilir AGENTS.md bulunmadı. Mevcut Task 2 runner/build/Compose/website/ölçümleri ve Task 1'in doğrulanmış iki modelli yapısı incelendi. Task 1, checkpoint'ler, eski ölçüm JSON'ları ve demo dosyaları için hash snapshot alındı. Gerçek .env okunmadı; eğitim/HPO/model veya dataset indirme yapılmadı. Git add/commit/push/merge yoktur.
- Başlangıçta Docker motoru çalışmıyordu: dockerDesktopLinuxEngine pipe bulunamadı. Docker Desktop gizli pencere ayarıyla başlatıldı; mevcut beş container Exited durumundaydı. FashionMNIST'in üç mevcut container'ı yeni container oluşturulmadan aynı kimlikle açıldı. Başlangıçta zaten healthy/çalışır oldukları iddia edilmez. FashionMNIST kaynakları ve üç image ID'si değişmedi; Week 6'ya dokunulmadı.
- Başlangıçtaki yerel CIFAR10 cog_runner.py dosyasında Runner/setup bloğu eksik ve sözdizimi bozuktu. Bu hâl outputs/stage8-inputs/cog_runner.py içinde korundu; önceki sağlam outputs/build/baseline sürümüyle karşılaştırılarak eksik blok onarıldı. Bu başlangıç değişikliğinin kimden/nasıl geldiği hakkında varsayım yapılmadı. Onarım sırasında yinelenmiş Runner bloğu kaldı; Cog `Runner must define run() or predict()` hatası verdi. Yinelenmiş blok çıkarıldı; AST kontrolü tek Runner sınıfı ve setup/run metotlarını doğruladı. Windows Python yazımının CRLF ürettiği build.sh önce pipefail hatası verdi; LF düzeltildi ve task-2/.gitattributes içine `*.sh text eol=lf` eklendi. Başarısız denemeler başarı sayılmadı.
- prepare_build iki checkpoint'i korunmuş baseline/HPO SHA'larıyla context değişikliğinden önce doğrular. Ayrı outputs/build/baseline ve optimized bağlamlarına aynı runner, orijinal CNN/preprocess/CLASSES ve sabit requirements; her modele yalnız kendi checkpoint'i kopyalanır. Her image içinde tek /src/checkpoint.pth bulunur. Dataset/eğitim/HPO/eval kodu, sonuç/demo/.env/venv/geçici dosyalar model image'larına girmez. Cog'un kendi .cog metadata'sı tekrar hazırlamada kabul edilir fakat model girdilerinden hariçtir.
- Baseline SHA256 `60cc152fb4cf1e10dad8b870e9b3f847c7293e30a363eecba8972b4a5e1cbd7c`, optimized `3afe36d66e686617f7a8628b12607e6e25f4c4cc7e218338d018226943ed4c0e`. Gerçek iki image build'i ve final image içi SHA kontrolleri geçti. Cog 0.23.1 label/schema aşamasında yine `no access allowed to dir "context"` satırı yazdı; iki image export edildi ve build exit0 verdi. Bu satır gizlenmedi; gerçek offline setup ve HTTP/model kontrolleri ayrıca yapıldı. Son açık class log biçimi eklendikten sonra tekrar build de exit0 ve iki SHA doğrulamasıyla geçti.
- Image'lar ee471-week7-cifar10-baseline / ee471-week7-cifar10-optimized; website ee471-week7-cifar10-website. Compose proje adı ee471-week7-cifar10-baseline korundu. Host website5074/baseline5075 sabit, optimized127.0.0.1:5076 eklendi. Üçü container içinde5000 kullanır. Model pull_policy never; build/başlangıç eğitim veya veri indirme yapmaz. Kaynak bind mount yoktur.
- Ortak Runner CPU/2 thread'de bir kez state_dict yükler, hash'i kontrol eder, eval/inference_mode uygular; orijinal RGB32×32 ToTensor/kanal mean/std .5 dönüşümü doğrudan import edilir. Her image'ın runner/CNN/preprocess hash'lerinin aynı kaynaklarla eşleştiği, tek doğru checkpoint, ağ kapalı CPU/eval setup ve eksik/yanlış hash'te açık hata verdiği doğrulandı. Model adı, açık sınıf, ilk üç skor ve süre stdout ile iki ayrı dosyaya yazılır: /var/log/ee471/cifar10-baseline.log ve /var/log/ee471/cifar10-optimized.log. Base64/görsel loglanmaz.
- Website tek doğrulanmış görseli aynı data URL ile iki ayrı adrese, en fazla iki paralel istekte gönderir. İki Cog status/output/error bağımsız işlenir; sonuçlar results.baseline/optimized, üst status succeeded/partial/failed biçimindedir. Tek servis hatası diğer kartın çıktısını silmez. Yeni seçim/istek eski sonuç/hataları temizler; dosya doğrulaması32×32/1MiB ve double-submit/abort/eski yanıt/object URL korumaları sürer. Kartlar genişte yan yana, 640px altında alt alta. Resmi %51,41/%54,24 accuracy korunmuş ölçümlerden türetilip tek-görsel skorlarından ayrı gösterilir; eski baseline/HPO JSON'ları yeniden yazılmaz.

| Sabit test_00000_label_3_cat.png | Python / Cog / website tahmini | cat | dog | bird |
| --- | --- | --- | --- | --- |
| Baseline | cat / cat / cat | 0.44070398807525635 | 0.18100601434707642 | 0.12535478174686432 |
| Optimized | cat / cat / cat | 0.4304862320423126 | 0.22625336050987244 | 0.12188039720058441 |

- Gerçek sınıf3/cat, PNG SHA256 `0d4964922e2463ad0e2b1cd298e03d5627ff7dad1ab1cdd173ce35e9974e204f`. Orijinal checkpoint/modüllerle ayrı Python, doğrudan Cog HTTP ve website her modelde aynı sınıf/top3 verdi; tüm skorlar 1e-7 toleransında eşleşti. Son basamak JSON sayı serileştirme farkı dışında anlamlı fark yoktur. Beklenen %44,07/%43,05 korunmuştur; aynı sınıf sonucu için örnek değiştirilmedi. Daha yüksek resmi test accuracy'nin her tek PNG'de daha yüksek skor anlamına geldiği iddia edilmedi.
- Website'in gerçek tahmini iki container loguna birer yeni Prediction completed satırı ekledi; son image'larda açık `class=cat` ve süre doğrulandı. Base64/data:image bulunmadı. Eksik/bozuk upload, iki Cog'da bozuk resmin HTTP200 içindeki failed durumu ve ardından geçerli tahmin doğrulandı. Gerçek JPEG iki modelde Cog/website üzerinden başarılı; aynı JPEG için skorlar eşleşti. Kayıplı JPEG ile orijinal PNG arasında eşit skor iddia edilmedi.
- **18 website mock testi** geçti: aynı görsel iki adrese birer kez, hem baseline hem optimized hata durumlarında diğer sonucun kalması ve tekrar kullanım, format/boyut, timeout/busy/servis/güvenli hata, skor/top-1 tutarlılığı, iki resmi accuracy. **7 mevcut sentetik core/seçim testi** de geçti. Bu kontroller yeni gerçek eğitim doğrulaması gibi sunulmadı.
- **Gerçek Windows Chrome headless + gerçek Cog/model:** beş form gönderimi, gerçek önizleme, iki kartın Cog skorlarıyla eşleşmesi, çift submit'in tek backend isteğine indirgenmesi, iki eski sonucun temizlenmesi, bozuk dosya sonrası yeniden kullanım, eksik upload ve 375px tek sütun/taşma kontrolü geçti. Optimized servis gerçekten durduruldu: baseline sonucu kaldı, yalnız ilgili kartta hata göründü; servis yeniden başlatılıp üç servis healthy olduktan sonra iki kart da toparlandı. İki object URL bırakıldı; JS error/unhandledrejection boş. Bu kullanıcı tarafından yapılmış manuel masaüstü kontrolü olarak yazılmaz.
- Postman v2.1 collection mevcut biçimiyle korundu ve iki doğrudan JSON/data URL isteğine genişletildi. İkisi de helper'ın aynı PNG'den ürettiği prediction_body ortamını kullanır; body/environment outputs altında Git dışında. Uzun Base64 yazdırılmadı; pre-request script yerel dosyaya keyfî erişim yapmaz. **Postman CLI1.85.0: 2 istek, 10 assertion, 0 hata, exit0**, --no-report-events; login/cloud paylaşımı uyarıları yerel koşuyu engellemedi, login/publish/update yapılmadı. **Masaüstü Postman kullanılmadı**; import/environment seçimi/iki Send kullanıcıya kaldı. V3 lint, v2.1 dosyada yapılmış gibi sunulmadı.
- Son koruma kontrolünde **100 eski dosyanın** hash'i aynıydı; FashionMNIST image ve mevcut container ID'leri korundu. Ana sayfa5071 HTTP200 ve iki Fashion Cog READY doğrulandı. Altı servis healthy bırakıldı: CIFAR10website5074/baseline5075/optimized5076 ve FashionMNISTwebsite5071/baseline5072/optimized5073. Eski CIFAR10 ölçümleri, checkpoint'ler ve demo manifesti korunur.
- Yeni makinece okunabilir kayıt results/comparison-validation.json; eski results/service-validation.json/baseline/hpo JSON'ları korundu. README'ye iki checkpoint için clean-clone hazırlığı, hash uyuşmazlığında durma, iki build/üç servis/iki log, Postman ve Task-2 demo sırası eklendi. Clean-clone eğitim/HPO komutları bu aşamada çalıştırılmadı. Kullanıcının kaynak dosyaları yalnız task-2 ve ortak README/PROMPTS kapsamında değişti; Git add/commit/push/merge yapılmadı.

Son teslim kontrolünde yeni JS durum mesajındaki tipografik apostrofun Windows CP1252 ile yazıldığı ve UTF-8 taramasının bu yüzden geçmediği görüldü. Karakter ASCII apostrofla düzeltildi; yalnız website image yeniden build edilip oluşturuldu. Son gerçek headless beş-gönderim testi (optimized stop/geri açma dahil) tekrar geçti. UTF-8/AST/JSON/whitespace/merge işareti/LF kontrolü 53 Task2 metin dosyasında geçti; 100 korunan dosya hash’i aynı kaldı. Altı servis healthy, FashionMNIST image/container kimlikleri korundu. Bir encoding düzeltme sarmalayıcısı PowerShell tırnaklama hatası verdi; dosya tabanlı helper ile düzeltildi, hatalı komut başarı sayılmadı.
