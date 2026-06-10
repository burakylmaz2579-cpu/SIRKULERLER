import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 1. Klasör Ayarları
KLASOR = os.getcwd()
HEDEF_KLASOR = os.path.join(KLASOR, "Sirkuler_PDFleri")
if not os.path.exists(HEDEF_KLASOR):
    os.makedirs(HEDEF_KLASOR)

print("Guinea-Bissau (Sekmeli Sistem) İçerik Avcısı başlatılıyor...")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://gbisr.com/marine-circulars/")

# 2. İnteraktif Toplama Aşaması
print("\n" + "="*60)
print("DİKKAT: Tarayıcı açıldı!")
print("1. Sol tarafta 2026, 2025, 2024 gibi YILLARI göreceksiniz.")
print("2. Lütfen sırayla TÜM YILLARA tek tek tıklayın.")
print("3. Siz tıkladıkça gizli olan PDF bağlantıları görünür olacaktır.")
print("Bunu yapmanız için tam 45 saniyeniz var...")
print("="*60 + "\n")

time.sleep(45)

# 3. Linkleri Toplama
print("Süre doldu! Sitedeki tüm bağlantılar toplanıyor...")
elements = driver.find_elements(By.TAG_NAME, "a")
potansiyel_linkler = []

for el in elements:
    href = el.get_attribute("href")
    if href and href.startswith("http"):
        potansiyel_linkler.append(href)

potansiyel_linkler = list(set(potansiyel_linkler))
print(f"Ekranda toplam {len(potansiyel_linkler)} adet bağlantı yakalandı. Sunucu analizine geçiliyor...\n")

driver.quit()

# 4. Sunucu Kontrolü ve İndirme (Bulut Koruması Açık)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
pdf_sayaci = 0

for url in potansiyel_linkler:
    try:
        kontrol = requests.head(url, headers=headers, allow_redirects=True, timeout=7)
        content_type = kontrol.headers.get("Content-Type", "").lower()
        
        if "application/pdf" in content_type or ".pdf" in url.lower():
            pdf_sayaci += 1
            
            # GBI linkleri genellikle uzun olur, güvenli isimlendirme yapalım
            dosya_adi = url.split("/")[-1].split("?")[0]
            if len(dosya_adi) < 4 or not dosya_adi.endswith(".pdf"):
                dosya_adi = f"GBI_Sirkuler_MC_{pdf_sayaci}.pdf"
            
            # Geçersiz karakterleri temizle (Windows dosya isimlerinde sorun yaratmasın diye)
            gecersiz_karakterler = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in gecersiz_karakterler:
                dosya_adi = dosya_adi.replace(char, '_')

            dosya_yolu = os.path.join(HEDEF_KLASOR, dosya_adi)
            
            cevap = requests.get(url, headers=headers, allow_redirects=True)
            with open(dosya_yolu, "wb") as f:
                f.write(cevap.content)
            
            print(f"[BAŞARILI - {pdf_sayaci}] İndirildi: {dosya_adi}")
            
    except Exception:
        pass

print("\n" + "="*50)
print(f"İŞLEM TAMAM! Toplam {pdf_sayaci} adet GBI sirküleri klasöre çekildi.")
print("="*50)