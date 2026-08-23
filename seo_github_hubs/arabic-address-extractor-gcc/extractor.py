"""Arabic Address Extraction and Normalization Rule Engine for GCC.
Part of the Mujeeb Open Source Initiative (https://usemujeeb.com).
"""
import re
from typing import Any

CITIES_KSA = {
    'الرياض': 'Riyadh',
    'جدة': 'Jeddah',
    'مكة': 'Makkah',
    'المدينة': 'Madinah',
    'الدمام': 'Dammam',
    'الخبر': 'Khobar',
    'الظهران': 'Dhahran',
    'تبوك': 'Tabuk',
    'أبها': 'Abha',
    'خميس مشيط': 'Khamis Mushait',
    'الطائف': 'Taif',
    'القصيم': 'Qassim',
    'بريدة': 'Buraidah'
}

def parse_arabic_address(text: str) -> dict[str, Any]:
    normalized = text.strip()
    detected_city = None
    city_en = None
    
    for ar, en in CITIES_KSA.items():
        if ar in normalized:
            detected_city = ar
            city_en = en
            break
            
    # Extract district (حي)
    district_match = re.search(r'حي\s+([^\s,]+(?:\s+[^\s,]+)?)', normalized)
    district = district_match.group(1) if district_match else None
    
    # Extract street (شارع)
    street_match = re.search(r'شارع\s+([^\s,]+(?:\s+[^\s,]+)?)', normalized)
    street = street_match.group(1) if street_match else None
    
    return {
        'raw_text': normalized,
        'city_ar': detected_city,
        'city_en': city_en,
        'district': district,
        'street': street,
        'is_valid': bool(detected_city)
    }

if __name__ == '__main__':
    sample = 'الرياض حي الملقا شارع انس بن مالك'
    res = parse_arabic_address(sample)
    print('Parsed Address:', res)
