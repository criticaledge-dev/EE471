# Mini Project 2 — İstem ve çalışma kaydı

Bu belge Mini Project 2 için kronolojik olarak düzenlenmiş bir çalışma kaydıdır; mevcut **tam istemleri**, açıkça etiketlenmiş **istem özetlerini**, geliştirme sonuçlarını ve kullanıcı tarafından bildirilen manuel doğrulamaları içerir. Eksiksiz ham Codex transkripti değildir. Kaynak Week4 uygulamasının eski PROMPTS içeriği kopyalanmamıştır.

**Tam istem** başlıklarında mevcut tam metin korunur. Kısaltılarak aktarılmış kayıtlar **İstem özeti** olarak etiketlenir; eksik tam metinler tahminle tamamlanmaz. Test sayıları, hata nedenleri ve yeniden üretilemeyen bulguların belirsizliği ilgili aşamanın kaydı olarak korunur.

Eski aşamalardaki “gerçek ses doğrulaması bekliyor” ve benzeri ifadeler **o aşamadaki durumu** anlatır; silinmemiştir. Sonradan gelen kullanıcı doğrulamaları bu tarihsel kayıtları tüm senaryolar için başarıya dönüştürmez. Otomatik/mock kontroller ile kullanıcının gerçek manuel kontrolleri ayrı kaydedilir; İngilizce TTS bildirimi kendisine ait ayrı bölümde korunur. Daha sonraki düzeltmeler bu kronolojinin devamına eklenir.

## Başlangıç kopyası ve sözleşme incelemesi

Bağlam dosyası: `Mini-Project-2.pdf` (kullanıcının belirttiği yerel PDF). PDF'deki sonraki sesli geliştirme ve teslim beklentileri, aşağıdaki ilk aşama talimatını genişletmez.

### Tam istem

```text
EE471 Mini Project 2’ye başlıyoruz: Voice-activated Library App.

Bu aşamada yalnızca başlangıç uygulamasını hazırla ve mevcut sözleşmeyi incele.

Kapsam:
- Aktif branch voice-library olmalı; farklıysa değişiklik yapmadan bildir.
- main içindeki Week4/library uygulamasını başlangıç olarak kullan.
- Kaynakları Mini-Project-2 klasörüne kopyala.
- Week4, Week5 ve diğer proje klasörlerini değiştirme.
- .venv, gerçek .env, __pycache__, .test-deps, geçici ve üretilmiş dosyaları kopyalama.
- Library modelini, API sözleşmesini ve mevcut arayüz davranışını koru.
- Henüz ses özelliği ekleme.

Gerekli mevcut işlemler:
POST /api/items
GET /api/items — available ve type filtreleri
GET /api/items/<id>
PUT /api/items/<id>
PATCH /api/items/<id>
DELETE /api/items/<id>
POST /api/items/<id>/checkout
POST /api/items/<id>/return

İnceleme:
- Book/DVD oluşturma alanlarını ve PUT/PATCH kurallarını gerçek koddan çıkar.
- Başarı yanıtlarını, hata durumlarını ve DELETE 204 davranışını bildir.
- Sonraki aşamada sesli komutların mevcut API’yi kullanacağı uygun bağlantı noktalarını belirle; ayrı koleksiyon veya ikinci bir iş mantığı oluşturma.

Belgeler:
- Mini-Project-2 için .gitignore, README.md ve PROMPTS.md hazırla.
- Eski PROMPTS içeriğini yeni projenin geliştirme geçmişi gibi sunma.
- Bu istemi yeni PROMPTS.md’ye kaydet.
- .env ignore kuralı olsun. Gerçek .env dosyalarını okuma veya kopyalama.

Kopyanın mevcut testlerini çalıştır. Yapılmamış tarayıcı/Azure testlerini yapılmış gibi yazma.
Commit/push/merge yapma.

Sonuçta oluşturulan dosyaları, model/API alanlarını, test sonuçlarını ve PowerShell çalıştırma komutlarını bildir.
```

### Çalışma kaydı — 2026-11-02

- Aktif branch `voice-library` olarak kontrol edildi; AGENTS.md bulunmadı. Başlangıçta çalışma ağacı temizdi.
- `main` kaynak commit'i: `fc6b814d0e37f6bd79a83e4f54ab9966c4acac80`. Branch değiştirmeden Git blob'larından yalnızca on kaynak/bağımlılık/test dosyası açık listeyle kopyalandı. Eski README/PROMPTS ve ortam/üretilmiş dosyalar alınmadı.
- Model, API, arayüz ve test kodları değiştirilmedi. Yeni `.gitignore`, README ve bu istem kaydı oluşturuldu. Henüz ses kodu veya Azure bağımlılığı eklenmedi.
- Gerçek Book/DVD şemaları, tam PUT/kısmi PATCH kuralları, filtreler, checkout/iade durumları ve boş DELETE 204 sözleşmesi incelendi ve README'ye yazıldı. DVD için de yazar/yönetmen alanının `author`, süre alanının `duration` olduğu doğrulandı.
- Tek koleksiyon ve mevcut HTTP/model akışını koruyacak ses bağlantıları belgelendi: `apiRequest`, `runAction`, `refreshItems`, form/kart istekleri; mevcut GET-by-ID ve PUT endpoint'leri. Bu bağlantılar gelecekteki çalışma önerisidir, bu aşamada ses adaptörü uygulanmadı.

### Bu kopyada yapılan kontroller

- Yeni `Mini-Project-2` klasöründe **26 Python testi (16 API + 10 model) geçti**. Ana sayfa ve statik dosyalar, model/API sözleşmesi, filtreler, atomik güncellemeler, ID ömrü, checkout/iade mesajları, hata yanıtları, DELETE 204 ve import davranışı kontrol edildi.
- **9 Node.js testi geçti.** Bunlar gerçek tarayıcı yerine taklit DOM/API kullanır; mevcut arayüzün istek/durum akışı, hata sonrası kullanım ve 204 davranışı sınanır.
- `node --check static/script.js` sözdizimi kontrolü geçti. Python testleri için proje dışındaki geçici Flask bağımlılıkları kullanıldı; sanal ortam veya `.test-deps` kopyalanmadı.
- Bunlar bu klasörde çalıştırılan sonuçlardır; kaynak projenin eski test raporu aktarılmadı. Gerçek tarayıcı, mikrofon veya Azure doğrulaması yapılmadı.
- Gerçek .env dosyası oluşturulmadı, okunmadı veya kopyalanmadı. Week4, Week5 ve diğer proje dosyaları değiştirilmedi. Commit/push/merge yapılmadı.

## Port 5002 — 2026-11-02

### Tam istem

```text
Yalnızca Mini-Project-2 içinde Flask geliştirme sunucusunun portunu 5002 yap.

Önce mevcut başlatma kodunu incele. app.py doğrudan çalıştırıldığında http://127.0.0.1:5002 adresinde açılsın.

Frontend API çağrıları göreli URL kullanıyorsa koru. Sabit localhost:5000 referansları varsa uygulama ve belgelerde gerekli yerleri tutarlı biçimde güncelle. API yollarını ve uygulama davranışını değiştirme.

README.md ve PROMPTS.md dosyalarını güncelle. Diğer projeleri değiştirme. Commit/push yapma.
```

### Geliştirme sonuçları

- Başlatma kodu varsayılan `app.run()` kullanıyordu; `__main__` koruması içinde `app.run(host="127.0.0.1", port=5002)` olarak değiştirildi.
- README'deki tarayıcı adresi ve PowerShell API örnekleri 5002 ile güncellendi. Frontend zaten göreli `/api/items` yollarını kullanıyor; JavaScript ve API sözleşmesi değiştirilmedi.
- Başlatma çağrısı gerçek sunucu açılmadan mock ile kontrol edildi; import sırasında sunucunun başlamadığı da doğrulandı. Bu kontrol gerçek tarayıcı testi değildir.
- Yalnızca `app.py`, README ve bu kayıt güncellendi. Commit/push yapılmadı.

## Aşama 2

### Tam istem

```text
Mini Project 2 — Aşama 2: İngilizce komut ayrıştırma ve mevcut Library API’sine bağlama.

Önce Mini-Project-2 içindeki güncel kodları ve testleri oku. Aşağıdaki adları ve davranışları mevcut kodda doğrula; varsayımla uygulama yapma.

Kapsam:
- Aktif branch voice-library olmalı.
- Yalnızca Mini-Project-2 içinde değişiklik yap.
- Port 5002 korunmalı.
- Henüz mikrofon, Azure STT veya TTS ekleme.
- Mevcut model, tek collection, API yolları, HTTP durumları ve elle kullanılan arayüz korunmalı.
- Gerçek .env dosyalarını okuma.
- Commit/push/merge yapma.

Mevcut sözleşme:
- Book POST: type, title, author, page_count.
- DVD POST: type, title, author, duration.
- PUT: ilgili türün tüm düzenlenebilir alanları; type gönderilmez.
- PATCH: en az bir düzenlenebilir alan.
- id, type ve is_available güncellenemez.
- DELETE başarılıysa 204 ve tamamen boş gövde.
- Checkout/return yanıtı message ve item içerir.
- Listeleme available=true/false ve type=book/dvd destekler.

1. Komut ayrıştırma
Ayrı, DOM ve ağ bağımlılığı olmayan bir JavaScript modülü oluştur.
Metni doğrulanmış bir komut nesnesine dönüştürsün.
Ayrıştırma veri değiştirmesin ve ağ isteği yapmasın.
eval veya LLM servisi kullanma.

Desteklenecek açık İngilizce komutlar:

CREATE:
Create item, type book, title The Hobbit, author Tolkien, pages 310
Create item, type DVD, title Inception, author Christopher Nolan, duration 148

LIST:
List items
List books
List DVDs
List available items
List available books
List available DVDs
List checked out items
List checked out books
List checked out DVDs

GET:
Get item 3

PUT:
Replace item 3, title The Hobbit Revised, author Tolkien, pages 320
Replace item 2, title Inception Revised, author Christopher Nolan, duration 150

PATCH:
Update item 3, pages 330
Update item 3, title The Hobbit Updated
Update item 2, title Inception Updated, duration 151

DELETE:
Delete item 3

CHECKOUT:
Check out item 3
Checkout item 3

RETURN:
Return item 3

Kurallar:
- Komutlar büyük/küçük harften etkilenmesin.
- Başlık/yazar metninin özgün içeriğini mümkün olduğunca koru.
- DVD/DVDs gibi yazımları destekle.
- Alanların sırası title/author/detail için değişebilir.
- Azure noktalama ekleyebilir veya virgülleri kaldırabilir. Açık alan etiketleriyle virgülsüz örnekleri de destekle.
- Ondalık olmayan sayısal alanlarda rakam ve İngilizce sayı kelimelerini destekle; örneğin item three, pages three hundred ten.
- Sayıları yalnızca ID/sayfa/süre alanlarında normalleştir. “1984” gibi başlıkları sayı işleminden geçirme.
- ID ve sayfa/süre pozitif güvenli integer olmalı; negatif, ondalık, eksik ve çözümlenemeyen sayıları reddet.
- Tek komutta birden fazla işlem çalıştırma.
- Yinelenen alanları, bilinmeyen alanları, eksik CREATE/PUT alanlarını ve boş PATCH’i reddet.
- PUT/PATCH tür değiştirmeye çalışmamalı.
- Başlık/yazar içinde alan etiketiyle çakışan belirsiz metni tahmin ederek bölme. Desteklenen grameri ve belirsizlik sınırlarını belgele.
- Bilinmeyen komutları sessizce değiştirme veya atlama.
- Tam komut doğrulanmadan hiçbir değişiklik isteği gönderilmesin.

2. Mevcut API’ye bağlama
- Ayrı koleksiyon veya ikinci Library iş mantığı oluşturma.
- Mevcut apiRequest, runAction ve refreshItems yapılarını uygun şekilde kullan.
- İstek yöntemi/path/query/body ayrıştırılmış komuttan oluşturulsun.
- PUT/PATCH için gerekli olduğunda mevcut öğeyi GET ile alarak türünü öğren; önbellekteki eski kartı tek doğruluk kaynağı sayma.
- Model doğrulamaları yine sunucuda kalsın.
- Mutasyon endpoint’ini yalnızca bir kez çağır.
- Mutasyon başarılı, sonraki liste yenilemesi başarısızsa işlemi başarısız gibi tekrar gönderme. İşlem sonucu ve yenileme uyarısını ayrı göster.
- Silmede 204 gövdesini okumaya çalışma; ID ile açık başarı mesajı üret.
- DVD checkout yanıtındaki bakım uyarısını kaybetme.
- 400/404/409 hataları kullanıcıya açıkça gösterilsin.

3. Arayüz
Küçük bir “Command” paneli ekle:
- İngilizce komut metni alanı.
- “Run command” düğmesi.
- Anlaşılan işlem özeti.
- Sonuç/hata alanı.

Bu metin alanı, sonraki aşamada mikrofon transkriptinin de kullanacağı ortak komut yürütme akışını çalıştırsın.

- GET tek öğe sonucunu ID, tür, başlık, yazar, sayfa/süre ve durumuyla göster.
- LIST sonuçları mevcut liste/kart düzeninde görünsün.
- available=true/false filtresini arayüzde doğru temsil et. Mevcut kutuyu gerekiyorsa All / Available / Checked out seçimine dönüştür; eski filtre davranışını ve erişilebilirliği koru.
- Liste komutları aktif tür ve durum kontrollerini eşitlesin.
- Mutasyon sonrası mevcut görünümün filtrelerini koru; öğe filtre nedeniyle görünmüyorsa yanlışlıkla işlem başarısız denmesin.
- Sonuçları textContent veya güvenli DOM yöntemleriyle göster.
- Başarı mesajı yalnızca gerçek API başarısından sonra gösterilsin.
- busy durumunda çift gönderimi engelle.
- Mevcut formun başarılı POST sonrası ID’yi koruyan davranışını bozma.

4. Sonraki TTS aşamasına hazırlık
Başarılı veya hatalı her komut için gerçek sonuçtan türetilen kısa İngilizce responseText üret.
Henüz seslendirme yapma.

Örnekler:
Successfully created book 'The Hobbit' with ID 4.
Item 4, 'The Hobbit', has been checked out.
Successfully deleted item 4.
Sorry, item 999 was not found.

- Mesajlar gerçek API sonucuna dayanmalı.
- Boş liste için açık mesaj üret.
- Liste özeti adetleri ve dönen öğelerin ID/başlık bilgilerini içersin; uzun listelerde ekran ve ilerideki ses için belgelenmiş bir sınır uygula.
- Ağ hatasında işlemin sunucuya uygulanıp uygulanmadığı kesin değilse “uygulanmadı” deme ve otomatik tekrar gönderme.
- TTS’ye uygun yanıt üretimi API sözleşmesini değiştirmesin.

5. Doğrulama ve belgeler
- Mevcut testleri çalıştır.
- Parser testleri: tüm komutlar, alan sırası, virgülsüz giriş, sayı kelimeleri, sayısal başlık, geçersiz/eksik/yinelenen alanlar ve belirsizlikler.
- Arayüz testleri: gerçek HTTP yöntem/path/body, 204, 404/409, filtre eşitleme, çift gönderim, başarılı mutasyon sonrası yenileme hatasında ikinci mutasyon yapılmaması.
- Model/API tarafında CREATE, GET list/detail, PUT, PATCH, checkout, return ve DELETE sözleşmelerinin korunduğunu doğrula.
- Gerçek tarayıcıda yapılmamış kontrolleri açıkça belirt.
- README’ye desteklenen komutları ve sınırlarını ekle.
- Bu istemi ve gerçek sonuçları PROMPTS.md’ye kaydet.

Sonuçta değişen dosyaları, komut nesnesinin şemasını, ortak yürütme fonksiyonunu, test sonuçlarını ve manuel deneme adımlarını bildir.
```

