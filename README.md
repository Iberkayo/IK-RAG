# HR Copilot AI - İnsan Kaynakları RAG Asistanı

Bu proje, kurum içi politikalar, prosedürler, mevzuatlar (4857 Sayılı İş Kanunu, Yıllık İzin Yönetmeliği vb.) ve iş tanımları hakkında sorulan sorulara hızlı, doğru ve kaynak göstererek cevap verebilen kurumsal bir **İnsan Kaynakları Yapay Zeka Asistanı (HR Copilot AI)** demo uygulamasıdır.

Sistem, anlamsal arama hassasiyetini ve tablo bütünlüğünü en üst düzeye çıkaran ileri düzey bir **RAG (Retrieval-Augmented Generation)** hattı kullanmaktadır.

---

##  Öne Çıkan Özellikler

1. **Gelişmiş Tablo Okuyucu & Birleşik Hücre Desteği**:
   * Dokümanlardaki tablolar PyMuPDF ile izole edilerek Pandas üzerinden temizlenir.
   * Tablolardaki birleşik hücrelerin (merged cells) veri kayıplarını engellemek amacıyla dikey ve yatay **Forward-fill (`ffill`)** uygulanır.
   * Tablo alanlarının ham metinleri ana gövde metninden ayrıştırılarak veri tekrarı tamamen engellenir.

2. **Çift Yönlü Tablo Chunklama**:
   * Tablolar hem bütünsel bağlamı korumak için **tam markdown tablosu** olarak hem de satır bazlı aramalarda nokta atışı eşleşme sağlamak için **başlıklarıyla birleştirilmiş satır-satır** chunk'lar halinde indekslenir.

3. **Metadata Prefixing (Arama Skorunu Artırıcı Ön Ek)**:
   * Her veri parçasının başına otomatik olarak `[Döküman: ...] [Kategori: ...] [Bölüm: ...]` etiketleri eklenerek, kullanıcının sorgu kelimeleri ile doküman adlarının anlamsal eşleşmesi en üst seviyeye çıkartılır.

4. **Yerel Vektör Veritabanı**:
   * Qdrant'ın SQLite/WAL tabanlı **Local Disk Storage** yapısı kullanılmıştır. Herhangi bir Docker kurulumuna veya uzak sunucu bağlantısına gerek duymadan çalışır.

5. **Arayüz (Streamlit & FastAPI)**:
   * **FastAPI Backend**: Lifespan yönetimiyle veri tabanına güvenli ve kilitlenmesiz erişim sağlar, RAG akışını ve GPT-4o Completion adımlarını yönetir.
   * **Streamlit Frontend**: Bağlantı durum göstergeleri, tek tıkla test yapılmasını sağlayan hazır senaryo tetikleyicileri ve kullanılan kaynakları benzerlik skorlarıyla listeleyen döküman referans paneli içeren modern bir İK kokpiti sunar.

---

## Klasör Yapısı

```text
IK-Rag/
├── data/
│   ├── raw/                 # Ham PDF dokümanları (İş Kanunu, El Kitapları vb.)
│   ├── processed/
│   │   ├── chunks.jsonl     # Normalleştirilmiş ve temizlenmiş döküman parçaları
│   │   └── metadata.json    # İçe aktarma çalışma raporu
│   ├── synthetic/           # Sentetik iş tanımı JSONL dosyaları
│   └── qdrant_db/           # SQLite tabanlı yerel Qdrant veritabanı klasörü
├── backend/
│   ├── main.py              # FastAPI sunucusu ve REST uç noktaları
│   ├── rag_engine.py        # Qdrant anlamsal araması ve OpenAI Completion akışı
│   └── config.py            # Ortam değişkenleri ve yapılandırma yöneticisi
├── frontend/
│   └── app.py               # Streamlit arayüzü ve API entegrasyonu
├── scripts/
│   ├── ingest.py            # Gelişmiş PDF/Tablo ayrıştırma ve chunking betiği
│   └── upload_vectors.py    # OpenAI ile vektörleştirme ve Qdrant'a yükleme betiği
├── requirements.txt         # Gerekli Python kütüphaneleri
├── .gitignore               # Hassas ve yerel dosyaları hariç tutma listesi
└── .env                     # API anahtarları şablonu (GitHub'a gönderilmez)
```

