import os
import fitz  
import pandas as pd
import re
from deep_translator import GoogleTranslator

# Klasör Yolları
KLASOR = os.getcwd()
KAYNAK_KLASOR = os.path.join(KLASOR, "Sirkuler_PDFleri")

if not os.path.exists(KAYNAK_KLASOR):
    print(f"[HATA] PDF'lerin olduğu '{KAYNAK_KLASOR}' bulunamadı. Önce indirme işlemini tamamlayın.")
    exit()

print("Palau sirkülerleri okunuyor, kural referansları çıkarılıyor ve TÜRKÇE ÇEVİRİSİ yapılıyor...")
print("Lütfen bekleyin...\n")

veri_listesi = []
cevirmen = GoogleTranslator(source='en', target='tr')

def turkceye_cevir(metin):
    if not metin or metin == "Bulunamadı":
        return "Bulunamadı"
    try:
        return cevirmen.translate(metin)
    except:
        return "Çeviri hatası."

sertifikalar = {
    "SMC / ISM": ["ism code", "safety management", "dpa"],
    "ISSC / ISPS": ["isps", "security", "ssas", "cso", "pmsc", "armed"],
    "MLC": ["mlc", "maritime labour", "dmlc", "seafarer", "rest hours"],
    "Statüter / Donanım": ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas", "dispensation"]
}

for dosya in os.listdir(KAYNAK_KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(KAYNAK_KLASOR, dosya)
        
        dosya_verisi = {
            "Sirküler Dosyası": dosya,
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
            for sayfa_no in range(min(3, len(pdf))): # Sadece ilk 3 sayfa özet için yeterlidir
                tum_metin += pdf[sayfa_no].get_text()
            pdf.close()
            
            metin_kucuk = tum_metin.lower()
            
            # Kategori Tespiti
            kategoriler = [kat for kat, kelimeler in sertifikalar.items() if any(k in metin_kucuk for k in kelimeler)]
            dosya_verisi["İlgili Sertifika Kategorisi"] = ", ".join(kategoriler) if kategoriler else "Genel / Diğer"

            # Konu Tespiti
            subject_match = re.search(r'(?i)(?:SUBJECT|TITLE|To:)\s*[:\-]\s*(.*?)(?=\n[A-Z]|\n\n|$)', tum_metin)
            if subject_match:
                ing_konu = subject_match.group(1).strip().replace("\n", " ")
                dosya_verisi["Konu (İngilizce)"] = ing_konu
                dosya_verisi["Konu (TÜRKÇE)"] = turkceye_cevir(ing_konu)

            # Kural Dayanağı / Referans Tespiti
            ref_match = re.search(r'(?i)(?:REFERENCE|REFERENCES|REF)\s*[:\-]\s*([\s\S]*?)(?=\n(?:PURPOSE|APPLICABILITY|SUBJECT|BACKGROUND|1\.)|$)', tum_metin)
            if ref_match:
                dosya_verisi["Kural Dayanağı / Referanslar"] = re.sub(r'\s+', ' ', ref_match.group(1).strip())

            # Özet Tespiti
            purpose_match = re.search(r'(?i)(?:PURPOSE|BACKGROUND|APPLICABILITY|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|ACTION|$))', tum_metin)
            if purpose_match:
                ing_ozet = re.sub(r'\s+', ' ', purpose_match.group(1).strip())[:800]
                dosya_verisi["Özet Açıklama (İngilizce)"] = ing_ozet + "..."
                dosya_verisi["Özet Açıklama (TÜRKÇE)"] = turkceye_cevir(ing_ozet) + "..."
            
            veri_listesi.append(dosya_verisi)
            print(f"[TAMAMLANDI] -> {dosya}")
            
        except Exception:
            print(f"[HATA] {dosya} atlandı.")

df = pd.DataFrame(veri_listesi)
excel_adi = "Palau_Sirkuler_Analizi.xlsx"
df.to_excel(excel_adi, index=False)

print("\n" + "="*50)
print(f"HARİKA! Türkçe açıklamalı ve dayanaklı detaylı Excel dosyanız '{excel_adi}' adıyla kaydedildi.")
print("="*50)