### Aşama 2 — Uygulama ve doğrulama kaydı (2026-11-02)

- Branch `voice-library` ve doğrudan çalıştırma portu 5002 kontrol edildi. Yalnızca Mini-Project-2 içinde çalışıldı. Model ve tek collection korundu; API endpoint gövdeleri değiştirilmedi. `app.py` içine yalnızca ES modüllerini doğru JavaScript MIME türünde sunmak için mimetypes tanımı eklendi.
- `command-parser.mjs`: DOM/ağ bağımsız `parseLibraryCommand`, pozitif güvenli İngilizce sayı çözümleme ve işlem özeti eklendi. Komut nesnesi `{action,id,fields,filters}`; pages API'nin page_count alanına çevrilir. Rakamlı başlıklar sayı dönüşümünden geçmez. Gerekli/tekrarlı/yasak alanlar ve desteklenmeyen diziler mutasyon öncesinde reddedilir.
- Gramer açık etiketlere dayanır; tamamen virgüllü veya tamamen virgülsüz alanlar desteklenir. Etiketle çakışan literal metin ve virgül içeren başlık/yazar için çift tırnak gerekir. Virgüllü girişte metin içindeki etiket tahminle yeni alana bölünmez; alıntı/tutarlı ayırıcı istenerek reddedilir. Virgülsüz gramerde etiketler açık alan sınırlarıdır. Bilinmeyen virgülle ayrılmış alan reddedilir; serbest metindeki sıradan kelimelerin alan olup olmadığı tahmin edilmez. Ayrıntılı sınırlar README'dedir.
- `command-runner.mjs`: aynı API'ye yöntem/path/query/body ile bağlanır. PUT/PATCH öncesi taze GET ile tür kontrolü yapar, ardından mutasyonu bir kez çağırır. Kopya model, koleksiyon, checkout veya güncelleme mantığı eklenmedi. responseText gerçek sonuç/hata üzerinden üretilir; DVD uyarısı ve boş DELETE 204 korunur.
- `script.js`: ortak `runCommandText(text)` dışa aktarılır; mevcut apiRequest/runAction/refreshItems kullanılır. Tam ayrıştırmadan önce ağ isteği yoktur. Yeni Command formu aynı girişi çağırır; ileride transkript de bunu kullanabilir. Henüz ses kodu yoktur.
- Müsaitlik kutusu All/Available/Checked out seçimine dönüştürüldü. LIST komutları tür/durum kontrollerini eşitler; mutasyonlar görünüm filtrelerini korur. GET ayrıntıları ve tüm kullanıcı metinleri güvenli textContent ile gösterilir. Busy kilidi iki formu da kapsar.
- Mutasyon başarısı ve yenileme uyarısı ayrıldı. Yenileme hatasından sonra aynı metni tekrar çalıştırmak yalnızca GET yenilemesi yapar. Ağda belirsiz mutasyon, uygulanmamış gibi gösterilmez; otomatik tekrar yoktur. Aynı belirsiz metnin tekrar gönderimi de engellenir; kullanıcı koleksiyonu kontrol edip bilinçli karar vermelidir. Mevcut manuel POST sonrası ID saklama davranışı korundu.
- Komut LIST çıktısı 100 kartla, kısa responseText ilk 5 ID/başlık ve başlık başına 60 karakterle sınırlıdır; gerçek toplam ve kesilme belirtilir. GET ayrıntıları tam alanları gösterir. Bu sınırlar API yanıtını veya modeli değiştirmez.

### Çalıştırılan kontroller

- **26 Python ve 29 Node.js testi geçti.** Önceki 9 UI testi korundu/erişilebilir durum seçimine uyarlandı; 9 parser/orkestrasyon ve 11 yeni panel testi eklendi. Tüm komut aileleri, dokuz LIST bileşimi, alan sırası, virgülsüz metin, sayı kelimeleri, sayısal başlık, alıntı/belirsizlik, güvenli integer, geçersiz alanlar/diziler, gerçek yöntem/path/body, taze tür GET'i, 204, 400/404/409, filtreler, uzun liste sınırı, busy, belirsiz ağ yanıtı ve yenileme sonrası ikinci mutasyon yapılmaması kontrol edildi. İlk aşamanın eski sonuçları bu aşamanın sonucu gibi aktarılmadı.
- JavaScript sözdizimi kontrolleri geçti. Kaynak main ile karşılaştırmada `custom_classes.py` baytları ve bütün API fonksiyon gövdelerinin AST'leri aynı bulundu. `app.run` mock kontrolü `127.0.0.1:5002` başlatmasını doğruladı.
- `check_commands_browser.py` headless Chrome ile **14 metin paneli işlemini**, gerçek HTML/ES modülleri, submit olayları, yerel Flask HTTP ve izole gerçek Library modeli üzerinde başarıyla çalıştırdı: oluşturma, dokuz gruptan örnek liste filtreleri, detay GET, PUT, PATCH, checkout/iade, DELETE 204, 404/409 ve DVD bakım uyarısı. JavaScript error/unhandledrejection sayısı sıfırdı.
- Bu gerçek yerel headless işlev kontrolüdür; kullanıcının etkileşimli tarayıcısında görsel, dar ekran veya erişilebilirlik denemesi yapılmadı. Mikrofon/Azure/STT/TTS eklenmedi veya denenmedi. Gerçek .env okunmadı. Commit/push/merge yapılmadı.

## Alan sınırları — Kullanıcı düzeltme isteği

### İstem özeti

Yalnızca Mini-Project-2 içinde komut ayrıştırıcısının alan sınırları incelenip düzeltilmeli. Kullanıcı oluşturma denemesinde “Ambiguous field word in title/author. Quote the value, or separate every field with commas.” hatası aldı; özgün başarısız metin birebir kaydedilmedi. Daha sonra `Create item, type book, title "Test Book", author "Test Author", pages 220` komutunu gerçek tarayıcıda başarıyla çalıştırdı. Önerilmiş tırnaksız biçim yeniden üretilmeden kesin hata nedeni olarak kaydedilmemeli.

İstenen davranış: virgüllü bölümün yalnızca başındaki sözcük alan etiketi olsun; değer içindeki author/title/pages kelimeleri belirsizlik sayılmasın. Tırnaklı ve tırnaksız Test Book/Test Author aynı nesneyi üretsin. Tırnak/alan sırası ve açık virgülsüz CREATE/PUT/PATCH örnekleri korunsun. Gerçekten belirsiz virgülsüz metin tahminle mutasyona dönüşmesin; bilinmeyen/tekrarlı/eksik alanlar reddedilsin. Tam doğrulamadan önce ağ isteği gönderilmesin. İlgili beş regresyon grubu test edilsin; README/PROMPTS güncellensin. API/model/diğer komut davranışları korunmalı; commit/push/merge yapılmamalı.

### Gerçek bulgular ve düzeltme

- Branch `voice-library` doğrulandı. Değişiklikten önce önerilmiş tırnaksız `Create item, type book, title Test Book, author Test Author, pages 220` gerçek parser modülüyle yeniden üretildi ve bildirilen belirsizlik hatasını verdi. Tırnaklı karşılığı başarılıydı. Bu yeniden üretim, kaydedilmemiş özgün kullanıcı komutuyla aynı komut olduğu iddiası değildir.
- Kodda virgüllü değer zaten virgüle kadar tek bölüm olarak okunuyordu. Ancak ek bir kontrol `Test Author` içindeki Author sözcüğünü etiket listesinde bulduğu için gereksiz yere reddediyordu. Virgülle sınırlandırılmış title/author değerinde etiket kelimesi reddi kaldırıldı; etiket yalnızca bölüm başında tanınır.
- Tırnak/alan sırası korunur. Virgülsüz açık CREATE, PUT ve text/detail PATCH aynı şekilde çalışır. İki tırnaksız isteğe bağlı title/author alanıyla bir uzun text alanı arasında seçim gerektiren virgülsüz PATCH açık hatayla reddedilir. Tek komut için hiç ön GET veya mutasyon gönderilmez.
- Yinelenen veya bilinmeyen bölüm etiketleri, eksik CREATE/PUT alanları, boş PATCH, geçersiz sayılar ve tırnak hataları reddedilmeye devam eder. API/model ve diğer işlem yolları değiştirilmedi.
- Kullanıcının tırnaklı komutu gerçek tarayıcıda çalıştırdığı bildirimi manuel kullanıcı doğrulaması olarak kaydedildi; asistanın yaptığı test olarak sunulmadı.

### Kontroller

- **34 Node.js testi geçti:** tırnaklı/tırnaksız nesne eşitliği ve tam API gövdesi, virgüllü metin içindeki title/author/pages/duration kelimeleri, alan sırası/tırnaklar, mevcut virgülsüz CREATE/PUT/PATCH, gerçekten belirsiz PATCH ve geçersiz alanlarda sıfır yeni ağ isteği. Önceki komut, API orkestrasyonu ve manuel form regresyonları da çalıştırıldı.
- **26 Python testi geçti:** mevcut model/API sözleşmesi ve statik dosya kontrolleri korundu.
- İzole gerçek Flask/model ve headless Chrome ile **18 panel işlemi geçti**, JavaScript hatası yoktu. Eklenen dört adım, tırnaksız ve tırnaklı Test Book/Test Author oluşturma ile her iki yeni öğenin gerçek GET yanıtını kontrol etti. Bu test ayrı geçici koleksiyon kullanır; kullanıcının etkileşimli tarayıcısında görsel/dar ekran doğrulaması veya ses/Azure testi yapılmadı.
- Kullanıcının daha önce bildirdiği tırnaklı gerçek tarayıcı başarısı ayrı bir manuel doğrulamadır. Kaydedilmemiş ilk başarısız komutun içeriği veya kesin nedeni hakkında ek iddia üretilmedi.
- Değişiklikler yalnızca Mini-Project-2 parser'ı, ilgili testler ve belgeler içindedir. Gerçek .env okunmadı; commit/push/merge yapılmadı.

## Aşama 3

### Tam istem

