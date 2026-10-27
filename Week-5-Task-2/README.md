# EE471 Week 5 Task 2 — Sesli girişli hesap makinesi

`Week4/calculator` temelinden bağımsız çalışan Flask hesap makinesi. Mevcut dört işlem, Calculator sınıfı, hesaplama API'si, tuşlar ve hesap makinesi görünümü korunur. Mikrofon paneli en-US sesli komut alır; isteğe bağlı Azure TTS fiziksel arayüz tuşlarını ve eşittir sonucunu İngilizce okur.

Flask, `GET /` ile arayüzü ve `POST /api/calculate` ile dört işlem API'sini sunar. Hesaplamalar Python'daki `Calculator` sınıfında yapılır. JavaScript girişleri, işlem ekranını ve API isteklerini yönetir; `eval()` kullanılmaz. HTML/CSS/JavaScript için derleme adımı yoktur.

## PowerShell ile kurulum ve çalıştırma

EE471 repo kökünden:

```powershell
cd .\Week-5-Task-2
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
.\.venv\Scripts\python.exe app.py
```

Sanal ortam zaten varsa oluşturma adımını atlayın. `.env` zaten varsa kopyalama komutunu çalıştırmayın. Yerelde kendi Azure Speech anahtarınızı `SPEECH_KEY`, kaynak bölgesini `SPEECH_REGION` olarak ayarlayın. Örnek dosyada anahtar boştur; `eastus` yalnızca örnek bölgedir. Anahtarları paylaşmayın.

Sanal ortamı etkinleştirmek gerekmez. Tarayıcıda <http://127.0.0.1:5000> adresini açın. Mikrofon için localhost üzerinde güncel Chrome/Edge gibi AudioWorklet destekli tarayıcı kullanın. Durdurmak için `Ctrl+C` kullanın. Aynı portta başka bir Flask uygulaması çalışıyorsa önce onu durdurun. Azure ayarları eksik olsa da ana sayfa ve manuel hesaplama çalışır.

## Sesli komut kullanımı

“Mikrofonu başlat” ile izin verin, İngilizce komutu söyleyin, “Durdur ve işle”ye basın. Kayıt otomatik olarak en fazla 15 saniyede durur ve işlenir. Bu sürüm kayıt tamamlandıktan sonra WAV yükler; canlı metin akışı sunmaz. Tanınan özgün metin ve normalleştirilmiş işlem ayrı gösterilir.

| Söylenen komut | İşlem | Beklenen sonuç |
| --- | --- | --- |
| five plus two is | 5 + 2 = | 7 |
| seven minus three is | 7 − 3 = | 4 |
| three times two is | 3 × 2 = | 6 |
| nine over three is | 9 ÷ 3 = | 3 |
| one point five plus two is | 1.5 + 2 = | 3.5 |

Desteklenen kelimeler: `zero one two three four five six seven eight nine point plus minus times over is`. Azure'un `5`, `12`, `1.5` gibi rakamlı çıktıları da kabul edilir. Söylenen art arda rakamlar birleştirilir: `one two` → `12`. Büyük/küçük harf ve olağan cümle noktalaması normalleştirilir; sayısal ondalık nokta korunur. Dilbilgisi **sayı işlem sayı is** biçimindedir. Bir komutta tek işlem ve sonda tek `is` gerekir; negatif sayı, yüzlük sayı kelimeleri ve ek ifadeler bu sürümde desteklenmez.

Azure'un sembollü çıktıları da desteklenir: `+` → `plus`, `-`/`−` → `minus`, `*`/`×` → `times`, `/`/`÷` → `over`, `=` → `is`. Semboller ayrı token olarak eşlenir; boşluksuz `6−2=` de kabul edilir. Bilinmeyen kelimeler silinmez. Negatif sayılar, art arda operatörler ve birden fazla eşittir reddedilir. `1.5` içindeki ondalık nokta korunur, `is.` sonundaki nokta ayrılır; `.5` ve `1..5` gibi desteklenmeyen/bozuk sayılar başka sayılara dönüştürülmez.

### Gerçek hata ve ayrıştırıcı düzeltmesi

