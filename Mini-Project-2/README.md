# EE471 Mini Project 2 — Metin, mikrofon ve sesli yanıtlarla Library App

Mevcut Library uygulamasına İngilizce metin komutu paneli, Azure STT ile mikrofon girişi ve isteğe bağlı Azure TTS yanıtları eklendi. Tam transkript aynı `runCommandText` akışını, Flask API'sini ve tek `LibraryCollection` modelini kullanır. Ortak İngilizce `responseText` hem ekranda görünür hem seslendirme katmanına gider. **Spoken responses başlangıçta kapalıdır; sayfa açılırken TTS isteği gönderilmez.**

## Güncel doğrulama durumu — 2026-11-03

**Kullanıcının manuel bildirimi:** Kullanıcı, DVD parser düzeltmesini gerçek mikrofonla yeniden denediğini ve çalıştığını bildirdi. İlgili hata örneği `Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.` transkriptiydi. Ayrıca İngilizce TTS yanıtlarının hoparlörden doğru duyulduğunu ve önceki metin komutlarının çalıştığını bildirdi. Bunlar kullanıcıya aittir; asistanın gerçekleştirdiği gerçek mikrofon/Azure testleri değildir. Tüm endpoint seslerinin veya ses hata/iptal senaryolarının ayrı ayrı doğrulandığı sonucu çıkarılmadı. Aşağıdaki yeni karma ayırıcı düzeltmesi henüz kullanıcı tarafından yeniden doğrulanmadı.

**Otomatik/mock sonuçlar:** Karma ayırıcı düzeltmesinden sonra **51 Python / 87 Node.js testi** ve **29 yerel Flask/headless metin paneli kontrolü** geçti. İki yeni tam transkript doğru gövdeyle birer POST gönderdi; saklanan alanlar GET ile doğrulandı. Mikrofon/TTS istekleri bu metin kontrolünde engellidir. Headless kontrolün gerçek sayfa/Flask kullanması, mock SDK/medya kontrollerinin gerçek sesli doğrulama olduğu anlamına gelmez. Önceki aşamalardaki test sayıları ve o aşamada bekleyen doğrulamalar aşağıda tarihsel kayıt olarak korunur.

**2026-11-02 belge ve Git kontrolü (tarihsel kayıt):** README/PROMPTS güncellendi. Ek whitespace kontrolünde bulunan `speech_service.py` sonundaki fazladan boş satır kaldırıldı; uygulama davranışı değiştirilmedi. Python dosyasındaki bu biçim temizliği sonrası **51 Python testi yeniden geçti**; JavaScript değişmediği için önceki **81 Node.js** sonucu korunup testler tekrarlanmadı. Kurulum komutları, boş anahtarlı `.env.example`, port 5002 ve komut etiketleri mevcut kodla karşılaştırıldı. Gerçek `.env`, `.venv`, `__pycache__`, `.test-deps` ve geçici ses yolları Git dışında; `.env.example` izlenebilir. PROMPTS geliştirme istemlerini ve doğrulanmış hata/düzeltme geçmişini içerir; eksik geçmiş eklenmedi. O kontrol sırasında proje henüz untracked olduğundan normal/staged `git diff --check` yanında, Git'e eklemeden 32 izlenebilir dosya `--no-index --check` ile de kontrol edildi; son kontrolde whitespace sorunu kalmadı. Stage/commit kullanıcıya bırakıldı.

## Aşama 4 — Azure TTS ile komut yanıtları

Command panelinde **Spoken responses** kutusunu açıkça etkinleştirin, sonra bir metin veya mikrofon komutu çalıştırın. Başarı yalnızca gerçek Library API yanıtından sonra bildirilir. **Play response** yalnızca son yanıtın sesini yeniden ister/oynatır; komutu veya mutasyonu yeniden çalıştırmaz. **Stop speech**, sesi kapatma ve sayfadan ayrılma bekleyen/oynayan sesleri iptal eder; eski TTS yanıtları sonradan oynatılmaz. Son yanıt metni ses kapalıyken de görünürdür. Kontroller Library busy durumunda kullanılabilir; mikrofon sırasında Play response devre dışıdır.

Tarayıcı asenkron `audio.play()` çağrısını reddederse ayrı ses hatası görünür. **Play response** düğmesine doğrudan basın; gerekirse site ses/oynatma izinlerini kontrol edin. Sentez veya oynatma hatası başarılı Library sonucunu değiştirmez. Aynı komutu tekrar göndermek ses hatasından kurtulma yöntemi değildir.

### Veri akışı ve sınırlar

- `runCommandText` → mevcut parser/`executeLibraryCommand` → gerçek API sonucu → ortak `responseText` (+ varsa ayrı yenileme uyarısı) → `spoken-responses.mjs` → göreli `/api/tts` → tarayıcı Audio. İkinci Library iş mantığı/isteği yoktur. Elle form/kart kullanımı korunur; otomatik sesli yanıt Command metin/mikrofon akışına aittir.
- CREATE gerçek tür/başlık/atanmış ID; GET temel alanlar/durum; LIST gerçek adet ve en fazla 5 ID/başlık özeti (kart sınırı 100, her kısa metin 60 karakter); PUT/PATCH tamamlanan ID; DELETE boş 204 yanıtından sonra ID; checkout/return gerçek öğe ve DVD bakım uyarısını mevcut runner üretir. Uzun başlık/yazar için önceki kısa özet politikası sürer. Boş liste, parser ve HTTP 400/404/409/ağ belirsizliği açıklamaları da aynı yanıt yolunu kullanır.
- Başarılı mutasyondan sonra liste yenilenememesi ayrı uyarıdır; ses, başarı ve uyarıyı tek bildirimde okur. Aynı komutla yalnızca yenileme tekrarlandığında önceki başarı yeniden okunmaz/mutasyon tekrarlanmaz. Belirsiz ağ sonucunda işlem uygulanmadı iddiası veya otomatik tekrar yoktur.
- STT sessizliği, servis/izin/timeout hataları, komut yoluna ulaşmadığında mikrofonun `onFailure` bildirimiyle aynı ses katmanına gider; ham SDK ayrıntısı okunmaz. Mikrofon başlatılmadan oynayan/bekleyen sesler durur; mikrofon oturumu (tanıma/komut dahil) boyunca TTS başlamaz. Başarılı güncel sesli komut yanıtı mikrofon kaynakları bırakılınca sıraya alınır. İptal edilmiş/eski transkript ses veya mutasyon başlatmaz.
- En fazla **3 ses işi** (aktif dahil), **tek TTS HTTP isteği ve tek oynatma** sırayla yürür; dolu kuyrukta son metin ekranda kalır, Play response kullanılabilir. TTS hazırlama isteği 40 saniye, oynatma 180 saniye ile sınırlıdır; WAV yanıtı 16 MiB üzerindeyse oynatılmaz. Native tarayıcı zamanlayıcıları global bağlamı koruyan sarmalayıcılarla çağrılır. Object URL, medya olay dinleyicileri, timer ve oynatma kaynakları tamamlanma/iptalde temizlenir.
- Backend STT ile aynı işlem kilidini ve `SPEECH_KEY`/`SPEECH_REGION` ayarlarını kullanır. TTS sonuç bekleme 30 saniye, SDK stop bekleme 5 saniyeyle sınırlıdır; finally kilidi bırakır. Sentez istek başına bağımsızdır. Hata/timeout veya temizlik başarısızlığında ses başarısı dönmez; asıl hatayı temizlik hatası maskelemez. HTTP iptali başlamış sunucu sentezinin anında durduğunu garanti etmez; devam eden sunucu işi sırasında STT/TTS busy hatası alınırsa yeni bir Library mutasyonu otomatik denenmez.

### TTS endpoint sözleşmesi

`POST /api/tts`, JSON `{"text":"Successfully deleted item 4."}` kabul eder. Yalnızca `text` alanı vardır; boş olmayan string, en fazla **2000 karakter**. İstek gövdesi üst sınırı 16 KiB. Geçersiz JSON/tür/boş/uzun metin 400, büyük HTTP gövdesi 413, eksik Azure ayarı 503, servis/iptal/timeout/busy/temizlik hatası 502 ve güvenli JSON `error` döndürür. Başarı `audio/wav`, `Cache-Control: no-store` yanıtıdır.