```text
Mini Project 2 — Aşama 3: mevcut komut akışına Azure ile mikrofon girişi ekle.

Önce güncel Mini-Project-2 kodunu incele:
- static/command-parser.mjs
- static/command-runner.mjs
- static/script.js
- templates/index.html
- app.py ve ilgili testler

Ardından Week-5-Task-2 içindeki çalışan mikrofon/PCM/STT kodlarını incele. Gerekli parçaları uyarlayarak kullan; hesap makinesine özel komut veya TTS kuyruk kodlarını taşıma.

Kapsam:
- Branch voice-library, port 5002.
- Yalnızca Mini-Project-2 içinde değişiklik yap.
- Diğer projeleri değiştirme.
- Task 2’ye çalışma zamanı importu veya dosya yolu bağımlılığı oluşturma.
- Mevcut model, API sözleşmesi, komut paneli ve elle kullanım korunsun.
- Henüz TTS ekleme.
- Gerçek .env dosyalarını okuma/kopyalama/loglama.
- Commit/push/merge yapma.

1. Tarayıcıdan kayıt
- Mikrofonu başlat, durdur ve iptal et kontrolleri ekle.
- İlk hedef dil en-US.
- Kayıt sınırı 30 saniye; süre dolduğunda son ses parçalarını koruyarak otomatik durdur ve işle.
- İzin bekleme, kayıt, dönüştürme/gönderme, tanıma ve komut sonucu durumlarını göster.
- AudioWorklet ile gerçek AudioContext.sampleRate üzerinden 16 kHz, mono, signed 16-bit little-endian PCM üret.
- WAV başlığı gerçek üretilmiş PCM ile tutarlı olsun; yalnızca başlık değerlerini değiştirme.
- Kayıt sonunda worklet’in son parçasını bekle; eksik veriyle gönderme.
- Task 2’deki doğrulanmış kaynak temizliği yaklaşımını kullan.
- Durdurma, iptal, hata ve sayfadan ayrılmada mikrofon kanalları, AudioContext, portlar ve URL’ler temizlensin.
- Kayıt/işleme sırasında ikinci kayıt veya komut gönderimini engelle.
- İptal edilmiş/eski oturumun geç gelen sonucu komut çalıştırmasın.
- Zamanlayıcıları nesne metodu gibi yanlış this bağlamıyla çağırarak önceki Illegal invocation hatasını tekrarlama.

2. Flask STT endpoint’i
- POST /api/voice-input oluştur; yalnızca WAV alıp transkript dönsün.
- Bu endpoint doğrudan Library koleksiyonunu değiştirmesin.
- Dosyanın gerçek RIFF/WAVE yapısını, PCM biçimini, 16 kHz/16-bit/mono oluşunu, en fazla 1 MiB ve 30 saniye sınırlarını sunucuda doğrula.
- Boş, eksik veya bozuk WAV ve geçersiz dil isteklerini açık hatayla reddet.
- Azure Speech SDK ve python-dotenv kullan.
- SPEECH_KEY ve SPEECH_REGION yalnızca sunucuda yüklensin.
- .env.example, .gitignore ve requirements.txt dosyalarını güncelle.
- Uygulama, Azure ayarları olmadan açılabilsin; mevcut Library işlemleri çalışsın. Eksik ayar hatası yalnızca ses isteğinde verilsin.

3. Azure tanıma
- Kaydın tamamı için continuous recognition kullan.
- Kesinleşmiş segmentleri sırayla birleştir; interim sonuçları komut çalıştırmakta kullanma.
- Normal bitişi session_stopped ile doğrula.
- Hata veya zaman aşımında kısmi transkripti tamamlanmış komut olarak uygulama.
- Task 2’deki gerçek SDK uyumluluğunu koru:
  cancellation_details alanlarını doğru kullan;
  desteklenmeyen disconnect(handler) çağrısı ekleme;
  oturuma ait dinleyicileri uygun disconnect_all() ile kaldır.
- SDK callback’i içinden bloklayan stop/get beklemesi yapma.
- Start/stop ve sonuç beklemeleri sınırlı olsun; hata sonrası kaynaklar ve işlem kilidi serbest kalsın.
- Gizli bilgiler ve ham SDK hata ayrıntıları istemciye veya loglara sızmasın.

4. Ortak komut akışına bağlantı
- Tam ve başarılı transkript mevcut runCommandText(text) akışına yalnızca bir kez aktarılsın.
- Ayrı parser, ikinci mutasyon yolu veya yeni Library iş mantığı oluşturma.
- Tanınan özgün metni ekranda koru.
- Komut parser’ı tüm girdiyi doğrulamadan değişiklik isteği göndermesin.
- Başarılı mutasyon sonrası liste yenileme hatasını aynı mutasyonu tekrar göndererek çözme.
- responseText üretimini koru; sonraki aşamada TTS bunu okuyacak.
- Mikrofon hatası, komut ayrıştırma hatası ve Library API hatasını ayrı anlaşılır mesajlarla göster.
- İptal ağdaki bir mutasyonun geri alındığı anlamına gelmez. Mutasyon gönderildikten sonraki belirsiz bağlantı durumunda otomatik tekrar yapma.

5. Ses transkriptleri ve alan sınırları
- Azure’un eklediği noktalama ve sayı yazımlarını mevcut parser testleriyle birlikte değerlendir.
- İçeriği bozacak genel noktalama silme veya tüm metni küçük harfe çevirme uygulama.
- Başlık/yazar içeriğini koru; mevcut virgül/tırnak düzeltmesini bozma.
- Açıkça ayrıştırılan virgülsüz örnekler çalışsın:
  Create item type book title The Hobbit author Tolkien pages 310
  Update item four pages three hundred twenty
  Check out item four
- Gerçekten belirsiz transkriptte tahmin ederek mutasyon yapma.
- Belirsizlik durumunda tanınan metin Command alanından düzeltilebilir olsun; kullanıcı Run command ile mevcut akışı kullanabilsin.
- Böyle bir manuel düzeltmeyi başarılı tam sesli yürütme gibi raporlama.

6. Doğrulama
- Mevcut 26 Python ve 34 Node.js testini başlangıç olarak doğrula; başarısızlıkları gizleme.
- Geçerli/geçersiz WAV, eksik ayar, çok segment, sessizlik, timeout, callback hatası ve kaynak temizliği için gerçek SDK yüzeyine uygun mock testleri ekle.
- Mikrofon izni reddi, son PCM parçasını bekleme, otomatik durdurma, iptal sonrası geç yanıtı yok sayma ve tek komuttan tek mutasyon testlerini ekle.
- Tanınan CREATE/GET/LIST/PUT/PATCH/checkout/return/DELETE örneklerinin ortak yürütme yoluna ulaştığını doğrula.
- Headless tarayıcı testleri yapılabiliyorsa gerçek sayfa başlangıcını kullan; mock mikrofon/Azure ile gerçek donanım testini ayır.
- Yapılmamış gerçek Azure/mikrofon testlerini yapılmış gibi belirtme.

README:
- PowerShell kurulum ve çalıştırma.
- Yerel Azure ayarları; anahtarı paylaşmadan yapılandırma.
- İngilizce ses komutları ve ayrıştırma sınırları.
- Manuel test listesi.

PROMPTS:
- Bu istem ve gerçek geliştirme sonuçları.
- Kullanıcı, önceki aşamada diğer komut işlemlerinin doğru çalıştığını bildirdi.
- Son parser düzeltmesinin kullanıcı tarafından yeniden doğrulandığını varsayma.

Sonuçta değişen dosyaları, veri akışını, test sonuçlarını, gerekli kurulum komutlarını ve gerçek mikrofonla denenmesi gereken komutları bildir.
```

### Aşama 3 — Çalışma ve gerçek sonuçlar (2026-11-02)

- Başlangıç branch'i voice-library, port 5002 ve mevcut **26 Python / 34 Node.js testi** doğrulandı; hepsi geçti. Mevcut komut paneli, parser, runner ve Library sözleşmeleri okundu. Task 2'nin PCM/Worklet ve düzeltilmiş continuous STT kaynakları incelendi.
- Yalnızca Mini-Project-2 içine bağımsız `speech_service.py`, `voice-input.mjs`, `voice-worklet.mjs`, `voice-audio.mjs`, `pcm-resampler.mjs` uyarlandı. Hesap makinesi parser'ı, buton mantığı ve TTS kuyruğu taşınmadı. Task 2'ye runtime import/dosya yolu bağımlılığı yoktur.
- Mikrofon paneli en-US başlat/durdur/iptal ve ayrı durum/hata/transkript alanları içerir. Gerçek sampleRate ile sürekli PCM dönüşümü, 30 saniye/960000 bayt sınırı, son parçayı flush ile bekleme, doğru WAV paketleme ve sessiz worklet çıkışı uygulanır. Kayıt sonunda işlenir; interim/canlı komut yürütme yapılmaz.
- `LibraryMicrophone` kaynakları idempotent temizler; izin beklerken, kayıt/işleme ve pagehide iptallerinde eski token/transkript çalıştırılmaz. Zamanlayıcılar native global alıcıyı koruyan sarmalayıcılarla çağrılır. İzin 45 s, son parça 3 s, STT HTTP 90 s ile sınırlıdır. Track, port, düğümler ve AudioContext kapanır; oynatma/object URL üretilmez.
- `/api/voice-input` yalnızca WAV doğrulayıp transkript döndürür; koleksiyona erişmez. 1 MiB/30 s, RIFF boyut/chunk, PCM 16-bit/mono/16 kHz ve byte rate/alignment doğrulanır. FileStorage okuma sonrası kapanır. Upload toplam sınırı yalnızca ses endpoint'indedir; Library POST boyut sözleşmesi değiştirilmez. Geçersiz dil reddedilir; varsayılan en-US'tır.
- SDK 1.53.0 continuous tanıma; kesin segmentlerin sıralı birleşimi, session_stopped zorunluluğu, NoMatch/iptal/timeout/callback/temizlik hatalarında kısmi başarının reddi korundu. Start/stop 5'er s, sonuç 60 s ile sınırlıdır. CancellationDetails.reason/code ve disconnect_all kullanılır. SDK callback'inde stop/get beklenmez. Kilit finally ile bırakılır; ham SDK hata metni veya gizli değer loglanmaz/istemciye aktarılmaz.
- SPEECH_KEY/SPEECH_REGION uygulama klasöründeki açık dotenv yolundan yalnızca ses isteğinde yüklenir. `.env.example` boş anahtar/örnek eastus içerir. Gerçek .env oluşturulmadı, okunmadı, kopyalanmadı veya loglanmadı. SDK/dotenv requirements'a, ham PCM/geçici kayıt ignore kuralları `.gitignore`a eklendi. Ayarlar olmadan sayfa ve mevcut Library işlemleri çalışır.
- Tam transkript tek kez mevcut `runCommandText` yoluna, dahili oturum token'ı ve iptal sinyaliyle aktarılır. Parser değişmedi; ayrı mutasyon yolu/Library modeli yoktur. Ön tür GET'i sırasında iptal olursa yazma yapılmaz. Mutasyon zaten gönderildiyse iptal geri alma sayılmaz; belirsiz ağ sonucu ve tekrar engeli korunur. Başarılı mutasyon sonrası yenileme uyarısı aynı yazıyı tekrarlatmaz.
- Özgün transkript hem ekranda hem düzenlenebilir Command alanında kalır. Genel noktalama silme/küçük harfe çevirme eklenmedi. Parser hatasında manuel düzeltme istenir; sonradan Run ile düzeltme tam sesli başarı olarak işaretlenmez. Mikrofon/STT hataları ile parser/API hataları ayrı gösterilir; yeni kayıtta önceki başarı gizlenir.

### Kullanıcı tarafından bildirilmiş doğrulama

Kullanıcı, önceki aşamada diğer komut işlemlerinin doğru çalıştığını bildirdi. Son alan-sınırı düzeltmesinin kullanıcı tarafından yeniden doğrulandığı varsayılmadı. Önceki tırnaklı oluşturma başarısı da yalnızca kullanıcının bildirdiği kapsamda tutulur; asistanın veya Aşama 3 mikrofonunun doğrulaması olarak sunulmaz.

### Otomatik kontroller

- **42 Python ve 49 Node.js testi geçti.** Başlangıçtaki 26 Python/34 Node regresyonuna 16 STT ve 15 PCM/mikrofon/ortak komut testi eklendi. Geçerli/geçersiz WAV, 30 saniye/1 MiB sınırı, dil, ayarsız sayfa/Library, çok segment/EOF/interim/NoMatch, timeout/iptal/callback/start/stop/cleanup hataları ve kilit kullanımı kontrol edildi. SDK testleri gerçek EventSignal, SpeechRecognizer, SpeechRecognitionResult/EventArgs ve CancellationDetails spec/autospec yüzeyiyle çalışır; dotenv ve Azure çağrıları mock edilir.
- Node testleri izin reddi/izin beklerken iptal, son PCM'yi bekleme, otomatik durdurma, eksik flush reddi, timeout/geç yanıt, 16/44.1/48/96 kHz dönüşümü, gerçek worklet'in 30 saniye/sessiz çıkış sınırı, her komut türü için ortak tek yürütme, parser düzeltmesi, HTTP hata ayrımı, başarılı yazı sonrası liste hatası ve iptal sırasında ön GET/çoktan gönderilmiş mutasyon belirsizliğini kapsar. Tüm JavaScript sözdizimi kontrolleri geçti.
- Eski **18 metin paneli headless işlemi** yeniden geçti. Kaynak main ile karşılaştırmada Library model baytları ve mevcut endpoint fonksiyon gövdeleri aynı kaldı; mock app.run kontrolü `127.0.0.1:5002` başlatmasını doğruladı. Üretim uygulamasında ek koleksiyon yoktur; headless kontroller kendi izole test koleksiyonunu kullanır.
- Headless Chrome'da gerçek sayfa/ES modülleri ve yerel Flask/Library API ile **8 sesli komut türü** (CREATE, GET, LIST, PUT, PATCH, checkout, return, DELETE) başarıyla yürütüldü. Ek bir belirsiz transkript ağda mutasyon yapmadan parser hatası verdi; Command alanında manuel düzeltilerek ayrı işlem olarak çalıştırıldı. Ardından kayıt iptali kontrol edildi. **9 mock STT çağrısı, 10 kapatılmış mock mikrofon track'i ve sıfır JavaScript hatası** görüldü.
- Mikrofon, AudioContext/Worklet kaynakları ve transkriptler bu headless kontrolde mock'tur. Gerçek PCM dönüşümü ayrıca sentetik örneklerle test edilir. Gerçek mikrofon/Azure isteği, fiziksel ses aygıtı, kullanıcının etkileşimli tarayıcı oturumu veya görsel/dar ekran doğrulaması yapılmadı. Commit/push/merge yapılmadı.

## Page düzeltmesi — Gerçek Azure transkriptinde alan noktası (2026-11-02)

### İstem özeti

Yalnızca Mini-Project-2 içinde gerçek Azure transkriptinin ayrıştırılmasını düzelt. Gerçek kullanıcı denemesi:

```text
Create Item Type Book Title Hobbit Author Tolkien. Page 310.
```

Alınan hata: `Sorry, Create requires type, title, author and the correct pages/duration field.` Beklenen komut `action: create`; alanlar `type: book`, `title: Hobbit`, `author: Tolkien`, `page_count: 310`.

