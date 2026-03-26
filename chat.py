import sys
import webbrowser
import random
import string
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QPushButton

class ChatBrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Ana pencere ayarları
        self.setWindowTitle('Sohbet ve Tarayıcı Simülasyonu')
        self.setGeometry(300, 300, 600, 400)
        
        # Ana widget ve layout oluşturma
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Sohbet alanı
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        main_layout.addWidget(self.chat_area)
        
        # Metin giriş alanı ve gönder butonu için horizontal layout
        input_layout = QHBoxLayout()
        
        self.text_input = QLineEdit()
        self.text_input.returnPressed.connect(self.on_send)
        input_layout.addWidget(self.text_input)
        
        send_button = QPushButton('Gönder')
        send_button.clicked.connect(self.on_send)
        input_layout.addWidget(send_button)
        
        main_layout.addLayout(input_layout)
        
        self.show()
    
    def on_send(self):
        user_input = self.text_input.text().strip()
        if not user_input:
            return
            
        # Kullanıcı mesajını ekrana yaz
        self.chat_area.append(f"Siz: {user_input}")
        
        # URL kontrolü
        if user_input.startswith("http://") or user_input.startswith("https://"):
            self.handle_url(user_input)
        else:
            self.handle_chat(user_input)
            
        # Metin kutusunu temizle
        self.text_input.clear()
    
    def handle_url(self, url):
        # Rastgele çerez oluştur
        random_cookie = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        
        # URL bilgisini ekrana yaz
        self.chat_area.append(f"URL algılandı: {url} | User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) | Cookies: session_id={random_cookie}")
        
        # URL'yi varsayılan tarayıcıda aç
        webbrowser.open(url)
    
    def handle_chat(self, message):
        # Basit sohbet yanıtları
        message = message.lower()
        response = ""
        
        if "merhaba" in message:
            response = "Selam! Nasılsın?"
        elif "nasılsın" in message:
            response = "İyiyim, teşekkürler!"
        elif "ne yapıyorsun" in message:
            response = "Seninle sohbet ediyorum!"
        else:
            response = "Hmm, bunu anlamadım, başka ne sorabilirsin?"
        
        # AI yanıtını ekrana yaz
        self.chat_area.append(f"AI: {response}")

def main():
    app = QApplication(sys.argv)
    ex = ChatBrowserApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