Kullanıcının gerçek mikrofon/Azure denemesinde tanınan `6 - 2 is.` metni “Desteklenmeyen kelime var” hatası verdi. Neden: önceki ayrıştırıcı işlem kelimelerini kabul ediyor, Azure'un ürettiği `-` sembolünü kelimeye eşlemiyordu. Token düzeyindeki sembol eşlemesiyle beklenen normalleştirme `6 − 2 =`, mevcut hesaplama API'sindeki sonuç `4` olur. Azure tanıma kodu ve hesaplama akışı değiştirilmedi.

Düzeltme sonrasında 15 Node.js testi ve 15 Python testi geçti. Beş sembollü örnek, önceki kelimeli örnekler, negatif/geçersiz diziler ve hata halinde hesap makinesi durumunun korunması kontrol edildi. UI testlerinde API yanıtları mock'tur; Python testleri aynı operandların gerçek yerel Calculator/API sonuçlarını ayrıca kontrol eder. **Bu düzeltmenin yeni gerçek mikrofon/Azure doğrulaması henüz yapılmadı.**

Tüm komut doğrulanmadan hesap makinesi durumu değişmez. Bilinmeyen kelime atlanmaz. Geçerli komut, tuşlarla aynı `clear` / `enterDigit` / `chooseOperation` / `calculate` akışından geçer; ayrı hesaplama motoru yoktur. Sıfıra bölme mevcut API hata alanında gösterilir. Ses işlemi boyunca tekrar başlatma, manuel tuşlar ve klavye girişleri engellenir.

## Ses ve tanıma mimarisi

- `voice-input.mjs` izin, kayıt, durdurma, yükleme ve hata durumlarını yönetir. `voice-worklet.mjs`, gerçek AudioContext örnekleme hızını kullanır; `pcm-resampler.mjs` parçalar arasında dönüşüm fazını korur, kanalları monoya indirir ve 16 kHz signed 16-bit little-endian PCM üretir. Hoparlör çıkışı sessizdir.
- İşlenmiş PCM bellekte en fazla 480.000 bayt tutulur. `voice-audio.mjs` doğru RIFF/WAVE başlığı ekler. Örnekleme hızının yalnızca başlıkta değiştirilmesi söz konusu değildir.
- `POST /api/voice-input`, multipart `audio` dosyası alır. Sunucu uzantı/MIME yerine gerçek RIFF boyutlarını, fmt/data bölümlerini, PCM formatını, 16-bit/mono/16 kHz, süreyi (15 saniye) ve dosya boyutunu (1 MiB) doğrular. Başarı: `{"text":"Five plus two is.","language":"en-US"}`. Geçersiz ses 400, büyük HTTP yüklemesi 413, tanınmayan/eksik segment 422, eksik yapılandırma 503, servis/temizlik hatası 502 döndürür.
- `speech_service.py`, yalnızca bu klasördeki açık `.env` yolunu konuşma isteği sırasında python-dotenv ile yükler. Ortam değişkenleri önceliklidir. Anahtarlar istemciye ve loglara aktarılmaz; dosya inceleme araçlarıyla gerçek `.env` okunmamıştır.
- SDK 1.53.0 `SpeechRecognizer` ve `PushAudioInputStream` ile continuous recognition kullanılır. Kesinleşmiş `recognized` parçaları sırayla birleştirilir; geçici sonuçlar eklenmez. İlk sonuç/duraklama bitiş sayılmaz; normal EOF sonrasında `session_stopped` gerekir. NoMatch segmenti varsa diğer parçalar tam komut gibi sunulmaz.
- [Microsoft SpeechRecognizer belgeleri](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer) continuous başlangıç/durdurma API'sini açıklar. [Resmî Python örnekleri](https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/samples/python/console/speech_sample.py) incelenmiştir. Task 1'in düzeltilmiş yaklaşımı Task 2'ye bağımsız taşınmıştır; Task 1 dosyalarını çalışma sırasında import etmez.
- Her istek kendi recognizer ve stream'ine sahiptir. Ortak kilit paralel Azure oturumlarını engeller. Beklemeler sınırlıdır (tanıma 45 saniye, SDK başlatma/durdurma ayrı ayrı 5 saniye). İptal `event.cancellation_details.reason/code` üzerinden değerlendirilir; kısmi sonuç hata/timeout durumunda başarı sayılmaz.
- Temizlik ana akışta tanımayı durdurur, `disconnect_all()` ile yalnızca o isteğin dinleyicilerini kaldırır, stream'i kapatır; kilit `finally` içinde bırakılır. Temizlik hatası başarı üretmez ve asıl hatayı maskelemez. Takılmış native SDK çağrısını Python zorla sonlandıramaz; istek beklemesi sınırlanır.
- Durdurma son PCM parçasını bekler. Mikrofon track'leri, port, ses düğümleri ve AudioContext yüklemeden önce kapatılır; hata ve `pagehide` yollarında da temizlenir. Ağ isteği sınırlı sürede iptal edilir. Geçici WAV dosyası sunucu diskine yazılmaz.