Önce hatayı yeniden üret; tekil Page ve alanlar arasındaki noktayı ayrı incele. `page`, `pages`, `page count` etiketlerini destekle. Açık sonraki etiket öncesindeki cümle noktası ayrıştırmayı bozmasın; J.D. Salinger gibi değerlerin iç noktalarını ve özgün harflerini koru. Genel nokta silme veya bütün transkripti küçültme yapma. Virgüllü/tırnaklı ayrıştırmayı ve alan sırasını koru; gerçekten belirsiz, eksik ve tekrarlı girdileri reddet. Tam doğrulamadan API isteği gönderme. STT/model/API sözleşmesini değiştirme. Gerçek transkript, etiket eş anlamlıları, noktalı/noktasız sınırlar, noktalı yazar adları, mevcut CREATE/PUT/PATCH örnekleri ve tek POST için regresyonlar ekle. README/PROMPTS kayıtlarını güncelle; gerçek Azure ile yeniden doğrulama yapılmadığını belirt. Commit/push/merge yapma. İstem mesajda iki kez aynı içerikle yer aldı; burada tek kayıt tutuldu.

### Yeniden üretim ve doğrulanmış neden

- Değişiklikten önce gerçek transkript mevcut parser'da aynı eksik CREATE alanları hatasını verdi.
- `Tolkien Page 310` biçiminde nokta kaldırıldığında aynı hata sürdü: `Page` etiket değildi, sayfa alanı oluşmuyordu.
- `Tolkien. Pages 310.` biçiminde yalnızca çoğul etiket kullanıldığında CREATE ayrıştı fakat yazar `Tolkien.` oldu. `Tolkien Pages 310` ise doğru alanları verdi. Nokta, eksik alan hatasından ayrı bir sınır/değer sorunuydu.

### Düzeltme ve gerçek sonuçlar

- `static/command-parser.mjs`: Etiket tanıma `page/pages/page count` biçimlerini aynı `page_count` alanına bağlar. Farklı eş anlamlılarla tekrar da yinelenen alan sayılır. Açık bir sonraki alan etiketinde yapısal son nokta ayıklanır; iç noktalar, baş harfler, tırnak içi noktalar ve özgün büyük/küçük harf korunur. Virgüllü bölümlerde etiket yalnızca bölüm başında tanınır. Belirsiz virgülsüz PATCH koruması sürer; sonradan gelen bir nokta önceki belirsiz title/author sınırını geçerli yapmaz.
- `test_commands.mjs`: Gerçek transkript, üç eş anlamlı etiket, alan sırası, noktalı/noktasız CREATE/PUT/PATCH, J.D. Salinger ve literal tırnaklı noktalar, eksik/tekrarlı/belirsiz alanlar kontrol edildi.
- `test_script.js`: Gerçek transkript mock STT üzerinden mevcut ortak komut yoluna aktarıldı; beklenen gövdeyle yalnızca bir POST gönderildi. Geçersiz alanlarda hiçbir ağ isteği yapılmadı. Tüketim için ayrı parser veya mutasyon yolu eklenmedi.
- **55 Node.js ve 42 Python testi geçti.** Node testlerinde taklit medya/STT/API kullanıldı; Python regresyon testlerinde gerçek Azure çağrısı yapılmadı. Önceki aşamanın headless tarayıcı sonuçları bu düzeltmede yeniden yapılmış sonuçlar olarak sunulmaz.
- README desteklenen etiketleri, sınırları ve gerçek bulguları açıklayacak şekilde güncellendi. STT kodu, Library modeli/API sözleşmesi ve diğer projeler değiştirilmedi. Gerçek .env içeriği okunmadı. **Düzeltme sonrası gerçek Azure/mikrofon yeniden doğrulaması yapılmadı.** Commit/push/merge yapılmadı.

## Genel tolerans kapsamı — İstem ve sonuçlar (2026-11-02)

### İstem özeti

Son rapor yalnızca page/pages/page count ve noktalı alan sınırı düzeltmesini açıklıyor. Önceki kapsamlı isteğin genel toleranslarını mevcut kod ve testlere göre kontrol et: büyük/küçük harf, fazla boşluk ve satır sonları; alan sınırlarında virgül/nokta/noktalı virgül/iki nokta; komut sonu noktalama; rakamlar ve İngilizce sayı kelimeleri (three hundred and ten); doğru/bozuk binlik gruplama; duration/duration in minutes ve minute/minutes; noktalı isimler ve sayısal başlıklar; sekiz işlemin ortak parser üzerinden çalışması. Her maddeyi uygulandı ve test edildi, eksik veya belgelenmiş belirsizlik olarak bildir. Eksik açık gereksinimleri tamamla; belirsiz metni tahmin ederek kabul etme. Testleri/belgeleri güncelle. Gerçek mikrofon/Azure doğrulaması iddia etme. Yalnızca Mini-Project-2; .env okuma, commit/push/merge yapma.

### Önceki kodda doğrulanan durum

- `voice-library` branch'i doğrulandı. Büyük/küçük harf, boşluk, temel satır sonları, virgül/nokta, rakamlar, `three hundred and ten`, noktalı adlar/sayısal başlıklar ve sekiz işlemin ortak akışı zaten mevcuttu; yeni regresyonlarla kapsamı genişletildi.
- `Create item; type book; title 1984; author J.D. Salinger; pages 310` ve iki noktalı biçimi ayrışmadı. `Get item 1,000`, `Update item 2 duration in minutes 148 minutes` ve `List items?!` de hata verdi. Noktalı virgül/iki nokta, gruplu rakamlar, süre etiketi/birimi ve bitişik son noktalama dizileri eksik olarak yeniden üretildi; önceki page düzeltmesi bunları sağlamıyordu.

### Yapılan değişiklikler ve sınırlar

- `static/command-parser.mjs`: Tırnak dışındaki noktalı virgül ve bölüm ayıran iki nokta açık bölüm sınırı; tam etiketin hemen sonundaki iki nokta değer başlangıcı olarak tanınır. Önceki virgüllü bölüm davranışı ve virgülsüz noktalı sınır yaklaşımı korunur. Tırnak içindeki noktalama aynen kalır; metnin tamamı küçültülmez veya noktalaması genel olarak silinmez. Çok satırlı sayılı GET/DELETE/checkout/return girdileri de desteklenir.
- Komut sonunda `. ! ? ; :` ve bitişik dizileri kabul edilir; sonda virgül eksik bölüm olarak reddedilir. Literal son noktalama tırnakla korunur.
- İngilizce binlik virgülleri yalnızca pozitif sayısal alan doğrulamasında kaldırılır. İlk grup 1–3 basamak/sıfırdan farklı başlangıç, devamında tam üç basamak gerekir; `1,00`, `12,34,567`, `1234,567`, `1, 000`, kesir ve güvenli sınır aşımı reddedilir. Tokenizer gruplu rakamı ayırmaz; sayısal başlık içeriği değiştirilmez.
- `duration` ve `duration in minutes` aynı alana bağlanır; değerde isteğe bağlı minute/minutes birimi kabul edilir. Başka birim, kesir, tekrarlı süre alanı veya sayfaya dakika birimi reddedilir. Yeni API alanı veya sunucu iş mantığı eklenmez.
- Belirsiz virgülsüz title/author sınırları **belgelenmiş belirsizlik** olarak kalır; tırnak veya açık bölüm ayırıcı gerekir. Literal virgül/noktalı virgül/iki nokta için tırnak kullanılır. Bilinmeyen alan tahmin edilmez, desteklenmeyen kelime atlanmaz. README her maddeyi durum tablosunda gösterir; tamamlanan açık maddelerde kalan eksik yoktur.
- `test_commands.mjs`: Altı yeni testle harf/boşluk/satır sonu, dört alan sınırı, son noktalama dizileri, sayısal gruplama, dakika etiket/birimi ve belirsiz/geçersiz girdi regresyonları eklendi.
- `test_script.js`: İki yeni test gerçek form submit olayını ve gerçek parser/runner kaynaklarını taklit DOM/HTTP ile kullanır. Sekiz işlemde HTTP yöntemi/yolu/gövdesi ve tek mutasyon; bozuk grup/birim/alan/belirsizlikte sıfır ağ isteği kontrol edildi. Parser veya tüketici testten elle atlanmadı.

### Doğrulama

**63 Node.js ve 42 Python testi geçti.** Önceki 55 Node testinin üzerine 8 test eklendi. `node --test --test-reporter=dot test_commands.mjs test_script.js test_voice_input.mjs` ve mevcut Python unittest keşfi çalıştırıldı. İlk yeni süre testinde virgülsüz author değeri olarak ayrılmış `Director` sözcüğü kullanılmıştı; parser'ın mevcut belirsizlik koruması bunu doğru reddetti. Testin geçerli yazar örneği Nolan olarak düzeltildi; bu koruma kaldırılmadı.

Bu aşamada headless/gerçek tarayıcı, mikrofon veya Azure yeniden doğrulaması yapılmadı. Mock test başarısı gerçek donanım/servis başarısı değildir. Gerçek .env okunmadı. STT, Library model/API, port 5002 ve diğer projeler değiştirilmedi. Commit/push/merge yapılmadı.

## İki tam manuel CREATE girdisi — İstem ve bulgular (2026-11-02)

### İstem özeti

Sessiz manuel testte iki başarısızlık bildirildi:

```text
Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.
```

Hata: `Unknown or non-editable field. Use type, title, author, page/pages/page count or duration as appropriate.` Beklenen fields: `{"type":"book","title":"Test Book","author":"Test Author","page_count":310}`.

```text
Create item, type DVD, title Inception, author Christopher Nolan, duration in minutes 148.
```

Hata: `Use digits or an unambiguous English cardinal number.` Beklenen fields: `{"type":"dvd","title":"Inception","author":"Christopher Nolan","duration":148}`.

İki girdiyi mevcut parser'da yeniden üret, nedenlerini ayrı doğrula; noktalı virgül bölümleri ve etiket sonu iki noktayı destekle; çok kelimeli duration in minutes etiketini kısa duration'dan önce tam sınırlarıyla tanı. Three hundred and ten dönüşümünü ve sayı çözümleyicisine etiket/birim sızmamasını kontrol et. Genel noktalama silme yapma, başlık/yazar içeriğini ve eski virgüllü/virgülsüz/tırnaklı biçimleri koru. Belirsiz/geçersiz girdide mutasyon yapma. İki tam girdiyi regresyona ekle, ortak runner ile tek doğru POST'u doğrula. Mümkünse gerçek Flask/headless Command panelini kullan. Diğer toleransları ve gerçek bulguları belgele. Yalnızca Mini-Project-2; mikrofon/Azure/ses oynatma, .env okuma, commit/push/merge yok.

### Ayrı ayrı yeniden üretim

- Çalışma başında branch voice-library doğrulandı. İki tam girdi **yeni değişiklikten önce** mevcut diskteki parser'a verildi; ikisi de beklenen fields nesnesini döndürdü. Birincinin bilinmeyen alan ve ikincinin sayı hatası bu kod sürümünde yeniden üretilemedi.
- İlk girdide mevcut tokenizer noktalı virgülü açık bölüm olarak ayırıyor, etiketten sonraki iki nokta tüketiliyor. Test Book/Test Author içindeki alan sözcükleri virgül/noktalı virgülle sınırlandırılmış değer içinde korunuyor; sayı alanına three hundred and ten kalıyor.
- İkincide mevcut fieldAt üç sözcüklü duration in minutes etiketini kısa duration'dan önce tüketiyor; sayı alanına 148 kalıyor. İki hatanın kullanıcının oturumundaki kesin nedeni **doğrulanamadı**. Eski modül/önbellek/başka sunucu olasılığı kesin neden olarak yazılmadı.
- Ayrı bir sınır hatası doğrulandı: `Update item 2 duration "in" "minutes" 148` hatalı biçimi 148 olarak kabul ediliyordu. Bu, bildirilen iki tırnaksız girdinin hata nedeni değildir.

### Değişiklikler

- `static/command-parser.mjs`: Çok kelimeli etiketler önce ve yalnızca tam, tırnaksız word token'larıyla eşleştirilir; kısa duration/page biçimlerine sonra geçilir. Tırnaklı etiket parçalarının yanlış kabulü giderildi. Genel noktalama/harf dönüşümü eklenmedi; model/API/STT değiştirilmedi.
- `test_commands.mjs`: İki tam örneğin beklenen gövdeleri, three hundred and ten → 310, çıplak sayı çözümleyicisinde etiket/birim reddi ve çok kelimeli etiketlerin tam/tırnaksız sınırları test edildi.
- `test_script.js`: Her iki örnek gerçek Command form submit bağlantısı ve ortak parser/runner ile doğru JSON gövdeli tek POST gönderir. Geçersiz tırnaklı süre etiketi de sıfır ağ isteği regresyonuna eklendi.
- `check_commands_browser.py`: İki tam girdi gerçek sayfada Command panelinden gönderilir; fetch gözlemiyle tek POST/yol/gövde, ardından gerçek GET ile saklanan alanlar kontrol edilir. Hatalı tırnaklı etiket mutasyon yapmaz. Mikrofon endpoint'i çağrılırsa test başarısız olur; donanım/Azure/ses kullanılmaz.
- README gerçek yeniden üretim sınırını, ayrı doğrulanan hatayı, iki gövdeyi ve manuel ayırt etme adımlarını anlatır. Genel tolerans durumları korunur: harf/boşluk/satır sonu; dört sınır işareti; komut sonu noktalama; rakam/sayı kelimeleri; doğru/bozuk binlik gruplama; dakika etiketi/birimi; noktalı/sayısal değerler; sekiz ortak işlem uygulandı ve test edildi. Literal ayırıcı veya virgülsüz title/author çakışması belgelenmiş belirsizliktir; tahmin edilmez.

