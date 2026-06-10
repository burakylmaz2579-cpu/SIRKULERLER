import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from PyPDF2 import PdfMerger

# 1. Ayarlar
DOWNLOAD_DIR = "Indirilen_Sirkulerler"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 2. Selenium Robot Tarayıcıyı Başlatma
print("Robot Chrome tarayıcı başlatılıyor, lütfen bekleyin...")
options = webdriver.ChromeOptions()
# Tarayıcıyı ekranda görebilmen için gizli modu kapalı tutuyoruz
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.liscr.com/onlinelibrary/"
driver.get(url)

# 3. YARI OTOMATİK MÜDAHALE SÜRESİ
print("\n" + "="*50)
print("DİKKAT: Tarayıcı açıldı!")
print("Ekranda 694 belgenin hepsi görünmüyorsa (sayfalara bölünmüşse),")
print("açılan Chrome penceresinde tablonun altındaki/üstündeki sayfa sayısını")
print("'Show All' (Tümünü Göster) veya en yüksek sayıya manuel olarak ayarlayın.")
print("Bunu yapmanız için 25 saniyeniz var...")
print("="*50 + "\n")

time.sleep(25) # Senin tabloyu ayarlaman veya sayfanın tam yüklenmesi için bekleme süresi

# 4. Sayfadaki PDF Linklerini Toplama
print("Süre doldu! Ekranda görünen PDF bağlantıları taranıyor...")
links = driver.find_elements(By.TAG_NAME, "a")
pdf_urls = []

for link in links:
    href = link.get_attribute("href")
    if href and ".pdf" in href.lower():
        pdf_urls.append(href)

# Tekrarları temizle
pdf_urls = list(set(pdf_urls))
print(f"Toplam {len(pdf_urls)} benzersiz PDF yakalandı. İndirme başlıyor...")

# Tarayıcıyla işimiz bitti, kapatabiliriz
driver.quit()

# 5. İndirme İşlemi
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

downloaded_files = []
for idx, pdf_url in enumerate(pdf_urls, 1):
    try:
        file_name = pdf_url.split("/")[-1]
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        pdf_response = requests.get(pdf_url, headers=headers)
        with open(file_path, "wb") as f:
            f.write(pdf_response.content)
            
        downloaded_files.append(file_path)
        print(f"[{idx}/{len(pdf_urls)}] İndirildi: {file_name}")
    except Exception as e:
        print(f"Hata - Atlandı: {pdf_url}")

# 6. Birleştirme İşlemi
if len(downloaded_files) > 0:
    print("Tüm sirkülerler tek bir dosyada birleştiriliyor...")
    merger = PdfMerger()

    for pdf in downloaded_files:
        try:
            merger.append(pdf)
        except Exception as e:
            print(f"Bozuk PDF atlandı ({pdf})")

    output_filename = "Liberia_Birlesik_Sirkulerler_Rapor.pdf"
    merger.write(output_filename)
    merger.close()
    print(f"\nİŞLEM TAMAMLANDI! Dosya adınız: {output_filename}")
else:
    print("İndirilecek PDF bulunamadı veya bağlantı hatası oluştu.")