## Kullanım ve API

- Dört işlem, ondalık giriş, ardışık işlemler ve klavye desteği korunmuştur.
- `3`, `+`, `2`, `=` sırası ekranda önce `3 + 2`, ardından API'den gelen `5` sonucunu gösterir.
- Sonuçtan sonra sayı girişi yeni işlem başlatır; operatör seçimi sonuçla devam eder.
- Temizle veya `Esc` durumu sıfırlar; `Backspace` mevcut girdiden karakter siler.
- İstek sırasında tuşlar devre dışı kalır; hatalar görünür alanda gösterilir.

`POST /api/calculate`, JSON olarak `operation`, `x`, `y` alanlarını alır. İşlemler `add`, `subtract`, `multiply`, `divide`; sayısal girdiler sonlu JSON sayıları olmalıdır. Boolean ve sayısal metin kabul edilmez.

```json
{"operation":"add","x":10,"y":5}
```

Başarı: HTTP 200, `{"result":15}`. Geçersiz JSON/alan/işlem/sayı, sıfıra bölme veya hesaplanamayan sonuç: HTTP 400, `{"error":"..."}`.

Sunucu çalışırken ayrı bir PowerShell penceresinde:

```powershell
$payload = @{ operation = 'add'; x = 10; y = 5 } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/calculate' -Method Post -ContentType 'application/json' -Body $payload
```

## Dosyalar ve kontroller

`app.py` Flask uygulaması; `custom_classes.py` hesaplama sınıfı; `main.py` konsol örneğidir. `templates/index.html`, `static/style.css`, `static/script.js` hesap makinesi arayüzünü oluşturur. Bağımlılıklar Flask, python-dotenv ve Azure Speech SDK 1.53.0'dır. Ses modülleri ve çevrimdışı regresyon testleri Task 2 klasöründedir.

