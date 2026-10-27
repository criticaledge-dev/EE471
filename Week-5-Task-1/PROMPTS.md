# Speech Studio — İstem geçmişi

## Part 1 — TTS branch geçmişi

# Geliştirme istemi

```text
EE471 Week 5 Task 1 Part 1: Azure Text to Speech uygulamasını oluştur.

Önce AGENTS.md varsa oku ve aktif branch'i kontrol et.
Branch text-to-speech değilse dosya değiştirmeden dur.
Yalnızca Week-5-Task-1 klasörü içinde çalış.
Week3, Week4 ve diğer projeleri değiştirme.

Bu aşamada yalnızca çalışan TTS özelliğini geliştir.
STT, diarization, çeviri veya telaffuz değerlendirmesi ekleme.

Dosya yapısı:
Week-5-Task-1/
  app.py
  speech_service.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  PROMPTS.md
  templates/index.html
  static/style.css
  static/script.js
  tests/

Backend:
- Flask kullan; GET / ile index.html sun.
- POST /api/tts JSON kabul et:
  {"text":"Hello world","language":"en-US"}
- Azure Speech Python SDK ile gerçek ses üret.
- Dil seçenekleri en-US ve tr-TR olsun.
- Seçilen dil için uygun standart neural voice kullan;
  HD/özel ses gerektirme.
- Başarıda WAV dosyası baytlarını audio/wav yanıtıyla döndür.
- RIFF başlığı içeren PCM WAV çıktı biçimini açıkça seç.
- Ses üretimini speech_service.py içinde tut.
- Ses sunucunun hoparlöründen çalmasın; tarayıcıya gönderilsin.
- Mümkünse bellek içi çıktı kullan; ortak output.wav dosyası
  üzerinden istekleri birbirine karıştırma.
- Metin boş olmayan string olsun; en fazla 1000 karakter.
- Dil desteklenmiyorsa veya JSON geçersizse 400 ve
  {"error":"..."} döndür.
- Eksik yapılandırma için açıklayıcı JSON hata yanıtı ver.
- Azure iptal/kimlik doğrulama/kota/bağlantı hatalarında
  sahte başarı döndürme; kullanıcıya anlaşılır hata göster.
- Ham exception veya gizli bilgileri istemciye aktarma.
- Azure ayarları eksik olsa da ana sayfa açılabilsin.

Yapılandırma:
- requirements.txt içine flask, python-dotenv ve
  azure-cognitiveservices-speech ekle.
- .env dosyasını proje klasörüne göre açık bir yoldan yükle.
- Bu aşamada SpeechConfig için SPEECH_KEY ve SPEECH_REGION kullan.
- .env.example:
  SPEECH_KEY=
  SPEECH_REGION=eastus
- Gerçek .env oluşturma, mevcut .env içeriğini okuma/yazdırma.
- Anahtarı kod, HTML, JavaScript, log veya belgelerde gösterme.
- .gitignore: .env, .venv/, __pycache__/, *.pyc ve geçici sesler.
- .env.example izlenebilir kalsın.

Arayüz:
- Başlık: Speech Studio — Text to Speech.
- Metin alanı, dil seçimi ve Generate Speech butonu.
- Ses üretildiğinde audio controls ile oynatma.
- Üretilen WAV için indirme bağlantısı.
- Bekleme sırasında tekrar gönderimi engelle.
- Hata mesajını görünür bir alanda göster.
- Başarısız yeni istekte eski sesi yeni sonuç gibi sunma.
- Yenilenen sesler için eski object URL'lerini serbest bırak.
- Açık renkli, ortalanmış, maksimum genişliği sınırlı,
  dar ekranlarda taşmayan sade bir tasarım yap.
- API çağrısı yalnızca kendi Flask backend'ine yapılsın;
  tarayıcıya Azure anahtarı gönderme.

Doğrulama:
- Azure çağrısını mock ederek başarılı WAV yanıtını,
  geçersiz girdileri, eksik yapılandırmayı ve servis hatasını test et.
- Mock testlerini gerçek Azure bağlantı testi olarak tanımlama.
- Gerçek Azure isteği yapma; bunu kullanıcı yerelde deneyecek.
- Ana sayfa ve statik dosyaların sunulduğunu kontrol et.

README'ye PowerShell kurulum/çalıştırma adımlarını,
.env hazırlığını ve test komutunu ekle.
Bu istemi PROMPTS.md'ye kaydet.
Commit, push, merge veya branch işlemi yapma.
Bitince değişiklikleri ve test sonuçlarını özetle.
```

