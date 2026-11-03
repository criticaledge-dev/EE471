# EE471 Week 6 çalışma kaydı

Bu belge bu aşamanın kullanıcı istemini ve gerçek geliştirme sonuçlarını içerir. Önceki projelerin geçmişi taşınmamıştır. Ekli PDF genel ders teslimini tanımlar; aşağıdaki kullanıcı isteği bu aşamanın kapsamını sınırlar.

## 2026-11-03 — Başlangıç istemi (tam metin)

EE471 Week 6 çalışmasına başlıyoruz.

Ortam:
- Windows 11, Ubuntu WSL2.
- Docker Desktop çalışıyor; Ubuntu içinden Docker Client/Server erişimi doğrulandı.
- Ubuntu mimarisi x86_64.
- Ubuntu içinde Cog 0.23.1 kurulu.
- Aktif branch week6-containers olmalı.

Bu aşamada Week-6 yapısını ve Task 2’nin temel Cog modelini hazırla. Henüz website veya Task 1 uygulama kopyalarını oluşturma.

Kapsam:
- Yalnızca Week-6 içinde dosya oluştur/değiştir.
- Mevcut projeleri değiştirme.
- Gerçek .env dosyalarını okuma/kopyalama.
- Commit/push/merge veya registry’ye image push yapma.

Önce oku:
https://github.com/replicate/cog/blob/v0.23.1/docs/getting-started.md
https://github.com/replicate/cog/blob/v0.23.1/docs/python.md
https://github.com/replicate/cog/blob/v0.23.1/docs/yaml.md

Güncel main dokümanı yerine kurulu 0.23.1 sürümüyle uyumu doğrula. Komutları da kurulu CLI help üzerinden kontrol et.

Dosya yapısı:
Week-6/
  README.md
  PROMPTS.md
  .gitignore
  task-2/
    classifier/
      cog.yaml
      requirements.txt
      run.py
      .dockerignore
      gerekiyorsa model ağırlığı hazırlama yardımcısı

Model:
- Verilen Cog başlangıç örneğindeki ResNet50,
  ResNet50_Weights.IMAGENET1K_V1 ve ağırlıkların kendi transforms/categories bilgilerini kullan.
- İlk hedef CPU. CUDA/GPU zorunlu olmasın; gereksiz CUDA bağımlılıkları indirme.
- Cog/Python/torch/torchvision/Pillow sürümlerini uyumlu seç ve sabitle.
- Runner(BaseRunner), setup ve run biçimini kullan.
- setup modeli bir kez yüklesin, eval moduna alsın.
- run görseli RGB’ye dönüştürsün, doğru dönüşümü uygulasın,
  gradyan hesaplamadan tahmin yapsın ve en yüksek üç sınıfın skorunu döndürsün.
- Bu genel ImageNet modelini tüm kedi ırklarını tanıyan özel model gibi sunma.
- Bozuk görselde anlaşılır hata ver; tahmin uydurma.

Ağırlıklar ve image:
- Ağırlıkları Git’e ekleme.
- Container yeniden oluşturulduğunda her seferinde tekrar indirmek zorunda kalmayacağımız açık bir strateji uygula.
- Mümkünse ağırlıkları build sırasında hazırla; modelin runtime cache yoluyla aynı olduğunu doğrula.
- .dockerignore ile runtime’da gerekli ağırlıkları yanlışlıkla dışlamamaya dikkat et.
- .env, sanal ortamlar ve geçici çıktılar build context’e girmesin.
- Modelin gerçek ağırlıkları yüklediği doğrulanmadan mock testi başarı kanıtı sayma.

Log:
- Model yükleme ve her gerçek tahmin için kısa log üret.
- Tahmin sonucundaki sınıf/skorlar hem stdout’a hem container içinden
  okunabilecek bir log dosyasına yazılabilsin.
- Log dosyasının yolunu belgele; sonradan demo sırasında docker exec ile okuyacağız.
- Base64 görsel içeriğini loglama.

Doğrulama:
- Ortama erişebiliyorsan WSL üzerinden Cog/Docker komutlarını çalıştır.
- Docker Desktop ile entegre mevcut motoru kullan; Ubuntu içine ayrıca Docker Engine kurma.
- Resmî örnek görseli indirip gerçek model tahmini al.
- Image adı: ee471-week6-classifier.
- HTTP kontrolünde host 5064 → container 5000 portunu kullan.
- /predictions endpoint’ini gerçek istekle doğrula.
- İlk build sürebilir; aşamaları ve gerçek hataları görünür raporla.
- WSL/Docker’a erişimin yoksa bunu açıkça belirt; yapılmamış build/tahmini yapılmış gösterme. Kullanıcı için Ubuntu komutlarını hazırla.

README:
- Bu aşamanın amacı ve kullanılan model.
- Hangi komutun PowerShell, hangisinin Ubuntu terminalinde çalışacağı.
- Repo mevcut Windows/OneDrive konumundaysa WSL yolu için doğru ve tırnaklı örnek.
- Build, CLI tahmin, HTTP çalıştırma ve container içi log görüntüleme.
- Gerçek test sonuçları ve kalan işler.

PROMPTS:
- Bu istemi ve gerçek geliştirme sonuçlarını kaydet.
- Önceki projelerin geçmişini yeni çalışma geçmişi olarak kopyalama.

