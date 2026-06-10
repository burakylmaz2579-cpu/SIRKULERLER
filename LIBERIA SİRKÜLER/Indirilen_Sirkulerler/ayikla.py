import os
import shutil
import fitz  # PyMuPDF kütüphanesi

# Çalıştırıldığı klasörü otomatik algılar
KLASOR = os.getcwd()
HEDEF_KLASOR = os.path.join(KLASOR, "Ilgili_Sirkulerler")

ANAHTAR_KELIMELER = [
    "ism code", "isps code", "mlc, 2006", "dmlc", 
    "designated person ashore", "dpa", 
    "ship security alert", "ssas", 
    "lifeboat", "recognized organization", "ro authorization",
    "exemption", "dispensation", "thickness measurement",
    "ballast water"
]

if not os.path.exists(HEDEF_KLASOR):
    os.makedirs(HEDEF_KLASOR)

print("PDF'ler taranıyor, lütfen bekleyin...")

bulunan = 0
for dosya in os.listdir(KLASOR):
    if dosya.lower().endswith(".pdf"):
        dosya_yolu = os.path.join(KLASOR, dosya)
        eslesme = False
        
        try:
            pdf = fitz.open(dosya_yolu)
            for sayfa in pdf:
                metin = sayfa.get_text().lower()
                # Kelimelerden herhangi biri metinde varsa kopyala
                if any(kelime in metin for kelime in ANAHTAR_KELIMELER):
                    eslesme = True
                    break 
            pdf.close()
            
            if eslesme:
                shutil.copy2(dosya_yolu, os.path.join(HEDEF_KLASOR, dosya))
                bulunan += 1
                print(f"[BULUNDU] -> {dosya}")
                
        except Exception:
            pass # Okunamayan veya bozuk dosyaları sessizce atlar

print("\n" + "="*40)
print(f"İŞLEM TAMAM! {bulunan} adet sirküler ayıklandı.")
print("="*40)