# Week 5 Task 2 — İstem ve çalışma kaydı

## İlk aşama: proje temeli

```text
Week 5 Task 2’ye başlıyoruz. Aktif branch voice-calculator olmalı; farklıysa değişiklik yapmadan bildir.

İlk aşamada yalnızca proje temelini hazırla:

- Week4/calculator uygulamasını incele.
- Kaynak kodları Week-5-Task-2 içine kopyala; mevcut hesap makinesi davranışını ve görünümünü koru.
- .venv, .env, __pycache__, .test-deps ve üretilmiş/geçici dosyaları kopyalama.
- Week4 ve Week-5-Task-1 dosyalarını değiştirme.
- Yeni klasörde uygun .gitignore oluştur.
- README.md ve PROMPTS.md dosyalarını Task 2’ye göre düzenle. Önceki çalışmanın test sonuçlarını yeni çalışmada yapılmış gibi aktarma.
- Henüz sesli giriş veya sesli çıkış ekleme.
- Mevcut hesap makinesinin kopyada çalıştığını uygun kontrollerle doğrula.
- Commit, push veya merge yapma.

Sonuçta oluşturulan dosyaları, doğrulamaları ve PowerShell çalıştırma komutlarını bildir.
```

## Uygulama notları — 2026-10-27

- Aktif branch `voice-calculator` olarak kontrol edildi. AGENTS.md bulunmadı.
- Kaynak uygulamanın sekiz kod/bağımlılık/test dosyası açık bir listeyle kopyalandı. Toplu klasör kopyası yapılmadı; yerel ortamlar, gerçek `.env`, önbellekler ve geçici dosyalar alınmadı.
- Python, HTML, CSS ve JavaScript kaynakları değiştirilmedi. Task 2 için `.gitignore`, `README.md`, `PROMPTS.md` hazırlandı.
- Bu aşamada yalnızca hesap makinesi temeli vardır. Ses özellikleri eklenmedi.
- Önceki projenin istem ve test geçmişi bu çalışmanın sonucu olarak aktarılmadı.

## Bu kopyada yapılan doğrulamalar

- Task 2 klasöründe Python 3.13 / Flask 3.1.3 ile dört unittest metodu ve alt senaryolar geçti. API işlemleri, hatalı girdiler ve JSON, ana sayfa ve statik dosyalar kontrol edildi. Flask yalnızca proje dışındaki geçici test dizinine kuruldu.
- `main.py` çıktısı `10.0`; Node.js JavaScript sözdizimi kontrolü başarılı.
- Sekiz kopya dosyanın SHA256 değerleri kaynaklarıyla eşleşti. `.gitignore` örnek yollarla kontrol edildi.
- Gerçek tarayıcıda görsel veya etkileşimli doğrulama yapılmadı; önceki çalışmaların doğrulamaları bu sonuçlara dahil edilmedi.
- Git durumunda yalnızca yeni `Week-5-Task-2/` klasörü var. Week4 ve Week-5-Task-1 değiştirilmedi. Commit, push veya merge yapılmadı.

## İkinci aşama: Azure ile mikrofon üzerinden sesli giriş