Son rapor:
Oluşturulan dosyalar, seçilen sürümler, ağırlık stratejisi,
gerçek build/tahmin sonuçları veya erişim engelleri ve sıradaki komutlar.

## Geliştirme sonuçları

- Başlangıç branch'i `week6-containers`, çalışma ağacı temizdi. Uygulanabilir AGENTS.md bulunmadı.
- PDF okundu; website/Task 1 dahil geniş ders kapsamı bu aşamada uygulanmadı.
- Web aracı sürüm belgelerini açamadı. Aynı v0.23.1 etiketli üç resmi raw dosya WSL curl ile okundu; güncel main içeriğiyle değiştirilmedi.
- WSL başlangıçta sandbox altında E_ACCESSDENIED verdi; izinli çağrı ile Ubuntu, Cog 0.23.1, x86_64 ve mevcut Docker Desktop motoruna erişildi.
- `cog --help`, `build --help`, `run --help`, `predict --help` gerçek kurulu CLI üzerinden incelendi.
- CPU torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0; container Python 3.12.9 ve Cog SDK 0.23.1 seçildi. PyTorch resmi CPU eşleşmesi kontrol edildi.
- İlk build komutu iki birbirini dışlayan base-image seçeneği nedeniyle reddedildi. `--use-cog-base-image=false` bırakılarak build tekrar başlatıldı; CUDA tabanı gerekmedi.
- Ağırlık build katmanında `/opt/ee471/torch/hub` altında hazırlanır; runtime aynı yolu kullanır. Eksik ağırlıkta rastgele model veya sessiz indirme yoktur.
- PDF okuma aracı için Windows pip denemesi bağlantı reset'iyle başarısız oldu; küçük wheel WSL üzerinden geçici indirildi, PDF okundu, wheel silindi. Proje runtime bağımlılığı eklenmedi.
- `cog build -t ee471-week6-classifier --progress plain --use-cog-base-image=false` başarılı oldu (exit 0). İlk build gerçek CPU bağımlılıklarını ve yaklaşık 98 MiB checkpoint'i indirdi. İkinci build'de bağımlılık ve ağırlık komutu `CACHED` idi; tekrar indirme yoktu.
- Her iki başarılı build'in son etiketleme adımında BuildKit `no access allowed to dir "context"` satırı gösterdi. Komut yine exit 0 ile bitti ve etiketli image sonraki gerçek kontrollerde çalıştı. Bu mesajın iç nedeni doğrulanmadı; sessizce başarılı diye gizlenmedi.
- Resmi görsel indirildi. `cog run ee471-week6-classifier -i image=@test-data/input.jpg` gerçek ağırlıklarla başarılı oldu: tiger cat 0.4597228467464447, Egyptian cat 0.3693339228630066, tabby 0.16575656831264496. Kategori adları ağırlığın gerçek metadata'sından gelir; eski belge çıktısına benzetmek için değiştirilmedi.
- İzole test container'ı host 127.0.0.1:5064 → container 5000 ile açıldı. Gerçek `/predictions` isteği yerel görselin data URI'siyle gönderildi; payload veya base64 çıktılanmadı. HTTP 200 / `status: succeeded` ile CLI'daki aynı sonuç alındı.
- Bozuk görselde HTTP 200 / `status: failed`, null çıktı ve `Invalid or unreadable image` hatası doğrulandı. Sonraki geçerli istek başarılıydı; sahte tahmin üretilmedi.
- `docker exec` ile `/var/log/ee471/classifier.log` okundu: model yükleme, iki gerçek başarılı tahminin sınıf/skorları ve bozuk görsel uyarısı vardı; base64/görsel içeriği yoktu. Aynı model stdout kayıtlarının container loglarına ulaştığı kontrol edildi.
- Geçici doğrulama yardımcısı önce `/` yanıtında READY beklediği için zaman aşımına uğradı; gerçek index yanıtındaki `/health-check` kullanılarak düzeltildi. İkinci denemede gerçek HTTP/görsel/log dosyası kontrolleri geçti fakat yalnız stdout'u okuyan `docker logs` kontrolü başarısız oldu. Cog model stdout'unu yakalayıp yapılandırılmış logunu stderr'e verdiğinden test iki kanalı okuyacak şekilde düzeltildi. Son toplu doğrulama exit 0 ile tamamlandı. Model kodunda bu kontroller için davranış değiştirilmedi.
- Yeni bir container'da `--network none` ile model setup gerçek checkpoint'i yükledi; runtime hub yolu, checkpoint varlığı/boyutu, eval modu, CPU build ve `nvidia-*` bağımlılığı olmadığı doğrulandı. Cog 0.23.1, torch 2.6.0+cpu, torchvision 0.21.0+cpu, Pillow 11.1.0 gerçek kurulu metadata ile karşılaştırıldı.
- Kaynak sözdizimi, satır sonu boşlukları ve ignore kuralları kontrol edildi. Test görseli/yardımcısı/sonucu Git ve build context dışında tutulan yerel test klasörlerindedir; teslim kaynakları yedi dosyadır. Test container'ları temizlendi; image ve build cache bırakıldı.
- Bunlar gerçek CPU model/build/CLI/HTTP kontrolleridir; mock başarıları modelin yüklendiği kanıtı olarak kullanılmadı. Website, Task 1 kopyası ve demo videoları bu aşamanın kapsamı dışında kaldı. Gerçek `.env` okunmadı; yalnız Week-6 altında dosya oluşturuldu. Git stage/commit/push/merge ve registry push yapılmadı.

