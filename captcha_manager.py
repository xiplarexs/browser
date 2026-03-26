#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CAPTCHA algılama ve çözme işlemleri için sınıf
"""

import logging
from pathlib import Path
import tempfile
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config_loader import get_config

# Config sınıfını yükle
Config = get_config()

# Logger ayarları
logger = logging.getLogger(__name__)

class CaptchaManager:
    """CAPTCHA yönetimi için yardımcı sınıf"""

    @staticmethod
    def solve_captcha(image_path: Path, session_id: Optional[str] = None) -> str:
        """
        CAPTCHA çözme işlemi
        
        Args:
            image_path (Path): CAPTCHA görüntü dosya yolu
            session_id (str, optional): Oturum kimliği
        
        Returns:
            str: Çözülen CAPTCHA metni
        """
        method = Config.CAPTCHA_SETTINGS['preferred_method']
        logger.info(f"CAPTCHA çözme yöntemi: {method}")
        
        if session_id:
            logger.info(f"Oturum ID'si kullanılıyor: {session_id}")
            # ...Oturum bilgilerini kullanarak işlem yap...
        
        if method == 'local_ai' and Config.CAPTCHA_SETTINGS['local_model']['enabled']:
            result = CaptchaManager._solve_with_local_model(image_path)
        elif method == 'external_api':
            result = CaptchaManager._solve_with_external_api(image_path)
        else:
            logger.warning("Geçersiz CAPTCHA çözme yöntemi")
            result = "Başarısız"
        
        CaptchaManager._log_statistics(image_path, result)
        return result
    
    @staticmethod
    def _solve_with_local_model(image_path: Path) -> str:
        """
        Yerel model ile CAPTCHA çözme
        
        Args:
            image_path (Path): CAPTCHA görüntü dosya yolu
        
        Returns:
            str: Çözülen CAPTCHA metni
        """
        model_path = Config.CAPTCHA_SETTINGS['local_model']['model_path']
        logger.info(f"Yerel model kullanılıyor: {model_path}")
        # ...Yerel model çözüm kodları...
        return "Yerel Çözüm"
    
    @staticmethod
    def _solve_with_external_api(image_path: Path) -> str:
        """
        Harici API ile CAPTCHA çözme
        
        Args:
            image_path (Path): CAPTCHA görüntü dosya yolu
        
        Returns:
            str: Çözülen CAPTCHA metni
        """
        logger.info("Harici CAPTCHA çözme API'si kullanılıyor")
        # ...Harici API çözüm kodları...
        return "API Çözüm"
    
    @staticmethod
    def _log_statistics(image_path: Path, result: str):
        """
        CAPTCHA çözme istatistiklerini kaydet
        
        Args:
            image_path (Path): CAPTCHA görüntü dosya yolu
            result (str): Çözüm sonucu
        """
        if Config.CAPTCHA_SETTINGS['statistics']['track']:
            stats_file = Config.CAPTCHA_SETTINGS['statistics']['log_file']
            logger.info(f"CAPTCHA istatistikleri kaydediliyor: {stats_file}")
            # ...İstatistik kaydetme kodları...
    
    @staticmethod
    def detect_captcha(html_content, soup=None):
        """
        HTML içeriğinde CAPTCHA olup olmadığını algılar
        
        Args:
            html_content (str): HTML içeriği
            soup (BeautifulSoup, optional): Parse edilmiş BeautifulSoup nesnesi
        
        Returns:
            bool: CAPTCHA var mı
        """
        if not soup:
            soup = BeautifulSoup(html_content, 'html.parser')
        
        # CAPTCHA algılama yöntemleri
        captcha_indicators = [
            # Meta etiketleri
            lambda s: any('captcha' in meta.get('name', '').lower() for meta in s.find_all('meta')),
            # Input alanları
            lambda s: bool(s.find('input', {'name': lambda x: x and 'captcha' in x.lower()})),
            # Captcha görüntüleri
            lambda s: bool(s.find('img', {'src': lambda x: x and 'captcha' in x.lower()})),
            # CAPTCHA yazıları
            lambda s: bool(s.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'p', 'div', 'span'] 
                         and tag.string and 'captcha' in tag.text.lower())),
            # Google reCAPTCHA
            lambda s: bool(s.find('div', {'class': 'g-recaptcha'})),
            # hCaptcha
            lambda s: bool(s.find('div', {'class': 'h-captcha'}))
        ]
        
        # Herhangi bir gösterge bulunduysa CAPTCHA var demektir
        return any(indicator(soup) for indicator in captcha_indicators)
    
    @staticmethod
    def extract_captcha_image(response, soup=None):
        """
        HTML yanıtından CAPTCHA görüntüsünü çıkartır ve kaydeder
        
        Args:
            response (requests.Response): HTTP yanıt nesnesi
            soup (BeautifulSoup, optional): Parse edilmiş BeautifulSoup nesnesi
        
        Returns:
            Path or None: CAPTCHA görüntü dosya yolu
        """
        if not soup:
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # CAPTCHA resim bulma yöntemleri
        captcha_img = None
        base_url = response.url
        
        # 1. Doğrudan 'captcha' adında img etiketi
        img_tag = soup.find('img', {'name': lambda x: x and 'captcha' in x.lower()})
        if not img_tag:
            # 2. src içinde 'captcha' içeren img etiketi
            img_tag = soup.find('img', {'src': lambda x: x and 'captcha' in x.lower()})
        
        if img_tag and img_tag.get('src'):
            img_url = img_tag['src']
            if not img_url.startswith(('http://', 'https://')):
                img_url = urljoin(base_url, img_url)
            
            try:
                # CAPTCHA görüntüsünü indir
                img_response = requests.get(img_url, stream=True, headers=response.request.headers)
                if img_response.status_code == 200:
                    # Geçici dosya oluştur ve görüntüyü kaydet
                    temp_dir = Path(tempfile.gettempdir())
                    captcha_img = temp_dir / f"captcha_{time.time()}.png"
                    with open(captcha_img, 'wb') as f:
                        f.write(img_response.content)
                    logger.info(f"CAPTCHA görüntüsü kaydedildi: {captcha_img}")
                    return captcha_img
            except Exception as e:
                logger.error(f"CAPTCHA görüntüsü çıkarılırken hata: {str(e)}")
        
        return None
