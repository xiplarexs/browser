import tkinter as tk
from tkinter import ttk, messagebox
import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from threading import Thread
import urllib.request
from urllib.parse import urlparse
import re
import time
import os
from PIL import Image, ImageTk
import io
import base64

class BrowserSimulator:
    def __init__(self, root):
        self.root = root
        self.setup_logging()
        self.setup_ui()
        self.initialize_browser()
        self.history = []
        self.history_index = -1
        self.current_url = ""
        
    def setup_logging(self):
        """Hata kaydı için logging ayarları"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='browser_errors.log'
        )
        
    def setup_ui(self):
        """Kullanıcı arayüzünü oluştur"""
        self.root.title("Gelişmiş Tarayıcı Simülatörü")
        self.root.geometry("1200x800")
        
        # Ana çerçeve
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Araç çubuğu
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X)
        
        # Gezinme butonları
        self.back_btn = ttk.Button(self.toolbar, text="←", command=self.go_back, width=3)
        self.back_btn.pack(side=tk.LEFT)
        
        self.forward_btn = ttk.Button(self.toolbar, text="→", command=self.go_forward, width=3)
        self.forward_btn.pack(side=tk.LEFT)
        
        self.refresh_btn = ttk.Button(self.toolbar, text="↻", command=self.refresh, width=3)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # Adres çubuğu
        self.url_entry = ttk.Entry(self.toolbar)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.url_entry.bind("<Return>", lambda e: self.navigate())
        
        self.go_btn = ttk.Button(self.toolbar, text="Git", command=self.navigate)
        self.go_btn.pack(side=tk.LEFT)
        
        # İçerik alanı
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(
            self.content_frame, 
            wrap=tk.WORD, 
            font=('Arial', 12),
            padx=10,
            pady=10
        )
        self.scrollbar = ttk.Scrollbar(
            self.content_frame, 
            command=self.content_text.yview
        )
        self.content_text.config(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # Durum çubuğu
        self.status_bar = ttk.Label(
            self.root, 
            text="Hazır", 
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def initialize_browser(self):
        """Tarayıcıyı başlat"""
        try:
            options = Options()
            options.set_preference("permissions.default.image", 1)
            options.set_preference("media.autoplay.default", 0)
            
            self.driver = webdriver.Firefox(options=options)
            self.update_status("Tarayıcı başlatıldı")
        except WebDriverException as e:
            self.show_error("Tarayıcı başlatılamadı", str(e))
            self.root.destroy()
            
    def navigate(self):
        """URL'ye git"""
        url = self.url_entry.get().strip()
        if not url:
            self.show_warning("Lütfen bir URL girin")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        Thread(target=self._load_page, args=(url,), daemon=True).start()
    
    def _load_page(self, url):
        """Sayfayı thread içinde yükle"""
        try:
            self.update_status(f"{url} yükleniyor...")
            
            self.driver.get(url)
            current_url = self.driver.current_url
            
            # Geçmişi güncelle
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index+1]
            self.history.append(current_url)
            self.history_index = len(self.history) - 1
            
            # Sayfa içeriğini al
            page_source = self.driver.page_source
            text_content = self._extract_text(page_source)
            
            # GUI güncellemeleri
            self.root.after(0, self._update_ui, current_url, text_content)
            self.root.after(0, self.update_status, f"{current_url} yüklendi")
            
        except WebDriverException as e:
            self.root.after(0, self.show_error, "Sayfa yüklenemedi", str(e))
            self.root.after(0, self.update_status, "Hata oluştu")
        except Exception as e:
            self.root.after(0, self.show_error, "Beklenmeyen hata", str(e))
            self.root.after(0, self.update_status, "Kritik hata")
            
    def _extract_text(self, html):
        """HTML'den metin içeriğini çıkar"""
        try:
            # Basit bir regex ile HTML etiketlerini temizle
            clean_text = re.sub('<[^<]+?>', '', html)
            clean_text = re.sub('\s+', ' ', clean_text)
            return clean_text[:10000] + ("..." if len(clean_text) > 10000 else "")
        except Exception as e:
            self.show_error("İçerik işlenemedi", str(e))
            return "İçerik görüntülenemedi"
    
    def _update_ui(self, url, content):
        """Arayüzü güncelle"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
        self.content_text.config(state=tk.DISABLED)
        
        self.current_url = url
        
    def go_back(self):
        """Geri git"""
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            Thread(target=self._load_page, args=(url,), daemon=True).start()
    
    def go_forward(self):
        """İleri git"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            Thread(target=self._load_page, args=(url,), daemon=True).start()
    
    def refresh(self):
        """Sayfayı yenile"""
        if self.current_url:
            Thread(target=self._load_page, args=(self.current_url,), daemon=True).start()
    
    def update_status(self, message):
        """Durum çubuğunu güncelle"""
        self.status_bar.config(text=message)
        
    def show_error(self, title, message):
        """Hata mesajı göster"""
        logging.error(f"{title}: {message}")
        messagebox.showerror(title, message)
        
    def show_warning(self, message):
        """Uyarı mesajı göster"""
        logging.warning(message)
        messagebox.showwarning("Uyarı", message)
    
    def __del__(self):
        """Nesne yok edilirken tarayıcıyı kapat"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

def main():
    root = tk.Tk()
    try:
        app = BrowserSimulator(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Uygulama çöktü: {str(e)}")
        messagebox.showerror("Kritik Hata", f"Uygulama kapatıldı:\n{str(e)}")
        root.destroy()

if __name__ == "__main__":
    main()