```text
Week 5 Task 2: çalışan hesap makinesine Azure ile mikrofon üzerinden sesli giriş ekle.

Kapsam:
- Aktif branch voice-calculator olmalı.
- Yalnızca Week-5-Task-2 içinde değişiklik yap.
- Week4 ve Week-5-Task-1 dosyalarını değiştirme.
- Task 1 kaynaklarını tekrar kullanılabilecek yöntemler için inceleyebilirsin; Task 2 bağımsız çalışmalı.
- Mevcut hesap makinesi görünümünü, butonlarını, Calculator sınıfını ve hesaplama API’sini koru.
- Bu aşamada sesli çıkış ekleme.

Sesli giriş:
1. “Mikrofonu başlat” ve “Durdur ve işle” kontrolleri ekle.
2. Tarayıcı mikrofonundan kayıt al; izin, dinleme, işleme ve hata durumlarını göster.
3. Kaydı en fazla 15 saniye ile sınırla.
4. Task 1’deki AudioWorklet ve PCM dönüşüm yaklaşımından yararlan. Gerçek örnekleme hızını kullanarak 16 kHz, 16-bit, mono PCM üret ve doğru WAV başlığıyla paketle. Yalnızca başlık değerini değiştirerek dönüşüm yapma.
5. WAV dosyasını Task 2’nin Flask endpoint’ine gönder. Sunucu dosya biçimini, boyutunu ve süre sınırını doğrulasın.
6. Azure Speech SDK ile en-US konuşma tanıma kullan. Kaydın tamamını işle; Task 1’de düzeltilmiş continuous recognition ve SDK olay temizliği yaklaşımından yararlan.
7. Azure anahtarı yalnızca sunucuda, python-dotenv üzerinden SPEECH_KEY ve SPEECH_REGION ile yüklensin. Gerçek .env dosyalarını okuma, kopyalama veya loglama. .env.example ve ignore kurallarını hazırla.

Komutları işleme:
- Desteklenen kelimeler: zero, one, two, three, four, five, six, seven, eight, nine, point, plus, minus, times, over, is.
- Tanıyıcının sayıları “5” gibi rakamla döndürebileceğini de destekle.
- Büyük/küçük harf ve olağan noktalama farklarını normalleştir.
- “is” eşittir komutudur.
- “over” bölme, “times” çarpma komutudur.
- Örnekler:
  five plus two is → 7
  seven minus three is → 4
  three times two is → 6
  nine over three is → 3
  one point five plus two is → 3.5
- Ekranda tanınan özgün metni ve normalleştirilmiş işlemi göster.
- Desteklenmeyen kelime veya geçersiz komut dizisinde açıklayıcı hata ver. Anlaşılmayan kelimeleri atlayarak başka bir işlem hesaplama.
- Komutun tamamını doğrulamadan hesap makinesi durumunu değiştirme.
- eval kullanma.
- Sesli komutları mevcut butonların kullandığı ortak işlem akışına bağla. Ayrı bir hesaplama motoru oluşturma.
- Sıfıra bölme gibi mevcut hataları koru.

Kaynak yönetimi:
- İşlem sürerken tekrar başlatmayı engelle.
- Durdurma, hata ve sayfadan ayrılmada mikrofon kanallarını ve AudioContext kaynaklarını kapat.
- Hata sonrası yeniden deneme çalışmalı.

Doğrulama:
- Mevcut testleri çalıştır.
- Komut normalizasyonu ve ayrıştırması için dört zorunlu işlem, ondalık sayı, rakam biçimi, geçersiz kelime/dizi ve is komutunu doğrulayan anlamlı testler ekle.
- Azure testlerinde gerçek SDK yüzeyine uygun mock kullan.
- Mikrofon veya Azure ile yapılmamış testleri yapılmış gibi belirtme.
- README.md ve PROMPTS.md dosyalarını bu aşamaya göre güncelle.

Commit, push veya merge yapma.
Sonuçta değişiklikleri, test sonuçlarını, çalıştırma adımlarını ve gerçek tarayıcıda kontrol edilmesi gerekenleri bildir.
```

### Uygulama — 2026-10-27

- Branch yeniden `voice-calculator` olarak doğrulandı; değişiklikler Task 2 ile sınırlı tutuldu.
- `speech_service.py`, Task 1'den incelenen sıkı WAV doğrulaması ve düzeltilmiş continuous yaşam döngüsünün bağımsız en-US uyarlamasıdır. Sınırlar 15 saniye ve 1 MiB; gerçek SDK iptal alanları ve `disconnect_all()` kullanılır. NoMatch içeren kayıtta eksik komut hesaplanmaz.
- `app.py` içine multipart `/api/voice-input` ve güvenli hata yanıtları eklendi. Mevcut hesaplama fonksiyonu ve Calculator sınıfı korundu; sayfa Azure ayarları olmadan açılır.
- Mikrofon paneli ile `voice-input.mjs`, `voice-worklet.mjs`, `pcm-resampler.mjs`, `voice-audio.mjs`, `voice-command.mjs` eklendi. Gerçek hızdan PCM dönüşümü, WAV paketleme, tam komut doğrulaması ve mevcut tuş akışına yönlendirme yapılır. Sesli çıkış yoktur.
- `.env.example` boş anahtar/örnek bölge içerir; gerçek `.env` oluşturulmadı, okunmadı, kopyalanmadı ve loglanmadı. Ignore kuralları gizli ayarları ve ortamları dışlar; `.env.example` izlenebilir.
- Test bağımlılıkları yalnızca proje dışındaki geçici dizine kuruldu. Gerçek Azure veya mikrofon testi yapılmadı; kullanıcıdan henüz Task 2 için manuel doğrulama alınmadı.