## Part 2 — STT branch geçmişi

# Geliştirme istemi

```text
EE471 Week 5 Task 1 Part 2: Azure Speech to Text uygulaması oluştur.

Önce AGENTS.md varsa oku.
Aktif branch speech-to-text değilse dosya değiştirmeden dur.
Yalnızca Week-5-Task-1 içinde çalış.

Bu branch, TTS geliştirmesinden önceki başlangıçtan geliyor.
main veya text-to-speech branch'inden dosya alma, merge yapma.
Bu aşamada yalnızca STT geliştir; TTS ekleme.

Dosya yapısı:
  app.py
  speech_service.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  PROMPTS.md
  templates/index.html
  static/style.css
  static/script.js
  tests/test_stt.py

Özellik:
- Flask GET / üzerinden Speech Studio — Speech to Text sayfası sun.
- Kullanıcı WAV dosyası yükleyip dil seçebilsin:
  en-US veya tr-TR.
- POST /api/stt multipart/form-data kabul et:
  audio: dosya
  language: dil
- Azure Speech Python SDK ile sesi metne dönüştür.
- Başarıda {"text":"..."} JSON yanıtı döndür.
- Bu sürüm kısa kayıtlar için olsun; tek seferlik tanımayı kullan
  ve yaklaşık 30 saniyelik/tek ifadeli kullanım sınırını README
  ve arayüzde açıkla.
- İlk sürümde mikrofon zorunlu değil; WAV yükleme yeterli.

Ses doğrulama:
- Desteklenen formatı açıkça sınırla:
  sıkıştırılmamış PCM WAV, 16-bit, mono, 16 kHz.
- Yalnızca dosya uzantısına güvenme; WAV başlığını doğrula.
- Dosya boyutuna ve süresine sunucuda sınır koy.
- Boş/eksik dosya, bozuk WAV, desteklenmeyen format veya dil
  için açıklayıcı JSON hata yanıtı ver.
- Konuşma tanınamazsa bunu başarılı metin sonucu gibi gösterme.
- Azure iptal/kimlik doğrulama/kota/bağlantı hatalarını yönet.
- Geçici dosya kullanırsan her istek için benzersiz olsun ve
  başarı/hata sonrasında temizlensin.

Yapılandırma:
- flask, python-dotenv, azure-cognitiveservices-speech kullan.
- Yerel .env dosyasını proje klasörüne göre yükle.
- SPEECH_KEY ve SPEECH_REGION kullan.
- Gerçek .env dosyasını okuma, değiştirme veya çıktılama;
  uygulama çalışırken dotenv üzerinden yüklenmesi yeterli.
- .env.example içine boş anahtar ve eastus bölgesi koy.
- .gitignore ile .env, .venv/, __pycache__/, *.pyc ve geçici
  ses dosyalarını Git dışında tut.
- Anahtarları istemciye veya loglara aktarma.
- Ayarlar eksik olsa da ana sayfa açılabilsin.

Arayüz:
- WAV seçme, dil seçimi ve Transcribe butonu.
- Bekleme, hata ve sonuç alanları.
- Sonuç metnini kopyalama ve TXT olarak indirme.
- İstek sürerken tekrar gönderimi engelle.
- Başarısız yeni istekte önceki metni yeni sonuç gibi gösterme.
- Kullanıcı metinlerini textContent ile yerleştir.
- Sade, açık renkli ve dar ekrana uyumlu tasarım kullan.

Testler:
- Azure çağrısını mock ederek başarı, tanınmayan konuşma,
  servis hatası ve geçersiz dosya/dil durumlarını kontrol et.
- Gerçek anahtarı okuma veya gerçek Azure isteği yapma.
- Mock testlerini gerçek Azure doğrulaması olarak sunma.
- Ana sayfanın ve statik dosyaların sunulduğunu kontrol et.

README'ye PowerShell kurulum/çalıştırma, desteklenen ses
formatı ve test komutlarını ekle.
Bu istemi PROMPTS.md'ye kaydet.
Commit, push veya merge yapma.
Sonunda değişiklikleri ve test sonuçlarını özetle.

Branch değişiminden kalan yerel .env ve .venv dosyaları var.
Önce Week-5-Task-1/.gitignore dosyasını oluşturup bunları
yok say. İçeriklerini okuma, silme veya Git'e ekleme.
Mevcut sanal ortamı koru.
```

## Gerçek Azure doğrulaması ve Part 3 entegrasyon notu istemi

