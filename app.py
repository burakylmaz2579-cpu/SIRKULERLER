import os
import urllib.parse
import streamlit as st
import pandas as pd
import hashlib
import textwrap
import re

# Initialize session state for unified filters
if "selected_flag" not in st.session_state:
    st.session_state["selected_flag"] = "Tümü"
if "selected_cat" not in st.session_state:
    st.session_state["selected_cat"] = "Tümü"
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

# Set page config
st.set_page_config(
    page_title="PHRS Bayrak Sirkülerleri & Statutory Kontrol Portalı",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Clean Light Maritime Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main container background */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Sidebar styling (Clean Light Theme for visibility) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sidebar text colors */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label {
        color: #0f172a !important;
        font-weight: 500;
    }
    
    /* Clean white cards with light borders and soft shadows */
    .glass-card {
        background: #ffffff;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.2s ease-in-out;
    }
    .glass-card:hover {
        border-color: #0284c7;
        box-shadow: 0 10px 15px -3px rgba(2, 132, 199, 0.08), 0 4px 6px -2px rgba(2, 132, 199, 0.04);
        transform: translateY(-1px);
    }
    
    /* Headings */
    .gradient-text {
        color: #0369a1;
        font-weight: 700;
    }
    
    .gradient-header {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    .gradient-subheader {
        font-size: 1.4rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
        color: #0369a1;
    }

    /* Metric container */
    .metric-container {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }
    .metric-box {
        flex: 1;
        min-width: 150px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        transition: all 0.2s;
    }
    .metric-box:hover {
        background: #f0f9ff;
        border-color: #bae6fd;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0284c7;
        margin-bottom: 5px;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Styled badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .badge-flag { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-cat { background: #fce7f3; color: #be185d; border: 1px solid #fbcfe8; }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f8fafc;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to clean common Turkish character encoding corruptions
def clean_cell_text(val):
    if not isinstance(val, str):
        return val
    replacements = {
        'TRKE': 'TÜRKÇE',
        'gili': 'İlgili',
        'zet': 'Özet',
        'Sirkler': 'Sirküler',
        'Dayana': 'Dayanağı',
        'ngilizce': 'İngilizce',
        'Dosya Ad': 'Dosya Adı',
        'aklama': 'açıklama',
        'dzenlenmesi': 'düzenlenmesi',
        'dzenleme': 'düzenleme',
        'gvenlik': 'güvenlik',
        'grevi': 'görevi',
        'grevli': 'görevli',
        'kılavuz': 'kılavuzu',
        'artlar': 'şartlar',
        'belgelendirme': 'belgelendirme',
        'ynerge': 'yönerge',
        'irket': 'şirket',
        'lkeler': 'ülkeler',
        'e alım': 'işe alım',
        'nlem': 'önlem',
        'szleşme': 'sözleşme',
        'prosedr': 'prosedür',
        'gvde': 'gövde',
        'deerlendir': 'değerlendir',
        'ntelik': 'nitelik',
        'ynetim': 'yönetim',
        'sektr': 'sektör',
        'gemi adam': 'gemi adamı',
        'bulunamad': 'Bulunamadı',
        'bulunamadı': 'Bulunamadı'
    }
    for corrupted, corrected in replacements.items():
        val = val.replace(corrupted, corrected)
    return val

# Automatically classify categories for rows without a category
def classify_category(row):
    subject = str(row.get('Subject_EN', '')).lower() + " " + str(row.get('Subject_TR', '')).lower()
    summary = str(row.get('Summary_EN', '')).lower() + " " + str(row.get('Summary_TR', '')).lower()
    combined = subject + " " + summary
    
    categories = []
    if any(k in combined for k in ["ism", "safety management", "dpa", "smc", "safety auditing", "audit", "doc "]):
        categories.append("SMC / ISM")
    if any(k in combined for k in ["isps", "security", "ssas", "cso", "piracy", "issc"]):
        categories.append("ISSC / ISPS")
    if any(k in combined for k in ["mlc", "maritime labour", "dmlc", "seafarer", "crew", "cook", "rest hours", "repatriation", "medical"]):
        categories.append("MLC")
    if any(k in combined for k in ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas", "dispensation", "exemption", "equipment", "fire", "co2", "radio"]):
        categories.append("Statüter / Donanım")
    if any(k in combined for k in ["recognized organization", "ro authorization", "surveyor", "class society"]):
        categories.append("Klas / RO Yetkileri")
        
    if not categories:
        return "Genel / Diğer"
    return ", ".join(categories)

# Normalize column names to a unified schema regardless of encoding issues
def normalize_columns(df):
    mapping = {}
    for col in df.columns:
        col_lower = str(col).lower()
        if 'dosya' in col_lower or 'sirküler' in col_lower or 'sirkuler' in col_lower or 'filename' in col_lower:
            mapping[col] = 'Filename'
        elif 'kategori' in col_lower or 'category' in col_lower:
            mapping[col] = 'Category'
        elif 'konu' in col_lower or 'subject' in col_lower:
            if any(k in col_lower for k in ['türkçe', 'turkce', 'trke', 'trk', 'tr', '_tr']):
                mapping[col] = 'Subject_TR'
            else:
                mapping[col] = 'Subject_EN'
        elif 'referans' in col_lower or 'dayan' in col_lower or 'kural' in col_lower or 'reference' in col_lower:
            mapping[col] = 'References'
        elif 'özet' in col_lower or 'ozet' in col_lower or 'zet' in col_lower or 'summary' in col_lower:
            if any(k in col_lower for k in ['türkçe', 'turkce', 'trke', 'trk', 'tr', '_tr']):
                mapping[col] = 'Summary_TR'
            else:
                mapping[col] = 'Summary_EN'
        elif 'tavsiye' in col_lower or 'ne yap' in col_lower or 'rec' in col_lower or 'action' in col_lower or 'recommendation' in col_lower:
            mapping[col] = 'Recommendations_TR'
    df = df.rename(columns=mapping)
    return df

# Clean filename to a readable title
def clean_filename_to_title(filename):
    title = filename
    if title.lower().endswith('.pdf'):
        title = title[:-4]
    title = urllib.parse.unquote(title)
    title = title.replace('-', ' ').replace('_', ' ')
    title = re.sub(r'\s+', ' ', title).strip()
    return title.title()

def classify_category_from_text(text):
    combined = text.lower()
    categories = []
    if any(k in combined for k in ["ism", "safety management", "dpa", "smc", "safety auditing", "audit", "doc "]):
        categories.append("SMC / ISM")
    if any(k in combined for k in ["isps", "security", "ssas", "cso", "piracy", "issc"]):
        categories.append("ISSC / ISPS")
    if any(k in combined for k in ["mlc", "maritime labour", "dmlc", "seafarer", "crew", "cook", "rest hours", "repatriation", "medical"]):
        categories.append("MLC")
    if any(k in combined for k in ["lifeboat", "lsa", "thickness", "ballast water", "bwm", "marpol", "solas", "dispensation", "exemption", "equipment", "fire", "co2", "radio"]):
        categories.append("Statüter / Donanım")
    if any(k in combined for k in ["recognized organization", "ro authorization", "surveyor", "class society"]):
        categories.append("Klas / RO Yetkileri")
        
    if not categories:
        return "Genel / Diğer"
    return ", ".join(categories)

# Dynamic Path Resolver
def resolve_path(prefix, subpath=""):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        base_dir,
        os.path.join(base_dir, '..'),
        os.path.join(base_dir, '..', '..')
    ]
    for parent_dir in search_dirs:
        if not os.path.exists(parent_dir):
            continue
        try:
            for item in os.listdir(parent_dir):
                if item.upper().startswith(prefix.upper()):
                    current_path = os.path.join(parent_dir, item)
                    if not subpath:
                        return current_path
                    
                    parts = [p for p in subpath.replace('\\', '/').split('/') if p]
                    for part in parts:
                        if os.path.isdir(current_path):
                            found = False
                            for sub_item in os.listdir(current_path):
                                clean_sub = sub_item.upper().replace('İ', 'I').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C').replace('Ğ', 'G')
                                clean_part = part.upper().replace('İ', 'I').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C').replace('Ğ', 'G')
                                if clean_sub == clean_part or clean_sub.startswith(clean_part):
                                    current_path = os.path.join(current_path, sub_item)
                                    found = True
                                    break
                            if not found:
                                current_path = os.path.join(current_path, part)
                        else:
                            current_path = os.path.join(current_path, part)
                    if os.path.exists(current_path):
                        return current_path
        except Exception:
            pass
    return os.path.join(base_dir, '..', prefix)

# Data Loader
@st.cache_data
def load_all_circulars():
    configs = {
        'Comoros': ('COMOROS', 'Sirkuler_PDFleri/GBI_Sirkuler_Analizi_Turkce.xlsx', 'Sirkuler_PDFleri'),
        'Guinea Bissau': ('GBI', 'Sirkuler_PDFleri/GBI_Sirkuler_Analizi_Turkce.xlsx', 'Sirkuler_PDFleri'),
        'Liberia': ('LIBERIA', 'Indirilen_Sirkulerler/Liberia_Sirkuler_Analizi_Turkce.xlsx', 'Indirilen_Sirkulerler'),
        'Palau': ('PALAU', 'Palau_Sirkuler_Analizi.xlsx', 'Sirkuler_PDFleri'),
        'Panama': ('PANAMA', 'PANAMA_Sirkuler_Analizi_Turkce.xlsx', ''),
        'Sierra Leone': ('SIERRA', 'Sirkuler_PDFleri/SLMARAD_Sirkuler_Analizi_Turkce.xlsx', 'Sirkuler_PDFleri')
    }
    
    all_records = []
    for flag_name, (prefix, excel_subpath, pdf_subpath) in configs.items():
        excel_path = resolve_path(prefix, excel_subpath)
        pdf_dir = resolve_path(prefix, pdf_subpath)
        
        excel_df = None
        if excel_path and os.path.exists(excel_path):
            try:
                excel_df = pd.read_excel(excel_path)
                excel_df = normalize_columns(excel_df)
                excel_df = excel_df.fillna("")
            except Exception as e:
                st.warning(f"⚠️ Hata: {flag_name} Excel dosyası okunamadı. ({str(e)})")
        
        pdf_files = []
        if pdf_dir and os.path.exists(pdf_dir):
            try:
                for root, dirs, files in os.walk(pdf_dir):
                    for f in files:
                        if f.lower().endswith('.pdf'):
                            pdf_files.append(f)
            except Exception:
                pass
        
        excel_lookup = {}
        if excel_df is not None:
            for _, row in excel_df.iterrows():
                fname = str(row.get('Filename', '')).strip()
                if fname:
                    excel_lookup[fname.lower()] = row
                    excel_lookup[urllib.parse.unquote(fname).lower()] = row
                    
        matched_excel_files = set()
        
        for pdf_file in pdf_files:
            decoded_pdf = urllib.parse.unquote(pdf_file)
            matched_row = None
            for key in [pdf_file.lower(), decoded_pdf.lower()]:
                if key in excel_lookup:
                    matched_row = excel_lookup[key]
                    matched_excel_files.add(key)
                    break
            
            rec = {
                'Flag': flag_name,
                'Filename': pdf_file,
                'Excel_Path': excel_path if excel_path else "",
                'PDF_Dir': pdf_dir if pdf_dir else ""
            }
            
            if matched_row is not None:
                rec['Category'] = clean_cell_text(str(matched_row.get('Category', ''))).strip()
                rec['Subject_EN'] = clean_cell_text(str(matched_row.get('Subject_EN', '')))
                rec['Subject_TR'] = clean_cell_text(str(matched_row.get('Subject_TR', '')))
                rec['References'] = clean_cell_text(str(matched_row.get('References', '')))
                rec['Summary_EN'] = clean_cell_text(str(matched_row.get('Summary_EN', '')))
                rec['Summary_TR'] = clean_cell_text(str(matched_row.get('Summary_TR', '')))
                rec['Recommendations_TR'] = clean_cell_text(str(matched_row.get('Recommendations_TR', '')))
                if not rec['Category']:
                    rec['Category'] = classify_category(rec)
            else:
                cleaned_title = clean_filename_to_title(pdf_file)
                rec['Category'] = classify_category_from_text(pdf_file + " " + cleaned_title)
                rec['Subject_EN'] = cleaned_title
                rec['Subject_TR'] = cleaned_title
                rec['References'] = "Belirtilmedi"
                rec['Summary_EN'] = "PDF dosyası klasörde mevcut. Excel özet tablosunda bulunmamaktadır."
                rec['Summary_TR'] = "PDF dosyası klasörde mevcut. Excel özet tablosunda bulunmamaktadır."
                rec['Recommendations_TR'] = "1. İlgili genelgeyi gemideki sirküler klasörüne ekleyin. 2. Gereksinimleri PSC denetimleri öncesinde kontrol listesine ekleyin."
                
            all_records.append(rec)
            
        if excel_df is not None:
            for _, row in excel_df.iterrows():
                fname = str(row.get('Filename', '')).strip()
                if not fname:
                    continue
                fname_lower = fname.lower()
                decoded_fname_lower = urllib.parse.unquote(fname).lower()
                
                if fname_lower not in matched_excel_files and decoded_fname_lower not in matched_excel_files:
                    rec = {
                        'Flag': flag_name,
                        'Filename': fname,
                        'Excel_Path': excel_path if excel_path else "",
                        'PDF_Dir': pdf_dir if pdf_dir else "",
                        'Category': clean_cell_text(str(row.get('Category', ''))).strip(),
                        'Subject_EN': clean_cell_text(str(row.get('Subject_EN', ''))),
                        'Subject_TR': clean_cell_text(str(row.get('Subject_TR', ''))),
                        'References': clean_cell_text(str(row.get('References', ''))),
                        'Summary_EN': clean_cell_text(str(row.get('Summary_EN', ''))),
                        'Summary_TR': clean_cell_text(str(row.get('Summary_TR', ''))),
                        'Recommendations_TR': clean_cell_text(str(row.get('Recommendations_TR', '')))
                    }
                    if not rec['Category']:
                        rec['Category'] = classify_category(rec)
                    all_records.append(rec)
                    
    if not all_records:
        return pd.DataFrame(columns=['Filename', 'Category', 'Subject_EN', 'Subject_TR', 'References', 'Summary_EN', 'Summary_TR', 'Recommendations_TR', 'Flag', 'Excel_Path', 'PDF_Dir'])
    df = pd.DataFrame(all_records)
    df = df.fillna("")
    return df

# Helper to locate PDF file
def get_pdf_file_path(row):
    pdf_dir = row['PDF_Dir']
    filename = row['Filename']
    if not filename:
        return None
    path1 = os.path.join(pdf_dir, filename)
    if os.path.exists(path1):
        return path1
    decoded_filename = urllib.parse.unquote(filename)
    path2 = os.path.join(pdf_dir, decoded_filename)
    if os.path.exists(path2):
        return path2
    if os.path.exists(pdf_dir):
        for root, dirs, files in os.walk(pdf_dir):
            for f in files:
                if f.lower() == filename.lower() or f.lower() == decoded_filename.lower():
                    return os.path.join(root, f)
    return None

df_circulars = load_all_circulars()

FLAG_GUIDES = {
    'Panama': {
        'portal_url': 'https://www.amp.gob.pa/normatividad/page/73/',
        'description': 'Panama Denizcilik Otoritesi (PMA) / SEGUMAR kuralları kapsamındaki kritik denetim gereksinimleri.',
        'contacts': [
            {'name': 'SEGUMAR Head Office', 'email': 'segumar.headoffice@segumar.com', 'purpose': 'Teknik onaylar, muafiyetler ve idari izinler.'},
            {'name': 'SEGUMAR Istanbul Office', 'email': 'segumar@panama.org.tr', 'purpose': 'Türkiye ve çevre bölge yerel Segumar onayları.'},
            {'name': 'Maritime Security (ISPS)', 'email': 'threat@amp.gob.pa', 'purpose': 'SSAS test aktivasyonları ve resmi güvenlik raporlamaları.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**DPA Deklarasyon Onayı**: Şirket DPA atamasını SEGUMAR ofisine bildirmek zorundadır (MMC-197 / MMC-354). Gemide DPA tescil belgesinin kopyası bulunmalıdır.",
                "**Geçici (Interim) Denetim**: Geçici SMC denetimleri 6 aylık düzenlenir. Gemi tipine göre ek ISM gereklilikleri (örneğin petrol tankerlerinde cargo handling safety) kontrol edilmelidir.",
                "**DPA Nitelikleri**: Atanan DPA'in denizcilik geçmişi ve uygun ISM eğitimi belgeleri doğrulanmalıdır."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**SSAS Alarm Mesajı Yönlendirmesi**: SSAS ayarlarının doğrudan Panama Denizcilik Otoritesi SEGUMAR ofisine (`threat@amp.gob.pa`) alarm gönderecek şekilde programlanmış olması zorunludur (MMC-131, MMC-205).",
                "**Yıllık SSAS Test Raporlaması**: Yılda en az bir kez SEGUMAR ile koordineli test yapılmalı ve onay alınmalıdır.",
                "**CSO Bildirimi**: Şirket Güvenlik Sorumlusu (CSO) SEGUMAR tarafından kayıt altına alınmış olmalıdır (MMC-206)."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**DMLC Kısım I & II**: DMLC Kısım I doğrudan Panama İdaresi tarafından düzenlenir. DMLC Kısım II ise RO (Sınıf Kuruluşu) tarafından incelenip onaylandıktan sonra gemide bulundurulmalıdır.",
                "**MLC Mali Güvence Sertifikaları**: MLC Kural 2.5 (Terk edilme) ve Kural 4.2 (Gemi sahibi sorumluluğu) kapsamındaki sigorta sertifikaları gemide görünür bir yere asılmalıdır. Poliçe kapsamında Panama bayrağı ibaresi aranır.",
                "**Asgari Personel (Safe Manning)**: Gemideki fiili mürettebat sayısı Minimum Güvenli Personel Belgesi (MSMC) gerekliliklerinin altına düşmemelidir."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Muafiyet ve Dispansasyonlar**: Herhangi bir SOLAS/MARPOL ekipman muafiyeti verilmeden önce SEGUMAR'dan yazılı resmi izin (Authorization) alınmalıdır. RO bu izne istinaden sertifika düzenler.",
                "**LRIT Uygunluk Test Raporu (CTR)**: Yetkili bir servis sağlayıcı tarafından verilmiş güncel ve geçerli LRIT test raporu gemide bulunmalıdır (MMC-195)."
            ]
        }
    },
    'Sierra Leone': {
        'portal_url': 'https://slmarad.com/maritime-circulars/',
        'description': 'SLMARAD (Sierra Leone Denizcilik İdaresi) teknik direktifleri ve PHRS sörveyörlerinin dikkat etmesi gereken kurallar.',
        'contacts': [
            {'name': 'SLMARAD Technical Dept', 'email': 'technical@slmarad.com', 'purpose': 'Teknik muafiyetler, dispansasyonlar ve sörvey onayları.'},
            {'name': 'Vessel Registration Division', 'email': 'registration@slmarad.com', 'purpose': 'Gemi tescili ve CSR başvuruları.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**ISM Deklarasyonları**: Şirket ve DPA deklarasyon formları SLMARAD formatına uygun doldurulmuş ve tescil edilmiş olmalıdır.",
                "**Raporlama**: ISM sörveylerinde tespit edilen Majör Uygunsuzluklar (Major NC) 24 saat içinde SLMARAD'a iletilmelidir (MC4)."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**SSP Güvenlik Planı Onayı**: Gemi Güvenlik Planı (SSP) idare tarafından veya idare adına yetkilendirilen RO tarafından damgalanmış olmalıdır.",
                "**SSAS E-posta Ayarı**: SSAS alarm alıcı e-postalarına `technical@slmarad.com` adresinin eklendiği test edilmelidir (MC7)."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**Onaylı P&I Listesi Kontrolü**: MLC kapsamındaki mali güvence sigortaları (Terk edilme ve Ölüm/Yaralanma) sadece SLMARAD tarafından yayınlanan onaylı sigorta şirketlerinden (MC47) alınmış olmalıdır.",
                "**Gemiadamı Sözleşmesi (SEA)**: Sözleşme şartlarının Sierra Leone denizcilik mevzuatı gereksinimlerini (MC17) karşıladığı teyit edilmelidir."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Nairobi Enkaz Kaldırma Sertifikası**: Nairobi Enkaz Kaldırma Sözleşmesi (2007) sertifikası orijinal olarak gemide taşınmalıdır (Maritime Circular No.40).",
                "**Bunker CLC**: 1000 GT üzerindeki tüm gemilerde geçerli Bunker CLC sertifikası bulunmalıdır (MC6).",
                "**Ekipman Muafiyeti**: İdarenin yazılı izni olmadan RO tarafından hiçbir muafiyet (exemption) düzenlenemez (MC12)."
            ]
        }
    },
    'Comoros': {
        'portal_url': 'http://bihlyumov.com/circulars/',
        'description': 'Union of the Comoros (ANAM) idaresine ait sörvey yönergeleri ve dikkat edilecek hususlar.',
        'contacts': [
            {'name': 'ANAM Technical Office', 'email': 'tech@bihlyumov.com', 'purpose': 'Teknik onaylar, muafiyetler ve sörvey uzatma talepleri.'},
            {'name': 'Comoros Port State Control Liaison', 'email': 'operations@anam-comoros.org', 'purpose': 'PSC denetimleri ve gemi tutulma (detention) raporlamaları.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**DPA ve Şirket Deklarasyonları**: ANAM'a kayıtlı DPA atamalarının güncelliği kontrol edilmelidir.",
                "**ISM Raporları**: Yıllık ara denetimlerin zamanında yapıldığı ve raporların idare portalına yüklendiği doğrulanmalıdır."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**SSAS Test Protokolü**: SSAS alarmlarının `tech@bihlyumov.com` adresine uyarı gönderecek şekilde yapılandırılmış olması gerekir.",
                "**Güvenlik Seviyesi (ISPS Security Level)**: Doğu Akdeniz gibi yüksek riskli bölgelerde seyreden gemilerde Güvenlik Seviyesi III uygulamalarına dikkat edilmelidir."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**MLC Sözleşmeleri**: Gemiadamı iş sözleşmeleri (SEA) MLC 2006 Kural 2.1'e uygun olmalıdır. Çalışma ve dinlenme saatleri kayıtları (Rest Hours) eksiksiz tutulmalıdır.",
                "**Mali Güvence Poliçeleri**: Terk edilme ve tıbbi sorumluluk sigortalarının ANAM tarafından onaylı P&I kulüpleri listesindeki firmalardan yapılmış olması gerekir."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Muafiyet Prosedürleri (Exemptions)**: SOLAS/MARPOL donanım muafiyetlerinde ANAM'ın onay prosedürü (Circular 08) harfiyen takip edilmeli, onay belgesi olmadan muafiyet verilmemelidir.",
                "**PSC Raporlama Zorunluluğu**: PSC denetimlerinde geminin eksiklik alması veya tutulması durumunda, en geç 24 saat içinde durum idareye raporlanmalıdır."
            ]
        }
    },
    'Guinea Bissau': {
        'portal_url': 'https://gbisr.com/marine-circulars/',
        'description': 'Guinea Bissau Uluslararası Gemi Sicili (GBISR) kuralları ve PHRS sörveyörlerinin yetki kapsamındaki dikkat edecekleri hususlar.',
        'contacts': [
            {'name': 'GBISR Technical Division', 'email': 'technical@gbisr.com', 'purpose': 'Sörvey izinleri, teknik muafiyetler ve operasyonel direktifler.'},
            {'name': 'General Registrar', 'email': 'gregory@gbisr.com', 'purpose': 'Genel tescil ve sertifika tescil doğrulamaları.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**ISM Raporlaması**: ISM iç denetim kayıtları ve DPA atama formunun güncel kopyası SMS dosyalarında bulunmalıdır.",
                "**SMC Onayı**: Sörveyör, ara denetim sonrasında sertifikayı onaylamalı ve raporu GBISR teknik servisine e-posta ile sunmalıdır."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**Gemide Bulunması Gereken Belgeler**: Gemide bulunması zorunlu tüm ISPS ve güvenlik dokümanları MARCIR-06-2022'ye uygun şekilde düzenlenmelidir.",
                "**SSAS Yapılandırması**: SSAS alarm sisteminin teknik departmana doğrudan uyarı vermesi sağlanmalıdır."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**MLC Değişiklikleri ve Sorumluluklar**: MARCIR-03-2023 uyarınca, gemi sahibinin seafarer terk edilmesi, sakatlanması veya ölümü durumunda mali güvence sağlayan sigorta poliçelerini kontrol edin.",
                "**Mutfak ve Aşçı Kuralları**: Gemide 10 veya daha fazla personel varsa, onaylı aşçı sertifikası aranmalıdır. Gıda ve içme suyu ücretsiz sağlanmalıdır."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Belge Listesi Kontrolü**: Gemide bulunması gereken statüter sertifikalar ve kılavuzların güncel listesi MARCIR-06-2022 genelgesine göre kontrol edilmelidir.",
                "**P&I ve Sigorta Limitleri**: Nairobi Enkaz Kaldırma ve Bunker CLC sigortalarının geçerli poliçe limitleri kontrol edilmelidir."
            ]
        }
    },
    'Palau': {
        'portal_url': 'https://www.palaushipreg.com/information-center/online-library/marine-documents',
        'description': 'Palau Uluslararası Gemi Sicili (PISR) teknik yönergeleri ve sörveyör kılavuz maddeleri.',
        'contacts': [
            {'name': 'PISR Technical Dept', 'email': 'technical@palaushipreg.com', 'purpose': 'Teknik muafiyetler, sörvey onay talepleri ve dispensasyonlar.'},
            {'name': 'Marine Safety Department', 'email': 'marine@palaushipreg.com', 'purpose': 'PSC denetimleri, kaza raporlama ve genel deniz emniyeti.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**DPA Nitelikleri (MC 175)**: Atanan DPA'in eğitim ve nitelikleri MC 175 standardına uygun olmalıdır (asgari deniz tecrübesi veya denizcilik yönetimi eğitimi).",
                "**ISM ve ISPS Deklarasyonları (MC 158)**: Şirket ve DPA deklarasyonları tescil ofisine PISR standart formlarıyla bildirilmiş olmalıdır."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**CSO Rehberi (MC 106)**: Şirket Güvenlik Sorumlusu (CSO) tarafından mürettebata verilen ISPS eğitim kayıtları ve korsanlık/güvenlik tehditlerine hazırlık planları kontrol edilmelidir.",
                "**Siber Risk Yönetimi (MC 110)**: Siber güvenlik önlemlerinin gemi SMS (Güvenlik Yönetim Sistemi) planına entegre edildiği doğrulanmalıdır."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**Onaylı Sigorta Şirketleri (MC 137 / MC 148)**: MLC mali güvence sertifikalarını düzenleyen sigorta şirketlerinin PISR onaylı listede yer alıp almadığı kontrol edilmelidir.",
                "**Gemiadamı İşe Alım Hizmetleri (MC 138)**: Sözleşmeli personelin işe alım ajanslarının (SRPS) MLC lisansları doğrulanmalıdır."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Gemide Taşınacak Sertifikalar (MC 172)**: Palau bayraklı gemide bulundurulması zorunlu olan sertifika ve belgelerin basılı veya elektronik asılları MC 172'ye göre doğrulanmalıdır.",
                "**BWM ve Balast Suyu Yönetimi**: Balast suyu arıtma ünitesi (BWMS) kayıt defteri ve güncel arıtma parametreleri doğrulanmalıdır."
            ]
        }
    },
    'Liberia': {
        'portal_url': 'https://www.liscr.com/onlinelibrary/',
        'description': 'Liberia Denizcilik Sicili (LISCR) teknik kuralları ve PHRS sörveyör kontrol listesi.',
        'contacts': [
            {'name': 'LISCR Technical Support', 'email': 'technical@liscr.com', 'purpose': 'Teknik muafiyet onayları, SOLAS/MARPOL yorumları.'},
            {'name': 'Marine Safety & Audit', 'email': 'safety@liscr.com', 'purpose': 'ISM/ISPS/MLC denetim bildirimleri ve PSC koordinasyonu.'}
        ],
        'checklists': {
            'SMC / ISM (Güvenlik Yönetimi)': [
                "**DPA ve Master Deklarasyonu**: DPA deklarasyon formu (RLM-297b) güncel olmalı ve gemide saklanmalıdır.",
                "**Denetim Prosedürleri (ADM-001)**: Geçici ve tam dönem SMC denetim raporlarının idare standartlarına uygunluğu ve zamanlaması kontrol edilmelidir."
            ],
            'ISSC / ISPS (Gemi Güvenliği)': [
                "**ISPS Kodu Uygulaması (ISP-001)**: Gemi Güvenlik Planının (SSP) LISCR onaylı güncel revizyonu kontrol edilmelidir. SSAS test log kayıtları incelenmelidir.",
                "**CSO İletişim Bilgileri**: Gemide CSO tescil formu ve 24 saat erişilebilir iletişim bilgileri doğrulanmalıdır."
            ],
            'MLC (Denizcilik Çalışma Sözleşmesi)': [
                "**DMLC Part I & II**: DMLC Part I LISCR portalından online talep edilerek alınmış olmalıdır. DMLC Part II ise RO onaylı olmalıdır.",
                "**Çalışma Sözleşmeleri**: Gemiadamlarının SEA sözleşmelerindeki maaş, izin ve sağlık sigortası maddelerinin Liberya İş Kanununa uygunluğu teyit edilmelidir."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Gereken Yayınlar Listesi (ADM-007)**: Liberya bayraklı gemide taşınması zorunlu olan tüm uluslararası kodlar (SOLAS, MARPOL, vb.) ve Liberya genelgelerinin güncel listesi kontrol edilmelidir.",
                "**Ballast Suyu Kuralları (Marine Advisory 02/2017)**: ABD sularına giren gemilerde USCG ballast deşarj onay kriterleri ve BWM kayıt defteri doğrulanmalıdır.",
                "**Biyoyakıt Karışımları (Marine Advisory 14/2025)**: Biyoyakıt taşıyan veya yakıt olarak kullanan gemilerde MARPOL Ek I gereklilikleri kontrol edilmelidir."
            ]
        }
    }
}

# SIDEBAR FILTERS (Clean Light Design)
st.sidebar.markdown(f'<h2 style="color:#0369a1;font-size:1.4rem;margin-bottom:15px;font-weight:600;">🔍 Filtre Paneli</h2>', unsafe_allow_html=True)

# Page Navigation
page = st.sidebar.radio(
    "Görünüm Seçin",
    ["📊 Dashboard & Arama", "📋 Bayrak Kontrol Listeleri", "📋 Sörveyör Denetim Rehberi", "🌐 Canlı Bayrak Siteleri"]
)

# Shared Filters in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown('<p style="color:#64748b;font-size:0.85rem;font-weight:600;text-transform:uppercase;">Veri Filtreleri</p>', unsafe_allow_html=True)

if not df_circulars.empty:
    all_flags = ["Tümü"] + sorted(list(df_circulars['Flag'].unique()))
    selected_flag = st.sidebar.selectbox("Bayrak Devleti", all_flags, key="selected_flag")
    
    unique_cats = set()
    for cat_str in df_circulars['Category'].dropna().unique():
        for c in str(cat_str).split(","):
            c_clean = c.strip()
            if c_clean:
                unique_cats.add(c_clean)
    all_categories = ["Tümü"] + sorted(list(unique_cats))
    selected_cat = st.sidebar.selectbox("Sertifika / Konu Kategorisi", all_categories, key="selected_cat")
    
    search_query = st.sidebar.text_input("Anahtar Kelime Ara (TR / EN)", key="search_query")
else:
    selected_flag = "Tümü"
    selected_cat = "Tümü"
    search_query = ""

# Sidebar Footer
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Verileri Yenile (Clear Cache)"):
    st.cache_data.clear()
    st.sidebar.success("Önbellek temizlendi!")
st.sidebar.markdown(
    '<p style="color:#64748b;font-size:0.8rem;text-align:center;">🚢 PHRS Vessel Survey Portal v1.0.0<br>© 2026 Phoenix Register of Shipping</p>', 
    unsafe_allow_html=True
)

# PAGE 1: DASHBOARD & CIRCULARS SEARCH
if page == "📊 Dashboard & Arama":
    st.markdown('<h1 class="gradient-text gradient-header">🚢 PHRS Bayrak Sirkülerleri Portalı</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:1.1rem;margin-bottom:20px;">PHRS yetki kapsamındaki bayrak devletlerinin sirküler analiz tablosu, tavsiyeler ve statutory rehberlik veritabanı.</p>', unsafe_allow_html=True)
    
    if df_circulars.empty:
        st.error("❌ Veri tabanında sirküler kaydı bulunamadı! Lütfen Excel dosyalarının belirtilen klasörlerde mevcut olduğundan emin olun.")
        st.stop()
        
    # Apply Filtering
    filtered_df = df_circulars.copy()
    if selected_flag != "Tümü":
        filtered_df = filtered_df[filtered_df['Flag'] == selected_flag]
    if selected_cat != "Tümü":
        filtered_df = filtered_df[filtered_df['Category'].apply(lambda x: selected_cat.lower() in str(x).lower())]
    if search_query:
        query = search_query.lower()
        filtered_df = filtered_df[
            filtered_df['Filename'].str.lower().str.contains(query) |
            filtered_df['Subject_EN'].str.lower().str.contains(query) |
            filtered_df['Subject_TR'].str.lower().str.contains(query) |
            filtered_df['References'].str.lower().str.contains(query) |
            filtered_df['Summary_EN'].str.lower().str.contains(query) |
            filtered_df['Summary_TR'].str.lower().str.contains(query) |
            filtered_df['Recommendations_TR'].str.lower().str.contains(query)
        ]
        
    # Flag-filtered dataframe for counts
    flag_filtered_df = df_circulars.copy()
    if selected_flag != "Tümü":
        flag_filtered_df = flag_filtered_df[flag_filtered_df['Flag'] == selected_flag]
        
    total_circs = len(flag_filtered_df)
    filtered_circs_count = len(filtered_df)
    
    ism_count = len(flag_filtered_df[flag_filtered_df['Category'].apply(lambda x: 'ism' in str(x).lower() or 'smc' in str(x).lower())])
    mlc_count = len(flag_filtered_df[flag_filtered_df['Category'].apply(lambda x: 'mlc' in str(x).lower())])
    isps_count = len(flag_filtered_df[flag_filtered_df['Category'].apply(lambda x: 'isps' in str(x).lower() or 'issc' in str(x).lower())])
    stat_count = len(flag_filtered_df[flag_filtered_df['Category'].apply(lambda x: 'statüter' in str(x).lower() or 'donanım' in str(x).lower() or 'exemption' in str(x).lower() or 'bwm' in str(x).lower())])
    
    # Custom Styling for KPI Buttons to look like Metrics
    st.markdown("""
    <style>
        div[data-testid="stColumn"] button {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 12px 5px !important;
            width: 100% !important;
            min-height: 95px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
            transition: all 0.2s ease-in-out !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            color: #64748b !important;
            font-size: 0.8rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            font-weight: 600 !important;
            text-align: center !important;
        }
        div[data-testid="stColumn"] button:hover {
            background-color: #f0f9ff !important;
            border-color: #bae6fd !important;
            box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.08) !important;
            transform: translateY(-1px) !important;
        }
        div[data-testid="stColumn"] button p {
            margin: 0 !important;
            line-height: 1.3 !important;
            text-align: center !important;
        }
        div[data-testid="stColumn"] button strong {
            font-size: 1.7rem !important;
            display: block !important;
            margin-bottom: 3px !important;
            font-weight: 700 !important;
        }
        /* Custom Colors for KPI metrics */
        div[data-testid="stColumn"]:nth-child(1) button strong { color: #0284c7 !important; }
        div[data-testid="stColumn"]:nth-child(2) button strong { color: #0284c7 !important; }
        div[data-testid="stColumn"]:nth-child(3) button strong { color: #db2777 !important; }
        div[data-testid="stColumn"]:nth-child(4) button strong { color: #7c3aed !important; }
        div[data-testid="stColumn"]:nth-child(5) button strong { color: #0891b2 !important; }
        div[data-testid="stColumn"]:nth-child(6) button strong { color: #059669 !important; }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button(f"**{total_circs}**\n\nToplam Sirküler", key="btn_total_circs"):
            st.session_state["selected_flag"] = "Tümü"
            st.session_state["selected_cat"] = "Tümü"
            st.session_state["search_query"] = ""
            st.rerun()
    with col2:
        if st.button(f"**{filtered_circs_count}**\n\nFiltrelenmiş", key="btn_filtered_circs"):
            st.session_state["selected_cat"] = "Tümü"
            st.session_state["search_query"] = ""
            st.rerun()
    with col3:
        if st.button(f"**{ism_count}**\n\nISM / SMC", key="btn_ism_count"):
            st.session_state["selected_cat"] = "SMC / ISM"
            st.session_state["search_query"] = ""
            st.rerun()
    with col4:
        if st.button(f"**{isps_count}**\n\nISPS / ISSC", key="btn_isps_count"):
            st.session_state["selected_cat"] = "ISSC / ISPS"
            st.session_state["search_query"] = ""
            st.rerun()
    with col5:
        if st.button(f"**{mlc_count}**\n\nMLC 2006", key="btn_mlc_count"):
            st.session_state["selected_cat"] = "MLC"
            st.session_state["search_query"] = ""
            st.rerun()
    with col6:
        if st.button(f"**{stat_count}**\n\nStatüter / Ekipman", key="btn_stat_count"):
            st.session_state["selected_cat"] = "Statüter / Donanım"
            st.session_state["search_query"] = ""
            st.rerun()
    
    st.markdown('<h3 class="gradient-subheader" style="margin-top:0;">🔍 Arama Sonuçları</h3>', unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.info("ℹ️ Kriterlere uyan sirküler bulunamadı. Lütfen filtreleri veya arama kelimesini değiştirin.")
    else:
        # Helper function for rendering flag section
        def render_flag_section(flag_df, flag_name):
            state_key = f"selected_fname_{flag_name}"
            doc_options = flag_df['Filename'].tolist()
            
            if not doc_options:
                st.info("Kriterlere uyan sirküler bulunamadı.")
                return
                
            if state_key not in st.session_state:
                st.session_state[state_key] = doc_options[0]
            elif st.session_state[state_key] not in doc_options:
                st.session_state[state_key] = doc_options[0]
                
            # Render dataframe with row selection enabled
            selection = st.dataframe(
                flag_df[['Category', 'Subject_TR', 'References', 'Filename']],
                use_container_width=True,
                column_config={
                    "Category": st.column_config.TextColumn("Kategori"),
                    "Subject_TR": st.column_config.TextColumn("Konu (Türkçe)"),
                    "References": st.column_config.TextColumn("Kural Dayanağı"),
                    "Filename": st.column_config.TextColumn("Dosya Adı")
                },
                on_select="rerun",
                selection_mode="single-row",
                key=f"df_{flag_name}"
            )
            
            # If a row was selected in the table, update the session state
            selected_rows = selection.selection.rows
            if selected_rows:
                clicked_fname = flag_df.iloc[selected_rows[0]]['Filename']
                if clicked_fname != st.session_state[state_key]:
                    st.session_state[state_key] = clicked_fname
                    st.rerun()
            
            st.markdown("---")
            st.markdown('<h4 style="color:#0369a1; font-weight:600;">📄 Sirküler Detayı, Yapılması Gerekenler & İndirme Paneli</h4>', unsafe_allow_html=True)
            
            def get_option_label(fname):
                rows = flag_df[flag_df['Filename'] == fname]
                if not rows.empty:
                    subj = rows.iloc[0]['Subject_TR']
                    return f"{subj if subj else fname}"
                return fname
                
            try:
                default_idx = doc_options.index(st.session_state[state_key])
            except ValueError:
                default_idx = 0
                
            selected_fname = st.selectbox(
                f"Detaylarını görmek, tavsiyeleri okumak ve indirmek istediğiniz {flag_name} sirkülerini seçin:",
                options=doc_options,
                format_func=get_option_label,
                index=default_idx,
                key=f"selected_doc_details_{flag_name}"
            )
            
            if selected_fname != st.session_state[state_key]:
                st.session_state[state_key] = selected_fname
                st.rerun()
            
            if selected_fname:
                selected_row = flag_df[flag_df['Filename'] == selected_fname].iloc[0]
                pdf_file_path = get_pdf_file_path(selected_row)
                
                card_html = textwrap.dedent(f"""
                <div class="glass-card" style="border-left: 5px solid #0284c7; background: #ffffff;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span style="font-size:1.3rem; font-weight:700; color:#0369a1;">{selected_row['Subject_TR'] if selected_row['Subject_TR'] else selected_row['Subject_EN']}</span>
                        <div>
                            <span class="badge badge-flag" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Flag']}</span>
                            <span class="badge badge-cat" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Category']}</span>
                        </div>
                    </div>
                    <p style="margin-bottom:12px; font-size:0.9rem; color:#64748b;">
                        <b>Dosya Adı:</b> {selected_row['Filename']} | 
                        <b>Referanslar / Kural Dayanağı:</b> {selected_row['References'] if selected_row['References'] else 'Belirtilmedi'}
                    </p>
                    <hr style="border-color:#e2e8f0; margin:15px 0;"/>
                    
                    <div style="display:grid; grid-template-columns: 1.2fr 1fr; gap:25px; font-size:0.95rem;">
                        <div>
                            <p style="color:#be185d; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Özet (TÜRKÇE)</p>
                            <p style="color:#334155; line-height:1.5; margin-bottom:15px;">{selected_row['Summary_TR'] if selected_row['Summary_TR'] else 'Türkçe özet bulunmamaktadır.'}</p>
                            
                            <p style="color:#0369a1; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Summary (ENGLISH)</p>
                            <p style="color:#334155; line-height:1.5;">{selected_row['Summary_EN'] if selected_row['Summary_EN'] else 'No English summary available.'}</p>
                        </div>
                        <div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 18px; box-shadow: inset 0 2px 4px rgba(2, 132, 199, 0.02);">
                            <p style="color:#0369a1; font-weight:700; margin-bottom:8px; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.5px;">📋 YAPILMASI GEREKENLER / TAVSİYELER</p>
                            <p style="color:#1e293b; line-height:1.6; font-size:0.95rem; font-weight:500;">
                                {selected_row.get('Recommendations_TR', 'İlgili sirküler belgesini gemideki klasöre ekleyin ve gereksinimleri PSC denetimleri öncesinde kontrol listesine ekleyin.')}
                            </p>
                        </div>
                    </div>
                </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 3, 6])
                with col1:
                    if pdf_file_path:
                        try:
                            with open(pdf_file_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button(
                                label="📄 PDF Sirkülerini İndir",
                                data=pdf_bytes,
                                file_name=selected_row['Filename'],
                                mime="application/pdf",
                                key=f"download_pdf_{flag_name}_{selected_fname}"
                            )
                        except Exception as e:
                            st.caption(f"⚠️ Dosya okunamadı: {str(e)}")
                    else:
                        st.button("❌ PDF Bulunamadı", disabled=True, key=f"download_err_{flag_name}_{selected_fname}")
                
                with col2:
                    flag_cfg = FLAG_GUIDES.get(selected_row['Flag'])
                    if flag_cfg:
                        st.markdown(f'<a href="{flag_cfg["portal_url"]}" target="_blank" style="text-decoration:none;"><button style="padding:4px 12px; border-radius:4px; border:1px solid #cbd5e1; background:transparent; color:#475569; font-size:0.9rem; height:38px; cursor:pointer; width:100%;">🌐 Bayrak Resmi Sitesine Git</button></a>', unsafe_allow_html=True)

        flags_in_data = sorted(list(filtered_df['Flag'].unique()))
        
        if len(flags_in_data) > 1:
            tab_titles = [f"{flag} ({len(filtered_df[filtered_df['Flag'] == flag])})" for flag in flags_in_data]
            tabs = st.tabs(tab_titles)
            for i, flag in enumerate(flags_in_data):
                with tabs[i]:
                    flag_df = filtered_df[filtered_df['Flag'] == flag]
                    render_flag_section(flag_df, flag)
        elif len(flags_in_data) == 1:
            flag = flags_in_data[0]
            flag_df = filtered_df[filtered_df['Flag'] == flag]
            render_flag_section(flag_df, flag)

# PAGE 2: FLAG GUIDES & CHECKLISTS
elif page == "📋 Bayrak Kontrol Listeleri":
    st.markdown('<h1 class="gradient-text gradient-header">📋 Bayrak Bazlı Kontrol Listesi & Statutory Kriterleri</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:1.1rem;margin-bottom:25px;">Statutory denetimler yaparken (ISM, MLC, ISPS, Statüter Ekipmanlar) bayraklara göre dikkat etmeniz gereken özel maddeler, tavsiyeler ve ek istekler.</p>', unsafe_allow_html=True)
    
    flags_with_guides = list(FLAG_GUIDES.keys())
    
    # Sync with unified sidebar selection or let select
    if selected_flag == "Tümü":
        selected_guide_flag = st.selectbox(
            "Detaylarını İncelemek İstediğiniz Bayrak Devleti:", 
            flags_with_guides,
            index=0,
            key="checklist_flag_selector"
        )
    else:
        if selected_flag in flags_with_guides:
            selected_guide_flag = selected_flag
            st.info(f"ℹ️ Sol menüden seçilen **{selected_flag}** bayrağı rehberi görüntüleniyor.")
        else:
            selected_guide_flag = flags_with_guides[0]
            st.warning(f"⚠️ Seçilen {selected_flag} için kılavuz kontrol listesi bulunmamaktadır. {selected_guide_flag} kılavuzu gösteriliyor.")
            
    guide = FLAG_GUIDES[selected_guide_flag]
    
    # Flag Details Header Card
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid #0284c7; background: #ffffff;">
        <h2 style="margin:0 0 5px 0; color:#0369a1;">{selected_guide_flag} Bayrak Rehberi</h2>
        <p style="margin-bottom:12px; font-size:1.05rem; color:#334155;">{guide['description']}</p>
        <p style="margin:0; font-size:0.9rem; color:#64748b;"> Resmi Circular Portalı: <a href="{guide['portal_url']}" target="_blank" style="color:#0284c7;text-decoration:none;font-weight:600;">{guide['portal_url']} ↗</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contacts Section
    st.markdown('<h3 class="gradient-subheader">📞 Kritik Bayrak İletişim Bilgileri (Segumar, Teknik, Alarm vb.)</h3>', unsafe_allow_html=True)
    
    cols = st.columns(len(guide['contacts']))
    for i, contact in enumerate(guide['contacts']):
        with cols[i]:
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:15px; height:100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                <p style="margin:0 0 4px 0; font-weight:700; color:#be185d; font-size:0.95rem;">{contact['name']}</p>
                <p style="margin:0 0 8px 0; font-size:0.85rem; color:#64748b; font-style:italic;">{contact['purpose']}</p>
                <p style="margin:0; font-size:0.9rem; font-weight:600; color:#0284c7;">✉️ {contact['email']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Checklist Tabs
    st.markdown('<h3 class="gradient-subheader">📝 Sörvey Kontrol Maddeleri (Surveyor Checklists)</h3>', unsafe_allow_html=True)
    
    checklists = guide['checklists']
    tab_names = list(checklists.keys()) + ["Tüm Sirkülerler"]
    tabs = st.tabs(tab_names)
    
    for i, name in enumerate(tab_names):
        with tabs[i]:
            if name == "Tüm Sirkülerler":
                st.markdown(f"<p style='color:#be185d; font-weight:600; font-size:1.05rem; margin-bottom:12px;'>📂 {selected_guide_flag} Bayrağına Ait Tüm Sirkülerler:</p>", unsafe_allow_html=True)
                cat_mask = pd.Series([True] * len(df_circulars))
            else:
                items = checklists[name]
                st.markdown(f"<p style='color:#be185d; font-weight:600; font-size:1.05rem; margin-bottom:12px;'>⚠️ {selected_guide_flag} Bayrağı Altında {name} Kontrollerinde Dikkat Edilecekler:</p>", unsafe_allow_html=True)
                
                for item in items:
                    st.markdown(f"""
                    <div style="background:#ffffff; border-left:3px solid #be185d; border-radius:0 6px 6px 0; padding:12px; margin-bottom:10px; font-size:0.95rem; line-height:1.4; color:#334155; border-top:1px solid #f1f5f9; border-right:1px solid #f1f5f9; border-bottom:1px solid #f1f5f9; box-shadow:0 1px 3px rgba(0,0,0,0.01);">
                        {item}
                    </div>
                    """, unsafe_allow_html=True)
                    
                tab_lower = name.lower()
                if 'ism' in tab_lower or 'smc' in tab_lower:
                    cat_mask = df_circulars['Category'].apply(lambda x: 'ism' in str(x).lower() or 'smc' in str(x).lower())
                elif 'isps' in tab_lower or 'issc' in tab_lower:
                    cat_mask = df_circulars['Category'].apply(lambda x: 'isps' in str(x).lower() or 'issc' in str(x).lower())
                elif 'mlc' in tab_lower:
                    cat_mask = df_circulars['Category'].apply(lambda x: 'mlc' in str(x).lower())
                elif 'statüter' in tab_lower or 'donanım' in tab_lower or 'ekipman' in tab_lower:
                    cat_mask = df_circulars['Category'].apply(lambda x: 'statüter' in str(x).lower() or 'donanım' in str(x).lower() or 'exemption' in str(x).lower() or 'bwm' in str(x).lower())
                else:
                    cat_mask = pd.Series([True] * len(df_circulars))
                
            tab_circs = df_circulars[(df_circulars['Flag'] == selected_guide_flag) & cat_mask]
            
            st.markdown("<hr style='border-color:#e2e8f0; margin:15px 0;'/>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='color:#0369a1; font-size:1.1rem; margin-bottom:10px;'>📂 İlgili Kategorideki Sirkülerler ({len(tab_circs)} Adet)</h4>", unsafe_allow_html=True)
            
            tab_search_key = f"search_tab_{selected_guide_flag}_{name.replace(' ', '_').replace('/', '_')}"
            tab_search = st.text_input("Bu kategorideki sirkülerlerde ara (Dosya, konu, özet veya tavsiye):", "", key=tab_search_key)
            
            if tab_search:
                q = tab_search.lower()
                tab_circs = tab_circs[
                    tab_circs['Filename'].str.lower().str.contains(q) |
                    tab_circs['Subject_EN'].str.lower().str.contains(q) |
                    tab_circs['Subject_TR'].str.lower().str.contains(q) |
                    tab_circs['References'].str.lower().str.contains(q) |
                    tab_circs['Summary_EN'].str.lower().str.contains(q) |
                    tab_circs['Summary_TR'].str.lower().str.contains(q) |
                    tab_circs['Recommendations_TR'].str.lower().str.contains(q)
                ]
                
            if tab_circs.empty:
                st.info("Bu kriterlere uyan sirküler bulunamadı.")
            else:
                tab_items_per_page = 10
                tab_total_pages = max(1, (len(tab_circs) + tab_items_per_page - 1) // tab_items_per_page)
                
                filter_str = f"{selected_guide_flag}_{name}_{tab_search}"
                tab_page_hash = hashlib.md5(filter_str.encode('utf-8')).hexdigest()[:8]
                tab_page_key = f"page_tab_{tab_page_hash}"
                
                current_tab_page = 1
                if tab_total_pages > 1:
                    col_space, col_select = st.columns([6, 4])
                    with col_select:
                        current_tab_page = st.selectbox(
                            "Sayfa Seçin",
                            options=list(range(1, tab_total_pages + 1)),
                            index=0,
                            key=tab_page_key,
                            format_func=lambda x: f"Sayfa {x} / {tab_total_pages}"
                        )
                
                t_start = (current_tab_page - 1) * tab_items_per_page
                t_end = min(t_start + tab_items_per_page, len(tab_circs))
                
                st.markdown(f"<p style='color: #64748b; font-size: 0.85rem; margin-bottom:10px;'>Toplam {len(tab_circs)} sirkülerden {t_start + 1} - {t_end} arası gösteriliyor</p>", unsafe_allow_html=True)
                
                page_circs = tab_circs.iloc[t_start:t_end]
                for t_idx, row in page_circs.iterrows():
                    pdf_file_path = get_pdf_file_path(row)
                    
                    card_html_tab = textwrap.dedent(f"""
                    <div class="glass-card" style="margin-bottom: 15px; padding: 15px; border-left: 3px solid #0284c7; background: #ffffff;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-size:1.05rem; font-weight:700; color:#0369a1;">{row['Subject_TR'] if row['Subject_TR'] else row['Subject_EN']}</span>
                            <span class="badge badge-cat" style="font-size:0.7rem;">{row['Category']}</span>
                        </div>
                        <p style="margin-bottom:6px; font-size:0.8rem; color:#64748b;"><b>Dosya:</b> {row['Filename']} | <b>Referans:</b> {row['References'] if row['References'] else 'Belirtilmedi'}</p>
                        <hr style="border-color:#e2e8f0; margin:6px 0;"/>
                        <div style="display:grid; grid-template-columns: 1.2fr 1fr 1fr; gap:15px; font-size:0.85rem;">
                            <div>
                                <p style="color:#be185d; font-weight:700; margin-bottom:2px; font-size:0.75rem;">ÖZET (TÜRKÇE)</p>
                                <p style="color:#334155; line-height:1.4;">{row['Summary_TR'] if row['Summary_TR'] else 'Türkçe özet bulunmamaktadır.'}</p>
                            </div>
                            <div>
                                <p style="color:#0369a1; font-weight:700; margin-bottom:2px; font-size:0.75rem;">SUMMARY (ENGLISH)</p>
                                <p style="color:#334155; line-height:1.4;">{row['Summary_EN'] if row['Summary_EN'] else 'No English summary available.'}</p>
                            </div>
                            <div style="background-color:#f0f9ff; border:1px solid #bae6fd; border-radius:4px; padding:10px;">
                                <p style="color:#0369a1; font-weight:700; margin-bottom:4px; font-size:0.75rem;">📋 TAVSİYELER / NE YAPILMALI</p>
                                <p style="color:#1e293b; line-height:1.4; font-weight:500;">{row.get('Recommendations_TR', 'İlgili sirküler belgesini gemideki klasöre ekleyin.')}</p>
                            </div>
                        </div>
                    </div>
                    """)
                    st.markdown(card_html_tab, unsafe_allow_html=True)
                    
                    col_dl, col_site, col_empty = st.columns([2.5, 2.5, 7])
                    with col_dl:
                        if pdf_file_path:
                            try:
                                with open(pdf_file_path, "rb") as f:
                                    pdf_bytes = f.read()
                                st.download_button(
                                    label="📄 PDF İndir",
                                    data=pdf_bytes,
                                    file_name=row['Filename'],
                                    mime="application/pdf",
                                    key=f"tab_dl_{t_idx}_{name.replace(' ', '_')}"
                                )
                            except Exception as e:
                                st.caption(f"⚠️ Hata: {str(e)}")
                        else:
                            st.button("❌ PDF Bulunamadı", key=f"tab_dl_err_{t_idx}_{name.replace(' ', '_')}", disabled=True)
                    with col_site:
                        flag_cfg = FLAG_GUIDES.get(row['Flag'])
                        if flag_cfg:
                            st.markdown(f'<a href="{flag_cfg["portal_url"]}" target="_blank" style="text-decoration:none;"><button style="padding:4px 10px; border-radius:4px; border:1px solid #cbd5e1; background:transparent; color:#475569; font-size:0.8rem; height:35px; cursor:pointer; width:100%;">🌐 Bayrak Sitesine Git</button></a>', unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
                
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h3 class="gradient-subheader">📂 {selected_guide_flag} Bayrağına Ait Tüm Sirkülerler</h3>', unsafe_allow_html=True)
    
    flag_circs = df_circulars[df_circulars['Flag'] == selected_guide_flag]
    if flag_circs.empty:
        st.info("Bu bayrağa ait veri tabanında taranmış sirküler bulunmamaktadır.")
    else:
        selection_p2 = st.dataframe(
            flag_circs[['Filename', 'Category', 'Subject_TR', 'References']],
            use_container_width=True,
            column_config={
                "Filename": st.column_config.TextColumn("Dosya Adı"),
                "Category": st.column_config.TextColumn("Kategori"),
                "Subject_TR": st.column_config.TextColumn("Konu (Türkçe)"),
                "References": st.column_config.TextColumn("Kural Dayanağı")
            },
            on_select="rerun",
            selection_mode="single-row",
            key=f"df_p2_{selected_guide_flag}"
        )
        
        selected_p2_rows = selection_p2.selection.rows
        if selected_p2_rows:
            selected_row = flag_circs.iloc[selected_p2_rows[0]]
            pdf_file_path = get_pdf_file_path(selected_row)
            
            st.markdown("---")
            st.markdown('<h4 style="color:#0369a1; font-weight:600;">📄 Seçilen Sirküler Detayı, Yapılması Gerekenler & İndirme Paneli</h4>', unsafe_allow_html=True)
            
            card_html = textwrap.dedent(f"""
            <div class="glass-card" style="border-left: 5px solid #0284c7; background: #ffffff;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span style="font-size:1.3rem; font-weight:700; color:#0369a1;">{selected_row['Subject_TR'] if selected_row['Subject_TR'] else selected_row['Subject_EN']}</span>
                    <div>
                        <span class="badge badge-flag" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Flag']}</span>
                        <span class="badge badge-cat" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Category']}</span>
                    </div>
                </div>
                <p style="margin-bottom:12px; font-size:0.9rem; color:#64748b;">
                    <b>Dosya Adı:</b> {selected_row['Filename']} | 
                    <b>Referanslar / Kural Dayanağı:</b> {selected_row['References'] if selected_row['References'] else 'Belirtilmedi'}
                </p>
                <hr style="border-color:#e2e8f0; margin:15px 0;"/>
                
                <div style="display:grid; grid-template-columns: 1.2fr 1fr; gap:25px; font-size:0.95rem;">
                    <div>
                        <p style="color:#be185d; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Özet (TÜRKÇE)</p>
                        <p style="color:#334155; line-height:1.5; margin-bottom:15px;">{selected_row['Summary_TR'] if selected_row['Summary_TR'] else 'Türkçe özet bulunmamaktadır.'}</p>
                        
                        <p style="color:#0369a1; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Summary (ENGLISH)</p>
                        <p style="color:#334155; line-height:1.5;">{selected_row['Summary_EN'] if selected_row['Summary_EN'] else 'No English summary available.'}</p>
                    </div>
                    <div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 18px; box-shadow: inset 0 2px 4px rgba(2, 132, 199, 0.02);">
                        <p style="color:#0369a1; font-weight:700; margin-bottom:8px; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.5px;">📋 YAPILMASI GEREKENLER / TAVSİYELER</p>
                        <p style="color:#1e293b; line-height:1.6; font-size:0.95rem; font-weight:500;">
                            {selected_row.get('Recommendations_TR', 'İlgili sirküler belgesini gemideki klasöre ekleyin ve gereksinimleri PSC denetimleri öncesinde kontrol listesine ekleyin.')}
                        </p>
                    </div>
                </div>
            </div>
            """)
            st.markdown(card_html, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 3, 6])
            with col1:
                if pdf_file_path:
                    try:
                        with open(pdf_file_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label="📄 PDF İndir",
                            data=pdf_bytes,
                            file_name=selected_row['Filename'],
                            mime="application/pdf",
                            key=f"download_pdf_p2_{selected_guide_flag}_{selected_row['Filename']}"
                        )
                    except Exception as e:
                        st.caption(f"⚠️ Dosya okunamadı: {str(e)}")
                else:
                    st.button("❌ PDF Bulunamadı", disabled=True, key=f"download_err_p2_{selected_guide_flag}_{selected_row['Filename']}")
            with col2:
                flag_cfg = FLAG_GUIDES.get(selected_row['Flag'])
                if flag_cfg:
                    st.markdown(f'<a href="{flag_cfg["portal_url"]}" target="_blank" style="text-decoration:none;"><button style="padding:4px 12px; border-radius:4px; border:1px solid #cbd5e1; background:transparent; color:#475569; font-size:0.9rem; height:38px; cursor:pointer; width:100%;">🌐 Bayrak Resmi Sitesine Git</button></a>', unsafe_allow_html=True)

# PAGE 3: SURVEYOR AUDIT GUIDE (Sörveyör Denetim Rehberi)
elif page == "📋 Sörveyör Denetim Rehberi":
    st.markdown('<h1 class="gradient-text gradient-header">📋 Sörveyör Denetim Rehberi</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:1.1rem;margin-bottom:25px;">Sörveyörlerin denetim sırasında gemilerde ve bayrak özelinde kontrol etmesi gereken maddeler ve ilgili sirküler dosyaları.</p>', unsafe_allow_html=True)
    
    flags_with_guides = list(FLAG_GUIDES.keys())
    
    col_flag, col_audit = st.columns(2)
    with col_flag:
        selected_guide_flag = st.selectbox(
            "Gemi Bayrağını Seçin (Select Vessel Flag):", 
            flags_with_guides,
            index=0,
            key="surveyor_guide_flag"
        )
    
    guide = FLAG_GUIDES[selected_guide_flag]
    audit_types = list(guide['checklists'].keys())
    
    with col_audit:
        selected_audit = st.selectbox(
            "Denetim Türünü Seçin (Select Audit Type):",
            audit_types,
            index=0,
            key="surveyor_guide_audit"
        )
        
    st.markdown("---")
    
    # Guide Flag Header Card
    st.markdown(textwrap.dedent(f"""
    <div class="glass-card" style="border-left: 5px solid #be185d; background: #ffffff;">
        <h3 style="margin:0 0 5px 0; color:#be185d;">{selected_guide_flag} Bayrağı - {selected_audit} Denetim Rehberi</h3>
        <p style="margin-bottom:10px; font-size:1.05rem; color:#334155;">{guide['description']}</p>
        <p style="margin:0; font-size:0.9rem; color:#64748b;"> Resmi Circular Portalı: <a href="{guide['portal_url']}" target="_blank" style="color:#0284c7;text-decoration:none;font-weight:600;">{guide['portal_url']} ↗</a></p>
    </div>
    """), unsafe_allow_html=True)
    
    # Display Checklist items
    items = guide['checklists'][selected_audit]
    
    st.markdown('<h4 style="color:#0369a1; font-weight:600;">📝 Kontrol Maddeleri ve Referans Sirkülerler</h4>', unsafe_allow_html=True)
    
    for idx, item in enumerate(items):
        # Find referenced circulars
        ref_circs = []
        codes = re.findall(r'\b(MMC-\d+|MC-\d+|MC\d+|Circular\s*\d+|MARCIR-\d+-\d+)\b', item, re.IGNORECASE)
        flag_circs = df_circulars[df_circulars['Flag'] == selected_guide_flag]
        
        for code in codes:
            cleaned_code = re.sub(r'[\s\-_]', '', code).lower()
            for c_idx, row in flag_circs.iterrows():
                fname = str(row['Filename']).lower()
                subject = str(row['Subject_EN']).lower() + " " + str(row['Subject_TR']).lower()
                ref = str(row['References']).lower()
                
                clean_fname = re.sub(r'[\s\-_]', '', fname)
                clean_subj = re.sub(r'[\s\-_]', '', subject)
                clean_ref = re.sub(r'[\s\-_]', '', ref)
                
                if cleaned_code in clean_fname or cleaned_code in clean_subj or cleaned_code in clean_ref:
                    ref_circs.append(row)
                    
        # Remove duplicates
        seen = set()
        unique_circs = []
        for r in ref_circs:
            if r['Filename'] not in seen:
                seen.add(r['Filename'])
                unique_circs.append(r)
                
        # Render item
        st.markdown(textwrap.dedent(f"""
        <div style="background:#ffffff; border-left:4px solid #0284c7; border-radius:0 6px 6px 0; padding:15px; margin-bottom:15px; font-size:1rem; line-height:1.5; color:#1e293b; border-top:1px solid #e2e8f0; border-right:1px solid #e2e8f0; border-bottom:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
            {item}
        </div>
        """), unsafe_allow_html=True)
        
        # If there are matched circulars, display download buttons and info
        if unique_circs:
            st.markdown("<p style='font-size:0.85rem; color:#64748b; font-weight:600; margin-left:15px; margin-top:-5px;'>🔗 Referans Genelgeler (Referenced Circulars):</p>", unsafe_allow_html=True)
            for c_idx, row in enumerate(unique_circs):
                pdf_file_path = get_pdf_file_path(row)
                
                col_btn, col_info = st.columns([3, 9])
                with col_btn:
                    if pdf_file_path:
                        try:
                            with open(pdf_file_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button(
                                label=f"📥 {row['Filename'][:25]}...",
                                data=pdf_bytes,
                                file_name=row['Filename'],
                                mime="application/pdf",
                                key=f"guide_dl_{idx}_{c_idx}_{selected_guide_flag}"
                            )
                        except Exception as e:
                            st.caption(f"⚠️ Hata: {str(e)}")
                    else:
                        st.button(f"❌ PDF Bulunamadı ({row['Filename'][:15]}...)", key=f"guide_dl_err_{idx}_{c_idx}_{selected_guide_flag}", disabled=True)
                with col_info:
                    st.markdown(textwrap.dedent(f"""
                    <div style="font-size:0.9rem; padding:5px 10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; min-height:38px; display:flex; align-items:center;">
                        <span style="font-weight:600; color:#0369a1; margin-right:8px;">Konu:</span>
                        <span style="color:#334155;">{row['Subject_TR'] if row['Subject_TR'] else row['Subject_EN']}</span>
                    </div>
                    """), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<h4 style="color:#0369a1; font-weight:600;">📂 {selected_guide_flag} Bayrağı Altındaki Tüm {selected_audit} Genelgeleri</h4>', unsafe_allow_html=True)
    
    # Filter the circular database for this flag and category
    cat_mask = pd.Series([True] * len(df_circulars))
    audit_lower = selected_audit.lower()
    if 'ism' in audit_lower or 'smc' in audit_lower:
        cat_mask = df_circulars['Category'].apply(lambda x: 'ism' in str(x).lower() or 'smc' in str(x).lower())
    elif 'isps' in audit_lower or 'issc' in audit_lower:
        cat_mask = df_circulars['Category'].apply(lambda x: 'isps' in str(x).lower() or 'issc' in str(x).lower())
    elif 'mlc' in audit_lower:
        cat_mask = df_circulars['Category'].apply(lambda x: 'mlc' in str(x).lower())
    elif 'statüter' in audit_lower or 'donanım' in audit_lower or 'ekipman' in audit_lower:
        cat_mask = df_circulars['Category'].apply(lambda x: 'statüter' in str(x).lower() or 'donanım' in str(x).lower() or 'exemption' in str(x).lower() or 'bwm' in str(x).lower())
        
    audit_circs = df_circulars[(df_circulars['Flag'] == selected_guide_flag) & cat_mask]
    
    if audit_circs.empty:
        st.info("Bu kategoriye ait sirküler bulunamadı.")
    else:
        selection_audit = st.dataframe(
            audit_circs[['Filename', 'Subject_TR', 'References']],
            use_container_width=True,
            column_config={
                "Filename": st.column_config.TextColumn("Dosya Adı"),
                "Subject_TR": st.column_config.TextColumn("Konu (Türkçe)"),
                "References": st.column_config.TextColumn("Kural Dayanağı")
            },
            on_select="rerun",
            selection_mode="single-row",
            key=f"df_audit_guide_{selected_guide_flag}_{selected_audit.replace(' ', '_').replace('/', '_')}"
        )
        
        selected_audit_rows = selection_audit.selection.rows
        if selected_audit_rows:
            selected_row = audit_circs.iloc[selected_audit_rows[0]]
            pdf_file_path = get_pdf_file_path(selected_row)
            
            st.markdown("---")
            st.markdown('<h4 style="color:#0369a1; font-weight:600;">📄 Seçilen Sirküler Detayı, Yapılması Gerekenler & İndirme Paneli</h4>', unsafe_allow_html=True)
            
            card_html = textwrap.dedent(f"""
            <div class="glass-card" style="border-left: 5px solid #0284c7; background: #ffffff;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span style="font-size:1.3rem; font-weight:700; color:#0369a1;">{selected_row['Subject_TR'] if selected_row['Subject_TR'] else selected_row['Subject_EN']}</span>
                    <div>
                        <span class="badge badge-flag" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Flag']}</span>
                        <span class="badge badge-cat" style="font-size:0.8rem; padding:6px 12px;">{selected_row['Category']}</span>
                    </div>
                </div>
                <p style="margin-bottom:12px; font-size:0.9rem; color:#64748b;">
                    <b>Dosya Adı:</b> {selected_row['Filename']} | 
                    <b>Referanslar / Kural Dayanağı:</b> {selected_row['References'] if selected_row['References'] else 'Belirtilmedi'}
                </p>
                <hr style="border-color:#e2e8f0; margin:15px 0;"/>
                
                <div style="display:grid; grid-template-columns: 1.2fr 1fr; gap:25px; font-size:0.95rem;">
                    <div>
                        <p style="color:#be185d; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Özet (TÜRKÇE)</p>
                        <p style="color:#334155; line-height:1.5; margin-bottom:15px;">{selected_row['Summary_TR'] if selected_row['Summary_TR'] else 'Türkçe özet bulunmamaktadır.'}</p>
                        
                        <p style="color:#0369a1; font-weight:700; margin-bottom:6px; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Summary (ENGLISH)</p>
                        <p style="color:#334155; line-height:1.5;">{selected_row['Summary_EN'] if selected_row['Summary_EN'] else 'No English summary available.'}</p>
                    </div>
                    <div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 18px; box-shadow: inset 0 2px 4px rgba(2, 132, 199, 0.02);">
                        <p style="color:#0369a1; font-weight:700; margin-bottom:8px; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.5px;">📋 YAPILMASI GEREKENLER / TAVSİYELER</p>
                        <p style="color:#1e293b; line-height:1.6; font-size:0.95rem; font-weight:500;">
                            {selected_row.get('Recommendations_TR', 'İlgili sirküler belgesini gemideki klasöre ekleyin ve gereksinimleri PSC denetimleri öncesinde kontrol listesine ekleyin.')}
                        </p>
                    </div>
                </div>
            </div>
            """)
            st.markdown(card_html, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 3, 6])
            with col1:
                if pdf_file_path:
                    try:
                        with open(pdf_file_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label="📄 PDF İndir",
                            data=pdf_bytes,
                            file_name=selected_row['Filename'],
                            mime="application/pdf",
                            key=f"download_pdf_guide_{selected_guide_flag}_{selected_row['Filename']}"
                        )
                    except Exception as e:
                        st.caption(f"⚠️ Hata: {str(e)}")
                else:
                    st.button("❌ PDF Bulunamadı", disabled=True, key=f"download_err_guide_{selected_guide_flag}_{selected_row['Filename']}")
            with col2:
                flag_cfg = FLAG_GUIDES.get(selected_row['Flag'])
                if flag_cfg:
                    st.markdown(f'<a href="{flag_cfg["portal_url"]}" target="_blank" style="text-decoration:none;"><button style="padding:4px 12px; border-radius:4px; border:1px solid #cbd5e1; background:transparent; color:#475569; font-size:0.9rem; height:38px; cursor:pointer; width:100%;">🌐 Bayrak Resmi Sitesine Git</button></a>', unsafe_allow_html=True)

# PAGE 4: FLAG OFFICIAL WEBSITES
elif page == "🌐 Canlı Bayrak Siteleri":
    st.markdown('<h1 class="gradient-text gradient-header">🌐 Canlı Bayrak Devletleri Sirküler Portalları</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:1.1rem;margin-bottom:20px;">En güncel sirküler, form ve mevzuat değişikliklerini teyit etmek için bayrakların resmi web sitelerini ziyaret edebilirsiniz.</p>', unsafe_allow_html=True)
    
    portals = {
        'Panama': {
            'name': 'Panama Maritime Authority (AMP) Normatividad',
            'url': 'https://www.amp.gob.pa/normatividad/page/73/',
            'desc': 'Panama Genelgesi (Merchant Marine Circulars - MMC) ve yasal kararnamelerin yayınlandığı resmi veritabanı.'
        },
        'Sierra Leone': {
            'name': 'Sierra Leone Maritime Administration (SLMARAD) Circulars',
            'url': 'https://slmarad.com/maritime-circulars/',
            'desc': 'Sierra Leone idaresi tarafından RO yetkilendirmeleri, gemi tescili ve statüter sörvey kurallarını bildiren güncel denizcilik genelgeleri.'
        },
        'Comoros': {
            'name': 'Union of Comoros Maritime Administration (ANAM)',
            'url': 'http://bihlyumov.com/circulars/',
            'desc': 'Comoros Bayraklı gemiler için yayınlanan sirkülerler, onaylı P&I sigorta şirketleri listesi ve PSC rapor formları.'
        },
        'Guinea Bissau': {
            'name': 'Guinea Bissau International Ships Registry (GBISR) Circulars',
            'url': 'https://gbisr.com/marine-circulars/',
            'desc': 'Guinea-Bissau gemi sicili resmi yönergeleri, MLC kuralları ve safe manning asgari personel kriterleri.'
        },
        'Palau': {
            'name': 'Palau International Ship Registry (PISR) Online Library',
            'url': 'https://www.palaushipreg.com/information-center/online-library/marine-documents',
            'desc': 'Palau Denizcilik sirkülerleri (Marine Circulars - MC), DPA kuralları, onaylı sigorta şirketleri ve statüter denetim yönergeleri.'
        },
        'Liberia': {
            'name': 'Liberian Registry (LISCR) Online Library',
            'url': 'https://www.liscr.com/onlinelibrary/',
            'desc': 'Liberya Denizcilik İlanları (Marine Notices), Denizcilik Genelgeleri (Marine Advisories) ve form kütüphanesi.'
        }
    }
    
    for flag_name, info in portals.items():
        st.markdown(f"""
        <div class="glass-card" style="background:#ffffff;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; color:#0369a1;">{flag_name}</h3>
                <a href="{info['url']}" target="_blank" style="background:#0284c7; color:#ffffff; padding:6px 16px; border-radius:4px; font-weight:700; text-decoration:none; font-size:0.9rem; box-shadow:0 2px 4px rgba(2,132,199,0.2);">Sitede Aç ↗</a>
            </div>
            <p style="margin:10px 0 5px 0; font-weight:600; color:#1e293b;">{info['name']}</p>
            <p style="margin:0; color:#64748b; font-size:0.9rem;">{info['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("---")
    st.markdown('<h2 class="gradient-text gradient-header" style="font-size:1.6rem; margin-top:20px;">🔄 Canlı Sirküler Güncelleme Takip Paneli</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.95rem;margin-bottom:15px;">Bayrakların resmi sitelerine bağlanarak yeni yayınlanan sirküler dosyası olup olmadığını yerel veritabanınızla karşılaştırarak denetleyin.</p>', unsafe_allow_html=True)
    
    if st.button("🔌 Sitelere Bağlan ve Yeni Yayınları Tara", type="primary"):
        import requests
        from bs4 import BeautifulSoup
        
        status_placeholder = st.empty()
        status_placeholder.info("🔄 Resmi web sitelerine bağlanılıyor, lütfen bekleyin...")
        
        known_files = set(df_circulars['Filename'].dropna().str.lower().str.strip().tolist())
        
        new_circulars = []
        
        # 1. Comoros
        try:
            r = requests.get('http://bihlyumov.com/circulars/', timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if '.pdf' in href.lower():
                        filename = href.split('/')[-1]
                        if filename.lower().strip() not in known_files:
                            title = a.text.strip() if a.text.strip() else filename
                            new_circulars.append({
                                'Flag': 'Comoros',
                                'Title': title,
                                'Filename': filename,
                                'Link': href
                            })
        except Exception as e:
            st.warning(f"⚠️ Comoros sitesine bağlanırken hata oluştu: {str(e)}")
            
        # 2. Guinea Bissau
        try:
            r = requests.get('https://gbisr.com/marine-circulars/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if '.pdf' in href.lower():
                        filename = href.split('/')[-1]
                        if filename.lower().strip() not in known_files:
                            title = a.text.strip() if a.text.strip() else filename
                            new_circulars.append({
                                'Flag': 'Guinea Bissau',
                                'Title': title,
                                'Filename': filename,
                                'Link': href
                            })
        except Exception as e:
            st.warning(f"⚠️ Guinea Bissau sitesine bağlanırken hata oluştu: {str(e)}")
            
        # 3. Sierra Leone
        try:
            r = requests.get('https://slmarad.com/maritime-circulars/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if '.pdf' in href.lower():
                        filename = href.split('/')[-1]
                        if filename.lower().strip() not in known_files:
                            title = a.text.strip() if a.text.strip() else filename
                            if not href.startswith('http'):
                                href = 'https://slmarad.com/' + href
                            new_circulars.append({
                                'Flag': 'Sierra Leone',
                                'Title': title,
                                'Filename': filename,
                                'Link': href
                            })
        except Exception as e:
            st.warning(f"⚠️ Sierra Leone sitesine bağlanırken hata oluştu: {str(e)}")
            
        status_placeholder.empty()
        
        if new_circulars:
            st.markdown(f'<div style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 15px; border-radius: 4px; margin-bottom: 20px;"><h4 style="color: #991b1b; margin:0 0 5px 0;">🚨 Yeni Sirküler(ler) Tespit Edildi!</h4><p style="color: #7f1d1d; margin:0; font-size:0.95rem;">Resmi sitelerde yayınlanmış ancak yerel klasörünüzde bulunmayan <b>{len(new_circulars)} adet</b> dosya tespit edildi. Bu dosyaları indirip ilgili bayrak klasörüne ekleyin.</p></div>', unsafe_allow_html=True)
            
            # Show new items in a table
            new_df = pd.DataFrame(new_circulars)
            st.dataframe(
                new_df[['Flag', 'Title', 'Filename']],
                use_container_width=True,
                column_config={
                    "Flag": st.column_config.TextColumn("Bayrak Devleti"),
                    "Title": st.column_config.TextColumn("Sirküler Başlığı / Tanım"),
                    "Filename": st.column_config.TextColumn("Dosya Adı")
                }
            )
            
            st.markdown("#### 📥 Yeni Dosyaları Doğrudan İndirin:")
            for item in new_circulars:
                st.markdown(f"- **[{item['Flag']}]** {item['Title']} &rarr; [PDF İndir / Kaynağa Git]({item['Link']})")
        else:
            st.success("✅ Tüm sirkülerleriniz güncel! Web sitelerinde yerel veritabanınızda bulunmayan yeni bir sirküler dosyası tespit edilmedi.")