SDK 1.53.0 `SpeechSynthesizer(audio_config=None)`, `en-US-JennyNeural` ve açık `Riff16Khz16BitMonoPcm` kullanılır; ses bellekte üretilir. `speak_text_async` düz metin sentezler: başlık/yazar SSML değildir. Sunucu hoparlörü, ortak ses dosyası, browser speechSynthesis veya yeni Azure servisi/anahtarı kullanılmaz. Ayarlar yalnızca ses isteğinde uygulama klasöründeki açık dotenv yolundan yüklenir; ayarsızken Library sayfası/API çalışır. Mevcut requirements yeterlidir; yeni bağımlılık eklenmedi.

### Aşama 4 otomatik ve manuel doğrulama

**51 Python ve 77 Node.js testi geçti.** SDK 1.53.0 SpeechSynthesizer/SpeechSynthesisResult spec mock'larıyla giriş sınırı, düz metin/WAV/format, hoparlörün kapalı olması, ayarsız kullanım, servis/iptal/timeout/cleanup ve kilit tekrar kullanımı kontrol edilir. Frontend testleri gerçek UI kaynaklarını mock DOM/medya/ağ ile çalıştırır; sekiz işlem ve hataların ses yoluna ulaşması, sonuçtan önce ses olmaması, 204/DVD uyarısı, tek mutasyon, replay, kuyruk/sıra/iptal, mikrofon çakışması, geç yanıt, URL/olay temizliği ve play reddi kapsanır.

Önceki gerçek Flask/headless Chrome **23 metin paneli kontrolü** ve mock STT ile **8 işlem + parser hatası** yeniden geçti. Yeni gerçek sayfa/Flask sesli yanıt kontrolünde **20 adım**, 19 mock TTS çağrısı, 2 mock STT çağrısı, 18 mock play çağrısı, 18 URL temizliği, 2 kapatılmış mock mikrofon track'i ve sıfır JavaScript hatası görüldü. Audio/mikrofon/SDK tamamen mock'tur; gerçek ses duyulması veya Azure başarısı değildir. Gerçek .env okunmadı; mikrofon/Azure/hoparlör kullanılmadı.

PowerShell test komutları (`Mini-Project-2` içinden):

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -p "test_*.py"
node --test test_commands.mjs test_script.js test_voice_input.mjs test_spoken_responses.mjs
.\.venv\Scripts\python.exe -B check_commands_browser.py
.\.venv\Scripts\python.exe -B check_voice_browser.py
.\.venv\Scripts\python.exe -B check_spoken_browser.py
```

Headless kontroller kurulu Chrome ister; kendi test koleksiyonlarını/geçici port ve `tmp/` profillerini kullanır. Normal port **5002** korunur. `check_spoken_browser.py` gerçek olay bağlantılarını kullanır, SDK/medyayı mock eder ve ses çıkışını ayrıca mute eder.

**Kullanıcı İngilizce TTS yanıtlarını hoparlörden doğru duyduğunu ayrıca bildirdi.** DVD parser düzeltmesinin gerçek mikrofon denemesi de yukarıda ayrı kaydedildi. Bu bildirimler tüm endpoint seslerinin, genel tolerans değişikliklerinin veya aşağıdaki hata/iptal kontrollerinin ayrı ayrı doğrulanması sayılmaz. Daha sonra yerelde:

1. Sayfa sessiz açılmalı; kutuyu açıp CREATE/GET/LIST/PUT/PATCH/checkout/return/DELETE yanıtlarını ve gerçek atanan ID'yi dinleyin. DVD uyarısı, boş liste, 404/409 ve parser hatasını deneyin.
2. Oynatma reddi/TTS hatasında Library sonucunun korunduğunu, Play response ile yalnızca sesin tekrarlandığını kontrol edin. Ağ belirsizliğinde koleksiyonu kontrol etmeden mutasyonu tekrarlamayın.
3. Ses sırasında mikrofonu başlatın: eski ses durmalı; kayıt/tanıma sırasında ses başlamamalı; güncel sonuç kayıt kaynakları kapandıktan sonra okunmalı. Sessizlik ve servis hatasını ayrıca deneyin.
4. Ses hazırlanırken/oynarken kapatma, Stop speech ve sayfadan ayrılma; sonra yeniden etkinleştirme ve mikrofon iptal/geç yanıt durumlarını kontrol edin. Bu ayrı kontrollerin gerçek donanım/Azure ile sonuçları kullanıcı tarafından ayrıca bildirilmedi; asistan gerçek donanım/Azure kullanmadı.

Başlangıç kaynağı: `main` branch'indeki `Week4/library`, commit `fc6b814d0e37f6bd79a83e4f54ab9966c4acac80`. İlk aşamada kaynaklar değiştirilmeden kopyalandı; ikinci aşamada komut modülleri ve arayüz bağlantıları eklendi. Model ve API endpoint gövdeleri korunur. Eski README/PROMPTS geçmişi yeni projenin geliştirme geçmişi olarak aktarılmadı. Yerel ortamlar, gerçek `.env`, önbellekler ve geçici/üretilmiş dosyalar kopyalanmadı.

## PowerShell kurulumu ve çalıştırma

EE471 repo kökünden:

```powershell
cd .\Mini-Project-2
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe app.py
```

Mevcut sanal ortam varsa oluşturma adımını atlayın. Etkinleştirme gerekmez. `.env` zaten varsa kopyalama yapılmaz. `.env` içine kendi Azure Speech kaynağınızın anahtarını `SPEECH_KEY`, bölgesini `SPEECH_REGION` olarak yerelde girin; anahtarı paylaşmayın. Örnek anahtar boştur, `eastus` örnek bölgedir; gerçek kaynağınızla eşleşmelidir.

<http://127.0.0.1:5002> adresini açın; durdurmak için `Ctrl+C` kullanın. Geliştirme sunucusu doğrudan çalıştırmada `127.0.0.1:5002` kullanır. Aynı portta başka uygulama çalışıyorsa önce onu durdurun. Import sunucuyu başlatmaz. Frontend göreli API URL'leri kullanır. Bağımlılıklar Flask, python-dotenv ve Speech SDK 1.53.0'dır; frontend derleme adımı yoktur. Mikrofon için localhost'ta güncel AudioWorklet destekli Chrome/Edge kullanın.

Sayfa, manuel Library işlemleri ve metin komutları Azure ayarları olmadan çalışır. Dotenv yalnızca ses isteğinde, `speech_service.py` dosyasının bulunduğu klasördeki açık `.env` yoluyla yüklenir; mevcut ortam değişkenleri önceliklidir. Eksik ayar hatası yalnızca ses isteğinde verilir. Geliştirme sırasında gerçek `.env` oluşturulmadı, okunmadı veya kopyalanmadı. `.gitignore` `.env`, ortam/önbellek/geçici sesleri dışlar; `.env.example` izlenebilir.

## Dosyalar ve mevcut davranış

```text
Mini-Project-2/
  .gitignore
  README.md
  PROMPTS.md
  app.py
  custom_classes.py
  main.py
  requirements.txt
  speech_service.py
  .env.example
  templates/index.html
  static/script.js
  static/style.css
  static/command-parser.mjs
  static/command-runner.mjs
  static/spoken-responses.mjs
  static/voice-input.mjs
  static/voice-worklet.mjs
  static/voice-audio.mjs
  static/pcm-resampler.mjs
  test_app.py
  test_custom_classes.py
  test_script.js
  test_commands.mjs
  test_voice.py
  test_tts.py
  test_voice_input.mjs
  test_spoken_responses.mjs
  speech-test-helpers.mjs
  voice-test-helpers.mjs
  check_commands_browser.py
  check_voice_browser.py
  check_spoken_browser.py
