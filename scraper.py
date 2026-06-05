import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import time
import re
import os

ZENROWS_API_KEYS = [
    "174e22ec05b47f8ef8ed35a97c1f7e8a926c3bb4",
    "4ec134284d5729d29d6b9e4fed73b6cf19e2580e",
    "c0015e1857fb966e8b1e841a7d4793c817b7c0de",
    "ccc54f8d95eb2d79d02c97cc0dc9168ae423cee3",  # eski, en sonda
]
ZENROWS_API_KEY = ZENROWS_API_KEYS[0]  # aktif key
_key_index = 0

# ============================================================
#  TAKİP EDİLECEK ÜRÜNLER
#  Yeni ürün eklemek: listeye {"site": "...", "ad": "...", "url": "..."} satırı ekle
#  Silmek: ilgili satırı sil
# ============================================================
URUNLER = [
    # ── Mevcut ürünler ──────────────────────────────────────
    {"site": "N11",         "ad": "FunFlix P1 Android 4K Projeksiyon Cihazı",              "url": "https://www.n11.com/urun/funflix-p1-android-4k-destekli-bluetooth-5g-wi-fi-led-full-hd-projeksiyon-cihazi-66449240"},
    {"site": "Trendyol",    "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",       "url": "https://www.trendyol.com/gamma-screens/240x200-storlu-projeksiyon-perdesi-p-32240762"},

    # ── Rakip HB ürünleri — Motorlu ─────────────────────────
    {"site": "Hepsiburada", "ad": "Golge Stor 150x160 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-en150cm-boy160cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002Z5W7V"},
    {"site": "Hepsiburada", "ad": "Liteout LO150MP 150x150 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/liteout-lo150mp-150x150-cm-motorlu-projeksiyon-perdesi-pm-HB00000I6DTF"},
    {"site": "Hepsiburada", "ad": "Liteout LO160M 160x160 Motorlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/liteout-lo160m-160x160-cm-motorlu-kumandali-projeksiyon-perdesi-pm-HB00000I6DTI"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 180x180 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/gamma-screens-180x180-motorlu-projeksiyon-perdesi-pm-HB000009FK0A"},
    {"site": "Hepsiburada", "ad": "Peak M70 180x180 Motorlu Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/peak-m70-180x180cm-70inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm70"},
    {"site": "Hepsiburada", "ad": "Golge Stor 180x170 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-180x170-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000031WBPJ"},
    {"site": "Hepsiburada", "ad": "Codegen EX-18 180x180 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/codegen-ex-18-180x180-motorlu-uzaktan-kumandali-pro-perde-pm-HB00000F8530"},
    {"site": "Hepsiburada", "ad": "Liteout LO180M 180x180 Motorlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/liteout-lo180m-180x180-cm-motorlu-beyaz-standart-projeksiyon-perdesi-kumanda-dahil-pm-ofislomt180180"},
    {"site": "Hepsiburada", "ad": "Xblack 180x180 Motorlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/xblack-180-x-180-cm-cam-tozlu-kumas-motorlu-uzaktan-kumandali-projeksiyon-perdesi-xge-180-arkasi-siyah-fonlu-pm-ofisxblamtr"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 180x180 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-180x180cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A75TU5"},
    {"site": "Hepsiburada", "ad": "Rovline Akıllı 180x180 Motorlu Projeksiyon Perdesi",     "url": "https://www.hepsiburada.com/rovline-akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-180x180-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-HBCV0000EXB4J0"},
    {"site": "Hepsiburada", "ad": "Golge Stor 180x170 Şarjlı Motorlu Projeksiyon Perdesi",  "url": "https://www.hepsiburada.com/golge-stor-en-180cm-boy-170cm-sarjli-projeksiyon-perdesi-lityum-pilli-uzun-omurlu-ve-uzaktan-kumandali-p-HBCV00007I3MP9"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 200x200 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/gamma-screens-200x200-motorlu-projeksiyon-perdesi-pm-HB000009FK0C"},
    {"site": "Hepsiburada", "ad": "Peak M100 203x152 Motorlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-m100-203x152cm-100inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm100"},
    {"site": "Hepsiburada", "ad": "Codegen EX-20 200x200 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/codegen-ex-20-200x200-cm-motorlu-elektrikli-uzaktan-kumandali-projeksiyon-perdesi-arkasi-siyah-fonlu-p-OFISCODEXMTR-EX20"},
    {"site": "Hepsiburada", "ad": "Everest EPP-200 200x200 Motorlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/everest-epp-200-200-200cm-uzaktan-kumandali-otomatik-projeksiyon-perdesi-pm-HBC0000BFGPCJ"},
    {"site": "Hepsiburada", "ad": "Xbright 200x200 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/xbright-200-x-200-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-200-arkasi-siyah-fonlu-pm-HB00000OYTH3"},
    {"site": "Hepsiburada", "ad": "Rovline Akıllı 200x180 Motorlu Projeksiyon Perdesi",     "url": "https://www.hepsiburada.com/rovline-akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-200x180-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-HBCV0000EXB47Y"},
    {"site": "Hepsiburada", "ad": "Liteout 200x200 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/liteout-200x200-cm-motorlu-kumandali-projeksiyon-perdesi-p-OFISLOMT200200"},
    {"site": "Hepsiburada", "ad": "Liteout 200x125 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/liteout-200x125-cm-motorlu-kumandali-projeksiyon-perdesi-pm-ofislomt200125"},
    {"site": "Hepsiburada", "ad": "Liteout 200x150 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/liteout-200x150-cm-motorlu-kumandali-projeksiyon-perdesi-pm-HBC000013IBXG"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 200x180 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-200x180cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GXX3"},
    {"site": "Hepsiburada", "ad": "Golge Stor 200x190 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-200x190-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000031WBPL"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 200x200 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-200x200cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7G1ZO"},
    {"site": "Hepsiburada", "ad": "Golge Stor 210x190 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-210x190-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W731"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-220x125cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7EFBS"},
    {"site": "Hepsiburada", "ad": "Full Screen 234x132 Motorlu Projeksiyon Perdesi",        "url": "https://www.hepsiburada.com/full-screen-fullscreen-234x132-motorlu-projeksiyon-perdesi-16-9-format-pm-HBC000077GEZH"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 240x200 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/gamma-screens-240x200-motorlu-projeksiyon-perdesi-p-HBV000009FK09"},
    {"site": "Hepsiburada", "ad": "Xbright 240x200 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/xbright-240-x-200-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-240-arkasi-siyah-fonlu-pm-HB00000OYTHH"},
    {"site": "Hepsiburada", "ad": "Everest EPP-240 240x200 Motorlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/everest-epp-240-240-200cm-uzaktan-kumandali-otomatik-projeksiyon-perdesi-pm-HBC0000BFGQXE"},
    {"site": "Hepsiburada", "ad": "Peak M120 244x183 Motorlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-m120-244x183cm-120inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm120"},
    {"site": "Hepsiburada", "ad": "Fullscreen 240x200 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/fullscreen-240x200-motorlu-projeksiyon-perdesi-pm-HBC000076RFC2"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 240x200 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-240x200cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GM7J"},
    {"site": "Hepsiburada", "ad": "Golge Stor 240x200 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-240x200-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W733"},
    {"site": "Hepsiburada", "ad": "Akıllı 240x200 Motorlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-240x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXAU4U"},
    {"site": "Hepsiburada", "ad": "Golge Stor 250x200 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-en250cm-boy200cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00003XB4BE"},
    {"site": "Hepsiburada", "ad": "Golge Stor 260x220 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-260x220-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032WKPW"},
    {"site": "Hepsiburada", "ad": "Akıllı 260x200 Motorlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-260x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXALED"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 265x200 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/gamma-screens-265x200-motorlu-projeksiyon-perdesi-pm-HB000009FK0E"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-265x150cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GHTF"},
    {"site": "Hepsiburada", "ad": "Fullscreen 265x150 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/fullscreen-265x150-motorlu-projeksiyon-perdesi-16-9-format-pm-HBC0000772H8G"},
    {"site": "Hepsiburada", "ad": "Golge Stor 270x230 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-270x230-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W735"},
    {"site": "Hepsiburada", "ad": "Akıllı 290x200 Motorlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-290x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXAO1Z"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/gamma-screens-300x225-motorlu-projeksiyon-perdesi-pm-HB000009FK0G"},
    {"site": "Hepsiburada", "ad": "Peak M150 305x229 Motorlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-m150-305x229cm-150-inc-motorlu-kumandali-projeksiyon-perdesi-pm-ofispeakm150"},
    {"site": "Hepsiburada", "ad": "Xbright 300x225 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/xbright-300-x-225-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-300-arkasi-siyah-fonlu-pm-HB00000OYTHQ"},
    {"site": "Hepsiburada", "ad": "Liteout 300x225 Motorlu Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/liteout-motorlu-kumandali-projeksiyon-perdesi-300x225-cm-beyaz-renk-ile-kolay-kullanim-p-OFISLOMT300225"},
    {"site": "Hepsiburada", "ad": "Codegen EX-30 300x225 Motorlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/codegen-ex-30-300x225-cm-motorlu-elektrikli-uzaktan-kumandali-projeksiyon-perdesi-arkasi-siyah-fonlu-p-OFISCODEXMTR-EX30"},
    {"site": "Hepsiburada", "ad": "Decon DPC-15 300x225 Projeksiyon Perdesi",               "url": "https://www.hepsiburada.com/decon-dpc-15-300x225-projeksiyon-perdesi-mat-beyaz-pm-HBC0000BKCNPJ"},
    {"site": "Hepsiburada", "ad": "Golge Stor 290x225 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-en290cm-boy225cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00003W8RLD"},
    {"site": "Hepsiburada", "ad": "Golge Stor 340x240 Motorlu Projeksiyon Perdesi",         "url": "https://www.hepsiburada.com/golge-stor-en340cm-boy240cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-pm-HBC00006Y3OBC"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 332x188 Motorlu Projeksiyon Perdesi",   "url": "https://www.hepsiburada.com/groove-vizio-pro-150-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-332x188cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GUDX"},
    {"site": "Hepsiburada", "ad": "Peak M200 400x300 Motorlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-m200-400x300cm-200inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm200"},

    # ── Rakip HB ürünleri — Storlu ──────────────────────────
    {"site": "Hepsiburada", "ad": "Liteout 150x150 Storlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-150x150-cm-storlu-manuel-projeksiyon-perdesi-pm-HB00000HZWM9"},
    {"site": "Hepsiburada", "ad": "Golge Stor 150x160 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-150x160-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLS"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 180x180 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-180x180-cm-storlu-projeksiyon-perdesi-p-HBV000009FK0J"},
    {"site": "Hepsiburada", "ad": "Codegen AX-18 180x180 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/codegen-ax-18-180x180-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-18"},
    {"site": "Hepsiburada", "ad": "Golge Stor 180x170 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-180x170-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLU"},
    {"site": "Hepsiburada", "ad": "Liteout 180x180 Storlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-manuel-projeksiyon-perdesi-180x180-cm-mat-beyaz-renk-4k-uhd-ozellikli-pm-HB00000C3FD9"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 200x200 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-200x200-storlu-projeksiyon-perdesi-ultra-hd-yuksek-kontrast-goruntu-performansi-pm-HB000009FK0K"},
    {"site": "Hepsiburada", "ad": "Codegen AX-20 200x200 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/codegen-ax-20-200x200-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-20"},
    {"site": "Hepsiburada", "ad": "Golge Stor 200x190 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-200x190-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLW"},
    {"site": "Hepsiburada", "ad": "Everest MPP-200 200x200 Storlu Projeksiyon Perdesi",     "url": "https://www.hepsiburada.com/everest-mpp-200-200-200cm-arkasi-siyah-fonlu-storlu-projeksiyon-perdesi-pm-HBC00008O6MXH"},
    {"site": "Hepsiburada", "ad": "Liteout 200x150 Storlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-200x150-cm-storlu-manuel-projeksiyon-perdesi-pm-HB000008CI6Y"},
    {"site": "Hepsiburada", "ad": "Liteout 200x200 Storlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-200x200-cm-storlu-manuel-projeksiyon-perdesi-yerli-uretim-ile-kaliteli-goruntu-p-OFISLOS200200"},
    {"site": "Hepsiburada", "ad": "Havit PS84M 84 inç Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/havit-ps84m-ayarlanabilir-84inc-duvar-perdesi-pm-HBC0000BADJWC"},
    {"site": "Hepsiburada", "ad": "Golge Stor 210x180 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-en210cm-boy180cm-manuel-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00005JRFT2"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Storlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-220x125cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHOFR"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-240x200-cm-yuksek-gain-mat-beyaz-storlu-projeksiyon-perdesi-pratik-kullanim-pm-HB000009FK0M"},
    {"site": "Hepsiburada", "ad": "Codegen AX-24 240x200 Storlu Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/codegen-ax-24-240x200-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-24"},
    {"site": "Hepsiburada", "ad": "Peak 244x183 Storlu Projeksiyon Perdesi",                "url": "https://www.hepsiburada.com/peak-storlu-arkasi-siyah-ithal-projeksiyon-perdesi-beyaz-kasa-244-x-183-cm-pm-HB00000JGUV0"},
    {"site": "Hepsiburada", "ad": "Golge Stor 240x220 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-240x220-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002YNYEO"},
    {"site": "Hepsiburada", "ad": "Liteout LO240S 240x200 Storlu Projeksiyon Perdesi",      "url": "https://www.hepsiburada.com/liteout-lo240s-240x200-cm-storlu-projeksiyon-perdesi-pm-ofislos240200"},
    {"site": "Hepsiburada", "ad": "Liteout 250x190 Storlu Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-250x190-cm-storlu-manuel-projeksiyon-perdesi-p-HBV00000MM2OB"},
    {"site": "Hepsiburada", "ad": "Golge Stor 250x200 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-golge-storen250cm-boy200cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-teknolojisi-pm-HBC00005ULW5Q"},
    {"site": "Hepsiburada", "ad": "Golge Stor 260x230 Storlu Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-260x230-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002YNYEQ"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Storlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-265x150cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHQ7H"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 332x188 Storlu Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/groove-vizio-pro-150-inch-332x188cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHPU2"},

    # ── Rakip HB ürünleri — Tripod ──────────────────────────
    {"site": "Hepsiburada", "ad": "Liteout 100x75 Tripod Projeksiyon Perdesi",              "url": "https://www.hepsiburada.com/liteout-100x75-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000TKG1M"},
    {"site": "Hepsiburada", "ad": "Liteout 120x90 Tripod Projeksiyon Perdesi",              "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-tasinabilir-projeksiyon-perdesi-120x90-cm-kullanim-kolayligi-ile-pm-HB00000TDD80"},
    {"site": "Hepsiburada", "ad": "Liteout 135x100 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-135x100-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HBC000007YL17"},
    {"site": "Hepsiburada", "ad": "Havit PS60 60 inç Tripod Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/havit-ps60-tasinabilir-ayakli-projeksiyon-perdesi-60-inc-pm-HBC00006LAOLZ"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 150x150 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-150x150-tripod-ayakli-projeksiyon-perdesi-pm-HBC0000CQ9NR5"},
    {"site": "Hepsiburada", "ad": "Liteout 150x150 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-tasinabilir-tripod-ayakli-projeksiyon-perdesi-150x150-cm-beyaz-renkli-pm-HB00000I6DTA"},
    {"site": "Hepsiburada", "ad": "Golge Stor 150x95 Tripod Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en150cm-boy95cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000076UA1G"},
    {"site": "Hepsiburada", "ad": "Liteout 160x160 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-160x160-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000UF6OO"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 180x180 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-180-x-180-tripod-projeksiyon-perdesi-pm-HB00000A5M3H"},
    {"site": "Hepsiburada", "ad": "Codegen TX-18 180x180 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/codegen-tx-18-180x180-tripod-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodaxtrp"},
    {"site": "Hepsiburada", "ad": "Havit PS72M 72 inç Tripod Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/havit-ps72m-ayarlanabilir-72inc-duvar-perdesi-pm-HBC0000BADJWA"},
    {"site": "Hepsiburada", "ad": "Golge Stor 180x105 Tripod Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en180cm-boy105cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000076U6V0"},
    {"site": "Hepsiburada", "ad": "Liteout 180x180 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-projeksiyon-perdesi-180x180-cm-mat-beyaz-4k-uhd-1-1-model-pm-ofislotri180180"},
    {"site": "Hepsiburada", "ad": "Peak T70 180x180 Tripod Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/peak-t70-180x180-70inch-tripod-projeksiyon-perdesi-pm-ofispeakt70"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 200x200 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-200-x-200-tripod-projeksiyon-perdesi-pm-HB00000A5M3J"},
    {"site": "Hepsiburada", "ad": "Peak T100 203x152 Tripod Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/peak-t100-203x152-70inch-tripod-projeksiyon-perdesi-pm-ofispeakt100"},
    {"site": "Hepsiburada", "ad": "Codegen TX-20 200x200 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/codegen-tx-20-200x200-tripod-ayakli-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-HB00000F7Y3B"},
    {"site": "Hepsiburada", "ad": "Golge Stor 200x115 Tripod Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en200cm-boy115cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000079V02J"},
    {"site": "Hepsiburada", "ad": "Havit 220x125 Tripod Projeksiyon Perdesi",               "url": "https://www.hepsiburada.com/havit-220x125cm-ayarlanabilir-100inc-16-9-boyut-ayakli-projeksiyon-perdesi-pm-HBC00004XPTF9"},
    {"site": "Hepsiburada", "ad": "Liteout 200x200 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-projeksiyon-perdesi-200x200-cm-kullanim-kolayligi-ile-pm-HB00000I6DTO"},
    {"site": "Hepsiburada", "ad": "Liteout 200x150 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-200x150-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HBC0000060DCT"},
    {"site": "Hepsiburada", "ad": "Taviss 221x124 Tripod Projeksiyon Perdesi",              "url": "https://www.hepsiburada.com/taviss-221x124-cm-mat-beyaz-siyah-tripod-ayakli-tasinabilir-ve-duvar-kullanimli-projeksiyon-perdesi-pm-HBC000087KP3S"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Tripod Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-220x125cm-blackout-isik-gecirmez-tripod-ayakli-projeksiyon-perdesi-tasinabilir-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHOIH"},
    {"site": "Hepsiburada", "ad": "Gamma Screens 240x200 Tripod Projeksiyon Perdesi",       "url": "https://www.hepsiburada.com/gamma-screens-240x200-tripod-projeksiyon-perdesi-pm-HB00000E7VNB"},
    {"site": "Hepsiburada", "ad": "Liteout 240x200 Tripod Projeksiyon Perdesi",             "url": "https://www.hepsiburada.com/liteout-240x200-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000I6DTQ"},
    {"site": "Hepsiburada", "ad": "Peak 244x183 Tripod Projeksiyon Perdesi",                "url": "https://www.hepsiburada.com/peak-ayakli-tasinabilir-projeskiyon-perdesi-arkasi-siyah-fonlu-120-244-x-183-cm-pm-HB00000JGUUY"},
    {"site": "Hepsiburada", "ad": "Peak T120 244x183 Tripod Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/peak-t120-244x183-120inch-tripod-projeksiyon-perdesi-pm-ofispeakt120"},
    {"site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Tripod Projeksiyon Perdesi",    "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-265x150cm-blackout-isik-gecirmez-tripod-ayakli-projeksiyon-perdesi-tasinabilir-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHN9R"},

    # ── Rakip HB ürünleri — Floor Up ────────────────────────
    {"site": "Hepsiburada", "ad": "Peak F60 120x90 Floor Up Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/peak-120-90-cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f60-pm-HBC000074AEGH"},
    {"site": "Hepsiburada", "ad": "Peak F70 142x107 Floor Up Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-142x107cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f70-pm-HBC000074AD5M"},
    {"site": "Hepsiburada", "ad": "Peak F80 163x122 Floor Up Projeksiyon Perdesi",          "url": "https://www.hepsiburada.com/peak-163x122-cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f80-pm-HBC000074AEKM"},
    {"site": "Hepsiburada", "ad": "Codegen 221x123 Floor Up Projeksiyon Perdesi",           "url": "https://www.hepsiburada.com/codegen-221x123-cm-tasinabilir-portatif-pull-up-floor-screen-projeksiyon-perdesi-pm-HBC00002JMHXG"},
    {"site": "Hepsiburada", "ad": "Codegen 145x82 Floor Up Projeksiyon Perdesi",            "url": "https://www.hepsiburada.com/codegen-145x82-cm-tasinabilir-portatif-pull-up-floor-screen-projeksiyon-perdesi-pm-HBC00003UTMN2"},
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

def zenrows_fetch(url):
    global ZENROWS_API_KEY, _key_index
    for attempt in range(len(ZENROWS_API_KEYS)):
        params = {
            "apikey": ZENROWS_API_KEY,
            "url": url,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "tr",
        }
        r = requests.get("https://api.zenrows.com/v1/", params=params, timeout=60)
        if r.status_code == 200:
            return r.text
        elif r.status_code == 402:
            # Kota doldu, sonraki key'e geç
            _key_index += 1
            if _key_index < len(ZENROWS_API_KEYS):
                ZENROWS_API_KEY = ZENROWS_API_KEYS[_key_index]
                print(f"  ⚡ Key {_key_index+1}/{len(ZENROWS_API_KEYS)} geçildi")
            else:
                print("  ❌ Tüm key'lerin kotası doldu!")
                return None
        else:
            print(f"  ZenRows {r.status_code}: {r.text[:100]}")
            return None
    return None

def cek_urun(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None}
    site = urun["site"].lower()
    html = zenrows_fetch(urun["url"])
    if not html:
        return sonuc

    if site == "n11":
        m = re.search(r'"displayPrice"\s*:\s*"([0-9.,]+ TL)"', html)
        if not m:
            m = re.search(r'"displayPrice"\s*:\s*"([0-9.,]+)"', html)
        if m:
            val = fiyat_parse(m.group(1))
            if val and val > 10:
                sonuc["fiyat"] = val
        m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        if m: sonuc["puan"] = float(m.group(1))
        m = re.search(r'"reviewCount"\s*:\s*(\d+)', html)
        if not m: m = re.search(r'(\d+)\s*[Dd]eğerlendirme', html)
        if m: sonuc["yorum"] = int(m.group(1).replace('.', ''))

    elif site == "trendyol":
        for pat in [r'"priceInfo"\s*:\s*\{[^}]*"discountedPrice"\s*:\s*([\d.]+)',
                    r'"priceInfo"\s*:\s*\{[^}]*"price"\s*:\s*([\d.]+)',
                    r'"sellingPrice"\s*:\s*([\d.]+)']:
            m = re.search(pat, html)
            if m:
                sonuc["fiyat"] = float(m.group(1))
                break
        if not sonuc["fiyat"]:
            matches = re.findall(r'([\d]{1,3}(?:\.\d{3})+(?:,\d+)?)\s*TL', html)
            for m in matches:
                val = fiyat_parse(m)
                if val and 500 < val < 100000:
                    sonuc["fiyat"] = val
                    break
        m = re.search(r'"ratingScore"\s*:\s*([\d.]+)', html)
        if m: sonuc["puan"] = float(m.group(1))
        m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
        if m: sonuc["yorum"] = int(m.group(1))

    elif site == "hepsiburada":
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
        if not sonuc["fiyat"]:
            m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', html)
            if m: sonuc["fiyat"] = fiyat_parse(m.group(1))
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
        ws = sh.add_worksheet("Ürün Takip", rows=200, cols=10)

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
        time.sleep(1.2)

    print(f"✅ Google Sheets güncellendi: {tarih} {saat}")

if __name__ == "__main__":
    print(f"🚀 Ürün takip başlatıldı... Toplam {len(URUNLER)} ürün")
    veriler = []
    for i, urun in enumerate(URUNLER):
        print(f"  [{i+1}/{len(URUNLER)}] {urun['ad'][:50]}")
        veri = cek_urun(urun)
        print(f"    fiyat={veri['fiyat']} puan={veri['puan']} yorum={veri['yorum']}")
        veriler.append({**urun, **veri})
        time.sleep(2)
    print("\n📊 Google Sheets güncelleniyor...")
    sheets_guncelle(veriler)
    print("✅ Tamamlandı!")


									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