### Çalıştırılan doğrulamalar

- **66 Node.js testi geçti:** `node --test --test-reporter=dot test_commands.mjs test_script.js test_voice_input.mjs`. Önceki 63 teste üç regresyon testi eklendi.
- **42 Python unittest testi geçti.** Azure/dotenv mock'ları kullanılır; gerçek .env okunmaz.
- **Gerçek yerel Flask + headless Chrome: 23 panel kontrolü geçti**, iki tam CREATE için toplam iki POST ve doğru kaydedilmiş alanlar doğrulandı; sıfır JavaScript hatası. Test kendi izole süreç içi koleksiyonunu ve geçici test portunu kullanır; normal uygulama portu 5002 korunur. Kullanıcının açık tarayıcı oturumuna erişilmedi.
- Bu turda mikrofon erişimi, Azure isteği veya ses oynatma yapılmadı. .env okunmadı. Diğer projeler değiştirilmedi; commit/push/merge yapılmadı.

## Aşama 4 — Komut sonuçlarını Azure TTS ile seslendirme (2026-11-02)

### Tam istem

Mini Project 2 — Aşama 4: komut sonuçlarını Azure TTS ile seslendirme.

Önce güncel kodları incele:
- runCommandText ve command-runner.mjs
- responseText üretimi
- runAction/apiRequest/refreshItems
- voice-input.mjs ve kayıt durumları
- speech_service.py ve app.py
- ilgili testler

Week-5-Task-2 içindeki düzeltilmiş TTS/oynatma kodlarını örnek olarak inceleyebilirsin. Yalnızca gerekli parçaları uyarlayıp Mini-Project-2 içinde bağımsız tut.

Kapsam:
- Branch voice-library, port 5002.
- Yalnızca Mini-Project-2 içinde değişiklik yap.
- Model/API sözleşmesi ve çalışan metin/mikrofon komut akışını koru.
- Gerçek .env dosyalarını okuma veya loglama.
- Kullanıcı sessiz ortamda: gerçek mikrofon, Azure çağrısı veya hoparlörden ses oynatma yapma.
- Commit/push/merge yapma.

1. Azure TTS endpoint’i
- POST /api/tts ekle.
- Mevcut sunucu yapılandırmasındaki SPEECH_KEY ve SPEECH_REGION kullanılsın.
- Azure Speech SDK ile İngilizce ses üret; browser speechSynthesis kullanma.
- Ses WAV yanıtı olarak tarayıcıya dönsün; sunucu hoparlöründen çalınmasın.
- Boş/geçersiz/aşırı uzun metin için açık doğrulama ve belgelenmiş sınır uygula.
- Eksik yapılandırma ve servis hataları güvenli JSON mesajları dönsün.
- Library işlemleri Azure ayarları olmadan çalışmaya devam etsin.
- Kütüphane başlığı/yazarı SSML olarak yorumlanmasın; düz metin sentezle.

2. Ortak komut sonucunu seslendir
- Başarılı veya hatalı her metin/ses komutu tamamlandığında ortak responseText seslendirme katmanına gitsin.
- Ayrı sonuç üretimi veya ikinci Library işlemi oluşturma.
- Başarı sesi ancak gerçek API başarısından sonra üretilsin.
- CREATE: tür, gerçek başlık ve sunucunun atadığı ID.
- GET: istenen öğenin temel ayrıntıları ve durumu.
- LIST: filtreye uygun adet ve belgelenmiş sınıra kadar ID/başlık özeti; boş listeyi belirt.
- PUT/PATCH: doğru ID ve tamamlanan güncelleme.
- DELETE: 204 gövdesini okumadan silinen ID.
- Checkout/return: gerçek öğe bilgisi; DVD checkout bakım uyarısı korunsun.
- 400/404/409 ve parser hataları için uygun İngilizce açıklama.
- STT sessizlik/servis hataları komut katmanına ulaşmıyorsa bunlar da uygun ortak bildirim yolundan seslendirilebilsin.
- Ağ hatasında mutasyonun uygulanmadığı kesin değilse bunu olmuş gibi söyleme; otomatik mutasyon tekrarı yapma.
- Başarılı mutasyon sonrası liste yenileme hatasında başarı ile yenileme uyarısını ayır; aynı sonuç iki kez okunmasın.
- İptal edilen/eski oturum geç yanıtla seslendirme başlatmasın.

3. Tarayıcı oynatması
- Görünür “Spoken responses” aç/kapat kontrolü ekle.
- Sessiz kullanım için başlangıçta kapalı olsun; demoda açıkça etkinleştirilebilir olsun.
- Kullanıcı etkileşiminden sonra gelen asenkron oynatmanın reddedilebileceğini ele al.
- audio.play() reddini gizleme; kısa hata ve son yanıtı oynatmak için düğme sun.
- “Play response” yalnızca mevcut yanıtı oynatsın; Library komutunu yeniden çalıştırmasın.
- Sesler üst üste binmesin; kuyruk ve bekleyen istekler sınırlı olsun.
- Mikrofon kaydı başlamadan oynayan/bekleyen sesleri durdur.
- Mikrofon aktifken ses oynatma; geç gelen TTS yanıtları kayıt sırasında başlamasın.
- Mikrofon ve TTS arasında döngü oluşmasın.
- Sesi kapatma ve sayfadan ayrılmada istek/oynatma kaynaklarını temizle; geç sonuçları yok say.
- Object URL ve olay dinleyicilerini temizle.
- TTS hatası Library sonucunu değiştirmesin ve “işlem başarısız” diye sunulmasın; ayrı ses hatası gösterilsin.
- Kullanıcı yeniden ses denediğinde mutasyon tekrarlanmasın.
- Önceki Illegal invocation hatasını tekrarlama: tarayıcı zamanlayıcılarını doğru bağlamla çağır.
- Sayfa yüklenirken arka planda Azure isteği gönderme.

4. Durum yönetimi
- Mevcut busy kontrolü tüm butonları kapatıyorsa ses kapatma/durdurma kontrollerinin kullanılabilirliğini incele.
- Kayıt, komut yürütme ve ses oynatma durumlarını tutarlı yönet.
- Azure işlemlerinde kilit kullanılıyorsa hata/timeout sonrası bırakıldığını doğrula.
- UI durumları: ses kapalı, hazırlanıyor, oynatılıyor, tamamlandı, hata.
- Son yanıt metni ses kapalıyken de görünür kalsın.

5. Testler
- Mevcut testleri koru ve çalıştır.
- TTS endpoint girişleri ve SDK çıktısı için gerçek SDK yüzeyine uygun mock testleri.
- Sekiz işlemin başarı yanıtları ve 404/409/parser hatasının seslendirme yoluna ulaştığı testler.
- Sonuçtan önce başarı sesi olmaması.
- DELETE 204 ve DVD uyarısı.
- Play response ile ikinci mutasyon gönderilmemesi.
- TTS hatasında başarılı Library sonucunun korunması.
- Aç/kapat, geç yanıt, mikrofon başlangıcı, kaynak temizliği ve play reddi.
- Gerçek sayfa ve olay bağlantıları üzerinden headless kontrol; Azure ve medya mock olsun.
- Yapılan mock kontrolleri gerçek ses duyulması olarak raporlama.

README/PROMPTS:
- Gerçek sesli doğrulamanın beklediğini belirt.
- Kullanıcı önceki metin komutlarının çalıştığını bildirdi; son genel tolerans değişikliklerinin mikrofonla yeniden doğrulandığını varsayma.
- Sesli yanıtı açma ve oynatma hatasından kurtulma adımlarını ekle.
- Bu istemi ve gerçek sonuçları kaydet.

Sonuçta değişiklikleri, test sonuçlarını, çalıştırma komutlarını ve daha sonra yapılacak gerçek ses kontrol listesini bildir.

### Uygulama ve gerçek geliştirme sonuçları

- Aktif branch voice-library doğrulandı; AGENTS.md bulunmadı. Yalnızca Mini-Project-2 değiştirildi. Ortak runner/responseText, runAction/apiRequest/refreshItems, mikrofon yaşam döngüsü ve SDK testleri incelendi; Task 2'nin düzeltilmiş TTS/oynatma kaynakları örnek olarak okundu. Hesap makinesi kodu taşınmadı ve runtime bağımlılık oluşturulmadı.
- `app.py`: Yalnızca ses üreten `/api/tts` eklendi. JSON yalnızca text; 2000 karakter/16 KiB sınırı, doğrulamada 400/413, ayar eksikliğinde 503, güvenli servis hatasında 502; başarıda audio/wav/no-store. Library endpoint/model/sözleşme ve port 5002 korunur.
- `speech_service.py`: Mevcut açık dotenv yolu, SPEECH_KEY/SPEECH_REGION ve STT kilidi kullanılır. İstek başına SpeechSynthesizer, audio_config=None, JennyNeural ve Riff16Khz16BitMonoPcm; düz speak_text_async, bellek içi WAV. Sonuç bekleme 30 s, stop 5 s ile sınırlı; finally kilit bırakır. Servis/iptal/boş WAV/timeout/temizlik hatası sahte başarı üretmez; ham exception/cancellation bilgisi istemciye/loga aktarılmaz. Mevcut STT callback/PCM davranışı değiştirilmedi.
- `static/spoken-responses.mjs`: Bağımsız ses katmanı; 3 işlik kuyruk, tek üretim/oynatma, generation ile geç yanıt iptali, AbortController ve sınırlı beklemeler. WAV MIME/boşluk/RIFF kontrolü yapılır. URL ve medya olayları/oynatma kaynakları temizlenir. Audio.play reddi ayrı hatadır; Play response yalnızca son text üzerinden TTS isteği yapar. Native timer çağrıları global bağlamı korur. Sayfa açılışında ses kapalı ve istek yoktur.
- `static/script.js`: Gerçek ortak result.responseText ve yenileme uyarısı sese bağlandı; ikinci parser/runner/mutasyon oluşturulmadı. Başarı gerçek API sonrasındadır. Yenileme-only tekrar veya belirsiz komut tekrar engelinde önceki sonuç yeniden okunmaz. Eski/iptal edilmiş komut ticket/sinyali ses başlatmaz. Ses kontrolleri genel busy kilidinden ayrıdır.
- `static/voice-input.mjs`: Kayıt/işleme boyunca ses durur; güncel yanıt kaynaklar bırakıldıktan sonra kuyruğa alınır. Komut yoluna ulaşmayan STT/izin/timeout hatası ortak onFailure yolundan bildirilir. HTTP STT hataları İngilizce ve güvenli açıklamayla gösterilir. Gerçek mikrofon/PCM/STT mekanizması korunur.
- `templates/index.html` ve küçük CSS eklemesi: Spoken responses kutusu, Play response/Stop speech, ayrı ses durum/hata ve kalıcı son metin; metinler textContent ile gösterilir, dar ekranda sarılır. Gerçek .env okunmadı veya oluşturulmadı. Mevcut bağımlılıklar yeterli olduğundan requirements değiştirilmedi.

### Doğrulama ve sınırlar

- **51 Python testi geçti** (önceki 42 + 9 TTS). SDK 1.53.0 SpeechSynthesizer/SpeechSynthesisResult için create_autospec/spec_set kullanıldı. Geçerli PCM WAV, format/voice, speak_text ve audio_config=None, metin/JSON sınırı, ayarsız Library, iptal/boş/servis hatası, timeout/stop/cleanup ve kilit tekrar kullanımı test edildi. Dotenv/Azure mock; gerçek .env okunmadı.
- **77 Node.js testi geçti** (önceki 66 + 11). Yeni `test_spoken_responses.mjs`, `speech-test-helpers.mjs` ve UI regresyonları: sıra/kapasite, geç TTS, kapat/aç, mikrofon iptali/deferred yanıt, play reddi/replay, hatalı ses/HTTP, timeout/pagehide/URL/olay temizliği. Sekiz komut ve 400/404/409/parser/ağ belirsizliği sonuçlarının ses yoluna bir kez ulaşması, API öncesi ses olmaması, DVD uyarısı/204, refresh warning tek bildirimi, ikinci mutasyon yapmayan replay ve iptal edilmiş geç transkript kontrol edildi. Bunlar gerçek UI kaynakları ve olay bağlantılarını kullanır, DOM/medya/ağ mock'tur.
- Önceki gerçek Flask/Chrome **23 metin paneli kontrolü** yeniden geçti. Mevcut headless mock mikrofon/STT kontrolünde **8 işlem + parser hatası**, 9 mock STT çağrısı, 10 kapatılan mock track ve sıfır JavaScript hatası görüldü.
- Yeni `check_spoken_browser.py` gerçek HTML/ES modülleri, Flask ve izole gerçek Library koleksiyonunu kullanır; synthesize_speech/transcribe_pcm, getUserMedia/AudioContext/Worklet ve Audio mock'tur. Ayrıca Chrome mute edilir. **20 adım**, 19 mock TTS, 2 mock STT, 18 mock play, 18 URL temizliği, 2 kapatılan mock track ve sıfır JavaScript hatasıyla geçti. Başarı öncesi ses olmaması, tüm işlemler, DVD uyarısı/204, refresh-only tekrar, play reddi/kurtulma, HTTP TTS hatasında Library başarısı, kapatma sonrası geç yanıt, mikrofonla karşılıklı dışlama ve sessizlik bildirimi gerçek sayfa olayları üzerinden kontrol edildi. Gerçek ses duyulması iddia edilmez.
- Gerçek Azure isteği, mikrofon erişimi veya hoparlörden ses oynatma yapılmadı; gerçek sesli doğrulama bekliyor. Kullanıcı önceki metin komutlarının çalıştığını bildirdi; son genel tolerans değişikliklerinin mikrofonla yeniden doğrulandığı varsayılmadı.
- Çalıştırma ve daha sonraki gerçek ses kontrol listesi README'dedir. Headless süreçler kendi koleksiyon/geçici port/profillerini kullanır. Commit/push/merge yapılmadı.

