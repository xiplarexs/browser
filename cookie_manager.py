#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Çerez yönetimi için yardımcı sınıf
"""

import os
import json
import logging
import time
from urllib.parse import urlparse

# Logger ayarları
logger = logging.getLogger(__name__)

class CookieManager:
    """Çerez yönetimi için yardımcı sınıf"""
    
    def __init__(self, cookie_file=None):
        """
        CookieManager örneği başlatır
        
        Args:
            cookie_file (str, optional): Çerez dosya yolu
        """
        self.cookie_file = cookie_file or os.path.join(os.path.expanduser("~"), ".browser_simulator_cookies.json")
        self.cookies = self._load_cookies()
    
    def _load_cookies(self):
        """
        Disk'ten çerezleri yükler
        
        Returns:
            dict: Çerezler sözlüğü
        """
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Çerezler yüklenirken hata: {str(e)}")
        return {}
    
    def save_cookies(self):
        """Çerezleri diske kaydeder"""
        try:
            with open(self.cookie_file, 'w') as f:
                json.dump(self.cookies, f)
        except Exception as e:
            logger.error(f"Çerezler kaydedilirken hata: {str(e)}")
    
    def update_from_response(self, response, domain):
        """
        Yanıttan çerezleri günceller
        
        Args:
            response (requests.Response): HTTP yanıt nesnesi
            domain (str): Domain adı
        """
        if domain not in self.cookies:
            self.cookies[domain] = {}
        
        # RequestsCookieJar içindeki çerezleri işle
        for name, cookie in response.cookies.items():
            try:
                # Çerez bir nesne ise (RequestsCookieJar.morsel)
                if hasattr(cookie, 'value'):
                    expires = cookie.expires if hasattr(cookie, 'expires') else None
                    cookie_domain = cookie.domain if hasattr(cookie, 'domain') else None
                    cookie_path = cookie.path if hasattr(cookie, 'path') else '/'
                    cookie_secure = cookie.secure if hasattr(cookie, 'secure') else False
                    http_only = cookie.has_nonstandard_attr("httponly") if hasattr(cookie, 'has_nonstandard_attr') else False
                    
                    self.cookies[domain][name] = {
                        "value": cookie.value,
                        "expires": expires,
                        "domain": cookie_domain or domain,
                        "path": cookie_path,
                        "secure": cookie_secure,
                        "httponly": http_only,
                        "last_accessed": int(time.time()),
                    }
                # Çerez doğrudan bir değer ise (string)
                else:
                    self.cookies[domain][name] = {
                        "value": str(cookie),  # Cookie'yi string olarak kabul et
                        "expires": None,       # Oturum çerezi olarak kabul et
                        "domain": domain,
                        "path": "/",
                        "secure": False,
                        "httponly": False,
                        "last_accessed": int(time.time()),
                    }
            except Exception as e:
                logger.error(f"Çerez işlenirken hata: {name}={cookie}, hata: {str(e)}")
                # Hata durumunda basitleştirilmiş bir çerez bilgisi kaydet
                self.cookies[domain][name] = {
                    "value": str(cookie),
                    "expires": None,
                    "domain": domain,
                    "path": "/",
                    "secure": False,
                    "httponly": False,
                    "last_accessed": int(time.time()),
                }
        
        # Süreleri dolmuş çerezleri temizle
        current_time = int(time.time())
        for domain in list(self.cookies.keys()):
            for name in list(self.cookies[domain].keys()):
                expires = self.cookies[domain][name].get("expires")
                if expires and expires < current_time:
                    del self.cookies[domain][name]
            if not self.cookies[domain]:
                del self.cookies[domain]
        
        self.save_cookies()
    
    def get_cookies_for_url(self, url):
        """
        URL için uygun çerezleri döndürür
        
        Args:
            url (str): URL
            
        Returns:
            dict: Çerezler sözlüğü
        """
        domain = urlparse(url).netloc
        cookies_dict = {}
        
        # Tam domain eşleşmesi
        if domain in self.cookies:
            for name, cookie_data in self.cookies[domain].items():
                cookies_dict[name] = cookie_data["value"]
        
        # Alt alan adı eşleşmesi (.example.com)
        domain_parts = domain.split('.')
        for i in range(1, len(domain_parts)):
            parent_domain = '.'.join(domain_parts[i:])
            parent_domain_with_dot = f".{parent_domain}"
            if parent_domain_with_dot in self.cookies:
                for name, cookie_data in self.cookies[parent_domain_with_dot].items():
                    cookies_dict[name] = cookie_data["value"]
        
        return cookies_dict
