import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 1. Ayarlar
KLASOR = os.getcwd()
HEDEF_KLASOR = os.path.join(KLASOR, "Sirkuler_PDFleri")
if not os.path.exists(HEDEF_KLASOR):
    os.makedirs(HEDEF_KLASOR)

print("Palau İçerik Avcısı (V3 - Bulut Sunucu Koruması Açık) başlatılıyor...")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://www.palaushipreg.com/information-center/online-library/marine-documents")

print("\n" + "="*50)
print("DİKKAT: Tarayıcı açıldı!")
print("1. Lütfen ekrandaki 'Marine Circulars' listesinin AÇIK olduğundan emin olun.")
print("2. Varsa 'Show All' (Tümünü Göster) seçeneğine tıklayın.")
print("Sistem 30 saniye sonra ekrandaki tüm bağlantıları kısıtlama olmadan toplayacak...")
print("="*50 + "\n")

time.sleep(30)

# 2. Linkleri Toplama (Filtresiz)
print("Süre doldu! Linkler toplanıyor...")
elements = driver.find_elements(By.TAG_NAME, "a")
potansiyel_linkler = []

for el in elements:
    href = el.get_attribute("href")
    # Domain filtresini kaldırdık! Bulut sunucusu linklerini (AWS, CDN vb.) de yakalayacak.
    if href and href.startswith("http"):
        potansiyel_linkler.append(href)

potansiyel_linkler = list(set(potansiyel_linkler))
print(f"Ekranda toplam {len(potansiyel_linkler)} adet geçerli bağlantı bulundu.")
print("Sunucuların kapısı çalınıyor, lütfen bekleyin (Bu işlem 1-2 dakika sürebilir)...\n")

driver.quit()

# 3. Bulut Kontrolü ve İndirme
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
pdf_sayaci = 0

for url in potansiyel_linkler:
    try:
        # Linkin arkasında ne olduğunu soruyoruz
        kontrol = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        content_type = kontrol.headers.get("Content-Type", "").lower()
        
        # Eğer sunucu "Bu bir PDF" derse veya URL'de pdf geçiyorsa:
        if "application/pdf" in content_type or ".pdf" in url.lower():
            pdf_sayaci += 1
            
            # İsimlendirme
            dosya_adi = url.split("/")[-1].split("?")[0]
            if len(dosya_adi) < 4 or not dosya_adi.endswith(".pdf"):
                dosya_adi = f"Palau_Sirkuler_MC_{pdf_sayaci}.pdf"

            dosya_yolu = os.path.join(HEDEF_KLASOR, dosya_adi)
            
            # Dosyayı indir
            cevap = requests.get(url, headers=headers, allow_redirects=True)
            with open(dosya_yolu, "wb") as f:
                f.write(cevap.content)
            
            print(f"[BAŞARILI - {pdf_sayaci}] İndirildi: {dosya_adi}")
            
    except Exception:
        pass # Yanıt vermeyen sayfaları atlar

print("\n" + "="*50)
print(f"İŞLEM TAMAM! Toplam {pdf_sayaci} adet dosya indirildi.")
print("="*50)