import os
import urllib.parse
import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="PHRS Bayrak Sirkülerleri & Statutory Kontrol Portalı",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Sleek Dark Mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main container background */
    .stApp {
        background-color: #0e1117;
        color: #e2e8f0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease-in-out;
    }
    .glass-card:hover {
        border-color: rgba(46, 134, 171, 0.5);
        box-shadow: 0 8px 32px 0 rgba(46, 134, 171, 0.15);
        transform: translateY(-2px);
    }
    
    /* Gradient Headers */
    .gradient-text {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    .gradient-header {
        font-size: 2.2rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .gradient-subheader {
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
        color: #00f2fe;
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
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        transition: all 0.2s;
    }
    .metric-box:hover {
        background: rgba(79, 172, 254, 0.05);
        border-color: rgba(79, 172, 254, 0.2);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00f2fe;
        margin-bottom: 5px;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #8b949e;
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
    .badge-flag { background: rgba(79, 172, 254, 0.15); color: #00f2fe; border: 1px solid rgba(79, 172, 254, 0.3); }
    .badge-cat { background: rgba(162, 59, 114, 0.15); color: #ff54b0; border: 1px solid rgba(162, 59, 114, 0.3); }

    /* Tables styles */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    .dataframe th {
        background-color: #1f242d;
        color: #00f2fe;
        font-weight: 600;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    .dataframe td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .dataframe tr:hover {
        background-color: rgba(255, 255, 255, 0.02);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #8b949e;
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

# Automatically classify categories for rows without a category (Panama, Sierra Leone)
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
        if 'dosya' in col_lower or 'sirküler' in col_lower or 'sirkuler' in col_lower:
            mapping[col] = 'Filename'
        elif 'kategori' in col_lower:
            mapping[col] = 'Category'
        elif 'konu' in col_lower:
            if 'türkçe' in col_lower or 'turkce' in col_lower or 'trke' in col_lower:
                mapping[col] = 'Subject_TR'
            else:
                mapping[col] = 'Subject_EN'
        elif 'referans' in col_lower or 'dayan' in col_lower:
            mapping[col] = 'References'
        elif 'özet' in col_lower or 'ozet' in col_lower or 'zet' in col_lower or 'summary' in col_lower:
            if 'türkçe' in col_lower or 'turkce' in col_lower or 'trke' in col_lower:
                mapping[col] = 'Summary_TR'
            else:
                mapping[col] = 'Summary_EN'
    df = df.rename(columns=mapping)
    return df

# Dynamic Path Resolver to handle Windows encoding issues in directory names
# and support both local and Streamlit Cloud layouts (where app.py is in repo root or subfolder)
def resolve_path(prefix, subpath=""):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # We search in multiple directory levels relative to app.py
    search_dirs = [
        base_dir,                             # app.py is at the root of the repo (Streamlit Cloud setup)
        os.path.join(base_dir, '..'),         # app.py is inside websitekodlar (Local setup)
        os.path.join(base_dir, '..', '..')    # fallback
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
                    
                    # Resolve subpath parts dynamically
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
            
    # Default fallback
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
    
    all_dfs = []
    
    for flag_name, (prefix, excel_subpath, pdf_subpath) in configs.items():
        excel_path = resolve_path(prefix, excel_subpath)
        pdf_dir = resolve_path(prefix, pdf_subpath)
        
        if excel_path and os.path.exists(excel_path):
            try:
                df = pd.read_excel(excel_path)
                df = normalize_columns(df)
                df['Flag'] = flag_name
                df['Excel_Path'] = excel_path
                df['PDF_Dir'] = pdf_dir
                all_dfs.append(df)
            except Exception as e:
                st.warning(f"⚠️ Hata: {flag_name} Excel dosyası yüklenemedi. ({str(e)})")
        else:
            st.info(f"ℹ️ Bilgi: {flag_name} Excel dosyası yerelde bulunamadı ({excel_path}).")
            
    if not all_dfs:
        return pd.DataFrame(columns=['Filename', 'Category', 'Subject_EN', 'Subject_TR', 'References', 'Summary_EN', 'Summary_TR', 'Flag', 'Excel_Path', 'PDF_Dir'])
        
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Standardize columns
    for col in ['Filename', 'Category', 'Subject_EN', 'Subject_TR', 'References', 'Summary_EN', 'Summary_TR']:
        if col not in merged_df.columns:
            merged_df[col] = ""
            
    merged_df = merged_df.fillna("")
    
    # Apply text cleaning for UI layout
    for col in ['Filename', 'Subject_EN', 'Subject_TR', 'References', 'Summary_EN', 'Summary_TR']:
        merged_df[col] = merged_df[col].apply(clean_cell_text)

        
    # Standardize Category
    def standardize_category(row):
        cat = str(row.get('Category', '')).strip()
        if not cat:
            return classify_category(row)
        return clean_cell_text(cat)
        
    merged_df['Category'] = merged_df.apply(standardize_category, axis=1)
    
    return merged_df


# Helper function to find a PDF file on the disk (supports URL-decoding and recursive checks)
def get_pdf_file_path(row):
    pdf_dir = row['PDF_Dir']
    filename = row['Filename']
    
    if not filename:
        return None
        
    # 1. Direct match
    path1 = os.path.join(pdf_dir, filename)
    if os.path.exists(path1):
        return path1
        
    # 2. URL Decoded match (e.g. MC%203%20(Rev.15).pdf -> MC 3 (Rev.15).pdf)
    decoded_filename = urllib.parse.unquote(filename)
    path2 = os.path.join(pdf_dir, decoded_filename)
    if os.path.exists(path2):
        return path2
        
    # 3. Recursive directory search (case insensitive)
    if os.path.exists(pdf_dir):
        for root, dirs, files in os.walk(pdf_dir):
            for f in files:
                if f.lower() == filename.lower() or f.lower() == decoded_filename.lower():
                    return os.path.join(root, f)
                    
    return None

# Load unified dataset
df_circulars = load_all_circulars()

# Curriculum database of flag guidelines & statutory checklists
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
                "**MLC Değişiklikleri ve Sorumluluklar**: MARCIR-03-2023 uyarınca, gemi sahibinin denizcilerin terk edilmesi, sakatlanması veya ölümü durumunda mali güvence sağlamakla yükümlü olduğu poliçeler doğrulanmalıdır.",
                "**Mutfak ve Aşçı Kuralları**: Gemide 10 veya daha fazla mürettebat varsa, ehil ve sertifikalı bir gemi aşçısı bulundurulması zorunludur. Yiyecek ve içme suyu mürettebata tamamen ücretsiz sağlanmalıdır."
            ],
            'Statüter Sörveyler & Ekipmanlar': [
                "**Belge Listesi Kontrolü**: Gemide bulunması gereken statüter sertifikalar ve güncel kılavuzların listesi MARCIR-06-2022 genelgesine göre kontrol edilmelidir.",
                "**P&I ve Sigorta Limitleri**: Nairobi Enkaz Kaldırma ve Bunker CLC sigortalarının geçerli poliçe limitleri ve geçerliliği kontrol edilmelidir."
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

# SIDEBAR FILTERS
st.sidebar.markdown(f'<h2 style="color:#00f2fe;font-size:1.4rem;margin-bottom:15px;font-weight:600;">🔍 Filtre Paneli</h2>', unsafe_allow_html=True)

# Page Navigation
page = st.sidebar.radio(
    "Görünüm Seçin",
    ["📊 Dashboard & Arama", "📋 Bayrak Kontrol Listeleri", "🌐 Canlı Bayrak Siteleri"]
)

# Shared Filters in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown('<p style="color:#8b949e;font-size:0.85rem;font-weight:600;text-transform:uppercase;">Veri Filtreleri</p>', unsafe_allow_html=True)

if not df_circulars.empty:
    all_flags = ["Tümü"] + sorted(list(df_circulars['Flag'].unique()))
    selected_flag = st.sidebar.selectbox("Bayrak Devleti", all_flags)
    
    # Extract unique categories
    unique_cats = set()
    for cat_str in df_circulars['Category'].dropna().unique():
        for c in str(cat_str).split(","):
            c_clean = c.strip()
            if c_clean:
                unique_cats.add(c_clean)
    all_categories = ["Tümü"] + sorted(list(unique_cats))
    selected_cat = st.sidebar.selectbox("Sertifika / Konu Kategorisi", all_categories)
    
    search_query = st.sidebar.text_input("Anahtar Kelime Ara (TR / EN)", "")
else:
    selected_flag = "Tümü"
    selected_cat = "Tümü"
    search_query = ""

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="color:#8b949e;font-size:0.8rem;text-align:center;">🚢 PHRS Vessel Survey Portal v1.0.0<br>© 2026 Phoenix Register of Shipping</p>', 
    unsafe_allow_html=True
)

# PAGE 1: DASHBOARD & CIRCULARS SEARCH
if page == "📊 Dashboard & Arama":
    st.markdown('<h1 class="gradient-text gradient-header">🚢 PHRS Bayrak Sirkülerleri Portalı</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:20px;">Yetkili bayrak devletlerinin sirküler analiz tablosu, arama motoru ve statutory gereklilik kütüphanesi.</p>', unsafe_allow_html=True)
    
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
            filtered_df['Summary_TR'].str.lower().str.contains(query)
        ]
        
    # KPI metrics row
    total_circs = len(df_circulars)
    filtered_circs_count = len(filtered_df)
    
    # Calculate categories count
    ism_count = len(df_circulars[df_circulars['Category'].apply(lambda x: 'ism' in str(x).lower() or 'smc' in str(x).lower())])
    mlc_count = len(df_circulars[df_circulars['Category'].apply(lambda x: 'mlc' in str(x).lower())])
    isps_count = len(df_circulars[df_circulars['Category'].apply(lambda x: 'isps' in str(x).lower() or 'issc' in str(x).lower())])
    stat_count = len(df_circulars[df_circulars['Category'].apply(lambda x: 'statüter' in str(x).lower() or 'donanım' in str(x).lower() or 'exemption' in str(x).lower() or 'bwm' in str(x).lower())])
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-val">{total_circs}</div>
            <div class="metric-lbl">Toplam Sirküler</div>
        </div>
        <div class="metric-box">
            <div class="metric-val" style="color: #4facfe;">{filtered_circs_count}</div>
            <div class="metric-lbl">Filtrelenmiş</div>
        </div>
        <div class="metric-box">
            <div class="metric-val" style="color: #ff54b0;">{ism_count}</div>
            <div class="metric-lbl">ISM / SMC</div>
        </div>
        <div class="metric-box">
            <div class="metric-val" style="color: #a23b72;">{isps_count}</div>
            <div class="metric-lbl">ISPS / ISSC</div>
        </div>
        <div class="metric-box">
            <div class="metric-val" style="color: #00f2fe;">{mlc_count}</div>
            <div class="metric-lbl">MLC 2006</div>
        </div>
        <div class="metric-box">
            <div class="metric-val" style="color: #2e86ab;">{stat_count}</div>
            <div class="metric-lbl">Statüter / Ekipman</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show circulars list
    st.markdown('<h3 class="gradient-subheader" style="margin-top:0;">🔍 Arama Sonuçları</h3>', unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.info("ℹ️ Kriterlere uyan sirküler bulunamadı. Lütfen filtreleri veya arama kelimesini değiştirin.")
    else:
        # We display the data using st.expander for detailed card layout
        for idx, row in filtered_df.iterrows():
            pdf_file_path = get_pdf_file_path(row)
            
            with st.container():
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:1.1rem; font-weight:700; color:#00f2fe;">{row['Subject_TR'] if row['Subject_TR'] else row['Subject_EN']}</span>
                        <div>
                            <span class="badge badge-flag">{row['Flag']}</span>
                            <span class="badge badge-cat">{row['Category']}</span>
                        </div>
                    </div>
                    <p style="margin-bottom:6px; font-size:0.85rem; color:#8b949e;"><b>Dosya Adı:</b> {row['Filename']} | <b>Referanslar:</b> {row['References'] if row['References'] else 'Belirtilmedi'}</p>
                    <hr style="border-color:rgba(255,255,255,0.05); margin:8px 0;"/>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:0.9rem;">
                        <div>
                            <p style="color:#ff54b0; font-weight:600; margin-bottom:4px; font-size:0.8rem; text-transform:uppercase;">Özet (TÜRKÇE)</p>
                            <p style="color:#d1d5db; line-height:1.4;">{row['Summary_TR'] if row['Summary_TR'] else 'Türkçe özet bulunmamaktadır.'}</p>
                        </div>
                        <div>
                            <p style="color:#00f2fe; font-weight:600; margin-bottom:4px; font-size:0.8rem; text-transform:uppercase;">Summary (ENGLISH)</p>
                            <p style="color:#9ca3af; line-height:1.4;">{row['Summary_EN'] if row['Summary_EN'] else 'No English summary available.'}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render PDF actions inside st.container using native streamlit buttons
                col1, col2, col3 = st.columns([2, 2, 8])
                with col1:
                    if pdf_file_path:
                        try:
                            with open(pdf_file_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button(
                                label="📄 PDF İndir",
                                data=pdf_bytes,
                                file_name=row['Filename'],
                                mime="application/pdf",
                                key=f"dl_{idx}"
                            )
                        except Exception as e:
                            st.caption(f"⚠️ Dosya okunamadı: {str(e)}")
                    else:
                        st.button("❌ PDF Bulunamadı", key=f"dl_err_{idx}", disabled=True)
                
                with col2:
                    # Link to flag website details if available
                    flag_cfg = FLAG_GUIDES.get(row['Flag'])
                    if flag_cfg:
                        st.markdown(f'<a href="{flag_cfg["portal_url"]}" target="_blank"><button style="padding:4px 12px; border-radius:4px; border:1px solid rgba(255,255,255,0.15); background:transparent; color:#e2e8f0; font-size:0.85rem; height:38px; cursor:pointer;">🌐 Bayrak Sitesine Git</button></a>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

# PAGE 2: FLAG GUIDES & CHECKLISTS
elif page == "📋 Bayrak Kontrol Listeleri":
    st.markdown('<h1 class="gradient-text gradient-header">📋 Bayrak Bazlı Kontrol Listesi & Statutory Kriterleri</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:25px;">Statutory denetimler yaparken (ISM, MLC, ISPS, Statüter Ekipmanlar) bayraklara göre dikkat etmeniz gereken özel maddeler ve ek istekler.</p>', unsafe_allow_html=True)
    
    # Selector for Flag Guide
    flags_with_guides = list(FLAG_GUIDES.keys())
    selected_guide_flag = st.selectbox("Detaylarını İncelemek İstediğiniz Bayrak Devleti:", flags_with_guides)
    
    guide = FLAG_GUIDES[selected_guide_flag]
    
    # Flag Details Header Card
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid #00f2fe;">
        <h2 style="margin:0 0 5px 0; color:#00f2fe;">{selected_guide_flag} Bayrak Rehberi</h2>
        <p style="margin-bottom:12px; font-size:1.05rem;">{guide['description']}</p>
        <p style="margin:0; font-size:0.9rem; color:#8b949e;"> Resmi Circular Portalı: <a href="{guide['portal_url']}" target="_blank" style="color:#00f2fe;text-decoration:none;">{guide['portal_url']} ↗</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contacts Section
    st.markdown('<h3 class="gradient-subheader">📞 Kritik Bayrak İletişim Bilgileri (Segumar, Teknik, Alarm vb.)</h3>', unsafe_allow_html=True)
    
    cols = st.columns(len(guide['contacts']))
    for i, contact in enumerate(guide['contacts']):
        with cols[i]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:15px; height:100%;">
                <p style="margin:0 0 4px 0; font-weight:700; color:#ff54b0; font-size:0.95rem;">{contact['name']}</p>
                <p style="margin:0 0 8px 0; font-size:0.85rem; color:#8b949e; font-style:italic;">{contact['purpose']}</p>
                <p style="margin:0; font-size:0.9rem; font-weight:600; color:#00f2fe;">✉️ {contact['email']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Checklist Tabs
    st.markdown('<h3 class="gradient-subheader">📝 Sörvey Kontrol Maddeleri (Surveyor Checklists)</h3>', unsafe_allow_html=True)
    
    checklists = guide['checklists']
    
    tab_names = list(checklists.keys())
    tabs = st.tabs(tab_names)
    
    for i, name in enumerate(tab_names):
        with tabs[i]:
            items = checklists[name]
            st.markdown(f"<p style='color:#ff54b0; font-weight:600; font-size:1.05rem; margin-bottom:12px;'>⚠️ {selected_guide_flag} Bayrağı Altında {name} Kontrollerinde Dikkat Edilecekler:</p>", unsafe_allow_html=True)
            
            for item in items:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.01); border-left:3px solid #ff54b0; border-radius:0 6px 6px 0; padding:12px; margin-bottom:10px; font-size:0.95rem; line-height:1.4;">
                    {item}
                </div>
                """, unsafe_allow_html=True)
                
    # Relevant circulars from database for this flag
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h3 class="gradient-subheader">📂 {selected_guide_flag} Bayrağına Ait Veri Tabanındaki Sirkülerler</h3>', unsafe_allow_html=True)
    
    flag_circs = df_circulars[df_circulars['Flag'] == selected_guide_flag]
    if flag_circs.empty:
        st.info("Bu bayrağa ait veri tabanında taranmış sirküler bulunmamaktadır.")
    else:
        st.dataframe(
            flag_circs[['Filename', 'Category', 'Subject_TR', 'References']],
            use_container_width=True,
            column_config={
                "Filename": st.column_config.TextColumn("Dosya Adı"),
                "Category": st.column_config.TextColumn("Kategori"),
                "Subject_TR": st.column_config.TextColumn("Konu (Türkçe)"),
                "References": st.column_config.TextColumn("Kural Dayanağı")
            }
        )

# PAGE 3: FLAG OFFICIAL WEBSITES
elif page == "🌐 Canlı Bayrak Siteleri":
    st.markdown('<h1 class="gradient-text gradient-header">🌐 Canlı Bayrak Devletleri Sirküler Portalları</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e;font-size:1.1rem;margin-bottom:20px;">En güncel sirküler, form ve mevzuat değişikliklerini teyit etmek için bayrakların resmi web sitelerini ziyaret edebilirsiniz.</p>', unsafe_allow_html=True)
    
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
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; color:#00f2fe;">{flag_name}</h3>
                <a href="{info['url']}" target="_blank" style="background:#00f2fe; color:#0e1117; padding:6px 16px; border-radius:4px; font-weight:700; text-decoration:none; font-size:0.9rem;">Sitede Aç ↗</a>
            </div>
            <p style="margin:10px 0 5px 0; font-weight:600; color:#e2e8f0;">{info['name']}</p>
            <p style="margin:0; color:#8b949e; font-size:0.9rem;">{info['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