## 2026-11-03 — Website, Compose ve Postman istemi (tam metin)

Week 6 — Task 2: çalışan Cog sınıflandırıcısına web sitesi, Compose ve Postman doğrulaması ekle.

Önce mevcut dosyaları oku:
- Week-6/README.md ve PROMPTS.md
- task-2/classifier/cog.yaml, requirements.txt, run.py ve .dockerignore
- Gerçek HTTP yanıt şeması ve mevcut log yolu

Mevcut doğrulanmış ortam:
- Cog 0.23.1
- ee471-week6-classifier image’ı CPU üzerinde çalışıyor.
- Model ağırlıkları image içinde; runtime indirmesi gerekmiyor.
- POST /predictions çalışıyor.
- Model logu: /var/log/ee471/classifier.log

Kapsam:
- Branch week6-containers.
- Yalnızca Week-6 içinde değişiklik yap.
- Çalışan model, bağımlılık sürümleri ve ağırlık stratejisini gereksiz değiştirme.
- Henüz Task 1’i oluşturma.
- .env okuma; commit/push/merge veya registry push yapma.

1. Web sitesi
Week-6/task-2/website içinde küçük bir Flask uygulaması oluştur:
- Görsel seçme.
- Seçilen görselin önizlemesi.
- Classify düğmesi.
- Yükleniyor, başarı ve hata durumları.
- En yüksek sınıf ve mevcut modelin döndürdüğü ilk üç sınıf/skor.
- Skorları yüzde olarak göster; gerçek sonuçları kullan.
- Bunun ImageNet tabanlı bir sınıflandırıcı olduğunu kısa ve anlaşılır biçimde belirt.
- Kedi dışı görselleri zorla bir kedi sınıfına eşleme.
- Sade, okunabilir ve dar ekrana uygun görünüm yeterli.

2. Website → Cog bağlantısı
- Tarayıcı dosyayı website backend’ine göndersin.
- Backend görseli doğrulayıp Cog’a JSON input.image data URL biçiminde iletsin.
- Cog’a multipart gönderme.
- Cog adresini yapılandırılabilir yap; Compose içinde
  http://classifier:5000 kullan.
- Cog yanıtındaki status/output/error alanlarını gerçek şemaya göre işle.
- HTTP 200 tek başına tahmin başarısı sayılmasın; failed sonucu başarı gösterilmesin.
- Ağ, timeout, servis hazır değil ve geçersiz yanıt durumlarında anlaşılır hata ver.
- Otomatik sınırsız retry yapma.
- Eksik dosya, bozuk görsel ve aşırı büyük yüklemeleri reddet.
- JPEG/PNG desteği ve açık dosya/piksel sınırları uygula.
- Dosya adına veya MIME türüne tek başına güvenme.
- Kullanıcı dosya adını doğrudan sunucu dosya yolu olarak kullanma.
- Base64 içeriğini loglama.
- Başka dosya seçildiğinde eski sonuç/önizleme doğru temizlensin.
- Aynı anda tekrar gönderimi engelle.

3. Container ve Compose
- Website için Dockerfile, requirements.txt ve .dockerignore ekle.
- Website container içinde erişilebilir arayüzde dinlesin.
- Website host adresi: http://localhost:5063
- Cog host adresi: http://localhost:5064
- Host portlarını 127.0.0.1’e bağla.
- task-2/compose.yaml iki servisi aynı ağda başlatsın.
- Classifier, daha önce Cog ile üretilen ee471-week6-classifier image’ını kullansın.
- Website Dockerfile ile build edilsin.
- Classifier için sıradan Dockerfile ile ikinci ve farklı model image’ı oluşturma.
- Kaynakların doğru sırası belgelensin:
  önce cog build, sonra website build/Compose up.
- Image eksikse onu registry’den yanlışlıkla indirmeye çalışma; açık hata/talimat ver.
- Mevcut doğrulama container’ını kontrol et. 5064 çakışıyorsa yalnızca bu çalışmaya ait container’ı durdur/kaldır; diğer projelere dokunma.
- Sağlık kontrolü kullanırsan Cog 0.23.1’de gerçekten var olan endpoint’i doğrula.
- Gerçek .env, sanal ortam ve geçici çıktıları image’a alma.

4. Log gösterimi
- Mevcut model logunu koru.
- Web sitesinden yapılan gerçek tahminin bu loga yazıldığını doğrula.
- README’ye container içine girerek canlı izleme komutlarını ekle:
  docker compose exec classifier sh
  ardından container içinde mevcut log dosyasını tail -f ile izleme.
- Bu gerçek tahmin logu olmalı; örnek/sahte log üretme.

5. Postman
Week-6/task-2/postman içinde içe aktarılabilir collection oluştur.
- İstek doğrudan http://localhost:5064/predictions adresine gitsin;
  website endpoint’ine değil.
- Content-Type application/json.
- Body input.image alanında yerel görselin base64 data URL’si.
- Kullanıcıya uzun base64 metnini elle yazdırma.
- Yerel görseli Postman’da kullanılacak JSON gövdesine dönüştüren küçük yardımcı araç ve açık adımlar hazırla.
- Üretilen görsel/base64/request dosyalarını Git dışında tut.
- Postman’ın yerel dosyayı pre-request script içinden keyfî biçimde okuyabildiğini varsayma.
- Collection’da succeeded ve gerçek output için kontroller ekle.
- Gerçek Postman uygulamasını kullanamıyorsan bunu belirt.
  curl/Python doğrulamasını Postman testi yapılmış gibi raporlama.