### Sesli giriş doğrulama sonuçları

- Python 3.13 / Speech SDK 1.53.0 ile **15 Python testi geçti**: önceki dört hesap makinesi testi, beş örneğin gerçek Calculator/API sonuçları, WAV sınırları/bozuk başlıklar, çok parçalı kesin sonuçlar, EOF, sessizlik/NoMatch, servis hatası, timeout/iptal, callback/temizlik ve yarım başlangıç hataları, kilidin tekrar kullanımı, eksik ayarlar ve statik dosyalar.
- **12 Node.js testi geçti**: komut grameri ve normalizasyonu, dört işlem ve ondalık örneklerinin ortak API akışı, bilinmeyen kelimeyle durumun korunması, 16/44.1/48/96 kHz sentetik ses dönüşümü ve parça sürekliliği, mono/little-endian ve WAV başlığı, worklet kuyruk sonu/15 saniye sınırı/sessiz hoparlör çıkışı, taklit mikrofon izni/durdurma/sayfadan ayrılma, hata sonrası tekrar kullanım ve son parça timeout'u.
- `node --check static/script.js` başarılı. Test bağımlılıkları proje dışındaki geçici dizinden kullanıldı.
- Bunlar mock/sentetik kontrollerdir; **gerçek Azure çağrısı, gerçek mikrofon erişimi veya gerçek tarayıcı doğrulaması yapılmadı**. İlk aşamanın dört test sonucu yukarıda tarihsel kayıt olarak korunmuştur.
- Commit, push ve merge yapılmadı. Week4 ve Task 1 dosyaları değiştirilmedi.

## Sembollü sesli komut regresyonu — 2026-10-27

Kullanıcı, gerçek mikrofon/Azure denemesinde `6 - 2 is.` tanındığını ancak “Desteklenmeyen kelime var” hatası aldığını bildirdi; beklenen işlem `6 − 2 =`, sonuç `4` idi. Yalnızca Task 2 ayrıştırmasını düzeltme, işlem sembollerini kelimelere eşleme, mevcut kelime/rakam desteğini ve hesaplama akışını koruma istendi. Güvenli token normalizasyonu, ondalık/cümle noktası ayrımı, negatif/geçersiz komutları reddetme, tam doğrulamadan önce durumu değiştirmeme ve regresyon testleri şart koşuldu. Commit/push/merge yasaklandı.

### Doğrulanan neden ve düzeltme

- `voice-command.mjs` yalnızca işlem kelimelerini tanıyordu. Noktalama temizliği `-` sembolünü koruyor, ancak sembol kelimeye dönüştürülmediği için desteklenen token kontrolü isteği reddediyordu.
- Ayrı sembol token'ları `+` → `plus`, `-`/`−` → `minus`, `*`/`×` → `times`, `/`/`÷` → `over`, `=` → `is` olarak eşlendi. Bilinmeyen token'lar korunup reddedilir; negatif sayılar ve geçersiz işlem sıraları kabul edilmez.
- Sayısal ondalık noktalar korunur; cümle sonu noktası ayrılır. `.5`, `1..5`, `1.5.2` gibi desteklenmeyen/bozuk sayılar silme yoluyla geçerli bir sayıya dönüşmez.
- Mevcut Azure tanıma koduna, hesaplama akışına ve Calculator sınıfına dokunulmadı. Tüm komut doğrulanmadan hesap makinesi durumu değişmez.

### Bu düzeltmede çalıştırılan testler

