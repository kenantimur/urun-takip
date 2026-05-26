import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import time
import re
import os

ZENROWS_API_KEY = "ccc54f8d95eb2d79d02c97cc0dc9168ae423cee3"

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
    text = text.strip()
    text = re.sub(r'[^\d,.]', '', text)
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

def zenrows_fetch(url, js_render=True):
    """ZenRows ile sayfa çek"""
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": url,
        "js_render": "true" if js_render else "false",
        "premium_proxy": "true",
        "proxy_country": "tr",
    }
    r = requests.get("https://api.zenrows.com/v1/", params=params, timeout=60)
    print(f"  ZenRows HTTP {r.status_code} — {url[:60]}")
    if r.status_code == 200:
        return r.text
    else:
        print(f"  ZenRows hata: {r.text[:200]}")
        return None

def cek_urun(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    site = urun["site"].lower()

    html = zenrows_fetch(urun["url"], js_render=True)
    if not html:
        return sonuc

    print(f"  HTML uzunluğu: {len(html)}")

    if site == "n11":
        # Fiyat
        m = re.search(r'"displayPrice"\s*:\s*"([\d.,]+)"', html)
        if m:
            sonuc["fiyat"] = fiyat_parse(m.group(1))
            print(f"  N11 displayPrice: {m.group(1)} → {sonuc['fiyat']}")
        if not sonuc["fiyat"]:
            for pat in [r'class="price[^"]*"[^>]*>\s*<[^>]+>\s*([\d.,]+\s*TL)', r'([\d.]+,\d+)\s*TL']:
                m = re.search(pat, html)
                if m:
                    sonuc["fiyat"] = fiyat_parse(m.group(1))
                    print(f"  N11 fiyat regex: {m.group(1)} → {sonuc['fiyat']}")
                    break
        if not sonuc["fiyat"]:
            m = re.search(r'"salePrice"\s*:\s*(\d+)', html)
            if m:
                sonuc["fiyat"] = round(int(m.group(1)) / 100, 2)
                print(f"  N11 salePrice: {sonuc['fiyat']}")

        m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        if m: sonuc["puan"] = float(m.group(1))

        m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
        if not m: m = re.search(r'(\d+)\s*[Dd]eğerlendirme', html)
        if m: sonuc["yorum"] = int(m.group(1).replace('.', ''))

    elif site == "trendyol":
        # Fiyat
        for pat in [
            r'"discountedPrice"\s*:\s*([\d.]+)',
            r'"price"\s*:\s*([\d.]+)',
            r'"sellingPrice"\s*:\s*([\d.]+)',
        ]:
            m = re.search(pat, html)
            if m:
                val = float(m.group(1))
                sonuc["fiyat"] = round(val / 100, 2) if val > 100000 else val
                print(f"  TY fiyat: {m.group(1)} → {sonuc['fiyat']}")
                break
        if not sonuc["fiyat"]:
            matches = re.findall(r'([\d]{1,3}(?:\.\d{3})*(?:,\d+)?)\s*TL', html)
            for m in matches:
                val = fiyat_parse(m)
                if val and 100 < val < 100000:
                    sonuc["fiyat"] = val
                    print(f"  TY fiyat TL: {m} → {val}")
                    break

        m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
        if m: sonuc["puan"] = float(m.group(1))

        m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
        if m: sonuc["yorum"] = int(m.group(1))

    elif site == "hepsiburada":
        # JSON-LD
        for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                ld = json.loads(ld_str)
                offers = ld.get("offers", {})
                if isinstance(offers, list): offers = offers[0]
                if offers.get("price"):
                    sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                    print(f"  HB JSON-LD fiyat: {sonuc['fiyat']}")
                agg = ld.get("aggregateRating", {})
                if agg.get("ratingValue"):
                    sonuc["puan"] = float(agg["ratingValue"])
                    sonuc["yorum"] = int(agg.get("reviewCount", 0))
            except:
                pass

        if not sonuc["fiyat"]:
            m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', html)
            if m:
                sonuc["fiyat"] = fiyat_parse(m.group(1))
                print(f"  HB regex fiyat: {sonuc['fiyat']}")

        if not sonuc["puan"]:
            m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
            if m: sonuc["puan"] = float(m.group(1))
        if not sonuc["yorum"]:
            m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
            if not m: m = re.search(r'(\d+)\s*[Dd]eğerlendirme', html)
            if m: sonuc["yorum"] = int(m.group(1))

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
        veri = cek_urun(urun)
        print(f"  → fiyat={veri['fiyat']} puan={veri['puan']} yorum={veri['yorum']}")
        veriler.append({**urun, **veri})
        time.sleep(3)
    print("\n📊 Google Sheets güncelleniyor...")
    sheets_guncelle(veriler)
    print("✅ Tamamlandı!")



									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
