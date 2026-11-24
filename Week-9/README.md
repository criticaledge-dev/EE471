# EE471 Week 9 · Task 1

On demo, ödev PDF’sinin Task 1 girdileriyle PyTorch ve Transformers üzerinde çalışır. Her komut tek bir model yükler. Model fonksiyonları `task-1/demo.py` içinde CLI’dan bağımsızdır. Ödev PDF’i bu makinede `C:\Users\LENOVO\Downloads\Week-9-InClass-Exercise.pdf` konumundadır. [Hugging Face LLM Course](https://huggingface.co/learn/llm-course/chapter1/3?fw=pt).

Komutları Ubuntu/WSL’de çalıştırın. Mevcut ortamı kullanmak için:

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-9/task-1"
PY=/home/lenovo/hf-class/.venv/bin/python
mkdir -p output
PHOTO=../../Week-8/samples/cat_and_dog.jpg
WAV=../../Week-8/samples/speech_16000_hz_mono.wav
```

`PHOTO`, Google MediaPipe nesne tespiti örneğindeki [kedi ve köpek fotoğrafıdır](https://storage.googleapis.com/mediapipe-tasks/object_detector/cat_and_dog.jpg). `WAV`, Google MediaPipe’ın [İngilizce konuşma örneğidir](https://storage.googleapis.com/mediapipe-assets/speech_16000_hz_mono.wav) ve 4,27 saniye sürer. İki dosya bu makinede Week 8’den okunur. Başka bir ortamda aynı örnekleri yerel bir klasöre koyup değişkenlere yollarını verin. ViT JPEG/PNG, ASR en fazla 30 saniyelik PCM16 WAV kabul eder. WAV videoda bir oynatıcıyla açılabilir. ASR komutu transkript üretir ve isteğe bağlı TXT kaydeder.

Eksik yeni modelleri hazırlamak için `"$PY" -B prepare_models.py` çalıştırın. Yardımcı, altı ek model için gerekli yapılandırma, tokenizer ve bir ağırlık dosyasını alır. Varsa safetensors seçer. SmolLM2, ViT, Whisper ve Fransızca → İngilizce Marian modeli mevcut Ubuntu önbelleğinden yüklenir. Çeviri doğrudan model ve tokenizer API’siyle yapılır. Demo komutları çevrimdışı çalışır.

| Demo ve model kimliği | Kopyala ve çalıştır | Çıktı |
|---|---|---|
| Sentiment · `distilbert/distilbert-base-uncased-finetuned-sst-2-english` | `"$PY" -B cli.py sentiment_analysis` | İki cümle, etiket ve skor |
| Zero-shot · `MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33` | `"$PY" -B cli.py zero_shot_classification` | Üç aday ve sıralı skorlar |
| Generation · `HuggingFaceTB/SmolLM2-360M` | `"$PY" -B cli.py text_generation` | İki tam cümle ve ayrı kelime sayıları |
| Fill-mask · `distilbert/distilroberta-base` | `"$PY" -B cli.py fill_mask` | Önerilen kelime, doldurulmuş cümle ve skor |
| NER · `dslim/bert-base-NER` | `"$PY" -B cli.py ner > output/ner.json && cat output/ner.json` | Özgün metindeki varlıklar, türler, karakter aralıkları ve skorlar |
| QA · `distilbert/distilbert-base-cased-distilled-squad` | `"$PY" -B cli.py question_answering --ner-results output/ner.json` | Üç cevap, çıkarılan aralıklar ve NER ile eşleşme |
| Summary · `google-t5/t5-small` | `"$PY" -B cli.py summarization` | Tam paragraf ve model özeti |
| Translation · `Helsinki-NLP/opus-mt-fr-en` | `"$PY" -B cli.py translation` | “Ce cours est produit par Hugging Face.” ve İngilizce çevirisi |
| ViT · `google/vit-base-patch16-224` | `"$PY" -B cli.py image_classification "$PHOTO"` | Fotoğraf ve üç skor `output/vit-top3.png` içinde |
| ASR · `openai/whisper-large-v3` | `"$PY" -B cli.py asr "$WAV" --output transcript.txt` | Terminalde transkript ve `output/transcript.txt` |

QA karşılaştırması için NER satırını önce çalıştırın. Karşılaştırma aynı bağlamda tür ve karakter aralığıyla yapılır. Böylece kurum adındaki `Izmir` ile bağımsız şehir adı `İzmir` ayrı kalır. Generation tam ilk cümleyi seçer ve yarım ya da 35 kelimeyi aşan adayları atar. Sayım başlangıç dahil, boşlukla ayrılan kelimeler üzerinden yapılır.

Doğrulama ortamı Ubuntu’da Python 3.14.4, CPU PyTorch 2.15.0 ve Transformers 5.24.0 kullanır. Ortamı yeniden hazırlamanız gerekirse aynı Ubuntu yorumlayıcısıyla `"$PY" -m pip install -r requirements.txt` çalıştırın. Xet aktarımı zaman aşımına uğrarsa `HF_HUB_DISABLE_XET=1 "$PY" -B prepare_models.py` ile standart HTTP aktarımını deneyin.

Her video için ilgili komutu önceden çalıştırın. İlk 3 saniyede komutu veya girdiyi gösterin. Sonraki 12 saniye içinde sonucu gösterirken aşağıdaki cümleyi okuyun. ASR videosunda ilk 5 saniyede konuşma örneğini dinletin ve sonraki 10 saniyede transkripti gösterin. Windows’tan ViT PNG ve ASR TXT dosyalarını `Week-9\task-1\output\` içinde açabilirsiniz.

| En fazla 15 saniyelik AVI | Ekranda aç | Okunacak cümle |
|---|---|---|
| `Task1_sentiment_analysis.avi` | İki cümle ve JSON etiketleri | “Model iki cümlenin duygu etiketini ve skorunu veriyor.” |
| `Task1_zero_shot_classification.avi` | Berkshire metni, üç aday ve sıralama | “Model Berkshire cümlesini verilen üç konu arasında sıralıyor.” |
| `Task1_text_generation.avi` | Başlangıç, iki tam cümle ve kelime sayıları | “SmolLM2 aynı başlangıcı 35 kelimeyi aşmayan iki farklı cümleyle tamamlıyor.” |
| `Task1_fill_mask.avi` | Boşluklu girdi ve tamamlanan cümle | “Model boşluk için bir kelime öneriyor ve onu cümleye yerleştiriyor.” |
| `Task1_ner.avi` | Nate bağlamı ve varlık aralıkları | “NER kişi, kurum ve konumları metindeki yerleriyle gösteriyor.” |
| `Task1_question_answering.avi` | Üç cevap ve NER eşleşmeleri | “QA isim, kurum ve şehir cevaplarını bağlamdan çıkarıyor ve NER ile karşılaştırıyoruz.” |
| `Task1_summarization.avi` | Girdi paragrafı ve gerçek özet | “T5 finans krizi paragrafını daha kısa bir metne dönüştürüyor.” |
| `Task1_translation.avi` | Terminalde “Ce cours est produit par Hugging Face.” ve İngilizce çıktı | “Marian modeli bu Fransızca cümleyi İngilizceye çeviriyor.” |
| `Task1_image_classification.avi` | `output/vit-top3.png` | “ViT bu fotoğraf için en yüksek üç ImageNet etiketini ve skorunu gösteriyor.” |
| `Task1_asr.avi` | Kaynak WAV oynatıcısı ve terminalde transkript | “Whisper kısa WAV kaydındaki konuşmayı yazıya dönüştürüyor.” |

## 23 Kasım 2026 gerçek model sonuçları

Doğrulama `/home/lenovo/hf-class/.venv/bin/python` ile Ubuntu’da CPU üzerinde ve çevrimdışı gerçekleştirildi. İlk Task 1 çalıştırmasında **10/10 demo geçti** ve `pip check` bağımlılık hatası bulmadı. Çeviri maddesi güncellendiğinde yalnız çeviri demosu yeniden çalıştırıldı.

| Demo | Ölçülen sonuç |
|---|---|
| Sentiment | Birinci cümle `NEGATIVE` 0,9880, ikinci cümle `NEGATIVE` 0,9995. İki etiket de modelin gerçek çıktısı. |
| Zero-shot | Finance %99,8663, sports %0,0708, technology %0,0630 |
| Text generation | İki farklı tam cümle. Başlangıç dahil 26 ve 35 kelime |
| Fill-mask | `AI`, skor 0,5665. “To understand generative AI, one must study AI well.” |
| NER | `Nate` (PER), `Izmir Institute of Technology` (ORG), `İzmir` (LOC). Model ayrıca `Türkiye` adını `T` ve `ürkiye` şeklinde iki LOC parçası olarak etiketledi. |
| QA | `Nate`, `Izmir Institute of Technology` ve `İzmir`. Üçü de NER ile aynı karakter aralığında. |
| Summarization | 85 kelimelik paragraftan 27 kelimelik özet. Model krizin ciddiyetini ve subprime mortgage piyasasındaki başlangıcını korudu. |
| Translation | “Ce cours est produit par Hugging Face.” → “This course is produced by Hugging Face.” |
| ViT | Egyptian cat %66,9076, tabby %10,3400, tiger cat %4,9987. PNG’de fotoğraf ve üç skor kontrol edildi |
| Whisper | 4,2725 saniyelik WAV’dan “Send a text to Mike. I'll be home late tomorrow.” Terminal ve TXT aynı transkripti içerir |

Transformers 5’te extractive QA pipeline’ı kaldırıldığı için DistilBERT modelinin başlangıç ve bitiş skorları doğrudan karşılaştırılır. Cevaplar özgün bağlamın karakter aralıklarından çıkarılır. T5 ve Marian için doğrudan model/tokenizer API’si kullanılır. Sonuç kontrolleri, cümlelerin 35 kelime sınırını, QA aralıklarını, ViT PNG’sindeki fotoğraf piksellerini ve Whisper TXT ile terminal transkriptinin eşitliğini doğruladı.

## Task 3 · Yerel Gradio uygulaması

`task-3/inference.py` içindeki `TransformerDemos` sınıfı on public metodu Task 1’in model fonksiyonlarına bağlar. Sınıf girdi doğrulamasını ve tek seferde bir CPU işlemini yönetir. Gradio bütün düğmeleri aynı kuyruğa bağlar. Bir düğmeye basılınca yalnız ilgili model önbellekten yüklenir. İstek sona erdiğinde sınıf model nesnesini saklamaz. [Hugging Face Chapter 2](https://huggingface.co/learn/llm-course/chapter2/1).

Ubuntu/WSL’de şu komutları çalıştırıp Windows tarayıcısında [127.0.0.1:7860](http://127.0.0.1:7860) adresini açın.

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-9/task-3"
PY=/home/lenovo/hf-class/.venv/bin/python
"$PY" -m pip install -r requirements.txt
"$PY" -m pip check
"$PY" -B app.py
```

Uygulama loopback üzerinde `share=False` ile çalışır. `Ctrl+C` ile durdurabilirsiniz. Port doluysa `--port 7861` ile başka bir yerel port seçebilirsiniz. Gradio geçici dosyaları varsayılan olarak `task-3/output/gradio-cache/` altında tutar.

Task 1’in [kedi ve köpek fotoğrafı](https://storage.googleapis.com/mediapipe-tasks/object_detector/cat_and_dog.jpg) ile [İngilizce WAV örneği](https://storage.googleapis.com/mediapipe-assets/speech_16000_hz_mono.wav), yerel `Week-8/samples/` klasöründe bulunduğunda başlangıçta görünür. Temiz klonda bağlantılardaki dosyaları bilgisayarınıza kaydedip ilgili sekmeden yükleyin. Başlangıçta seçili gelmeleri için `"$PY" -B app.py --photo "/yerel/yol/cat_and_dog.jpg" --wav "/yerel/yol/speech_16000_hz_mono.wav"` komutunu kullanabilirsiniz. WAV oynatıcısındaki Play düğmesi kaynak kaydı çalar. Whisper metin sonucu verir.

### Task3.avi çekim akışı · 4 dakika 45 saniye

| Süre | Ekranda gösterilecek işlem |
|---|---|
| 0:00–0:20 | **Sentiment.** İki satırı ve modelin etiket ile skorlarını göster. |
| 0:20–0:40 | **Zero-shot.** Berkshire metnini, düzenlenebilir adayları ve finance skorunu göster. |
| 0:40–1:05 | **Generation.** İki tamamlamayı ve her cümlenin kelime sayısını göster. |
| 1:05–1:20 | **Fill-mask.** `[…]` boşluğunu ve doldurulmuş cümleyi göster. |
| 1:20–1:40 | **NER.** Nate, kurum adı ve şehir için varlık türlerini göster. |
| 1:40–2:00 | **QA.** Üç düzenlenebilir soruyu ve bağlamdan çıkarılmış cevapları göster. |
| 2:00–2:20 | **Summarization.** Özgün paragrafı ve kısaltılmış çıktıyı göster. |
| 2:20–2:40 | **Translation.** Verilen Fransızca cümleyi çalıştır ve İngilizce sonucu göster. |
| 2:40–3:00 | **Görsel.** Fotoğrafı ve ViT’nin üç skorunu göster. |
| 3:00–3:30 | **Ses.** Kısa WAV’ı oynat, sonra Whisper transkriptini göster. |
| 3:30–4:10 | **OOP kodu.** `inference.py` içindeki `TransformerDemos` ve `serialized` bölümlerini aç. Bir public metodun Task 1 fonksiyonuna nasıl ulaştığını anlat. |
| 4:10–4:45 | **Gradio bağlantısı.** `app.py` içindeki `build_app`, `bind` ve `launch` çağrılarını göster. Sekme, düğme, sonuç ve ortak kuyruk arasındaki bağlantıyı açıkla. |

Headless tarayıcı kontrolünü tekrarlamak için çalışan uygulamanın yanında ikinci bir Ubuntu terminalinde aşağıdaki komutları kullanın. Playwright yalnız bu kontrol için gerekir.

```bash
PY=/home/lenovo/hf-class/.venv/bin/python
"$PY" -m pip install playwright==1.65.2
"$PY" -m playwright install chromium --only-shell
"$PY" -B verify_browser.py
```

Kontrol, yukarıdaki iki örnek dosyayı kullanır. Bu WSL kurulumunda eksik `libnspr4`, `libnss3` ve `libasound2t64` paketleri `apt download` ile alınıp `output/browser-deps/root` altına çıkarıldı. Bu yerel test kütüphaneleri için `LD_LIBRARY_PATH="$PWD/output/browser-deps/root/usr/lib/x86_64-linux-gnu" "$PY" -B verify_browser.py` komutunu kullanabilirsiniz. Uygulama başlatmak için Chromium gerekmez.

23 Kasım 2026 doğrulamasında Chromium’da gerçek düğmelerle **10/10** işlem geçti. Sentiment, zero-shot, generation, fill-mask, NER, QA, summarization ve translation sonuçları sayfada kontrol edildi. JPG ve WAV arayüzden yeniden yüklendi. Fotoğraf çözümlenip gösterildi ve ViT üç etiketi ekrana yazdı. Play ile WAV sayacı `0:00`’dan `0:01`’e ilerledi. Whisper transkripti ekranda görüldü. Tarayıcı sessiz headless modda çalıştığı için fiziksel hoparlör kontrolü yapılmadı.

Torch, Task 1’deki dört CPU iş parçacığı ayarını kullandı. Sunucunun RSS değeri ilk model çağrısından önce yaklaşık 157 MiB idi. Whisper sırasında tepe RSS 9,49 GiB, Whisper tamamlandığında ve ardından düzenlenen `Bonjour.` girdisi `Hello.` olarak çevrildiğinde yaklaşık 0,94 GiB ölçüldü. Bunlar bu örnek girdilerle ölçülen süreç değerleridir. Task 1’in **10/10 CLI komutu** ayrıca yeniden çalıştırıldı ve önceki JSON sonuçlarıyla eşleşti. `pip check` bağımlılık hatası bulmadı.

## Task 4 · Model kaydetme ve tokenlaştırma

Demolar, Task 1’in Ubuntu önbelleğindeki `distilbert/distilbert-base-uncased-finetuned-sst-2-english` modelini ve tokenizer’ını kullanır. Load & Save, sınıflandırma ağırlıklarını ve tokenizer’ı yükler. Diğer dört demo yalnız tokenizer’ı açar. Hepsi yerel dosyalarla çevrimdışı çalışır. [Hugging Face Chapter 2 · Behind the pipeline](https://huggingface.co/learn/llm-course/chapter2/2?fw=pt).

Ubuntu/WSL terminalinde aşağıdaki dizine geçin. Her Python satırı tek bir demoyu çalıştırır.

```bash
cd "/mnt/c/Users/LENOVO/OneDrive/Masaüstü/EE 471 Soft-Tech/Hafta 1/EE471/Week-9/task-4"
PY=/home/lenovo/hf-class/.venv/bin/python
"$PY" -B load_and_save.py
"$PY" -B encoding_and_decoding.py
"$PY" -B padding.py
"$PY" -B truncation.py
"$PY" -B special_tokens.py
```

Load & Save, `save_pretrained()` ile modeli ve tokenizer’ı `task-4/output/distilbert-sst2/` dizinine yazar. Ardından ikisini de bu dizinden açıp aynı girdinin token ID’lerini, logitlerini ve sınıf etiketini karşılaştırır. Bu çıktı dizini Git dışında kalır. Diğer dört komut sonuçlarını terminale yazar.

### En fazla 15 saniyelik kayıtlar

Her video için ilgili komutu önceden çalıştırın. İlk 3 saniyede komutu ve girdiyi, kalan 12 saniye içinde sonucu gösterirken aşağıdaki cümleyi okuyun.

| Video | Ekranda göster | Söylenecek cümle |
|---|---|---|
| `Task4_load_and_save.avi` | Kayıt dizini, önceki ve sonraki etiket/skor, PASS satırı | “Model ve tokenizer’ı kaydettim. Klasörden yeniden yükleyince aynı girdinin tahmini eşleşti.” |
| `Task4_encoding_and_decoding.avi` | Kaynak cümle, token ID’leri ve çözülen metin | “Tokenizer cümleyi ID’lere dönüştürüyor ve bunları küçük harfli metne geri çözüyor.” |
| `Task4_padding.avi` | İki satırın önceki ve sonraki uzunlukları ile attention mask | “Kısa satır batch uzunluğuna tamamlanıyor. Eklenen dolgu konumlarının maskesi sıfır.” |
| `Task4_truncation.avi` | Token sayıları, 10 token sınırı ve çıkarılan metin | “Özel token ayarı aynı. On token sınırı cümlenin sonundaki bu parçayı çıkarıyor.” |
| `Task4_special_tokens.avi` | Aynı metnin iki token listesi, `[CLS]` ve `[SEP]` | “Özel token seçeneği açılınca mevcut CLS başa, SEP sona ekleniyor.” |

23 Kasım 2026’da Ubuntu/WSL’de **5/5** demo geçti. Load & Save öncesi ve sonrası `POSITIVE (0.999858)` döndü. Token ID’leri ve logitler de eşleşti. Encoding aynı ID’lere geri döndü. Padding uzunlukları `[4, 8] → [8, 8]` oldu ve dört dolgu konumu sıfırla maskelendi. Truncation, `[CLS]` ve `[SEP]` dahil `19 → 10` token bıraktı. Special Tokens, sözlük boyutu 30.522 kalırken `[CLS]=101` ve `[SEP]=102` eklendiğini doğruladı.
