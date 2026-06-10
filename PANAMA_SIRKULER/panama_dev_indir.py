import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 1. Ayarlar
BASE_URL = "https://www.amp.gob.pa"
START_URL = "https://www.amp.gob.pa/normatividad/"
HEDEF_KLASOR = os.path.join(os.getcwd(), "Sirkuler_PDFleri")
if not os.path.exists(HEDEF_KLASOR): os.makedirs(HEDEF_KLASOR)

print("Panama 73 sayfalık dev arşiv taranıyor...")
headers = {"User-Agent": "Mozilla/5.0"}

# Sayfaları sırayla gez (1'den 74'e kadar)
for sayfa_no in range(1, 74):
    print(f"--- {sayfa_no}. Sayfa taranıyor ---")
    url = f"{START_URL}?page={sayfa_no}" if sayfa_no > 1 else START_URL
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Sayfadaki tüm PDF linklerini topla
        for link in soup.find_all("a", href=True):
            if ".pdf" in link['href'].lower():
                pdf_url = urljoin(BASE_URL, link['href'])
                dosya_adi = pdf_url.split("/")[-1].split("?")[0]
                
                if not os.path.exists(os.path.join(HEDEF_KLASOR, dosya_adi)):
                    print(f"İndiriliyor: {dosya_adi}")
                    res = requests.get(pdf_url, headers=headers)
                    with open(os.path.join(HEDEF_KLASOR, dosya_adi), "wb") as f:
                        f.write(res.content)
    except Exception as e:
        print(f"Sayfa {sayfa_no} atlandı: {e}")

print("\nİŞLEM TAMAM! Tüm sayfalar tarandı.")