import os
import fitz  # PyMuPDF
import pandas as pd
import re

# Klasör Yolları
KLASOR = os.getcwd()
KAYNAK_KLASOR = os.path.join(KLASOR, "Ilgili_Sirkulerler")

# Eğer klasör yoksa uyar ve çık
if not os.path.exists(KAYNAK_KLASOR):
    print(f"[HATA] '{KAYNAK_KLASOR}' klasörü bulunamadı. Lütfen kodun doğru yerde olduğundan emin olun.")
    exit()

print("Sirkülerler okunuyor ve detaylı Excel tablosu hazırlanıyor. Lütfen bekleyin...")

# Excel'e aktarılacak verilerin tutulacağı liste
veri_listesi = []

# Sertifika Tespiti İçin Kilit Kelimeler
sertifikalar = {
    "SMC / ISM": ["ism code", "safety management", "dpa"],
    "ISSC / ISPS": ["isps", "security", "ssas", "cso"],
    "MLC": ["mlc", "maritime labour", "dmlc", "seafarer"],
    "Statüter / Donanım": ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas"]
}

# Kaynak klasördeki PDF'leri sırayla oku
for dosya in os.listdir(KAYNAK_KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(KAYNAK_KLASOR, dosya)
        
        # Her dosya için varsayılan değerler
        dosya_verisi = {
            "Dosya Adı": dosya,
            "İlgili Sertifika Kategorisi": "",
            "Sirküler Konusu (Subject)": "Bulunamadı",
            "Referans Kurallar (Reference)": "Bulunamadı",
            "Amaç / Kural Özeti": "Bulunamadı"
        }
        
        try:
            pdf = fitz.open(dosya_yolu)
            tum_metin = ""
            
            # İlk 3 sayfayı okumak genellikle özet, konu ve referanslar için yeterlidir
            for sayfa_no in range(min(3, len(pdf))):
                tum_metin += pdf[sayfa_no].get_text()
            pdf.close()
            
            # 1. Kategori Tespiti
            metin_kucuk = tum_metin.lower()
            kategoriler = []
            for kat, kelimeler in sertifikalar.items():
                if any(kelime in metin_kucuk for kelime in kelimeler):
                    kategoriler.append(kat)
            dosya_verisi["İlgili Sertifika Kategorisi"] = ", ".join(kategoriler) if kategoriler else "Genel / Diğer"

            # 2. Konu (Subject) Tespiti (Regex ile)
            subject_match = re.search(r'(?i)(?:SUBJECT|TITLE|Konu)\s*[:\-]\s*(.*?)(?=\n[A-Z]|\n\n|$)', tum_metin)
            if subject_match:
                dosya_verisi["Sirküler Konusu (Subject)"] = subject_match.group(1).strip().replace("\n", " ")

            # 3. Referanslar (Reference) Tespiti
            ref_match = re.search(r'(?i)(?:REFERENCE|REF)\s*[:\-]\s*([\s\S]*?)(?=\n(?:PURPOSE|APPLICABILITY|SUBJECT|BACKGROUND|1\.)|$)', tum_metin)
            if ref_match:
                # Referansları tek bir temiz satır haline getir
                temiz_ref = re.sub(r'\s+', ' ', ref_match.group(1).strip())
                dosya_verisi["Referans Kurallar (Reference)"] = temiz_ref

            # 4. Amaç ve Kural Özeti (Purpose / Background) Tespiti
            purpose_match = re.search(r'(?i)(?:PURPOSE|BACKGROUND|APPLICABILITY|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|ACTION|$))', tum_metin)
            if purpose_match:
                temiz_ozet = re.sub(r'\s+', ' ', purpose_match.group(1).strip())
                # Özeti makul bir uzunlukta tutalım (max 1000 karakter)
                dosya_verisi["Amaç / Kural Özeti"] = temiz_ozet[:1000] + ("..." if len(temiz_ozet) > 1000 else "")
            
            veri_listesi.append(dosya_verisi)
            print(f"[EKLENDİ] -> {dosya}")
            
        except Exception as e:
            print(f"[HATA] {dosya} okunamadı. Sebeb: {e}")

# 3. Verileri Excel'e Dönüştür ve Kaydet
df = pd.DataFrame(veri_listesi)

excel_adi = "Liberia_Sirkuler_Analizi.xlsx"
df.to_excel(excel_adi, index=False)

print("\n" + "="*50)
print(f"MÜKEMMEL! Tüm detaylar '{excel_adi}' adlı Excel dosyasına aktarıldı.")
print("="*50)