6. Gerçek doğrulama
- Website image’ını build et.
- İki servisi Compose ile çalıştır.
- Tarayıcıdan gerçek görsel yükleyip gerçek model tahmini al.
- Sonucun mevcut Cog yanıtıyla eşleştiğini kontrol et.
- Yeni tahminin container içi loga geldiğini doğrula.
- Cog’a doğrudan JSON/data URL isteğini doğrula.
- Bozuk görsel, eksik dosya ve Cog bağlantı hatasını kontrol et;
  hata sonrasında tekrar kullanım çalışsın.
- Mock kontroller ile gerçek model kontrollerini ayır.
- Son durumda hangi servislerin çalıştığını bildir.

7. Belgeler
README:
- PowerShell ve Ubuntu komutlarını açıkça ayır.
- Kurulum/build/başlatma/durdurma.
- İki adres ve servislerin bağlantısı.
- Postman adımları.
- Container içi canlı log gösterimi.
- Task-2-demo.avi için kısa ve uygulanabilir gösterim sırası.

PROMPTS:
- Bu istemi, gerçek bulguları ve yapılan doğrulamaları kaydet.

Sonuçta dosyaları, gerçek test sonuçlarını, Postman’da kullanıcıya kalan adımları ve çalıştırma komutlarını bildir.

## Website/Compose/Postman geliştirme sonuçları

- Branch `week6-containers` idi. Önceki Week-6 dosyaları untracked durumdaydı; silinmedi veya geri alınmadı. Uygulanabilir AGENTS.md yoktu. Başlangıçta Docker container listesi boştu; 5064 için başka container durdurulmadı.
- Classifier kaynakları, Cog/Python/torch/torchvision/Pillow sürümleri ve image içindeki ağırlık stratejisi korundu. Yeni model image'ı veya Task 1 oluşturulmadı.
- Flask website `POST /api/classify` üzerinde multipart `image` alır, Pillow ile JPEG/PNG yapı/decode kontrolü yapar; 5 MiB, 12 milyon piksel ve 6000 piksel/kenar sınırı uygular. Dosya adı veya bildirilen MIME doğruluk kaynağı değildir; kullanıcı adıyla dosya kaydedilmez. Doğrulanan görsel Cog'a JSON `input.image` data URL'si olarak gönderilir; base64 loglanmaz.
- Gerçek Cog yanıtı bu aşamada tekrar gözlendi: üst alanlar `id`, `logs`, `metrics`, `output`, `status`. Başarıda output üç sınıf/skordur. Website ham servis log/hatalarını iletmez; HTTP 200/failed veya eksik/geçersiz output başarı değildir. İlk mock denemesinde eksik status alanının 503 olarak sınıflandırılması yakalandı ve geçersiz yanıt için 502 olacak şekilde düzeltildi.
- Website image'ı gerçek Docker build ile üretildi. Compose mevcut classifier image'ını `pull_policy: never` ile kullanır. Website için Flask 3.1.2, requests 2.32.5, Pillow 11.1.0, gunicorn 23.0.0 ve Python 3.12.9 seçildi. Website build context'i allowlist ile yalnız runtime dosyalarını alır; gizli/ortam/geçici dosyalar ayrıca dışlanır.
- İki servis `ee471-week6-task2` Compose projesinde açıldı: localhost 5063 website, 5064 Cog; host bind 127.0.0.1. Backend URL `http://classifier:5000`. Gerçek `/health-check` READY ve website `/healthz` kontrolleri kullanıldı. `start.sh` önce yerel model image'ını kontrol eder, yoksa Cog build talimatıyla durur; model registry pull'ı yapmaz.
- Son ağsız Python test koşusu **14/14 başarılı**. Cog HTTP yanıtları mock edildi; geçerli/geçersiz görsel, request/file/pixel sınırları, schema/skor, failed, busy, timeout, connection, non-cat sonuç ve tekrar kullanım kontrol edildi. Bu mock koşusu modelin gerçek çalışmasının kanıtı olarak sunulmadı.
- Test multipart kaynaklarının temizliğinde önce ResourceWarning görüldü. Yardımcıyı değiştirirken EnvironBuilder'ın context-manager olmaması ve `input_stream` alanının None olması kaynaklı iki test-yardımcısı hatası oluştu. Gerçek `get_environ()['wsgi.input']` finally içinde kapatılıp builder `closing()` ile temizlendi. Son 14 test ve stack koşusu uyarısız ve exit 0 ile bitti; bu hatalar çalışan model kaynaklı değildi.
- Gerçek HTTP stack kontrolünde Postman yardımcısının ürettiği JSON doğrudan Cog'a gönderildi: HTTP 200/succeeded. Website'e gerçek multipart upload da aynı değerleri verdi: tiger cat 0.4597228467464447, Egyptian cat 0.3693339228630066, tabby 0.16575656831264496. Website isteğiyle container logundaki başarılı tahmin sayısı tam bir arttı; gerçek log okundu ve base64 olmadığı kontrol edildi.
- Eksik görsel 400, bozuk görsel 400 ve büyük dosya 413 gerçek website HTTP istekleriyle kontrol edildi. Yalnız bu Compose projesinin classifier servisi durdurulduğunda website 503 bağlantı hatası verdi; finally ile classifier yeniden açıldı ve gerçek tahmin tekrar başarılı oldu.
- Gerçek Windows Chrome headless, gerçek Compose website ve gerçek modelle ayrı kontrol yapıldı: dosya input'undan gerçek dosya seçildi, önizleme decode edildi, gerçek form Classify olayıyla tahmin başlatıldı, doğrudan Cog sonucuyla ilk üç yüzde ve üst sınıf eşleştirildi. Hızlı ikinci submit ikinci isteğe dönüşmedi. Bozuk dosya sonrası eski sonuç gizlendi, hata gösterildi, geçerli dosyayla toparlanma çalıştı. Toplam üç gerçek form submit, iki preview URL temizliği, eksik dosya backend hatası ve 375 piksel görünüm kontrol edildi; JavaScript error/unhandledrejection listesi boştu. Bu headless otomasyondur, insanın yaptığı manuel görsel değerlendirme değildir.
- İçe aktarılabilir Postman collection doğrudan `http://localhost:5064/predictions` adresine JSON gönderir; HTTP 200, succeeded ve üç gerçek skor için testler içerir. Standart Python kütüphaneli `make_request.py` local request/environment JSON'larını üretir. Dosya okumak için Postman sandbox'ında keyfî erişim varsayılmaz; kullanıcı environment'i import/seçer veya JSON'u binary body dosyası olarak seçer.
- Gerçek Postman masaüstü uygulamasına erişilip Send yapılmadı. Üretilen JSON ve environment eşitliği kontrol edilip JSON Python HTTP isteğiyle gerçek Cog'da doğrulandı; bu Postman uygulaması testi olarak raporlanmadı. Kullanıcıya import/environment seçimi/Send/Test Results ve demo kaydı kaldı.
- README'ye PowerShell/Ubuntu ayrımı, tırnaklı WSL yolu, build sırası, iki adres, sağlık/log komutları, Postman adımları ve Task-2-demo.avi gösterim sırası eklendi. Önceki aşamada website'in henüz bulunmadığını söyleyen tarihsel PROMPTS kayıtları korundu; bunlar o aşamanın durumudur.
- Son durumda classifier ve website Compose servisleri healthy ve açık bırakıldı; Chrome headless kapatıldı. Son model image kimliği önceki doğrulanmış `sha256:1a67563989f05d91a2a419a5530eb14baf065f765b4733ab3525d1b0950099d9` ile aynıydı. Gerçek `.env` okunmadı, başka projeler değiştirilmedi; stage/commit/push/merge veya registry push yapılmadı. Üretilen base64/image/request/profile/test çıktıları Git ve build context dışında tutulur.

