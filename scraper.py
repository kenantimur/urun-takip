import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
import time
import re
import os

ZENROWS_API_KEY = "890b4485ccc0e6e82ced6ccff8190fb2dc5cf249"

# ============================================================
#  TAKİP EDİLECEK ÜRÜNLER
#  Yeni ürün eklemek: listeye {"site": "...", "ad": "...", "url": "..."} satırı ekle
#  Silmek: ilgili satırı sil
# ============================================================
URUNLER = [
    # ── e150 ──────────────────────────────────────────────
    {"olcu": "e150", "site": "Hepsiburada", "ad": "Golge Stor 150x160 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en150cm-boy160cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002Z5W7V"},
    {"olcu": "e150", "site": "Hepsiburada", "ad": "Liteout LO150MP 150x150 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-lo150mp-150x150-cm-motorlu-projeksiyon-perdesi-pm-HB00000I6DTF"},
    {"olcu": "e150", "site": "Hepsiburada", "ad": "Liteout LO160M 160x160 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-lo160m-160x160-cm-motorlu-kumandali-projeksiyon-perdesi-pm-HB00000I6DTI"},
    # ── e180 ──────────────────────────────────────────────
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Gamma Screens 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-180x180-motorlu-projeksiyon-perdesi-pm-HB000009FK0A"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Peak M70 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-m70-180x180cm-70inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm70"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Golge Stor 180x170 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-180x170-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000031WBPJ"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Codegen EX-18 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ex-18-180x180-motorlu-uzaktan-kumandali-pro-perde-pm-HB00000F8530"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Liteout LO180M 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-lo180m-180x180-cm-motorlu-beyaz-standart-projeksiyon-perdesi-kumanda-dahil-pm-ofislomt180180"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Xblack 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/xblack-180-x-180-cm-cam-tozlu-kumas-motorlu-uzaktan-kumandali-projeksiyon-perdesi-xge-180-arkasi-siyah-fonlu-pm-ofisxblamtr"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Groove Vizio Pro 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-180x180cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A75TU5"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Rovline Akıllı 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/rovline-akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-180x180-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-HBCV0000EXB4J0"},
    {"olcu": "e180", "site": "Hepsiburada", "ad": "Golge Stor 180x170 Şarjlı Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en-180cm-boy-170cm-sarjli-projeksiyon-perdesi-lityum-pilli-uzun-omurlu-ve-uzaktan-kumandali-p-HBCV00007I3MP9"},
    # ── e200 ──────────────────────────────────────────────
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Gamma Screens 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-200x200-motorlu-projeksiyon-perdesi-pm-HB000009FK0C"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Peak M100 203x152 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-m100-203x152cm-100inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm100"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Codegen EX-20 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ex-20-200x200-cm-motorlu-elektrikli-uzaktan-kumandali-projeksiyon-perdesi-arkasi-siyah-fonlu-p-OFISCODEXMTR-EX20"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Everest EPP-200 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/everest-epp-200-200-200cm-uzaktan-kumandali-otomatik-projeksiyon-perdesi-pm-HBC0000BFGPCJ"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Xbright 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/xbright-200-x-200-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-200-arkasi-siyah-fonlu-pm-HB00000OYTH3"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Rovline Akıllı 200x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/rovline-akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-200x180-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-HBCV0000EXB47Y"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Liteout 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x200-cm-motorlu-kumandali-projeksiyon-perdesi-p-OFISLOMT200200"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Liteout 200x125 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x125-cm-motorlu-kumandali-projeksiyon-perdesi-pm-ofislomt200125"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Liteout 200x150 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x150-cm-motorlu-kumandali-projeksiyon-perdesi-pm-HBC000013IBXG"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Groove Vizio Pro 200x180 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-200x180cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GXX3"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Golge Stor 200x190 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-200x190-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000031WBPL"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Groove Vizio Pro 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-200x200cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7G1ZO"},
    {"olcu": "e200", "site": "Hepsiburada", "ad": "Golge Stor 210x190 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-210x190-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W731"},
    # ── e220 ──────────────────────────────────────────────
    {"olcu": "e220", "site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-220x125cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7EFBS"},
    # ── e240 ──────────────────────────────────────────────
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Full Screen 234x132 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/full-screen-fullscreen-234x132-motorlu-projeksiyon-perdesi-16-9-format-pm-HBC000077GEZH"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Gamma Screens 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-240x200-motorlu-projeksiyon-perdesi-p-HBV000009FK09"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Xbright 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/xbright-240-x-200-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-240-arkasi-siyah-fonlu-pm-HB00000OYTHH"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Everest EPP-240 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/everest-epp-240-240-200cm-uzaktan-kumandali-otomatik-projeksiyon-perdesi-pm-HBC0000BFGQXE"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Peak M120 244x183 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-m120-244x183cm-120inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm120"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Fullscreen 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/fullscreen-240x200-motorlu-projeksiyon-perdesi-pm-HBC000076RFC2"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Groove Vizio Pro 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-240x200cm-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GM7J"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Golge Stor 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-240x200-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W733"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Akıllı 240x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-240x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXAU4U"},
    {"olcu": "e240", "site": "Hepsiburada", "ad": "Golge Stor 250x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en250cm-boy200cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00003XB4BE"},
    # ── e260 ──────────────────────────────────────────────
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Golge Stor 260x220 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-260x220-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032WKPW"},
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Akıllı 260x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-260x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXALED"},
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Gamma Screens 265x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-265x200-motorlu-projeksiyon-perdesi-pm-HB000009FK0E"},
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-265x150cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GHTF"},
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Fullscreen 265x150 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/fullscreen-265x150-motorlu-projeksiyon-perdesi-16-9-format-pm-HBC0000772H8G"},
    {"olcu": "e260", "site": "Hepsiburada", "ad": "Golge Stor 270x230 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-270x230-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC000032W735"},
    # ── e300 ──────────────────────────────────────────────
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Akıllı 290x200 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-290x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-pm-HBC0000EXAO1Z"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-300x225-motorlu-projeksiyon-perdesi-pm-HB000009FK0G"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Peak M150 305x229 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-m150-305x229cm-150-inc-motorlu-kumandali-projeksiyon-perdesi-pm-ofispeakm150"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Xbright 300x225 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/xbright-300-x-225-cm-motorlu-uzaktan-kumandali-projeksiyon-perdesi-be-300-arkasi-siyah-fonlu-pm-HB00000OYTHQ"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Liteout 300x225 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-motorlu-kumandali-projeksiyon-perdesi-300x225-cm-beyaz-renk-ile-kolay-kullanim-p-OFISLOMT300225"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Codegen EX-30 300x225 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ex-30-300x225-cm-motorlu-elektrikli-uzaktan-kumandali-projeksiyon-perdesi-arkasi-siyah-fonlu-p-OFISCODEXMTR-EX30"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Decon DPC-15 300x225 Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/decon-dpc-15-300x225-projeksiyon-perdesi-mat-beyaz-pm-HBC0000BKCNPJ"},
    {"olcu": "e300", "site": "Hepsiburada", "ad": "Golge Stor 290x225 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en290cm-boy225cm-motorlu-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00003W8RLD"},
    # ── e335 ──────────────────────────────────────────────
    {"olcu": "e335", "site": "Hepsiburada", "ad": "Golge Stor 340x240 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en340cm-boy240cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-pm-HBC00006Y3OBC"},
    {"olcu": "e335", "site": "Hepsiburada", "ad": "Groove Vizio Pro 332x188 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-150-inch-blackout-isik-gecirmez-elektrikli-otomatik-kumandali-projeksiyon-perdesi-332x188cm-motorlu-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000A7GUDX"},
    # ── e400 ──────────────────────────────────────────────
    {"olcu": "e400", "site": "Hepsiburada", "ad": "Peak M200 400x300 Motorlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-m200-400x300cm-200inch-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-pm-ofispeakm200"},
    # ── s150 ──────────────────────────────────────────────
    {"olcu": "s150", "site": "Hepsiburada", "ad": "Liteout 150x150 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-150x150-cm-storlu-manuel-projeksiyon-perdesi-pm-HB00000HZWM9"},
    {"olcu": "s150", "site": "Hepsiburada", "ad": "Golge Stor 150x160 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-150x160-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLS"},
    # ── s180 ──────────────────────────────────────────────
    {"olcu": "s180", "site": "Hepsiburada", "ad": "Gamma Screens 180x180 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-180x180-cm-storlu-projeksiyon-perdesi-p-HBV000009FK0J"},
    {"olcu": "s180", "site": "Hepsiburada", "ad": "Codegen AX-18 180x180 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ax-18-180x180-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-18"},
    {"olcu": "s180", "site": "Hepsiburada", "ad": "Golge Stor 180x170 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-180x170-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLU"},
    {"olcu": "s180", "site": "Hepsiburada", "ad": "Liteout 180x180 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-manuel-projeksiyon-perdesi-180x180-cm-mat-beyaz-renk-4k-uhd-ozellikli-pm-HB00000C3FD9"},
    # ── s200 ──────────────────────────────────────────────
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Gamma Screens 200x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-200x200-storlu-projeksiyon-perdesi-ultra-hd-yuksek-kontrast-goruntu-performansi-pm-HB000009FK0K"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Codegen AX-20 200x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ax-20-200x200-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-20"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Golge Stor 200x190 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-200x190-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC000030QHLW"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Everest MPP-200 200x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/everest-mpp-200-200-200cm-arkasi-siyah-fonlu-storlu-projeksiyon-perdesi-pm-HBC00008O6MXH"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Liteout 200x150 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x150-cm-storlu-manuel-projeksiyon-perdesi-pm-HB000008CI6Y"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Liteout 200x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x200-cm-storlu-manuel-projeksiyon-perdesi-yerli-uretim-ile-kaliteli-goruntu-p-OFISLOS200200"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Havit PS84M 84 inç Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/havit-ps84m-ayarlanabilir-84inc-duvar-perdesi-pm-HBC0000BADJWC"},
    {"olcu": "s200", "site": "Hepsiburada", "ad": "Golge Stor 210x180 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-en210cm-boy180cm-manuel-projeksiyon-perdesi-parlama-yapmaz-pm-HBC00005JRFT2"},
    # ── s220 ──────────────────────────────────────────────
    {"olcu": "s220", "site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-220x125cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHOFR"},
    # ── s240 ──────────────────────────────────────────────
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-240x200-cm-yuksek-gain-mat-beyaz-storlu-projeksiyon-perdesi-pratik-kullanim-pm-HB000009FK0M"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Codegen AX-24 240x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-ax-24-240x200-storlu-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodegenax-24"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Peak 244x183 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-storlu-arkasi-siyah-ithal-projeksiyon-perdesi-beyaz-kasa-244-x-183-cm-pm-HB00000JGUV0"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Golge Stor 240x220 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-240x220-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002YNYEO"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Liteout LO240S 240x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-lo240s-240x200-cm-storlu-projeksiyon-perdesi-pm-ofislos240200"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Liteout 250x190 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-250x190-cm-storlu-manuel-projeksiyon-perdesi-p-HBV00000MM2OB"},
    {"olcu": "s240", "site": "Hepsiburada", "ad": "Golge Stor 250x200 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-golge-storen250cm-boy200cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-teknolojisi-pm-HBC00005ULW5Q"},
    # ── s260 ──────────────────────────────────────────────
    {"olcu": "s260", "site": "Hepsiburada", "ad": "Golge Stor 260x230 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-260x230-manuel-projeksiyon-perdesi-parlama-yapmaz-stor-kumas-pm-HBC00002YNYEQ"},
    {"olcu": "s260", "site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-265x150cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHQ7H"},
    # ── s335 ──────────────────────────────────────────────
    {"olcu": "s335", "site": "Hepsiburada", "ad": "Groove Vizio Pro 332x188 Storlu Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-150-inch-332x188cm-blackout-isik-gecirmez-profesyonel-projeksiyon-perdesi-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHPU2"},
    # ── t100 ──────────────────────────────────────────────
    {"olcu": "t100", "site": "Hepsiburada", "ad": "Liteout 100x75 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-100x75-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000TKG1M"},
    # ── t120 ──────────────────────────────────────────────
    {"olcu": "t120", "site": "Hepsiburada", "ad": "Liteout 120x90 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-tasinabilir-projeksiyon-perdesi-120x90-cm-kullanim-kolayligi-ile-pm-HB00000TDD80"},
    {"olcu": "t120", "site": "Hepsiburada", "ad": "Liteout 135x100 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-135x100-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HBC000007YL17"},
    # ── t150 ──────────────────────────────────────────────
    {"olcu": "t150", "site": "Hepsiburada", "ad": "Havit PS60 60 inç Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/havit-ps60-tasinabilir-ayakli-projeksiyon-perdesi-60-inc-pm-HBC00006LAOLZ"},
    {"olcu": "t150", "site": "Hepsiburada", "ad": "Gamma Screens 150x150 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-150x150-tripod-ayakli-projeksiyon-perdesi-pm-HBC0000CQ9NR5"},
    {"olcu": "t150", "site": "Hepsiburada", "ad": "Liteout 150x150 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-tasinabilir-tripod-ayakli-projeksiyon-perdesi-150x150-cm-beyaz-renkli-pm-HB00000I6DTA"},
    {"olcu": "t150", "site": "Hepsiburada", "ad": "Golge Stor 150x95 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en150cm-boy95cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000076UA1G"},
    {"olcu": "t150", "site": "Hepsiburada", "ad": "Liteout 160x160 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-160x160-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000UF6OO"},
    # ── t180 ──────────────────────────────────────────────
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Gamma Screens 180x180 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-180-x-180-tripod-projeksiyon-perdesi-pm-HB00000A5M3H"},
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Codegen TX-18 180x180 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-tx-18-180x180-tripod-ithal-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-ofiscodaxtrp"},
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Havit PS72M 72 inç Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/havit-ps72m-ayarlanabilir-72inc-duvar-perdesi-pm-HBC0000BADJWA"},
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Golge Stor 180x105 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en180cm-boy105cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000076U6V0"},
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Liteout 180x180 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-projeksiyon-perdesi-180x180-cm-mat-beyaz-4k-uhd-1-1-model-pm-ofislotri180180"},
    {"olcu": "t180", "site": "Hepsiburada", "ad": "Peak T70 180x180 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-t70-180x180-70inch-tripod-projeksiyon-perdesi-pm-ofispeakt70"},
    # ── t200 ──────────────────────────────────────────────
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Gamma Screens 200x200 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-200-x-200-tripod-projeksiyon-perdesi-pm-HB00000A5M3J"},
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Peak T100 203x152 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-t100-203x152-70inch-tripod-projeksiyon-perdesi-pm-ofispeakt100"},
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Codegen TX-20 200x200 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-tx-20-200x200-tripod-ayakli-projeksiyon-perdesi-arkasi-siyah-fonlu-pm-HB00000F7Y3B"},
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Golge Stor 200x115 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/golge-stor-tripodlu-en200cm-boy115cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-HBCV000079V02J"},
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Havit 220x125 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/havit-220x125cm-ayarlanabilir-100inc-16-9-boyut-ayakli-projeksiyon-perdesi-pm-HBC00004XPTF9"},
    {"olcu": "t200", "site": "Hepsiburada", "ad": "Liteout 200x200 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-tripod-ayakli-projeksiyon-perdesi-200x200-cm-kullanim-kolayligi-ile-pm-HB00000I6DTO"},
    # ── t220 ──────────────────────────────────────────────
    {"olcu": "t220", "site": "Hepsiburada", "ad": "Liteout 200x150 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-200x150-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HBC0000060DCT"},
    {"olcu": "t220", "site": "Hepsiburada", "ad": "Taviss 221x124 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/taviss-221x124-cm-mat-beyaz-siyah-tripod-ayakli-tasinabilir-ve-duvar-kullanimli-projeksiyon-perdesi-pm-HBC000087KP3S"},
    {"olcu": "t220", "site": "Hepsiburada", "ad": "Groove Vizio Pro 220x125 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-100-inch-220x125cm-blackout-isik-gecirmez-tripod-ayakli-projeksiyon-perdesi-tasinabilir-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHOIH"},
    # ── t240 ──────────────────────────────────────────────
    {"olcu": "t240", "site": "Hepsiburada", "ad": "Gamma Screens 240x200 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/gamma-screens-240x200-tripod-projeksiyon-perdesi-pm-HB00000E7VNB"},
    {"olcu": "t240", "site": "Hepsiburada", "ad": "Liteout 240x200 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/liteout-240x200-cm-tripod-ayakli-tasinabilir-projeksiyon-perdesi-pm-HB00000I6DTQ"},
    {"olcu": "t240", "site": "Hepsiburada", "ad": "Peak 244x183 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-ayakli-tasinabilir-projeskiyon-perdesi-arkasi-siyah-fonlu-120-244-x-183-cm-pm-HB00000JGUUY"},
    {"olcu": "t240", "site": "Hepsiburada", "ad": "Peak T120 244x183 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-t120-244x183-120inch-tripod-projeksiyon-perdesi-pm-ofispeakt120"},
    # ── t265 ──────────────────────────────────────────────
    {"olcu": "t265", "site": "Hepsiburada", "ad": "Groove Vizio Pro 265x150 Tripod Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/groove-vizio-pro-120-inch-265x150cm-blackout-isik-gecirmez-tripod-ayakli-projeksiyon-perdesi-tasinabilir-canli-renkler-goz-korumasi-leke-tutmaz-projector-pm-HBC0000ABHN9R"},
    # ── p120 ──────────────────────────────────────────────
    {"olcu": "p120", "site": "Hepsiburada", "ad": "Peak F60 120x90 Floor Up Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-120-90-cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f60-pm-HBC000074AEGH"},
    # ── p140 ──────────────────────────────────────────────
    {"olcu": "p140", "site": "Hepsiburada", "ad": "Peak F70 142x107 Floor Up Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-142x107cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f70-pm-HBC000074AD5M"},
    {"olcu": "p140", "site": "Hepsiburada", "ad": "Peak F80 163x122 Floor Up Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/peak-163x122-cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f80-pm-HBC000074AEKM"},
    # ── p160 ──────────────────────────────────────────────
    {"olcu": "p160", "site": "Hepsiburada", "ad": "Codegen 221x123 Floor Up Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-221x123-cm-tasinabilir-portatif-pull-up-floor-screen-projeksiyon-perdesi-pm-HBC00002JMHXG"},
    # ── p140 ──────────────────────────────────────────────
    {"olcu": "p140", "site": "Hepsiburada", "ad": "Codegen 145x82 Floor Up Projeksiyon Perdesi", "url": "https://www.hepsiburada.com/codegen-145x82-cm-tasinabilir-portatif-pull-up-floor-screen-projeksiyon-perdesi-pm-HBC00003UTMN2"},
    # ── e300 ──────────────────────────────────────────────
    {"olcu": "e300", "site": "Trendyol", "ad": "Gamma Screens 300x225 Motorlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/300x225-motorlu-projeksiyon-perdesi-p-32240151?boutiqueId=61&merchantId=108524"},
    # ── p140 ──────────────────────────────────────────────
    {"olcu": "p140", "site": "Trendyol", "ad": "CODEGEN 145x82 cm Taşınabilir Portatif Pull Up Floor Screen Projeksiyon Perdesi", "url": "https://www.trendyol.com/codegen/145x82-cm-tasinabilir-portatif-pull-up-floor-screen-projeksiyon-perdesi-p-994418874?boutiqueId=61&merchantId=1058560"},
    # ── s150 ──────────────────────────────────────────────
    {"olcu": "s150", "site": "Trendyol", "ad": "Genel Markalar Zincirli Projeksiyon Perdesi 160x160", "url": "https://www.trendyol.com/genel-markalar/zincirli-projeksiyon-perdesi-160x160-p-109199334?boutiqueId=61&merchantId=402585"},
    # ── s180 ──────────────────────────────────────────────
    {"olcu": "s180", "site": "Trendyol", "ad": "CODEGEN AX-18 180x180 cm Storlu Manuel Projeksiyon Perdesi (Arkası Siyah Fonlu)", "url": "https://www.trendyol.com/codegen/ax-18-180x180-cm-storlu-manuel-projeksiyon-perdesi-arkasi-siyah-fonlu-p-2704854?boutiqueId=61&merchantId=1058560"},
    # ── s200 ──────────────────────────────────────────────
    {"olcu": "s200", "site": "Trendyol", "ad": "Gamma Screens 200x200 Storlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/200x200-storlu-projeksiyon-perdesi-p-49002023?boutiqueId=61&merchantId=108524"},
    {"olcu": "s200", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En200cm Boy180cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k", "url": "https://www.trendyol.com/golge-stor/manuel-en200cm-boy180cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-p-366301882?boutiqueId=61&merchantId=585843"},
    # ── s240 ──────────────────────────────────────────────
    {"olcu": "s240", "site": "Trendyol", "ad": "Gamma Screens 240x200 Storlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/240x200-storlu-projeksiyon-perdesi-p-32240762?boutiqueId=61&merchantId=108524"},
    {"olcu": "s240", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En240cm Boy190cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/manuel-en240cm-boy190cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-372039412?boutiqueId=61&merchantId=585843"},
    {"olcu": "s240", "site": "Trendyol", "ad": "Genel Markalar Storlu Arkası Siyah Ithal Projeksiyon Perdesi-beyaz Kasa 240 X 200 Cm", "url": "https://www.trendyol.com/genel-markalar/storlu-arkasi-siyah-ithal-projeksiyon-perdesi-beyaz-kasa-240-x-200-cm-p-66169635?boutiqueId=61&merchantId=132091"},
    # ── t150 ──────────────────────────────────────────────
    {"olcu": "t150", "site": "Trendyol", "ad": "Gamma Screens 150x150 Tripod Ayaklı Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/150x150-tripod-ayakli-projeksiyon-perdesi-p-1129363771?boutiqueId=61&merchantId=108524"},
    # ── t180 ──────────────────────────────────────────────
    {"olcu": "t180", "site": "Trendyol", "ad": "Gamma Screens 180x180 Tripod Ayaklı Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/180x180-tripod-ayakli-projeksiyon-perdesi-p-782821120?boutiqueId=61&merchantId=108524"},
    # ── t200 ──────────────────────────────────────────────
    {"olcu": "t200", "site": "Trendyol", "ad": "GÖLGE STOR ( Tripodlu ) En200cm Boy115cm Projeksiyon Perdesi Ayaklı Taşınabilir Yeni Akıllı Kumaş Işık Geçirmez", "url": "https://www.trendyol.com/golge-stor/tripodlu-en200cm-boy115cm-projeksiyon-perdesi-ayakli-tasinabilir-yeni-akilli-kumas-isik-gecirmez-p-872481327?boutiqueId=61&merchantId=585843"},
    # ── t220 ──────────────────────────────────────────────
    {"olcu": "t220", "site": "Trendyol", "ad": "Havit 220x125cm Ayarlanabilir 100inç 16:9 Boyut Ayaklı Projeksiyon Perdesi", "url": "https://www.trendyol.com/havit/220x125cm-ayarlanabilir-100inc-16-9-boyut-ayakli-projeksiyon-perdesi-p-761572765?boutiqueId=61&merchantId=133183"},
    # ── t240 ──────────────────────────────────────────────
    {"olcu": "t240", "site": "Trendyol", "ad": "Genel Markalar T120 240x200 Cm Tripod Projeksiyon Perdesi", "url": "https://www.trendyol.com/genel-markalar/t120-240x200-cm-tripod-projeksiyon-perdesi-p-57433158?boutiqueId=61&merchantId=132091"},
    # ── s150 ──────────────────────────────────────────────
    {"olcu": "s150", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En150cm Boy160cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k", "url": "https://www.trendyol.com/golge-stor/manuel-en150cm-boy160cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-p-661489899?boutiqueId=61&merchantId=585843"},
    # ── e200 ──────────────────────────────────────────────
    {"olcu": "e200", "site": "Trendyol", "ad": "Gamma Screens 200x200 Motorlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/200x200-motorlu-projeksiyon-perdesi-p-1129289425?boutiqueId=61&merchantId=108524"},
    # ── s180 ──────────────────────────────────────────────
    {"olcu": "s180", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En180cm Boy170cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/manuel-en180cm-boy170cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-366319391?boutiqueId=61&merchantId=585843"},
    # ── s200 ──────────────────────────────────────────────
    {"olcu": "s200", "site": "Trendyol", "ad": "CODEGEN Ax-20 200x200 Cm Storlu Manuel Projeksiyon Perdesi (ARKASI SİYAH FONLU)", "url": "https://www.trendyol.com/codegen/ax-20-200x200-cm-storlu-manuel-projeksiyon-perdesi-arkasi-siyah-fonlu-p-2704858?boutiqueId=61&merchantId=1058560"},
    # ── e260 ──────────────────────────────────────────────
    {"olcu": "e260", "site": "Trendyol", "ad": "Gamma Screens 265x200 Motorlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/265x200-motorlu-projeksiyon-perdesi-p-32241750?boutiqueId=61&merchantId=108524"},
    # ── p80 ──────────────────────────────────────────────
    {"olcu": "p80", "site": "Trendyol", "ad": "CODEGEN MX-40 81x61 cm Taşınabilir Portatif Masaüstü Projeksiyon Perdesi ( Çanta Dahil)", "url": "https://www.trendyol.com/codegen/mx-40-81x61-cm-tasinabilir-portatif-masaustu-projeksiyon-perdesi-canta-dahil-p-129161294?boutiqueId=61&merchantId=1058560"},
    # ── s180 ──────────────────────────────────────────────
    {"olcu": "s180", "site": "Trendyol", "ad": "Genel Markalar Bej AX-18 STORLU PROJEKSİYON PERDESİ 180x180 (Arkası Siyah Fonlu - Duvar/Tavan Asılabilir) 1 Yıl", "url": "https://www.trendyol.com/genel-markalar/bej-ax-18-storlu-projeksiyon-perdesi-180x180-arkasi-siyah-fonlu-duvar-tavan-asilabilir-1-yil-p-760351235?boutiqueId=61&merchantId=145937"},
    # ── e200 ──────────────────────────────────────────────
    {"olcu": "e200", "site": "Trendyol", "ad": "GÖLGE STOR En:215cm Boy:180cm Şarjlı Projeksiyon Perdesi Lityum Pilli Uzun Ömürlü Ve Uzaktan Kumandalı", "url": "https://www.trendyol.com/golge-stor/en-215cm-boy-180cm-sarjli-projeksiyon-perdesi-lityum-pilli-uzun-omurlu-ve-uzaktan-kumandali-p-885143692?boutiqueId=61&merchantId=585843"},
    # ── e260 ──────────────────────────────────────────────
    {"olcu": "e260", "site": "Trendyol", "ad": "Rovline Akıllı Projeksiyon Perdesi, Wi-Fi + Rf, Motorlu, 260x200, Sesle Kontrol, Kumanda ve Mobil Uygulama Kontrollü, Tuya uyumlu", "url": "https://www.trendyol.com/rovline/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-260x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-1147923036?boutiqueId=61&merchantId=206489"},
    # ── s260 ──────────────────────────────────────────────
    {"olcu": "s260", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En260cm Boy190cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/manuel-en260cm-boy190cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-274499740?boutiqueId=61&merchantId=585843"},
    # ── t180 ──────────────────────────────────────────────
    {"olcu": "t180", "site": "Trendyol", "ad": "Genel Markalar T70 180x180(70inch)tripod Projeksiyon Perdesi", "url": "https://www.trendyol.com/genel-markalar/t70-180x180-70inch-tripod-projeksiyon-perdesi-p-59052827?boutiqueId=61&merchantId=132091"},
    # ── s200 ──────────────────────────────────────────────
    {"olcu": "s200", "site": "Trendyol", "ad": "GÖLGE STOR Manuel En210cm Boy180cm Projeksiyon Perdesi Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/manuel-en210cm-boy180cm-projeksiyon-perdesi-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-690590872?boutiqueId=61&merchantId=585843"},
    # ── e180 ──────────────────────────────────────────────
    {"olcu": "e180", "site": "Trendyol", "ad": "Gamma Screens 180x180 Motorlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/180x180-motorlu-projeksiyon-perdesi-p-32240800?boutiqueId=61&merchantId=108524"},
    # ── t200 ──────────────────────────────────────────────
    {"olcu": "t200", "site": "Trendyol", "ad": "CODEGEN TX-20 200x200 cm Tripod Ayaklı Taşınabilir Manuel Projeksiyon Perdesi (Arkası Siyah Fonlu)", "url": "https://www.trendyol.com/codegen/tx-20-200x200-cm-tripod-ayakli-tasinabilir-manuel-projeksiyon-perdesi-arkasi-siyah-fonlu-p-2704896?boutiqueId=61&merchantId=1058560"},
    # ── e240 ──────────────────────────────────────────────
    {"olcu": "e240", "site": "Trendyol", "ad": "Peak M120 240x200 Cm Motorlu Kumandalı Projeksiyon Perdesi-beyaz Kasa", "url": "https://www.trendyol.com/peak/m120-240x200-cm-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-p-66333205?boutiqueId=61&merchantId=132091"},
    # ── t240 ──────────────────────────────────────────────
    {"olcu": "t240", "site": "Trendyol", "ad": "CODEGEN 240X200Cm Tripod Projeksiyon Perdesi TX-24", "url": "https://www.trendyol.com/codegen/240x200cm-tripod-projeksiyon-perdesi-tx-24-p-847628508?boutiqueId=61&merchantId=201140"},
    # ── t200 ──────────────────────────────────────────────
    {"olcu": "t200", "site": "Trendyol", "ad": "LiteOut 200x200cm Tripod Ayaklı Projeksiyon Perdesi", "url": "https://www.trendyol.com/liteout/200x200cm-tripod-ayakli-projeksiyon-perdesi-p-5474853?boutiqueId=61&merchantId=107190"},
    # ── e340 ──────────────────────────────────────────────
    {"olcu": "e340", "site": "Trendyol", "ad": "GÖLGE STOR En340cm Boy225cm Projeksiyon Perdesi Motorlu Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/en340cm-boy225cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-857293551?boutiqueId=61&merchantId=585843"},
    # ── t180 ──────────────────────────────────────────────
    {"olcu": "t180", "site": "Trendyol", "ad": "Genel Markalar Tpp-180, 180x180, Trıpod, Projeksiyon Perdesi, Arkası Siyah Fonlu, Taşınabilir Ayaklı Model", "url": "https://www.trendyol.com/genel-markalar/tpp-180-180x180-tripod-projeksiyon-perdesi-arkasi-siyah-fonlu-tasinabilir-ayakli-model-p-941664099?boutiqueId=61&merchantId=712699"},
    # ── s240 ──────────────────────────────────────────────
    {"olcu": "s240", "site": "Trendyol", "ad": "gaman Storlu Projeksiyon Perdesi 240x200 Cm Işık Geçirmez Beyaz Renk Yüksek Kaliteli Görüntü İçin", "url": "https://www.trendyol.com/gaman/storlu-projeksiyon-perdesi-240x200-cm-isik-gecirmez-beyaz-renk-yuksek-kaliteli-goruntu-icin-p-1097390274?boutiqueId=61&merchantId=130886"},
    # ── e240 ──────────────────────────────────────────────
    {"olcu": "e240", "site": "Trendyol", "ad": "GÖLGE STOR En250cm Boy190cm Projeksiyon Perdesi Motorlu Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k", "url": "https://www.trendyol.com/golge-stor/en250cm-boy190cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-p-366307993?boutiqueId=61&merchantId=585843"},
    # ── p140 ──────────────────────────────────────────────
    {"olcu": "p140", "site": "Trendyol", "ad": "Peak 142x107cm Taşınabilir Portatif Pull Up Floor Projeksiyon Perdesi F70", "url": "https://www.trendyol.com/peak/142x107cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f70-p-865173120?boutiqueId=61&merchantId=132091"},
    # ── e300 ──────────────────────────────────────────────
    {"olcu": "e300", "site": "Trendyol", "ad": "Rovline Akıllı Projeksiyon Perdesi, Wi-Fi + Rf, Motorlu, 290x200, Sesle Kontrol, Kumanda ve Mobil Uygulama Kontrollü, Tuya uyumlu", "url": "https://www.trendyol.com/rovline/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-290x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-1147923242?boutiqueId=61&merchantId=206489"},
    # ── p200 ──────────────────────────────────────────────
    {"olcu": "p200", "site": "Trendyol", "ad": "CODEGEN PTX-200 210x123 Projeksiyon Perdesi Portatif Pull Up Floor", "url": "https://www.trendyol.com/codegen/ptx-200-210x123-projeksiyon-perdesi-portatif-pull-up-floor-p-1131291955?boutiqueId=61&merchantId=162201"},
    # ── t220 ──────────────────────────────────────────────
    {"olcu": "t220", "site": "Trendyol", "ad": "Groove Vizio Pro 100¨Inch 220x125cm Blackout Işık Geçirmez Tripod Ayaklı Projeksiyon Perdesi +Taşına", "url": "https://www.trendyol.com/groove/vizio-pro-100-inch-220x125cm-blackout-isik-gecirmez-tripod-ayakli-projeksiyon-perdesi-tasina-p-996713723?boutiqueId=61&merchantId=106199"},
    # ── e200 ──────────────────────────────────────────────
    {"olcu": "e200", "site": "Trendyol", "ad": "Peak M100 200x150 Cm Motorlu Kumandalı Projeksiyon Perdesi-beyaz Kasa", "url": "https://www.trendyol.com/peak/m100-200x150-cm-motorlu-kumandali-projeksiyon-perdesi-beyaz-kasa-p-66902102?boutiqueId=61&merchantId=132091"},
    # ── e150 ──────────────────────────────────────────────
    {"olcu": "e150", "site": "Trendyol", "ad": "GÖLGE STOR En:150cm Boy:160cm Şarjlı Projeksiyon Perdesi Lityum Pilli Uzun Ömürlü Ve Uzaktan Kumandalı", "url": "https://www.trendyol.com/golge-stor/en-150cm-boy-160cm-sarjli-projeksiyon-perdesi-lityum-pilli-uzun-omurlu-ve-uzaktan-kumandali-p-885161024?boutiqueId=61&merchantId=585843"},
    # ── s240 ──────────────────────────────────────────────
    {"olcu": "s240", "site": "Trendyol", "ad": "taviss 240X200 CM STORLU MANUEL PROJEKSİYON PERDESİ", "url": "https://www.trendyol.com/taviss/240x200-cm-storlu-manuel-projeksiyon-perdesi-p-863626403?boutiqueId=61&merchantId=182955"},
    # ── t120 ──────────────────────────────────────────────
    {"olcu": "t120", "site": "Trendyol", "ad": "LiteOut 135x100cm Tripod Projeksiyon Perdesi", "url": "https://www.trendyol.com/liteout/135x100cm-tripod-projeksiyon-perdesi-p-117353791?boutiqueId=61&merchantId=107190"},
    # ── p160 ──────────────────────────────────────────────
    {"olcu": "p160", "site": "Trendyol", "ad": "Peak 163X122 cm Taşınabilir Portatif Pull Up Floor Projeksiyon Perdesi F80", "url": "https://www.trendyol.com/peak/163x122-cm-tasinabilir-portatif-pull-up-floor-projeksiyon-perdesi-f80-p-951821437?boutiqueId=61&merchantId=132091"},
    # ── s180 ──────────────────────────────────────────────
    {"olcu": "s180", "site": "Trendyol", "ad": "Gamma Screens 180x180 Storlu Projeksiyon Perdesi", "url": "https://www.trendyol.com/gamma-screens/180x180-storlu-projeksiyon-perdesi-p-49150741?boutiqueId=61&merchantId=108524"},
    # ── t120 ──────────────────────────────────────────────
    {"olcu": "t120", "site": "Trendyol", "ad": "LiteOut 120x90cm Taşınabilir Tripod Ayaklı Projeksiyon Perdesi", "url": "https://www.trendyol.com/liteout/120x90cm-tasinabilir-tripod-ayakli-projeksiyon-perdesi-p-40132511?boutiqueId=61&merchantId=107190"},
    # ── e300 ──────────────────────────────────────────────
    {"olcu": "e300", "site": "Trendyol", "ad": "GÖLGE STOR En290cm Boy200cm Projeksiyon Perdesi Motorlu Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/en290cm-boy200cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-681098047?boutiqueId=61&merchantId=585843"},
    # ── e200 ──────────────────────────────────────────────
    {"olcu": "e200", "site": "Trendyol", "ad": "GÖLGE STOR En200cm Boy180cm Projeksiyon Perdesi Motorlu Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/en200cm-boy180cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-333049751?boutiqueId=61&merchantId=585843"},
    # ── e260 ──────────────────────────────────────────────
    {"olcu": "e260", "site": "Trendyol", "ad": "GÖLGE STOR En267cm Boy200cm Projeksiyon Perdesi Motorlu Yeni Akıllı Kumaş Blackout-ışık Geçirmez 4k 8k Hd", "url": "https://www.trendyol.com/golge-stor/en267cm-boy200cm-projeksiyon-perdesi-motorlu-yeni-akilli-kumas-blackout-isik-gecirmez-4k-8k-hd-p-371919259?boutiqueId=61&merchantId=585843"},
    # ── e180 ──────────────────────────────────────────────
    {"olcu": "e180", "site": "Trendyol", "ad": "Rovline Akıllı Projeksiyon Perdesi, Wi-Fi + Rf, Motorlu, 180x180, Sesle Kontrol, Kumanda ve Mobil Uygulama Kontrollü, Tuya uyumlu", "url": "https://www.trendyol.com/pd/rovline/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-180x180-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-1147923685?boutiqueId=61&merchantId=206489"},
    # ── s240 ──────────────────────────────────────────────
    {"olcu": "s240", "site": "Trendyol", "ad": "CODEGEN AX-24 240x200 cm Storlu Manuel Projeksiyon Perdesi (Arkası Siyah Fonlu)", "url": "https://www.trendyol.com/codegen/ax-24-240x200-cm-storlu-manuel-projeksiyon-perdesi-arkasi-siyah-fonlu-p-90956708?boutiqueId=61&merchantId=1058560"},
    # ── e240 ──────────────────────────────────────────────
    {"olcu": "e240", "site": "Trendyol", "ad": "Rovline Akıllı Projeksiyon Perdesi, Wi-Fi + Rf, Motorlu, 240x200, Sesle Kontrol, Kumanda ve Mobil Uygulama Kontrollü, Tuya uyumlu", "url": "https://www.trendyol.com/pd/rovline/akilli-projeksiyon-perdesi-wi-fi-rf-motorlu-240x200-sesle-kontrol-kumanda-ve-mobil-uygulama-kontrollu-tuya-uyumlu-p-1147920610?choicennenabled=false&subPathStrategy=no-subpath&boutiqueId=61&merchantId=206489"},
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

def proxy_fetch(url, site=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }

    # Önce direkt dene (sadece N11 için yeterli; Trendyol/Hepsiburada ülke/bot engeli koyuyor)
    if site != "trendyol" and site != "hepsiburada":
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200 and len(r.text) > 5000:
                print(f"  Direkt HTTP 200")
                return r.text
        except:
            pass

    # ZenRows ile dene
    try:
        params = {
            "apikey": ZENROWS_API_KEY,
            "url": url,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "tr",
        }
        extra_headers = {}
        if site == "trendyol":
            extra_headers = {"Cookie": "storefrontId=1; countryCode=TR; language=tr"}

        r = requests.get("https://api.zenrows.com/v1/", params=params, timeout=90, headers=extra_headers)
        print(f"  ZenRows HTTP {r.status_code}")
        if r.status_code == 200:
            if "m-country-selection" in r.text:
                print(f"  ZenRows ülke seçim sayfası döndü")
                return None
            return r.text
        print(f"  ZenRows hata: {r.text[:150]}")
    except Exception as e:
        print(f"  ZenRows hata: {e}")

    return None

def cek_urun(urun):
    sonuc = {"fiyat": None, "puan": None, "yorum": None, "satici": None}
    site = urun["site"].lower()
    url = urun["url"]
    # Trendyol için TR sürümünü zorla
    if site == "trendyol" and "storefrontId" not in url:
        sep = "&" if "?" in url else "?"
        url = url + sep + "storefrontId=1&culture=tr-TR"
    html = proxy_fetch(url, site)
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
        for pat in [r'"discountedPrice"\s*:\s*\{[^}]*"value"\s*:\s*([\d.]+)',
                    r'"discountedPrice"\s*:\s*([\d.]+)',
                    r'"priceInfo"\s*:\s*\{[^}]*"discountedPrice"\s*:\s*([\d.]+)',
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

        # JSON-LD üzerinden puan ve satıcı
        for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                ld = json.loads(ld_str)
                agg = ld.get("aggregateRating", {})
                if agg.get("ratingValue"):
                    sonuc["puan"] = float(str(agg["ratingValue"]).replace(",", "."))
                if agg.get("reviewCount") and not sonuc["yorum"]:
                    sonuc["yorum"] = int(agg["reviewCount"])
                offers = ld.get("offers", {})
                if isinstance(offers, list): offers = offers[0]
                seller = offers.get("seller", {})
                if isinstance(seller, dict) and seller.get("name"):
                    sonuc["satici"] = seller["name"]
            except:
                pass

        if not sonuc["puan"]:
            for pat in [r'"ratingScore"\s*:\s*\{[^}]*"averageRating"\s*:\s*([\d.]+)',
                        r'"ratingScore"\s*:\s*([\d.]+)',
                        r'"averageRating"\s*:\s*"?([\d.]+)"?',
                        r'"rate"\s*:\s*([\d.]+)']:
                m = re.search(pat, html)
                if m:
                    sonuc["puan"] = float(m.group(1))
                    break

        m = re.search(r'"commentCount"\s*:\s*(\d+)', html)
        if m: sonuc["yorum"] = int(m.group(1))

        if not sonuc["satici"]:
            for pat in [r'"merchantName"\s*:\s*"([^"]+)"',
                        r'"sellerName"\s*:\s*"([^"]+)"',
                        r'"storeName"\s*:\s*"([^"]+)"',
                        r'class="[^"]*merchant-name[^"]*"[^>]*>\s*([^<]+)']:
                m = re.search(pat, html)
                if m:
                    sonuc["satici"] = m.group(1).strip()
                    break

        if not sonuc["satici"]:
            # JSON-LD bloklarından seller/brand bilgisini ara
            for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
                try:
                    ld = json.loads(ld_str)
                    if isinstance(ld, list):
                        for item in ld:
                            if isinstance(item, dict):
                                offers = item.get("offers", {})
                                if isinstance(offers, list): offers = offers[0] if offers else {}
                                seller = offers.get("seller", {}) if isinstance(offers, dict) else {}
                                if isinstance(seller, dict) and seller.get("name"):
                                    sonuc["satici"] = seller["name"]
                                    print(f"    DBG JSON-LD listeden satıcı bulundu: {seller['name']}")
                    elif isinstance(ld, dict):
                        offers = ld.get("offers", {})
                        if isinstance(offers, list): offers = offers[0] if offers else {}
                        seller = offers.get("seller", {}) if isinstance(offers, dict) else {}
                        if isinstance(seller, dict) and seller.get("name"):
                            sonuc["satici"] = seller["name"]
                            print(f"    DBG JSON-LD dict satıcı bulundu: {seller['name']}")
                except Exception as e:
                    pass

            if not sonuc["satici"]:
                # merchantName regex - JSON içinde isim formatı dene
                for pat in [r'"merchantName"\s*:\s*"([^"]{2,40})"',
                            r'"merchant"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]{2,40})"',
                            r'"storeName"\s*:\s*"([^"]{2,40})"',
                            r'"sellerName"\s*:\s*"([^"]{2,40})"',
                            r'"merchantDisplayName"\s*:\s*"([^"]{2,40})"']:
                    m = re.search(pat, html)
                    if m:
                        sonuc["satici"] = m.group(1).strip()
                        print(f"    DBG regex satıcı bulundu ({pat}): {m.group(1)}")
                        break

            if not sonuc["satici"]:
                # DOM'dan dene - "Mağazaya Git" veya "Satıcı:" gibi metin civarı
                m = re.search(r'class="[^"]*store-name[^"]*"[^>]*>\s*([^<]{2,50})', html)
                if not m:
                    m = re.search(r'class="[^"]*merchant-info[^"]*"[^>]*>\s*<[^>]+>\s*([^<]{2,50})', html)
                if m:
                    sonuc["satici"] = m.group(1).strip()
                    print(f"    DBG DOM satıcı bulundu: {m.group(1)}")

    elif site == "hepsiburada":
        for ld_str in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                ld = json.loads(ld_str)
                offers = ld.get("offers", {})
                if isinstance(offers, list): offers = offers[0]
                if offers.get("price"):
                    sonuc["fiyat"] = float(str(offers["price"]).replace(",", "."))
                if offers.get("seller", {}).get("name"):
                    sonuc["satici"] = offers["seller"]["name"]
                agg = ld.get("aggregateRating", {})
                if agg.get("ratingValue"):
                    sonuc["puan"] = float(agg["ratingValue"])
                    sonuc["yorum"] = int(agg.get("reviewCount", 0))
            except:
                pass
        if not sonuc["fiyat"]:
            m = re.search(r'"price"\s*:\s*"?([\d.,]+)"?', html)
            if m: sonuc["fiyat"] = fiyat_parse(m.group(1))
        if not sonuc["satici"]:
            m = re.search(r'"merchantName"\s*:\s*"([^"]+)"', html)
            if not m: m = re.search(r'"sellerName"\s*:\s*"([^"]+)"', html)
            if not m: m = re.search(r'class="[^"]*merchant[^"]*"[^>]*>\s*([^<]+)', html)
            if m: sonuc["satici"] = m.group(1).strip()
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
    dun_tarih = (simdi - timedelta(days=1)).strftime("%d.%m.%Y")

    basliklar = ["Ölçü", "Site", "Ürün Adı", "Satıcı", "Fiyat (TL)", "Puan", "Yorum Sayısı", "Son Güncelleme", "URL"]
    header_format = {
        "backgroundColor": {"red": 0.11, "green": 0.62, "blue": 0.46},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
    }

    def satir_yaz(ws, v):
        ws.append_row([
            v.get("olcu", ""),
            v["site"],
            v["ad"],
            v.get("satici") or "-",
            v["fiyat"] if v["fiyat"] else "Çekilemedi",
            v["puan"]  if v["puan"]  else "-",
            v["yorum"] if v["yorum"] else "-",
            f"{tarih} {saat}",
            v["url"]
        ])
        time.sleep(1.2)

    # ── Adım 1: Mevcut "Ürün Takip" sayfasını dünün tarihiyle arşivle ──
    try:
        ana_ws = sh.worksheet("Ürün Takip")
        mevcut_veriler = ana_ws.get_all_values()
        if len(mevcut_veriler) > 1:  # Başlık + en az 1 satır varsa
            try:
                arsiv = sh.worksheet(dun_tarih)
                arsiv.clear()
            except:
                arsiv = sh.add_worksheet(dun_tarih, rows=300, cols=10)

            arsiv.update(mevcut_veriler, "A1")
            arsiv.format("A1:I1", header_format)
            print(f"  Arşiv sayfası '{dun_tarih}' oluşturuldu.")
        else:
            print(f"  Ana sayfada veri yok, arşiv atlandı.")
    except Exception as e:
        print(f"  Arşiv hatası: {e}")

    # ── Adım 2: Ana sayfayı temizle ve yeni verileri yaz ──
    try:
        ana_ws = sh.worksheet("Ürün Takip")
        ana_ws.clear()
    except:
        ana_ws = sh.add_worksheet("Ürün Takip", rows=300, cols=10)

    ana_ws.append_row(basliklar)
    ana_ws.format("A1:I1", header_format)
    for v in veriler:
        satir_yaz(ana_ws, v)

    # ── Adım 3: Sayfa sırasını garanti et — Ürün Takip en başta, dünün arşivi 2. sırada ──
    try:
        ana_ws = sh.worksheet("Ürün Takip")
        ana_ws.update_index(0)
        try:
            dun_ws = sh.worksheet(dun_tarih)
            dun_ws.update_index(1)
        except:
            pass
        print(f"  Sayfa sırası güncellendi.")
    except Exception as e:
        print(f"  Sıralama hatası: {e}")

    print(f"  Ana sheet güncellendi: {len(veriler)} ürün")
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


									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
									