```

`custom_classes.py` iş kurallarını, `app.py` HTTP/JSON adaptörünü barındırır. Uygulamada tek bir `LibraryCollection` vardır. Başlangıçta The Hobbit (ID 1), Inception (ID 2) ve 1984 (ID 3) eklenir. Hepsi başlangıçta müsaittir. Veriler bellektedir; yeniden başlatmada bu başlangıç verileri yüklenir. ID'ler bir koleksiyonun yaşamı boyunca artar; silinen ID tekrar kullanılmaz. `main.py` bağımsız konsol örneğidir; web uygulamasına ikinci koleksiyon eklemez.

Mevcut liste/form düzeni, All/Book/DVD filtresi, ekleme, PATCH ile düzenleme, checkout/iade ve silme korunur. Available only kutusu, aynı müsaitlik filtresine `false` değerini de verebilmek için erişilebilir **All / Available / Checked out** seçimine dönüştürüldü. Düzenleme modunda tür alanı kilitlenir. Ödünçteki öğede silme düğmesi tıklanabilir kalır; reddetme kuralı sunucudadır. Kullanıcı metinleri `textContent` ile gösterilir. İstek sırasında kontroller kilitlenip finally ile açılır; hata sonrası form girdileri korunur.

Başarılı değişiklikten sonra mevcut filtrelerle liste yenilenir. Yeni filtre isteğinde eski liste kaldırılır. Oluşturma başarılı olup liste yenileme başarısız olursa yeni ID form durumunda korunur; yeniden kaydetme ikinci POST yerine mevcut öğeye PATCH gönderir. DELETE 204 yanıtı JSON olarak okunmaz.

## Gerçek koddan çıkarılan model sözleşmesi

Ortak yanıt alanları: `id`, `type`, `title`, `author`, `is_available`. Book ayrıca `page_count`, DVD ayrıca `duration` döndürür.

| Alan | Oluşturma ve düzenleme kuralı |
| --- | --- |
| `title` | Boş olmayan string; yalnızca boşluktan oluşamaz. Geçerli metin olduğu gibi saklanır. |
| `author` | Aynı metin kuralı; DVD yönetmeni/üreticisi de bu alanla gönderilir, `director` alanı yoktur. |
| `page_count` | Yalnızca Book; pozitif integer. Boolean, sıfır/negatif, kesirli sayı ve sayısal string reddedilir. |
| `duration` | Yalnızca DVD; dakika cinsinden pozitif integer; aynı sayı kuralları geçerlidir. |
| `type` | POST'ta tam olarak `book` veya `dvd`; PUT/PATCH ile değiştirilemez. |
| `id` | Koleksiyon atar; API üzerinden gönderilemez veya düzenlenemez. |
| `is_available` | POST'ta gönderilemez; yeni öğe true başlar. PUT/PATCH ile düzenlenemez; checkout/return kullanılır. |

Modelin Python kurucuları boolean `is_available` kabul edebilir; bu, API'nin oluşturma/güncelleme gövdesinde alanı kabul ettiği anlamına gelmez.

**POST tam alan kümesi:** Book için `type,title,author,page_count`; DVD için `type,title,author,duration`. Eksik veya ek alanlar, bilinmeyen alan ve diğer türe ait alan reddedilir.

**PUT tam alan kümesi:** Mevcut Book için tam olarak `title,author,page_count`; DVD için tam olarak `title,author,duration`. Alan atlamak, `type`, `id`, `is_available` veya başka alan eklemek 400'dür. PUT mevcut ID'yi, türü ve müsaitlik durumunu korur; öğe yoksa oluşturmaz, 404 verir.

**PATCH:** İlgili türün düzenlenebilir alanlarından en az biri gerekir. Boş nesne ve ek/yasak alanlar reddedilir. Bütün alanlar önce doğrulanır; tek bir geçersiz alan varsa diğer alanlar da değişmez. PUT da aynı atomik güncelleme kuralını kullanır. Güncelleme için öğenin müsait olması şartı eklenmemiştir; mevcut kural korunur.

## API sözleşmesi

POST/PUT/PATCH gövdeleri `Content-Type: application/json` ile geçerli JSON nesnesi olmalıdır. `GET /` HTML döndürür. Aşağıdaki API başarıları DELETE hariç JSON'dur. Beklenen hata yanıtı `{"error":"açıklama"}` biçimindedir.

| Metot ve yol | Başarı | Beklenen hatalar |
| --- | --- | --- |
| `POST /api/items` | 201 + oluşturulan öğe sözlüğü | 400 geçersiz gövde/alan/değer |
| `GET /api/items` | 200 + öğe dizisi; eşleşme yoksa `[]` | 400 geçersiz filtre |
| `GET /api/items/<id>` | 200 + tek öğe | 404 bulunamadı |
| `PUT /api/items/<id>` | 200 + güncel öğe | 400 geçersiz tam temsil, 404 bulunamadı |
| `PATCH /api/items/<id>` | 200 + güncel öğe | 400 geçersiz/boş kısmi temsil, 404 bulunamadı |
| `DELETE /api/items/<id>` | **204 + tamamen boş gövde** | 404 bulunamadı, 409 ödünçte |
| `POST /api/items/<id>/checkout` | 200 + `message` ve güncel `item` | 404 bulunamadı, 409 zaten ödünçte |
| `POST /api/items/<id>/return` | 200 + `message` ve güncel `item` | 404 bulunamadı, 409 zaten müsait |

Filtreler: `available=true` / `available=false`, `type=book` / `type=dvd`. Parametre yoksa o filtre uygulanmaz. İkisi AND olarak birlikte uygulanır: `/api/items?available=false&type=dvd`. Değerler büyük/küçük harfe duyarlıdır; boş değer, `True`, `1`, `BOOK` gibi geçersiz değerler 400 döndürür.

Checkout ve return gövde gerektirmez. Book checkout mesajı `Successful checkout`; DVD için `Successful checkout. Handle with care: Do not scratch the disc.` olur. İade mesajı `Successful return`dür. Checkout `is_available=false`, return true yapar. Uygun olmayan geçiş değişiklik yapmadan 409 verir; ödünçteki öğe silinemez.

Geçersiz JSON, nesne olmayan gövde ve yanlış/eksik JSON Content-Type 400'dür. Bilinmeyen yol veya integer olmayan ID yolu 404, desteklenmeyen metot 405 döndürür; HTTP hata işleyicisi JSON hata biçimini ve Allow gibi başlıkları korur. Eksik ID ile bozuk gövde birlikte gönderilirse gövde çözümleme hatası önce gelebilir; model aramasına ulaşan geçerli PUT/PATCH isteği için bulunmayan ID 404'tür.

### Gövde ve yanıt örnekleri

Book oluşturma:

```json
{"type":"book","title":"The Catcher in the Rye","author":"J.D. Salinger","page_count":220}
```

Başarı 201; bu yeni süreçte ilk yeni öğe için örnek:

```json
{"id":4,"type":"book","title":"The Catcher in the Rye","author":"J.D. Salinger","is_available":true,"page_count":220}
```

DVD oluşturma:

```json
{"type":"dvd","title":"Spirited Away","author":"Hayao Miyazaki","duration":125}
```

Book için tam PUT ve kısmi PATCH örnekleri:

```json
{"title":"Updated title","author":"Updated author","page_count":225}
```

```json
{"page_count":230}
```

İkinci gövde PATCH için geçerli, PUT için eksiktir. Başarılı PUT/PATCH tüm güncel öğeyi döndürür.

DVD 2 için checkout yanıtı:

```json
{"message":"Successful checkout. Handle with care: Do not scratch the disc.","item":{"id":2,"type":"dvd","title":"Inception","author":"Christopher Nolan","is_available":false,"duration":148}}
```

Bulunamayan ID örneği: HTTP 404, `{"error":"Item not found: 999"}`. Ödünçteki öğeyi silme: HTTP 409, `{"error":"Cannot remove a checked-out item."}`. Başarılı DELETE'in gövdesi `null`, `{}` veya bir başarı mesajı değildir; hiç gövde yoktur.

Sunucu açıkken ayrı PowerShell penceresinde:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5002/api/items?available=true&type=book'
$body = @{ type = 'book'; title = 'New book'; author = 'Writer'; page_count = 220 } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5002/api/items' -Method Post -ContentType 'application/json' -Body $body
```

## Başlangıç incelemesinde belirlenen ses bağlantı noktaları

Sesli komutlar, niyet/ID/alanlar doğrulandıktan sonra **aynı HTTP endpoint'lerini** çağırmalıdır. `app.py` içindeki tek `collection` ve `custom_classes.py` içindeki kurallar korunmalıdır. İkinci koleksiyon, kopya bir veri listesi veya ayrı checkout/güncelleme mantığı oluşturulmamalıdır.