- **15 Node.js testi geçti:** `6 - 2 is.` → `4`, `5 + 2 is.` → `7`, `3 × 2 is.` → `6`, `9 / 3 is.` → `3`, `1.5 + 2 is.` → `3.5` örneklerinin ayrıştırılması, ortak API istekleri ve mock yanıtların ekranda gösterilmesi; tüm sembol alternatifleri; önceki kelimeli komutlar; bilinmeyen kelimeler, negatif/geçersiz diziler ve durumun korunması.
- **15 Python testi geçti:** mevcut hesaplama/sesli giriş regresyonları; gerçek yerel Calculator/API üzerinde beş örneğin operandları ve ayrıca `6 − 2 = 4` kontrolü. Azure çağrıları ve dotenv yüklemesi mock edildi.
- Kullanıcının bildirdiği hata gerçek denemeden gelir. **Düzeltme sonrası yeni gerçek mikrofon veya Azure doğrulaması henüz yapılmadı.** Mock kontrolleri gerçek Azure doğrulaması değildir.
- Değişiklikler yalnızca Week-5-Task-2 içindedir; commit/push/merge yapılmadı.

## Sesli işlem sonucunun görünürlüğü

Kullanıcı, başarılı sesli komutta `Tanınan metin: 4 * 6 is.` korunurken `İşlem: 4 × 6 =` satırının `İşlem: 4 × 6 = 24` olarak gösterilmesini istedi. Bu bir görünürlük iyileştirmesidir; önceki görünüm hesaplama hatası değildir. Sonucun mevcut başarılı hesaplama yanıtından alınması, asenkron işlem bitmeden başarı gösterilmemesi, hata halinde eski sonuç/başarı mesajının kaldırılması ve Azure/ayrıştırma davranışının korunması istendi.

- `calculatorVoice.apply`, mevcut `calculate()` akışını bekleyip başarılı API yanıtından ekrana aktarılmış sonucu döndürüyor. Yeniden hesaplama veya ayrı hesaplama motoru eklenmedi.
- Sesli giriş paneli, başarılı yanıt geldikten sonra işlem satırına sonucu ekliyor. Yeni istekte önceki satır temizleniyor; hata halinde sonuç satırı boşaltılıyor ve başarı mesajı gösterilmiyor. Tanınan özgün metin hata incelemesi için korunabiliyor.
- Azure tanıma ve komut ayrıştırma kodları değiştirilmedi.
- `node --test test_voice.mjs test_voice_ui.mjs`: **17 test geçti**. Geciktirilmiş API yanıtını bekleme, `4 × 6 = 24`, sıfır sonucu, API'nin döndürdüğü değeri kullanma ve başarılı işlemden sonraki hatada eski sonucu kaldırma kontrol edildi.
- Bu testler taklit DOM/medya/API kullanır; bu iyileştirme için gerçek tarayıcı, mikrofon veya Azure doğrulaması yapılmadı. Commit/push/merge yapılmadı.

## Azure TTS ile sesli çıkış

Kullanıcı, yalnızca voice-calculator branch'inde Week-5-Task-2 içinde Azure Speech SDK ile sesli çıkış eklenmesini istedi. Week4/Task 1, Calculator sınıfı, hesaplama API'si, buton davranışları ve çalışan sesli giriş korunmalı; gerçek .env okunmamalı/kopyalanmamalı/loglanmamalı. Mevcut SPEECH_KEY/SPEECH_REGION kullanılmalı. Commit/push/merge yapılmamalı.

İstenen davranışlar: 0–9, point, plus/minus/times/over fiziksel butonlarda İngilizce okunmalı; eşittir başarılı mevcut hesaplama yanıtını bekleyip “is eight” gibi sonucu okumalı. Ses Azure'dan gelip tarayıcıda oynatılmalı; speechSynthesis veya ikinci hesaplama motoru kullanılmamalı. Ondalık/negatif/bilimsel gösterim politikası açık olmalı; başarısız hesaplamada sonuç sesi olmamalı. Görünür aç/kapat kontrolü ve sıralı/sınırlı kuyruk bulunmalı. Temizleme/kapatma/sayfadan ayrılmada eski sesler iptal edilmeli; geç yanıtlar oynatılmamalı, URL/kaynaklar temizlenmeli. TTS hatası sonucu bozmadan ayrı gösterilmeli. Mikrofon öncesinde TTS durmalı; programatik sesli giriş tuşları okunmamalı. İlgili mock testleri ve mevcut testler çalıştırılmalı, belgeler güncellenmeli.

