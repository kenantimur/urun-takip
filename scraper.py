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

def fiyat_parse(text):
    """'10.999 TL' → 10999.0, '3.285,00' → 3285.0"""
    text = text.strip()
    text = re.sub(r'[^\d,.]', '', text)
    # Türk formatı: nokta binlik ayırıcı, virgül ondalık
    # Örn: 10.999 → 10999, 3.285,00 → 3285.0
    if re.match(r'^\d{1,3}(\.\d{3})+(,\d+)?$', text):
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text and '.' in text:
        text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except:
        return None

def stealth_context(playwright):
    """Bot tespitini zorlaştıran tarayıcı context'i"""
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="tr-TR",
        timezone_id="Europe/Istanbul",
        viewport={"width": 1280, "height": 800},
        extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"},
    )
    # navigator.webdriver = false yap
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr', 'en'] });
        window.chrome = { runtime: {} };
    """)
    return browser, context

def cek_playwright(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    site = urun["site"].lower()

    try:
        with sync_playwright() as p:
            browser, context = stealth_context(p)
            page = context.new_page()

            if site == "hepsiburada":
                # HB için önce ana sayfaya git, cookie al
                page.goto("https://www.hepsiburada.com", wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)

            page.goto(urun["url"], wait_until="networkidle", timeout=45000)
            time.sleep(4)
            html = page.content()
            print(f"  HTML uzunluğu: {len(html)}, Başlık: {page.title()[:50]}")

            if site == "n11":
                for sel in ['.price', '[class*="price"]', '.newPrice span', 'span[class*="price"]']:
                    try:
                        txt = page.locator(sel).first.inner_text(timeout=3000)
                        val = fiyat_parse(txt)
                        if val and val > 10:
                            sonuc["fiyat"] = val
                            print(f"  N11 fiyat ({sel}): {txt} → {val}")
                            break
                    except:
                        pass
                m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
                if m:
                    sonuc["puan"] = float(m.group(1))
                m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

            elif site == "trendyol":
                # Trendyol fiyat regex — JSON içinde
                # Format: "price":32.85 veya "price":3285
                patterns = [
                    r'"discountedPrice"\s*:\s*([\d]+\.[\d]+)',
                    r'"discountedPrice"\s*:\s*([\d]+)',
                    r'"price"\s*:\s*([\d]+\.[\d]+)',
                    r'"sellingPrice"\s*:\s*([\d]+\.[\d]+)',
                    r'"listPrice"\s*:\s*([\d]+\.[\d]+)',
                ]
                for pat in patterns:
                    m = re.search(pat, html)
                    if m:
                        val = float(m.group(1))
                        # 3285 → kuruşsa 100'e böl değil, TL cinsinden
                        # Trendyol genelde tam TL verir
                        sonuc["fiyat"] = val
                        print(f"  TY fiyat regex ({pat}): {val}")
                        break

                # DOM selector dene
                if not sonuc["fiyat"]:
                    for sel in ['[class*="price"]', 'span[class*="Price"]', '.product-price-container span']:
                        try:
                            items = page.locator(sel).all_inner_texts()
                            for txt in items:
                                val = fiyat_parse(txt)
                                if val and 100 < val < 1000000:
                                    sonuc["fiyat"] = val
                                    print(f"  TY DOM fiyat ({sel}): {txt} → {val}")
                                    break
                            if sonuc["fiyat"]:
                                break
                        except:
                            pass

                m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
                if m:
                    sonuc["puan"] = float(m.group(1))
                m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
                if m:
                    sonuc["yorum"] = int(m.group(1))

            elif site == "hepsiburada":
                if len(html) < 5000:
                    print(f"  HB engel sayfası — stealth başarısız")
                else:
                    for sel in ['[data-test-id="price-current-price"]', '[class*="price"]', 'span[class*="Price"]']:
                        try:
                            txt = page.locator(sel).first.inner_text(timeout=3000)
                            val = fiyat_parse(txt)
                            if val and val > 10:
                                sonuc["fiyat"] = val
                                print(f"  HB fiyat ({sel}): {txt} → {val}")
                                break
                        except:
                            pass
                    for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
                        try:
                            ld = json.loads(ld_str)
                            offers = ld.get("offers", {})
                            if isinstance(offers, list): offers = offers[0]
                            if offers.get("price"):
                                sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                            agg = ld.get("aggregateRating", {})
                            if agg.get("ratingValue"):
                                sonuc["puan"] = float(agg["ratingValue"])
                                sonuc["yorum"] = int(agg.get("reviewCount", 0))
                        except:
                            pass

            browser.close()

    except Exception as e:
        print(f"  [{urun['site']}] HATA: {e}")

    return sonuc

def sheets_guncelle(veriler):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        print("HATA: GOOGLE_CREDENTIALS bulunamadı!")
        return
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
        ws.append_row([v["site"], v["ad"],
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            f"{tarih} {saat}", v["url"]])
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
        gs.append_row([tarih, saat, v["site"], v["ad"],
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            v["url"]])
        time.sleep(0.5)
    print(f"✅ Google Sheets güncellendi: {tarih} {saat}")

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



									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
