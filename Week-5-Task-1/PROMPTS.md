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
