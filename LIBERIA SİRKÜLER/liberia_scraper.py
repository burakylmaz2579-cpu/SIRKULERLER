import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger

# 1. Ayarlar ve Klasör Oluşturma
BASE_URL = "https://www.liscr.com"
# Not: LISCR'ın Maritime dokümanlarının tam listelendiği sayfanın spesifik URL'sini buraya koymalısınız.
# Şimdilik örnek bir kütüphane linki koyuyoruz.
LIBRARY_URL = "https://www.liscr.com/online-library-search" 

DOWNLOAD_DIR = "Liberia_Sirkulerler"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

print("İndirme klasörü hazırlandı:", DOWNLOAD_DIR)

# 2. Web Sayfasından PDF Linklerini Çekme
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print("Liberya kütüphanesine bağlanılıyor...")
response = requests.get(LIBRARY_URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# '.pdf' ile biten tüm linkleri bul
pdf_links = []
for link in soup.find_all("a", href=True):
    if ".pdf" in link['href'].lower():
        full_url = link['href']
        if not full_url.startswith("http"):
            full_url = BASE_URL + full_url
        pdf_links.append(full_url)

# Tekrarlayan linkleri temizle
pdf_links = list(set(pdf_links))
print(f"Toplam {len(pdf_links)} adet sirküler bulundu. İndirme başlıyor...")

# 3. PDF'leri İndirme
downloaded_files = []
for idx, pdf_url in enumerate(pdf_links, 1):
    try:
        # Dosya adını URL'den alma
        file_name = pdf_url.split("/")[-1]
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        # Dosyayı indir
        pdf_response = requests.get(pdf_url, headers=headers)
        with open(file_path, "wb") as f:
            f.write(pdf_response.content)
            
        downloaded_files.append(file_path)
        print(f"[{idx}/{len(pdf_links)}] İndirildi: {file_name}")
    except Exception as e:
        print(f"Hata: {pdf_url} indirilemedi. Detay: {e}")

# 4. İndirilen PDF'leri Tek Bir Dosyada Birleştirme
print("Tüm sirkülerler birleştiriliyor. Bu işlem dosya boyutuna göre biraz sürebilir...")
merger = PdfMerger()

for pdf in downloaded_files:
    try:
        merger.append(pdf)
    except Exception as e:
        print(f"Birleştirme hatası ({pdf}): {e}")

output_filename = "Liberia_Tum_Sirkulerler_Birlesik.pdf"
merger.write(output_filename)
merger.close()

print(f"İşlem Tamamlandı! Tüm dokümanlar '{output_filename}' adıyla kaydedildi.")