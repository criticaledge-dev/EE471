# İstem kaydı

## Kullanıcı istemi

```text
EE471 reposunda yalnızca Week4/calculator içinde çalış.
Önce mevcut custom_classes.py ve main.py dosyalarını incele.

Mevcut Calculator sınıfını kullanarak Flask tabanlı bir web
hesap makinesi oluştur.

Tasarım referansı: Week4/design/calculator.png

Gereksinimler:
- app.py, requirements.txt, templates/index.html,
  static/style.css ve static/script.js oluştur.
- requirements.txt dosyasına flask ekle.
- Flask, GET / üzerinden HTML sayfasını sunsun.
- POST /api/calculate JSON kabul etsin:
  {"operation": "add", "x": 10, "y": 5}
- operation değerleri: add, subtract, multiply, divide.
- Başarıda HTTP 200 ve {"result": 15} döndür.
- Geçersiz JSON, eksik alan, geçersiz işlem, sayısal olmayan
  girdi ve sıfıra bölmede HTTP 400 ve {"error": "..."} döndür.
- Boolean değerleri sayı olarak kabul etme.
- Bütün hesaplamalar Python'daki Calculator metotlarında yapılsın.
- JavaScript yalnızca girdiyi, ekranı ve API isteklerini yönetsin.
- eval() kullanma.
- Arayüz tasarım görselindeki düzeni ve renkleri izlesin.
- API hatalarını sayfada görünür şekilde göster.
- main.py içindeki mevcut örnek kullanım çalışmaya devam etsin.
- Bu istemi PROMPTS.md dosyasına kaydet; yaptığın düzeltmeleri
  ayrıca belgeleyebileceğimiz bir bölüm bırak.
- Henüz commit veya push yapma.

Bitince değişiklikleri ve Windows PowerShell üzerinde
kurulum/çalıştırma komutlarını açıkla.
```

## Yapılan düzenlemeler

- `app.py`: HTML ve JSON API uçları, alan/tür/işlem doğrulaması ve HTTP 400 hata yanıtları eklendi. Hesaplamalar istek başına oluşturulan mevcut `Calculator` nesnesiyle yapılıyor.
- `requirements.txt`: `flask` bağımlılığı eklendi.
- `templates/index.html`, `static/style.css`: Tasarım referansının mavi zemini, beyaz ekranı, gri tuşları ve koyu mavi eşittir tuşu uygulandı. Küçük ekran desteği ve erişilebilir hata alanı eklendi.
- `static/script.js`: Ondalık giriş, klavye kullanımı, temizleme, ardışık API işlemleri ve görünür hata mesajları eklendi. Aritmetik hesaplama ve `eval()` kullanılmıyor.
- `custom_classes.py` ve `main.py` korundu.
- `test_app.py`: Sayfa/statik dosyalar, dört işlemin mevcut Calculator metotlarına yönlendirilmesi ve geçersiz API istekleri için unittest kontrolleri eklendi.

## Doğrulama

- Cygwin Python 3.9.16 ve geçici dizine kurulan Flask 3.1.3 ile `test_app.py` içindeki dört test metodu ve alt senaryolar geçti.
- `main.py` çalıştırıldı; çıktı `10.0`.
- Node.js ile JavaScript sözdizimi kontrolü geçti. Taklit DOM ve API yanıtlarıyla giriş, istek gövdesi, ardışık işlemler, hata gösterimi, hata sonrası devam etme ve ondalık giriş kontrol edildi.
- Gerçek tarayıcıda görsel kontrol yapılmadı.
- Commit veya push yapılmadı.

## Sonraki düzeltmeler ve notlar

<!-- Sonraki düzeltmelerin tarihini, gerekçesini ve doğrulama sonucunu buraya ekleyin. -->

| Tarih | Düzeltme | Gerekçe | Doğrulama |
| --- | --- | --- | --- |
| 2026-10-19 | Mavi arka planın tüm sayfayı kaplaması düzeltildi. `html/body` beyaz yapıldı; mavi yalnızca hesap makinesinin ana gövdesine uygulandı. | İlk uygulamada mavi renk kök elemana verilmişti ve hesap makinesi 560 px genişliğe kadar büyüyordu. Ana gövde 280 × 360 px temel ölçüye indirildi, sayfada ortalandı ve dar ekranlarda küçülecek şekilde düzenlendi. Temizleme ve hata alanı ana gövdenin dışında tutuldu. | CSS ölçüleri kontrol edildi: 8 px dış dolgu, 56 px ekran, 8 px aralık ve 280 px tuş ızgarası toplam 360 px yükseklik oluşturur. Gerçek tarayıcıda görsel kontrol yapılmadı. |
| 2026-10-19 | İşlem ifadesinin beyaz ekran yerine ayrı alanda gösterilmesi düzeltildi. Alttaki `#status` alanı kaldırıldı; ifade doğrudan beyaz ekranda gösteriliyor. | İlk uygulamada ekran yalnızca son girilen sayıyı gösteriyordu. Artık `0 → 3 → 3 + → 3 + 2 → 5` sırası izleniyor; son değer API yanıtından geliyor. Uzun ifadeler ekran içinde yatay kayıyor. | Taklit DOM/API ile örnek sıra, sonuç sonrası yeni sayı girişi, sonuçla devam, operatör değiştirme, temizleme, hata gösterimi ve uzun ifade kontrol edildi. API testlerinin dördü de geçti. |

Hesaplamalar Flask API'de kaldı; JavaScript yalnızca giriş/ifade ve arayüz durumunu yönetiyor. `eval()` eklenmedi. Bu düzeltmelerde commit/push yapılmadı.

### 2026-10-19 — Gövde ve tuş ölçülerinin açıkça sabitlenmesi

