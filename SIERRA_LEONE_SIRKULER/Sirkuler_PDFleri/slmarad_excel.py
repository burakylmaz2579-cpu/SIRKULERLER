import os
import fitz  # PyMuPDF
import pandas as pd
import re
from deep_translator import GoogleTranslator

# 1. Klasör ve Dosya Ayarları
# 1. Klasör ve Dosya Ayarları
HEDEF_KLASOR = "." 
EXCEL_ADI = "SLMARAD_Sirkuler_Analizi_Turkce.xlsx"
print("PDF dosyaları taranıyor ve analiz ediliyor...")
veri_listesi = []
cevirmen = GoogleTranslator(source='en', target='tr')

def turkceye_cevir(metin):
    if not metin or metin == "Bulunamadı": return "Bulunamadı"
    try: return cevirmen.translate(metin[:800]) # Çeviri sınırı
    except: return "Çeviri hatası."

# 2. PDF Tarama Döngüsü
for dosya in os.listdir(HEDEF_KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(HEDEF_KLASOR, dosya)
        print(f"İşleniyor: {dosya}")
        
        try:
            pdf = fitz.open(dosya_yolu)
            metin = ""
            for sayfa in pdf: metin += sayfa.get_text()
            pdf.close()
            
            # Veri Çıkarma
            konu = re.search(r'(?i)(?:SUBJECT|TITLE|To:)\s*[:\-]\s*(.*?)(?=\n)', metin)
            ozet = re.search(r'(?i)(?:PURPOSE|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|$))', metin)
            
            ing_konu = konu.group(1).strip() if konu else "Bulunamadı"
            ing_ozet = ozet.group(1).strip() if ozet else "Bulunamadı"
            
            veri_listesi.append({
                "Sirküler Dosyası": dosya,
                "Konu (İngilizce)": ing_konu,
                "Konu (TÜRKÇE)": turkceye_cevir(ing_konu),
                "Özet (İngilizce)": ing_ozet[:500] + "...",
                "Özet (TÜRKÇE)": turkceye_cevir(ing_ozet)[:500] + "..."
            })
        except Exception as e:
            print(f"Hata: {dosya} işlenemedi.")

# 3. Excel'e Yaz
df = pd.DataFrame(veri_listesi)
df.to_excel(EXCEL_ADI, index=False)
print(f"\nİŞLEM TAMAM! '{EXCEL_ADI}' dosyası hazır.")