| Mevcut yer | Sonraki aşamada yeniden kullanılabilecek nokta |
| --- | --- |
| `static/script.js: apiRequest` | Aynı API üzerinden POST/GET/PUT/PATCH/DELETE gönderme; JSON hataları ve boş 204 çözümlemesini koruma. |
| `runAction`, `setBusy`, `showMessage` | Sesli işlemde de mevcut tek işlem durumu, hata/başarı mesajı ve finally sonrası kontrol açma. |
| `refreshItems`, `renderItems` | API'den gelen listeyi mevcut filtrelerle yenileme; ayrı istemci koleksiyonu oluşturmama. |
| Form submit ve kart dinleyicileri | POST oluşturma, PATCH düzenleme, DELETE, checkout/return isteklerinin mevcut örnekleri. Ses adaptörü aynı request/response akışını kullanabilir. |
| `GET /api/items/<id>` ve `PUT /api/items/<id>` | API'de hazırdır; mevcut form PUT yerine PATCH kullanır. Ses adaptörü bu iki endpoint'i de doğrudan `apiRequest` üzerinden kullanabilir. |

Bu bağlantıların metin komutu uygulaması aşağıdadır. Oluşturmada ID gerçek yanıttan alınır; `pages`, `page_count`a çevrilir. PUT tam şemayı, PATCH kısmi şemayı kullanır. Müsaitlik için checkout/return çağrılır. API'ye eşanlamlı alanlar eklenmedi; mikrofon henüz bağlanmadı.

## İlk aşamanın doğrulama kaydı

2026-11-02 tarihinde **26 Python testi (16 API + 10 model) ve 9 Node.js testi geçti**. Bunlar yeni klasörde yeniden çalıştırıldı; Week4'teki önceki sonuçlar yeni sonuç olarak aktarılmadı. Python 3.13 ve proje dışındaki geçici dizinde önceden kurulu Flask bağımlılıkları kullanıldı; proje içine ortam/paket kopyalanmadı.

Kapsam: model alanları, atomik PUT/PATCH, ID ömrü, filtreler, 201/200 başarıları, 400/404/409 ve JSON yönlendirme hataları, DELETE 204 boş gövde, checkout/iade mesajları, ana sayfa/statik dosyaların sunulması ve import sırasında sunucunun başlamaması. Node testleri taklit DOM/API ile form, filtre, ağ hatası sonrası kullanım, 204 çözümlemesi ve başarılı POST sonrası liste hatasında tekrar POST yapılmamasını kontrol eder. JavaScript sözdizimi kontrolü de geçti.

Mini-Project-2 içinden tekrar çalıştırma:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
node --check static/script.js
node --test test_commands.mjs test_script.js test_voice_input.mjs
.\.venv\Scripts\python.exe main.py
```

**Gerçek tarayıcı/görsel, mikrofon veya Azure testi yapılmadı.** Arayüz davranışı kaynak eşitliği ve taklit testlerle korundu; gerçek görsel deneme iddia edilmez. Sonraki manuel kontrol için ekleme/düzenleme, birleşik filtreler, checkout/iade, ödünçte silme 409 ve dar ekran düzeni denenebilir. İstem ve bu aşamanın çalışma kaydı `PROMPTS.md` içindedir.

## Aşama 2 — İngilizce metin komutları

Sayfanın altındaki **Command** paneline tek komut yazıp **Run command** düğmesine basın. Anlaşılan işlem özeti, gerçek sonuç ve hata/yenileme uyarısı ayrı gösterilir. Başarı, API yanıtı gelmeden gösterilmez. GET sonucu ID, tür, başlık, yazar, sayfa/süre ve durum alanlarını gösterir. LIST mevcut kart düzenini ve filtre kontrollerini kullanır. Mutasyon sonrası mevcut tür/durum filtresi korunur; yeni öğenin o filtrede görünmemesi işlemin başarısız olduğu anlamına gelmez.

### Desteklenen komutlar

```text
Create item, type book, title The Hobbit, author Tolkien, pages 310
Create item, type DVD, title Inception, author Christopher Nolan, duration 148

List items
List books
List DVDs
List available items
List available books
List available DVDs
List checked out items
List checked out books
List checked out DVDs

