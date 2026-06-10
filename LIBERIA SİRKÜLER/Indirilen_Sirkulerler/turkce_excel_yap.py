import os
import fitz  
import pandas as pd
import re
from deep_translator import GoogleTranslator

# Klasör Yolları
KLASOR = os.getcwd()
KAYNAK_KLASOR = os.path.join(KLASOR, "Ilgili_Sirkulerler")

if not os.path.exists(KAYNAK_KLASOR):
    print(f"[HATA] '{KAYNAK_KLASOR}' klasörü bulunamadı.")
    exit()

print("Sirkülerler okunuyor ve TÜRKÇE ÇEVİRİSİ yapılıyor...")
print("Lütfen bekleyin, 441 belgenin çevirisi internet hızınıza bağlı olarak 3-5 dakika sürebilir.\n")

veri_listesi = []
# Çevirmeni başlat
cevirmen = GoogleTranslator(source='en', target='tr')

def turkceye_cevir(metin):
    if not metin or metin == "Bulunamadı":
        return "Bulunamadı"
    try:
        return cevirmen.translate(metin)
    except:
        return "Çeviri yapılamadı (Bağlantı hatası)."

sertifikalar = {
    "SMC / ISM": ["ism code", "safety management", "dpa"],
    "ISSC / ISPS": ["isps", "security", "ssas", "cso"],
    "MLC": ["mlc", "maritime labour", "dmlc", "seafarer"],
    "Statüter / Donanım": ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas"]
}

for dosya in os.listdir(KAYNAK_KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(KAYNAK_KLASOR, dosya)
        
        dosya_verisi = {
            "Dosya Adı": dosya,
            "Sertifika Kategorisi": "",
            "Konu (İngilizce)": "Bulunamadı",
            "Konu (TÜRKÇE)": "Bulunamadı",
            "Referans Kurallar": "Bulunamadı",
            "Özet (İngilizce)": "Bulunamadı",
            "Özet (TÜRKÇE)": "Bulunamadı"
        }
        
        try:
            pdf = fitz.open(dosya_yolu)
            tum_metin = ""
            for sayfa_no in range(min(3, len(pdf))):
                tum_metin += pdf[sayfa_no].get_text()
            pdf.close()
            
            # 1. Kategori Tespiti
            metin_kucuk = tum_metin.lower()
            kategoriler = [kat for kat, kelimeler in sertifikalar.items() if any(k in metin_kucuk for k in kelimeler)]
            dosya_verisi["Sertifika Kategorisi"] = ", ".join(kategoriler) if kategoriler else "Genel / Diğer"

            # 2. Konu (Subject) Tespiti ve Çevirisi
            subject_match = re.search(r'(?i)(?:SUBJECT|TITLE)\s*[:\-]\s*(.*?)(?=\n[A-Z]|\n\n|$)', tum_metin)
            if subject_match:
                ing_konu = subject_match.group(1).strip().replace("\n", " ")
                dosya_verisi["Konu (İngilizce)"] = ing_konu
                dosya_verisi["Konu (TÜRKÇE)"] = turkceye_cevir(ing_konu)

            # 3. Referans Tespiti (Çevrilmeden kalacak)
            ref_match = re.search(r'(?i)(?:REFERENCE|REF)\s*[:\-]\s*([\s\S]*?)(?=\n(?:PURPOSE|APPLICABILITY|SUBJECT|BACKGROUND|1\.)|$)', tum_metin)
            if ref_match:
                dosya_verisi["Referans Kurallar"] = re.sub(r'\s+', ' ', ref_match.group(1).strip())

            # 4. Özet Tespiti ve Çevirisi
            purpose_match = re.search(r'(?i)(?:PURPOSE|BACKGROUND|APPLICABILITY|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|ACTION|$))', tum_metin)
            if purpose_match:
                # Çeviri API'sini yormamak ve hızlandırmak için ilk 800 karakteri alıyoruz
                ing_ozet = re.sub(r'\s+', ' ', purpose_match.group(1).strip())[:800] 
                dosya_verisi["Özet (İngilizce)"] = ing_ozet + "..."
                dosya_verisi["Özet (TÜRKÇE)"] = turkceye_cevir(ing_ozet) + "..."
            
            veri_listesi.append(dosya_verisi)
            print(f"[ÇEVRİLDİ VE EKLENDİ] -> {dosya}")
            
        except Exception as e:
            print(f"[HATA] {dosya} atlandı.")

# Excel'i Kaydetme
df = pd.DataFrame(veri_listesi)
excel_adi = "Liberia_Sirkuler_Analizi_Turkce.xlsx"
df.to_excel(excel_adi, index=False)

print("\n" + "="*50)
print(f"HARİKA! Türkçe çevirili detaylı Excel dosyanız '{excel_adi}' adıyla klasöre kaydedildi.")
print("="*50)