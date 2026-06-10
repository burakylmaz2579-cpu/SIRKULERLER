import os
import fitz  
import pandas as pd
import re
from deep_translator import GoogleTranslator

# 1. Klasör Yolları
KLASOR = os.getcwd()
KAYNAK_KLASOR = "."

if not os.path.exists(KAYNAK_KLASOR):
    print(f"[HATA] '{KAYNAK_KLASOR}' klasörü bulunamadı. Lütfen önce PDF'leri indirdiğinizden emin olun.")
    exit()

print("Gine-Bissau (GBI) sirkülerleri taranıyor, kurallar çıkarılıyor ve TÜRKÇE'ye çevriliyor...")
print("Lütfen bekleyin, dosya sayısına ve internet hızınıza göre bu işlem birkaç dakika sürebilir...\n")

veri_listesi = []
cevirmen = GoogleTranslator(source='en', target='tr')

def turkceye_cevir(metin):
    if not metin or metin == "Bulunamadı":
        return "Bulunamadı"
    try:
        return cevirmen.translate(metin)
    except:
        return "Çeviri yapılamadı (Bağlantı hatası)."

# Verifier Sertifika Etiketleri
sertifikalar = {
    "SMC / ISM": ["ism code", "safety management", "dpa", "audit"],
    "ISSC / ISPS": ["isps", "security", "ssas", "cso", "piracy"],
    "MLC": ["mlc", "maritime labour", "dmlc", "seafarer", "medical", "rest hours"],
    "Statüter / Donanım": ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas", "dispensation", "exemption"],
    "Klas / RO Yetkileri": ["recognized organization", "ro authorization", "surveyor"]
}

for dosya in os.listdir(KAYNAK_KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(KAYNAK_KLASOR, dosya)
        
        # Excel'deki Sütun Başlıklarımız
        dosya_verisi = {
            "GBI Sirküler Dosyası": dosya,
            "İlgili Sertifika Kategorisi": "",
            "Konu (İngilizce)": "Bulunamadı",
            "Konu (TÜRKÇE)": "Bulunamadı",
            "Kural Dayanağı / Referanslar": "Bulunamadı",
            "Özet Açıklama (İngilizce)": "Bulunamadı",
            "Özet Açıklama (TÜRKÇE)": "Bulunamadı"
        }
        
        try:
            pdf = fitz.open(dosya_yolu)
            tum_metin = ""
            # Sadece ilk 3 sayfayı okuyoruz (Özet ve referanslar genelde baştadır, hızı artırır)
            for sayfa_no in range(min(3, len(pdf))): 
                tum_metin += pdf[sayfa_no].get_text()
            pdf.close()
            
            metin_kucuk = tum_metin.lower()
            
            # 1. Kategori Tespiti
            kategoriler = [kat for kat, kelimeler in sertifikalar.items() if any(k in metin_kucuk for k in kelimeler)]
            dosya_verisi["İlgili Sertifika Kategorisi"] = ", ".join(kategoriler) if kategoriler else "Genel / Diğer"

            # 2. Konu (Subject) Tespiti ve Çevirisi
            subject_match = re.search(r'(?i)(?:SUBJECT|TITLE|To:)\s*[:\-]\s*(.*?)(?=\n[A-Z]|\n\n|$)', tum_metin)
            if subject_match:
                ing_konu = subject_match.group(1).strip().replace("\n", " ")
                dosya_verisi["Konu (İngilizce)"] = ing_konu
                dosya_verisi["Konu (TÜRKÇE)"] = turkceye_cevir(ing_konu)

            # 3. Kural Dayanağı (Referans) Tespiti (Referanslar çevrilmez, orijinal kalır)
            ref_match = re.search(r'(?i)(?:REFERENCE|REFERENCES|REF)\s*[:\-]\s*([\s\S]*?)(?=\n(?:PURPOSE|APPLICABILITY|SUBJECT|BACKGROUND|1\.)|$)', tum_metin)
            if ref_match:
                dosya_verisi["Kural Dayanağı / Referanslar"] = re.sub(r'\s+', ' ', ref_match.group(1).strip())

            # 4. Özet Tespiti ve Çevirisi
            purpose_match = re.search(r'(?i)(?:PURPOSE|BACKGROUND|APPLICABILITY|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|ACTION|SCOPE|$))', tum_metin)
            if purpose_match:
                # Çeviri API'sini yormamak ve hızı artırmak için ilk 800 karakteri alıyoruz
                ing_ozet = re.sub(r'\s+', ' ', purpose_match.group(1).strip())[:800]
                dosya_verisi["Özet Açıklama (İngilizce)"] = ing_ozet + "..."
                dosya_verisi["Özet Açıklama (TÜRKÇE)"] = turkceye_cevir(ing_ozet) + "..."
            
            veri_listesi.append(dosya_verisi)
            print(f"[ÇEVRİLDİ VE EKLENDİ] -> {dosya}")
            
        except Exception:
            print(f"[HATA] {dosya} atlandı (Şifreli veya hasarlı olabilir).")

# Verileri Excel'e Dönüştür ve Kaydet
df = pd.DataFrame(veri_listesi)
excel_adi = "GBI_Sirkuler_Analizi_Turkce.xlsx"
df.to_excel(excel_adi, index=False)

print("\n" + "="*50)
print(f"MÜKEMMEL! Türkçe açıklamalı Excel tablonuz '{excel_adi}' adıyla klasöre kaydedildi.")
print("="*50)