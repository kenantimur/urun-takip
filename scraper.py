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
        "url": "https://www.trendyol.com/gamma-screens/240x200-storlu-projeksiyon-perdesi-p-32240762",
        "urun_id": "32240762"
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-300x225-motorlu-projeksiyon-perdesi-p-HBV000009FK0H",
        "urun_id": "HBV000009FK0H"
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-240x200-storlu-projeksiyon-perdesi-p-HBV000009FK0N",
        "urun_id": "HBV000009FK0N"
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ============================================================
#  N11
# ============================================================
def cek_n11(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        r = requests.get(urun["url"], headers=HEADERS, timeout=20)
        print(f"  N11 HTTP {r.status_code}")
        if r.status_code != 200:
            return sonuc
        html = r.text

        # Fiyat — N11 kuruş cinsinden veriyor, 100'e böl
        m = re.search(r'"price"\s*:\s*"?([\d]+)"?', html)
        if m:
            sonuc["fiyat"] = round(int(m.group(1)) / 100, 2)
        if not sonuc["fiyat"]:
            m = re.search(r'itemprop="price"[^>]*content="([\d.,]+)"', html)
            if m:
                sonuc["fiyat"] = float(m.group(1).replace(".", "").replace(",", "."))

        # Puan
        m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        if m:
            sonuc["puan"] = float(m.group(1))

        # Yorum
        m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
        if not m:
            m = re.search(r'(\d+)\s*[Dd]eğerlendirme', html)
        if m:
            sonuc["yorum"] = int(m.group(1))

    except Exception as e:
        print(f"  N11 HATA: {e}")
    return sonuc

# ============================================================
#  TRENDYOL — mobil API
# ============================================================
def cek_trendyol(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        urun_id = urun.get("urun_id", "")
        # Trendyol mobil API endpoint
        api_url = f"https://mobileapi.trendyol.com/discovery-web-productgw-service/api/product-detail/{urun_id}/mobile"
        headers = {
            "User-Agent": "Trendyol/6.12.0 (iPhone; iOS 15.0; Scale/3.00)",
            "Accept": "application/json",
            "Accept-Language": "tr-TR",
        }
        r = requests.get(api_url, headers=headers, timeout=20)
        print(f"  Trendyol API HTTP {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            result = data.get("result", data)
            price = result.get("price", {})
            if isinstance(price, dict):
                sonuc["fiyat"] = price.get("discountedPrice") or price.get("originalPrice")
            elif isinstance(price, (int, float)):
                sonuc["fiyat"] = price

            sonuc["puan"] = result.get("ratingScore") or result.get("averageRating")
            sonuc["yorum"] = result.get("commentCount") or result.get("reviewCount")
            print(f"  Trendyol API sonuç: {result.keys() if hasattr(result, 'keys') else result}")
            return sonuc

        # Alternatif: web sayfasından çek
        r2 = requests.get(urun["url"], headers=HEADERS, timeout=20)
        print(f"  Trendyol web HTTP {r2.status_code}")
        if r2.status_code == 200:
            html = r2.text
            # Fiyat — JSON içinde
            m = re.search(r'"discountedPrice"\s*:\s*([\d.]+)', html)
            if not m:
                m = re.search(r'"price"\s*:\s*([\d.]+)', html)
            if m:
                val = float(m.group(1))
                # Trendyol bazen kuruş olarak veriyor
                sonuc["fiyat"] = round(val / 100, 2) if val > 100000 else val

            m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
            if m:
                sonuc["puan"] = float(m.group(1))

            m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
            if m:
                sonuc["yorum"] = int(m.group(1))

    except Exception as e:
        print(f"  Trendyol HATA: {e}")
    return sonuc

# ============================================================
#  HEPSİBURADA — JSON-LD + meta tag
# ============================================================
def cek_hepsiburada(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.hepsiburada.com/",
        }
        r = requests.get(urun["url"], headers=headers, timeout=20)
        print(f"  HB HTTP {r.status_code}")
        if r.status_code != 200:
            return sonuc

        html = r.text

        # JSON-LD bloğunu bul
        ld_match = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        if ld_match:
            try:
                ld = json.loads(ld_match.group(1))
                offers = ld.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0]
                if offers.get("price"):
                    sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                if ld.get("aggregateRating"):
                    sonuc["puan"] = float(ld["aggregateRating"].get("ratingValue", 0))
                    sonuc["yorum"] = int(ld["aggregateRating"].get("reviewCount", 0))
                print(f"  HB JSON-LD: fiyat={sonuc['fiyat']} puan={sonuc['puan']} yorum={sonuc['yorum']}")
                if sonuc["fiyat"]:
                    return sonuc
            except:
                pass

        # Regex fallback
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

    except Exception as e:
        print(f"  HB HATA: {e}")
    return sonuc

# ============================================================
#  GOOGLE SHEETS
# ============================================================
def sheets_guncelle(veriler):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        print("HATA: GOOGLE_CREDENTIALS bulunamadı!")
        return

    creds_dict = json.loads(creds_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    sh = gc.open_by_key(spreadsheet_id)

    simdi = datetime.now()
    tarih = simdi.strftime("%d.%m.%Y")
    saat  = simdi.strftime("%H:%M")

    # Ana sheet
    try:
        ws = sh.worksheet("Ürün Takip")
        ws.clear()
    except:
        ws = sh.add_worksheet("Ürün Takip", rows=100, cols=10)

    basliklar = ["Site", "Ürün Adı", "Fiyat (TL)", "Puan", "Yorum Sayısı", "Son Güncelleme", "URL"]
    ws.append_row(basliklar)
    ws.format("A1:G1", {
        "backgroundColor": {"red": 0.11, "green": 0.62, "blue": 0.46},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    })

    for v in veriler:
        ws.append_row([
            v["site"], v["ad"],
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            f"{tarih} {saat}",
            v["url"]
        ])
        time.sleep(0.5)

    # Geçmiş sheet
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
            tarih, saat, v["site"], v["ad"],
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
    print("🚀 Ürün takip başlatıldı...")
    veriler = []

    for urun in URUNLER:
        print(f"\n📦 {urun['ad']} ({urun['site']})")
        site = urun["site"].lower()

        if site == "n11":
            veri = cek_n11(urun)
        elif site == "trendyol":
            veri = cek_trendyol(urun)
        elif site == "hepsiburada":
            veri = cek_hepsiburada(urun)
        else:
            veri = {"fiyat": None, "puan": None, "yorum": None}

        print(f"  → fiyat={veri['fiyat']} puan={veri['puan']} yorum={veri['yorum']}")
        veriler.append({**urun, **veri})
        time.sleep(2)

    print("\n📊 Google Sheets güncelleniyor...")
    sheets_guncelle(veriler)
    print("✅ Tamamlandı!")	
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