## 2026-11-03 — Task 1 container istemi (tam metin)

Week 6 Class Exercise Task 1’i uygula: mevcut Week 5 Speech Studio ve sesli hesap makinesini Docker container’larında çalıştır.

Önce mevcut kodları, repo talimatlarını ve git durumunu incele. Aktif branch week6-containers olmalı. Mevcut Week-6 Task 2 çalışmalarını koru. Yalnızca Week-6 içinde değişiklik yap; kaynak Week 5 projelerini değiştirme. Commit/push/merge yapma.

1. Kaynakları incele ve kopyala
- Week-5-Task-1: Speech Studio.
- Week-5-Task-2: sesli hesap makinesi.
- Uygulama için gerekli kaynakları şu klasörlere kopyala:
  Week-6/task-1/speech-studio/
  Week-6/task-1/voice-calculator/
- .env, .venv, .test-deps, node_modules, önbellekler, üretilmiş sesler ve geçici dosyaları kopyalama.
- Gerçek .env dosyalarını okuma veya değerlerini çıktıya yazma.
- Uygulama davranışını koru. Docker için gereken değişiklikleri yalnızca yeni kopyalara uygula.

2. Her uygulama için Dockerfile ve .dockerignore oluştur
- Azure Speech SDK ile uyumlu, glibc tabanlı resmi Python image’ı kullan.
- Python sürümünü mevcut kaynakların ve SDK’nın desteğine göre seç.
- Linux sistem bağımlılıklarını resmi Microsoft belgeleriyle doğrula; tahmin ederek paket ekleme.
- Mevcut Python bağımlılıklarını koru; gereksiz sürüm yükseltmesi yapma.
- Önce bağımlılıkları, ardından kaynakları kopyalayarak build cache kullanımını sağla.
- Anahtarları Dockerfile, ARG, ENV veya image katmanlarına koyma.
- Sunucu container içinde 0.0.0.0 üzerinde çalışmalı.
- Debug/reloader kapalı olmalı.
- Speech Studio’nun Flask-Sock WebSocket akışı çalışmalı. Mevcut işlem kilitleri nedeniyle tek process kullan; HTTP ve WebSocket akışları için uygun threading sağla.
- Yeni bir production sunucusu eklemek zorunlu değil; ders demosu için mevcut sunucuyu uygun şekilde başlatabilirsin.

3. Week-6/task-1/compose.yaml oluştur
- İki bağımsız servis:
  speech-studio: host 127.0.0.1:5061
  voice-calculator: host 127.0.0.1:5062
