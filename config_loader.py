#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Yapılandırma modülünü dışarıdan yüklemek için yardımcı işlevler
"""

import sys
import importlib.util
import logging
import re
import urllib.parse
from constants import DEFAULT_CONFIG

# Logger ayarları
logger = logging.getLogger(__name__)

# URL doğrulama için regex deseni
URL_PATTERN = re.compile(
    r'^(?:http|https)://'  # http:// veya https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
    r'(?::\d+)?'  # port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_url(url):
    """
    URL'in geçerli olup olmadığını kontrol eder
    
    Args:ig
        url (str): Kontrol edilecek URL
        
    Returns:
        bool: URL geçerliyse True, değilse False
    """
    if not url:
        return False
        
    try:
        # URL şemasını kontrol et
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme not in ('http', 'https'):
            return False
            
        # Regex ile doğrula
        return bool(URL_PATTERN.match(url))
    except Exception as e:
        logger.error(f"URL doğrulama hatası: {str(e)}")
        return False

def load_config_module():
    """
    Config modülünü dinamik olarak yükler, başarısız olursa varsayılanı döndürür
    
    Returns:
        object: Config sınıfı veya varsayılan config
    """
    try:
        # Önce sys.path'e eklenmiş mi kontrol et ve uygun ekleme yapılmamışsa ekle
        config_path = 'd:/x/webbrowser'
        if config_path not in sys.path:
            sys.path.append(config_path)
        
        # İlk olarak düzenli import ile dene
        try:
            try:
                from core.config import Config # type: ignore
            except ImportError as e:
                logger.error(f"core.config modülü bulunamadı: {str(e)}")
                raise
            logger.info("Config modülü başarıyla içe aktarıldı")
            return Config
        except ImportError:
            logger.warning("Düzenli import başarısız, dinamik yükleme deneniyor...")
        
        # Dinamik yükleme dene
        spec = importlib.util.find_spec('core.config', [config_path])
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info("Config modülü dinamik olarak başarıyla yüklendi")
            return module.Config
        else:
            logger.error("Config modülü bulunamadı")
            return None
    except Exception as e:
        logger.error(f"Config modülü yüklenirken hata: {str(e)}")
        return None

class DefaultConfig:
    """Varsayılan yapılandırma sınıfı"""
    def __init__(self):
        # Temel yapılandırma değerlerini ayarla
        for key, value in DEFAULT_CONFIG.items():
            setattr(self, key, value)
            
        # Tarayıcı simülatörü için gelişmiş varsayılan ayarlar
        self.browser = {
            # Tarayıcı görünüm ayarları
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
            "screen_resolution": "1920x1080",
            "timezone": "Europe/Istanbul",
            "language": "tr-TR",
            
            # Gizlilik ayarları
            "privacy": {
                "tracking_protection": True,
                "resist_fingerprinting": True,
                "clear_on_exit": True,
                "do_not_track": True,
                "block_third_party_cookies": True
            },
            
            # Performans ayarları
            "performance": {
                "max_cache_size_mb": 500,
                "cache_ttl_seconds": 3600,
                "resource_monitor_enabled": True,
                "memory_threshold_percent": 80
            },
            
            # Güvenlik ayarları
            "security": {
                "malicious_domain_blocking": True,
                "js_injection_detection": True,
                "phishing_protection": True,
                "auto_virus_scan": True
            },
            
            # Captcha çözüm ayarları
            "captcha": {
                "solver_priority": ["ocr", "api", "manual"],
                "api_key": "",
                "max_retry_count": 3
            },
            
            # Geliştirici araçları
            "developer_tools": {
                "enabled": False,
                "available_tools": ["element_inspector", "network_monitor", "console"]
            },
            
            # Oturum yönetimi
            "session": {
                "encrypted_storage": True,
                "encryption_key_path": "",
                "sync_enabled": False
            },
            
            # Hata yönetimi ayarları
            "error_handling": {
                "show_detailed_errors": True,
                "auto_recover": True,
                "max_retry_count": 3,
                "log_errors": True
            },
            
            # URL işleme ayarları
            "url_handling": {
                "validate_before_load": True,
                "default_protocol": "https",
                "auto_correct": True,
                "allowed_protocols": ["http", "https"],
                "fallback_url": "about:blank"
            },
            
            # UI hata yönetimi
            "ui": {
                "safe_widget_access": True,
                "error_notification_duration": 5000,  # ms
                "show_loading_indicator": True,
                "widget_check_before_access": True
            }
        }

    def validate_and_fix_url(self, url):
        """
        URL'i doğrular, geçerli değilse düzeltmeye çalışır
        
        Args:
            url (str): Doğrulanacak URL
            
        Returns:
            tuple: (geçerli_url, hata_mesajı) - URL geçerliyse hata_mesajı None olacaktır
        """
        if not url:
            return None, "URL boş olamaz"
            
        # Eğer scheme yoksa varsayılan ekle
        if not url.startswith(('http://', 'https://')):
            url = f"{self.browser['url_handling']['default_protocol']}://{url}"
            
        # Doğrula
        if validate_url(url):
            return url, None
        else:
            # Auto-correct etkinse basit düzeltmeler yap
            if self.browser['url_handling']['auto_correct']:
                # Yaygın yazım hatalarını düzelt
                url = url.replace(' ', '')
                url = re.sub(r'(?<!:)/{2,}', '/', url)  # Çift slash düzeltme
                
                # Tekrar kontrol et
                if validate_url(url):
                    return url, "URL düzeltildi"
                    
            return None, "URL geçersiz veya sayfa yüklenemedi."

def get_config(profile_name=None):
    """
    Config sınıfını yükler, başarısız olursa varsayılan yapılandırmayı döndürür
    
    Args:
        profile_name (str, optional): Yüklenecek profil adı. None ise varsayılan profil kullanılır.
    
    Returns:
        object: Config sınıfı örneği
    """
    Config = load_config_module()
    
    # Config yoksa veya yüklenemezse varsayılan yapılandırmayı kullan
    if Config is None:
        logger.warning("Varsayılan Config kullanılıyor")
        config = DefaultConfig()
    else:
        try:
            config = Config()
        except Exception as e:
            logger.error(f"Config örneği oluşturulurken hata: {str(e)}")
            logger.warning("Varsayılan Config kullanılıyor")
            config = DefaultConfig()
    
    # Özel profil yükle
    if profile_name:
        try:
            profile_path = f"d:/x/webbrowser/profiles/{profile_name}.py"
            spec = importlib.util.spec_from_file_location(f"profile_{profile_name}", profile_path)
            if spec:
                profile_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(profile_module)
                
                # Profil yapılandırmasını uygula
                if hasattr(profile_module, "apply_profile"):
                    logger.info(f"{profile_name} profili yükleniyor")
                    profile_module.apply_profile(config)
                else:
                    logger.warning(f"{profile_name} profilinde apply_profile fonksiyonu bulunamadı")
            else:
                logger.error(f"{profile_name} profili bulunamadı")
        except Exception as e:
            logger.error(f"Profil yüklenirken hata: {str(e)}")
    
    # Hata durumunda kullanıcıya daha açıklayıcı mesajlar göstermek için ek kontroller
    try:
        # Tkinter UI için ek güvenlik kontrolleri
        if hasattr(config, "browser") and config.browser.get("ui", {}).get("safe_widget_access", False):
            # UI widget'larını güvenli şekilde kullanmak için yardımcı metod ekle
            def safe_widget_access(widget, action, *args, **kwargs):
                """Güvenli widget erişimi sağlamak için yardımcı fonksiyon"""
                try:
                    if widget and widget.winfo_exists():
                        return getattr(widget, action)(*args, **kwargs) if action else widget
                    else:
                        logger.warning(f"Widget artık mevcut değil: {widget}")
                        return None
                except Exception as e:
                    logger.error(f"Widget erişim hatası: {str(e)}")
                    return None
                    
            config.safe_widget_access = safe_widget_access
    except Exception as e:
        logger.error(f"Güvenli widget erişimi ayarlanırken hata: {str(e)}")
    
    return config
