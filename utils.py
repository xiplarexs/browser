#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Yardımcı fonksiyonlar ve araçlar
"""

import uuid
import random
import time
import platform
from urllib.parse import urlparse
from constants import DEFAULT_START_URL

def normalize_url(url):
    """
    URL'yi düzenler ve geçerli bir URL formatına getirmeye çalışır
    
    Args:
        url (str): Düzenlenecek URL
    
    Returns:
        str: Normalize edilmiş URL
    """
    if not url:
        return DEFAULT_START_URL  # Varsayılan URL
    
    # URL şeması kontrolü
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    
    return url

def generate_firefox_profile():
    """
    Firefox profili için benzersiz kimlikler oluşturur
    
    Returns:
        dict: Firefox profil bilgileri
    """
    profile = {
        "machine_id": uuid.uuid4().hex,
        "browser_id": uuid.uuid4().hex,
        "install_date": int(time.time() - random.randint(7776000, 31536000)),  # 90-365 gün önce
        "platform": platform.system(),
        "firefox_version": "115.0",
        "language": "tr-TR,tr;en-US;q=0.7,en;q=0.3",
        "do_not_track": "1",
        "color_depth": 24,
        "timezone": "Europe/Istanbul",
        "cookie_enabled": True,
    }
    return profile

def get_domain_from_url(url):
    """URL'den domain adını çıkarır"""
    return urlparse(url).netloc

def get_origin_from_url(url):
    """
    URL'den origin bilgisini döndürür (scheme + domain)
    
    Args:
        url (str): URL
    
    Returns:
        str: Origin bilgisi (örn: https://example.com)
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
