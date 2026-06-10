# 🚢 Flag State Circulars & Statutory Checklists Portal

Bu portal, yetkili olunan bayrak devletlerinin (Panama, Sierra Leone, Comoros, Guinea Bissau, Palau ve Liberia) sirkülerlerini bir araya getirerek hızlıca arama yapmanızı, detayları incelemenizi ve Statutory (ISM, MLC, ISPS, Statüter Donanım) sörveylerinde dikkat etmeniz gereken maddelere hızlıca ulaşmanızı sağlar.

---

## 💻 Yerel Kurulum ve Çalıştırma

Uygulamayı bilgisayarınızda çalıştırmak için aşağıdaki adımları takip edin:

1. **Terminal / PowerShell Açın**:
   `C:\Users\LIVAPC8\Desktop\SIRKULERLER\websitekodlar` klasöründe bir PowerShell terminali açın.

2. **Gerekli Paketleri Yükleyin**:
   Aşağıdaki komutu çalıştırarak gerekli kütüphaneleri (Streamlit, Pandas, OpenPyXL) yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. **Uygulamayı Başlatın**:
   Aşağıdaki komutla Streamlit arayüzünü açın:
   ```bash
   streamlit run app.py
   ```
   *Tarayıcınız otomatik olarak `http://localhost:8501` adresinde açılacaktır.*

---

## 🌐 GitHub ve Streamlit Cloud ile Canlı Yayın (Deploy)

Web sitesini tüm dünyadan erişilebilir kılmak ve Streamlit Cloud üzerinden ücretsiz yayınlamak için:

1. **GitHub Deposu (Repository) Oluşturun**:
   - GitHub hesabınızda yeni bir repository oluşturun (Örn: `phrs-flag-circulars`).
   - Masaüstünüzdeki **`SIRKULERLER`** klasörünün **içindeki tüm klasör ve dosyaları** bu repository'e yükleyin.
   - *Önemli Dosya Düzeni*:
     - `COMOROS_SIRKULER/`
     - `GBI_SIRKULER/`
     - `LIBERIA SİRKÜLER/`
     - `PALAU SIRKULER/`
     - `PANAMA_SIRKULER/`
     - `SIERRA_LEONE_SIRKULER/`
     - `websitekodlar/` (bu klasörün içinde `app.py`, `requirements.txt`, vb. bulunmalı)

2. **Streamlit Community Cloud'a Bağlanın**:
   - [share.streamlit.io](https://share.streamlit.io/) sitesine gidin ve GitHub hesabınızla giriş yapın.
   - **"Create app"** veya **"New app"** butonuna tıklayın.
   - Repository olarak yeni oluşturduğunuz depoyu seçin.
   - **Branch** olarak `main` veya `master` seçin.
   - **Main file path** alanına `websitekodlar/app.py` yazın.
   - **"Deploy!"** butonuna tıklayın. Birkaç dakika içinde siteniz canlıya alınacaktır!
