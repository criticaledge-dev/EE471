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