```text
Yalnızca Week-5-Task-1 içinde README.md ve PROMPTS.md'yi güncelle.

Gerçek Azure STT denemesi başarılı:
Türkçe WAV doğru metne dönüştürüldü; kopyalama, TXT indirme
ve hata sonrası tekrar kullanım kullanıcı tarafından doğrulandı.

Entegrasyon notu:
TTS branch'inin mevcut WAV çıktısı 24 kHz, 16-bit, mono PCM.
STT 16 kHz, 16-bit, mono PCM kabul ediyor.
Part 3 birleşiminde TTS çıktı formatı 16 kHz PCM WAV olarak
ayarlanacak ve üretilen dosyanın doğrudan STT'ye yüklenmesi
test edilecek.

Bu aşamada STT davranışını değiştirme.
Diğer branch'lerden dosya alma ve merge yapma.
Dönüştürme denemesi için yerelde kurulan scipy'yi,
uygulama kullanmıyorsa requirements.txt'ye ekleme.
Commit veya push yapma.
```

## Part 3 — Merge çözümü ve 24 kHz → 16 kHz düzeltmesi

İki branch'in istemleri yukarıda korunmuştur. Birleşimde TTS SDK çıktı seçimi
`Riff24Khz16BitMonoPcm` yerine `Riff16Khz16BitMonoPcm` olarak değiştirildi;
sesin başlığı yeniden yazılmadı ve scipy eklenmedi. STT doğrulaması ve
30 saniye / 1 MiB sınırları korundu. Ortak yapılandırma ve ortak sunucu kilidi
ile iki özellik tek uygulamada birleştirildi.

```text
Git şu anda main üzerinde, speech-to-text merge işleminin
ortasında. Yalnızca Week-5-Task-1 içindeki merge conflict'lerini
iki özelliği koruyarak çöz.

Önce git status ve çakışan dosyaları incele.
Current/HEAD TTS, Incoming STT sürümüdür.
Gerekirse git show :2:dosya ve :3:dosya ile iki tarafın
orijinal içeriğini ayrı ayrı incele.

Çakışan dosyalar:
.gitignore
PROMPTS.md
README.md
app.py
speech_service.py
static/script.js
static/style.css
templates/index.html

Bir tarafı topluca seçme. Son uygulama şu özellikleri korusun:

1. Backend:
- GET / birleşik sayfayı sunsun.
- POST /api/tts metinden WAV üretsin.
- POST /api/stt WAV'dan metin üretsin.
- İki branch'in doğrulamalarını ve hata yönetimini koru.
- Ortak Flask uygulaması ve ortak yapılandırma kullan.
- Gerçek .env içeriğini okuma, değiştirme veya çıktılama.
- Uygulamanın çalışma sırasında dotenv yüklemesi devam etsin.
- Azure anahtarlarını istemciye veya loglara aktarma.

2. Ses uyumluluğu:
- TTS çıktı biçimini Speech SDK'nın
  Riff16Khz16BitMonoPcm seçeneğiyle açıkça ayarla.
- Çıktı gerçek RIFF başlıklı, 16-bit, mono, 16 kHz PCM WAV olsun.
- Yalnızca WAV başlığını değiştirme; sesi Azure'un doğru
  formatta üretmesini sağla.
- STT'nin mevcut WAV doğrulamasını koru.
- STT'nin 30 saniye sınırını arayüzde belirt:
  TTS'den gelen uzun kayıtların tamamının kabul edileceğini
  iddia etme.
- scipy'ye ihtiyaç yoksa uygulama bağımlılığı ekleme.

3. Arayüz:
- Aynı sayfada TTS ve STT için ayrı bölümler veya sekmeler olsun.
- TTS: metin, dil, üretim, oynatma ve WAV indirme.
- STT: WAV yükleme, dil, tanıma, kopyalama ve TXT indirme.
- DOM kimlikleri ve olay dinleyicileri çakışmasın.
- Her bölümün yükleniyor, sonuç ve hata durumunu ayrı yönet.
- Her iki bölüm en-US ve tr-TR seçeneklerini korusun.
- F0 üzerinde eşzamanlı istekleri önlemek için konuşma
  işlemlerini sırayla çalıştır.
- Hata sonrası kontroller yeniden kullanılabilir olsun.
- Yeni başarısız istekte eski sonucu yeni sonuç gibi gösterme.
- Sade ve dar ekrana uyumlu görünüm oluştur.

4. Belgeler ve Git:
- .gitignore kurallarını birleştir; .env, .venv, .test-deps,
  önbellekler ve geçici sesler yok sayılmaya devam etsin.
- .env.example izlenebilir kalsın.
- PROMPTS.md'de iki branch'in istem geçmişini koru;
  merge ve 24 kHz → 16 kHz düzeltmesini ayrıca kaydet.
- README'yi birleşik uygulamaya göre yeniden düzenle.
- Gerçek Azure doğrulaması ile mock test sonuçlarını ayır.

5. Doğrulama:
- İki branch'in testlerini koru ve birleşik yapıya uyarla.
- TTS çıktı formatı seçimini mock testinde doğrula.
- STT biçim kontrollerinin çalıştığını doğrula.
- Ana sayfada iki özelliğin de bulunduğunu kontrol et.
- Kaynak dosyalarda merge işaretleri kalmadığını kontrol et.
- Gerçek Azure çağrısı yapma.
- Tarayıcı kontrolü yapılamıyorsa açıkça belirt.

Merge'i abort etme. Commit, push veya git add yapma.
Sonunda dosya bazında neyin birleştirildiğini ve test
sonuçlarını açıkla. Stage işlemini kullanıcı yapacak.
```