## Gerçek transkriptte Duration. etiketi — İstem ve doğrulama (2026-11-02)

### İstem özeti

Yalnızca Mini-Project-2 içinde gerçek ses transkriptindeki alan etiketi/noktalama sorununu incele ve düzelt.

Gerçek Azure transkripti:

```text
Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.
```

Alınan hata: `Sorry, Create requires type, title, author and the correct pages/duration field.` Beklenen CREATE fields:

```json
{"type":"dvd","title":"Inception","author":"Christopher Nolan","duration":148}
```

Önce tam girdiyi mevcut parser'da yeniden üret ve nedeni doğrula. Sayısal alan etiketi ile değeri arasına Azure'un koyduğu nokta gibi işaretleri destekle; duration. 148 minutes, duration: 148 minutes ve duration 148 minutes aynı sonucu üretsin. Page/pages/page count için de tutarlı kontrol et; duration in minutes desteğini koru. Başlık/yazar noktalarını genel olarak silme; J.D. Salinger korunsun. Önceki virgüllü/virgülsüz/tırnaklı/sayı kelimeli örnekler sürsün. Belirsiz, eksik/geçersiz sayılı girdiler mutasyondan önce reddedilsin. STT/model/API sözleşmesini değiştirme. Tam transkripti parser/ortak runner regresyonuna ekle, doğru gövdeyle tek POST'u doğrula; mümkünse gerçek Flask/headless Command panelini dene. Testleri ve README/PROMPTS'ı güncelle; yeni gerçek mikrofon doğrulamasının beklediğini belirt. .env okuma; commit/push/merge yapma.

### Yeniden üretim ve doğrulanmış neden

- Branch voice-library doğrulandı; AGENTS.md bulunmadı. Değişiklik öncesi tam transkript aynı eksik CREATE alanları hatasını verdi. Etiketten nokta kaldırıldığında ve iki nokta kullanıldığında beklenen alanlar elde edildi.
- Tokenizer `Duration.` sözcüğünü noktayla birlikte koruyordu. fieldAt yalnızca tam `duration` etiketini tanıyordu; böylece virgülsüz girdide `Duration. 148 minutes` author değerinin içinde kalıyor, zorunlu duration alanı oluşmuyordu. Sorun sayı kelimeleri veya minutes biriminin kendisi değildi.
- `Update item 3 page. 310`, `Update item 3 page count. 310` ve `Update item 2 duration in minutes. 148 minutes` da değişiklik öncesinde sayı ayrıştırma hatası verdi. Kısa/çok kelimeli etiket sonu noktası tutarlı işlenmiyordu.

### Düzeltme

- `static/command-parser.mjs`: Uzun sayısal etiketler önce, tam tırnaksız word sınırlarıyla tanınır. Yalnızca bilinen sayısal etiketin son sözcüğüne bağlı tek nokta yapısal kabul edilir. Etiketten sonra ayrı tek nokta veya mevcut iki nokta da tüketilir; kaynak token'lar/değerler genel olarak değiştirilmez. Sayısal etiket bulma, ID/alan sınırı ve virgülsüz değer taraması aynı fieldAt yardımcısını kullanır.
- `duration`, `duration in minutes`, `page`, `pages`, `page count` için noktalı, ayrı noktalı, iki noktalı ve noktasız biçimler aynı sayıya bağlanır. Minutes birimi yalnızca süre değeri için mevcut kuralla işlenir. Başlık/yazarın case'i, J.D. Salinger ve tırnaklı noktalar korunur. Virgüllü metin içindeki Duration. Study gibi literal içerik bölünmez.
- `test_commands.mjs`: Üç regresyon testi tam gerçek transkript, tüm etiket/ayraç kombinasyonları, CREATE/PUT/PATCH, rakam/sayı kelimesi/binlik biçimi, noktalı/alıntılı metinler ve eksik/negatif/sıfır/kesir/bozuk/tekrarlı/belirsiz girdileri kapsar.
- `test_script.js`: Bir regresyon testi gerçek Command form olayını/ortak runner'ı kullanır; tam transkript ve iki eşdeğer duration biçimi doğru JSON gövdesiyle yalnızca bir POST gönderir. Geçersiz varyantlar hiçbir API isteği yapmaz.
- `check_commands_browser.py`: Yeni tam transkript, önceki iki tam CREATE örneğine eklendi. Gerçek sayfa/Flask/model ile tek POST/gövde ve kaydedilen alanlar GET üzerinden doğrulanır. Metin kontrolünde mikrofon/TTS çağrıları engellenir; Chrome mute çalışır.
- README etiket/değer sınırını, gerçek nedeni ve sınırlamaları açıklayacak şekilde güncellendi. Yalnızca Mini-Project-2 değiştirildi; STT, model/API ve TTS kodu değiştirilmedi. Gerçek .env okunmadı.

### Çalıştırılan kontroller

- **81 Node.js testi geçti:** `node --test --test-reporter=dot test_commands.mjs test_script.js test_voice_input.mjs test_spoken_responses.mjs`. Önceki 77 test korunup dört test eklendi.
- **51 Python unittest testi geçti.** SDK/dotenv mock'ları gerçek Azure/.env kullanmaz.
- **Gerçek yerel Flask/headless Chrome'da 25 panel kontrolü geçti**, JavaScript hatası görülmedi. Önceki iki ve yeni bir tam CREATE olmak üzere üç örnek için üç doğru POST ve GET doğrulaması; yeni transkript için yalnızca bir POST görüldü. Test izole koleksiyon/geçici port kullanır; normal port 5002 korunur.
- Bu geliştirme turunda asistan gerçek mikrofon, Azure isteği veya ses oynatma kullanmadı; o sırada yeni gerçek mikrofon doğrulaması bekliyordu. **Sonraki kullanıcı bildirimi:** Son DVD parser düzeltmesi gerçek mikrofonla yeniden denendi ve çalıştı. Bu yalnızca kullanıcının bildirdiği kapsamdır; tüm varyantların veya TTS'nin doğrulandığı iddia edilmez. Kullanıcının bildirdiği özgün başarısızlık da asistanın yaptığı test olarak sunulmadı. Commit/push/merge yapılmadı.

## Son belge ve commit öncesi kontrol — 2026-11-02

### İstem özeti

Yalnızca Mini-Project-2 içinde son belge ve commit öncesi kontrolü yap; uygulama davranışını değiştirme. Kullanıcının son DVD parser düzeltmesini gerçek mikrofonla yeniden deneyip çalıştığını bildirdiğini README/PROMPTS'a kaydet. Manuel doğrulamaları otomatik/mock testlerden ayır; ayrıca bildirilmemiş sonuç ekleme. Geliştirme istemleri ve gerçek hata/düzeltme geçmişini kontrol et, eksik geçmiş uydurma. Kurulum/.env.example/port 5002/sesli komut tutarlılığını ve gerçek .env/.venv/__pycache__/.test-deps/geçici seslerin Git dışında olduğunu kontrol et; .env içeriğini okuma. git diff --check çalıştır. Son 51 Python / 81 Node sonucundan sonra uygulama kodu değiştiyse ilgili testleri çalıştır; yalnızca belge değişikliği için tekrarlama. Değişen dosyaları ve kalan teslim işlerini bildir. Git add/commit/push/merge yapma.

### Kullanıcının manuel doğrulaması

Kullanıcı, son DVD parser düzeltmesini **gerçek mikrofonla yeniden denediğini ve çalıştığını** bildirdi. İlgili düzeltme `Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.` transkriptinin sayısal etiket/nokta sınırıdır. Bu, kullanıcının bildirimidir; asistan tarafından yapılmış gerçek mikrofon/Azure testi değildir. Kullanıcının önceki metin komutları için başarı bildirimi de korunur. Ayrı ayrı bildirilmediği için tüm etiket varyantları, TTS'nin gerçekten duyulması, oynatma reddi, iptal/timeout ve diğer mikrofon senaryoları bu manuel başarıya eklenmedi.

### Belge ve Git kontrolü

- Başlangıç/port değişikliği, Aşama 2 parser/runner, alan sınırları, Aşama 3 mikrofon, Page/genel tolerans/tam CREATE girdileri, Aşama 4 TTS ve son Duration. hatasının istem/bulgu/düzeltme kayıtları mevcut. Eski bölümlerin test sayıları ve o zamanki doğrulama sınırları tarihsel kayıttır; eksik konuşma veya yeni sonuç uydurulmadı.
- README'nin güncel doğrulama özeti ve son DVD kaydı kullanıcı bildirimiyle güncellendi. TTS ve diğer ayrı kontrollerin ayrıca bildirilmediği açık tutuldu. Kurulum komutları, .env.example (boş SPEECH_KEY / eastus), requirements, en-US komut grameri ve app.py'deki 127.0.0.1:5002 başlatması tutarlı bulundu.
- Gerçek .env içeriği okunmadan Git yol kontrolleri yapıldı. .env, .venv, __pycache__, .test-deps, tmp/temp/uploads/outputs/recordings ve wav/pcm/mp3 örnek yolları ignore kurallarıyla dışlanır. .env.example için check-ignore çıkış kodu 1: dosya dışlanmıyor ve izlenebilir. Git'te izlenen veya stage edilmiş Mini-Project-2 dosyası yoktur; gizli/üretilmiş dosya stage edilmemiştir.
- README.md ve PROMPTS.md güncellendi. Uygulama davranışı değiştirilmedi. Ek whitespace kontrolü `speech_service.py` sonunda fazladan boş satır buldu; yalnızca bu boş satır temizlendi. Python dosyası değiştiği için **51 Python unittest testi yeniden çalıştırıldı ve geçti**. JavaScript değişmediğinden son **81 Node.js** sonucu korunup Node testleri tekrarlanmadı. Bu turda mikrofon/Azure veya headless oturumu çalıştırılmadı.
- `git diff --check -- Mini-Project-2` ve staged fark kontrolü çalıştırıldı. Proje henüz untracked olduğundan normal diff bu dosyaları kapsamaz; Git'e eklemeden 32 izlenebilir dosyaya ek `git diff --no-index --check` uygulandı. İlk kontroldeki tek sorun yukarıdaki dosya sonu boş satırıydı; temizleme sonrası son kontrolde whitespace sorunu kalmadı. Bu komutlarda gerçek .env veya ignore edilmiş dosya içerikleri okunmadı.
- Stage ve commit kullanıcıya bırakıldı. TTS oynatma ve diğer ayrı gerçek ses kontrollerinin sonuçları ayrıca bildirilmedi; yapılmış gibi teslim kaydı oluşturulmadı. Gerçek .env okunmadı. Git add/commit/push/merge yapılmadı.

### İstem özeti — Teslim düzeni

Yalnızca PROMPTS.md'yi başlangıç kopyası, port 5002, Aşama 2, alan sınırı düzeltmesi, Aşama 3, Page düzeltmesi, genel toleranslar, iki CREATE örneğinin kontrolü, Aşama 4 TTS, Duration. düzeltmesi ve son kontroller sırasına getir. Kısaltılmış istemleri özet olarak etiketle; mevcut tam metinleri ve tarihsel bulguları koru. Belgenin ham transkript olmadığını açıkla. Yeni kullanıcı TTS doğrulamasını en sona, bildirilen kapsamla ekle. Uygulama/test/.env/Git işlemi yapma.

### Belge düzenlemesinin sonucu

Yalnızca bu dosya düzenlendi. Mevcut bölümler kronolojik sıraya taşındı; beş tam istem ve altı önceki istem özeti ayrıldı. Bu düzenleme isteği de yukarıda ayrı bir istem özeti olarak kaydedildi. Mevcut kod blokları, test sayıları, doğrulanmış nedenler ve yeniden üretilemeyen hataların belirsizliği korundu. Eski bekleyen doğrulama kayıtları ait oldukları aşamada bırakıldı. Bu belge düzenlemesinde uygulama kodu değiştirilmedi; test çalıştırılmadı, .env okunmadı ve Git işlemi yapılmadı.

## Yeni kullanıcı doğrulaması — İngilizce TTS

Kullanıcı, İngilizce TTS yanıtlarının hoparlörden doğru şekilde duyulduğunu ayrıca bildirdi.

Bu, kullanıcı tarafından yapılan gerçek manuel kontroldür; asistanın gerçekleştirdiği bir ses testi veya otomatik/mock test sonucu değildir. Bildirim tüm endpoint seslerinin, autoplay reddinin veya iptal senaryolarının ayrı ayrı doğrulandığı şeklinde genişletilmez. Önceki aşamalardaki bekleyen doğrulama ifadeleri kendi zamanlarının kaydı olarak korunur.

## Karma alan ayırıcıları ve title/titled düzeltmesi — 2026-11-03

### Tam istem

```text
Önceki voice-library branch koşulunu bu düzeltme için kaldırıyorum.
Yetkili çalışma branch’i: fix-library-command-boundaries.

Yalnızca Mini-Project-2 içinde doğruladığın karma ayırıcı hatasını düzelt.

İki gerçek transkript:
1. Create item type book titled Hobbit Author Tolkien, pages 500.
2. Create Item Type Book Title Hobbit Author Tolkien, Pages 500.

İkisi için beklenen fields:
{"type":"book","title":"Hobbit","author":"Tolkien","page_count":500}

Doğrulanan neden:
Tek virgül global commaMode açıyor; diğer açık alan sınırları tanınmayınca type değeri sonraki alanları da içeriyor.

- Global virgüllü/virgülsüz seçiminden kaynaklanan bu sorunu gider.
- Aynı komutta karma ayırıcılar bulunan açık, tek anlamlı alanları destekle.
- title/titled eş anlamlılarını destekle.
- Virgülle veya tırnakla sınırlandırılmış başlık/yazar içindeki etiket kelimelerini yanlışlıkla bölme.
- Gerçekten belirsiz girdilerde tahmin ederek mutasyon yapma.
- Mevcut sayı, noktalama, alan sırası ve doğrulama davranışlarını koru.
- Her iki tam transkripti parser ve ortak runner regresyonlarına ekle.
- Doğru gövdeyle yalnızca bir POST gönderildiğini doğrula.
- Mümkünse gerçek Flask/headless panelinde de iki örneği kontrol et.
- Önceki ilgili testleri çalıştır; README/PROMPTS kayıtlarını güncelle.

.env okuma. Commit/push/merge yapma.
```

