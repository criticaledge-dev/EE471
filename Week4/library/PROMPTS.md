# Week 4 Section 2 Part 2 — İstem kaydı

## Kullanıcı istemi

```text
Yalnızca Week4/library içinde çalış.
Önce mevcut custom_classes.py ve main.py dosyalarını oku.
Week3 dosyalarına ve calculator klasörüne dokunma.

Week 4 Section 2 Part 2 için mevcut sınıfları genişlet:

1. ItemNotFoundError ve ItemStateError exception sınıflarını ekle.

2. Her öğenin id alanı olsun.
   LibraryCollection.add_item(item):
   - 1'den başlayan benzersiz integer ID atasın.
   - Atanan ID'yi döndürsün.
   - Silinen ID'ler tekrar kullanılmasın.
   - Aynı nesnenin tekrar eklenip mevcut ID'sinin değişmesini engelle.

3. MediaItem.to_dict() şu alanları döndürsün:
   id, type, title, author, is_available.
   Book ve DVD bu metodu override edip super() sonucuna
   sırasıyla page_count ve duration eklesin.
   Tür değerleri "book" ve "dvd" olsun.
   Temel MediaItem desteklenmeye devam ederse türü "media" olabilir.

4. checkout():
   - Uygunsa is_available=False yapıp başarı mesajı döndürsün.
   - Zaten ödünçteyse ItemStateError oluştursun.

5. return_item():
   - Ödünçteyse is_available=True yapıp başarı mesajı döndürsün.
   - Zaten müsaitse ItemStateError oluştursun.

6. DVD.checkout(), super().checkout() kullansın.
   Bakım uyarısını print ile yazdırmasın;
   başarı mesajına ekleyerek döndürsün.

7. LibraryCollection içine ekle:
   - get_item(item_id): öğeyi döndür; yoksa ItemNotFoundError.
   - list_items(available=None, item_type=None):
     iki isteğe bağlı filtreyi birlikte destekle.
     available=None tüm durumlar, True müsait, False ödünçte.
     item_type=None tüm türler; "book"/"dvd" ilgili türler.
     Geçersiz filtrede ValueError oluştur.
   - update_item(item_id, **fields):
     yalnızca title, author ve öğenin türüne uygun
     page_count veya duration alanlarını güncelle.
     id, type, is_available, bilinmeyen veya türe uygun
     olmayan alanlarda ValueError oluştur.
     Tüm alanları değişiklikten önce doğrula;
     hatalı güncellemede nesne kısmen değişmiş kalmasın.
   - remove_item(item_id):
     yoksa ItemNotFoundError;
     ödünçteyse ItemStateError;
     uygunsa koleksiyondan kaldır.

8. Mevcut list_available() metodunu koru.
   Başlık/yazar boş olmayan metin; sayfa sayısı ve süre
   pozitif integer olsun. Boolean değerleri sayı kabul etme.
   Bu doğrulamaları model içinde yap.

9. main.py içinde en az 3 karışık türde öğeyle:
   - Ekleme ve dönen ID'leri,
   - to_dict ve __str__ kullanımını,
   - Bulma ve mevcut list_available metodunu,
   - Filtresiz ve filtreli listelemeyi,
   - Düzenlemeyi,
   - Checkout ve return işlemlerini,
   - Silmeyi ve silinen ID'nin yeniden kullanılmadığını göster.
   - ItemNotFoundError, ItemStateError ve ValueError
     örneklerini try/except ile yakalayıp açıkça yazdır.
   - DVD uyarısının dönen mesajda bulunduğunu göster.
   Gösterim if __name__ == "__main__" korumasında çalışsın.

Sınıflara ve public metotlara kısa, anlamlı docstring ekle.
Bu istemi library/PROMPTS.md dosyasına kaydet.
Gerekirse __pycache__/ ve *.pyc için yerel .gitignore ekle.

Henüz Flask, HTML/CSS/JS veya veritabanı ekleme.
Commit/push yapma.
Sonunda değişiklikleri ve main.py çalıştırma sonucunu özetle.
```

## Uygulama notları

