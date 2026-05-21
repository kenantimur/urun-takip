import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import time
import re
import os
from playwright.sync_api import sync_playwright

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
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-300x225-motorlu-projeksiyon-perdesi-p-HBV000009FK0H",
    },
    {
        "site": "Hepsiburada",
        "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",
        "url": "https://www.hepsiburada.com/gamma-screens-240x200-storlu-projeksiyon-perdesi-p-HBV000009FK0N",
    },
]

# ============================================================
#  PLAYWRIGHT ile veri çek (tüm siteler için)
# ============================================================
def cek_playwright(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    site = urun["site"].lower()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="tr-TR",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.goto(urun["url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            html = page.content()
            print(f"  [{urun['site']}] Sayfa yüklendi, HTML uzunluğu: {len(html)}")

            if site == "n11":
                # Fiyat — N11 sayfasındaki tüm fiyat formatlarını dene
                m = re.search(r'"displayPrice"\s*:\s*"([\d.,]+)"', html)
                if m:
                    sonuc["fiyat"] = float(m.group(1).replace(".", "").replace(",", "."))
                    print(f"  N11 displayPrice: {sonuc['fiyat']}")

                if not sonuc["fiyat"]:
                    m = re.search(r'"salePrice"\s*:\s*(\d+)', html)
                    if m:
                        sonuc["fiyat"] = round(int(m.group(1)) / 100, 2)
                        print(f"  N11 salePrice/100: {sonuc['fiyat']}")

                if not sonuc["fiyat"]:
                    # Sayfadaki fiyat elementini doğrudan oku
                    try:
                        fiyat_el = page.locator('[class*="price"]').first.inner_text()
                        print(f"  N11 DOM fiyat elementi: {fiyat_el}")
                        m2 = re.search(r'([\d.,]+)', fiyat_el.replace(".", "").replace(",", "."))
                        if m2:
                            sonuc["fiyat"] = float(m2.group(1))
                    except:
                        pass

                m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
                if m:
                    sonuc["puan"] = float(m.group(1))
                m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

            elif site == "trendyol":
                # Fiyat DOM'dan oku
                try:
                    fiyat_el = page.locator('.prc-dsc').first.inner_text()
                    print(f"  TY DOM fiyat: {fiyat_el}")
                    m = re.search(r'([\d.,]+)', fiyat_el.replace(".", "").replace(",", "."))
                    if m:
                        sonuc["fiyat"] = float(m.group(1))
                except Exception as e:
                    print(f"  TY DOM fiyat hata: {e}")

                if not sonuc["fiyat"]:
                    m = re.search(r'"discountedPrice"\s*:\s*([\d.]+)', html)
                    if not m:
                        m = re.search(r'"price"\s*:\s*([\d.]+)', html)
                    if m:
                        val = float(m.group(1))
                        sonuc["fiyat"] = round(val / 100, 2) if val > 100000 else val
                        print(f"  TY regex fiyat: {sonuc['fiyat']}")

                try:
                    puan_el = page.locator('.rating-score').first.inner_text()
                    sonuc["puan"] = float(puan_el.strip())
                except:
                    m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
                    if m:
                        sonuc["puan"] = float(m.group(1))

                m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

            elif site == "hepsiburada":
                try:
                    fiyat_el = page.locator('[data-test-id="price-current-price"]').first.inner_text()
                    print(f"  HB DOM fiyat: {fiyat_el}")
                    m = re.search(r'([\d.,]+)', fiyat_el.replace(".", "").replace(",", "."))
                    if m:
                        sonuc["fiyat"] = float(m.group(1))
                except Exception as e:
                    print(f"  HB DOM fiyat hata: {e}")

                if not sonuc["fiyat"]:
                    for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
                        try:
                            ld = json.loads(ld_str)
                            offers = ld.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0]
                            if offers.get("price"):
                                sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                                print(f"  HB JSON-LD fiyat: {sonuc['fiyat']}")
                            agg = ld.get("aggregateRating", {})
                            if agg.get("ratingValue"):
                                sonuc["puan"] = float(agg["ratingValue"])
                                sonuc["yorum"] = int(agg.get("reviewCount", 0))
                        except:
                            pass

                if not sonuc["puan"]:
                    try:
                        puan_el = page.locator('[class*="star-rating"]').first.get_attribute("data-value")
                        if puan_el:
                            sonuc["puan"] = float(puan_el)
                    except:
                        pass

            browser.close()

    except Exception as e:
        print(f"  [{urun['site']}] Playwright HATA: {e}")

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
        veri = cek_playwright(urun)
        print(f"  → fiyat={veri['fiyat']} puan={veri['puan']} yorum={veri['yorum']}")
        veriler.append({**urun, **veri})
        time.sleep(2)

    print("\n📊 Google Sheets güncelleniyor...")
    sheets_guncelle(veriler)
    print("✅ Tamamlandı!")



									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
