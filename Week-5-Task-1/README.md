# Speech Studio — TTS, STT, Translation ve Pronunciation Assessment

Tek Flask uygulamasında İngilizce (`en-US`) ve Türkçe (`tr-TR`) TTS, STT ve
konuşmadan metne çeviri; ayrıca en-US referans metniyle telaffuz değerlendirmesi.
TTS standart `en-US-JennyNeural` / `tr-TR-EmelNeural` seslerini kullanır;
STT ve çeviri, dosyanın tamamını continuous recognition ile işler. Mikrofon erişimi gerekmez.

## Windows PowerShell kurulumu ve çalıştırma

Python 3.10 veya üzeri kurulu olmalıdır. Repo kökünden:

```powershell
cd .\Week-5-Task-1
if (!(Test-Path -LiteralPath .venv)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Mevcut `.env` ve `.venv` korunur. Yerelde ayar dosyası yoksa kullanıcı
aşağıdaki komutla hazırlayabilir; mevcut dosyanın üzerine yazılmaz:

```powershell
if (!(Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe app.py
```

Editörde `SPEECH_KEY` alanına Azure Speech kaynağınızın anahtarını,
`SPEECH_REGION` alanına aynı kaynağın bölgesini girin. Örnekteki `eastus`
yerine gerektiğinde kendi bölgenizi kullanın. Ayarlardan sonra sunucuyu
yeniden başlatın. http://127.0.0.1:5000 adresini açın; `Ctrl+C` ile durdurun.
Sanal ortamı etkinleştirmek gerekmez. Import işlemi sunucuyu başlatmaz.

## Ortak yapılandırma ve sırayla çalışma

`speech_service.py`, dört konuşma işlemi için ortak yapılandırmayı
`Path(__file__).resolve().parent / ".env"` açık yolundan python-dotenv ile
yükler. `override=False` sayesinde mevcut ortam değişkenleri önceliklidir.
SDK `subscription=SPEECH_KEY`, `region=SPEECH_REGION` kullanır; endpoint
kullanılmaz. Ayarlar yalnızca konuşma isteğinde yüklenip doğrulanır.
Ana sayfa ve statik dosyalar eksik Azure ayarlarıyla da açılır.

Anahtarlar, kullanıcı metni ve ham SDK hataları istemciye veya loglara
aktarılmaz. Bu merge çözümünde gerçek `.env` okunmamış veya değiştirilmemiştir.

F0 üzerinde eşzamanlı istekleri önlemek için arayüzde bir işlem sürerken
tüm gönderim butonları devre dışı kalır. Sunucuda ortak kilit TTS, STT, çeviri ve telaffuz
SDK işlemlerini farklı istemcilerden gelseler bile sırayla çalıştırır.
Bu kilit tek Python süreci kapsamındadır: yerel uygulamayı tek süreçle
çalıştırın. Birden fazla worker/sunucu için ortak dış kuyruk gerekir.
Hata sonrasında kilit ve arayüz kontrolleri serbest bırakılır.

## TTS — metinden WAV

`POST /api/tts`, `application/json` olarak
`{"text":"Hello world","language":"en-US"}` kabul eder. Metin boş olmayan
string olmalı ve ham uzunluğu 1000 karakteri aşmamalıdır. Dil `en-US` veya
`tr-TR` olmalıdır. Başarı yanıtı `audio/wav` baytlarıdır; tarayıcıda
oynatılabilir ve `speech.wav` olarak indirilebilir.

SDK çıktı biçimi açıkça `SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm`
olarak seçilir: RIFF başlıklı, 16 kHz, 16-bit, mono PCM WAV. Azure sesi bu
biçimde üretir; mevcut 24 kHz sesin başlığını değiştirme veya yerelde yeniden
örnekleme yapılmaz. Önceki TTS branch'indeki 24 kHz seçimi birleşimde
16 kHz olarak düzeltildi. `scipy` kullanılmaz ve bağımlılıklara eklenmez.

`audio_config=None` ile sunucunun hoparlöründen ses çalınmaz. Her isteğin
`result.audio_data` baytları bellekte işlenir; ortak çıktı dosyası kullanılmaz.

## STT — WAV'dan metin

`POST /api/stt`, `multipart/form-data` olarak `audio` dosyası ve
`language` (`en-US` / `tr-TR`) alanını alır. Başarıda `{"text":"..."}` döner.

- Yalnızca klasik RIFF/WAVE, sıkıştırılmamış PCM (format kodu 1), signed
  16-bit, mono, 16.000 Hz desteklenir. Float, stereo, sıkıştırılmış ve
  WAVE_FORMAT_EXTENSIBLE dosyaları kabul edilmez; otomatik dönüştürme yoktur.
- En fazla 1 MiB (1.048.576 bayt) dosya ve 30 saniye PCM örneği kabul edilir.
  Multipart isteğinin tamamı için ek 64 KiB pay vardır.
- Uzantıya veya MIME bilgisine güvenilmez: RIFF boyutu, bölüm sınırları,
  fmt/data alanları, örnek hizalaması ve gerçek örnek süresi doğrulanır.
- Continuous recognition dosyadaki birden fazla ifadeyi işler; kesinleşmiş
  metin parçaları geliş sırasıyla birleştirilir. Dosya sınırı yine 30 saniyedir.

Doğrulanan ham PCM, isteğe özel `PushAudioInputStream` ile gönderilir;
WAV başlığı SDK akışına yazılmaz. Akış başarı ve hata sonrasında kapatılır.
Uygulama ortak veya geçici ses dosyası oluşturmaz.

TTS'den indirilen WAV dosyası biçim bakımından doğrudan STT'ye yüklenebilir.
Ancak uzun TTS kayıtları STT'nin 30 saniye / 1 MiB sınırlarını aşabilir ve
reddedilir. Uzun kayıtların tamamının kabul edileceği iddia edilmez.

## Speech Translation — konuşma çevirisi

`POST /api/translate`, `multipart/form-data` olarak `audio` WAV dosyası,
`source_language` ve `target_language` alır. İlk sürüm yalnızca şu eşleşmeleri
destekler; dil alanları ve eşleşmeleri sunucuda doğrulanır:

| Kaynak konuşma dili | Hedef metin dili |
| --- | --- |
| `en-US` | `tr` |
| `tr-TR` | `en` |

Başarı yanıtı:

```json
{
  "recognized_text": "Hello world",
  "translated_text": "Merhaba dünya",
  "source_language": "en-US",
  "target_language": "tr"
}
```

Azure Speech SDK `SpeechTranslationConfig` ve `TranslationRecognizer` kullanılır.
Aynı `SPEECH_KEY` / `SPEECH_REGION` ve ortak sunucu kilidi geçerlidir; ayrı API
anahtarı, çeviri servisi veya yeni Azure kaynağı gerekmez. Kaynak katmanı
değiştirilmez. Çeviri sesi üretilmez; kaynak konuşma ve hedef metin döndürülür.

STT ile aynı `validate_wav()` yardımcısı PCM 16-bit, mono, 16 kHz, en fazla
30 saniye / 1 MiB doğrulamasını yapar. WAV başlığı çıkarıldıktan sonra PCM
isteğe özel bellek akışıyla gönderilir. Continuous recognition, dosyanın
tamamındaki kesinleşmiş kaynak metinleri ve hedef çevirileri sırayla birleştirir.
Akış başarı/hata sonrasında kapatılır. Tanınmayan konuşma 422, hedef dilde
çeviri bulunmaması 502 döndürür; eksik sonuç başarı gibi sunulmaz.

Dil desteği **26 Ekim 2026** tarihinde güncel resmi Azure belgelerinden
doğrulandı: kaynak konuşma dili tam locale (`en-US`, `tr-TR`), hedef metin
dili kısa kod (`en`, `tr`) kullanır. Kaynak:
[Azure gerçek zamanlı konuşma çevirisi dil desteği](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=speech-translation#real-time-speech-translation).
SDK kullanımı: [konuşma çevirisi rehberi](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-translate-speech).

## Pronunciation Assessment — en-US telaffuz değerlendirmesi

Kendi İngilizce WAV kaydınızı ve okuduğunuz referans metni gönderin.
`POST /api/pronunciation`, `multipart/form-data` olarak şu alanları alır:

| Alan | Kural |
| --- | --- |
| `audio` | Mevcut ortak doğrulama: PCM 16-bit mono 16 kHz WAV, en fazla 30 saniye / 1 MiB |
| `reference_text` | Boş olmayan string; ham uzunluğu en fazla 500 karakter |
| `language` | Yalnızca `en-US` |

SDK `SpeechRecognizer` ve `PronunciationAssessmentConfig` kullanır.
`HundredMark`, `Word` granularity ve `enable_miscue=False` seçilir;
`apply_to(recognizer)` tanıma başlamadan çağrılır. Prosody/content açılmaz.
Continuous modda yalnızca kesinleşmiş sonuçlar toplanır; ilk duraklamada
dosyanın kalanı atılmaz. Mevcut timeout, iptal, callback ve temizlik yönetimi
ve ortak işlem kilidi kullanılır. TTS/STT/çeviri callback'leri varsayılan
parametreleriyle çalışmaya devam eder; yeni assessment hook'ları yalnızca
bu özellikte etkinleşir.

Resmi Python continuous assessment örneğinin yapılandırma, `apply_to`,
kesinleşmiş segment ve servis JSON'u yaklaşımı incelendi. Tüm kayıt puanını
birleştiren algoritma bu sürüme alınmadı; basit ortalama/formül kullanılmaz.
Referans ile metin benzerliğinden puan veya yerel Omission/Insertion etiketi
üretilmez. Puanların kaynağı Azure'un `NBest[0].PronunciationAssessment`
ve kelime ayrıntılarıdır. SDK 1.53.0'da `SpeechRecognitionResult.properties`
bir dict'tir; JSON `SpeechServiceResponse_JsonResult` anahtarından okunur.

### Sonuç şeması ve kapsam

| Alan | Anlamı |
| --- | --- |
| `language`, `reference_text`, `recognized_text` | Dil, gönderilen referans ve sıralı kesinleşmiş metin |
| `score_scale` | `100`; her gösterilen puan 0–100 aralığındadır |
| `session_complete` | Yalnızca oturum normal sonlanıp temizlik tamamlanırsa `true` |
| `scope` | Tek sonuçta `single_segment`, çok sonuçta `segments_only` |
| `overall_scores` | Her zaman `null`; tüm kayıt için toplam puan üretilmez |
| `segments` | Geliş sırasıyla segmentler; `index`, `text`, `scores`, `words`, `assessment_complete` |
| `segments[i].scores` | Azure'dan gelen `accuracy`, `fluency`, `completeness`, `pronunciation` |
| `segments[i].words` | Varsa `word`, `accuracy`, `error_type`; anlaşılır kelime tablosunda gösterilir |
| `assessment_complete` | Tüm segmentlerde dört puan mevcut ve tanınamayan bölüm yoksa `true` |
| `unassessed_segments` | NoMatch veya boş kesinleşmiş sonuç sayısı |
| `warnings` | Segment kapsamı ve eksik değerlendirme açıklamaları |

Tek segmentte de dört puan adlarıyla gösterilir; tüm referans/kayıt için
yeniden hesaplanmış toplam olduğu iddia edilmez. Çok segmentte her puan
kendi segmentinde kalır. `assessment_complete`, referansın tamamının doğru
okunduğu anlamına gelmez; yalnızca dönen değerlendirme alanlarının kapsamını
belirtir. Sessiz/hiç tanınmayan kayıt 422; kullanılabilir değerlendirme hiç
gelmezse veya geçersizse 502 döner. Bazı puanlar gelmezse `null` ve açık eksik
değerlendirme uyarısı gösterilir; 0 uydurulmaz. Azure gerçekten 0 döndürürse
korunur. Omission için geçersiz olan kelime accuracy puanı gösterilmez.
Timeout/servis hatasında segmentler kısmi başarı olarak döndürülmez.

Arayüzde referans ve sonuçlar `textContent` ile gösterilir. TTS WAV kaydı
yalnızca teknik biçim/servis denemesi içindir; kullanıcının kendi telaffuzunu
değerlendirdiğini göstermez. Kullanıcı kendi kaydını yüklemelidir.

Resmi kaynaklar (27 Ekim 2026 tarihinde incelendi):
[Microsoft Python continuous assessment örneği](https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/scenarios/python/console/language-learning/pronunciation_assessment.py),
[Pronunciation Assessment rehberi](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-pronunciation-assessment).

Pronunciation eklemesi sonrasında mevcut testler dahil **69 Python testi ve
7 arayüz mock testi geçti**. Çok segmentli sıra/kapsam, eksik puanlar, gerçek
sıfırın korunması, geçersiz referans/dil/WAV, sessizlik, timeout/iptal,
servis/uygulama-temizliği hataları ve kilit kontrol edildi. Bunlar SDK spec'leri
ve sentetik Azure JSON'u ile çevrimdışı testlerdir; gerçek değerlendirme veya
gerçek tarayıcı doğrulaması değildir. `.env` okunmadı ve Azure isteği yapılmadı.

## Arayüz ve hatalar

`GET /` aynı sayfada ayrı TTS, STT, Speech Translation ve Pronunciation Assessment bölümlerini sunar. DOM kimlikleri,
sonuç, hata ve bekleme alanları bölüm bazında ayrıdır. Yeni istekte ilgili
bölümün önceki sonucu temizlenir; başarısız istek eski sonucu göstermez.
Eski WAV/TXT object URL'leri bırakılır. STT metni `textContent` ile yerleştirilir;
kopyalanabilir veya UTF-8 TXT indirilebilir. Kopyalama için localhost/güvenli
bağlam ve tarayıcı izni gerekir; izin yoksa indirme veya elle kopyalama yapılabilir.

Çeviri bölümünde kaynak ve hedef dil seçilir; kaynak değişince karşı hedef dil
önerilir. Geçersiz eşleşmeler backend tarafından reddedilir. Tanınan orijinal
metin ve çeviri ayrı alanlara `textContent` ile yerleştirilir. Ortak gönderim
engeli dört bölümü de kapsar; hata sonrasında yeniden kullanım mümkündür.

Hata yanıtları `{"error":"..."}` biçimindedir:

| Durum | HTTP |
| --- | --- |
| Geçersiz JSON, metin/referans, dosya, biçim, süre veya dil | 400 |
| Dosya/istek boyut sınırı aşıldı | 413 |
| STT/çeviri konuşmayı tanıyamadı veya boş kaynak metin döndü | 422 |
| Azure ayarları eksik | 503 |
| Azure iptal, kimlik doğrulama, kota, bağlantı veya eksik çeviri sorunu | 502 |
| Beklenmeyen uygulama hatası | 500 |

## Mock testleri ve gerçek doğrulama

### Gerçek kullanıcı hatası ve continuous recognition düzeltmesi

Kullanıcı çok cümleli WAV ile `/api/translate` denemesinde yalnızca ilk
cümleyi aldı; ikinci cümle kayboldu. Örnek kayıt:
`Hello, the weather is very nice today. I'm going to the library.`
Neden, önceki `recognize_once_async()` kullanımının tek ifade sonrasında
bitmesiydi. Aynı kullanım `/api/stt` içinde de bulundu; iki akış birlikte düzeltildi.

Ortak `_continuous_pcm()` yardımcısı `recognized` olaylarından yalnızca
kesinleşmiş sonuçları toplar. `recognizing` ara sonuçları eklenmez;
ilk sonuç veya `speech_end_detected` durdurma nedeni değildir.
Normal tamamlanma yalnızca `session_stopped` ile doğrulanır. `canceled`
olayında `EndOfStream` normal dosya sonudur ve yine oturum bitişi beklenir;
servis hatası veya kullanıcı iptali hata döndürür. JSON yanıt alanları korunur.

Callback hataları güvenli hata olarak ana akışa aktarılır. Timeout, iptal,
eksik çeviri veya ilk cümleden sonraki servis hatası kısmi sonucu başarı olarak
döndürmez. Sessiz/hiç tanınmayan kayıt 422 döndürür.

`threading.Event` ile oturum tamamlanması en fazla 60 saniye beklenir.
Başlatma ve durdurma SDK future'ları, `.get()` timeout parametresi sunmadığı
için ayrı daemon iş parçacığında en fazla 5'er saniye beklenir. Takılı kalan
native future zorla sonlandırılamaz; HTTP akışı sonsuza kadar beklemez.
Her çıkışta ana işlem akışı durdurmayı ister ve sınırlı süreyle tamamlanmasını
bekler; ardından olay dinleyicilerini ayırır, açık kalan PCM akışını kapatır
ve ortak işlem kilidini serbest bırakır. Normal akışta PCM girişinin daha önce
kapatılması dosya sonunu (EOF) bildirir; temizlik adımından ayrıdır. Durdurma veya
temizlik hatası da başarı sayılmaz. SDK callback'i içinde durdurma beklenmez.

Bu değişiklik 30 saniye, 1 MiB, 16-bit mono 16 kHz PCM WAV yükleme
sınırlarını kaldırmaz. TTS üretim kodu ve 16 kHz WAV seçimi değiştirilmedi.

Bu hataya ilişkin gerçek kullanıcı bildirimi ile düzeltme testleri ayrıdır:
düzeltme gerçek Azure üzerinde denenmedi. Yeni olay tabanlı mock testleri iki
kesinleşmiş cümleyi, ara sonuçların tekrarlanmamasını, ilk sonuç sonrası hatayı,
sessiz kaydı, timeout/iptali, callback hatasını, kaynak temizliğini ve hata
sonrasında kilidin yeniden kullanılmasını doğrular.

Continuous recognition düzeltmesi sonrası **47 Python mock testi ve 5 arayüz
mock testi geçti**. Gerçek Azure ve gerçek tarayıcı doğrulaması yapılmadı.

### Speech SDK 1.53.0 temizlik hatası ve mock düzeltmesi

Gerçek kullanıcı denemesinde TTS 200 dönerken continuous çeviri 502 ve
"Azure tanıma işlemi güvenle tamamlanamadı" mesajını döndürdü. Çevrimdışı
olarak gerçek SDK `EventSignal` nesneleriyle doğrulanan neden:
`signal.disconnect(handler)` çağrısı `AttributeError` üretiyordu.
Speech SDK 1.53.0'da `disconnect` yoktur; desteklenen API `disconnect_all()`'dır.

Önceki test yardımcısı SDK'da bulunmayan `disconnect` metodunu elle tanımladığı
için yanlış çağrı mock testlerini geçiyordu. Yardımcı artık gerçek
`speechsdk.EventSignal` üzerinden `create_autospec(..., spec_set=True)`
kullanır; desteklenmeyen metotlar ve yanlış imzalar testte hata verir.
Gerçek `EventSignal` sınıfıyla da ağsız çok cümleli STT/çeviri regresyonu vardır.

Her `_continuous_pcm()` çağrısı kendi recognizer, PCM akışı ve dinleyicilerini
oluşturur; recognizer paylaşılmaz. Bu nedenle durdurma tamamlandıktan sonra
yalnızca o işleme ait sinyallerin `disconnect_all()` metodu çağrılır.
Başlatma veya dinleyici bağlama yarıda hata verse de sahip olunan kaynakların
temizliği denenir. Uygulama geçici ses dosyası oluşturmaz.

Asıl işlem/callback/timeout hatası varsa temizlik hatası onun nesnesini veya
traceback'ini değiştirmez. Ek temizlik sorunları `cleanup_failures` üzerinde
yalnızca aşama ve exception tipi olarak tutulur; ham SDK mesajları ve sırlar
istemciye veya loglara aktarılmaz. Asıl hata yokken temizlik başarısız olursa
yine güvenli hata döner; temizlik hatasını yutarak 200 üretilmez. Ortak kilit
dekoratördeki context manager tarafından başarı/hata çıkışında bırakılır.

Bu düzeltmenin testleri mock/çevrimdışı kontrollerdir; gerçek Azure isteği
yapılmadı ve `.env` içeriği okunmadı. Resmi API referansı:
[EventSignal ve disconnect_all](https://learn.microsoft.com/en-us/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.eventsignal?view=azure-python).

Temizlik düzeltmesi sonrasında **54 Python testi ve 5 arayüz mock testi geçti**.
Bu sayıya gerçek EventSignal sınıfıyla ağsız regresyon ve başarısız temizlikte
asıl exception/traceback'in korunması kontrolleri de dahildir.

### STT dosya sonunda canceled olayı: SDK yüzeyi farkı

Kullanıcı gerçek Azure denemesinde çok cümleli çevirinin çalıştığını, STT'nin
ise "Azure tanıma sonucu işlenemedi; kayıt tamamlanamadı" döndürdüğünü bildirdi.
Bu mesaj yalnızca `recognized` için değildir: ortak `guarded()` sarmalayıcısı
`recognized`, `canceled` ve `session_stopped` callback'lerini kapsar.

Kurulu SDK 1.53.0'ın gerçek STT sonuç/olay sınıflarıyla ağsız tanıda
`recognized` sonucu başarıyla işlendi. Hata `canceled()` içinde doğrulandı:

```text
AttributeError: 'SpeechRecognitionCanceledEventArgs' object has no attribute 'reason'
  speech_service.py, canceled(): if event.reason == ...
```

STT canceled olayında çeviri olayındaki doğrudan `reason` / `error_code`
kısayolları yoktur. İki tür de `event.cancellation_details.reason` ve
`event.cancellation_details.code` sunar. Yalnızca ortak canceled callback'i
bu alanlara geçirildi. Normal EOF hâlâ `session_stopped` bekler; gerçek
servis hatası veya iptal kısmi sonucu başarıya dönüştürmez.

STT sonucunda yanlışlıkla `translations` okunması söz konusu değildi:
`RecognizedSpeech` ve `TranslatedSpeech` ayrımı, hedef dil koşulu ve sıralı
birleştirme korunmuştur. TTS kodu ve çalışan çeviri üretimi değiştirilmedi.
Önceki ortak `SimpleNamespace` iptal mock'u her iki olayda da `reason` ve
`error_code` varmış gibi davrandığından hata testlerden kaçmıştı.

Artık sonuçlar/olaylar STT için `SpeechRecognitionResult` /
`SpeechRecognitionEventArgs` / `SpeechRecognitionCanceledEventArgs`, çeviri
için ayrı Translation karşılıklarından `spec_set=True` ile oluşturulur.
CancellationDetails da gerçek SDK yüzeyine bağlıdır. STT mock'unda
`translations`, iptal mock'unda doğrudan `reason` / `error_code` erişimi
AttributeError verir. Çok cümle → EOF → session_stopped, servis hatası ve
hata sonrası yeniden kullanım regresyonları iki türü ayrı sınar.

Bu düzeltme sonrası **56 Python testi ve 5 arayüz mock testi geçti**.
Tanı ve testlerde anahtar, `.env`, ses verisi veya kullanıcı transkripti
okunmadı/loglanmadı; gerçek Azure isteği yapılmadı. Kullanıcının gerçek
deneme bildirimi ile düzeltmenin çevrimdışı doğrulaması birbirinden ayrıdır.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node --test tests/test_ui.cjs
```

Node.js yalnızca bağımlılıksız arayüz mock testleri içindir; uygulamayı
çalıştırmak için gerekli değildir. Python testleri iki branch'in testlerini
korur. TTS'nin SDK'da 16 kHz çıktı biçimini seçmesi, STT biçim/süre kontrolleri,
başarı/hata yanıtları, ana sayfa/statik dosyalar ve ortak sunucu kilidi sınanır.
Mock TTS WAV yanıtı doğrudan STT route'una yüklenerek birleşik akış da kontrol edilir.
Arayüz testleri ortak gönderim engeli, ayrı sonuç/hata alanları, yeniden kullanım,
kopyalama, indirme ve object URL temizliğini sahte DOM/fetch ile doğrular.

Bu testler gerçek `.env` okumaz veya Azure çağrısı yapmaz. Mock WAV'ın
doğrudan yüklenebilmesi gerçek Azure TTS→STT doğrulaması değildir.
Gerçek tarayıcıda görsel/etkileşim kontrolü bu merge çözümünde yapılmadı.

Birleşim kontrol sonucu: 28 Python mock testi ve 3 Node.js arayüz mock testi
geçti. Kaynak dosyalarda merge işareti kalmadığı ve `.env.example` dosyasının
yok sayılmadığı kontrol edildi.

Part 4 çeviri eklemesi sonrasında mevcut testler dahil **39 Python mock testi
ve 5 Node.js arayüz mock testi geçti**. Yeni testler iki çeviri yönünü, SDK
yapılandırmasını, ortak WAV sınırlarını, geçersiz dil eşleşmelerini, tanınmayan
konuşmayı, eksik çeviriyi, güvenli servis hatalarını, akış temizliğini ve ortak
kilidi kapsar. Arayüz mock testleri de çeviri sırasında ortak gönderim engelini,
metinlerin ayrı gösterimini ve hata sonrası yeniden kullanımı kontrol eder.
Çeviri için gerçek Azure isteği veya gerçek tarayıcı testi yapılmadı.

Kullanıcının daha önce STT branch'inde yerelde yaptığı gerçek Azure denemesi
başarılıdır: Türkçe WAV doğru metne dönüştürülmüş; kopyalama, TXT indirme ve
hata sonrası yeniden kullanım kullanıcı tarafından doğrulanmıştır.
Birleşik uygulamada gerçek Azure TTS→WAV→STT denemesi henüz yapılmadı;
kullanıcı kısa bir kayıtla bu akışı yerelde doğrulayabilir.

`.env`, `.venv/`, `.test-deps/`, Python önbellekleri ve geçici sesler Git dışında
tutulur; `.env.example` izlenebilir. Mevcut sanal ortamı korumak için önceki
kontrollerde kullanılan `.test-deps/` normal çalıştırmada gerekli değildir.
`PROMPTS.md` iki branch'in istem geçmişini ve birleşim isteğini saklar.

SDK kaynakları: [ses üretimi ve çıktı biçimi](https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis),
[continuous recognition ve olaylar](https://learn.microsoft.com/python/api/azure-cognitiveservices-speech/azure.cognitiveservices.speech.speechrecognizer),
[ses akışları](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-use-audio-input-streams).