- İki container da kendi içinde 5000 portunu kullanabilir.
- Task 2 Compose projesi, servisleri ve portlarıyla çakışmasın.
- Kaynak klasörlerini bind mount etmeden, build edilmiş image’lardan çalıştır.
- Azure SPEECH_KEY ve SPEECH_REGION değerlerini yalnızca çalışma anında al.
- Kullanıcının task-1 klasöründe oluşturacağı, Git dışında kalan ortak .env dosyasını runtime env_file olarak kullanabilirsin.
- Gerçek değer içermeyen .env.example oluştur.
- Eksik ayarlarda anlaşılır hata ver; anahtarı loglama.
- Gizli değerleri açığa çıkarabilecek docker compose config çıktısını yazdırma.
- Ana sayfayı kullanan, Azure isteği yapmayan healthcheck ekle.

4. Mevcut özellikleri koru
Speech Studio:
- TTS, STT, speech translation, pronunciation assessment ve canlı diarization.
- Mevcut 16 kHz WAV uyumluluğu ve doğrulama sınırları.
- /ws/diarization WebSocket yolu ve kaynak temizliği.
- Frontend API/WebSocket adresleri ziyaret edilen host ve portla uyumlu olmalı.
- Origin kontrolü varsa localhost:5061 ile uyumunu incele; güvenlik kontrolünü tamamen kaldırma.

Sesli hesap makinesi:
- Elle hesaplama, sesli giriş, komut ayrıştırma ve Azure TTS.
- Ses kuyruğu, önbellek, iptal ve mikrofonla çakışmama davranışları.

Mikrofon ve hoparlör tarayıcıda kullanılmaya devam etmeli. Container’a ses cihazı bağlama veya privileged yetki ekleme.

5. Gerçek Docker doğrulaması yap
- Her iki image’ı build et.
- Gerçek anahtarları okumadan, gerekiyorsa açıkça sahte test değerleriyle servisleri başlat.
- İki container’ın çalıştığını, ana sayfaları ve gerekli statik dosyaları doğrula.
- Container içinde Azure SDK importunu ve gerekli native kütüphanelerin yüklenmesini kontrol et; mümkünse sahte ayarlarla SDK nesnesi oluşturulmasını da doğrula. Gerçek Azure çağrısı yapma.
- Speech Studio WebSocket yolunu, bağlantı/temizlik davranışını ve yeni host portuyla Origin uyumunu uygun mock kontrolleriyle doğrula.
- Mevcut ilgili testleri çalıştır. Container uyumluluğuna ilişkin gerekli kontrolleri ekle; uygulama mantığını tekrar eden gereksiz testler ekleme.
- Testte sahte ayarlarla başlatılan container’ları sonunda durdur; kullanıcı gerçek .env ile başlatacak.
- Task 2 container’larını durdurma.
- Başarılı build veya mock testini gerçek Azure/mikrofon doğrulaması olarak sunma.

6. Belgeler
Week-6/README.md ve PROMPTS.md dosyalarını mevcut Task 2 kayıtlarını koruyarak güncelle.
Şunları açıkça yaz:
- Ubuntu/WSL terminalinde tam klasör yolu.
- .env.example üzerinden yerel .env oluşturma.
- Build, başlatma, durum, log ve durdurma komutları.
- İki uygulamanın adresleri.
- Tarayıcı mikrofonunun localhost üzerinden kullanılması.
- Her uygulama için kısa gerçek Azure manuel test listesi.
- Task-1-demo.avi için build → container durumu → iki uygulamanın çalışması sırası.
- Gerçekten yapılan kontroller ve henüz yapılmayanlar.

Sonuçta değişen dosyaları, doğrulama sonuçlarını ve benim çalıştıracağım komutları bildir. Gerçek .env okuma; commit/push/merge yapma.

## Task 1 geliştirme ve gerçek doğrulama sonuçları