## Part 4 — İlk aşama: konuşma çevirisi

```text
EE471 Week 5 Task 1 Part 4:
İlk aşamada yalnızca konuşma çevirisi ekle.

Aktif branch speech-extensions olmalı; değilse dur.
Önce mevcut birleşik TTS/STT uygulamasını ve testleri incele.
Yalnızca Week-5-Task-1 içinde çalış.

Mevcut TTS, STT ve 16 kHz WAV uyumluluğunu koru.
Bu aşamada diarization veya pronunciation assessment ekleme.

Backend:
- Azure Speech SDK TranslationRecognizer kullan.
- POST /api/translate multipart/form-data kabul et:
  audio: WAV dosyası
  source_language: en-US veya tr-TR
  target_language: tr veya en
- Kaynak ve hedef dil eşleşmelerini sunucuda doğrula.
- İlk sürümde İngilizce → Türkçe ve Türkçe → İngilizce destekle.
- Desteklenen dilleri güncel resmi Azure belgeleriyle doğrula.
- Mevcut PCM WAV doğrulamasını ortak yardımcı olarak kullan:
  16-bit, mono, 16 kHz; en fazla 30 saniye ve 1 MiB.
- Kısa kayıtlar için recognize_once_async kullan.
- Başarıda şu JSON biçimini döndür:
  {
    "recognized_text": "...",
    "translated_text": "...",
    "source_language": "...",
    "target_language": "..."
  }
- Tanınmayan konuşmayı, eksik çeviriyi ve Azure iptal/hata
  durumlarını açıklayıcı JSON hatalarına dönüştür.
- Çeviri mantığını speech_service.py içinde tut.
- Mevcut ortak işlem kilidini çeviri için de kullan.
- Kaynak katmanını değiştirme veya yeni Azure kaynağı oluşturma.
- Gerçek .env dosyasını inceleme veya çıktılama.
- Yeni bir API anahtarı veya ayrı çeviri servisi kullanma.

Arayüz:
- Mevcut iki bölüme Speech Translation bölümü ekle.
- WAV seçimi ve kaynak/hedef dil seçenekleri olsun.
- Tanınan orijinal metni ve çeviriyi ayrı göster.
- Bekleme, hata ve sonuç durumlarını yönet.
- Ortak gönderim engeli bu bölümü de kapsasın.
- Kullanıcı metinlerini textContent ile göster.
- Hata sonrası yeniden kullanım çalışsın.

Doğrulama:
- Azure çağrılarını mock et; gerçek Azure isteği yapma.
- Başarı, geçersiz WAV/dil, tanınmayan konuşma,
  eksik çeviri ve servis hatalarını test et.
- Mevcut TTS/STT testlerini yeniden çalıştır.
- Mock sonuçlarını gerçek Azure doğrulaması olarak sunma.

README ve PROMPTS.md'yi güncelle.
Commit, push veya merge yapma.
Sonunda değişiklikleri ve test sonuçlarını özetle.
```

## Part 4 düzeltmesi — Çok cümleli WAV ve continuous recognition

Gerçek kullanıcı hatası: çeviri yalnızca ilk cümleyi döndürüyordu. Neden,
STT ve çevirideki tek ifadeli `recognize_once_async()` kullanımıydı. İki akış
ortak continuous recognition yaşam döngüsüne geçirildi; TTS korunmuştur.
Düzeltme mock olaylarla sınanır; gerçek Azure doğrulaması yapılmamıştır.

