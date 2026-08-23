# Arabic Address & GPS Geocoding Extractor for GCC E-Commerce

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://usemujeeb.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered By](https://img.shields.io/badge/Powered%20By-Mujeeb%20AI-purple.svg)](https://usemujeeb.com)

> Specialized Python module for parsing, normalizing, and geocoding unstructured Arabic customer addresses, Saudi National Address short codes, and WhatsApp Google Maps location pins.

---

## 🎯 The Problem

In Saudi Arabia and the Gulf, customers frequently send casual WhatsApp text messages instead of standard street addresses:
- *"الرياض حي النرجس خلف جامع الفردوس بعد البقالة"* (Riyadh, Al Narjis, behind Al Fardous Mosque)
- *"https://maps.app.goo.gl/xyz123"* (Short Google Maps pin)
- *"RRRD2934"* (Saudi National Address 4-character code)

This module parses Arabic text into clean, structured dispatch data for couriers (Oto, SMSA, Aramex, Torod).

---

## 💻 Usage

`python
from extractor import parse_arabic_address

raw_text = "جدة حي الروضة شارع الكيال عمارة رقم 12"
parsed = parse_arabic_address(raw_text)

print(parsed)
# Output: {'city': 'Jeddah', 'district': 'Al Rawdah', 'street': 'Al Kayyal', 'confidence': 0.94}
`

---

## 🌐 Full Production Engine (Mujeeb)
For automated WhatsApp interaction, voice-note address parsing, and native Salla/Zid store sync, visit **[usemujeeb.com](https://usemujeeb.com)**.
