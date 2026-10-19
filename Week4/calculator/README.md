# EE471 Flask hesap makinesi

Mevcut `Calculator` sınıfının dört işlem metodunu kullanan web hesap makinesi. Hesaplamalar Python'da yapılır; JavaScript girdiyi, işlem ekranını ve API isteklerini yönetir.

## Kurulum ve çalıştırma

Windows için Python ve pip kurulu olmalıdır. PowerShell'de EE471 repo kökünden:

```powershell
cd .\Week4\calculator
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Sanal ortamı etkinleştirmek gerekmez. Tarayıcıda <http://127.0.0.1:5000> adresini açın. Sunucuyu durdurmak için `Ctrl+C` kullanın.

## Kullanım

- Örneğin `3`, `+`, `2` tuşları ekranda `3 + 2` gösterir; `=` ile API sonucundan gelen `5` görüntülenir.
- Sonuçtan sonra sayı girmek yeni işlem başlatır; operatör seçmek mevcut sonuçla devam eder.
- Temizle butonu veya `Esc` işlem durumunu ve ekranı sıfırlar.
- API hataları sayfada gösterilir.

## API

`GET /` HTML arayüzünü sunar.

`POST /api/calculate` için `Content-Type: application/json` kullanın. `operation`, `x` ve `y` zorunludur. İşlemler: `add`, `subtract`, `multiply`, `divide`. `x` ve `y` JSON sayıları olmalıdır; boolean ve sayısal metin kabul edilmez.

İstek:

```json
{"operation": "add", "x": 10, "y": 5}
```

Başarı yanıtı — HTTP 200:

```json
{"result": 15}
```

Sunucu çalışırken ayrı bir PowerShell penceresinde:

```powershell
$payload = @{ operation = 'add'; x = 10; y = 5 } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/calculate' -Method Post -ContentType 'application/json' -Body $payload
```

Sıfıra bölme isteği:

```json
{"operation": "divide", "x": 10, "y": 0}
```

Hata yanıtı — HTTP 400:

```json
{"error": "Sıfıra bölme yapılamaz."}
```

Geçersiz JSON, eksik alan, geçersiz işlem, sayısal olmayan veya boolean girdi ve sonlu olmayan sayılar da HTTP 400 ve `{"error": "..."}` döndürür.

## Kontroller

`Week4/calculator` içinden:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_app.py
.\.venv\Scripts\python.exe main.py
```

Mevcut `main.py` örneğinin çıktısı `10.0` olur. İstem ve düzeltme geçmişi `PROMPTS.md` içindedir. `.venv/`, `__pycache__/` ve `*.pyc` dosyaları yerel `.gitignore` ile Git dışında tutulur.