```text
Yalnızca Week-5-Task-1 içinde, speech-extensions branch'inde çalış.

Gerçek kullanıcı testinde hata bulundu:
Çok cümleli WAV dosyasında /api/translate yalnızca ilk cümleyi
tanıyıp çeviriyor. İkinci cümle kayboluyor.
Örnek:
"Hello, the weather is very nice today. I'm going to the library."

Önce mevcut kodu incele. Tek seferlik recognize_once_async
kullanımını, dosyanın tamamını işleyecek continuous recognition
akışıyla değiştir.

Gereksinimler:
- TranslationRecognizer'ın recognized olaylarından yalnızca
  kesinleşmiş çeviri sonuçlarını topla.
- İlk recognized veya speech_end_detected olayında durma.
- Normal tamamlanmayı session_stopped ile takip et.
- Kaynak metin parçalarını ve hedef çevirilerini sıralarıyla
  birleştir; mevcut JSON yanıt sözleşmesini koru.
- recognizing içindeki geçici sonuçları nihai metne ekleyip
  tekrar oluşturma.
- canceled olayındaki normal bitiş ve servis hatasını ayır.
- Timeout veya servis hatasında kısmi sonucu tam başarı gibi sunma.
- Callback hatalarını ana işlem akışına aktar.
- Sınırlı bekleme ve threading.Event benzeri senkronizasyon kullan;
  sonsuz döngü veya sınırsız bekleme oluşturma.
- Her durumda tanımayı durdur, kaynakları temizle ve ortak
  işlem kilidini serbest bırak.
- SDK callback'i içinden durdurma sonucunu bloklayarak bekleyip
  deadlock oluşturma; durdurmayı ana akışta yönet.

Aynı tek-cümle sınırlamasını /api/stt için de incele.
STT de recognize_once_async kullanıyorsa WAV'ın tamamını
işleyecek aynı yaşam döngüsü yaklaşımına geçir.
TTS'yi değiştirme.

Mevcut 30 saniye, 1 MiB, PCM 16-bit mono 16 kHz sınırları
korunsun. Continuous recognition kullanılması bu dosya
sınırlarını kaldırmak anlamına gelmesin.

Mock testlerine ekle:
- İki ayrı kesinleşmiş sonuç + session_stopped:
  iki cümle de doğru sırada dönmeli.
- Geçici ve kesinleşmiş sonuçlar: tekrar oluşmamalı.
- İlk sonuçtan sonra hata: eksik metin başarı sayılmamalı.
- Sessiz kayıt, timeout ve iptal.
- Hata sonrası işlem kilidinin yeniden kullanılabilmesi.

README ve PROMPTS.md'ye gerçek hatayı, nedenini ve düzeltmeyi yaz.
Gerçek Azure testi yapma; mock testlerini açıkça ayır.
.env içeriğini okuma veya çıktılama.
Commit/push/merge yapma.
```

## SDK 1.53.0 — Temizlik API'si ve yanlış mock düzeltmesi

Gerçek neden, her işlem sonunda `EventSignal.disconnect(handler)` çağrısının
`AttributeError` üretmesiydi. Önceki mock bu olmayan metodu tanımladığı için
uyumsuzluğu gizledi. İşlem başına recognizer sahipliği doğrulandı; temizlik
`disconnect_all()` ile ve SDK yüzeyini doğrulayan spec tabanlı mock ile düzeltildi.
Asıl hata korunur, ek temizlik hataları güvenli aşama/tip bilgisi olarak tutulur.

