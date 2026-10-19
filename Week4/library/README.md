# Week 4 Library — Flask REST API

`Book`, `DVD` ve `LibraryCollection` modellerini kullanan Flask REST API ve web arayüzü. İş kuralları, alan doğrulaması ve atomik güncellemeler `custom_classes.py` içindedir; `app.py` HTTP/JSON çevirisini yapar. Veritabanı yoktur.

Uygulama boyunca tek bir koleksiyon kullanılır. Başlangıçta iki kitap ve bir DVD eklenir (ID: 1, 2, 3). Veriler bellekte tutulur; süreç yeniden başladığında başlangıç verileri yüklenir. ID'ler aynı koleksiyonun yaşamı boyunca tekrar kullanılmaz.

## Kurulum ve çalıştırma

Windows Python ve pip kurulu olmalıdır. PowerShell'de EE471 repo kökünden:

```powershell
cd .\Week4\library
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Arayüz: <http://127.0.0.1:5000>. API adresi: `http://127.0.0.1:5000/api/items`. Sunucuyu `Ctrl+C` ile durdurabilirsiniz. `app.py` import edilince sunucu başlamaz; doğrudan çalıştırılınca başlar.

## Web arayüzü kullanımı

- Soldaki koleksiyonda başlık, yazar/yönetmen, tür, sayfa/süre ve müsaitlik etiketi gösterilir. All / Book / DVD ve Available only filtreleri birlikte kullanılabilir; filtreleme API üzerinden yapılır.
- Sağdaki formdan başlık, yazar, tür ve sayfa/süre girerek Add item ile öğe ekleyin. Kalem ikonuyla mevcut öğeyi düzenleyin; tür seçimi kilitlenir. Save changes, yalnızca düzenlenebilir alanları PATCH ile gönderir. Cancel formu temizleyip ekleme moduna döner.
- Checkout ve Return modelin durum geçişlerini uygular. DVD bakım mesajı dahil sunucunun başarı mesajı sayfada gösterilir.
- Çöp kutusu ikonuyla silmeyi deneyin. Ödünçteki öğede buton etkin kalır; sunucunun HTTP 409 hata mesajı görünür. Başarılı DELETE'in boş 204 gövdesi JSON olarak okunmaz.
- Başarılı değişiklikten sonra liste mevcut filtrelerle yeniden yüklenir. Liste isteği başladığında eski kartlar ve sayaç kaldırılır; başarısız filtre isteğinde eski sonuçlar yeni filtre altında gösterilmez. Kaydetme hatasında form girdileri korunur. İstek sırasında kontroller geçici olarak devre dışı kalır; sonrasında tekrar kullanılabilir. Düzenleme modunda tür alanı kilitli kalır.
- Boş liste, yükleniyor, hata ve başarı alanları bulunur. Ağ hatasında bağlantı mesajı gösterilir; Refresh list ile yeniden deneyebilirsiniz. Başarılı değişiklikten sonraki liste yükleme başarısız olursa başarı ve hata mesajları birlikte görülebilir. Oluşturulan öğenin ID'si hemen form durumuna alınır: girdiler korunur, tür kilitlenir ve Save changes mevcut öğeye PATCH gönderir; ikinci bir öğe oluşturulmaz. Listeyi tekrar yüklemek için Refresh list kullanılabilir.
- Tasarım `Week4/design/library.png` referansını izler. Masaüstünde liste/form iki sütun, 800 px ve altında tek sütundur. Kart metinleri ve mesajlar satıra bölünür. Başlangıç öğelerinin mevcut müsaitlik durumları değiştirilmemiştir.

## Endpoint'ler

| Metot | Yol | Davranış | HTTP durumları |
| --- | --- | --- | --- |
| GET | `/` | HTML arayüzünü sunar. | 200 |
| POST | `/api/items` | Book/DVD oluşturur; öğeyi döndürür. | 201, 400 |
| GET | `/api/items` | Öğelerin JSON listesini döndürür; filtrelenebilir. | 200, 400 |
| GET | `/api/items/<id>` | Tek öğeyi döndürür. | 200, 404 |
| PUT | `/api/items/<id>` | Tüm düzenlenebilir alanları zorunlu tutar. | 200, 400, 404 |
| PATCH | `/api/items/<id>` | En az bir düzenlenebilir alanı günceller. | 200, 400, 404 |
| DELETE | `/api/items/<id>` | Müsait öğeyi siler; yanıt gövdesi tamamen boştur. | 204, 404, 409 |
| POST | `/api/items/<id>/checkout` | Öğeyi ödünç verir. | 200, 404, 409 |
| POST | `/api/items/<id>/return` | Öğeyi iade alır. | 200, 404, 409 |

