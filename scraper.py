import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import time
import re
import os

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

# ============================================================
#  N11
# ============================================================
def cek_n11(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        r = requests.get(urun["url"], headers=headers, timeout=20)
        print(f"  N11 HTTP {r.status_code}")
        if r.status_code != 200:
            return sonuc
        html = r.text

        # Fiyat — tüm olası formatları dene
        # Format 1: "displayPrice":"13999,00"
        m = re.search(r'"displayPrice"\s*:\s*"([\d.,]+)"', html)
        if m:
            sonuc["fiyat"] = float(m.group(1).replace(".", "").replace(",", "."))
            print(f"  N11 fiyat (displayPrice): {sonuc['fiyat']}")

        # Format 2: "salePrice":1399900 (kuruş)
        if not sonuc["fiyat"]:
            m = re.search(r'"salePrice"\s*:\s*(\d+)', html)
            if m:
                sonuc["fiyat"] = round(int(m.group(1)) / 100, 2)
                print(f"  N11 fiyat (salePrice): {sonuc['fiyat']}")

        # Format 3: itemprop content
        if not sonuc["fiyat"]:
            m = re.search(r'itemprop="price"[^>]*content="([\d.,]+)"', html)
            if m:
                val = float(m.group(1).replace(",", "."))
                sonuc["fiyat"] = round(val / 100, 2) if val > 10000 else val
                print(f"  N11 fiyat (itemprop): {sonuc['fiyat']}")

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
#  TRENDYOL
# ============================================================
def cek_trendyol(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        r = requests.get(urun["url"], headers=headers, timeout=20)
        print(f"  Trendyol HTTP {r.status_code}")
        if r.status_code != 200:
            return sonuc
        html = r.text

        # Trendyol window.__PRODUCT_DETAIL_APP_INITIAL_STATE__ içinde veri saklar
        m = re.search(r'__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*(\{.*?\});', html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                product = data.get("product", {})
                price = product.get("priceInfo", {})
                sonuc["fiyat"] = price.get("discountedPrice") or price.get("price")
                sonuc["puan"] = product.get("ratingScore") or product.get("averageRating")
                sonuc["yorum"] = product.get("commentCount")
                print(f"  Trendyol state: fiyat={sonuc['fiyat']} puan={sonuc['puan']} yorum={sonuc['yorum']}")
                if sonuc["fiyat"]:
                    return sonuc
            except Exception as e:
                print(f"  Trendyol JSON parse hata: {e}")

        # Fallback regex
        # Fiyat formatları: 3285.00 veya "3285,00"
        m = re.search(r'"discountedPrice"\s*:\s*([\d.]+)', html)
        if not m:
            m = re.search(r'"price"\s*:\s*([\d.]+)', html)
        if m:
            val = float(m.group(1))
            sonuc["fiyat"] = round(val / 100, 2) if val > 100000 else val
            print(f"  Trendyol fiyat (regex): {sonuc['fiyat']}")

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
#  HEPSİBURADA — 403 veriyor, Oxylabs free proxy dene
# ============================================================
def cek_hepsiburada(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    try:
        # Farklı User-Agent kombinasyonları dene
        ua_listesi = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        ]

        for ua in ua_listesi:
            headers = {
                "User-Agent": ua,
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
            }
            session = requests.Session()
            # Önce ana sayfaya git (cookie al)
            session.get("https://www.hepsiburada.com", headers=headers, timeout=15)
            time.sleep(1)
            r = session.get(urun["url"], headers=headers, timeout=20)
            print(f"  HB HTTP {r.status_code} (UA: {ua[:40]}...)")

            if r.status_code == 200:
                html = r.text
                # JSON-LD
                for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
                    try:
                        ld = json.loads(ld_str)
                        offers = ld.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0]
                        if offers.get("price"):
                            sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                        agg = ld.get("aggregateRating", {})
                        if agg.get("ratingValue"):
                            sonuc["puan"] = float(agg["ratingValue"])
                            sonuc["yorum"] = int(agg.get("reviewCount", 0))
                    except:
                        pass

                if not sonuc["fiyat"]:
                    m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', html)
                    if m:
                        sonuc["fiyat"] = float(m.group(1).replace(",", "."))

                if sonuc["fiyat"]:
                    break
            time.sleep(2)

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
    sh = gc.open_by_key(os.environ.get("SPREADSHEET_ID"))

    simdi = datetime.now()
    tarih = simdi.strftime("%d.%m.%Y")
    saat  = simdi.strftime("%H:%M")

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
            f"{tarih} {saat}", v["url"]
        ])
        time.sleep(0.5)

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
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