- Model alanları hem oluşturma hem doğrudan atama sırasında doğrulanır. `update_item` herhangi bir atamadan önce tüm alanları doğrular.
- ID sayaçları koleksiyon başına 1'den başlar. Atanmış ID salt okunurdur; silinen nesnede korunur. Önceden ID atanmış nesne aynı veya başka koleksiyona tekrar eklenirse `ItemStateError` oluşur.
- `list_items` nesneleri, mevcut `list_available` ise müsait başlıkları ekleme sırasıyla döndürür. Temel `MediaItem` desteklenir; türü `media` olur. Tür filtresi istemdeki gibi yalnızca `None`, `book`, `dvd` kabul eder.
- `test_custom_classes.py`, ID yaşam döngüsü, durum geçişleri, filtreler, model doğrulaması, atomik güncelleme, silme ve sessiz import kontrollerini içerir.
- Yalnızca `Week4/library` içinde çalışıldı. Web katmanı ve veritabanı eklenmedi. Commit/push yapılmadı.

## Doğrulama sonucu

- Cygwin Python 3.9.16 ile `python3.9.exe -B -m unittest -v test_custom_classes.py` çalıştırıldı: 8 test ve alt senaryolar geçti.
- `main.py` başarıyla tamamlandı. İlk ID'ler 1, 2, 3; silinen ID 3; sonraki yeni ID 4 oldu. DVD uyarısının dönen mesajda bulunduğu ve hatalı güncellemenin nesneyi değiştirmediği `True` olarak gösterildi.
- Bulma, listeleme, düzenleme, ödünç alma/iade ve silme örnekleri çalıştı. `ItemNotFoundError`, `ItemStateError`, `ValueError` örnekleri yakalanıp açıkça yazdırıldı.

## Week 4 Section 2 Part 3 — Kullanıcı istemi

```text
Yalnızca Week4/library içinde çalış.
Önce custom_classes.py, main.py ve varsa test dosyalarını oku.

Week 4 Section 2 Part 3 için Flask REST API ekle.

Mimari:
- app.py oluştur.
- Tek bir LibraryCollection örneğini uygulama boyunca kullan.
- Başlangıçta en az 3 öğe ekle; Book ve DVD karışık olsun.
- requirements.txt içine flask ekle.
- Route'lar HTTP/JSON ile model metotları arasında çeviri yapsın.
- İş kuralları ve alan doğrulamaları custom_classes.py içinde kalsın.
- Gerekli model düzeltmelerini yapabilirsin; mevcut davranışları koru.
- Veritabanı veya frontend ekleme.

Endpoint'ler:

POST /api/items
- Book veya DVD oluştur.
- 201 ve oluşturulan öğenin to_dict() çıktısı.
- Geçersiz girdide 400.

GET /api/items
- 200 ve öğelerin sözlüklerinden oluşan JSON listesi.
- ?available=true veya ?available=false filtresini destekle.
- ?type=book veya ?type=dvd filtresini destekle.
- Filtreler birlikte kullanılabilsin.
- Parametre yoksa ilgili filtre uygulanmasın.
- Geçersiz filtre değeri için 400.

GET /api/items/<int:item_id>
- 200 ve öğe; bulunamazsa 404.

PUT /api/items/<int:item_id>
- Öğenin tüm düzenlenebilir alanlarını zorunlu tut:
  Book: title, author, page_count.
  DVD: title, author, duration.
- Kısmi güncellemeyi kabul etme.
- 200 ve güncel öğe; hatalı girdide 400, yoksa 404.

PATCH /api/items/<int:item_id>
- Düzenlenebilir alanların bir kısmını güncelle.
- 200 ve güncel öğe; hatalı girdide 400, yoksa 404.

DELETE /api/items/<int:item_id>
- Başarıda 204 ve tamamen boş yanıt gövdesi.
- Bulunamazsa 404, ödünçteyse 409.
- 204 yanıtına JSON gövdesi ekleme.

POST /api/items/<int:item_id>/checkout
POST /api/items/<int:item_id>/return
- Başarıda 200:
  {"message": "...", "item": {...}}
- Modelin döndürdüğü başarı mesajını kullan;
  DVD bakım uyarısı yanıtta korunsun.
- Bulunamazsa 404, geçersiz öğe durumunda 409.

JSON sözleşmesi:
- Oluşturma örneği:
  {"type":"book","title":"The Hobbit","author":"J.R.R. Tolkien","page_count":310}
- DVD için page_count yerine duration kullan.
- Bütün hata yanıtları {"error":"açıklama"} biçiminde olsun.
- ItemNotFoundError -> 404.
- ItemStateError -> 409.
- ValueError ve geçersiz JSON/gövde -> 400.
- POST oluşturma, PUT ve PATCH gövdeleri JSON nesnesi olmalı.
- Bozuk JSON ve yanlış Content-Type için HTML hata sayfası döndürme.
- PUT/PATCH ile id, type veya is_available değiştirilmesin.
- Bilinmeyen veya türe uygun olmayan alanları reddet.
- Boş PATCH gövdesini 400 ile reddet.
- Geçersiz güncelleme öğeyi kısmen değiştirmesin.

Doğrulama:
- Her endpoint'in başarılı ve ilgili hatalı durumlarını test et.
- PUT ile PATCH farkını özellikle test et.
- DELETE yanıtının 204 ve gövdesiz olduğunu doğrula.
- API testleri model metotlarının yerine iş kurallarını
  route'larda tekrar yazmaya yol açmasın.
- main.py gösterimi çalışmaya devam etsin.

PROMPTS.md'ye bu istemi ekle.
README.md'ye çalıştırma komutlarını, endpoint tablosunu
ve örnek JSON gövdelerini ekle.
Uygulamayı doğrudan app.py çalıştırıldığında başlat;
import edilince sunucu başlatma.

Commit/push yapma.
Sonunda değişiklikleri, test sonuçlarını ve çalıştırma
komutunu açıkla.
```

