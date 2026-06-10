import os
import fitz  # PyMuPDF
import pandas as pd
import re
from deep_translator import GoogleTranslator

# 1. Klasör ve Dosya Ayarları
# Kod ve PDF'lerin aynı klasörde olduğunu varsayıyoruz
HEDEF_KLASOR = "." 
EXCEL_ADI = "PANAMA_Sirkuler_Analizi_Turkce.xlsx"

print("Panama mevzuatı taranıyor, metinler ayıklanıyor ve çevriliyor...")
veri_listesi = []
cevirmen = GoogleTranslator(source='en', target='tr')

def turkceye_cevir(metin):
    if not metin or metin == "Bulunamadı": return "Bulunamadı"
    try: return cevirmen.translate(metin[:800]) 
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
            
            # Panama sirkülerleri/mevzuatları için başlık/konu desenleri
            konu_match = re.search(r'(?i)(?:SUBJECT|TITLE|To:|CIRCULAR|Circular No\.)\s*[:\-]?\s*(.*?)(?=\n)', metin)
            ozet_match = re.search(r'(?i)(?:PURPOSE|BACKGROUND|1\.\s+INTRODUCTION)\s*[:\-]?\s*([\s\S]*?)(?=\n(?:2\.|REQUIREMENTS|$))', metin)
            
            ing_konu = konu_match.group(1).strip() if konu_match else "Bulunamadı"
            ing_ozet = ozet_match.group(1).strip() if ozet_match else "Bulunamadı"
            
            veri_listesi.append({
                "Dosya Adı": dosya,
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