- Bildirilen hata: Hesap makinesi sayfa genişliğine yayılıyor, tuşlar aşırı büyüyordu.
- İncelenen HTML'de ekran ve tuş takımı `.calculator` içinde; hata ve temizleme alanları bu gövdenin dışında. Bu yapı korundu.
- CSS'de gövde `width: 100%` kullanıyor, yüksekliğini içerikten alıyordu. Tuşların `aspect-ratio: 15 / 16` kuralı genişlik arttığında yüksekliği de artırıyordu. Dış kapsayıcıda 280 px genişlik zaten bulunduğundan, yalnızca bu dosyalardan bildirilen tam sayfa genişlemesinin kesin nedeni doğrulanamadı; gövde ölçüleri doğrudan sınırlandırıldı.
- Geçici override eklenmeden mevcut kurallar değiştirildi: mavi gövde `border-box` ile 280 × 360 px, padding 8 px, grid satırları 56 ve 280 px, aralık 8 px olarak tanımlandı. Gövde ve dış kapsayıcı için flex büyümesi kapatıldı. Tuş takımı dört eşit satır/sütun kullanıyor; 280 px yükseklikte 8 px aralıklarla her satır 64 px. Tuşlardaki en-boy oranı ve viewport'a bağlı font kuralı kaldırıldı. Yazılar tuşlarda 28 px, ekranda 32 px kaldı.
- Beyaz sayfada ortalama korundu. Dar ekranlarda gövdenin genişliği mevcut alana sığacak şekilde sınırlandı; yüksekliği ve tuş satırları genişlikten bağımsız. Hata ve temizleme alanları 8 px aralıkla gövdenin altında ve aynı genişlik sınırında duruyor.
- JavaScript ve Python dosyaları değiştirilmedi; çalışan işlem davranışı korundu. Kullanılabilir tarayıcı aracı bulunmadığı için görsel doğrulama yapılmadı. CSS ölçüleri ve mantık dosyalarının SHA256 değerleri kontrol edildi. Commit/push yapılmadı.

## Ek ana istemler (özet)

1. Beyaz sayfa üzerinde yalnızca hesap makinesi gövdesinin mavi olması; 280 × 360 px referans boyutunun kullanılması; `3 → 3 + → 3 + 2 → 5` ifadesinin beyaz ekranda gösterilmesi istendi. Sonuç sonrası yeni sayı/operatör davranışı, temizleme ve görünür API hataları korunmalı; hesaplamalar API'de kalmalıydı. Bu iki gerçek hatanın düzeltmeleri yukarıdaki tabloda kayıtlıdır.
2. İşlem ekranı doğru çalıştığından JavaScript/Python'a dokunmadan görünümün düzeltilmesi istendi. Bildirilen genişleme için HTML/CSS incelendi; geçici override yerine mevcut kurallar değiştirildi. Sabit gövde, ekran, tuş satırları ve font ölçülerinin ayrıntıları yukarıdadır.
3. Hesap makinesi, Temizle butonu ve hata alanını içeren dış kapsayıcının yatay/dikey ortalanması istendi. `body` için `min-height: 100dvh`, flex ortalama ve 16 px padding; dış kapsayıcı için `flex: 0 0 auto`; kısa ekranlarda üst kısmın erişilebilirliği şart koşuldu.
4. Commit öncesinde `.venv`, `__pycache__` ve `*.pyc` yok sayma kurallarının doğrulanması, istem/düzeltme kayıtlarının kontrol edilmesi ve README'ye PowerShell kurulum/çalıştırma ile JSON API örnekleri eklenmesi istendi. Uygulama davranışı değişmemeli; commit/push yapılmamalıydı.

### 2026-10-19 — Dış kapsayıcının hizalanması

- `body` içindeki eski `100vh`/`100svh` tanımları `min-height: 100dvh` ile değiştirildi. `justify-content: center`, `align-items: center` ve açık `box-sizing: border-box` eklendi; margin 0 ve padding 16 px kullanıldı.
- `.calculator-shell` içindeki otomatik margin sıfırlandı; ortalama body'nin flex kurallarına bırakıldı. `flex: 0 0 auto` korundu. Dar ekranda body padding'ini 8 px yapan kural kaldırıldı.
- Sabit body yüksekliği kullanılmadığından kısa ekranlarda body içerikle uzayabilir; üst kısmın negatif taşmayla erişilemez hâle gelmesi önlenir. Temizle ve hata alanı ana gövdenin altında kaldı.
- Yalnızca CSS değişti; ölçüler, renkler, tuşlar ve işlem mantığı korunarak hizalama düzenlendi. Gerçek tarayıcıda görsel kontrol yapılmadı.

### 2026-10-19 — Commit öncesi belgeler ve Git kontrolü

- İlk kontrolde `.venv` kendi içindeki `.gitignore` ile yok sayılıyordu; `__pycache__` ve `*.pyc` için yerel kural eksikti. `Week4/calculator/.gitignore` içine üçü için de kurallar eklendi. Bu üretilen dosyaların Git tarafından izlenmediği kontrol edildi.
- Ana istem, gerçek arka plan/işlem ekranı düzeltmeleri ve sonraki boyut/hizalama düzenlemeleri kontrol edilip eksik kayıtlar tamamlandı.
- Yerel `README.md` oluşturuldu: PowerShell kurulum/çalıştırma komutları, test komutları, JSON istek, HTTP 200 sonuç ve HTTP 400 hata örnekleri eklendi.
- Bu aşamada yalnızca `.gitignore`, `README.md` ve `PROMPTS.md` değiştirildi. Uygulama davranışı değiştirilmedi; commit/push yapılmadı.