### Part 3 uygulama notları

- `app.py` içinde bir koleksiyon oluşturulup 2 Book ve 1 DVD ile başlatıldı. Route'lar model metotlarını çağırıp JSON ve HTTP durum kodlarına çeviriyor. Modül import edilince sunucu başlamıyor.
- Modelde `create_item`, `replace_item` ve `patch_item` eklendi. Oluşturma ve tam güncelleme alan kümeleri, boş kısmi güncelleme ve alan değerleri modelde doğrulanıyor. Mevcut `update_item` davranışı korunuyor; doğrulama/atama kodu ortak metoda taşındı.
- `ItemNotFoundError`, `ItemStateError`, `ValueError` sırasıyla 404, 409, 400 olarak dönüyor. Bozuk JSON, yanlış Content-Type ve nesne olmayan gövdeler JSON hata yanıtı alıyor. Flask HTTP hataları da JSON'a çevriliyor; HTTP başlıkları korunuyor.
- `requirements.txt` içine `flask` eklendi. `README.md` oluşturuldu; endpoint tablosu, tam/kısmi güncelleme örnekleri ve PowerShell komutları belgelendi. Yerel `.gitignore` içine `.venv/` eklendi.
- API testleri izole koleksiyonlarla çalışıyor; route'ların model metotlarına yönlendirdiği ayrıca kontrol ediliyor. Yeni oluşturma ve PUT/PATCH kuralları Flask olmadan model testlerinde de denetleniyor.
- Frontend/veritabanı eklenmedi. `main.py` değiştirilmedi. Yalnızca `Week4/library` içinde çalışıldı; commit/push yapılmadı.

### Part 3 doğrulama sonucu

- Cygwin Python 3.9.16 ve geçici dizindeki Flask 3.1.3 ile unittest discovery çalıştırıldı: 14 API + 10 model testi, toplam 24 test geçti.
- Her endpoint'in başarılı ve ilgili hatalı durumları; birlikte filtreleme, PUT/PATCH farkı, yasak alanlar, boolean girdiler, atomik güncelleme, JSON/gövde hataları, 404/409 dönüşümleri ve gövdesiz 204 doğrulandı.
- Route'ların model metotlarını ve modelden dönen mesajları kullandığı, DVD uyarısının korunduğu ve import sırasında sunucu başlamadığı test edildi.
- Değiştirilmemiş `main.py` yeniden çalıştırıldı; gösterim başarıyla tamamlandı. ID 3 silindikten sonra yeni ID 4 oldu; hatalı güncellemenin nesneyi değiştirmediği ve DVD uyarısının dönüş mesajında bulunduğu tekrar doğrulandı.
- `git diff --check` hata vermedi. Git durumunda yalnızca `Week4/library` değişiklikleri var.

## Section 2 Part 4 — Kullanıcı istemi