---

## Kurulum ve Çalıştırma

### 1. Sanal Ortam Oluşturma ve Bağımlılıkların Kurulması

Proje dizininde bir sanal ortam oluşturup gerekli kütüphaneleri yükleyin:

```bash
# Sanal ortam oluşturma
python -m venv .venv

# Sanal ortamı aktif etme (Windows için)
.venv\Scripts\activate

# Bağımlılıkların kurulması
python -m pip install -r requirements.txt
```

### 2. Ortam Değişkenlerinin Yapılandırılması

Kök dizindeki `.env` dosyasını açarak OpenAI API anahtarınızı tanımlayın (Bu dosya git tarafından takip edilmez):

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Verilerin İşlenmesi ve Veritabanının Doldurulması

Dökümanlardaki metin ve tabloları ayıklayarak chunk oluşturmak ve bu chunk'ları yerel Qdrant veritabanına yüklemek için sırasıyla aşağıdaki komutları çalıştırın:

```bash
# 1. PDF'leri oku, temizle ve chunks.jsonl oluştur
python scripts/ingest.py

# 2. Chunk'ları vektörleştir ve Qdrant'a yükle
python scripts/upload_vectors.py
```

### 4. Servislerin Başlatılması

Uygulamayı çalıştırmak için backend ve frontend sunucularını ayrı terminallerde başlatın:

**Terminallerde sanal ortamı aktif etmeyi unutmayın (`.venv\Scripts\activate`).**

* **FastAPI Sunucusu'nu Başlatma**:
  ```bash
  python -m backend.main
  ```
  *Sunucu varsayılan olarak `http://127.0.0.1:8000` portunda çalışacaktır.*

* **Streamlit Arayüzü'nü Başlatma**:
  ```bash
  streamlit run frontend/app.py --server.port 8501
  ```
  *Arayüze tarayıcınızdan `http://localhost:8501` adresi üzerinden erişebilirsiniz.*

---

## Doğrulanan Demo Senaryoları

Arayüz üzerindeki sol panelden tek tıkla test edebileceğiniz veya arama çubuğuna yazabileceğiniz örnek doğrulanmış sorular:

1. **Yıllık İzin Süresi Sorgusu**: `"3 yıldır çalışıyorum. Kaç gün yıllık izin hakkım var?"`
   * *Beklenen Yanıt*: Yıllık İzin Yönetmeliği'nden referansla 14 gün olduğunu belirten ve yönetmeliği kaynak gösteren cevap.
2. **Mevzuat Sorgusu**: `"Evlilik izni kaç gün?"`
   * *Beklenen Yanıt*: İş Kanunu (Madde 48) ve İK Yönetim Prosedürüne göre 3 gün olduğunu gösteren detaylı kaynaklı cevap.
3. **İK Görev Tanımı Sorgusu**: `"İnsan Kaynakları Uzmanının görevleri nelerdir?"`
   * *Beklenen Yanıt*: Sentetik İK Uzmanı görev tanımı belgesindeki işe alım, mülakat, bordro ve özlük süreçlerini listeleyen cevap.
4. **İK Üretkenlik Görevi**: `"Veri Analisti iş ilanı oluştur."`
   * *Beklenen Yanıt*: Veri Analisti İş Tanımı belgesindeki görevleri, nitelikleri ve aranan yetkinlikleri kullanarak otomatik olarak hazırlanan profesyonel bir iş ilanı taslağı.
  ### 5. Görsel Örnekler
<img width="2175" height="484" alt="image" src="https://github.com/user-attachments/assets/76686f5d-2b8a-442c-a1d0-8b60f49cce00" />

<img width="2169" height="1251" alt="image" src="https://github.com/user-attachments/assets/10a9b2c2-57d2-4b37-a58c-110d9b3ac062" />


