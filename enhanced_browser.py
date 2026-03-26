import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from PIL import Image, ImageTk
import io
import base64
import tempfile
import os
import threading
import time

class FirefoxBrowserSimulator:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.setup_firefox()
        self.media_viewer = MediaViewer(root)
        
    def setup_ui(self):
        """Firefox benzeri arayüz oluştur"""
        self.root.title("Firefox Simülatörü")
        self.root.geometry("1200x800")
        
        # Firefox benzeri araç çubuğu
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Gezinme butonları
        ttk.Button(toolbar, text="←", command=self.go_back, width=3).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="→", command=self.go_forward, width=3).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="↻", command=self.refresh, width=3).pack(side=tk.LEFT)
        
        # Adres çubuğu
        self.url_entry = ttk.Entry(toolbar)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.url_entry.bind("<Return>", lambda e: self.navigate())
        
        ttk.Button(toolbar, text="Git", command=self.navigate).pack(side=tk.LEFT)
        
        # Medya butonları
        ttk.Button(toolbar, text="🖼️", command=self.show_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="▶️", command=self.show_videos).pack(side=tk.LEFT)
        
        # İçerik alanı
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Durum çubuğu
        self.status_bar = ttk.Label(self.root, text="Hazır", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_firefox(self):
        """Firefox tarayıcı örneği oluştur"""
        try:
            firefox_options = Options()
            
            # Firefox özelleştirmeleri
            firefox_options.set_preference("browser.startup.homepage", "about:blank")
            firefox_options.set_preference("browser.toolbars.bookmarks.visibility", "never")
            firefox_options.set_preference("media.autoplay.default", 0)
            
            # Gerçek Firefox kullanıcı ayarları
            firefox_options.profile = webdriver.FirefoxProfile()
            firefox_options.profile.set_preference("permissions.default.image", 1)
            firefox_options.profile.set_preference("dom.webdriver.enabled", False)
            firefox_options.profile.set_preference("useAutomationExtension", False)
            
            # Headless mod isteğe bağlı
            # firefox_options.add_argument("--headless")
            
            self.driver = webdriver.Firefox(options=firefox_options)
            self.history = []
            self.history_index = -1
            
            # Tarayıcı penceresini yönet
            self.driver.minimize_window()
            self.update_status("Firefox başlatıldı")
            
        except Exception as e:
            self.show_error("Firefox başlatılamadı", str(e))
            self.root.destroy()
    
    def navigate(self):
        """URL'ye git"""
        url = self.url_entry.get().strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        threading.Thread(target=self._load_page, args=(url,), daemon=True).start()
    
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
            
            # GUI güncellemeleri ana thread'de
            self.root.after(0, self.url_entry.delete, 0, tk.END)
            self.root.after(0, self.url_entry.insert, 0, current_url)
            self.root.after(0, self.update_status, f"{current_url} yüklendi")
            
        except Exception as e:
            self.root.after(0, self.show_error, "Sayfa yüklenemedi", str(e))
            self.root.after(0, self.update_status, "Hata oluştu")
    
    def go_back(self):
        """Geri git"""
        if self.history_index > 0:
            self.history_index -= 1
            self.driver.get(self.history[self.history_index])
            self.update_url_entry()
    
    def go_forward(self):
        """İleri git"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.driver.get(self.history[self.history_index])
            self.update_url_entry()
    
    def refresh(self):
        """Sayfayı yenile"""
        self.driver.refresh()
        self.update_status("Sayfa yenilendi")
    
    def update_url_entry(self):
        """URL çubuğunu güncelle"""
        current_url = self.driver.current_url
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, current_url)
        self.update_status(f"{current_url} yüklendi")
    
    def show_images(self):
        """Sayfadaki resimleri göster"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, 'img')
            for img in images:
                src = img.get_attribute('src')
                if src:
                    # Base64 verisi mi kontrol et
                    if src.startswith('data:image'):
                        img_data = base64.b64decode(src.split(',')[1])
                        self.media_viewer.show_image(img_data, src)
                    else:
                        # Resmi indir ve göster
                        threading.Thread(
                            target=self._download_and_show_image,
                            args=(src,),
                            daemon=True
                        ).start()
                        
        except Exception as e:
            self.show_error("Resimler yüklenemedi", str(e))
    
    def _download_and_show_image(self, src):
        """Resmi indir ve göster"""
        try:
            self.update_status(f"Resim yükleniyor: {src}")
            
            # Resmi indir
            img_data = self.driver.execute_async_script("""
                var url = arguments[0];
                var callback = arguments[1];
                fetch(url)
                    .then(res => res.blob())
                    .then(blob => {
                        var reader = new FileReader();
                        reader.onloadend = () => callback(reader.result);
                        reader.readAsDataURL(blob);
                    });
            """, src)
            
            img_data = base64.b64decode(img_data.split(',')[1])
            
            # Ana thread'de göster
            self.root.after(0, self.media_viewer.show_image, img_data, src)
            self.root.after(0, self.update_status, f"Resim gösteriliyor: {src}")
            
        except Exception as e:
            self.root.after(0, self.show_error, "Resim indirilemedi", str(e))
    
    def show_videos(self):
        """Sayfadaki videoları göster"""
        try:
            videos = self.driver.find_elements(By.TAG_NAME, 'video')
            for video in videos:
                src = video.get_attribute('src')
                if src:
                    self.media_viewer.play_video(src)
            
            # YouTube/Vimeo iframe'leri
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                src = iframe.get_attribute('src')
                if src and any(domain in src for domain in ['youtube.com', 'vimeo.com']):
                    self.media_viewer.play_video(src)
                    
            self.update_status(f"{len(videos)} video bulundu")
            
        except Exception as e:
            self.show_error("Videolar yüklenemedi", str(e))
    
    def update_status(self, message):
        """Durum çubuğunu güncelle"""
        self.status_bar.config(text=message)
    
    def show_error(self, title, message):
        """Hata mesajı göster"""
        messagebox.showerror(title, message)
        self.update_status(f"Hata: {title}")
    
    def __del__(self):
        """Nesne yok edilirken tarayıcıyı kapat"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

class MediaViewer:
    def __init__(self, root):
        self.root = root
        self.media_windows = []
    
    def show_image(self, image_data, image_url):
        """Resim görüntüleme penceresi aç"""
        try:
            window = tk.Toplevel(self.root)
            window.title(f"Resim - {os.path.basename(image_url)}")
            window.geometry("800x600")
            
            # Resmi yükle
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((780, 580))
            photo = ImageTk.PhotoImage(img)
            
            # Görüntüle
            label = tk.Label(window, image=photo)
            label.image = photo
            label.pack(fill=tk.BOTH, expand=True)
            
            # Bilgi paneli
            info_frame = ttk.Frame(window)
            info_frame.pack(fill=tk.X)
            
            ttk.Label(info_frame, text=f"Kaynak: {image_url}").pack(side=tk.LEFT)
            ttk.Label(info_frame, text=f"Boyut: {img.size[0]}x{img.size[1]}").pack(side=tk.RIGHT)
            
            # Pencereyi kaydet ve temizlik fonksiyonu ekle
            self.media_windows.append(window)
            window.protocol("WM_DELETE_WINDOW", lambda: self._close_window(window))
            
        except Exception as e:
            messagebox.showerror("Resim Hatası", str(e))
    
    def play_video(self, video_url):
        """Video oynatıcı penceresi aç"""
        try:
            window = tk.Toplevel(self.root)
            window.title(f"Video - {os.path.basename(video_url)}")
            window.geometry("854x480")
            
            # Video bilgisi
            ttk.Label(
                window, 
                text=f"Video URL: {video_url}\n\n(Bu simülatörde video oynatma desteği kısıtlıdır)",
                font=('Arial', 12), 
                justify=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)
            
            # Gerçek uygulamada buraya VLC/MPV entegrasyonu eklenir
            ttk.Button(
                window, 
                text="Harici Oynatıcıda Aç", 
                command=lambda: self._open_in_external_player(video_url)
            ).pack(pady=10)
            
            # Pencereyi kaydet
            self.media_windows.append(window)
            window.protocol("WM_DELETE_WINDOW", lambda: self._close_window(window))
            
        except Exception as e:
            messagebox.showerror("Video Hatası", str(e))
    
    def _open_in_external_player(self, url):
        """Videoyu harici oynatıcıda açar (temel örnek)"""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Hata", f"Harici oynatıcı açılamadı: {str(e)}")
    
    def _close_window(self, window):
        """Medya penceresini kapat ve listeden çıkar"""
        if window in self.media_windows:
            self.media_windows.remove(window)
        window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        browser = FirefoxBrowserSimulator(root)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı:\n{str(e)}")
        root.destroy()