```text
Yalnızca Week-5-Task-1 içinde, speech-extensions branch'inde çalış.

Doğrulanmış hata:
_continuous_pcm temizliğinde EventSignal.disconnect(handler)
çağrısı AttributeError oluşturuyor. Kurulu Speech SDK 1.53.0
bu metodu desteklemiyor; disconnect_all() destekliyor.

Önce recognizer ve olay dinleyicilerinin sahipliğini kontrol et:
- Her tanıma işlemi kendi recognizer nesnesini oluşturuyorsa,
  ilgili sinyallerin temizliğinde disconnect_all() kullan.
- Paylaşılan recognizer varsa diğer işlemlerin dinleyicilerini
  silme; önce recognizer'ı işlem başına bağımsız hâle getir.

Temizlik sırası:
- Önce tanımayı durdur ve durdurmanın tamamlanmasını bekle.
- Sonra olay dinleyicilerini kaldır.
- Ses kaynaklarını ve geçici dosyaları temizle.
- Ortak işlem kilidini finally içinde mutlaka bırak.
- Başlatma yarıda başarısız olsa da temizlik güvenli çalışsın.
- Asıl hata varsa temizlik hatası onun tanı bilgisini maskelemesin.
- Hataları yalnızca yutarak veya cleanup_failed kontrolünü
  kaldırarak başarı üretme.

Testleri düzelt:
- Mock EventSignal'dan SDK'da olmayan disconnect metodunu kaldır.
- Gerçek EventSignal yüzeyiyle uyumlu mock/spec kullan.
- Başarılı çok cümleli STT ve çeviri, temizliği de tamamlayarak
  başarı dönmeli.
- Başarı ve hata sonrasında kilit yeniden kullanılabilmeli.
- Mevcut timeout, iptal ve kısmi sonuç kontrolleri korunmalı.

README/PROMPTS.md'ye gerçek nedeni, yanlış mock'un neden
kaçırdığını ve düzeltmeyi kaydet.
Gerçek Azure isteği yapma; .env içeriğini okuma.
Commit/push/merge yapma.
```

## STT canceled callback — gerçek SDK olay yüzeyi düzeltmesi

Çevrimdışı gerçek SDK sınıflarıyla doğrulanan exception:
`AttributeError: 'SpeechRecognitionCanceledEventArgs' object has no attribute 'reason'`.
Hata recognized callback'inde değil, ortak guarded sarmalayıcısının çağırdığı
canceled callback'indeydi. STT sonucu doğru işleniyordu; normal dosya sonu
olayında çeviriye özgü kısayol alanı okunuyordu. Callback ortak
`cancellation_details.reason` / `.code` alanlarına geçirildi. Ayrı SDK result
ve event spec'leri, çok cümleli birleştirme ve hata sonrası kilit kullanımı sınandı.

```text
Yalnızca Week-5-Task-1 içinde, speech-extensions branch'inde çalış.

Gerçek Azure testinde:
- Çok cümleli çeviri çalışıyor.
- STT şu hatayı veriyor:
  "Azure tanıma sonucu işlenemedi; kayıt tamamlanamadı."

Önce bu mesajın üretildiği yolu bul.
STT recognized callback'inde yakalanan gerçek exception tipini
ve güvenli traceback'i belirle. Nedeni tahmin ederek değiştirme.

Özellikle incele:
- Ortak continuous yardımcı STT sonucundan yanlışlıkla
  translations gibi yalnızca çeviri sonucunda bulunan alanları
  okumaya çalışıyor mu?
- STT için RecognizedSpeech, çeviri için TranslatedSpeech
  sonuçları uygun şekilde ayrılmış mı?
- Mock sonuç nesneleri gerçek SDK sonuç yüzeyine uyuyor mu?

Anahtar, .env içeriği, ses verisi veya transkript loglama.
Çalışan çeviriyi ve TTS'yi koru.

Nedeni doğrularsan:
- Yalnızca ilgili sonuç işleme hatasını düzelt.
- STT ve çeviri için gerçek SDK yüzeyine uygun ayrı mock/spec
  kullanarak regresyon testi ekle.
- Çok cümleli STT'nin sıralı birleştirilmesini ve hata sonrası
  kilidin yeniden kullanılmasını kontrol et.
- README/PROMPTS.md'ye gerçek nedeni ve düzeltmeyi kaydet.

Gerçek Azure çağrısı yapma.
Commit/push/merge yapma.
Sonunda exception'ı, nedenini ve test sonuçlarını açıkla.
```

## Part 4 — Pronunciation Assessment