Get item 3
Replace item 3, title The Hobbit Revised, author Tolkien, pages 320
Replace item 2, title Inception Revised, author Christopher Nolan, duration 150
Update item 3, pages 330
Update item 3, title The Hobbit Updated
Update item 2, title Inception Updated, duration 151
Delete item 3
Check out item 3
Checkout item 3
Return item 3
```

ID'ler mevcut koleksiyona göre seçilir; bu örnekler otomatik çalıştırılan bir işlem dizisi değildir. Ödünçte olan öğeyi silmek için önce iade gerekir.

### Gramer ve belirsizlik sınırları

#### Karma ayırıcı düzeltmesi — 2026-11-03

Şu iki gerçek transkript değişiklik öncesinde ayrı ayrı yeniden üretildi ve ikisi de `Create requires type book or DVD.` hatasını verdi:

```text
Create item type book titled Hobbit Author Tolkien, pages 500.
Create Item Type Book Title Hobbit Author Tolkien, Pages 500.
```

Tek virgülün açtığı global `commaMode`, önceki type/title/author sınırlarını da devre dışı bırakıyordu. Böylece type ilk örnekte `book titled hobbit author tolkien`, ikincide `book title hobbit author tolkien` olarak okunuyordu. Bu, `book` türünün geçersiz olması değildi. `titled` ayrıca tanınmayan bir eş anlamlıydı; yalnızca onu eklemek ikinci örneğin sorununu çözmezdi.

Global ayırıcı modu kaldırıldı. Artık açık alan sınırları yerel değerlendirilir; komutun tamamının virgüllü veya virgülsüz olması gerekmez. `title` ve `titled` aynı `title` alanına bağlanır. İki tam örnek de `{"type":"book","title":"Hobbit","author":"Tolkien","page_count":500}` üretir. Virgülle ayrı bölüm hâline getirilmiş başlık/yazar ve tırnaklı değer içindeki etiket sözcükleri bölünmez; belirsizlikte alternatif bir mutasyon tahmin edilmez. Ayrıntılı yerel gramer aşağıdadır. Bu düzeltme parser, ilgili testler ve belgelerle sınırlıdır; STT/TTS/model/API değiştirilmedi. Gerçek mikrofon/Azure ile yeniden deneme bekliyor.

#### Sayısal alan etiketinden sonraki nokta — gerçek transkript düzeltmesi

Kullanıcının gerçek Azure transkripti `Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.` düzeltme öncesi parser'da yeniden üretildi ve aynı eksik CREATE alanları hatası alındı. `Duration.` tek word token'ıydı; etiket olarak tanınmadığından yazar metnine ekleniyor ve `duration` alanı oluşmuyordu. Aynı metnin `duration: 148 minutes` ve `duration 148 minutes` biçimleri zaten doğru ayrışıyordu. `page.`, `page count.` ve `duration in minutes.` denemeleri de noktanın etiket/sayı sınırında işlenmediğini gösterdi.

Artık sayısal etiketin **son sözcüğüne bağlı tek nokta**, etikete ait yapısal ayraçtır: `duration. 148 minutes`, `duration: 148 minutes`, `duration 148 minutes` aynı `duration: 148` değerini üretir. `duration in minutes. 148 minutes`, `page. 310`, `pages. three hundred and ten` ve `page count. 310` de desteklenir. Etiket ile değer arasında ayrı bir nokta (`pages . 310`) kabul edilir. Etiket/değer ayrı token olmalıdır; nokta çok kelimeli etiketin ortasındaki sözcükleri birleştirmek veya bozuk sayıları onarmak için kullanılmaz.

Genel nokta silme yapılmaz: `J.D. Salinger`, sayısal başlıklar ve tırnaklı literal noktalar korunur. Virgülle ayrılmış metin değerlerinde `Duration. Study` gibi metin aynen kalır. Virgülsüz başlık/yazar içinde sayısal etiketle çakışan literal sözcük varsa tırnak kullanın; parser tahmin etmez. Eksik, negatif, sıfır, kesirli, bozuk gruplu veya çözülemeyen sayılar; yinelenen alanlar ve belirsiz komutlar ağ isteğinden önce reddedilir. Çift nokta gibi ek ayraçlar sayının içinden silinmez.

**Otomatik doğrulama:** Bu düzeltmede 81 Node.js ve 51 Python testi geçti. Tam transkript ve ayraç eşdeğerleri Command formu/ortak runner üzerinden beklenen gövdeyle yalnızca bir POST gönderdi. Gerçek yerel Flask ve headless Chrome'da **25 panel kontrolü** geçti; üç tam CREATE regresyonunun her biri tek doğru POST ile kaydedildi ve GET ile doğrulandı. Yeni transkript bu üç örnekten biridir; JavaScript hatası görülmedi. Bu headless metin kontrolünde mikrofon/TTS istekleri engellidir ve Chrome mute çalışır. STT, model/API sözleşmesi ve seslendirme kodu değiştirilmedi.

**Sonradan gelen kullanıcı doğrulaması:** Kullanıcı son DVD parser düzeltmesini gerçek mikrofonla yeniden denediğini ve çalıştığını bildirdi. Bu, yalnızca bildirilen manuel denemedir; asistan tarafından yapılmış veya tüm varyantları kapsayan bir doğrulama değildir.

#### Genel tolerans kontrolü (2026-11-02)

| Madde | Durum | Kontrol edilen kapsam |
| --- | --- | --- |
| Büyük/küçük harf, fazla boşluk, satır sonu | uygulandı ve test edildi | Komut/etiket sözdizimi esnek; başlık/yazar içeriği korunur. |
| Alan sınırında virgül, nokta, noktalı virgül, iki nokta | uygulandı ve test edildi | Açık bölüm sınırları, etiket sonrası iki nokta, CREATE/PUT/PATCH örnekleri. |
| Komut sonu noktalama | uygulandı ve test edildi | `. ! ? ; :` ve bitişik diziler; tırnak içi korunur. Sonda virgül reddedilir. |
| Rakamlar ve İngilizce sayı kelimeleri | uygulandı ve test edildi | `three hundred and ten`, güvenli pozitif integer kontrolü. |
| Binlik gruplama / bozuk gruplama | uygulandı ve test edildi | Doğru üçlü virgül grupları kabul; bozuk/taşan değerler reddedilir. |
| duration / duration in minutes ve minute(s) | uygulandı ve test edildi | İki etiket, isteğe bağlı birim, hatalı birim/kesir/tekrar reddi. |
| Noktalı isimler ve sayısal başlıklar | uygulandı ve test edildi | `J.D. Salinger`, `1984`, `1,984`, tırnaklı literal noktalama. |
| Sekiz işlem için ortak parser | uygulandı ve test edildi | CREATE/LIST/GET/PUT/PATCH/DELETE/checkout/return; gerçek form bağlantısı ve mock HTTP yöntemi/yolu/gövdesi. |
| Literal ayırıcı veya alan sözcüğüyle çakışan virgülsüz metin | belgelenmiş belirsizlik | Tahmin edilmez; tırnak veya açık bölüm ayrımı gerekir. Bilinmeyen/eksik/tekrarlı alanlarda ağ isteği yoktur. |

Kontrolde noktalı virgül/iki nokta, gruplu rakamlar, dakika etiket/birimi ve bitişik son noktalama dizileri başlangıçta eksikti; genel tolerans düzeltmesinde eklendi. İlk kontrolde 63 Node.js ve 42 Python testi geçti. Aşağıdaki tam girdi takibinde **66 Node.js ve 42 Python testi geçti**; gerçek yerel Flask/headless Chrome ile **23 panel kontrolü** de tamamlandı. STT, Library model/API ve port 5002 değiştirilmedi.

#### İki tam manuel hata örneğinin takibi

Kullanıcı aşağıdaki iki metin komutunun sırasıyla bilinmeyen alan ve sayı çözümleme hatası verdiğini bildirdi:

```text
Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.
Create item, type DVD, title Inception, author Christopher Nolan, duration in minutes 148.
```

Bu takip çalışmasının başında, herhangi bir yeni parser değişikliği yapılmadan iki tam girdi ayrı ayrı denendi. Güncel diskteki parser ikisini de beklenen alanlarla kabul etti: ilkinde `{"type":"book","title":"Test Book","author":"Test Author","page_count":310}`, ikincisinde `{"type":"dvd","title":"Inception","author":"Christopher Nolan","duration":148}`. Dolayısıyla kullanıcının oturumundaki iki hatanın kesin nedeni yeniden üretilemedi; eski modül/önbellek veya yanlış sunucu kaynaklı olduğu doğrulanmış değildir. Mevcut kodda noktalı virgül bölüm sınırı ve etiket sonu iki nokta tüketilir; `duration in minutes` kısa etiketten önce üç tam sözcük olarak tüketilir. Sayı çözümleyicisine yalnızca değer gider; `three hundred and ten` 310 olur, etiket ve birim içeren çıplak sayı girdisi reddedilir.

Ayrıca bağımsız bir sınır hatası yeniden üretildi: `Update item 2 duration "in" "minutes" 148` yanlışlıkla süre etiketi sayılıyordu. Çok kelimeli etiketler artık yalnızca tırnaksız, tam word token'larıyla eşleşir; bu geçersiz biçim ağ isteğinden önce reddedilir. Bu bulgu, kullanıcının iki hatasının nedeni olarak sunulmaz.

Her iki tam metin parser ve gerçek form/ortak runner regresyonlarına eklendi. `check_commands_browser.py` gerçek sayfa/ES modülleri, yerel Flask ve izole gerçek Library koleksiyonunda iki metni Command panelinden gönderir. **Her örnek için doğru gövdeyle tek POST**, ardından gerçek GET ile saklanan alanlar doğrulandı. Önceki panel kontrolleriyle birlikte **23 kontrol geçti, sıfır JavaScript hatası** görüldü; hatalı tırnaklı süre etiketi de mutasyon yapmadan reddedildi. Bu headless metin kontrolü mikrofon, STT, Azure veya ses oynatma kullanmaz; kullanıcının açık tarayıcı oturumunun yeniden doğrulandığı anlamına gelmez.

Yerelde sorun sürerse uygulamanın `http://127.0.0.1:5002` adresinde güncel Mini-Project-2 klasöründen çalıştığını kontrol edip sayfayı tam yenileyerek iki metni tekrar deneyin. Network panelindeki `command-parser.mjs` yanıtının güncel kodu içerdiğini ve hata halinde POST gönderilmediğini kontrol edin. Bunlar neden ayırt etme adımlarıdır; önbellek hatası teşhisi değildir. Genel tolerans tablosundaki sekiz açık madde uygulandı ve test edildi; literal ayırıcı/etiket çakışmaları belgelenmiş belirsizlik olarak kalır. Gerçek mikrofon/Azure denemesi yapılmadı.

