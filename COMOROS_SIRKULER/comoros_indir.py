import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 1. Ayarlar
URL = "http://bihlyumov.com/circulars/"
HEDEF_KLASOR = os.path.join(os.getcwd(), "Sirkuler_PDFleri")

if not os.path.exists(HEDEF_KLASOR):
    os.makedirs(HEDEF_KLASOR)

print("Comoros PDF Dizin Tarayıcısı başlatılıyor...")

try:
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    
    pdf_sayaci = 0
    # Sayfadaki tüm linkleri bul
    for link in soup.find_all("a", href=True):
        href = link['href']
        
        # Sadece PDF olanları yakala
        if href.lower().endswith(".pdf"):
            pdf_url = urljoin(URL, href)
            dosya_adi = href.split("/")[-1]
            dosya_yolu = os.path.join(HEDEF_KLASOR, dosya_adi)
            
            print(f"İndiriliyor: {dosya_adi}")
            pdf_dosyasi = requests.get(pdf_url)
            with open(dosya_yolu, "wb") as f:
                f.write(pdf_dosyasi.content)
            pdf_sayaci += 1

    print(f"\nİŞLEM TAMAM! Toplam {pdf_sayaci} adet PDF indirildi.")

except Exception as e:
    print(f"Hata oluştu: {e}")