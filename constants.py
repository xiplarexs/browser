#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tarayıcı Simülatörü için sabit değerler ve konfigürasyon sabitleri
"""

# Kullanıcı ajanları listesi - Firefox'u öne çıkardık
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
]

# Firefox özel başlıkları
FIREFOX_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr,tr-TR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

# Varsayılan yapılandırma ayarları
DEFAULT_CONFIG = {
    'CAPTCHA_SETTINGS': {
        'preferred_method': 'local_ai',
        'local_model': {
            'enabled': True,
            'model_path': 'd:/x/models/captcha_model.h5'
        },
        'external_api': {
            'url': 'https://api.captchaservice.com/solve',
            'key': 'YOUR_API_KEY_HERE'
        },
        'statistics': {
            'track': True,
            'log_file': 'd:/x/logs/captcha_stats.json'
        }
    }
}

# Uygulama varsayılanları
DEFAULT_TIMEOUT = 15
DEFAULT_START_URL = "https://www.google.com"