### Kullanıcının yaptığı manuel doğrulama

Kullanıcı, sesli girişin ve “işlem = sonuç” gösteriminin gerçek tarayıcı/Azure ile çalıştığını doğruladı. Bu kullanıcı tarafından yapılmış manuel doğrulamadır; asistanın gerçekleştirdiği bir test değildir. Ayrı ayrı bildirilmemiş test sonuçları bu kayda eklenmedi. Bu bildirim yeni TTS özelliğinin doğrulaması değildir.

### Uygulama

- Aynı açık dotenv yolu ve ayarları kullanan `synthesize_speech` ve `/api/tts` eklendi. SDK 1.53.0, JennyNeural, RIFF 16 kHz/16-bit/mono WAV, bellek içi çıktı ve `audio_config=None` kullanılır. Konuşma işlemleri ortak kilidi paylaşır; hesaplama API'si bu kilidi beklemez.
- `tts-queue.mjs` / `tts-output.mjs`: varsayılan kapalı görünür kontrol, aktif dahil 12 öğelik tek üretici/oynatıcı kuyruğu, nesil bazlı iptal, istek iptali, eski yanıt kontrolü, URL/Audio temizliği ve ayrı hata alanı eklendi. Kuyruk dolunca yeni ses atlanır ve hata gösterilir. TTS hesap makinesi tuşlarını kilitlemez.
- Fiziksel buton olayları konuşmaya bağlandı; eşittir mevcut `calculate()` başarısını bekleyip API sonucunu kullanır. Programatik sesli komut akışı ve klavye seslendirilmez. Temizleme kuyruğu iptal eder; mikrofon izni öncesinde oynayan/bekleyen ses kesilir ve sesli giriş süresince engellenir.
- Sonuçlar İngilizce sayı adlarıyla okunur; kesir basamakları tek tek, negatif işaret “minus” olarak okunur. Mevcut gösterim korunur; bilimsel gösterim “times ten to the power of [minus] ...” biçiminde okunur. 15 basamaktan uzun düz tam sayılar rakam rakam okunur. Sonlu olmayan/geçersiz değerler seslendirilmez.
- Gerçek .env oluşturulmadı, okunmadı, kopyalanmadı veya loglanmadı. Bağımlılıklar değişmedi; Task 2 bağımsızdır.

### TTS aşamasında doğrulama

- **21 Python testi geçti:** önceki hesaplama/sesli giriş regresyonları ve altı yeni TTS testi; WAV/SDK biçimi ve sunucu hoparlörünün kapalı olması, doğru metnin SDK'ya gönderilmesi, geçersiz istekler, eksik ayarlar, Azure iptal/kimlik/kota/bağlantı ve native hataları, güvenli hata yanıtı, kilidin bırakılması ve tekrar kullanım kontrol edildi.
- **27 Node.js testi geçti:** önceki komut/sesli giriş/sonuç görünürlüğü testleri, tuş-ses sözlüğü, “is eight”, ondalık/negatif/bilimsel gösterim, tek hesaplama yanıtını bekleme, başarısız hesaplamada sonuç sesi üretmeme, sıralı ve sınırlı kuyruk, iptal sonrası geç yanıtları oynatmama, URL/oynatıcı temizliği, toggle ve sayfadan ayrılma, ses hatası sonrası kullanım ve mikrofon izninden önce TTS engelleme.
- SDK testleri gerçek sınıfların spec/autospec yüzeyini kullanır; dotenv ve Azure işlemleri mock edilir. Tarayıcı testleri taklit DOM/Audio/medya/ağ ile yapılır. **Yeni TTS için gerçek Azure veya gerçek tarayıcı doğrulaması yapılmadı.**
- Değişiklikler yalnızca Task 2 içindedir. Calculator sınıfı ve mevcut hesaplama API'sinin fonksiyon gövdesi korunmuştur. Commit/push/merge yapılmadı.

## Etkin TTS'de ses duyulmaması: inceleme ve güvenli tanılama