Task 2 klasöründen:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v -p "test_*.py"
.\.venv\Scripts\python.exe main.py
node --test test_voice.mjs test_voice_ui.mjs test_tts.mjs test_tts_cache.mjs
```

`main.py` örneğinin beklenen çıktısı `10.0` olur. Node.js varsa JavaScript sözdizimi ayrıca denetlenebilir:

```powershell
node --check .\static\script.js
```

### İlk temel aşamasının geçmiş doğrulaması — 2026-10-27

- Python 3.13 ve proje dışında geçici dizine kurulan Flask 3.1.3 ile `test_app.py` içindeki dört test metodu ve alt senaryolar geçti: dört işlem, hatalı girdiler/JSON, ana sayfa ve iki statik dosyanın sunulması.
- Task 2 içindeki `main.py` çalıştırıldı; çıktı `10.0` oldu.
- `node --check static/script.js` sözdizimi kontrolü geçti.
- Kopyalanan sekiz dosyanın SHA256 değerleri kaynaklarıyla birebir eşleşti; davranış ve görünüm kodu aynen korundu.
- Git yok sayma kuralları örnek yollarla doğrulandı. Git durumunda yalnızca yeni `Week-5-Task-2/` klasörü bulunuyor.
- Gerçek tarayıcıda görsel/etkileşimli kontrol yapılmadı. Bu sonuçlar bu kopyada çalıştırılan kontrollerdir; Week4 veya Task 1'in önceki test sonuçları aktarılmadı.

`.gitignore`, yerel ortamları, gizli ayarları, önbellekleri ve geçici çıktıları dışarıda tutar. Kaynak projeden bu dosyalar kopyalanmamıştır. İstem kaydı `PROMPTS.md` içindedir.

### Sesli giriş aşamasının doğrulaması

Bu aşamada **15 Python testi ve 12 Node.js testi geçti**; JavaScript sözdizimi kontrolü de başarılı. Kapsam: mevcut hesaplama API'si, beş komut örneği, gramer/normalizasyon, ses biçimi/süre/boyut kontrolleri, kesin sonuç sıralaması, EOF/NoMatch/servis/timeout/temizlik hataları ve kilit temizliği; PCM dönüşümü, WAV başlığı, mikrofon durumları ve ortak hesaplama akışı. Ayrıntılar PROMPTS.md'deki sesli giriş kaydındadır.

Bunlar gerçek Azure/mikrofon testi değildir. Python testleri gerçek SDK sınıflarının `spec_set`/autospec yüzeyleriyle taklit olay ve sonuçlar kullanır; `.env` yükleme fonksiyonu mock edilir. Node testleri sentetik ses, taklit DOM, medya kaynakları ve API yanıtları kullanır.

Gerçek tarayıcıda ayrıca mikrofon izni verme/reddetme, beş örnek komut, 15 saniyede otomatik durdurma, sessiz/yanlış komut, sıfıra bölme, hata sonrası tekrar kayıt, sekmeden ayrılınca mikrofonun kapanması ve manuel tuşlarla devam etme kontrol edilmelidir. Task 1 için daha önce bildirilen kullanıcı doğrulaması Task 2 doğrulaması değildir. Bu aşamada gerçek Azure çağrısı veya mikrofon erişimi yapılmadı.

## Azure TTS ile sesli çıkış

“İngilizce sesli çıkış” kutusunu işaretleyin (başlangıçta kapalıdır). Sayı tuşları `zero`–`nine`, nokta `point`, işlem tuşları `plus`, `minus`, `times`, `over` olarak okunur. Fiziksel eşittir düğmesi, başarılı `/api/calculate` yanıtını bekler; örneğin `5 + 3 =` ardından **“is eight”** okunur. Yeniden hesaplama yapılmaz. Sıfıra bölme, geçersiz/sonlu olmayan sonuç veya henüz tamamlanmamış işlem için sonuç seslendirilmez. Boşta eşittire yeniden basılması da sonuç sesi üretmez. Klavye ve sesli girişin programatik tuşları bu aşamada seslendirilmez.

`tts-queue.mjs`, sayı gösterimini konuşma metnine dönüştürür; bir hesaplama motoru değildir. Negatif sonuç `minus`, ondalık sonuç `point` ve kesir basamakları tek tek okunur: `-24.05` → “is minus twenty four point zero five”. Normal tam sayılar 15 basamağa kadar İngilizce sayı adlarıyla, daha uzun düz tam sayılar rakam rakam okunur. Hesap makinesinin mevcut JavaScript Number / `String(result)` gösterimi ve hassasiyeti korunur. Bilimsel gösterim açılarak yeni bir sayı hesaplanmaz: `1e+21` → “is one times ten to the power of twenty one”; `1e-7` → “is one times ten to the power of minus seven”. Geçersiz veya sonlu olmayan değerler seslendirilmez.

`POST /api/tts`, `{"text":"is eight"}` JSON isteğini alır (boş olmayan, en fazla 500 karakter). Aynı `SPEECH_KEY`/`SPEECH_REGION` yapılandırması ve ortak konuşma kilidi kullanılır. Azure Speech SDK 1.53.0, `en-US-JennyNeural` ve `Riff16Khz16BitMonoPcm` ile bellek içi WAV üretir; `audio_config=None` sayesinde sunucu hoparlörü kullanılmaz. WAV tarayıcıda Audio ile oynatılır; tarayıcının speechSynthesis API'si kullanılmaz. [Microsoft'un bellek içi ses üretimi açıklaması](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis?pivots=programming-language-python) incelenmiştir. Yapılandırma hatası 503, servis/iptal hatası 502, geçersiz metin 400 döndürür; ham exception ve anahtarlar istemciye aktarılmaz.

Kuyruk, aktif öğe dahil en fazla 12 ses tutar. Üretim ve oynatma sırayla yapılır; sesler üst üste binmez. Dolduğunda yeni ses atlanır ve ayrı ses hatası gösterilir. Hesap makinesi, TTS kuyruğunu beklemez. Ses isteğinde 20 saniye ve oynatmada 30 saniye istemci bekleme sınırı vardır. Ses hatası hesaplama sonucunu değiştirmez.

Temizleme, sesli çıkışı kapatma ve sayfadan ayrılma kuyruk neslini geçersiz kılar; bekleyen istek iptal edilir, oynayan ses durur, object URL ve oynatma kaynakları temizlenir. Geç gelen eski yanıtlar oynatılmaz. HTTP iptali, sunucuda başlamış Azure üretiminin mutlaka iptal edildiği anlamına gelmez; bu ses tarayıcıya geri gelse de oynatılmaz. Mikrofon izni istenmeden önce TTS durdurulur; mikrofon/sesli giriş işlemi boyunca yeni ses alınmaz veya oynatılmaz. Sonrasında eski kuyruk yeniden başlamaz; sonraki fiziksel tuşlar yeniden seslendirilir.

### Manuel doğrulama ve TTS testleri

**Kullanıcının bildirdiği manuel doğrulama:** Sesli giriş ve “işlem = sonuç” gösterimi gerçek tarayıcı/Azure ile çalışıyor. Bu doğrulamayı kullanıcı gerçekleştirdi; bu kayda ayrı ayrı bildirilmemiş senaryolar eklenmemiştir.

TTS için otomatik mock/sentetik testler ayrı tutulur. Tüm testler yeniden çalıştırıldı: **21 Python testi ve 27 Node.js testi geçti**. SDK yüzeyine uygun TTS mock'ları, tuş eşleşmeleri, “is eight”, hata/iptal, ses sırası, kuyruk sınırı, URL temizliği ve mikrofonla çakışmama kontrol edildi. Yeni TTS özelliği henüz gerçek Azure veya tarayıcıyla doğrulanmadı. Ayrıntılar PROMPTS.md'nin TTS kaydındadır.

Gerçek tarayıcıda kullanıcı tarafından kontrol edilecekler:

- Sesli çıkışı açıp `5`, `+`, `3`, `=` tuşlarına basın; “five”, “plus”, “three”, “is eight” sırasını ve ekranda `8` sonucunu kontrol edin.
- Ondalık/negatif sonuçları ve hızlı tuş girişlerinde ses sırasını kontrol edin. Sıfıra bölmede sonuç okunmamalı; TTS hatası hesaplama sonucunu silmemeli.
- Ses beklerken temizleyin, çıkışı kapatın ve sayfadan ayrılın; eski sesler sonradan başlamamalı.
- Ses oynarken mikrofonu başlatın; ses durmalı, kayıtta uygulamanın sesi duyulmamalı. Sesli komutun programatik tuşları tek tek okunmamalı.
- Tarayıcının otomatik oynatma engeli veya Azure hatası olursa ayrı ses hata alanını ve sesli çıkışı kapatıp açarak tekrar kullanımı kontrol edin.

### Ses duyulmaması için aşamalı tanılama

Kullanıcı, sesli çıkış etkin olduğu halde butonlardan ses duymadığını bildirdi. Gerçek tarayıcıya erişim olmadığından bu olayın nedeni kesinleştirilemedi; Azure ayarı veya autoplay sorunu olduğu varsayılmadı.

Kodda doğrulanan ayrı bir başlangıç hatası düzeltildi: kutu başlangıçta işaretliyken kuyruk yine kapalı kuruluyordu ve yalnızca `change` olayı sonrasında açılıyordu. Kuyruk artık kurulurken kutunun güncel durumuyla eşitlenir. Bu durumun kullanıcının yaşadığı olayın nedeni olduğu henüz doğrulanmadı.

Sesli çıkış panelindeki yeni durum satırı, modül yüklenmesi, açık/kapalı veya mikrofon nedeniyle bekletilme, tuşun kuyruğa alınması, Flask isteği, doğrulanmış WAV boyutu, oynatmanın başlaması ve bitmesini ayırır. Modül yüklenmezse ilk açıklama ekranda kalır. HTTP hata kodları, boş/bozuk PCM WAV, istek zaman aşımı ve oynatma hatası ayrı güvenli mesajlarla gösterilir. `audio.play()` gerçekten `NotAllowedError` ile reddedilirse ancak o zaman izin reddi belirtilir. Ham sunucu gövdesi, exception mesajı, anahtar, ses verisi veya transkript loglanmaz.

Yanıt yalnızca `audio/wav` MIME etiketiyle kabul edilmez: boş olmaması, RIFF boyutu, fmt/data bölümleri, PCM 16-bit/mono/16 kHz biçimi ve ses örnekleri doğrulanır. Bu kontrol sesin duyulabildiğini kanıtlamaz. “Tarayıcı ses oynatmasını başlattı” ifadesi oynatma API'sinin kabulünü bildirir; fiziksel hoparlörden ses duyulduğu anlamına gelmez.

Güncel çevrimdışı kontroller: **31 Node.js testi ve 21 Python testi geçti**. İşaretli başlangıç kutusu regresyonu, gerçek uygulama modülleriyle taklit fiziksel buton → kuyruk → HTTP → WAV → play akışı, bozuk/boş yanıt ve oynatma reddi dahil edildi. Bunlar mock/sentetik kontrollerdir; yeni gerçek Azure/tarayıcı doğrulaması yapılmadı. Yerelde sayfayı yenileyip sesli çıkışı açın, bir tuşa basın ve panelde kalan durum/hata metniyle hangi aşamanın tamamlandığını kontrol edin.

### Kuyruk mesajında kalma düzeltmesi ve tarayıcı regresyonu

Sonraki kullanıcı denemesinde tüm tuşlar kuyruk mesajında kaldı. Bu belirti için doğrulanan akış hatası: native `Window.setTimeout` kuyruk metodu olarak `this.setTimer(...)` ile çağrıldığında headless Chrome **`TypeError: Illegal invocation`** üretti. Hata HTTP isteğinden önce, öğenin hata yakalama kapsamı dışındaydı. Zamanlayıcı sarmalayıcıları doğru çağrı bağlamını koruyacak şekilde düzeltildi; başlangıç hataları yakalama/temizlik kapsamına alındı. Yeni tuş mesajlarının aktif tüketicinin ilerleme durumunu ezmesi de engellendi.

Task 2 klasöründen ek tarayıcı regresyonu:

```powershell
.\.venv\Scripts\python.exe check_tts_browser.py
```

Bu kontrol yerelde kurulu Chrome'u boş, `tmp/` altında tutulan bir profille headless başlatır. Gerçek HTML/modüller, native zamanlayıcılar ve yerel Flask HTTP kullanılır; fiziksel 5 düğmesi tıklanır. Kapat/aç ve mikrofon düğmeleriyle başlat/durdur sonrası tekrar edilir. Çalıştırılan kontrolde **3 TTS HTTP isteği ve 3 Audio.play çağrısı**, sıfır JavaScript hatası görüldü. Tüketici elle tetiklenmedi.

**Sınırı:** Azure üretimi, medya kaynakları ve Audio mock'tur; testte autoplay izinli ayarlanır. Gerçek Azure sesi, fiziksel mikrofon/hoparlör veya kullanıcının etkileşimli tarayıcı oturumu doğrulanmış değildir. Native timer hatasının tarayıcıda yeniden üretilmesi ve düzeltilmesi, gerçek sesin duyulduğu iddiasından ayrıdır. Önceki Node testlerinin native Window alıcı kısıtını modellememesi giderildi. Güncel toplam test sayıları PROMPTS.md'nin son kaydındadır.

### Tuş sesi önbelleği ve gecikme ölçümü

Kullanıcı, sonraki gerçek Azure/tarayıcı denemesinde sesli çıkışın çalıştığını fakat tuş seslerinin gecikmeli geldiğini doğruladı. Bu kullanıcı tarafından yapılmış manuel doğrulamadır. Gerçek gecikmenin hangi bileşenden ne ölçüde kaynaklandığı ölçülmedi; Azure veya oynatma kesin darboğaz ilan edilmedi.

İncelenen önceki akış, her öğe için HTTP/WAV beklemesini ve oynatmanın bitmesini aynı sıralı tüketicide bekliyordu; tekrar kullanılan tuş da yeniden üretim istiyordu. Yeni `tts-cache.mjs`, `zero`–`nine`, `point`, `plus`, `minus`, `times`, `over` seslerini ilk başarılı WAV yanıtından sonra **sayfanın belleğinde** saklar. Aynı ses tekrar kullanıldığında Azure/Flask isteği gönderilmez. Aynı metnin devam eden istekleri tek Promise paylaşır; başarısız yanıt saklanmaz ve yeniden denenebilir. Sonuç cümleleri dinamik kalır; tamamlandıktan sonra önbelleğe alınmaz, yalnızca devam eden aynı metin isteği paylaşılır.

Önbellek en fazla 15 sabit kayıt ve toplam 2 MiB tutar; kapasiteye sığmayan ses normal yoldan oynatılabilir, ancak saklanmaz. Hazırlama tarafında en fazla 12 bekleyen benzersiz iş ve tek HTTP isteği vardır. Otomatik arka plan hazırlaması yapılmaz: ilk tuşun önüne gereksiz Azure istekleri geçmez. İlk kullanımda normal mevcut akış çalışır. Üretim ve oynatma sırası korunur; spekülatif paralel üretim eklenmedi. Hesaplama ses beklemez.

Temizleme/kapatma/mikrofon başlangıcı bekleyen istekleri ve eski oynatma neslini iptal eder; geç yanıtlar oynatılmaz veya önbelleğe eklenmez. Önceden başarıyla alınmış sabit sesler aynı sayfa açıkken saklanır; kapat/aç veya mikrofon işlemi sonrasında yeniden kullanılabilir. Object URL'ler önbelleğe alınmaz; her oynatma sonrasında mevcut kaynak temizliği uygulanır. Sayfa yeniden yüklenince ses önbelleği sıfırlanır; disk/localStorage kullanılmaz.

Panelde metin içermeyen son örnek ölçümleri ve sayaçları gösterilir:

- **İstek/önbellek bekleme (ms):** tüketicinin sesi istemesinden doğrulanmış Blob hazır olana kadar. HTTP, Azure üretimi, yanıt doğrulaması veya önbellek erişimini kapsar; yalnızca Azure sunucu süresi değildir.
- **Oynatma sırası bekleme (ms):** tuşun kuyruğa girişinden kendi ses isteğinin başlamasına kadar. Önceki öğelerin üretim/oynatma beklemesini kapsar; öğenin kendi istek süresi ayrıca gösterilir.
- **HTTP / önbellek / paylaşılan istek:** sayfa oturumundaki toplam sayaçlar. İstek sayacı denemeyi sayar, başarı garantisi değildir.

Süreler `performance.now()` ile ölçülür; yalnızca son sayısal süreler ve sayaçlar bellekte/arayüzde tutulur. Anahtar, kullanıcı metni, transkript veya ses içeriği ölçüm kaydına eklenmez; console/disk telemetrisi yoktur. Yerelde ilk kullanım ile aynı tuşun sonraki kullanımını panelden karşılaştırabilirsiniz. Kuyruk uzunsa, önbellek hazır olsa bile önceki seslerin sırayla bitmesi beklenir.

**Doğrulama:** 40 Node.js ve 21 Python testi geçti. Headless Chrome'da gerçek uygulama başlangıcı/DOM/yerel HTTP ile üç `5` oynatması için **1 mock TTS HTTP isteği ve 2 önbellek kullanımı** doğrulandı; kapat/aç ve mikrofon başlangıç/durdurma kontrolleri korundu. Süre alanları kontrollü saatle ayrıca sınandı. **Bu değişiklik için gerçek Azure gecikmesi ölçülmedi; gerçek kullanımda belirli bir hızlanma veya milisaniye kazancı doğrulandığı iddia edilmiyor.**
