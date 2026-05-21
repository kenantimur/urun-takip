import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import time
import re
import os

# ============================================================
#  TAKİP EDİLECEK ÜRÜNLER
# ============================================================
URUNLER = [
    {
        "site": "N11",
        "ad": "FunFlix P1 Android 4K Projeksiyon Cihazı",
        "url": "https://www.n11.com/urun/funflix-p1-android-4k-destekli-bluetooth-5g-wi-fi-led-full-hd-projeksiyon-cihazi-66449240"
    },
    {
        "site": "Trendyol",
        "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",
        "url": "https://www.trendyol.com/gamma-screens/240x200-storlu-projeksiyon-perdesi-p-32240762"
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-300x225-motorlu-projeksiyon-perdesi-p-HBV000009FK0H"
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-240x200-storlu-projeksiyon-perdesi-p-HBV000009FK0N"
    },
    # Yeni ürün eklemek için buraya satır ekleyin:
    # {"site": "Trendyol", "ad": "Ürün Adı", "url": "https://..."},
]

# ============================================================
#  HEADERS — gerçek tarayıcı gibi görün
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ============================================================
#  VERİ ÇEKME FONKSİYONLARI
# ============================================================
def urun_verisi_cek(urun):
    site = urun["site"].lower()
    url  = urun["url"]
    sonuc = {"fiyat": None, "puan": None, "yorum": None}

    try:
        session = requests.Session()
        session.headers.update(HEADERS)

        if site == "trendyol":
            # Trendyol: önce sayfayı çek, JSON verisini parse et
            r = session.get(url, timeout=20)
            print(f"  [{urun['site']}] HTTP {r.status_code}")
            if r.status_code == 200:
                html = r.text
                # JSON içindeki ürün verisi
                m = re.search(r'"price"\s*:\s*([\d.]+)', html)
                if not m:
                    m = re.search(r'"discountedPrice"\s*:\s*([\d.]+)', html)
                if m:
                    sonuc["fiyat"] = float(m.group(1))

                m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
                if m:
                    sonuc["puan"] = float(m.group(1))

                m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

        elif site == "hepsiburada":
            r = session.get(url, timeout=20)
            print(f"  [{urun['site']}] HTTP {r.status_code}")
            if r.status_code == 200:
                html = r.text
                # JSON-LD içinden çek
                m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', html)
                if m:
                    sonuc["fiyat"] = float(m.group(1).replace(",", "."))

                m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
                if m:
                    sonuc["puan"] = float(m.group(1))

                m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
                if not m:
                    m = re.search(r'(\d+)\s*[Dd]eğerlendirme', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

        elif site == "n11":
            r = session.get(url, timeout=20)
            print(f"  [{urun['site']}] HTTP {r.status_code}")
            if r.status_code == 200:
                html = r.text
                m = re.search(r'itemprop="price"[^>]*content="([\d.,]+)"', html)
                if not m:
                    m = re.search(r'"price"\s*:\s*"([\d.,]+)"', html)
                if m:
                    sonuc["fiyat"] = float(m.group(1).replace(".", "").replace(",", "."))

                m = re.search(r'itemprop="ratingValue"[^>]*content="([\d.]+)"', html)
                if not m:
                    m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
                if m:
                    sonuc["puan"] = float(m.group(1))

                m = re.search(r'itemprop="reviewCount"[^>]*content="(\d+)"', html)
                if not m:
                    m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

    except Exception as e:
        print(f"  HATA [{urun['site']}]: {e}")

    print(f"  Sonuç: fiyat={sonuc['fiyat']} puan={sonuc['puan']} yorum={sonuc['yorum']}")
    return sonuc


# ============================================================
#  GOOGLE SHEETS BAĞLANTISI
# ============================================================
def sheets_guncelle(veriler):
    # GitHub Secret'tan JSON key al
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        print("HATA: GOOGLE_CREDENTIALS secret bulunamadı!")
        return

    creds_dict = json.loads(creds_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc    = gspread.authorize(creds)

    # Spreadsheet ID'yi GitHub Secret'tan al
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sh = gc.open_by_key(spreadsheet_id)

    simdi    = datetime.now()
    tarih    = simdi.strftime("%d.%m.%Y")
    saat     = simdi.strftime("%H:%M")

    # ── Ana sheet ──
    try:
        ws = sh.worksheet("Ürün Takip")
        ws.clear()
    except:
        ws = sh.add_worksheet("Ürün Takip", rows=100, cols=10)

    basliklar = ["Site", "Ürün Adı", "Fiyat (TL)", "Puan", "Yorum Sayısı", "Son Güncelleme", "URL"]
    ws.append_row(basliklar)

    for v in veriler:
        ws.append_row([
            v["site"],
            v["ad"],
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            f"{tarih} {saat}",
            v["url"]
        ])
        time.sleep(0.5)  # API rate limit

    # Başlık formatı
    ws.format("A1:G1", {
        "backgroundColor": {"red": 0.11, "green": 0.62, "blue": 0.46},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    })

    # ── Geçmiş sheet ──
    try:
        gs = sh.worksheet("Geçmiş")
    except:
        gs = sh.add_worksheet("Geçmiş", rows=10000, cols=10)
        gs.append_row(["Tarih", "Saat", "Site", "Ürün Adı", "Fiyat (TL)", "Puan", "Yorum Sayısı", "URL"])
        gs.format("A1:H1", {
            "backgroundColor": {"red": 0.11, "green": 0.62, "blue": 0.46},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
        })

    for v in veriler:
        gs.append_row([
            tarih, saat,
            v["site"], v["ad"],
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            v["url"]
        ])
        time.sleep(0.5)

    print(f"✅ Google Sheets güncellendi: {tarih} {saat}")


# ============================================================
#  ANA AKIŞ
# ============================================================
if __name__ == "__main__":
    print("🚀 Ürün takip scripti başlatıldı...")
    veriler = []

    for urun in URUNLER:
        print(f"\n📦 {urun['ad']} ({urun['site']})")
        veri = urun_verisi_cek(urun)
        veriler.append({
            "site":  urun["site"],
            "ad":    urun["ad"],
            "url":   urun["url"],
            "fiyat": veri["fiyat"],
            "puan":  veri["puan"],
            "yorum": veri["yorum"],
        })
        time.sleep(2)

    print("\n📊 Google Sheets güncelleniyor...")
    sheets_guncelle(veriler)
    print("\n✅ Tamamlandı!")