Kullanıcı, sesli çıkışı etkinleştirdiği halde butonlardan ses alamadığını bildirdi. Aç/kapat → fiziksel tıklama → kuyruk → Flask → geçerli ses → tarayıcı oynatma akışının incelenmesini, mikrofon/iptal durumlarının kontrolünü, neden kanıtlanmadan autoplay veya Azure ayarı varsayılmamasını istedi. Gerçek tarayıcı yoksa aşamaları ayıran güvenli durum/hata mesajları eklenmesi; hesaplama/sesli girişin korunması ve regresyon testi istendi. Çalışma yalnızca Task 2 ile sınırlı; gerçek .env/gizli değer erişimi ve commit/push/merge yasak.

- Kodda doğrulanan başlangıç uyumsuzluğu: kontrol işaretli kurulsa da `SpeechQueue.enabled=false` kalıyor, eşitleme yalnızca `change` olayında yapılıyordu. Kurulumda kutunun güncel durumu kuyruğa uygulanarak düzeltildi. Başlangıçta işaretli kutu / change olayı gelmemesi regresyonu eklendi. Bu durumun kullanıcının olayındaki kök neden olduğu **henüz doğrulanmadı**.
- Mevcut akışta buton dinleyicileri kuyruk metodunu çağırıyor, adaptör `/api/tts` isteği gönderiyor, kuyruk Audio.play çağırıyor ve mikrofon engeli başlangıçta false. Önceki tüm hata yolları tek genel mesajda birleştiğinden gerçek olayın hangi aşamada olduğu anlaşılamıyordu.
- Modül yükleme, açık/kapalı/mikrofon engeli, kuyruğa alma, HTTP isteği, doğrulanmış WAV bayt boyutu, oynatma başlatma/tamamlama için görünür durum satırı eklendi. HTTP kodu, geçersiz/boş WAV, ağ/timeout ve oynatma reddi ayrıldı. NotAllowedError ancak gerçekten bu hata alındığında gösterilir; raw exception/server gövdesi gösterilmez.
- `tts-response.mjs` yanıt MIME'ını, dosya sınırını, gerçek RIFF/chunk boyutlarını, fmt PCM 16 kHz/16-bit/mono yapısını ve dolu data bölümünü doğrular. Boş/bozuk yanıt oynatılmaz. Ses içeriği loglanmaz.
- **31 Node.js ve 21 Python testi geçti.** Taklit DOM ile fiziksel butondan gerçek kuyruk/adaptör üzerinden mock WAV'ın play çağrısına ulaşması, işaretli kutu başlangıcı, HTTP/bozuk ses/oynatma reddi ayrımı, iptal/mikrofon ve mevcut hesaplama/sesli giriş regresyonları kontrol edildi.
- Kullanılabilir gerçek tarayıcı aracı yoktu. Mikrofon, gerçek Azure veya fiziksel hoparlör denemesi yapılmadı. Mock başarıları gerçek sesin duyulduğuna kanıt olarak sunulmadı. Kullanıcıdaki kalan neden, yeni paneldeki son durum/hata ve yerel gerçek deneme ile ayrıştırılmalı.
- Değişiklikler frontend tanılaması/başlangıç eşitlemesi, ilgili testler ve belgelerle sınırlıdır. Azure tanıma, hesaplama ve komut ayrıştırma kodları değiştirilmedi. Gerçek .env okunmadı; commit/push/merge yapılmadı.

## Gerçek belirti: her tuşta kuyruk mesajında kalma

Kullanıcı, gerçek tarayıcıda sesli çıkış açık ve mikrofon kapalıyken tüm tuşlarda panelin “Tuş kuyruğa alındı” mesajında kaldığını ve ses çıkmadığını bildirdi. Enqueue → tüketici tetikleme, durum bayrakları, beklenen Promise/olay, mesaj ezilmesi ve yakalanmayan hata incelenmeli; yalnızca mesaj eklemekle yetinilmemeli. Gerçek başlangıç/olay bağlantılarıyla fiziksel 5 → TTS HTTP → başarılı mock ses → play doğrulanmalı; tüketici elle çağrılmamalı. Kapat/aç ve mikrofon başlat/durdur sonrası da akış korunmalı. .env/gizli değer erişimi ve commit/push/merge yasak.