```text
Yalnızca Week4/library içinde çalış.
Önce mevcut app.py, custom_classes.py, README.md ve testleri oku.

Section 2 Part 4: Mevcut Flask REST API'ye web arayüzü ekle.

Tasarım referansı: Week4/design/library.png
Dosyayı incele; görünümü buna göre oluştur.

Dosyalar:
- templates/index.html
- static/style.css
- static/script.js
- app.py içine GET / ekleyerek index.html'i render et.

Mevcut API endpoint'lerini, durum kodlarını ve model kurallarını koru.
Sayfa http://127.0.0.1:5000 üzerinden açılsın.

Arayüz:
1. Kitap/DVD listesi:
   title, author, type, page_count veya duration ve müsaitlik etiketi.
2. Her öğede Checkout/Return, düzenleme ve silme butonları.
3. Ekleme/düzenleme formu:
   title, author, type ve türe göre page_count veya duration.
4. Available only filtresi ve All / Book / DVD tür filtresi.
5. Boş liste mesajı, yükleniyor durumu, hata ve başarı mesajları.

API bağlantısı:
- Listeyi GET /api/items ile yükle.
- Filtreleri API query parametrelerine çevir.
- Oluşturmayı POST, düzenlemeyi PATCH ile yap.
- Düzenlemede type seçicisini devre dışı bırak;
  id, type ve is_available alanlarını güncelleme gövdesine koyma.
- Checkout/Return için mevcut POST endpoint'lerini kullan.
- Silmede DELETE endpoint'ini kullan.
- Başarılı değişiklikten sonra mevcut filtrelerle listeyi yeniden yükle.
- DELETE 204 yanıtında response.json() çağırma.

Hata yönetimi:
- API'nin error alanındaki mesajı sayfadaki hata alanında göster.
- Ödünçteki öğede silme butonu tıklanabilir kalsın:
  kullanıcı silmeyi deneyince sunucunun 409 mesajı gösterilsin.
- İş kurallarını JavaScript'te yeniden uygulama.
- Ağ hatalarını da anlaşılır şekilde göster.
- İstek sürerken ilgili butonları devre dışı bırak;
  başarı veya hata sonrasında yeniden etkinleştir.
- Hata olursa formdaki kullanıcı girdilerini koru.

Görünüm:
- Ortalanmış, maksimum genişliği sınırlı bir sayfa oluştur.
- Masaüstünde solda liste, sağda form olsun.
- Dar ekranlarda tek sütuna geç.
- Uzun başlıklar ve hata mesajları yatay taşma oluşturmasın.
- Kullanıcı verilerini DOM'a textContent ile yerleştir;
  kullanıcı girdilerini innerHTML içine ekleme.
- Form alanlarına label, ikon butonlarına erişilebilir ad ekle.

Belgeler:
- Bu istemi PROMPTS.md'ye kaydet.
- Gerçekten tespit edip düzelttiğin hataları ayrıca kaydet.
- Henüz iki hata bulunmadıysa örnek hata uydurma;
  manuel inceleme sırasında tamamlamak üzere belirt.
- README'ye arayüz kullanımını ekle.

Mevcut testleri çalıştır. Ana sayfa ve statik dosyaların
sunulmasını da doğrula.
Tarayıcı kontrolü yapabiliyorsan yap; yapamıyorsan açıkça belirt.

Commit/push yapma.
Sonunda değişiklikleri, test sonuçlarını ve manuel kontrol
gerektiren noktaları özetle.
```

### Part 4 uygulama ve doğrulama

- API, model, README ve testler okundu; `Week4/design/library.png` görseli incelendi. Açık gri zemin, lacivert metinler, beyaz kart/form panelleri, mavi butonlar ve durum etiketleri referans alındı.
- `templates/index.html`, `static/style.css`, `static/script.js` eklendi. `app.py` içine yalnızca HTML için `render_template` import'u ve GET `/` eklendi. Model, başlangıç öğeleri ve mevcut API metotları/durum kodları değiştirilmedi.
- Liste ve filtreler API üzerinden çalışıyor. Ekleme POST, düzenleme PATCH, silme DELETE; checkout/iade mevcut POST endpoint'lerini kullanıyor. Düzenleme gövdesinde salt okunur alanlar bulunmuyor; tür seçicisi kilitleniyor. İş kuralları sunucuda kaldı.
- Kullanıcı metinleri `textContent` ile yerleştiriliyor; kartlar statik template'ten kopyalanıyor. Sunucu hata mesajları görünür; ödünçteki öğenin silme butonu istek dışında etkin. Ağ hataları, bekleme/boş liste, başarı mesajları ve hata sonrası form girdilerinin korunması uygulandı. Başarılı değişiklik sonrası aynı filtrelerle liste yenileniyor.
- Mevcut 24 Python testi ve eklenen ana sayfa/statik dosya kontrolleriyle toplam 26 Python testi geçti. JavaScript sözdizimi kontrolü ve taklit DOM/API ile 7 etkileşim testi geçti. 204 gövdesini JSON okumama, 409 gösterimi, PATCH alanları, filtreleri koruma, metin güvenliği, bekleme sırasında kilitleme ve hata sonrası devam etme kontrol edildi.
- Kullanılabilir tarayıcı kontrol aracı bulunmadı; gerçek tarayıcıda görsel/etkileşim kontrolü yapılmadı. Masaüstü/dar ekran, uzun metinler, klavye odağı ve gerçek ağ kesintisi manuel inceleme gerektirir.
- Yalnızca `Week4/library` içinde dosyalar değiştirildi. Commit/push yapılmadı.

