import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import tempfile
import os
import logging

# Logger yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CaptchaSolverDialog(tk.Toplevel):
    def __init__(self, parent, captcha_image_path):
        super().__init__(parent)
        self.title("CAPTCHA Doğrulama")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # CAPTCHA görselini yükle
        try:
            self.captcha_image = Image.open(captcha_image_path)
            self.tk_image = ImageTk.PhotoImage(self.captcha_image)
            
            lbl_image = ttk.Label(self, image=self.tk_image)
            lbl_image.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Hata", f"CAPTCHA görseli yüklenemedi: {str(e)}")
            self.destroy()
            return
        
        # Giriş alanı
        ttk.Label(self, text="CAPTCHA Metnini Girin:").pack(pady=5)
        self.entry = ttk.Entry(self)
        self.entry.pack(pady=5)
        self.entry.focus()
        
        # Butonlar
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Doğrula", command=self.on_verify).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="İptal", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Sonuç
        self.solution = None
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Geçici dosyayı izleme
        self.captcha_image_path = captcha_image_path
    
    def on_verify(self):
        self.solution = self.entry.get()
        self.cleanup()
        self.destroy()
    
    def cleanup(self):
        """Geçici dosyayı sil ve iz bırakma"""
        try:
            if os.path.exists(self.captcha_image_path):
                os.unlink(self.captcha_image_path)
        except Exception as e:
            logger.error(f"Geçici dosya silinemedi: {str(e)}")
    
    def show(self):
        self.wait_window()
        return self.solution

class BrowserSimulator:
    def __init__(self, root, driver):
        self.root = root
        self.driver = driver
        self.status = ttk.Label(root, text="Hazır")
        self.status.pack(pady=5)
    
    def solve_captcha(self):
        """CAPTCHA çözümü için manuel yöntem"""
        self.status.config(text="CAPTCHA tespit edildi, çözülüyor...")
        
        # 1. CAPTCHA görselini geçici dosyaya kaydet
        temp_dir = tempfile.gettempdir()
        captcha_file = os.path.join(temp_dir, f"captcha_{os.getpid()}.png")
        
        try:
            # Selenium ile CAPTCHA görselini al
            captcha_img = self.driver.find_element("xpath", "//img[contains(@src, 'captcha')]")
            captcha_img.screenshot(captcha_file)
            
            # 2. Kullanıcıya göster ve çözümü al
            dialog = CaptchaSolverDialog(self.root, captcha_file)
            solution = dialog.show()
            
            if solution:
                # 3. Çözümü forma uygula
                if self.submit_captcha_solution(solution):
                    self.status.config(text="CAPTCHA başarıyla çözüldü")
                    return True
                else:
                    self.status.config(text="CAPTCHA çözümü gönderilemedi")
            else:
                self.status.config(text="CAPTCHA çözümü iptal edildi")
                
        except Exception as e:
            logger.error(f"CAPTCHA çözme hatası: {str(e)}")
            self.status.config(text=f"CAPTCHA hatası: {str(e)}")
            try:
                if os.path.exists(captcha_file):
                    os.unlink(captcha_file)
            except:
                pass
        
        return False
    
    def submit_captcha_solution(self, solution):
        """CAPTCHA çözümünü forma gönder (iz bırakmadan)"""
        try:
            # Tarayıcı oturumunu kullanarak gönderim yap
            result = self.driver.execute_script("""
                var solution = arguments[0];
                var inputs = document.getElementsByTagName('input');
                for (var i = 0; i < inputs.length; i++) {
                    var input = inputs[i];
                    if (/captcha/i.test(input.name) || /verification/i.test(input.name)) {
                        input.value = solution;
                        return true;
                    }
                }
                return false;
            """, solution)
            
            if not result:
                logger.warning("CAPTCHA giriş alanı bulunamadı")
                return False
            
            # Formu JavaScript ile gönder (doğrudan selenium click kullanmadan)
            result = self.driver.execute_script("""
                var forms = document.getElementsByTagName('form');
                for (var i = 0; i < forms.length; i++) {
                    if (forms[i].querySelector('input[name*="captcha"]')) {
                        forms[i].submit();
                        return true;
                    }
                }
                return false;
            """)
            
            if not result:
                logger.warning("CAPTCHA formu bulunamadı")
                
            return result
        except Exception as e:
            logger.error(f"CAPTCHA gönderme hatası: {str(e)}")
            return False

# Örnek kullanım
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    
    # Selenium tarayıcısını burada başlatın ve aşağıdaki gibi kullanın:
    # browser_sim = BrowserSimulator(root, driver)
    # is_solved = browser_sim.solve_captcha()