- Başlangıç branch'i `week6-containers`. Var olan untracked `.postman/`, `postman/` ve `Week-6/` durumları incelendi; kullanıcı değişiklikleri silinmedi. Uygulanabilir AGENTS.md bulunmadı. Task 2 website ve classifier container'ları 5063/5064 üzerinde çalışıyordu; durdurulmadı.
- Kaynak Week 5 uygulamaları, ilgili testler, dotenv yükleme, PCM sınırları, frontend URL'leri ve Origin kontrolü okundu. Yalnız gerekli app/servis/Calculator/requirements/templates/static ve Python/Node testleri seçilerek 44 dosya kopyalandı. Gerçek `.env`, ortamlar/cache, üretilmiş sesler, önceki README/PROMPTS veya konsol örneği taşınmadı. Kaynak dosyaların hash'leriyle kopyalar ve özgün dosyaların korunması kontrol edildi.
- Kaynak ortamların yalnız paket metadata'sı okundu: Flask 3.1.3, python-dotenv 1.2.4, Speech SDK 1.53.0; Studio için flask-sock 0.7.0. Bu değerler yeni constraints.txt dosyalarında tutuldu; kaynak requirements dosyaları aynen korundu. Tam transitif lock eklenmedi.
- Microsoft Python SDK kurulum belgelerinde Debian 12, Python 3.8+ ve glibc/pthreads/OpenSSL/ALSA/sertifika gereksinimleri doğrulandı. Resmi Python 3.12.9-slim-bookworm tabanı; runtime ca-certificates/libssl3/libasound2 kullanıldı. SDK wheel'leri için gerekmeyen derleyici/dev başlıkları/wget kurulmadı. İki image gerçek Docker build ile başarılı üretildi.
- Runtime app/servis/static/template kodları değiştirilmedi. Yeni container_server.py ile mevcut Flask app tek process/threaded=True, 0.0.0.0:5000, debug=False, use_reloader=False başlatılır. Root olmayan kullanıcı kullanılır; production sunucusu eklenmedi. Bu yerel ders demosudur.
- Compose projesi `ee471-week6-task1`: host 127.0.0.1:5061 ve 5062, bağımsız Task 1 ağı. Uygulamalar build edilmiş image'lardan, kaynak bind mount'u veya ses cihazı/privileged yetki olmadan çalışır. Normal kullanımda ortak task-1/.env yalnız env_file üzerinden runtime'a gelir; boş anahtarlı .env.example hazırlandı. Gerçek dosya oluşturulmadı veya okunmadı. Secrets Dockerfile/ARG/ENV/build context'e konmadı; config/env dökümleri yazdırılmadı.
- Ayrı offline Compose override `env_file: !reset []` ve `--env-file /dev/null` ile gerçek .env'yi tamamen devre dışı bırakır, boş SPEECH_KEY/SPEECH_REGION verir. Native SDK constructor testleri açıkça sahte sabit değerlerle, `--network none` altında çalıştırıldı; start/speak/recognize çağrılmadı.
- İlk native taramada yalnız `libMicrosoft.CognitiveServices.Speech.extension.codec.so` için GStreamer/GLib bağlantıları eksik çıktı. Core SDK'nın gerçek ldd çıktısında eksik yoktu. Microsoft sıkıştırılmış ses belgesi bu codec'in sıkıştırılmış formatlar için olduğunu doğruladı. Bu uygulamalar sadece PCM/WAV kullandığından gereksiz GStreamer eklenmedi; test kapsamı bu eklentiyi açıkça opsiyonel raporlayacak, diğer eksikleri reddedecek şekilde düzeltildi. Temel SDK/OpenSSL/ALSA yüklemeleri ve gerçek nesne oluşturma kontrolleri geçti; tüm opsiyonel codec'ler kurulu diye raporlanmadı.
- İki image içinde SDK 1.53.0 import, native bağımlılıklar, SpeechRecognizer/SpeechSynthesizer/TranslationRecognizer/ConversationTranscriber/PronunciationAssessmentConfig(apply_to) oluşturma kontrol edildi. Tek process/threaded başlangıç bayrakları patch ile, image'da .env/ortam/test kaynaklarının bulunmaması ise dosya varlığı kontrolüyle doğrulandı.
- Mevcut kopya testleri gerçek Linux image'ları içinde mock SDK ile çalıştı: **Speech Studio 80 Python**, **hesap makinesi 21 Python** testi başarılı. Kaynak test istemcilerinin kapatmadığı dosyalara ilişkin ResourceWarning görüldü; başarısızlık değildi ve kaynak testler uyarıyı gizlemek için değiştirilmedi.
- Kopyada Node kontrolleri: **Speech Studio 14**, **hesap makinesi 40** test geçti. Bunlar DOM/medya/Azure mock veya saf PCM/parser/cache kontrolleridir; gerçek mikrofon veya ses duyulması değildir.
- İlk gerçek WebSocket testinde 403 alındı. Test istemcisi simple-websocket Client'ın kurulu handshake kaynağı incelendi: bağlantıda portu kullanmasına rağmen Host başlığına yalnız hostname yazıyordu. Bu bir uygulama Origin hatası diye sunulmadı; koruma kaldırılmadı. Testte standart kütüphaneli, sınırlı beklemeli WebSocket istemcisiyle tarayıcı gibi Host:port gönderildi.
- Gerçek Flask-Sock taşıması + SDK spec mock'larıyla localhost:5061 / doğru Origin kabul edildi; yanlış port/host 403 oldu. WebSocket açıkken HTTP ana sayfası 200, diğer konuşma isteği 409 busy verdi. Kesin sonuç ve stop sırasında gelen tail sonucu sırayla, tamamlanma temizlikten sonra iletildi; bağlantı kopması sonrası stream/dinleyici/kilit temizliği ve yeni oturum kullanılabilirliği doğrulandı. Kaynak /ws/diarization yolu, Origin algoritması ve frontend location.host/göreli API yolları değişmedi.
- Gerçek Compose kontrolünde iki Task 1 container'ı healthy oldu. 5061/5062 ana sayfaları ve tüm gerekli static JS/MJS/CSS dosyaları (byte içeriği ve JS MIME) doğrulandı. Elle API `4 × 6 = 24` ve sıfıra bölme davranışı korundu. Boş ayarla konuşma isteği açıklayıcı 503 verdi; host localhost:5061 üzerinden gerçek WebSocket upgrade → eksik ayar mesajı → kapanma kontrol edildi. Gerçek Azure çağrısı yapılmadı.
- Başarılı kontrol sonunda Task 1 test container'ları ve ağı finally ile kaldırıldı. Task 2 container kimlikleri test öncesi/sonrası aynı kaldı, iki servis çalışmaya devam etti. Image'lar kullanıcı gerçek .env ile başlatabilsin diye yerelde bırakıldı.
- README'ye Task 1 tam WSL yolu, ayar/build/up/ps/log/stop/down komutları, localhost mikrofon kullanımı, her uygulama için gerçek Azure manuel test listesi ve Task-1-demo.avi sırası eklendi. Task 2 belgeleri ve eski aşamaların o zamanki kapsam kayıtları korundu.
- Bu aşamada gerçek Azure/mikrofon/hoparlör veya Task 1 gerçek tarayıcı donanım testi yapılmadı. Eski Week 5 kullanıcı doğrulamaları yeni Docker kopyasının manuel kanıtı sayılmadı. Yeni manuel deneme kullanıcıya kaldı. Yalnız Week-6 içinde değişiklik yapıldı; commit/push/merge veya registry push yapılmadı.
- Son kontrol: 44 kaynak/test dosyasının hem asılları hem kopyaları ilk hash'lerle eşleşti. Python sözdizimi ve yeni Docker/test/belgelerin boşluk kontrolleri geçti. Kaynak custom_classes.py satır 8'in eski trailing whitespace'ı ilk genel taramada görüldü; aynılık korunarak bırakıldı, yeni bir mantık değişikliği yapılmadı. `git diff --check` geçti. Ortak `.env` Git dışında, `.env.example` izlenebilir durumdaydı. Son container kontrolü exit 0 ile tekrar tamamlandı; Task 1 test servisleri kaldırıldı, Task 2 kimlikleri korundu.