### Yeniden üretim ve doğrulanmış neden

- Önceki salt okunur incelemede branch main olduğu için dosya değiştirilmemişti. Kullanıcı bu görev için voice-library koşulunu kaldırdı; aktif branch **fix-library-command-boundaries** olarak doğrulandı. Branch değiştirilmedi/oluşturulmadı.
- İki tam transkript bu turda değişiklik öncesi ayrı ayrı parser'a verildi. İkisi de `Create requires type book or DVD.` hatasını verdi.
- `tokens.some(...comma...)` komutun tamamı için commaMode açıyordu. Type okunurken sonraki title/author etiketlerinde durulmadığından ilk örnekte `book titled hobbit author tolkien`, ikincide `book title hobbit author tolkien` type değerine giriyordu. Son şema kontrolü bunu geçersiz tür olarak bildiriyordu; gerçek sorun book türü değil, alan sınırıydı.
- Titled ayrıca desteklenmeyen eş anlamlıydı. Ancak ikinci örnek doğrudan Title içerdiğinden sorun yalnızca titled eksikliğine bağlanamaz; yalnızca eş anlamlı eklemek karma ayırıcı hatasını çözmezdi.

### Düzeltme ve gramer sınırları

- `static/command-parser.mjs`: Global commaMode kaldırıldı. Type/sayısal alanlar ve açık etiket akışındaki metin alanları sonraki açık etikette durur; bir bölümdeki virgül diğer bölümlerin sınırlarını kapatmaz. Title/titled aynı title anahtarına bağlanır ve ikisinin birlikte tekrarı duplicate alan sayılır.
- Metin etiketi ayırıcıyla sınırlandırılmış bir bölümün başındaysa bölümün tırnaksız değeri korunur. Örneğin `Create item type book, title The author of pages, author Test Author, pages 500` içindeki author/pages sözcükleri literal başlık/yazar verisidir. Tırnaklı title/author değeri tek atom olarak okunur; ardından farklı ayırıcı düzenindeki açık etiket gelebilir.
- İki yeni gerçek örnekte bölüm type ile başladığından sonraki title/titled ve author alanları açık akış olarak ayrı okunur; pages bölümüne gelindiğinde type yalnızca book'tur. İkisi de beklenen dört alanı üretir.
- Korunan bir author bölümünün içindeki `pages 500` gibi sözcükler, eksik zorunlu alanı tamamlamak için tahminle yeniden bölünmez. Örneğin `Create item type book title Hobbit, author Tolkien pages 500` eksik pages nedeniyle reddedilir; yalnızca belirsiz author değerini tırnaklayarak veya pages öncesine ayırıcı koyarak sınır açıklaştırılabilir. Tam komutun tek tarz ayırıcı kullanması gerekmez. Sınırlandırılmamış isteğe bağlı title/author PATCH belirsizlik kontrolü sürer.
- Sayı/sayı kelimesi/binlik, duration in minutes, etiket sonu nokta, alan sırası, J.D. Salinger, literal tırnak/virgül ve eski validasyon regresyonları korunur. Negatif/kesir/eksik sayı, duplicate alias, bilinmeyen alan ve belirsizlikte ön GET veya mutasyon yapılmaz. Backend, STT/TTS ve Library model/API değiştirilmedi.

### Testler ve gerçek sonuçlar

- **87 Node.js testi geçti**: `node --test --test-reporter=dot test_commands.mjs test_script.js test_voice_input.mjs test_spoken_responses.mjs`. Önceki 81 test korunup dört parser ve iki gerçek UI kaynağı/ortak runner regresyonu eklendi. Her tam transkript gerçek Command form olayıyla doğru gövdeli **bir POST /api/items** gönderir; geçersiz/belirsiz varyantlarda sıfır API isteği kontrol edildi.
- **51 Python unittest testi geçti**; API/STT/TTS regresyonları mock SDK/dotenv ile çalışır. Gerçek Azure/.env kullanılmadı.
- Gerçek yerel Flask/Chrome headless Command panelinde **29 kontrol geçti**, JavaScript hatası görülmedi. Beş tam CREATE regresyonu (önceki üç ve yeni iki) için doğru gövdeli beş POST ve gerçek GET doğrulaması görüldü; yeni örneklerin her biri tek POST gönderdi. İzole süreç koleksiyonu/geçici port kullanıldı; uygulama portu 5002 korunur. Mikrofon/TTS istekleri testte engellenir ve Chrome mute çalışır.
- `test_commands.mjs`, `test_script.js`, `check_commands_browser.py`, README ve bu kayıt güncellendi. Yalnızca Mini-Project-2 içinde çalışıldı. Gerçek .env okunmadı. Commit/push/merge yapılmadı.
- Gerçek kullanıcı mikrofonuyla **bu karma ayırıcı düzeltmesinin yeniden doğrulaması yapılmadı**. Önceki DVD ve İngilizce TTS manuel bildirimleri bu yeni düzeltmenin veya tüm ses senaryolarının doğrulaması sayılmaz. Önceki yeniden üretilemeyen iki ayrı CREATE vakasının belirsizliği değiştirilmedi.

## Noktalı gerçek PUT transkripti — takip düzeltmesi (2026-11-03)

### İstem özeti ve kesinleşen hata çifti

Kullanıcı, `Replace item six. Title revised Hobbit. Author Tolkien, pages 200.` girdisinin hata verdiğini bildirdi. İlk bildirimde son denemenin hata mesajı paylaşılmamıştı; ardından kesin mesaj **`Sorry, Replace requires title, author and pages or duration.`** olarak ayrıca verildi. Bu kayıt yalnızca bu Tolkien transkripti–hata çiftini kullanır. Önceki Arthur içeren denemenin tam girdisi veya hata mesajı buraya taşınmadı, tahmin edilmedi.

Beklenen istek:

```http
PUT /api/items/6
```

```json
{"title":"revised Hobbit","author":"Tolkien","page_count":200}
```

Kullanıcı güncel branch/kod durumunun bildirilmesini ve önceki karma ayırıcı düzeltmesinin varlığının kontrol edilmesini istedi. Main tek başına durma nedeni değil; yalnızca Mini-Project-2 içinde takip düzeltmesine yetki verdi. ID sonu nokta, Title/Author öncesindeki noktalar ve pages öncesindeki virgül ayrı incelenmeli; doğrulanan neden ortak CREATE/PUT/PATCH parser'ında düzeltilmeli. Başlık/yazar içeriği genel noktalama silmeyle bozulmamalı; belirsizlik tahminle mutasyona dönmemeli. Gerçek transkript/rakamlı ID, tam virgüllü/virgülsüz PUT, benzer PATCH, noktalı adlar/tırnaklar/eski CREATE ve hatalı girdiler regresyona alınmalı. Geçerli işlemde tür GET'i ve tek doğru PUT doğrulanmalı. Gerçek Flask/headless testinde ID 6 Book yalnızca test kurulumunda hazırlanmalı; normal koleksiyon değiştirilmemeli. STT/model/API değişikliği, .env okuma, commit/push/merge yok.

### Başlangıç ve ayrı yeniden üretimler

- Aktif branch **main** idi; Mini-Project-2 çalışma ağacı başlangıçta temizdi. Title/titled eş anlamlıları ve önceki global commaMode kaldırma düzeltmesi kodda mevcuttu. Kullanıcının bu takip görevi için verdiği main yetkisiyle devam edildi; branch değiştirilmedi/oluşturulmadı. AGENTS.md bulunmadı.
- Tam transkript parser'da `Replace requires title, author and pages or duration.` hatasını verdi; mevcut UI aynı hataya `Sorry, ` ön ekini ekler. Bu, kullanıcı tarafından sonradan verilen kesin mesajla eşleşir.
- Yalnızca ID sonu nokta kaldırılıp `item six Title ...` yapıldığında hata sürdü. ID yolu `six.` sözcüğünü zaten `six` → **6** olarak doğru çözümlüyordu.
- Hobbit sonundaki nokta kaldırıldığında da hata sürdü. Title alanı, daha sonraki pages virgülü nedeniyle yerel korunan bölüm olarak okunuyordu; `revised Hobbit. Author Tolkien` tek title değeri kalıyor, author alanı oluşmuyordu.
- Yalnızca pages öncesindeki virgül kaldırıldığında noktalı PUT doğru üç alanı verdi. Tam virgüllü ve tam virgülsüz PUT kontrol örnekleri de zaten çalışıyordu. Sorun PUT endpoint'i veya Tolkien sözcüğü değil, açık cümle sınırının yerel metin koruması içinde devre dışı kalmasıydı.
- Benzer `Update item six. Title revised Hobbit. Author Tolkien, pages 200.` girdisi eski parser'da hata vermeden `title: revised Hobbit. Author Tolkien` ve `page_count: 200` döndürüyordu; author ayrı değildi. Bu yanlış alan birleştirme yalnızca parser'da yeniden üretildi; gerçek koleksiyona yanlış PATCH uygulanmadı.

### Düzeltme ve kapsam

- `static/command-parser.mjs`: Bilinen alan etiketinin önündeki tek cümle noktası, bölüm sonunda virgül olsa da açık alan sınırı kabul edilir. Ayrı nokta token'ı ve tam sözcüğün sonundaki nokta aynı sınır davranışını kullanır. ID/sayı çözümlemesi değiştirilmedi; kaynak metinden genel noktalama silinmedi. Ortak parser düzeltmesi CREATE/PUT/PATCH akışlarına uygulanır.
- `J.D.` ve `J.` gibi baş harf noktaları cümle sınırı sayılmaz. Bilinen etiketten önce olmayan iç noktalar ve tırnak içindeki tüm literal içerik korunur. `title "Notes. Author biography"` tek başlıktır; tırnaksız nokta + bilinen etiket dizisi açık gramer sınırıdır. Ayırıcı işareti olmadan iki isteğe bağlı title/author yorumu gerektiren PATCH belirsizliği reddedilmeye devam eder.
- `test_commands.mjs`: Beş yeni test tam gerçek/rakamlı ID PUT, ID noktası kontrolü, ayrı nokta, eşdeğer virgüllü/virgülsüz PUT, benzer PATCH, noktalı adlar/tırnaklı metinler, eksik/geçersiz alanlar ve saf ortak runner'da tür GET'i + tek PUT'u kapsar.
- `test_script.js`: İki yeni test gerçek form olay bağlantısı ve ortak runner üzerinden GET /api/items/6 → tek PUT/PATCH /api/items/6 sırasını, tam JSON gövdesini ve geçersiz/belirsiz örneklerde tür GET'i dahil sıfır API isteğini doğrular.
- Yeni `check_put_browser.py`: Gerçek LibraryCollection ile beş test Book'u ve ID 6 Book fixture'ı yalnızca izole test sürecinde oluşturulur. Normal uygulama koleksiyonu patch süresi dışında korunur; test sonunda nesne ve içerik eşitliği ayrıca kontrol edilir. Gerçek sayfa/Flask üzerinden istek sırası, tek yazma, body ve kaydedilen alanlar doğrulanır. Mikrofon/TTS/SDK dotenv çağrıları engellenir; Chrome mute çalışır. Normal uygulamanın başlangıç verileri değiştirilmedi.
- README gramer, yeni kontrol komutu ve güncel test sonuçları için güncellendi. STT/TTS, model ve API kodu/sözleşmesi değiştirilmedi; port 5002 korunur.

### Çalıştırılan kontroller ve gerçek sonuçlar

- **94 Node.js testi geçti**: `node --test --test-reporter=dot test_commands.mjs test_script.js test_voice_input.mjs test_spoken_responses.mjs`. Önceki 87 test ve CREATE karma ayırıcı regresyonları korunup yedi test eklendi.
- İlk Python/headless başlatma girişimleri otomatik izin incelemesinin zaman aşımı/kapasite hataları nedeniyle çalıştırılmadı; bunlar test başarısızlığı olarak sayılmadı. Kullanıcı yeniden denemeye açık onay verdi; sonraki çağrı çalıştı ve aşağıdaki gerçek otomatik sonuçlar alındı.
- **51 Python unittest testi geçti**; SDK/dotenv mock'ları kullanıldı. Gerçek .env/Azure çağrısı yapılmadı.
- Yeni gerçek yerel Flask/headless kontrolde **10 senaryo geçti**: 5 PUT (tam gerçek, rakamlı ID, tam virgüllü, tam virgülsüz, tırnaklı/noktalı ad), 1 benzer PATCH ve 4 beklenen hatalı giriş. Fixture ID **6**; her geçerli örnekte önce tür GET'i, sonra **yalnızca bir** doğru PUT/PATCH, ardından gerçek GET ile kaydedilen alanlar kontrol edildi. Hatalı girişler hiç API isteği göndermedi. JavaScript hatası yoktu; normal koleksiyon değişmedi.
- Önceki **29 gerçek Flask/headless Command kontrolü** de yeniden geçti; beş tam CREATE örneği tek doğru POST/GET ile doğrulandı, JavaScript hatası görülmedi.
- Gerçek mikrofon/Azure veya ses oynatma yapılmadı. Bu takip düzeltmesinin kullanıcı tarafından gerçek mikrofonla yeniden doğrulandığı iddia edilmez. Önceki DVD ve TTS manuel bildirimleri kendi kapsamlarında korunur.
- Yalnızca Mini-Project-2 içinde parser, iki Node test dosyası, yeni headless test ve belgeler değiştirildi. .env okunmadı. Git add/commit/push/merge yapılmadı.

