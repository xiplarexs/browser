import tkinter as tk
import logging
import requests
import base64

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# tkinterhtml ve twocaptcha modüllerinin varlığını kontrol et
try:
    from tkinterhtml import HtmlFrame
    TKINTERHTML_AVAILABLE = True
except ImportError:
    logger.warning("tkinterhtml modülü bulunamadı. Metin tabanlı görünüm kullanılacak.")
    TKINTERHTML_AVAILABLE = False

try:
    from twocaptcha import TwoCaptcha
    TWOCAPTCHA_AVAILABLE = True
except ImportError:
    logger.warning("twocaptcha modülü bulunamadı. CAPTCHA çözme devre dışı.")
    TWOCAPTCHA_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    logger.warning("selenium modülü bulunamadı. Browser simülasyonu devre dışı.")
    SELENIUM_AVAILABLE = False

class Browser:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Browser")
        
        # Ana pencere yapılandırması
        self.root.geometry("1024x768")
        
        # URL giriş çubuğu
        self.url_frame = tk.Frame(root)
        self.url_frame.pack(fill=tk.X)
        
        self.url_entry = tk.Entry(self.url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.go_button = tk.Button(self.url_frame, text="Git", command=self.go_to_url)
        self.go_button.pack(side=tk.RIGHT)
        
        # İçerik çerçevesi
        self.content_frame = tk.Frame(root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # HtmlFrame veya alternatif içerik alanı oluştur
        if TKINTERHTML_AVAILABLE:
            self.content_area = HtmlFrame(self.content_frame)
            self.content_area.pack(fill=tk.BOTH, expand=True)
        else:
            self.content_area = tk.Text(self.content_frame)
            self.content_area.pack(fill=tk.BOTH, expand=True)
        
        # Durum çubuğu
        self.status_bar = tk.Label(root, text="Hazır", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Selenium tarayıcı simülatörü
        if SELENIUM_AVAILABLE:
            self.browser_simulator = BrowserSimulator(self.content_area, TKINTERHTML_AVAILABLE)
        else:
            self.browser_simulator = None
        
        # CAPTCHA yöneticisi
        if TWOCAPTCHA_AVAILABLE:
            self.captcha_manager = CaptchaManager()
        else:
            self.captcha_manager = None
    
    def go_to_url(self):
        url = self.url_entry.get()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.navigate(url)
    
    def navigate(self, url):
        try:
            self.status_bar.config(text=f"Yükleniyor: {url}")
            self.root.update()
            
            # İsteği gönder
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            
            # Yanıtı kontrol et
            if 200 <= response.status_code < 300:
                if TKINTERHTML_AVAILABLE:
                    # İçeriği HtmlFrame'e gönder
                    self.content_area.set_content(response.text)
                else:
                    # İçeriği Text widget'ına gönder
                    self.content_area.delete(1.0, tk.END)
                    self.content_area.insert(tk.END, response.text)
                self.status_bar.config(text=f"Yüklendi: {url}")
            else:
                self.status_bar.config(text=f"Hata: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Navigasyon hatası: {str(e)}")
            self.status_bar.config(text=f"Hata: {str(e)}")
            
            # Selenium ile deneme
            if self.browser_simulator:
                self.browser_simulator.navigate(url)

class BrowserSimulator:
    def __init__(self, content_area, html_mode=True):
        if not SELENIUM_AVAILABLE:
            return
            
        # Selenium Firefox driver ayarları
        options = Options()
        options.headless = True  # GUI olmadan çalışır
        self.driver = webdriver.Firefox(options=options)
        self.content_area = content_area
        self.html_mode = html_mode
        
    def navigate(self, url):
        if not SELENIUM_AVAILABLE:
            return False
            
        try:
            self.driver.get(url)
            # Sayfa kaynağını al ve göster
            page_source = self.driver.page_source
            
            if self.html_mode:
                self.content_area.set_content(page_source)
            else:
                self.content_area.delete(1.0, tk.END)
                self.content_area.insert(tk.END, page_source)
            return True
        except Exception as e:
            logger.error(f"Hata: {str(e)}")
            return False

class CaptchaManager:
    def __init__(self):
        if not TWOCAPTCHA_AVAILABLE:
            return
        self.api_key = "2CAPTCHA_API_KEY"  # Gerçek API anahtarınız
    
    def solve_with_2captcha(self, image_path):
        if not TWOCAPTCHA_AVAILABLE:
            return None
            
        try:
            # CAPTCHA görselini base64'e çevir
            with open(image_path, 'rb') as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 2captcha API'sine gönder
            solver = TwoCaptcha(self.api_key)
            result = solver.normal(image_base64)
            return result.get('code')
            
        except Exception as e:
            logger.error(f"2Captcha hatası: {str(e)}")
            return None

# Uygulamayı başlat
if __name__ == "__main__":
    root = tk.Tk()
    app = Browser(root)
    root.mainloop()