- Komut, etiket ve tür büyük/küçük harften etkilenmez; `DVD` ve `DVDs` ilgili örneklerde desteklenir. Sözdiziminde fazla boşluk, sekme ve satır sonları kabul edilir. Başlık/yazarın harfleri ve iç boşlukları korunur. Komut sonundaki bitişik `.`, `!`, `?`, `;`, `:` işaretleri veya dizileri (`?!`, `...`) ayrılabilir; tırnak içi noktalama korunur. Sonda virgül eksik sonraki alan sayılır ve reddedilir. Metni son noktalaması dahil tam korumak için çift tırnak kullanın.
- `type`, `title`/`titled`, `author`, `page`/`pages`/`page count`, `duration`/`duration in minutes` açık etiketlerdir. Eş anlamlılar aynı API alanına dönüşür; örneğin title ile titled veya page ile pages tekrar edilirse yinelenen alan hatasıdır. Alan sırası değişebilir ve aynı komutta virgül, açık etiket, nokta, noktalı virgül ve iki nokta birlikte kullanılabilir. Bir ayırıcı diğer bölümlerdeki sınırları kapatmaz.
- **Yerel metin bölümü:** Başlık/yazar etiketi, ayırıcıyla sınırlandırılmış bir bölümün başındaysa o bölümdeki tırnaksız değer sonraki ayırıcıya veya komut sonuna kadar korunur. `Create item type book, title The author of pages, author Test Author, pages 500` geçerlidir. `Update item 3, title X author Y` tek title alanını `X author Y` yapar; metin içindeki author yeni alan sayılmaz. Komutun ilk metin bölümü sağındaki virgülle de açıkça sınırlandırılabilir. Virgül/noktalı virgül/bölüm ayıran iki nokta aynı yerel kuralı kullanır.
- **Açık etiket akışı:** Type ve sayısal değerler sonraki açık etikette durur. Ayrı bir metin bölümü olarak korunmayan title/author değerleri de açık etiketlerle ayrılır; örneğin `Create item type book titled Hobbit author Tolkien, pages 500`. Literal etiket sözcüğü içeriyorsa değeri tırnaklayın. Tırnaklı title/author tek atomdur; ardından ayırıcı olmadan başka açık etiket gelebilir. `Create item type book title "The author of pages" author "Test Author", pages 500` geçerlidir. JSON string kaçışları desteklenir; literal virgül/nokta için de tırnak kullanılır.
- **Belirsizlik korunur:** `Update item 3 pages 500 title The author of books` gibi sınırlandırılmamış iki isteğe bağlı title/author yorumundan biri tahmin edilmez. `Create item type book title Hobbit, author Tolkien pages 500` örneğinde author bölümünün içindeki pages veri olabilir; parser eksik sayfa alanını tahminle ayırmaz. `author "Tolkien" pages 500` veya `author Tolkien, pages 500` ile yalnızca ilgili sınırı açıklaştırın. Komutun tamamına tek bir ayırıcı tarzı zorunlu değildir. Eksik/tekrarlı/geçersiz alanlarda API isteği gönderilmez.
- `id`, `is_available`, `page_count`, `director`, `publisher`, `isbn`, `year`, `available`, `status` bölüm başında alan etiketi olarak kullanılamaz. Virgülle sınırlandırılmış bir title/author değerinin içinde ise literal kelime olarak bulunabilirler. Virgülsüz biçimde bunlar da ayrılmış sınır sözcükleridir; literal kullanım için tırnak gerekir. API alan adı `page_count`, desteklenen komut etiketleri ise `page`, `pages` ve `page count`tur.
- Virgül sonrası bilinmeyen alan etiketi reddedilir. Değer içindeki sıradan kelimeler yeni alan varsayılmaz. Yinelenen bölüm etiketi, boş değer, ek komut ifadesi, kapanmayan tırnak veya tırnak sonrası artık metin reddedilir. Virgülsüz `title The Author author Tolkien` gibi çakışmayı `title "The Author" author Tolkien` olarak yazın.
- ID, pages ve duration pozitif güvenli integer olmalıdır (en fazla `9007199254740991`). Rakamlar ve İngilizce cardinal sayılar desteklenir: `item three`, `pages three hundred ten`, `three hundred and ten`, `twenty-one`, `one thousand and one`. Sayı ölçekleri quadrillion'a kadar azalan sırada olmalıdır. `one two` gibi rakam dizisi, negatif işaret/kelime, sıfır, ondalık, sayısal tırnaklı değer veya çözümlenemeyen sayı reddedilir.
- Sayı dönüşümü yalnızca ID/sayfa/süreye uygulanır. `title 1984` veya `title "1984"` başlığı aynı string olarak saklanır.
- Sayısal alanlarda doğru İngilizce binlik gruplama da kabul edilir: `1,000`, `12,345`, `1,234,567`. İlk grup 1–3 basamak ve sıfırdan farklı başlangıç, sonraki her grup tam üç basamak olmalıdır; grupların arasına boşluk konmaz. `1,00`, `12,34,567`, `1234,567`, `1, 000` ve güvenli integer sınırını aşan değerler reddedilir. Virgüller yalnızca sayısal alan doğrulamasında kaldırılır; `title 1,984` literal başlık olarak korunur.
- Süre etiketi `duration` veya `duration in minutes` olabilir; sayının ardından isteğe bağlı `minute`/`minutes` kabul edilir. Örnek: `Update item 2; duration in minutes: one hundred and forty eight minutes`. API gövdesi yalnızca `duration: 148` içerir. Kesir, sıfır/negatif veya `seconds` gibi başka birim kabul edilmez; sayfa/ID alanına dakika birimi eklenemez.
- Alanları noktalı virgül veya iki noktayla da açık bölümlere ayırabilirsiniz: `Create item; type: book; title: 1984; author: J.D. Salinger; pages: 310`. Etiketten hemen sonra gelen iki nokta değer başlangıcıdır; örneğin `title: Hobbit`. Metin bölümleri yukarıdaki yerel kuralla korunur. Noktalı alan biçimi de desteklenir: `Create item. Type book. Title Hobbit. Author Tolkien. Page 310.` Nokta yalnızca açık sınırda yapısaldır; `J.D.` gibi iç/baş harf noktaları değiştirilmez. Literal virgül, noktalı virgül, iki nokta veya alan etiketiyle çakışan metni çift tırnak içine alın. Örneğin `title "Notes: Author; Volume 1."`. Bilinmeyen bölüm etiketleri tahmin edilmez.
- CREATE tam alanları ister. Replace, title/author ve tam bir pages/duration alanını ister; Update en az bir düzenlenebilir alan ister. İkisi de type değiştiremez; pages ve duration aynı komutta birlikte verilemez. Türle eşleşme taze GET ile kontrol edilir; model doğrulaması yine sunucudadır.
- Her giriş tek komuttur ve en fazla 2000 karakterdir. `and delete item ...` gibi ikinci bir işlem çalıştırılmaz. Böyle bir ifade gerçekten başlığın parçasıysa tırnaklı metin olarak verilebilir; yalnızca veri olur. `eval`, LLM ve ses servisleri yoktur.

### Komut nesnesi ve ortak yürütme

DOM/ağ bağımsız `parseLibraryCommand(text)` örneği:

```json
{
  "action": "update",
  "id": 3,
  "fields": {"page_count": 330},
  "filters": {"type": null, "available": null}
}
```

`action`: `create`, `list`, `get`, `replace`, `update`, `delete`, `checkout`, `return`. CREATE/LIST için id null; gerekmeyen fields boştur. CREATE fields içinde type vardır. LIST filters, type için null/book/dvd ve available için null/true/false kullanır.

`static/script.js` içinden dışa aktarılan **`runCommandText(text)`**, hem panelin hem ilerideki mikrofon transkriptinin ortak girişidir. Önce mevcut busy kilidine girer, komutun tamamını ayrıştırır, ardından `executeLibraryCommand` çağırır. Ayrıştırma hatasında ağ isteği yapılmaz. `command-runner.mjs` API orkestrasyonudur; DOM veya ayrı koleksiyon içermez. Mevcut `apiRequest`, `runAction`, `refreshItems` enjekte edilir/kullanılır. ES modülleri Windows'ta doğru JavaScript MIME türüyle sunulur.

PUT/PATCH daima mevcut öğeyi GET ile alır ve güncel türüyle verilen detail alanını karşılaştırır. Eski kart tek doğruluk kaynağı değildir. Ardından tek PUT/PATCH gönderilir; id/type/is_available gövdeye eklenmez. Checkout/return, API'nin `message` ve `item` sonucunu kullanır; DVD bakım uyarısı responseText'te korunur. DELETE'in 204 gövdesi okunmaz; onaylanan ID ile başarı metni oluşturulur.

Yürütme sonucu `ok`, ayrıştırılmış `command`, `request` (method/path/body), `data`, kısa İngilizce `responseText`, ayrı `warning` ve `uncertain` bilgilerini taşır; HTTP hatasında status da bulunur. Sözdizimi/busy gibi API öncesi sonuçlar yalnızca ilgili hata bilgilerini döndürebilir. Hiçbir yanıt henüz seslendirilmez.

### Yenileme, tekrar gönderim ve ağ belirsizliği

- Mutasyon başarılı, liste yenileme başarısızsa sonuç **başarılı kalır**; ayrı uyarı Refresh list kullanılmasını ister. Aynı komut metni tekrar Run ile gönderilirse yalnızca liste GET'i denenir, ikinci mutasyon gönderilmez. Yenileme başarıyla tamamlandıktan sonraki yeni gönderim yeni bir işlemdir.
- Bir mutasyon isteği sırasında ağ koparsa veya başarılı HTTP yanıtının gövdesi okunamazsa sunucuda uygulanıp uygulanmadığı kesinleştirilmez. `responseText` bunun uygulanmış olabileceğini belirtir. Otomatik tekrar yoktur; aynı belirsiz komut metni de yeniden gönderilmez. Önce koleksiyonu kontrol edin; bilinçli tekrar için metni düzenleyin veya sayfayı yenileyin. Bu koruma kalıcı bir idempotency anahtarı değildir.
- Modelin 400/404/409 yanıtları anlaşılır hata olarak gösterilir; önceki sonuç gizlenir ve form tekrar kullanılabilir. Busy sırasında panel ve normal kontroller çift gönderime karşı kilitlenir.
- Mevcut manuel formun, başarılı POST'tan sonra yeni ID'yi hemen saklayan ve liste hatasında PATCH'e devam eden davranışı korunur.

### Uzun liste ve responseText sınırları