## PUT/PATCH toplu inceleme ve ortak alan kuralları — 2026-11-03

### İstem özeti

Kullanıcı demo sırasında hata veren PUT/PATCH komutlarını tek kapsamda, örneğe özel yamalar yerine CREATE/PUT/PATCH için ortak alan kurallarıyla inceleyip düzeltmeyi istedi. Önce aktif branch/status/kaynaklar okunmalı; main durma nedeni değil, yalnızca Mini-Project-2 yetkili. Mevcut değişiklikleri koru; port 5002/STT/model/API aynı kalsın. .env okuma/loglama, gerçek mikrofon/Azure, git add/commit/push/merge yok. Parser/runner/script/voice-input ve gerçek form/headless akışlarını incele; önceki karma ayırıcı ve title/titled desteğini gerçekten doğrula. Her örneğin önceki sonucunu/token ve sınır davranışını kaydet, sonra düzelt. Arthur → author dönüşümü yapma. Nokta/iki nokta metin/sayı etiketlerinde tutarlı olsun; içerik, noktalı adlar, tırnaklar, sayı ve güvenlik kontrolleri korunsun. Ayrı parser/iş motoru oluşturma; tam doğrulamadan ağ isteği, API başarısından önce başarı/ses veya yenileme hatası nedeniyle ikinci mutasyon olmasın. İzole Book ID 3/6 ile gerçek Command panelinde GET → tek PUT/PATCH/gövde/kayıt doğrulaması ve JavaScript hata kontrolü yap; eski CREATE, mikrofon ve TTS regresyonlarını koru. Yeniden üretilemeyen kullanıcı PATCH hatası için kesin neden uydurma; gerçek mikrofon doğrulamasını bekleyen olarak ayır.

### Kullanıcının bildirdiği girdiler

Bildirilen ortak PUT hata mesajı: `Sorry, Replace requires title, author and pages or duration.`

```text
A: Replace item six. Title revised Hobbit. Author Tolkien, pages 200.
B: Replace item six. Title revised Hobbit author. Tolkien, pages 200.
C: Replace item 3 titled Revised Hobbit author Tolkien, pages 200.
D: Replace item 3 title Revised Hobbit author Tolkien, pages 200.
```

A/B için ID 6 ve küçük harfle `revised Hobbit`; C/D için ID 3 ve büyük harfle `Revised Hobbit` beklenir. Author Tolkien, page_count 200'dür. Önce tür GET'i, ardından tek PUT gerekir. Önceki ayrı Arthur Tolkien denemesi bu girdilerle birleştirilmedi; Arthur kişi adı olarak korunur.

Kullanıcının PATCH için paylaştığı metin (ekrandaki birebir Azure transkripti olduğu **doğrulanmadı**):

```text
Update item three pages three hundred thirty.
```

Bildirilen hata: `Sorry, Unknown command. Use Create, List, Get, Replace, Update, Delete, Check out or Return.` Mesajdaki atıf tırnakları gerçek girdinin parçası sayılmadı. Ayrı tanılama örnekleri olarak `Update item 3 pages 330.` ve dışı eşleşmiş tipografik tırnaklı `“Update item three pages three hundred thirty.”` da denendi; sonuncusu kullanıcı tarafından birebir transkript olarak bildirilmiş değildir.

### Başlangıç durumu ve değişiklik öncesi yeniden üretim

- Branch **main** idi. Önceki turdan README, PROMPTS, parser, iki Node test dosyası değişikliği ve izlenmeyen check_put_browser.py mevcuttu; silinmedi/geri alınmadı. AGENTS.md bulunmadı. Global commaMode'un kaldırılmış olduğu, yerel bölüm koruması ve title/titled desteği kaynakta doğrulandı.
- Parser'ın mevcut tokenizer/alan tanıması, sonuç doğrulaması ve script/voice-input'un aynı runCommandText/runner'a bağlanması okundu. Salt okunur tanılamada gerçek parser kaynak kodundan token/değerler incelendi; uygulama dosyasına tanılama/log eklenmedi, API çağrılmadı.

| Girdi | Değişiklik öncesi gerçek yerel sonuç | İncelenen sınır/neden |
| --- | --- | --- |
| A | Zaten doğru üç alanla geçiyordu. | `Replace item` başlığı, `six.` → 6; Hobbit. öncesi değil, Hobbit. sonrasındaki Author etiketi önceki takip düzeltmesiyle ayrı okunuyordu. Demo hatası bu kod durumunda yeniden üretilmedi. |
| B | PUT zorunlu alan hatası yeniden üretildi. | author. tek word token'ıydı; yalnızca sayısal etiketlerin terminal noktası desteklendiğinden alan sayılmıyordu. title `revised Hobbit author. Tolkien` oluyor, author eksik kalıyordu. |
| C | Aynı PUT zorunlu alan hatası yeniden üretildi. | ID token'ı 3, titled zaten title olarak tanınıyordu; gelecekteki virgül, ilk title alanını korumalı bölüm saydığı için `Revised Hobbit author Tolkien` tek değer oluyordu. |
| D | C ile aynı hata yeniden üretildi. | title normal etiketti; sorun eş anlamlı değil, sağdaki virgülün geriye dönük bölüm korumasıydı. |
| Çıplak PATCH sayı kelimeleri | Zaten ID 3 / page_count 330 ile geçiyordu. | `Update item` başlığı tanınıyor; ID three ve pages değeri three hundred thirty, mevcut pozitif sayı çözümleyicisiyle doğru ayrılıyordu. |
| Çıplak rakamlı PATCH | Zaten geçiyordu. | ID 3, pages 330; Unknown command üretilmedi. |
| Dış tipografik tırnaklı PATCH tanılaması | Unknown command üretildi. | Baştaki U+201C nedeniyle başlık regex'i eşleşmiyordu. Bu tanılama, kullanıcının gerçek girdisinde dış tırnak bulunduğunu veya hatasının nedenini doğrulamaz. |

### Ortak düzeltme ve korunmuş belirsizlikler

- `static/command-parser.mjs`: Metin/sayı alanları artık tek etiket tablosuyla tanınır. Uzun etiket önce gelir, title/titled aynı title alanıdır; bilinen etiketin son sözcüğündeki tek nokta veya etiket sonrası iki nokta tüm alanlarda aynı mantıktadır. `title.`, `titled.`, `author.`, `pages.`, `duration.` ve ayrı nokta desteklenir. İçerik token'ları genel olarak yeniden yazılmaz.
- Yerel metin koruması yalnızca **açık sol bölüm ayırıcısı** ile başlatılır. Henüz okunmamış sağ virgül ilk text alanını korumalı yapıp Author'ı yutmaz; C/D ve eşdeğer PUT böylece ortak açık etiket akışıyla çalışır. Sol virgülle başlayan metindeki yalın alan sözcükleri literal kalır; açık nokta/iki noktalı etiket veya önceki cümle noktası yapısal sınırdır. Bu işaretli diziyi literal başlık içinde tutmak için tırnak gerekir. Tırnaklı alan tek atom olarak korunur. Eksik/tekrarlı/bilinmeyen alan, sayı hatası ve işaretsiz iki isteğe bağlı text alanı belirsizliği reddedilir.
- Yalnızca tüm komutun dışında eşleşmiş `“…”` veya `‘…’` çifti varsa ve içi bilinen komut başlangıcı taşıyorsa tek dış çift ayrılır. İç tırnaklar/literal tipografik karakterler silinmez; yarım/uyumsuz çift tahminle tamamlanmaz. Bu sınırlı dış tırnak desteği bir tanılama bulgusunu kapsar; çıplak PATCH için kullanıcı hatası düzeltilmiş veya nedeni doğrulanmış gibi sunulmaz.
- Genel Arthur → author, noktalama silme, tüm transkripti küçültme veya doğrulama koruması kaldırma yoktur. J.D. Salinger, sayısal başlıklar, mevcut sayı/bozuk binlik denetimleri ve özgün Revised/revised yazımı korunur.
- `command-regression-cases.json`: A/B/C/D, iki çıplak PATCH ve yalnızca tanılama olan dış tırnaklı örnek tek test tablosuna kondu. Origin alanları gerçek transkript bildirimi, birebirliği doğrulanmamış kullanıcı metni ve tanılama girdisini ayırır. Bu JSON yalnızca testlerde okunur; uygulama bağımlılığı veya ikinci parser değildir.
- `test_commands.mjs` ve `test_script.js`: Tablo, etiket/ayraç matrisi, tırnak/Arthur/bozuk girdi, gerçek formdan doğru GET/yöntem/path/body, sıfır ağ isteğiyle parser hatası, mikrofon mock'undan ortak giriş, çift gönderim engeli ve API öncesi başarı/ses olmaması eklendi. Başarılı PUT/PATCH sonrası yenileme hatasında aynı komut yalnızca GET yeniler; yazma ve TTS bildirimi tekrar edilmez.
- `check_put_browser.py`: Aynı test tablosunu gerçek sayfada kullanır; ID 3 ve 6 Book fixture'ları yalnızca izole koleksiyondadır. Güncel tür GET'i → tek doğru yazma → kaydedilen alanlar doğrulanır; normal koleksiyonun aynı kaldığı da kontrol edilir. Yenileme hatası ve yalnızca GET ile tekrar eklendi. Önceki eşdeğer PUT, noktalı/tırnaklı ad ve geçersiz girişler korunur. README güncel grameri ve doğrulama sınırlarını açıklar.
- Runner, script ve voice-input kaynakları incelendi fakat değiştirilmedi; tek ortak parser/yürütme yolu kullanılır. Backend/model/API sözleşmesi, STT/TTS ve port 5002 değiştirilmedi. Kullanıcının mevcut değişiklikleri korundu.

### Güncel sonuçlar

| Girdi | Değişiklik sonrası ve gerçek Command paneli |
| --- | --- |
| A/B | GET /api/items/6 → tek PUT /api/items/6; title `revised Hobbit`, author Tolkien, page_count 200. |
| C/D | GET /api/items/3 → tek PUT /api/items/3; title `Revised Hobbit`, author Tolkien, page_count 200. |
| İki çıplak PATCH | GET /api/items/3 → tek PATCH /api/items/3, yalnızca `{"page_count":330}`. Önceden de çalışan girdi olarak korunur. |
| Dış tırnaklı tanılama | Aynı PATCH akışı; sadece dış çift ayrılır. Kullanıcı hatasının kesin nedeni olduğu iddia edilmez. |

- **103 Node.js testi geçti.** Bu turda mevcut 94 test yeniden çalıştırıldı; dört parser ve beş arayüz/runner testi eklendi. Önceki rapordaki sayı güncel test yerine kullanılmadı. Testler gerçek kaynak/form olaylarını ve mock DOM/ağ/medyayı kullanır.
- Projedeki mevcut `.venv` ile SDK sürümü **1.53.0** doğrulandı; **51 Python unittest testi geçti**, SDK/dotenv I/O mock'tur. Gerçek .env okunmadı. İlk kısıtlı headless çalıştırmada Chrome `GPU process isn't usable` hatasıyla rapor üretmeden kapandı; bu uygulama/parser test başarısızlığı sayılmadı. Uygun süreç izniyle aşağıdaki gerçek headless kontroller yeniden çalıştırılıp tamamlandı.
- **check_put_browser.py: 21 adım geçti**: 13 geçerli varyant (9 PUT, 4 PATCH), ayrıca başarılı bir PUT sonrasında liste yenileme hatası ve yalnızca GET tekrarı, 6 hatalı giriş. A/B/C/D ve PATCH örnekleri gerçek Command panelinde çalıştı; GET sonrası tek doğru mutasyon ve kaydedilen alanlar kontrol edildi. Parser hatasında ağ isteği yoktu; JavaScript error/unhandledrejection sıfırdı. ID 3/6 fixture koleksiyonu izoledir; normal koleksiyon değişmedi.
- **check_commands_browser.py: önceki 29 adım geçti.** Gerçek CREATE transkriptleri ve diğer Library komutları korundu; beş tam CREATE için tek POST/gövde/GET doğrulaması ve sıfır JavaScript hatası.
- **check_voice_browser.py** yeniden geçti: sekiz işlem ve parser hatası, 9 mock STT çağrısı, 10 kapatılan mock track, sıfır JavaScript hatası. **check_spoken_browser.py** yeniden geçti: 20 adım, 19 mock TTS/2 mock STT, 18 mock play/18 URL temizliği, 2 kapatılan mock track, sıfır JavaScript hatası. Bunlar gerçek mikrofon veya ses duyulması doğrulaması değildir.
- Yeniden üretilemeyen nokta: Kullanıcının çıplak PATCH için bildirdiği Unknown command mesajının gerçek nedeni. İki çıplak metin başlangıç parser'ında ve güncel gerçek sayfada çalıştı; ekrandaki birebir Azure transkripti henüz doğrulanmadı. Önbellek, Azure veya dış tırnak kaynaklı olduğuna dair kesin iddia yoktur.
- Bu toplu değişikliklerin **gerçek mikrofon/Azure ile yeniden kullanıcı doğrulaması bekliyor**. Önceki DVD/TTS manuel bildirimleri kendi kapsamlarında korunur. Gerçek mikrofon/Azure/ses oynatma yapılmadı; yalnızca Mini-Project-2 değiştirildi. .env okunmadı; git add/commit/push/merge yapılmadı.