Liste filtreleri: `?available=true`, `?available=false`, `?type=book`, `?type=dvd`. Birlikte kullanılabilir: `/api/items?available=true&type=book`. Parametre yoksa ilgili filtre uygulanmaz. Değerler küçük harfle yazılır; boş veya geçersiz filtre değeri HTTP 400 döndürür.

## JSON örnekleri

POST, PUT ve PATCH gövdeleri JSON nesnesi olmalı; `Content-Type: application/json` gönderilmelidir. Başlık ve yazar boş olmayan metin; sayfa sayısı ve süre pozitif integer olmalıdır. Boolean, kesirli sayı ve sayısal metin sayfa/süre için kabul edilmez. Bilinmeyen ve türe uygun olmayan alanlar reddedilir.

Kitap oluşturma — `POST /api/items`:

```json
{"type":"book","title":"The Hobbit","author":"J.R.R. Tolkien","page_count":310}
```

Başarı — HTTP 201 (yeni ID, mevcut koleksiyona göre atanır):

```json
{"id":4,"type":"book","title":"The Hobbit","author":"J.R.R. Tolkien","is_available":true,"page_count":310}
```

DVD oluşturma — `POST /api/items`:

```json
{"type":"dvd","title":"Inception","author":"Christopher Nolan","duration":148}
```

Tam kitap güncelleme — `PUT /api/items/1`:

```json
{"title":"The Hobbit (revised)","author":"J.R.R. Tolkien","page_count":320}
```

Tam DVD güncelleme — `PUT /api/items/2`:

```json
{"title":"Inception","author":"Christopher Nolan","duration":150}
```

Kısmi güncelleme — `PATCH /api/items/1`:

```json
{"title":"Updated title"}
```

Bu son gövde PATCH için geçerlidir; PUT için eksik alan hatası verir. Boş PATCH reddedilir. Güncelleme ile `id`, `type`, `is_available` değiştirilemez. Hatalı güncelleme hiçbir alanı değiştirmez. Başarılı PUT/PATCH, HTTP 200 ile güncel öğenin sözlüğünü döndürür.

Checkout/iade istekleri gövde gerektirmez. Örneğin `POST /api/items/2/checkout`, HTTP 200:

```json
{"message":"Successful checkout. Handle with care: Do not scratch the disc.","item":{"id":2,"type":"dvd","title":"Inception","author":"Christopher Nolan","is_available":false,"duration":148}}
```

Başarılı iadenin mesajı `Successful return` olur ve öğede `is_available: true` döner. Zaten ödünçteki öğeyi tekrar ödünç alma, müsait öğeyi iade etme ve ödünçteki öğeyi silme HTTP 409 döndürür.

Hata yanıtları `{"error":"açıklama"}` biçimindedir. Örneğin bulunamayan ID için HTTP 404:

```json
{"error":"Item not found: 999"}
```

Geçersiz alan/gövde, bozuk JSON ve yanlış Content-Type HTTP 400 döndürür; HTML hata sayfası döndürülmez. Başarılı DELETE HTTP 204 döndürür ve JSON dahil hiçbir yanıt gövdesi içermez.

## PowerShell ile istek

Sunucu çalışırken ayrı bir PowerShell penceresinde:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/items?available=true&type=book'

$body = @{ type = 'dvd'; title = 'Spirited Away'; author = 'Hayao Miyazaki'; duration = 125 } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/items' -Method Post -ContentType 'application/json' -Body $body
```

## Testler ve konsol gösterimi

`Week4/library` içinden:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe main.py
```

Testler model kurallarını ve API'nin başarı/hata sözleşmelerini kontrol eder. Her API testi kendi koleksiyonunu kullanır. `main.py` önceki konsol gösterimini korur. İstemler ve çalışma notları `PROMPTS.md` içindedir.

Node.js varsa arayüzün istek/durum akışı testleri ayrıca çalıştırılabilir:

```powershell
node --check static/script.js
node --test test_script.js
```

Bu testler taklit DOM ve API yanıtları kullanır; gerçek tarayıcı kontrolü değildir. Son kontrolde 26 Python testi ve 9 JavaScript testi geçti; ana sayfa ve statik dosyaların sunulması doğrulandı.

Gerçek tarayıcı kontrol aracı bulunmadığından görsel doğrulama yapılmadı. Manuel olarak masaüstü/dar ekran düzenini, çok uzun metinleri, klavye odağını ve formun küçük ekranda kullanımını kontrol edin. Ayrıca ekleme/düzenleme, filtreler, checkout/iade, ödünçteki öğeyi silerken 409 mesajı ve sunucu kapalıyken ağ hatasını deneyin.