Komutla LIST çalıştırıldığında en fazla **100 kart** gösterilir; sayaç gerçek API sonucunun toplamını ve sınırı belirtir. Kısa ekran/TTS yanıtı toplam adet ile ilk **5 öğenin ID/başlığını** içerir. Her başlık özet içinde en fazla **60 karakter** olur; kesilme ve kalan öğeler belirtilir. Boş liste için `No items match these filters.` üretilir. GET'in ayrıntı alanı gerçek öğenin tüm istenen alanlarını gösterir; kısa responseText'te başlık/yazar 60 karakterle sınırlıdır. Kart/formdaki asıl metin değiştirilmez. Manuel Refresh/listenin önceki davranışı korunur; bu özet/kart sınırı komutla LIST çıktısına uygulanır.

### Aşama 2 testleri ve manuel deneme

Yeni test komutu:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
node --test test_commands.mjs test_script.js
.\.venv\Scripts\python.exe check_commands_browser.py
```

Son komut, yerelde Chrome kuruluysa yeni/ayrı profil ve yalnızca test sürecine ait bir koleksiyonla yerel headless kontrol yapar. Gerçek sayfa/ES modülleri, form submit olayları, Flask HTTP ve gerçek Library modeli kullanılır. Test sunucusu boş bir yerel port seçer; uygulamanın doğrudan çalıştırma portu **5002** olarak kalır. Azure/mikrofon kullanılmaz. Geçici Chrome profili `tmp/` altında ve Git dışındadır.

Bu aşamada **26 Python ve 29 Node.js testi geçti**. Python model/API sözleşmelerini, portu, yeni paneli ve ES modüllerinin sunulmasını; Node parser ve gerçek UI kodunun taklit DOM/API üzerinden yürütülmesini kapsar. Yerel headless Chrome'da gerçek Flask/model ile **14 panel işlemi** başarıyla tamamlandı; JavaScript hatası görülmedi. Ayrıntılar PROMPTS.md'nin Aşama 2 kaydındadır. Headless işlev kontrolü, kullanıcının etkileşimli tarayıcısında görsel/dar ekran kontrolü yapıldığı anlamına gelmez.

Manuel olarak http://127.0.0.1:5002 adresinde Command panelinden oluşturma → dönen ID ile GET → Replace → Update → Checkout → List checked out books → Return → Delete akışını deneyin. Eksik ID için 404, ikinci checkout için 409, hatalı alan/negatif sayı için ayrıştırma hatasını kontrol edin. Eski manuel formu, tür/durum filtrelerini, uzun metinleri ve dar ekranda paneli ayrıca deneyin. Henüz mikrofon, STT veya TTS denemesi yoktur.

### Alan sınırı regresyonu ve gerçek bulgular

Kullanıcı bir oluşturma denemesinde `Ambiguous field word in title/author...` hatası gördüğünü, ardından şu tırnaklı komutu gerçek tarayıcıda başarıyla çalıştırdığını bildirdi:

```text
Create item, type book, title "Test Book", author "Test Author", pages 220
```

Özgün başarısız komut birebir kaydedilmedi. Ayrı bir yerel yeniden üretimde aşağıdaki **önerilmiş tırnaksız örneğin** eski parser'da aynı hatayı verdiği doğrulandı:

```text
Create item, type book, title Test Book, author Test Author, pages 220
```

Doğrulanan kod nedeni, açık virgül sınırlarına rağmen `Test Author` değerindeki `Author` sözcüğüne uygulanan gereksiz belirsizlik reddiydi. Bu, kaydedilmemiş özgün kullanıcı komutunun kesin nedeni olarak sunulmaz. Kontrol düzeltildi; iki örnek artık aynı komut nesnesini ve API gövdesini üretir. Virgülsüz gerçekten belirsiz PATCH metninde ise başlık/yazar tahmin edilmez; ağ isteğinden önce hata verilir. API/model veya diğer komutların semantiği değiştirilmedi. Son regresyon sonuçları PROMPTS.md'de kayıtlıdır.

Bu düzeltmede **34 Node.js ve 26 Python testi geçti**. İzole gerçek Flask/model ile headless Chrome'da tırnaklı/tırnaksız Test Book / Test Author oluşturma ve GET doğrulamaları dahil **18 panel işlemi** geçti; JavaScript hatası görülmedi. Bu, kullanıcının etkileşimli tarayıcısında düzeltme sonrası doğrulama yapıldığı anlamına gelmez; görsel/dar ekran veya ses/Azure denemesi yapılmadı.

## Aşama 3 — Azure mikrofon girişi

### Gerçek transkript için sayfa etiketi ve nokta düzeltmesi

Kullanıcı Azure/mikrofon denemesinde `Create Item Type Book Title Hobbit Author Tolkien. Page 310.` transkriptini ve eksik CREATE alanları hatasını bildirdi. Bu girdi düzeltme öncesinde yerel parser ile yeniden üretildi: nokta kaldırıldığında da tekil `Page` tanınmadığı için aynı hata oluştu. Yalnızca `Pages` yapıldığında komut ayrıştı, ancak yazar `Tolkien.` olarak kaldı. Dolayısıyla eksik alan hatasının doğrulanan nedeni desteklenmeyen tekil etiketti; alan sınırındaki nokta ayrı bir değer sorunu oluşturuyordu.

Artık `page`, `pages` ve `page count` eş anlamlıdır. Yukarıdaki transkript `type: book`, `title: Hobbit`, `author: Tolkien`, `page_count: 310` alanlarını üretir. Açık sonraki alan etiketi öncesinde bir sözcüğün sonundaki cümle noktası veya ayrı nokta sınır olarak işlenir; tüm metinden nokta silinmez. `J.D. Salinger` içindeki noktalar, büyük/küçük harf ve tırnak içindeki literal noktalar korunur. Bir değerin son noktasını literal olarak korumak için değeri çift tırnak içine alın. Virgüllü değerlerin içindeki alan kelimeleri yeni alan sayılmaz; belirsiz virgülsüz girdiler reddedilmeye devam eder.

Bu düzeltmede **55 Node.js ve 42 Python testi geçti**. Gerçek transkriptin mock STT üzerinden ortak komut akışına aktarılması tek POST ve beklenen gövdeyle kontrol edildi; eksik, yinelenen ve belirsiz alanlar ağ isteğinden önce reddedildi. STT, model ve API sözleşmesi değiştirilmedi. **Düzeltme sonrası gerçek Azure/mikrofon yeniden doğrulaması yapılmadı.**

### Akış ve kullanım

Command bölümündeki **Start microphone → Stop and process** kontrollerini kullanın. **Cancel recording** izin beklerken, kayıt veya STT isteği sırasında iptal eder. İlk dil yalnızca **en-US**. İzin bekleme, kayıt, son PCM parçasını bekleme, WAV gönderme, Azure tanıma ve komut sonucu ayrı durumlarla gösterilir. Kayıt 30 saniyede otomatik durur; worklet'in son parçası alınmadan dosya gönderilmez. Bu sürüm canlı transkript göstermez; kayıt bitince tüm dosya tanınır.

```text
Microphone → AudioContext/AudioWorklet → 16 kHz mono PCM → WAV
→ POST /api/voice-input → complete transcript
→ runCommandText(text) → existing parser/runner → existing Library API
```

Tanınan metin harfleri/noktalaması değiştirilmeden `Recognized transcript` alanında ve düzenlenebilir Command kutusunda gösterilir. Sonuç yalnızca ortak yürütme akışının gerçek API yanıtından gelir. Belirsizlik veya parser hatasında otomatik tahmin yapılmaz; kullanıcı metni düzeltip Run command ile devam edebilir. **Bu manuel düzeltme, başarılı tam sesli yürütme sayılmaz.** Mikrofon/STT hatası ayrı ses hata alanında; parser ve Library API hataları Command panelinde gösterilir. `responseText` korunur, seslendirilmez.

Kayıt ve STT işlemi boyunca başka kayıt, metin komutu veya manuel mutasyon başlatılamaz. İç oturum token'ı yalnızca o oturumun tamamlanmış transkriptine mevcut busy akışından geçiş verir. Başarılı transkript tek kez yürütülür. Mikrofon hata verdiğinde önceki başarı yeni sonuç gibi bırakılmaz; özgün transkript varsa incelemek için saklanır.

### Ses biçimi ve kaynak yönetimi

- Task 2'de çalışan yaklaşım bağımsız kaynak olarak uyarlandı. Çalışma sırasında Task 2 importu/dosya yolu yoktur; hesap makinesi komutları ve TTS kuyrukları taşınmadı.
- AudioWorklet'in gerçek `sampleRate` değeriyle parçalar arası faz korunarak mono, signed 16-bit little-endian **16 kHz PCM** üretilir. Hoparlöre geri mikrofon sesi verilmez; worklet çıkışı sessizdir. `makeWav` doğru RIFF/fmt/data başlığını gerçek PCM baytlarına göre ekler. Yalnızca bir sampleRate etiketi değiştirilmez.
- 30 saniye en fazla 480.000 PCM örneği / 960.000 bayttır. Worklet ve ana akış bu sınırı ayrı uygular. Son parçayı flush bildirimiyle bekleme sınırı 3 saniyedir; eksik ses gönderilmez. İzin bekleme sınırı 45, STT HTTP bekleme sınırı 90 saniyedir.
- Durdurma/iptal/hata/pagehide yollarında track, port, ses düğümleri ve AudioContext temizlenir. Temizlik bir kez uygulanır; bir kaynak hatası diğer kaynakların kapatılmasını engellemez. WAV bellekte oluşturulur; oynatma/object URL üretilmez. Framework yüklemesinin FileStorage kaynağı sunucuda okunduktan sonra açıkça kapatılır; ortak geçici WAV dosyası kullanılmaz.
- Native timer'lar global alıcıyı koruyan sarmalayıcılarla çağrılır; eski Illegal invocation hatasındaki ham Window fonksiyonunu nesne metodu olarak saklama yapılmaz.

### Ses endpoint'i ve SDK

`POST /api/voice-input`, multipart `audio` WAV dosyası alır. `language` en-US olmalıdır; belirtilmezse en-US varsayılır. Dosya uzantısı/MIME güven kaynağı değildir. Gerçek RIFF/WAVE toplam/bölüm boyutları, PCM tag, sample rate, mono kanal, bit/örnek boyutu, byte rate/alignment, boş data ve süre kontrol edilir. Limitler **1 MiB ve 30 saniye**. Upload toplamı için 64 KiB multipart payı yalnızca bu endpoint'e uygulanır; mevcut Library JSON isteklerine yeni genel boyut sınırı eklenmez.

Başarı yalnızca transkript döndürür; endpoint koleksiyonu okumaz veya değiştirmez:

```json
{"text":"Check out item four","language":"en-US"}
```

Hatalar JSON `error` alanıyla gelir: eksik/boş/bozuk WAV veya geçersiz dil 400, toplam aşırı yükleme 413, sessiz/eksik tanıma 422, eksik Speech ayarı 503, Azure/timeout/temizlik hatası 502. Ses isteği başarısı Library işlemi başarısı demek değildir; parser veya sonraki API ayrıca hata verebilir.

Her istek bağımsız SpeechRecognizer/PushAudioInputStream ve dinleyicilere sahiptir. Continuous recognition yalnızca kesinleşmiş RecognizedSpeech segmentlerini sırayla birleştirir; interim sonuçlar kullanılmaz. Normal EOF tek başına başarı değildir: `session_stopped` gerekir. NoMatch bölümü, iptal, callback hatası veya timeout varsa kısmi komut uygulanmaz. Sonuç bekleme 60 saniye, SDK start/stop beklemeleri ayrı ayrı 5 saniyeyle sınırlıdır.

İptal olayında `event.cancellation_details.reason/code` kullanılır. Stop/get beklemesi SDK callback'i içinde yapılmaz. Ana işlem durdurmayı bekler, isteğe ait sinyallerde `disconnect_all()` çağırır, stream'i kapatır; konuşma kilidi her durumda bırakılır. Temizlik hatası başarı üretmez veya asıl hata tanısını maskelemez. Ham SDK hata ayrıntıları, anahtarlar, ses veya transkript loglanmaz/istemciye hata ayrıntısı olarak aktarılmaz. Takılmış native get iş parçacığı Python tarafından zorla sonlandırılamaz; uygulamanın beklemesi sınırlıdır.

### İptal ve mutasyon sınırı

İptal edilmiş veya eski STT yanıtı komut çalıştırmaz. Komut ortak yürütücüye aktarıldığında kayıt iptal düğmesi devre dışıdır; gönderilmiş bir mutasyonu geri alma sözü verilmez. Sekmeden ayrılma komut isteğini yerelde iptal edebilir; bu sunucuda işlemin uygulanmadığı anlamına gelmez. PUT/PATCH ön tür GET'i sırasında iptal olursa sonradan mutasyon gönderilmez. Mutasyon gönderildikten sonra belirsiz bağlantı sonucunda mevcut `uncertain` yanıtı ve tekrar engeli korunur; otomatik yeniden gönderim yoktur. Başarılı mutasyon sonrası yenileme hatasında da yalnızca görünüm yenilemesi tekrar denenir.

### Ses transkriptlerinde gramer

Mevcut komut grameri korunur. Açık virgülsüz örnekler:

```text
Create item type book title The Hobbit author Tolkien pages 310
Update item four pages three hundred twenty
Check out item four
```

Virgüllü başlık/yazar değerlerinde author/title gibi kelimeler literal veri olarak kalır. Genel noktalama silme veya bütün transkripti küçük harfe çevirme eklenmedi. Azure'un noktalaması alan sınırını belirsizleştirirse parser tahmin etmez. Komutu düzeltmek gerektiğinde sesli işlemin başarıyla tamamlandığı iddia edilmez.

### Aşama 3 doğrulaması ve gerçek deneme listesi

Başlangıçta mevcut **26 Python + 34 Node.js** testi doğrulandı. Son kontrolde **42 Python ve 49 Node.js testi geçti**. Eski 18 metin paneli headless işlemi de yeniden geçti. Yeni headless ses kontrolünde sekiz komut türü ve bir parser hatası için 9 mock STT çağrısı yapıldı; manuel düzeltme ve kayıt iptali ayrıca kontrol edildi. JavaScript hatası görülmedi. Ayrıntılar PROMPTS.md'dedir. SDK testlerinde gerçek 1.53.0 sınıflarının spec/autospec yüzeyi kullanılır; dotenv ve Azure çağrıları mock'tur. Node testlerinde sentetik ses ve taklit medya/ağ vardır.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
node --test test_commands.mjs test_script.js test_voice_input.mjs
.\.venv\Scripts\python.exe check_commands_browser.py
.\.venv\Scripts\python.exe check_voice_browser.py
```