### Doğrulanan neden

- `enqueue()` tüketiciyi gerçekten çağırıyordu. İlk engel enabled veya microphoneBusy değildi: `drain()` içindeki `this.setTimer(...)` çağrısıydı. Native `Window.setTimeout`, kuyruk nesnesinin metodu olarak saklanıp yanlış `this` ile çağrılıyordu.
- Yeni/boş profilli yerel **headless Chrome** üzerinde küçük bir yerel HTML denemesi aynı çağrıda **`TypeError: Illegal invocation`** üretti. Bu deneme Azure, mikrofon veya fiziksel ses aygıtı kullanmadı.
- Çağrı, Flask HTTP isteğinden ve öğeye ait `try/catch` bloğundan önceydi. Bu yüzden Promise reddi yakalanmıyor, son görünür mesaj kuyruk mesajı oluyordu. `running` dış finally ile sıfırlansa da `active` o hata yolunda temizlenmiyordu. Her yeni tuş aynı hatayı tekrar üretebiliyordu.
- Önceki Node testleri Node zamanlayıcılarını veya alıcı nesneyi kontrol etmeyen basit timer mock'larını kullandığından Window'un bu kısıtını kaçırdı. Mock başarıları tarayıcıda ses duyulduğuna kanıt değildir.

### Düzeltme

- Zamanlayıcılar küçük sarmalayıcılarla kuyruk nesnesi alıcı olarak aktarılmadan çağrılır. Controller/timer başlangıcı hata yakalama kapsamına alındı; tüketicinin dış Promise reddi de güvenli şekilde ele alınır.
- Çalışan tüketici varken yeni tuşun “kuyruğa alındı” mesajı, devam eden HTTP/oynatma durumunu artık ezmez.
- İptal, sıralı oynatma, sınırlandırılmış kuyruk, URL/Audio temizliği ve mikrofon engeli korundu. Hesaplama ve çalışan sesli giriş kodları değiştirilmedi.

### Regresyon doğrulaması

- **34 Node.js testi ve 21 Python testi geçti.** Node testleri Window benzeri `this` kısıtını, başlangıç hatasının yakalanmasını, running/active temizliğini ve ilerleme mesajının ezilmemesini kontrol eder. Mevcut hesaplama, sesli giriş, sıra, iptal ve kaynak temizliği regresyonları da çalıştırıldı.
- `check_tts_browser.py`, **gerçek uygulama HTML'i/modülleri, native Chrome zamanlayıcıları ve yerel Flask HTTP** ile çalıştırıldı. Gerçek DOM'da sesli çıkış açıldı ve fiziksel `5` tıklaması taklit edildi. Aynı kontrol kapat/aç ve gerçek mikrofon düğmesi başlangıç/durdurma olaylarından sonra tekrarlandı. Tüketici hiçbir adımda elle çağrılmadı.
- Sonuç: üç aşama da başarılı; **3 TTS HTTP isteği, 3 mock Audio.play çağrısı, sıfır JavaScript error/unhandledrejection**. Mikrofon düğmesi akışındaki mock komut gerçek hesaplama API'sinden `5 + 2 = 7` aldı; programatik tuşlar seslendirilmedi.
- Bu kontrol yerel headless Chrome'dur; Azure üretimi, mikrofon/AudioWorklet kaynakları ve Audio oynatıcısı mock'tur. Tarayıcı otomatik oynatma politikası testte izinli ayarlandı. Fiziksel hoparlörden gerçek Azure sesinin duyulması veya kullanıcının etkileşimli tarayıcısında son doğrulama **yapılmadı**.
- Çalışma yalnızca Task 2 içindedir; geçici boş Chrome profilleri `tmp/` altında ve Git dışında tutulur. Gerçek .env okunmadı; commit/push/merge yapılmadı.

## Sesli çıkış gecikmesi: sabit ses önbelleği