## 2026-11-03 — Speech Studio unsafe-port düzeltmesi (tam istem)

Speech Studio container’ı healthy ve curl ile HTTP 200 dönüyor; ancak tarayıcı 5061 için ERR_UNSAFE_PORT veriyor.

Yalnızca Week-6 içinde:
- Task 1 Speech Studio host portunu 5061 → 5081 değiştir.
- Container içindeki 5000 portunu ve hesap makinesinin 5062 portunu koru.
- İlgili README, test, başlatma ve Origin kontrolü referanslarını inceleyip yeni portla tutarlı güncelle.
- PROMPTS.md’ye gerçek hata ve düzeltmeyi kaydet.
- Eski projeleri ve Task 2’yi değiştirme.
- .env okuma; commit/push/merge yapma.
- Gerekliyse image’ı yeniden build ederek yalnızca speech-studio servisini yeniden oluştur.
- http://127.0.0.1:5081/ erişimini ve WebSocket Origin uyumunu doğrula.

### Gerçek bulgular ve sonuçlar

- Branch `week6-containers`. Kullanıcı bildirimi healthy/curl 200 ile tarayıcı ERR_UNSAFE_PORT ayrımını içeriyordu. Başlangıçta Speech Studio 5061, hesap makinesi 5062 ve Task 2 5063/5064 üzerinde açıktı.
- `task-1/compose.yaml` host portu 5081'e taşındı; container içindeki 5000 ve hesap makinesinin 5062 portu değişmedi. Aktif README/test URL'leri güncellendi. Eski PROMPTS ve açıkça tarihsel README kayıtlarındaki önceki 5061 sonuçları geçmişe ait olarak korundu.
- `check_containers.py`, `probe_websocket.py` yeni portla güncellendi. Eski 5061 Origin'i yanlış port regresyonuna eklendi. Yeni `check_studio_port.py` çalışan serviste HTTP/Origin kontrolü yapar; hiçbir servisi durdurmaz ve gerçek Azure başlatmaz.
- Origin kontrolü ve frontend location.host/göreli API mekanizması zaten dinamik portla uyumluydu; uygulama kaynağı veya güvenlik algoritması değiştirilmedi. Image içeriği değişmediği için build yapılmadı.
- Gerçek .env okumadan yalnız speech-studio yeniden oluşturuldu. Önceki container'ın etkin runtime ortamı yalnız bellekte tutuldu, stdin üzerinden override olarak verildi; `$` karakterleri Compose interpolasyonundan korunarak aktarıldı. Değerler çıktı/log/dosya/komut argümanı/image katmanına yazılmadı. Etkin ortam eşitliği ve image kimliği karşılaştırması geçti. Hesap makinesi ve Task 2 container kimlikleri değişmedi. Normal Compose env_file yerine bu tek seferlik adımda --env-file /dev/null ve env_file reset kullanıldı.
- Gerçek `http://127.0.0.1:5081/` HTTP 200 döndü. Yayınlanan portta localhost ve 127.0.0.1 WebSocket upgrade, geçersiz start'ın ayar/SDK oluşturma öncesi güvenli reddi ve kapanma geçti; eski port/diğer host Origin'leri 403 aldı.
- Ayrı ağsız image'da gerçek Flask-Sock taşıması + mevcut SDK-spec mock'larıyla 5081 Origin, eşzamanlı HTTP/busy, sıralı final/tail/completed ve kopma sonrası temizlik kontrolü başarılı oldu. Hesap makinesini durduran toplu container testi bu aşamada çalıştırılmadı.
- Gerçek Windows Chrome headless ile 127.0.0.1:5081 sayfası açıldı; Speech Studio DOM'u yüklendi, ERR_UNSAFE_PORT görülmedi. Bu, gerçek kullanıcı mikrofon/Azure/ses testi değildir; hiçbir konuşma işlemi başlatılmadı.
- Son durumda Speech Studio yeni portta healthy/açık bırakıldı; hesap makinesi ve Task 2 servisleri korunarak çalışmaya devam etti. Yalnız Week-6 içinde değişiklik yapıldı; .env okunmadı, Git add/commit/push/merge yapılmadı.