İkinci headless kontrol gerçek sayfa/ES modülleri ve gerçek yerel Flask/Library API kullanır; mikrofon, AudioContext/Worklet kaynağı ve STT transkriptleri mock'tur. İzole koleksiyon ve `tmp/` altında boş profil kullanılır; gerçek donanım veya Azure başarısı olarak sunulmaz.

**Kullanıcının bildirdiği önceki manuel doğrulama:** Diğer komut işlemleri önceki aşamada doğru çalışıyordu. Son alan-sınırı düzeltmesinin kullanıcı tarafından yeniden doğrulandığı varsayılmadı. Aşama 3 için asistan gerçek Azure çağrısı veya mikrofon erişimi yapmadı.

Gerçek mikrofonla yerelde kontrol edin:

1. İzin verme/reddetme, kaydı durdurma, 30 saniyede otomatik işlem, izin beklerken ve kayıt/STT sırasında iptal; sonrasında yeniden kullanım.
2. Bir Book oluşturun; gerçek dönen ID ile Get, List available books, Replace, Update, Checkout, List checked out books, Return ve Delete söyleyin. DVD oluşturma/düzenleme/checkout bakım uyarısını da deneyin.
3. Örnek `four` ID'sini gerçek öğenize uyarlayın. ID/sayfa/süre sayı kelimelerini ve rakamları, `1984` gibi başlıkları deneyin.
4. Aynı öğeyi ikinci kez checkout ederek 409, eksik ID ile 404, belirsiz komutla parser hatasını kontrol edin. Transkriptin Command alanında düzeltilebilir kaldığını doğrulayın; manuel düzeltmeyi ayrı kaydedin.
5. Kayıt sırasında ikinci kayıt ve manuel komut engelini; durdurmada son kelimenin kaybolmamasını; iptal sonrası geç yanıtın işlem yapmamasını kontrol edin.
6. Ağ/servis hatasında kısmi transkriptin çalıştırılmamasını, gönderilmiş mutasyonda belirsizliğin dürüstçe gösterilmesini ve otomatik tekrar yapılmamasını deneyin. Görsel/dar ekran kontrolünü ayrıca yapın.