```text
Week 5 Task 1 Part 4: Pronunciation Assessment ekle.

Aktif branch speech-extensions olmalı.
Yalnızca Week-5-Task-1 içinde çalış.
Önce mevcut uygulamayı ve testleri incele.

Çalışan TTS, STT ve çeviriyi koru.
Diarization bu aşamada eklenmeyecek.

Özellik:
- Kullanıcı İngilizce referans metin girip kendi WAV kaydını
  yükleyerek Azure telaffuz değerlendirmesi alabilsin.
- İlk sürüm yalnızca en-US desteklesin.
- POST /api/pronunciation multipart/form-data kabul et:
  audio, reference_text, language.
- Mevcut WAV doğrulamasını kullan:
  PCM 16-bit mono 16 kHz, en fazla 30 saniye ve 1 MiB.
- Referans metin boş olmayan string, en fazla 500 karakter olsun.

Azure:
- Güncel resmi Microsoft Python örneklerini incele.
- SpeechRecognizer ile PronunciationAssessmentConfig kullan.
- Yapılandırmayı recognizer'a apply_to ile uygula.
- HundredMark değerlendirme sistemini kullan.
- Gerçek Azure değerlendirme sonuçlarını döndür;
  metin benzerliği veya uydurma puan kullanma.
- Prosody ve content assessment gibi ek özellikleri açma.
- Speech SDK 1.53.0'ın gerçek API yüzeyini doğrula;
  önceki hatalardaki gibi SDK'da olmayan metot/alan kullanma.
- Ortak yapılandırmayı ve işlem kilidini kullan.
- .env içeriğini okuma veya loglama.

Dosyanın tamamının işlenmesi:
- İlk duraklamada kalan sesi sessizce atlama.
- Çok parçalı değerlendirme için resmi continuous assessment
  örneğindeki yaklaşımı izle.
- Yalnızca kesinleşmiş sonuçları sırayla topla.
- Tek sonuç için mevcut accuracy, fluency, completeness ve
  pronunciation puanlarını göster.
- Çok sonuç varsa segment değerlendirmelerini koru.
- Tüm kayıt puanı hesaplayacaksan resmi belgelenmiş
  birleştirme yöntemini uygula; basit ortalama veya yeni
  formül uydurma. Güvenilir toplam üretilemiyorsa toplam
  yerine segment puanları göster ve kapsamını açıkla.
- Eksik değerlendirmeyi tam kayıt başarısı diye sunma.
- Desteklenmeyen/gelmeyen puanı 0 olarak uydurma.
- Timeout, iptal, sessiz kayıt, callback ve temizlik
  hatalarını yönet; kilidi her durumda bırak.
- Çalışan STT/çeviri callback davranışlarını bozma.

Arayüz:
- Ayrı Pronunciation Assessment bölümü ekle.
- Referans metin alanı, WAV yükleme, en-US bilgisi,
  değerlendirme butonu ve sonuç alanı olsun.
- Puanları adlarıyla ve 0–100 ölçeğiyle göster.
- Kelime değerlendirmeleri varsa anlaşılır bir tabloda sun.
- Yükleniyor ve hata durumları diğer bölümlerle tutarlı olsun.
- Referans metni ve sonuçları textContent ile yerleştir.
- TTS kaydı yalnızca teknik test için kullanılabilir;
  kullanıcının kendi telaffuzunu değerlendirdiğini iddia etme.

Test:
- Gerçek SDK yüzeyine uygun mock/spec kullan.
- Başarı, geçersiz referans/dil/WAV, sessiz kayıt,
  servis hatası ve kilit temizliğini test et.
- Çok sonuç varsa sıralamanın ve kapsamın korunduğunu doğrula.
- Mevcut bütün testleri çalıştır.
- Gerçek Azure çağrısı yapma.

README ve PROMPTS.md'yi güncelle.
Commit/push/merge yapma.
Sonunda değişiklikleri, sonuç şemasını ve testleri özetle.
```

## Part 4 — Gerçek zamanlı mikrofon diarization