Kullanıcı, gerçek Azure/tarayıcı denemesinde sesin çalıştığını ancak tuş seslerinin gecikmeli geldiğini doğruladı. Bu manuel kullanıcı doğrulamasıdır. Yalnızca Task 2 içinde üretim/oynatma akışını inceleme, sabit kelimeleri önbelleğe alma, aynı metnin devam eden isteklerini paylaşma, isteğe bağlı düşük eşzamanlı hazırlama, kullanıcı tuşuna öncelik, dinamik sonuçlara kapasite politikası ve mevcut sıra/iptal/mikrofon/hesaplama davranışlarının korunması istendi. İstek ve oynatma kuyruğu süreleri metin/gizli bilgi kaydetmeden ölçülmeli; gerçek ölçüm olmadan gecikme azalması iddia edilmemeli. .env erişimi ve commit/push/merge yasak.

### İnceleme ve uygulama

- Önceki tüketici her öğe için önce `fetchAudio`, ardından oynatmanın bitişini bekliyordu. Tekrarlanan tuş yeniden HTTP isteği üretiyordu. Bu sıralama kodda doğrulandı; gerçek Azure gecikmesinin bileşenleri ölçülmedi, kesin darboğaz ilan edilmedi.
- `tts-cache.mjs` sabit 15 kelimenin başarılı WAV Blob'larını sayfa belleğinde saklar (toplam en fazla 2 MiB). Aynı metnin devam eden isteği tek Promise ile paylaşılır; başarısız/geç/iptal edilmiş yanıt saklanmaz. Dinamik sonuçlar tamamlandıktan sonra saklanmaz.
- Hazırlamada en fazla 12 benzersiz bekleyen iş ve bir HTTP isteği bulunur. İlk tuşu bekletecek otomatik ön hazırlama eklenmedi. Kullanılmamış kelime mevcut HTTP/oynatma akışına devam eder; tekrar kullanılan kelime yeniden Azure istemez. Oynatma sırası ve 12 öğelik sınır korundu.
- Kapatma/temizleme/mikrofon başlangıcı eski işleri iptal eder; geç yanıtlar oynatılmaz veya cache'e yazılmaz. Önceden başarılı sabit sesler saklanır; kaynak URL'leri oynatma sonunda temizlenir. Hesaplama bekletilmez. Azure ve hesaplama kodları değiştirilmedi.
- Panelde `performance.now()` tabanlı istek/önbellek bekleme ve oynatma sırası bekleme süreleri; HTTP, cache-hit ve paylaşılan istek sayaçları gösterilir. İstek süresi ağ/üretim/yanıt doğrulaması dahil uçtan uca ses hazırlama beklemesidir; sıra süresi enqueue'dan kendi isteğinin başlamasına kadardır. Ölçümlerde yalnızca sayılar vardır; kullanıcı metni, transkript, anahtar ve ses içeriği loglanmaz veya diske kaydedilmez.

### Kontroller ve sınırlar

- **40 Node.js testi ve 21 Python testi geçti.** Sabit seslerin tekrar kullanımı, aynı isteğin Promise paylaşımı, tek HTTP eşzamanlılığı, başarısız isteğin yeniden denenmesi, kapasite, geç yanıtın cache'e yazılmaması, cached sonucun iptalde oynatılmaması, sıra ve önceki hesaplama/sesli giriş kontrolleri çalıştırıldı.
- Kontrollü saat testinde istek bekleme ve sıra bekleme alanları ayrı doğrulandı (örnek sentetik süreler 40 ms istek, sonraki öğe için 90 ms sıra). Bu sayılar gerçek Azure ölçümü değildir.
- Headless Chrome, gerçek uygulama sayfası/modülleri/yerel Flask HTTP ile çalıştırıldı: **3 mock play, 1 TTS HTTP isteği, 2 cache kullanımı**, sıfır JavaScript hatası. Kapat/aç ve mikrofon düğmeleriyle başlat/durdur sonrasında aynı ses tekrar Azure/Flask isteği olmadan kullanıldı. Azure ve medya mock'tur; gerçek cihaz sesi veya Azure gecikme kazanımı ölçülmedi.
- Gerçek Azure'da gecikmenin azaldığı veya belirli bir hızlanma sağlandığı iddia edilmedi. Kullanıcı, son süreleri ilk kullanım ve tekrar kullanım arasında panelde karşılaştırabilir. .env okunmadı; commit/push/merge yapılmadı.
