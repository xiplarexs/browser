import re
import sys
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

def is_valid_url(url):
    """URL formatını kontrol eder."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def suggest_url(url):
    """Eksik şema (http/https) için öneri yapar."""
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url

def simulate_browser(start_url, click_count=3):
    """Tarayıcı simülasyonu yapar."""
    print(f"Kaç otomatik tıklama yapılsın? (varsayılan: 3): {click_count}")
    print(f"Başlangıç URL'si: {start_url}")
    
    # URL kontrolü
    if not is_valid_url(start_url):
        suggested_url = suggest_url(start_url)
        print(f"Hata: Invalid URL '{start_url}': No scheme supplied. Perhaps you meant {suggested_url}?")
        if input(f"'{suggested_url}' adresine gitmek ister misiniz? (e/h): ").lower() == 'e':
            start_url = suggested_url
        else:
            print("Başlangıç sayfası yüklenemedi, simülasyon durduruluyor.")
            return False
    
    # Tarayıcı yapılandırması
    options = Options()
    options.add_argument("--headless")  # Başsız mod (opsiyonel)
    
    try:
        # Tarayıcıyı başlat
        driver = webdriver.Chrome(options=options)
        driver.get(start_url)
        print(f"Sayfa yüklendi: {start_url}")
        
        # İsteğe bağlı gezinme simülasyonu
        for i in range(click_count):
            # Sayfada biraz bekle
            time.sleep(2)
            print(f"Simülasyon devam ediyor... ({i+1}/{click_count})")
            # Burada gerçek tıklama işlemleri eklenebilir
        
        # Tarayıcıyı kapat
        driver.quit()
        print("Tarayıcı oturumu kapatıldı")
        return True
        
    except WebDriverException as e:
        print(f"Tarayıcı hatası: {e}")
        print("Başlangıç sayfası yüklenemedi, simülasyon durduruluyor.")
        return False
    finally:
        print("Tarayıcı oturumu kapatıldı")

if __name__ == "__main__":
    # Komut satırı parametrelerini işle
    click_count = 3  # varsayılan değer
    
    # Kullanıcıdan URL al
    start_url = input("Ziyaret etmek istediğiniz web sitesinin URL'sini girin (örn. https://www.google.com): ")
    
    # Tıklama sayısını sor
    try:
        click_input = input("Kaç otomatik tıklama yapılsın? (varsayılan: 3): ")
        if click_input.strip():
            click_count = int(click_input)
    except ValueError:
        print("Geçersiz sayı, varsayılan değer kullanılacak: 3")
    
    # Simülasyonu başlat
    simulate_browser(start_url, click_count)
