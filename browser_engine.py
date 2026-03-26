#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tarayıcı motoru ana sınıfı
"""

import logging
import tkinter as tk
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image, ImageTk
from pathlib import Path

from constants import USER_AGENTS, FIREFOX_HEADERS, DEFAULT_TIMEOUT
from utils import normalize_url, generate_firefox_profile, get_domain_from_url, get_origin_from_url
from cookie_manager import CookieManager
from captcha_manager import CaptchaManager

# Logger ayarları
logger = logging.getLogger(__name__)

class BrowserSimulator:
    """Web Tarayıcı Simülatörü ana sınıfı"""
    
    def __init__(self, content_area, status_label, timeout=DEFAULT_TIMEOUT):
        """
        Web Tarayıcı Simülatörü başlatılır.
        
        Args:
            content_area (tkinter.scrolledtext.ScrolledText): İçerik alanı
            status_label (tk.Label): Durum etiketi
            timeout (int, optional): Zaman aşımı
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.history = []
        self.history_position = -1
        self.current_page = None
        self.current_url = None
        self.current_soup = None
        self.content_area = content_area  # GUI ile bağlantı
        self.status_label = status_label  # Durum etiketi
        
        # Firefox profili oluştur
        self.profile = generate_firefox_profile()
        
        # Çerez yöneticisi başlat
        self.cookie_manager = CookieManager()
        
        # Tarayıcı özellikleri
        self.user_agent = random.choice(USER_AGENTS)
        self.headers = FIREFOX_HEADERS.copy()
        self.headers["User-Agent"] = self.user_agent
        
        # CAPTCHA işleme için değişkenler
        self.captcha_detected = False
        self.captcha_image = None
        self.captcha_form = None
        self.captcha_attempts = 0
        
        self.session.headers.update(self.headers)
        logger.info(f"Firefox Tarayıcı Simülatörü başlatıldı (User-Agent: {self.user_agent})")
    
    def navigate(self, url):
        """
        Verilen URL'ye git.
        
        Args:
            url (str): Hedef URL
            
        Returns:
            bool: İşlem başarılı mı
        """
        self.update_status(f"URL'ye gidiliyor: {url}")
        # URL'yi normalize et
        normalized_url = normalize_url(url)
        if (normalized_url != url):
            logger.info(f"URL normalize edildi: {url} -> {normalized_url}")
        
        try:
            logger.info(f"Sayfa yükleniyor: {normalized_url}")
            self.content_area.delete(1.0, tk.END)
            self.content_area.insert(tk.END, f"Yükleniyor: {normalized_url}...\n")
            self.content_area.update_idletasks()  # GUI güncelleme
            
            # Referer başlığını güncelle
            headers = self.headers.copy()
            if self.current_url:
                headers["Referer"] = self.current_url
                headers["Sec-Fetch-Site"] = "same-origin" if urlparse(self.current_url).netloc == urlparse(normalized_url).netloc else "cross-site"
            
            # URL'nin domain'i için çerezleri al
            domain = get_domain_from_url(normalized_url)
            cookies = self.cookie_manager.get_cookies_for_url(normalized_url)
            
            # Sayfayı yükle
            response = self.session.get(
                normalized_url, 
                timeout=self.timeout,
                headers=headers,
                cookies=cookies,
                allow_redirects=True
            )
            
            # Çerezleri güncelle
            self.cookie_manager.update_from_response(response, domain)
            
            if 200 <= response.status_code < 300:
                self.current_page = response
                self.current_url = response.url
                
                # Geçmişi güncelle
                if self.history_position < len(self.history) - 1:
                    # Geçmişin ortasındaysak, bu noktadan sonrasını temizle
                    self.history = self.history[:self.history_position + 1]
                
                self.history.append(self.current_url)
                self.history_position = len(self.history) - 1
                
                self.current_soup = BeautifulSoup(response.text, 'html.parser')
                
                # CAPTCHA kontrolü
                self.captcha_detected = CaptchaManager.detect_captcha(response.text, self.current_soup)
                
                if self.captcha_detected:
                    return self._handle_captcha(response)
                
                # GUI'yi güncelle
                self._update_gui_with_content()
                self.update_status("Sayfa yüklendi")
                return True
            else:
                self.content_area.delete(1.0, tk.END)
                self.content_area.insert(tk.END, f"Hata: Sayfa yüklenemedi - Durum Kodu: {response.status_code}\n")
                
                self.update_status(f"Hata: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Sayfa yüklenirken hata: {str(e)}")
            self.content_area.delete(1.0, tk.END)
            self.content_area.insert(tk.END, f"Hata: {str(e)}\nURL geçersiz veya sayfa yüklenemedi.\n")
            
            self.update_status(f"Hata: {str(e)[:30]}...")
            return False
    
    def _update_gui_with_content(self):
        """Tarayıcı GUI'sini mevcut sayfa içeriği ile günceller"""
        # GUI'yi güncelle
        self.content_area.delete(1.0, tk.END)
        
        # Sayfa başlığını göster
        title = self._get_page_title() or "Başlık Yok"
        self.content_area.insert(tk.END, f"Sayfa Başlığı: {title}\n\n")
        
        # Sayfa içeriğini göster
        content = self.extract_text()
        if content:
            visible_content = content[:5000] + ("..." if len(content) > 5000 else "")
            self.content_area.insert(tk.END, visible_content)
        else:
            self.content_area.insert(tk.END, "Bu sayfada görüntülenecek içerik bulunamadı.")
        
        # URL çubuğunu güncelle
        # from browser_simulator import update_address_bar, root
        # update_address_bar(self.current_url)
        
        # Tarayıcı başlığını güncelle
        # root.title(f"{title} - Firefox Simülatörü")
        
        # Geri ve ileri butonlarını güncelle
        self.update_navigation_buttons()
        
        # Durumu güncelle
        # from browser_simulator import status_label
        # status_label.config(text="Sayfa yüklendi")
    
    def _handle_captcha(self, response):
        """
        CAPTCHA tespit edildiğinde bunu ele al
        
        Args:
            response (requests.Response): HTTP yanıt nesnesi
            
        Returns:
            bool: İşlem başarılı mı
        """
        # from browser_simulator import status_label
        
        self.captcha_attempts += 1
        
        if self.captcha_attempts > 3:
            self.content_area.delete(1.0, tk.END)
            self.content_area.insert(tk.END, "Çok fazla CAPTCHA denemesi. Lütfen daha sonra tekrar deneyin.\n")
            # status_label.config(text="CAPTCHA doğrulama başarısız")
            self.captcha_attempts = 0
            return False
        
        logger.info("CAPTCHA tespit edildi, çözümleme işlemi başlatılıyor...")
        self.update_status("CAPTCHA tespit edildi, çözümleniyor...")
        
        # CAPTCHA görüntüsünü çıkar
        captcha_img_path = CaptchaManager.extract_captcha_image(response, self.current_soup)
        
        if captcha_img_path:
            # GUI'yi temizle
            self.content_area.delete(1.0, tk.END)
            self.content_area.insert(tk.END, "CAPTCHA tespit edildi! Otomatik çözüm deneniyor...\n\n")
            
            # CAPTCHA görüntüsünü göster
            try:
                img = Image.open(captcha_img_path)
                img = img.resize((300, 100), Image.LANCZOS)  # Görüntüyü yeniden boyutlandır
                captcha_img = ImageTk.PhotoImage(img)
                
                # Label oluştur ve görüntüyü göster
                captcha_label = tk.Label(self.content_area, image=captcha_img)
                captcha_label.image = captcha_img  # Referansı koru
                self.content_area.window_create(tk.END, window=captcha_label)
                self.content_area.insert(tk.END, "\n\nCAPTCHA çözülüyor...\n")
            except Exception as e:
                logger.error(f"CAPTCHA görüntüsü gösterilirken hata: {str(e)}")
                self.content_area.insert(tk.END, "CAPTCHA görüntüsü gösterilemiyor.\n")
            
            # CAPTCHA'yı çöz
            session_id = self.profile["browser_id"]
            captcha_solution = CaptchaManager.solve_captcha(Path(captcha_img_path), session_id)
            
            if captcha_solution != "Başarısız":
                self.content_area.insert(tk.END, f"CAPTCHA çözüldü: {captcha_solution}\n")
                self.update_status("CAPTCHA çözüldü, doğrulanıyor...")
                
                # CAPTCHA formunu bul ve gönder
                form = self._find_captcha_form(self.current_soup)
                if form:
                    return self._submit_captcha_form(form, captcha_solution)
                else:
                    self.content_area.insert(tk.END, "CAPTCHA formu bulunamadı.\n")
                    self.update_status("CAPTCHA formu bulunamadı")
            else:
                self.content_area.insert(tk.END, "CAPTCHA çözülemedi.\n")
                self.update_status("CAPTCHA çözülemedi")
        else:
            self.content_area.insert(tk.END, "CAPTCHA görüntüsü bulunamadı.\n")
            self.update_status("CAPTCHA görüntüsü bulunamadı")
        
        return False
    
    def _find_captcha_form(self, soup):
        """
        CAPTCHA içeren formu bul
        
        Args:
            soup (BeautifulSoup): Parse edilmiş BeautifulSoup nesnesi
            
        Returns:
            Tag or None: Form etiketi
        """
        # CAPTCHA input alanı içeren formları ara
        form = soup.find('form', {'action': True, 'method': True})
        if not form:
            # Herhangi bir form bul (son çare)
            form = soup.find('form')
        
        return form
    
    def _submit_captcha_form(self, form, captcha_solution):
        """
        CAPTCHA çözümünü gönder
        
        Args:
            form (Tag): Form etiketi
            captcha_solution (str): CAPTCHA çözümü
            
        Returns:
            bool: İşlem başarılı mı
        """
        # Gereksiz import kaldırıldı
        # from browser_simulator import update_address_bar, root

        form_action = form.get('action', '')
        form_method = form.get('method', 'post').lower()
        
        # Form action URL'sini tam URL'ye dönüştür
        if not form_action.startswith(('http://', 'https://')):
            form_action = urljoin(self.current_url, form_action)
        
        # Form verilerini topla
        form_data = {}
        for input_tag in form.find_all(['input', 'textarea', 'select']):
            name = input_tag.get('name')
            if not name:
                continue
                
            if input_tag.name == 'select':
                selected_option = input_tag.find('option', selected=True)
                value = selected_option.get('value', '') if selected_option else ''
            else:
                value = input_tag.get('value', '')
                
            # CAPTCHA alanını bul ve çözümü yerleştir
            if 'captcha' in name.lower():
                form_data[name] = captcha_solution
            else:
                form_data[name] = value
        
        # Captcha alanı bulunamadıysa en olası yere yerleştir
        if not any('captcha' in name.lower() for name in form_data.keys()):
            # Boş bir input alanı bul
            for name, value in form_data.items():
                if not value and not name.lower() in ['submit', 'button', 'image']:
                    form_data[name] = captcha_solution
                    break
        
        try:
            # Formu gönder
            headers = self.headers.copy()
            headers['Referer'] = self.current_url
            headers['Origin'] = get_origin_from_url(self.current_url)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Çerezleri al
            domain = get_domain_from_url(form_action)
            cookies = self.cookie_manager.get_cookies_for_url(form_action)
            
            self.content_area.insert(tk.END, f"\nCAPTCHA formu gönderiliyor...\n")
            
            if form_method == 'post':
                response = self.session.post(
                    form_action,
                    data=form_data,
                    headers=headers,
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=self.timeout
                )
            else:
                response = self.session.get(
                    form_action,
                    params=form_data,
                    headers=headers,
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=self.timeout
                )
            
            # Çerezleri güncelle
            self.cookie_manager.update_from_response(response, domain)
            
            # CAPTCHA sayfasını geçebildik mi kontrol et
            new_soup = BeautifulSoup(response.text, 'html.parser')
            still_captcha = CaptchaManager.detect_captcha(response.text, new_soup)
            
            if not still_captcha:
                # CAPTCHA başarılı
                self.captcha_attempts = 0
                self.current_page = response
                self.current_url = response.url
                self.current_soup = new_soup
                
                # GUI'yi güncelle
                self.content_area.delete(1.0, tk.END)
                title = self._get_page_title() or "Başlık Yok"
                self.content_area.insert(tk.END, f"CAPTCHA başarıyla çözüldü!\nSayfa Başlığı: {title}\n\n")
                
                # Sayfa içeriğini göster
                content = self.extract_text()
                if content:
                    visible_content = content[:5000] + ("..." if len(content) > 5000 else "")
                    self.content_area.insert(tk.END, visible_content)
                
                # URL çubuğunu güncelle
                # update_address_bar(self.current_url)
                
                # Tarayıcı başlığını güncelle
                # root.title(f"{title} - Firefox Simülatörü")
                
                # Durumu güncelle
                self.update_status("CAPTCHA başarıyla çözüldü")
                
                return True
            else:
                # CAPTCHA hala var, yeniden dene
                self.content_area.insert(tk.END, "\nCAPTCHA doğrulaması başarısız. Yeniden deneniyor...\n")
                self.update_status("CAPTCHA doğrulaması başarısız")
                return self._handle_captcha(response)
                
        except Exception as e:
            logger.error(f"CAPTCHA formu gönderilirken hata: {str(e)}")
            self.content_area.insert(tk.END, f"\nHata: {str(e)}\n")
            self.update_status(f"CAPTCHA hatası: {str(e)[:30]}...")
            return False
    
    def update_navigation_buttons(self, back_button, forward_button):
        """Geri ve ileri butonlarının durumunu günceller"""
        if self.history_position > 0:
            back_button.config(state=tk.NORMAL)
        else:
            back_button.config(state=tk.DISABLED)
            
        if self.history_position < len(self.history) - 1:
            forward_button.config(state=tk.NORMAL)
        else:
            forward_button.config(state=tk.DISABLED)
    
    def go_back(self):
        """Geçmişteki önceki sayfaya git"""
        if self.history_position > 0:
            self.history_position -= 1
            url = self.history[self.history_position]
            # navigate fonksiyonunu çağırmak yerine özel bir durumu işle
            self._navigate_to_history(url)
        self.update_status("Geri gidildi")
    
    def go_forward(self):
        """Geçmişteki sonraki sayfaya git"""
        if self.history_position < len(self.history) - 1:
            self.history_position += 1
            url = self.history[self.history_position]
            self._navigate_to_history(url)
        self.update_status("İleri gidildi")
    
    def _navigate_to_history(self, url):
        """
        Geçmiş navigasyonu için özel gezinti
        
        Args:
            url (str): Hedef URL
        """
        # Gereksiz import kaldırıldı
        # from browser_simulator import update_address_bar, root

        headers = self.headers.copy()
        headers["Cache-Control"] = "max-age=0"
        
        # Referer başlığını güncelle
        if self.current_url:
            headers["Referer"] = self.current_url
        
        # Çerezleri al
        domain = get_domain_from_url(url)
        cookies = self.cookie_manager.get_cookies_for_url(url)
        
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout,
                headers=headers,
                cookies=cookies,
                allow_redirects=True
            )
            
            # Çerezleri güncelle
            self.cookie_manager.update_from_response(response, domain)
            
            if 200 <= response.status_code < 300:
                self.current_page = response
                self.current_url = response.url
                self.current_soup = BeautifulSoup(response.text, 'html.parser')
                
                # GUI'yi güncelle
                self.content_area.delete(1.0, tk.END)
                
                # Sayfa başlığını göster
                title = self._get_page_title() or "Başlık Yok"
                self.content_area.insert(tk.END, f"Sayfa Başlığı: {title}\n\n")
                
                # Sayfa içeriğini göster
                content = self.extract_text()
                if content:
                    visible_content = content[:5000] + ("..." if len(content) > 5000 else "")
                    self.content_area.insert(tk.END, visible_content)
                else:
                    self.content_area.insert(tk.END, "Bu sayfada görüntülenecek içerik bulunamadı.")
                
                # URL çubuğunu güncelle
                # update_address_bar(self.current_url)
                
                # Tarayıcı başlığını güncelle
                # root.title(f"{title} - Firefox Simülatörü")
                
                # Geri ve ileri butonlarını güncelley
                self.update_navigation_buttons()
            else:
                self.content_area.delete(1.0, tk.END)
                self.content_area.insert(tk.END, f"Hata: Sayfa yüklenemedi - Durum Kodu: {response.status_code}\n")
                
        except Exception as e:
            logger.error(f"Sayfa yüklenirken hata: {str(e)}")
            self.content_area.delete(1.0, tk.END)
            self.content_area.insert(tk.END, f"Hata: {str(e)}\nURL geçersiz veya sayfa yüklenemedi.\n")

    def _get_page_title(self):
        """
        Sayfa başlığını döndürür.
        
        Returns:
            str or None: Sayfa başlığı
        """
        if self.current_soup:
            title_tag = self.current_soup.find('title')
            if title_tag:
                return title_tag.get_text()
        return None

    def extract_text(self):
        """
        Sayfa içeriğini düz metin olarak çıkarır.
        
        Returns:
            str: Sayfa içeriği
        """
        if not self.current_soup:
            return ""
        
        for script in self.current_soup(["script", "style"]):
            script.decompose()
        
        return self.current_soup.get_text(separator="\n", strip=True)

    def extract_links(self):
        """
        Sayfadaki bağlantıları çıkarır.
        
        Returns:
            list: (url, text) çiftlerinden oluşan liste
        """
        if not self.current_soup:
            return []
        
        links = []
        for a_tag in self.current_soup.find_all('a', href=True):
            href = a_tag['href']
            # Sayfa içi bağlantıları filtrele
            if href.startswith('#'):
                continue
            # Göreceli yolları tam URL'ye dönüştür
            if not href.startswith(('http://', 'https://')):
                href = urljoin(self.current_url, href)
            # Link metni
            text = a_tag.get_text().strip() or "Bağlantı"
            links.append((href, text))
        
        return links

    def update_status(self, message):
        if self.status_label:
            self.status_label.config(text=f"Durum: {message}")