```text
Week 5 Task 1 Part 4: Gerçek zamanlı diarization ekle.

Aktif branch speech-extensions olmalı.
Yalnızca Week-5-Task-1 içinde çalış.
Mevcut TTS, STT, çeviri ve pronunciation özelliklerini koru.
Azure Speech kaynağı kullanıcı tarafından S0'a geçirildi.

Önce mevcut mimariyi, testleri ve Microsoft'un Python
ConversationTranscriber örneğini incele.
Kurulu SDK 1.53.0'ın gerçek metot ve olay yüzeyini doğrula.
Önceki disconnect ve canceled event alanı hatalarını tekrarlama.

Canlı ses akışı:
- Tarayıcı mikrofonunu getUserMedia ile kullan.
- Başlat, Durdur ve dil seçimi olan Diarization bölümü ekle.
- İlk sürüm en-US desteklesin.
- Kullanıcı mikrofon izni vermeden kayıt başlatma.
- Ses konuşma sırasında backend'e aktarılsın.
- Kaydı bitirip tek WAV yüklemeyi canlı diarization diye sunma.
- Flask ile uyumlu WebSocket bağlantısı için Flask-Sock
  gibi küçük bir bağımlılık kullanılabilir.
- Azure anahtarını tarayıcıya gönderme.

Ses formatı:
- Tarayıcıdaki gerçek AudioContext sampleRate değerini dikkate al.
- Mono, 16-bit little-endian, 16 kHz PCM'e gerçekten dönüştür.
- Parçalar arasında sürekliliği koruyan resampling kullan.
- Yalnızca başlık veya sampleRate etiketi değiştirerek dönüştürme.
- AudioWorklet kullan; gerekiyorsa ayrı statik dosya ekle.
- Ham PCM'i Azure PushAudioInputStream'e aktar;
  her parçaya WAV başlığı ekleme.
- Sesin yerel hoparlöre geri verilerek yankı oluşturmasını önle.

Backend:
- Her oturum için bağımsız ConversationTranscriber oluştur.
- transcribing: geçici metin; transcribed: kesinleşmiş metin.
- speaker_id ve varsa offset/duration bilgilerini istemciye ilet.
- Unknown konuşmacı etiketini dürüstçe göster; ID uydurma.
- Geçici sonuçları güncelle; kesinleşmiş sonuçları tekrar
  üretmeden listeye ekle.
- SDK callback'lerinden WebSocket'e kontrolsüz eşzamanlı
  yazma yapma; kuyruk ve tek gönderici yaklaşımı kullan.
- Mikrofon oturumu boyunca mevcut ortak işlem kilidini koru.
- Diğer konuşma işlemleri bu sırada açıklayıcı busy yanıtı alsın.

Yaşam döngüsü:
- Oturumu en fazla 60 saniyeyle sınırla; otomatik durdur.
- Başarılı bağlantı/hazır sinyalinden önce ses gönderme.
- Kullanıcı Durdur dediğinde son ses parçalarını gönder,
  giriş akışını kapat ve son Azure sonuçlarını sınırlı süre bekle.
- İşlemin bittiği onaylanmadan başarı gösterme.
- İptal, timeout, mikrofon izni reddi, WebSocket kopması,
  sekmenin kapanması ve SDK hatalarında kaynakları temizle.
- Mikrofon track'lerini, AudioContext'i, stream'i ve
  dinleyicileri temizle; kilidi mutlaka bırak.
- Callback içinde bloklayarak stop bekleyip deadlock oluşturma.
- Kuyruk/ses tamponlarına sınır koy; sınırsız bellek tüketme.
- Yalnızca localhost geliştirme kullanımı hedefle;
  izin verilmeyen WebSocket Origin değerlerini reddet.

Arayüz:
- Dinleniyor, bağlanıyor, durduruluyor ve hata durumları.
- Geçici metin ile kesinleşmiş konuşmalar ayrı görünsün.
- Konuşmacıları tutarlı etiket ve renklerle ayır.
- Bunların gerçek kişi adı veya kalıcı kimlik olmadığını belirt.
- Metni textContent ile göster.
- Bağlantı kapanınca dinleme ve buton durumu doğru sıfırlansın.
- Sonuçlar Durdur'a basmadan önce ekrana gelebilmeli.

Testler:
- Gerçek SDK yüzeyine uygun spec/mock kullan.
- Ses formatı, parça sınırları ve süre dönüşümünü kontrol et.
- Geçici/kesin sonuç ayrımı ve konuşmacı etiketleri.
- Durdururken gelen son sonuçların korunması.
- Süre sınırı, bağlantı kopması ve hata sonrası kilit temizliği.
- Mevcut testlerin tamamı çalışmaya devam etsin.
- Gerçek Azure çağrısı veya mikrofon erişimi yapma.
- Mock testlerini gerçek canlı doğrulama olarak tanımlama.

requirements.txt, README ve PROMPTS.md'yi güncelle.
.env içeriğini okuma veya loglama.
Commit/push/merge yapma.
Sonunda mimariyi, çalıştırma komutunu, test sonuçlarını
ve gerçek tarayıcıda kontrol edilecek noktaları açıkla.
```

## Kullanıcı tarafından bildirilen canlı diarization manuel doğrulaması

```text
Yalnızca Week-5-Task-1 içindeki README.md ve PROMPTS.md dosyalarını güncelle.

Kullanıcı, gerçek tarayıcı/mikrofon ve Azure ile canlı diarization akışının düzgün çalıştığını ve mevcut özelliklerin çalışmaya devam ettiğini doğruladı. Bunu kullanıcı tarafından yapılan manuel doğrulama olarak kaydet; kendin gerçekleştirmiş gibi yazma. Ayrı ayrı bildirilmemiş test sonuçları ekleme.

Uygulama kodunu değiştirme. Commit, push veya merge yapma.
```
