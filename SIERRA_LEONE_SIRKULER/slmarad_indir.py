import os
import requests
from bs4 import BeautifulSoup

# --- AYARLAR ---
HTML_DOSYASI = "sierra_liste.html"
HEDEF_KLASOR = os.path.join(os.getcwd(), "Sirkuler_PDFleri")

if not os.path.exists(HEDEF_KLASOR):
    os.makedirs(HEDEF_KLASOR)

# --- İŞLEM ---
print("Sierra Leone PDF listesi yerel dosyadan taranıyor...")

if not os.path.exists(HTML_DOSYASI):
    print(f"[HATA] '{HTML_DOSYASI}' bulunamadı. Lütfen sayfayı tarayıcıdan bu klasöre kaydedin.")
    exit()

with open(HTML_DOSYASI, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

pdf_sayaci = 0
# HTML içindeki tüm linkleri tara
for link in soup.find_all("a", href=True):
    href = link['href']
    # .pdf uzantısını veya indirme linklerini yakala
    if ".pdf" in href.lower():
        try:
            # Link tam değilse tamamla
            if not href.startswith("http"):
                pdf_url = "https://slmarad.com" + href
            else:
                pdf_url = href
            
            dosya_adi = href.split("/")[-1].split("?")[0]
            dosya_yolu = os.path.join(HEDEF_KLASOR, dosya_adi)
            
            print(f"İndiriliyor: {dosya_adi}")
            response = requests.get(pdf_url, stream=True)
            with open(dosya_yolu, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            pdf_sayaci += 1
        except Exception as e:
            print(f"Hata: {dosya_adi} - {e}")

print(f"\nİŞLEM TAMAM! Toplam {pdf_sayaci} adet sirküler indirildi.")