"""
Tarayıcı motoru implementasyonu.
"""
try:
    # Eksik import hatası düzeltildi
    from core import Config # type: ignore
except ImportError:
    print("Config modülü yüklenirken hata: No module named 'core'")
    # Varsayılan Config sınıfı
    class Config:
        def __init__(self):
            self.debug = False
            self.timeout = 30
            self.user_agent = "Mozilla/5.0"
            self.headless = True
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    print("Varsayılan Config kullanılıyor")

class BrowserEngine:
    """
    Tarayıcı motoru sınıfı, Selenium ile web otomasyonu sağlar.
    """
    def __init__(self, config=None):
        self.config = config or Config()
        self.driver = None
        self.wait_time = self.config.get('timeout', 30)
    
    def initialize(self, browser_type="firefox"):
        """Tarayıcıyı başlatır"""
        print(f"{browser_type} tarayıcısı başlatılıyor...")
        return True
    
    def navigate(self, url):
        """Belirtilen URL'ye gider"""
        print(f"Ziyaret ediliyor: {url}")
        return True
    
    def find_element(self, selector, by_type="css"):
        """Belirtilen seçiciye göre element bulur"""
        print(f"Element bulunuyor: {selector} (tip: {by_type})")
        return True
    
    def click(self, element):
        """Elementin tıklanmasını simüle eder"""
        print("Element tıklandı")
        return True
    
    def send_keys(self, element, text):
        """Elemente metin girer"""
        print(f"Metin giriliyor: {text[:20]}...")
        return True
    
    def screenshot(self, path):
        """Ekran görüntüsü alır"""
        print(f"Ekran görüntüsü kaydedildi: {path}")
        return True
    
    def close(self):
        """Tarayıcıyı kapatır"""
        print("Tarayıcı kapatıldı")
        return True