### Part 4 — Gerçek hata ve düzeltme kaydı

Part 4'ün ilk uygulama aşamasındaki inceleme ve otomatik testlerde iki gerçek hata tespit edilmemişti. Yeni özelliklerin gereksinime uygun uygulanması hata düzeltmesi olarak sayılmadı. Sonraki gözden geçirmede aşağıdaki iki hata ek testlerle yeniden üretildi ve düzeltildi.

| Bulunan gerçek hata | Tekrar üretme adımları | Yapılan düzeltme | Doğrulama |
| --- | --- | --- | --- |
| Başarılı oluşturma sonrasında liste isteği başarısız olursa yeniden gönderim ikinci POST yapıyordu. | Formu doldur; POST 201 döndürsün, takip eden GET ağ hatası versin; formu yeniden gönder. | POST yanıtındaki ID, liste isteğinden önce form durumuna kaydediliyor ve form düzenleme moduna alınıyor. Girdiler korunuyor; sonraki gönderim yeni POST yerine mevcut ID'ye PATCH yapıyor. Liste başarıyla yüklenirse form normal şekilde sıfırlanıyor. | `successful create followed by failed reload cannot create a duplicate on retry` testi düzeltme öncesinde `POST !== PATCH` ile başarısız oldu; düzeltme sonrasında geçti. Yalnızca bir POST gönderildiği, girdilerin korunduğu, türün kilitli ve Save/Cancel butonlarının etkin olduğu kontrol edildi. |
| Filtre isteği başarısız olduğunda eski kartlar ve sayaç yeni seçili filtre altında kalıyordu. | All görünümünde Book/DVD kartlarını yükle; DVD filtresine geçerken GET ağ hatası versin. | Yeni liste isteğinin başlangıcında önceki kartlar ve sayaç temizleniyor. Hata halinde yükleniyor durumu kapanıyor, hata gösteriliyor; yanlış filtreye ait kartlar gösterilmiyor. | `failed filter request cannot leave old items under the newly selected filter` testi düzeltme öncesinde eski 2 kartın kalması nedeniyle başarısız oldu; düzeltme sonrasında geçti. Refresh ile aynı DVD filtresinin başarıyla yüklenmesi ve butonların etkinleşmesi doğrulandı. |

### Part 4 gözden geçirme istemi

```text
Yalnızca Week4/library içindeki Part 4 kodunu gözden geçir.
Mevcut API sözleşmesiyle karşılaştır; hata yönetimi,
204 yanıtı, filtreler, düzenleme ve istek sonrası buton
durumlarını incele.

Gerçek hata bulursan düzelt, uygun kontrolü çalıştır ve
PROMPTS.md'ye önceki davranışı, düzeltmeyi ve doğrulamayı yaz.
Hata yoksa açıkça belirt; iki hata şartını doldurmak için
hata veya geçmiş düzeltme uydurma.

Section 2 kapsamında belgelenmiş gerçek düzeltmelerin
sayısını bildir. Commit/push yapma.
```

### Gözden geçirme sonucu

- Section 2 kapsamında bu `library/PROMPTS.md` içinde yeniden üretimi ve doğrulaması belgelenmiş gerçek hata düzeltmesi sayısı **2**. İkisi de bu gözden geçirmede bulundu; Part 2/3 gereksinim uygulamaları ve yeni özellikler bu sayıya eklenmedi.
- API sözleşmesi, endpoint'ler, durum kodları ve model kuralları değiştirilmedi. Hatasız çalışan 204 gövdesini JSON okumama, filtre query parametreleri, PATCH gövdesinden salt okunur alanları çıkarma ve sunucu hata mesajını gösterme davranışları korundu.
- JavaScript sözdizimi kontrolü, 9 JavaScript etkileşim testi ve 26 Python testi geçti. Yeni testler önce mevcut kod üzerinde başarısız çalıştırılarak sorunlar doğrulandı; düzeltmelerden sonra geçti. 409 ve kaydetme hatası sonrasında butonların yeniden etkinleşmesi, düzenlemede türün kilitli kalması da kontrol edildi.
- Gerçek tarayıcı kontrolü yapılmadı; JavaScript etkileşim testleri taklit DOM/API kullanır. README yeni kurtarma davranışı ve güncel test sayısı ile eşitlendi. Yalnızca `Week4/library` değiştirildi. Commit/push yapılmadı.
