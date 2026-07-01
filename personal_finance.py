import sys
import os
import json
import uuid
import csv
import hashlib
import traceback
import base64
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QFormLayout, QGroupBox, QLineEdit, QPushButton, QLabel, 
                             QListWidget, QComboBox, QMessageBox, QDesktopWidget, QInputDialog, QFileDialog, QProgressBar, QDialog,
                             QStackedWidget, QListWidgetItem, QDateEdit, QCheckBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QTextDocument, QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from PyQt5.QtPrintSupport import QPrinter
    PRINTER_AVAILABLE = True
except ImportError:
    PRINTER_AVAILABLE = False

CURRENT_LANG = "tr"
CURRENT_THEME = "dark"
DATA_FOLDER = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

def T(tr_text, en_text):
    return tr_text if CURRENT_LANG == "tr" else en_text

def ayarlari_oku():
    global CURRENT_LANG, CURRENT_THEME
    dosya = os.path.join(DATA_FOLDER, "settings.json")
    if os.path.exists(dosya):
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                ayarlar = json.load(f)
                CURRENT_THEME = ayarlar.get("tema", "dark")
                CURRENT_LANG = ayarlar.get("dil", "tr")
        except: pass

def ayarlari_kaydet():
    dosya = os.path.join(DATA_FOLDER, "settings.json")
    try:
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump({"tema": CURRENT_THEME, "dil": CURRENT_LANG}, f)
    except: pass

def guvenli_float(deger):
    deger = str(deger).strip()
    if not deger: return 0.0
    if '.' in deger and ',' in deger:
        deger = deger.replace('.', '')
    deger = deger.replace(',', '.')
    try: return float(deger)
    except: return 0.0

def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode('utf-8')).hexdigest()

def sifrele(metin):
    return base64.b64encode(metin.encode('utf-8')).decode('utf-8')

def sifre_coz(sifreli_metin):
    try: return base64.b64decode(sifreli_metin.encode('utf-8')).decode('utf-8')
    except: return sifreli_metin

LIGHT_THEME = """
    * { outline: none; }
    #GirisEkrani, QMainWindow, QDialog { background-color: #f1f5f9; font-family: 'Segoe UI', Arial, sans-serif; letter-spacing: 0.3px; color: #1e293b; }
    QWidget { font-size: 14px; font-family: 'Segoe UI', Arial, sans-serif; }
    QLabel, QCheckBox { background-color: transparent; border: none; color: #1e293b; }
    QGroupBox { font-weight: bold; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 15px; padding-top: 15px; background-color: #ffffff; color: #1e293b; }
    QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px 0 5px; color: #0f766e; background-color: transparent; }
    QLineEdit, QComboBox, QDateEdit { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; background-color: #f8fafc; color: #1e293b; }
    QPushButton { padding: 8px 15px; font-weight: bold; border-radius: 4px; background-color: #e2e8f0; border: 1px solid #cbd5e1; color: #1e293b; }
    QPushButton:hover { background-color: #cbd5e1; }
    QListWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 5px; color: #1e293b; }
    QScrollArea { border: none; background-color: transparent; }
    QScrollArea > QWidget > QWidget { background-color: transparent; }
"""

DARK_THEME = """
    * { outline: none; }
    #GirisEkrani, QMainWindow, QDialog { background-color: #0f172a; font-family: 'Segoe UI', Arial, sans-serif; letter-spacing: 0.3px; color: #e2e8f0; }
    QWidget { font-size: 14px; font-family: 'Segoe UI', Arial, sans-serif; }
    QLabel, QCheckBox { background-color: transparent; border: none; color: #e2e8f0; }
    QGroupBox { font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 15px; padding-top: 15px; background-color: #1e293b; color: #e2e8f0; }
    QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px 0 5px; color: #d4af37; background-color: transparent; }
    QLineEdit, QComboBox, QDateEdit { padding: 8px; border: 1px solid #334155; border-radius: 4px; background-color: #0f172a; color: #e2e8f0; border:none; }
    QPushButton { padding: 8px 15px; font-weight: bold; border-radius: 4px; background-color: #334155; color: #e2e8f0; border: none; }
    QPushButton:hover { background-color: #475569; }
    QListWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 4px; color: #e2e8f0; padding: 5px; border:none; }
    QScrollArea { border: none; background-color: transparent; }
    QScrollArea > QWidget > QWidget { background-color: transparent; }
"""

class MaskedLineEdit(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.check_cursor)
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.check_cursor()
        
    def check_cursor(self):
        t = self.text().replace(" ", "").replace("/", "")
        if not t:
            self.setCursorPosition(0)

class ManuelFiyatDiyalog(QDialog):
    def __init__(self, parent, mesaj):
        super().__init__(parent)
        self.setWindowTitle(T("Girdi", "Input"))
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.setFixedSize(300, 150)
        self.fiyat = -1.0
        
        duzen = QVBoxLayout(self)
        self.lbl_mesaj = QLabel(mesaj)
        self.lbl_mesaj.setWordWrap(True)
        self.girdi = QLineEdit()
        
        btn_duzen = QHBoxLayout()
        self.btn_tamam = QPushButton(T("Tamam", "OK"))
        self.btn_tamam.setStyleSheet("background-color: #10b981; color: white;")
        self.btn_tamam.clicked.connect(self.kabul)
        self.btn_iptal = QPushButton(T("İptal", "Cancel"))
        self.btn_iptal.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_iptal.clicked.connect(self.reject)
        
        btn_duzen.addWidget(self.btn_tamam)
        btn_duzen.addWidget(self.btn_iptal)
        duzen.addWidget(self.lbl_mesaj)
        duzen.addWidget(self.girdi)
        duzen.addLayout(btn_duzen)

    def kabul(self):
        try:
            self.fiyat = float(self.girdi.text().replace(',', '.'))
            self.accept()
        except:
            QMessageBox.warning(self, T("Hata", "Error"), T("Geçerli bir sayı giriniz.", "Enter a valid number."))

class KartEkleDialog(QDialog):
    def __init__(self, parent, kart=None):
        super().__init__(parent)
        self.kart = kart
        self.setWindowTitle(T("Kart Ekle/Düzenle", "Add/Edit Card"))
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.setFixedSize(350, 400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.ad = QLineEdit()
        self.ad.setPlaceholderText(T("Örn: Ziraat Bankkart", "Ex: Ziraat Bankkart"))
        
        self.tip = QComboBox()
        self.tip.addItems(["Mastercard", "Visa", "Troy", "American Express", "Diğer"])
        
        self.no = MaskedLineEdit()
        self.no.setInputMask("0000 0000 0000 0000")
        
        self.skt = MaskedLineEdit()
        self.skt.setInputMask("00/00")
        
        self.cvv = MaskedLineEdit()
        self.cvv.setInputMask("000")
        self.cvv.setEchoMode(QLineEdit.Password)
        
        self.limit = QLineEdit()
        self.limit.setPlaceholderText(T("Limit (TL)", "Limit (TL)"))
        
        form.addRow(T("Kart Adı:", "Card Name:"), self.ad)
        form.addRow(T("Ağ Tipi:", "Network:"), self.tip)
        form.addRow(T("Kart No:", "Card No:"), self.no)
        form.addRow(T("Son Kul. (AA/YY):", "Expiry (MM/YY):"), self.skt)
        form.addRow(T("CVV:", "CVV:"), self.cvv)
        form.addRow(T("Limit (TL):", "Limit (TL):"), self.limit)
        
        if kart:
            self.ad.setText(kart.get("ad", ""))
            self.tip.setCurrentText(kart.get("tip", "Mastercard"))
            try:
                self.no.setText(sifre_coz(kart.get("no", "")))
                self.skt.setText(sifre_coz(kart.get("skt", "")))
                self.cvv.setText(sifre_coz(kart.get("cvv", "")))
            except: pass
            self.limit.setText(str(kart.get("limit", "")))
        
        self.btn_kaydet = QPushButton(T("Kaydet", "Save"))
        self.btn_kaydet.setStyleSheet("background-color: #10b981; color: white;")
        self.btn_kaydet.clicked.connect(self.kabul)
        
        layout.addLayout(form)
        layout.addWidget(self.btn_kaydet)

    def kabul(self):
        ad = self.ad.text().strip()
        no = self.no.text().replace(" ", "")
        skt = self.skt.text()
        cvv = self.cvv.text()
        
        if not ad or len(no) != 16 or len(skt) != 5 or len(cvv) != 3:
            QMessageBox.warning(self, T("Hata", "Error"), T("Lütfen tüm alanları eksiksiz ve doğru formatta doldurun.", "Please fill all fields correctly."))
            return
            
        try:
            lim = guvenli_float(self.limit.text())
            if lim <= 0: raise ValueError
        except:
            QMessageBox.warning(self, T("Hata", "Error"), T("Geçerli bir limit girin.", "Enter a valid limit."))
            return
            
        self.accept()

class IslemDuzenleDialog(QDialog):
    def __init__(self, parent, islem, suanki_ay):
        super().__init__(parent)
        self.setWindowTitle(T("İşlem Yönetimi", "Manage Transaction"))
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.setFixedSize(350, 300)
        self.islem = islem
        self.suanki_ay = suanki_ay
        self.islem_silindi = False
        self.islem_guncellendi = False
        
        duzen = QVBoxLayout(self)
        form = QFormLayout()
        
        self.tutar = QLineEdit(str(islem.get("tutar", "")))
        self.aciklama = QLineEdit(islem.get("aciklama", ""))
        self.kategori = QLineEdit(islem.get("kategori", ""))
        self.sabit = QCheckBox(T("Düzenli (Her Ay Tekrarla)", "Regular (Monthly)"))
        self.sabit.setChecked(islem.get("sabit", False))
        
        form.addRow(T("Tutar:", "Amount:"), self.tutar)
        form.addRow(T("Açıklama:", "Description:"), self.aciklama)
        form.addRow(T("Kategori:", "Category:"), self.kategori)
        form.addRow("", self.sabit)
        
        btn_duzen = QHBoxLayout()
        self.btn_kaydet = QPushButton(T("Güncelle", "Update"))
        self.btn_kaydet.setStyleSheet("background-color: #10b981; color: white;")
        self.btn_kaydet.clicked.connect(self.guncelle)
        
        self.btn_sil = QPushButton(T("Tamamen Sil", "Delete All"))
        self.btn_sil.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_sil.clicked.connect(self.sil)
        
        btn_duzen.addWidget(self.btn_kaydet)
        btn_duzen.addWidget(self.btn_sil)
        
        duzen.addLayout(form)
        duzen.addLayout(btn_duzen)
        
        if islem.get("sabit", False) and not islem.get("bitis_tarihi"):
            self.btn_durdur = QPushButton(T("Bu Aydan Sonra İptal Et", "Cancel After This Month"))
            self.btn_durdur.setStyleSheet("background-color: #f59e0b; color: white;")
            self.btn_durdur.clicked.connect(self.durdur)
            duzen.addWidget(self.btn_durdur)

    def guncelle(self):
        self.islem["tutar"] = guvenli_float(self.tutar.text())
        self.islem["aciklama"] = self.aciklama.text().strip()
        self.islem["kategori"] = self.kategori.text().strip()
        self.islem["sabit"] = self.sabit.isChecked()
        self.islem_guncellendi = True
        self.accept()

    def sil(self):
        self.islem_silindi = True
        self.accept()

    def durdur(self):
        onceki_ay = self.suanki_ay - timedelta(days=28)
        self.islem["bitis_tarihi"] = onceki_ay.strftime("%Y-%m")
        self.islem_guncellendi = True
        self.accept()

class KayitEkrani(QDialog):
    def __init__(self, parent, kullanicilar, dosya_yolu):
        super().__init__(parent)
        self.kullanicilar = kullanicilar
        self.dosya_yolu = dosya_yolu
        self.setWindowTitle(T("Kayıt Ol", "Register"))
        self.setFixedSize(380, 320)
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        
        duzen = QVBoxLayout(self)
        form = QFormLayout()
        
        self.kullanici_adi = QLineEdit()
        self.sifre = QLineEdit()
        self.sifre.setEchoMode(QLineEdit.Password)
        
        self.gizli_soru = QComboBox()
        self.gizli_soru.addItems([
            T("İlk evcil hayvanınızın adı?", "Name of your first pet?"),
            T("İlkokul öğretmeninizin adı?", "Name of your primary school teacher?"),
            T("En sevdiğiniz film karakteri?", "Favorite movie character?"),
            T("Çocukluk kahramanınız kimdi?", "Who was your childhood hero?"),
            T("İlkokulu okuduğunuz şehir?", "City where you attended primary school?"),
            T("En yakın çocukluk arkadaşınız?", "Your closest childhood friend?")
        ])
        self.gizli_cevap = QLineEdit()
        self.gizli_cevap.setPlaceholderText(T("Sıfırlama ve Hesap Silme için gereklidir", "Needed for reset & account deletion"))
        
        self.lbl_ad = QLabel(T("Kullanıcı Adı:", "Username:"))
        self.lbl_sifre = QLabel(T("Şifre:", "Password:"))
        self.lbl_soru = QLabel(T("Güvenlik Sorusu:", "Security Question:"))
        self.lbl_cevap = QLabel(T("Cevap:", "Answer:"))
        
        form.addRow(self.lbl_ad, self.kullanici_adi)
        form.addRow(self.lbl_sifre, self.sifre)
        form.addRow(self.lbl_soru, self.gizli_soru)
        form.addRow(self.lbl_cevap, self.gizli_cevap)
        
        self.btn_kayit = QPushButton(T("Hesabı Oluştur", "Create Account"))
        self.btn_kayit.setStyleSheet("background-color: #10b981; color: white; border: none;")
        self.btn_kayit.clicked.connect(self.kayit_tamamla)
        
        self.lbl_baslik = QLabel(f"<h2>{T('Yeni Profil', 'New Profile')}</h2>")
        self.lbl_baslik.setAlignment(Qt.AlignCenter)
        
        duzen.addWidget(self.lbl_baslik)
        duzen.addLayout(form)
        duzen.addWidget(self.btn_kayit)

    def kayit_tamamla(self):
        ad = self.kullanici_adi.text().strip()
        sifre = self.sifre.text()
        cevap = self.gizli_cevap.text().strip().lower()
        soru = self.gizli_soru.currentText()
        
        if not ad or not sifre or not cevap:
            QMessageBox.warning(self, T("Hata", "Error"), T("Tüm alanları doldurun!", "Fill all fields!"))
            return
        if ad in self.kullanicilar:
            QMessageBox.warning(self, T("Uyarı", "Warning"), T("Bu kullanıcı adı zaten mevcut!", "This username already exists!"))
            return
            
        self.kullanicilar[ad] = {
            "sifre": sifre_hashle(sifre),
            "soru": soru,
            "cevap": sifre_hashle(cevap)
        }
        
        with open(self.dosya_yolu, "w", encoding="utf-8") as f:
            json.dump(self.kullanicilar, f, ensure_ascii=False, indent=4)
        QMessageBox.information(self, T("Başarılı", "Success"), T("Kayıt oluşturuldu. Giriş yapabilirsiniz.", "Registration complete. You can login."))
        self.accept()

class GirisEkrani(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("GirisEkrani")
        ayarlari_oku()
        self.setWindowTitle(T("Kişisel Finans Yöneticisi - Giriş", "Personal Finance Manager - Login"))
        self.setFixedSize(400, 520)
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.merkeze_al()
        
        os.makedirs(DATA_FOLDER, exist_ok=True)
        self.kullanicilar_dosyasi = os.path.join(DATA_FOLDER, "users.json")
        self.kullanicilar = self.kullanicilari_yukle()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        
        ust_bar = QHBoxLayout()
        self.btn_dil = QPushButton("EN" if CURRENT_LANG == "tr" else "TR")
        self.btn_dil.setFixedWidth(45)
        self.btn_dil.clicked.connect(self.dil_degistir)
        
        self.btn_tema = QPushButton("🌙" if CURRENT_THEME == "light" else "☀️")
        self.btn_tema.setFixedWidth(45)
        self.btn_tema.clicked.connect(self.tema_degistir)
        
        ust_bar.addStretch()
        ust_bar.addWidget(self.btn_dil)
        ust_bar.addWidget(self.btn_tema)
        layout.addLayout(ust_bar)
        
        self.lbl_ana_baslik = QLabel()
        self.lbl_ana_baslik.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_ana_baslik)
        layout.addSpacing(20)
        
        self.giris_grubu = QGroupBox()
        giris_duzen = QFormLayout()
        giris_duzen.setSpacing(15)
        
        self.giris_kullanici = QLineEdit()
        self.giris_sifre = QLineEdit()
        self.giris_sifre.setEchoMode(QLineEdit.Password)
        self.giris_sifre.returnPressed.connect(self.giris_yap)
        
        self.btn_giris = QPushButton()
        self.btn_giris.clicked.connect(self.giris_yap)
        
        self.lbl_ad = QLabel()
        self.lbl_sif = QLabel()
        
        giris_duzen.addRow(self.lbl_ad, self.giris_kullanici)
        giris_duzen.addRow(self.lbl_sif, self.giris_sifre)
        giris_duzen.addRow("", self.btn_giris)
        self.giris_grubu.setLayout(giris_duzen)
        layout.addWidget(self.giris_grubu)
        
        alt_butonlar = QHBoxLayout()
        self.lbl_sifre_unuttum = QLabel()
        self.lbl_sifre_unuttum.setCursor(QCursor(Qt.PointingHandCursor))
        self.lbl_sifre_unuttum.mousePressEvent = self.sifremi_unuttum
        
        self.btn_kayit = QPushButton()
        self.btn_kayit.clicked.connect(self.kayit_ekrani_ac)
        
        alt_butonlar.addWidget(self.btn_kayit)
        alt_butonlar.addStretch()
        alt_butonlar.addWidget(self.lbl_sifre_unuttum)
        
        layout.addSpacing(10)
        layout.addLayout(alt_butonlar)
        layout.addStretch()
        
        self.arayuz_metinlerini_guncelle()

    def merkeze_al(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def dil_degistir(self):
        global CURRENT_LANG
        CURRENT_LANG = "en" if CURRENT_LANG == "tr" else "tr"
        ayarlari_kaydet()
        self.arayuz_metinlerini_guncelle()

    def tema_degistir(self):
        global CURRENT_THEME
        CURRENT_THEME = "dark" if CURRENT_THEME == "light" else "light"
        ayarlari_kaydet()
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.arayuz_metinlerini_guncelle()

    def arayuz_metinlerini_guncelle(self):
        self.setWindowTitle(T("Kişisel Finans Yöneticisi - Giriş", "Personal Finance Manager - Login"))
        self.btn_dil.setText("EN" if CURRENT_LANG == "tr" else "TR")
        self.btn_tema.setText("🌙" if CURRENT_THEME == "light" else "☀️")
        
        saat = datetime.now().hour
        ikon = "☀️" if 5 <= saat < 18 else "🌙"
        if 5 <= saat < 12: selamlama = T("Günaydın", "Good Morning")
        elif 12 <= saat < 18: selamlama = T("İyi Günler", "Good Afternoon")
        else: selamlama = T("İyi Akşamlar", "Good Evening")
        
        self.lbl_ana_baslik.setText(f"{ikon} {selamlama}.\n{T('Kişisel Finans Yöneticisi', 'Personal Finance Manager')}")
        self.lbl_ana_baslik.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e; background: transparent; border: none;" if CURRENT_THEME == "light" else "font-size: 20px; font-weight: bold; color: #d4af37; background: transparent; border: none;")
        
        self.giris_grubu.setTitle(T("Sisteme Giriş Yap", "Login to System"))
        self.lbl_ad.setText(T("Kullanıcı Adı:", "Username:"))
        self.lbl_sif.setText(T("Şifre:", "Password:"))
        
        self.btn_giris.setText(T("Giriş Yap", "Login"))
        self.btn_giris.setStyleSheet("background-color: #0f766e; color: white; padding: 10px; border: none; border-radius: 4px;" if CURRENT_THEME == "light" else "background-color: #d4af37; color: black; padding: 10px; border: none; border-radius: 4px;")
        
        self.lbl_sifre_unuttum.setText(T("Şifremi Unuttum", "Forgot Password"))
        self.lbl_sifre_unuttum.setStyleSheet("color: #ef4444; padding: 4px; border-radius: 4px; background: transparent; border: none;")
        
        self.btn_kayit.setText(T("Yeni Kayıt", "Register"))
        self.btn_kayit.setStyleSheet("color: #0f766e; border: none; font-weight: bold; text-decoration: underline; background: transparent;" if CURRENT_THEME == "light" else "color: #d4af37; border: none; font-weight: bold; text-decoration: underline; background: transparent;")

    def kullanicilari_yukle(self):
        if os.path.exists(self.kullanicilar_dosyasi):
            with open(self.kullanicilar_dosyasi, "r", encoding="utf-8") as dosya:
                try: return json.load(dosya)
                except: return {}
        return {}

    def kayit_ekrani_ac(self):
        diyalog = KayitEkrani(self, self.kullanicilar, self.kullanicilar_dosyasi)
        if diyalog.exec_() == QDialog.Accepted:
            self.kullanicilar = self.kullanicilari_yukle()

    def sifremi_unuttum(self, event):
        ad, ok = QInputDialog.getText(self, T("Şifre Sıfırlama", "Password Reset"), T("Kullanıcı Adınız:", "Your Username:"))
        if ok and ad:
            if ad in self.kullanicilar and isinstance(self.kullanicilar[ad], dict):
                kullanici_bilgi = self.kullanicilar[ad]
                soru = kullanici_bilgi.get("soru", "")
                cevap, ok2 = QInputDialog.getText(self, T("Güvenlik Sorusu", "Security Question"), f"{soru}\n{T('Cevabınız:', 'Your Answer:')}")
                if ok2 and sifre_hashle(cevap.strip().lower()) == kullanici_bilgi.get("cevap", ""):
                    yeni_sifre, ok3 = QInputDialog.getText(self, T("Yeni Şifre", "New Password"), T("Yeni şifrenizi girin:", "Enter new password:"), QLineEdit.Password)
                    if ok3 and yeni_sifre:
                        self.kullanicilar[ad]["sifre"] = sifre_hashle(yeni_sifre)
                        with open(self.kullanicilar_dosyasi, "w", encoding="utf-8") as f:
                            json.dump(self.kullanicilar, f, ensure_ascii=False, indent=4)
                        QMessageBox.information(self, T("Başarılı", "Success"), T("Şifreniz başarıyla sıfırlandı.", "Password reset successful."))
                else:
                    QMessageBox.warning(self, T("Hata", "Error"), T("Yanlış cevap!", "Wrong answer!"))
            else:
                QMessageBox.warning(self, T("Hata", "Error"), T("Kullanıcı bulunamadı veya eski nesil hesap.", "User not found or legacy account."))

    def giris_yap(self):
        ad = self.giris_kullanici.text().strip()
        sifre = self.giris_sifre.text()
        
        if not ad:
            QMessageBox.warning(self, T("Hata", "Error"), T("Kullanıcı adı giriniz!", "Enter a username!"))
            return
            
        kayit = self.kullanicilar.get(ad)
        giris_basarili = False
        
        if isinstance(kayit, str):
            if kayit == sifre_hashle(sifre) or kayit == sifre:
                if kayit == sifre:
                    self.kullanicilar[ad] = {"sifre": sifre_hashle(sifre), "soru": "Eski Nesil Hesap", "cevap": ""}
                    with open(self.kullanicilar_dosyasi, "w", encoding="utf-8") as f:
                        json.dump(self.kullanicilar, f, ensure_ascii=False, indent=4)
                giris_basarili = True
        elif isinstance(kayit, dict):
            if kayit.get("sifre") == sifre_hashle(sifre) or kayit.get("sifre") == sifre:
                giris_basarili = True
                
        if giris_basarili:
            try:
                self.ana_uygulama = FinansUygulamasi(ad)
                self.ana_uygulama.show()
                self.close()
            except Exception as e:
                hata_detayi = traceback.format_exc()
                QMessageBox.critical(self, "Kritik Sistem Hatası", f"Uygulama açılırken bilgisayar/kod kaynaklı bir çökme yaşandı!\n\nLütfen bu hatayı Arda'ya bildir:\n\n{hata_detayi}")
        else:
            QMessageBox.warning(self, T("Hata", "Error"), T("Hatalı kullanıcı adı veya şifre!", "Invalid username or password!"))


class FinansUygulamasi(QMainWindow):
    def __init__(self, profil_adi):
        super().__init__()
        self.profil_adi = profil_adi
        self.dosya_adi = os.path.join(DATA_FOLDER, f"{self.profil_adi.replace(' ', '_')}_data.json")
        self.kaydedildi = True
        
        self.kartlar = []
        self.islemler = []
        self.taksitler = []
        self.portfoy = []
        self.hedefler = []
        self.borclar = []
        self.suanki_ay = datetime.now()
        
        self.kategoriler = [T("Maaş", "Salary"), T("Market", "Groceries"), T("Fatura", "Bills"), 
                            T("Kira/Aidat", "Rent"), T("Eğitim", "Education"), T("Eğlence", "Entertainment"), 
                            T("Yatırım", "Investment"), T("Sağlık", "Health"), T("Diğer", "Other")]
        
        self.setFixedSize(1150, 800)
        self.merkeze_al()
        
        self.kalan_saniye = 600
        
        merkez = QWidget()
        self.setCentralWidget(merkez)
        
        ana_duzen = QVBoxLayout()
        ana_duzen.setContentsMargins(15, 15, 15, 15)
        ana_duzen.setSpacing(10)
        
        ust_bar = QHBoxLayout()
        ust_sol_duzen = QVBoxLayout()
        
        saat = datetime.now().hour
        ikon = "☀️" if 5 <= saat < 18 else "🌙"
        if 5 <= saat < 12: selamlama = T("Günaydın", "Good Morning")
        elif 12 <= saat < 18: selamlama = T("İyi Günler", "Good Afternoon")
        else: selamlama = T("İyi Akşamlar", "Good Evening")
        
        self.hosgeldin_yazisi = QLabel(f"👤 {selamlama}. {self.profil_adi} {ikon}")
        self.hosgeldin_yazisi.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e; background: transparent; border: none;" if CURRENT_THEME == "light" else "font-size: 16px; font-weight: bold; color: #d4af37; background: transparent; border: none;")
        self.zaman_lbl = QLabel()
        self.zaman_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #7f8c8d; background: transparent; border: none;")
        
        self.zamanlayici = QTimer(self)
        self.zamanlayici.timeout.connect(self.saati_ve_sayaci_guncelle)
        self.zamanlayici.start(1000)
        
        ust_sol_duzen.addWidget(self.hosgeldin_yazisi)
        ust_sol_duzen.addWidget(self.zaman_lbl)
        
        self.btn_dil = QPushButton("EN" if CURRENT_LANG == "tr" else "TR")
        self.btn_dil.setFixedWidth(45)
        self.btn_dil.clicked.connect(self.dil_degistir)
        self.btn_tema = QPushButton("🌙" if CURRENT_THEME == "light" else "☀️")
        self.btn_tema.setFixedWidth(45)
        self.btn_tema.clicked.connect(self.tema_degistir)
        
        cikis_paneli = QVBoxLayout()
        self.btn_cikis = QPushButton(T("🚪 Çıkış Yap", "🚪 Logout"))
        self.btn_cikis.setStyleSheet("background-color: #ef4444; color: white; border: none;")
        self.btn_cikis.clicked.connect(self.cikis_yap)
        self.lbl_oturum = QLabel("⏱ 10:00")
        self.lbl_oturum.setAlignment(Qt.AlignCenter)
        self.lbl_oturum.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        
        cikis_paneli.addWidget(self.btn_cikis)
        cikis_paneli.addWidget(self.lbl_oturum)
        
        ust_bar.addLayout(ust_sol_duzen)
        ust_bar.addStretch()
        ust_bar.addWidget(self.btn_dil)
        ust_bar.addWidget(self.btn_tema)
        ust_bar.addLayout(cikis_paneli)
        
        self.sekmeler_stack = QStackedWidget()
        self.tab_islem = QWidget()
        self.tab_taksit = QWidget()
        self.tab_varliklar = QWidget()
        self.tab_kartlar = QWidget()
        self.tab_hedefler = QWidget()
        self.tab_borclar = QWidget()
        self.tab_aylik_analiz = QWidget()
        self.tab_ozet = QWidget()
        
        self.sekmeler_stack.addWidget(self.tab_islem)
        self.sekmeler_stack.addWidget(self.tab_taksit)
        self.sekmeler_stack.addWidget(self.tab_varliklar)
        self.sekmeler_stack.addWidget(self.tab_kartlar)
        self.sekmeler_stack.addWidget(self.tab_hedefler)
        self.sekmeler_stack.addWidget(self.tab_borclar)
        self.sekmeler_stack.addWidget(self.tab_aylik_analiz)
        self.sekmeler_stack.addWidget(self.tab_ozet)
        
        self.islem_arayuzu_kur()
        self.taksit_arayuzu_kur()
        self.varlik_arayuzu_kur()
        self.kart_arayuzu_kur()
        self.hedef_arayuzu_kur()
        self.borc_arayuzu_kur()
        self.aylik_analiz_arayuzu_kur()
        self.ozet_arayuzu_kur()
        
        sol_panel = QVBoxLayout()
        sol_panel.setSpacing(6)
        sol_panel.setContentsMargins(10, 15, 10, 15)
        self.btn_nav = []
        
        tab_labels = [
            (T("💸 İşlemler (Gelir/Gider)", "💸 Transactions"), 0),
            (T("💳 Kredi Kartı Taksitleri", "💳 Installments"), 1),
            (T("📈 Varlıklar (Yatırım)", "📈 Assets"), 2),
            (T("🪪 Kartlarım / Cüzdan", "🪪 My Cards"), 3),
            (T("🎯 Hedeflerim", "🎯 My Goals"), 4),
            (T("🤝 Borç / Alacak Defteri", "🤝 Debt Book"), 5),
            (T("📊 Aylık Analiz", "📊 Monthly Analysis"), 6),
            (T("📋 Profil Özeti", "📋 Profile Summary"), 7),
        ]
        
        for label, idx in tab_labels:
            btn = QPushButton(label)
            btn.setFixedHeight(45)
            btn.setStyleSheet("text-align: left; padding-left: 15px; font-size: 14px;")
            btn.clicked.connect(lambda checked, i=idx: self.sekmeler_stack.setCurrentIndex(i))
            sol_panel.addWidget(btn)
            self.btn_nav.append(btn)
            
        sol_panel.addStretch()
        sol_grup = QGroupBox()
        sol_grup.setLayout(sol_panel)
        sol_grup.setFixedWidth(230)
        
        merkez_duzen = QHBoxLayout()
        merkez_duzen.setSpacing(15)
        merkez_duzen.addWidget(sol_grup)
        merkez_duzen.addWidget(self.sekmeler_stack)
        
        ana_duzen.addLayout(ust_bar)
        ana_duzen.addLayout(merkez_duzen)
        merkez.setLayout(ana_duzen) 
        
        self.profili_yukle()
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.arayuz_metinlerini_guncelle()
        self.sekmeler_stack.setCurrentIndex(7)

    def saati_ve_sayaci_guncelle(self):
        suan = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.zaman_lbl.setText(f"📍 Balıkesir, Türkiye | 🕒 {suan}")
        
        self.kalan_saniye -= 1
        mins, secs = divmod(self.kalan_saniye, 60)
        self.lbl_oturum.setText(f"⏱ {mins:02d}:{secs:02d}")
        
        if self.kalan_saniye == 60:
            QMessageBox.warning(self, T("Güvenlik Uyarısı", "Security Warning"), T("Oturum sürenizin dolmasına 1 dakika kaldı!", "1 minute remaining until your session expires!"))
        elif self.kalan_saniye <= 0:
            self.kaydedildi = True 
            self.cikis_yap()

    def veri_degisti(self):
        self.kaydedildi = False
        self.setWindowTitle(f"{T('Kişisel Finans Yöneticisi', 'Personal Finance Manager')} - {self.profil_adi} *")
        self.islem_ay_filtre_guncelle()
        self.listeleri_guncelle()
        self.aylik_analiz_guncelle()
        self.ozeti_guncelle()

    def merkeze_al(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def dil_degistir(self):
        global CURRENT_LANG
        self.profili_kaydet(sessiz=True)
        CURRENT_LANG = "en" if CURRENT_LANG == "tr" else "tr"
        ayarlari_kaydet()
        self.arayuz_metinlerini_guncelle()
        self.islem_ay_filtre_guncelle() 
        self.listeleri_guncelle()
        self.aylik_analiz_guncelle()
        self.ozeti_guncelle()
        self.kart_gridini_ciz()
        self.hedef_gridini_ciz()

    def tema_degistir(self):
        global CURRENT_THEME
        self.profili_kaydet(sessiz=True)
        CURRENT_THEME = "dark" if CURRENT_THEME == "light" else "light"
        ayarlari_kaydet()
        self.setStyleSheet(DARK_THEME if CURRENT_THEME == "dark" else LIGHT_THEME)
        self.arayuz_metinlerini_guncelle()
        self.islem_ay_filtre_guncelle()
        self.listeleri_guncelle()
        self.aylik_analiz_guncelle()
        self.kart_gridini_ciz()
        self.hedef_gridini_ciz()

    def arayuz_metinlerini_guncelle(self):
        self.setWindowTitle(f"{T('Kişisel Finans Yöneticisi', 'Personal Finance Manager')} - {self.profil_adi}{'*' if not self.kaydedildi else ''}")
        self.btn_dil.setText("EN" if CURRENT_LANG == "tr" else "TR")
        self.btn_tema.setText("🌙" if CURRENT_THEME == "light" else "☀️")
        self.btn_cikis.setText(T("🚪 Çıkış Yap", "🚪 Logout"))
        
        saat = datetime.now().hour
        ikon = "☀️" if 5 <= saat < 18 else "🌙"
        if 5 <= saat < 12: selamlama = T("Günaydın", "Good Morning")
        elif 12 <= saat < 18: selamlama = T("İyi Günler", "Good Afternoon")
        else: selamlama = T("İyi Akşamlar", "Good Evening")
        
        self.hosgeldin_yazisi.setText(f"👤 {selamlama}. {self.profil_adi} {ikon}")
        self.hosgeldin_yazisi.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e; background: transparent; border: none;" if CURRENT_THEME == "light" else "font-size: 16px; font-weight: bold; color: #d4af37; background: transparent; border: none;")
        
        nav_text = [
            T("💸 İşlemler (Gelir/Gider)", "💸 Transactions"),
            T("💳 Kredi Kartı Taksitleri", "💳 Installments"),
            T("📈 Varlıklar (Yatırım)", "📈 Assets"),
            T("🪪 Kartlarım / Cüzdan", "🪪 My Cards"),
            T("🎯 Hedeflerim", "🎯 My Goals"),
            T("🤝 Borç / Alacak Defteri", "🤝 Debt Book"),
            T("📊 Aylık Analiz", "📊 Monthly Analysis"),
            T("📋 Profil Özeti", "📋 Profile Summary")
        ]
        for i, btn in enumerate(self.btn_nav):
            btn.setText(nav_text[i])
            
        mevcut_g_kat = self.gelir_kategori.currentText()
        mevcut_gi_kat = self.gider_kategori.currentText()
        
        yeni_kats = [T("Maaş", "Salary"), T("Market", "Groceries"), T("Fatura", "Bills"), T("Kira/Aidat", "Rent"),
                     T("Eğitim", "Education"), T("Eğlence", "Entertainment"), T("Yatırım", "Investment"), 
                     T("Sağlık", "Health"), T("Diğer", "Other")]
        
        ozel_kats = [k for k in self.kategoriler if k not in [T("Maaş", "Salary"), T("Market", "Groceries"), T("Fatura", "Bills"), T("Kira/Aidat", "Rent"), T("Eğitim", "Education"), T("Eğlence", "Entertainment"), T("Yatırım", "Investment"), T("Sağlık", "Health"), T("Diğer", "Other")]]
        self.kategoriler = yeni_kats + ozel_kats
        
        self.gelir_kategori.clear(); self.gider_kategori.clear()
        self.gelir_kategori.addItems(self.kategoriler); self.gider_kategori.addItems(self.kategoriler)
        if mevcut_g_kat in self.kategoriler: self.gelir_kategori.setCurrentText(mevcut_g_kat)
        if mevcut_gi_kat in self.kategoriler: self.gider_kategori.setCurrentText(mevcut_gi_kat)
        
        self.g_grup.setTitle(T("Gelir Ekle", "Add Income"))
        self.gi_grup.setTitle(T("Gider Ekle", "Add Expense"))
        self.lbl_g_kat.setText(T("Kategori:", "Category:"))
        self.lbl_g_acik.setText(T("Açıklama:", "Description:"))
        self.lbl_g_tut.setText(T("Tutar (TL):", "Amount (TL):"))
        self.lbl_g_tarih.setText(T("Tarih:", "Date:"))
        self.gelir_sabit.setText(T("Düzenli (Her Ay Tekrarla)", "Regular (Monthly)"))
        self.lbl_gi_kat.setText(T("Kategori:", "Category:"))
        self.lbl_gi_acik.setText(T("Açıklama:", "Description:"))
        self.lbl_gi_tut.setText(T("Tutar (TL):", "Amount (TL):"))
        self.lbl_gi_tarih.setText(T("Tarih:", "Date:"))
        self.gider_sabit.setText(T("Düzenli (Her Ay Tekrarla)", "Regular (Monthly)"))
        self.btn_gelir.setText(T("Gelir Ekle", "Add Income"))
        self.btn_gider.setText(T("Gider Ekle", "Add Expense"))
        self.lbl_ay_filtre.setText(T("Ay Filtresi:", "Month Filter:"))
        
        self.t_grup.setTitle(T("Yeni Taksitlendir", "New Installment"))
        self.lbl_t_kart.setText(T("Kullanılan Kart:", "Card Used:"))
        self.lbl_t_urun.setText(T("Ürün:", "Product:"))
        self.lbl_t_tut.setText(T("Toplam Tutar:", "Total Amount:"))
        self.lbl_t_ay.setText(T("Vade (Ay):", "Term (Months):"))
        self.lbl_t_tarih.setText(T("Tarih:", "Date:"))
        self.btn_t_ekle.setText(T("Ekle ve Kart Limitinden Düş", "Add & Deduct from Card"))
        self.taksit_urun.setPlaceholderText(T("Ürün/Hizmet", "Product/Service"))
        self.taksit_tutar.setPlaceholderText(T("Toplam Tutar (TL)", "Total Amount (TL)"))
        self.taksit_ay.setPlaceholderText(T("Taksit Sayısı", "Months"))
        
        self.p_grup.setTitle(T("Portföy (Yatırımlar)", "Portfolio (Investments)"))
        self.lbl_p_tur.setText(T("Varlık Türü:", "Asset Type:"))
        self.p_sembol_lbl.setText(T("Sembol/Ad (Örn: THYAO):", "Symbol/Name (Ex: AAPL):"))
        self.lbl_p_mik.setText(T("Miktar:", "Amount:"))
        self.p_miktar.setPlaceholderText(T("Lot veya Gram", "Amount"))
        self.lbl_p_mal.setText(T("Alış Maliyeti:", "Cost Price:"))
        self.p_maliyet.setPlaceholderText(T("Birim Başına Maliyet (Opsiyonel)", "Cost Per Unit (Optional)"))
        self.btn_p.setText(T("Canlı Fiyatla Ekle", "Add w/ Live Price"))
        
        self.btn_excel.setText(T("📊 Zengin Raporu Excel'e Aktar", "📊 Export Detailed Report to Excel"))
        self.b_grup.setTitle(T("Finansal Özet Kartları", "Financial Summary Cards"))
        self.s_grup.setTitle(T("Toplam Net Servet", "Total Net Worth"))
        self.btn_pdf.setText(T("📄 Kapsamlı PDF Raporu Oluştur", "📄 Generate Comprehensive PDF"))
        self.btn_kaydet.setText(T("💾 Profili Kaydet", "💾 Save Profile"))
        self.btn_hesap_sil.setText(T("⚠️ Hesabımı Sil", "⚠️ Delete Account"))

    def _add_empty_state(self, list_widget, text):
        if list_widget.count() == 0:
            item = QListWidgetItem(text)
            item.setFlags(Qt.NoItemFlags)
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(Qt.gray)
            font = item.font()
            font.setItalic(True)
            font.setPointSize(12)
            item.setFont(font)
            list_widget.addItem(item)

    def listeleri_guncelle(self):
        self.liste_gelir.clear()
        self.liste_gider.clear()
        filtre = self.ay_filtre_combo.currentText()
        
        for islem in sorted(self.islemler, key=lambda x: x.get('tarih', ''), reverse=True):
            if not isinstance(islem, dict): continue
            is_sabit = islem.get("sabit", False)
            islem_ay_str = f"{islem.get('yil')}-{islem.get('ay'):02d}"
            
            if filtre != T("Tüm Zamanlar", "All Time") and filtre != islem_ay_str: continue
            
            sbt_ikon = " 🔁" if is_sabit else ""
            iptal_txt = f" [İptal: {islem.get('bitis_tarihi')}]" if is_sabit and islem.get("bitis_tarihi") else ""
            
            if islem.get("tip") == "gelir":
                item = QListWidgetItem(f"🟢 {T('Gelir:', 'Income:')} [{islem.get('kategori', '')}] {islem.get('aciklama', '')}{sbt_ikon} | +{islem.get('tutar', 0.0):.2f} TL | {islem.get('tarih', '')}{iptal_txt}")
                item.setData(Qt.UserRole, islem.get("id"))
                item.setForeground(Qt.darkGreen if CURRENT_THEME == "light" else Qt.green)
                self.liste_gelir.addItem(item)
            elif islem.get("tip") == "gider":
                item = QListWidgetItem(f"🔴 {T('Gider:', 'Expense:')} [{islem.get('kategori', '')}] {islem.get('aciklama', '')}{sbt_ikon} | -{islem.get('tutar', 0.0):.2f} TL | {islem.get('tarih', '')}{iptal_txt}")
                item.setData(Qt.UserRole, islem.get("id"))
                item.setForeground(Qt.darkRed if CURRENT_THEME == "light" else Qt.red)
                self.liste_gider.addItem(item)
                
        self.liste_taksit.clear()
        for taksit in sorted(self.taksitler, key=lambda x: x.get('tarih', ''), reverse=True):
            if isinstance(taksit, dict):
                item = QListWidgetItem(f"💳 {taksit.get('kart', '')} | {taksit.get('urun', '')} | {taksit.get('vade', 1)} {T('Ay', 'Months')} | {T('Aylık:', 'Monthly:')} {taksit.get('aylik', 0.0):.2f} TL | {T('Toplam:', 'Total:')} {taksit.get('toplam', 0.0):.2f} TL | Tarih: {taksit.get('tarih', '')}")
                item.setData(Qt.UserRole, taksit.get("id"))
                self.liste_taksit.addItem(item)
                
        self.liste_portfoy.clear()
        for p in self.portfoy:
            if isinstance(p, dict):
                miktar = p.get('miktar', 0)
                maliyet = p.get('maliyet', p.get('fiyat', 0))
                guncel = p.get('fiyat', maliyet)
                top_maliyet = maliyet * miktar
                top_guncel = guncel * miktar
                fark = top_guncel - top_maliyet
                yuzde = (fark / top_maliyet * 100) if top_maliyet > 0 else 0
                durum_str = f"({'+' if fark>=0 else ''}{fark:.2f} TL | {'+' if yuzde>=0 else ''}{yuzde:.1f}%)"
                
                item = QListWidgetItem(f"📈 {p.get('sembol', '')} | {T('Miktar:', 'Amount:')} {miktar} | {T('Maliyet:', 'Cost:')} {maliyet:.2f} | {T('Güncel:', 'Current:')} {guncel:.2f} | {T('Toplam:', 'Total:')} {top_guncel:.2f} TL {durum_str}")
                item.setData(Qt.UserRole, p.get("id"))
                if fark > 0: item.setForeground(Qt.darkGreen if CURRENT_THEME == "light" else Qt.green)
                elif fark < 0: item.setForeground(Qt.darkRed if CURRENT_THEME == "light" else Qt.red)
                self.liste_portfoy.addItem(item)
                
        self.liste_borc.clear()
        for b in self.borclar:
            if isinstance(b, dict):
                tip_metni = "🟢 Alacak" if b.get("tip") == "alacak" else "🔴 Borç"
                item = QListWidgetItem(f"{tip_metni} | Kişi: {b.get('kisi')} | Tutar: {b.get('tutar'):.2f} TL")
                item.setData(Qt.UserRole, b.get("id"))
                item.setForeground(Qt.darkGreen if b.get("tip") == "alacak" else Qt.darkRed)
                self.liste_borc.addItem(item)
                
        self.varlik_listesini_guncelle()
        if hasattr(self, 'lbl_taksit_ozet'):
            self.lbl_taksit_ozet.setText(f"{T('Aylık Toplam Taksit Yükü:', 'Total Monthly Installment Load:')} {sum(t.get('aylik',0) for t in self.taksitler):.2f} TL")
        
        alacak = sum(b.get("tutar", 0) for b in self.borclar if b.get("tip") == "alacak")
        borc = sum(b.get("tutar", 0) for b in self.borclar if b.get("tip") == "borc")
        net = alacak - borc
        renk = "#28a745" if net >= 0 else "#e74c3c"
        durum = T("Alacaklıyız", "Creditor") if net >= 0 else T("Borçluyuz", "Debtor")
        if hasattr(self, 'lbl_borc_ozet'):
            self.lbl_borc_ozet.setText(f"{T('Toplam Alacak:', 'Total Receivables:')} {alacak:.2f} TL | {T('Toplam Borç:', 'Total Debt:')} {borc:.2f} TL | Net: <span style='color:{renk}'>{net:.2f} TL ({durum})</span>")
        
        self._add_empty_state(self.liste_gelir, T("Henüz bir gelir kaydı bulunmuyor...", "No income records yet..."))
        self._add_empty_state(self.liste_gider, T("Henüz bir gider kaydı bulunmuyor...", "No expense records yet..."))
        self._add_empty_state(self.liste_taksit, T("Aktif taksit bulunmuyor...", "No active installments..."))
        self._add_empty_state(self.liste_portfoy, T("Portföyünüz boş. Yeni varlık ekleyin...", "Portfolio is empty. Add new assets..."))
        self._add_empty_state(self.liste_borc, T("Borç/Alacak kaydı bulunmuyor...", "No debt/receivable records..."))

    def islem_ay_filtre_guncelle(self):
        if not hasattr(self, 'ay_filtre_combo'): return
        mevcut = self.ay_filtre_combo.currentText()
        aylar = set()
        for islem in self.islemler:
            if isinstance(islem, dict):
                aylar.add(f"{islem.get('yil')}-{islem.get('ay'):02d}")
        liste = sorted(list(aylar), reverse=True)
        
        self.ay_filtre_combo.blockSignals(True)
        self.ay_filtre_combo.clear()
        self.ay_filtre_combo.addItem(T("Tüm Zamanlar", "All Time"))
        self.ay_filtre_combo.addItems(liste)
        
        if mevcut in liste:
            self.ay_filtre_combo.setCurrentText(mevcut)
        else:
            self.ay_filtre_combo.setCurrentIndex(0)
            
        self.ay_filtre_combo.blockSignals(False)

    def islem_duzenle(self, item):
        if item.flags() == Qt.NoItemFlags: return
        islem_id = item.data(Qt.UserRole)
        idx = next((index for (index, d) in enumerate(self.islemler) if isinstance(d, dict) and d.get("id") == islem_id), None)
        if idx is None: return
        
        dialog = IslemDuzenleDialog(self, self.islemler[idx], self.suanki_ay)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.islem_silindi:
                del self.islemler[idx]
            self.veri_degisti()

    def taksit_duzenle(self, item):
        if item.flags() == Qt.NoItemFlags: return
        t_id = item.data(Qt.UserRole)
        idx = next((index for (index, d) in enumerate(self.taksitler) if isinstance(d, dict) and d.get("id") == t_id), None)
        if idx is None: return
        cevap = QMessageBox.question(self, T("Taksit İptali", "Cancel Installment"), T("Bu taksit ödemesini bitirmek/silmek istiyor musunuz?\n(Kart limitine iadesi yapılacaktır)", "Do you want to complete/delete this installment?\n(It will be refunded to card limit)"), QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            kart_id = self.taksitler[idx].get("kart_id", "")
            for k in self.kartlar:
                if k.get("id") == kart_id:
                    k["kullanilan"] = max(0, k["kullanilan"] - self.taksitler[idx].get("toplam", 0))
                    break
            del self.taksitler[idx]
            self.veri_degisti()

    def portfoy_duzenle(self, item):
        if item.flags() == Qt.NoItemFlags: return
        p_id = item.data(Qt.UserRole)
        idx = next((index for (index, d) in enumerate(self.portfoy) if isinstance(d, dict) and d.get("id") == p_id), None)
        if idx is None: return
        cevap = QMessageBox.question(self, T("Varlık Sil", "Delete Asset"), T("Bu yatırımı portföyden silmek istiyor musunuz?", "Delete this investment from portfolio?"), QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            del self.portfoy[idx]
            self.veri_degisti()

    def borc_sil(self, item):
        if item.flags() == Qt.NoItemFlags: return
        b_id = item.data(Qt.UserRole)
        idx = next((index for (index, d) in enumerate(self.borclar) if isinstance(d, dict) and d.get("id") == b_id), None)
        if idx is None: return
        cevap = QMessageBox.question(self, T("Sil / Ödendi", "Delete / Paid"), T("Bu borç/alacak kaydını ödenmiş sayıp silmek istiyor musunuz?", "Delete/Mark as paid?"), QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            del self.borclar[idx]
            self.veri_degisti()

    def aktif_taksit_hesapla(self, yil, ay):
        toplam = 0.0
        hedef_ay = yil * 12 + ay
        for t in self.taksitler:
            try:
                b_yil, b_ay = map(int, t.get("tarih", "2020-01").split("-"))
                baslangic_ayi = b_yil * 12 + b_ay
                vade = int(t.get("vade", 1))
                if baslangic_ayi <= hedef_ay < (baslangic_ayi + vade):
                    toplam += guvenli_float(t.get("aylik", 0))
            except: pass
        return toplam

    def toplam_odenen_taksit(self):
        suan_abs = self.suanki_ay.year * 12 + self.suanki_ay.month
        toplam = 0.0
        for t in self.taksitler:
            try:
                vade = int(t.get("vade", 1))
                aylik = guvenli_float(t.get("aylik", 0))
                b_yil, b_ay = map(int, t.get("tarih", "2020-01").split("-"))
                start_abs = b_yil * 12 + b_ay
                ay_farki = suan_abs - start_abs + 1
                odenen_ay = min(max(0, ay_farki), vade)
                toplam += odenen_ay * aylik
            except: pass
        return toplam

    def kategori_ekle(self):
        yeni, ok = QInputDialog.getText(self, T("Yeni Kategori", "New Category"), T("Adı:", "Name:"))
        if ok and yeni and yeni not in self.kategoriler:
            self.gelir_kategori.addItem(yeni)
            self.gider_kategori.addItem(yeni)
            self.kategoriler.append(yeni)
            self.veri_degisti()

    def islem_arayuzu_kur(self):
        duzen = QHBoxLayout(self.tab_islem)
        
        g_duzen = QVBoxLayout()
        self.g_grup = QGroupBox()
        g_form = QFormLayout(self.g_grup)
        self.gelir_kategori = QComboBox()
        btn_yeni_kg = QPushButton("+")
        btn_yeni_kg.setFixedWidth(35)
        btn_yeni_kg.clicked.connect(self.kategori_ekle)
        kg_satir = QHBoxLayout()
        kg_satir.setContentsMargins(0,0,0,0)
        kg_satir.addWidget(self.gelir_kategori)
        kg_satir.addWidget(btn_yeni_kg)
        self.gelir_aciklama = QLineEdit()
        self.gelir_tutar = QLineEdit()
        self.gelir_tarih = QDateEdit()
        self.gelir_tarih.setCalendarPopup(True)
        self.gelir_tarih.setDate(QDate.currentDate())
        self.gelir_sabit = QCheckBox()
        self.gelir_tutar.returnPressed.connect(self.gelir_ekle)
        self.btn_gelir = QPushButton()
        self.btn_gelir.setStyleSheet("background-color: #10b981; color: white; border: none;")
        self.btn_gelir.clicked.connect(self.gelir_ekle)
        
        self.lbl_g_kat = QLabel()
        self.lbl_g_acik = QLabel()
        self.lbl_g_tut = QLabel()
        self.lbl_g_tarih = QLabel()
        
        g_form.addRow(self.lbl_g_kat, kg_satir)
        g_form.addRow(self.lbl_g_acik, self.gelir_aciklama)
        g_form.addRow(self.lbl_g_tut, self.gelir_tutar)
        g_form.addRow(self.lbl_g_tarih, self.gelir_tarih)
        g_form.addRow("", self.gelir_sabit)
        g_form.addRow("", self.btn_gelir)
        
        self.liste_gelir = QListWidget()
        self.liste_gelir.itemDoubleClicked.connect(self.islem_duzenle)
        
        filtre_satir = QHBoxLayout()
        self.lbl_ay_filtre = QLabel()
        self.ay_filtre_combo = QComboBox()
        self.ay_filtre_combo.currentIndexChanged.connect(self.listeleri_guncelle)
        filtre_satir.addWidget(self.lbl_ay_filtre)
        filtre_satir.addWidget(self.ay_filtre_combo)
        
        g_duzen.addWidget(self.g_grup)
        g_duzen.addSpacing(10)
        g_duzen.addLayout(filtre_satir)
        
        lbl_ed1 = QLabel(T("(Düzenlemek için çift tıklayın)", "(Double click to edit)"))
        lbl_ed1.setStyleSheet("color: gray; font-style: italic; background-color: transparent; border: none;")
        g_duzen.addWidget(lbl_ed1)
        g_duzen.addWidget(self.liste_gelir)
        
        gi_duzen = QVBoxLayout()
        self.gi_grup = QGroupBox()
        gi_form = QFormLayout(self.gi_grup)
        self.gider_kategori = QComboBox()
        btn_yeni_kgi = QPushButton("+")
        btn_yeni_kgi.setFixedWidth(35)
        btn_yeni_kgi.clicked.connect(self.kategori_ekle)
        kgi_satir = QHBoxLayout()
        kgi_satir.setContentsMargins(0,0,0,0)
        kgi_satir.addWidget(self.gider_kategori)
        kgi_satir.addWidget(btn_yeni_kgi)
        self.gider_aciklama = QLineEdit()
        self.gider_tutar = QLineEdit()
        self.gider_tarih = QDateEdit()
        self.gider_tarih.setCalendarPopup(True)
        self.gider_tarih.setDate(QDate.currentDate())
        self.gider_sabit = QCheckBox()
        self.gider_tutar.returnPressed.connect(self.gider_ekle)
        self.btn_gider = QPushButton()
        self.btn_gider.setStyleSheet("background-color: #ef4444; color: white; border: none;")
        self.btn_gider.clicked.connect(self.gider_ekle)
        
        self.lbl_gi_kat = QLabel()
        self.lbl_gi_acik = QLabel()
        self.lbl_gi_tut = QLabel()
        self.lbl_gi_tarih = QLabel()
        
        gi_form.addRow(self.lbl_gi_kat, kgi_satir)
        gi_form.addRow(self.lbl_gi_acik, self.gider_aciklama)
        gi_form.addRow(self.lbl_gi_tut, self.gider_tutar)
        gi_form.addRow(self.lbl_gi_tarih, self.gider_tarih)
        gi_form.addRow("", self.gider_sabit)
        gi_form.addRow("", self.btn_gider)
        
        self.liste_gider = QListWidget()
        self.liste_gider.itemDoubleClicked.connect(self.islem_duzenle)
        
        gi_duzen.addWidget(self.gi_grup)
        gi_duzen.addSpacing(35)
        lbl_ed2 = QLabel(T("(Düzenlemek için çift tıklayın)", "(Double click to edit)"))
        lbl_ed2.setStyleSheet("color: gray; font-style: italic; background-color: transparent; border: none;")
        gi_duzen.addWidget(lbl_ed2)
        gi_duzen.addWidget(self.liste_gider)
        
        duzen.addLayout(g_duzen)
        duzen.addSpacing(15)
        duzen.addLayout(gi_duzen)

    def gelir_ekle(self):
        kat = self.gelir_kategori.currentText()
        aciklama = self.gelir_aciklama.text().strip()
        tutar = guvenli_float(self.gelir_tutar.text())
        sabit = self.gelir_sabit.isChecked()
        dt = self.gelir_tarih.date().toPyDate()
        if tutar > 0:
            islem = {
                "id": str(uuid.uuid4()),
                "tarih": dt.strftime("%Y-%m-%d"),
                "ay": dt.month,
                "yil": dt.year,
                "tip": "gelir",
                "kategori": kat,
                "aciklama": aciklama,
                "tutar": tutar,
                "sabit": sabit,
                "bitis_tarihi": None
            }
            self.islemler.append(islem)
            self.gelir_aciklama.clear()
            self.gelir_tutar.clear()
            self.veri_degisti()

    def gider_ekle(self):
        kat = self.gider_kategori.currentText()
        aciklama = self.gider_aciklama.text().strip()
        tutar = guvenli_float(self.gider_tutar.text())
        sabit = self.gider_sabit.isChecked()
        dt = self.gider_tarih.date().toPyDate()
        if tutar > 0:
            islem = {
                "id": str(uuid.uuid4()),
                "tarih": dt.strftime("%Y-%m-%d"),
                "ay": dt.month,
                "yil": dt.year,
                "tip": "gider",
                "kategori": kat,
                "aciklama": aciklama,
                "tutar": tutar,
                "sabit": sabit,
                "bitis_tarihi": None
            }
            self.islemler.append(islem)
            self.gider_aciklama.clear()
            self.gider_tutar.clear()
            self.veri_degisti()

    def taksit_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_taksit)
        self.t_grup = QGroupBox()
        form = QGridLayout(self.t_grup)
        self.taksit_kart_combo = QComboBox()
        self.taksit_urun = QLineEdit()
        self.taksit_tutar = QLineEdit()
        self.taksit_ay = QLineEdit()
        self.taksit_tarih = QDateEdit()
        self.taksit_tarih.setCalendarPopup(True)
        self.taksit_tarih.setDate(QDate.currentDate())
        self.taksit_ay.returnPressed.connect(self.taksit_ekle)
        self.btn_t_ekle = QPushButton()
        self.btn_t_ekle.setStyleSheet("background-color: #3b82f6; color: white; border: none;")
        self.btn_t_ekle.clicked.connect(self.taksit_ekle)
        
        self.lbl_t_kart = QLabel()
        self.lbl_t_urun = QLabel()
        self.lbl_t_tut = QLabel()
        self.lbl_t_ay = QLabel()
        self.lbl_t_tarih = QLabel()
        
        form.addWidget(self.lbl_t_kart, 0, 0)
        form.addWidget(self.taksit_kart_combo, 1, 0)
        form.addWidget(self.lbl_t_urun, 0, 1)
        form.addWidget(self.taksit_urun, 1, 1)
        form.addWidget(self.lbl_t_tut, 2, 0)
        form.addWidget(self.taksit_tutar, 3, 0)
        form.addWidget(self.lbl_t_ay, 2, 1)
        form.addWidget(self.taksit_ay, 3, 1)
        form.addWidget(self.lbl_t_tarih, 4, 0)
        form.addWidget(self.taksit_tarih, 4, 1)
        form.addWidget(self.btn_t_ekle, 5, 0, 1, 2)
        
        self.lbl_taksit_ozet = QLabel()
        self.lbl_taksit_ozet.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: transparent; border: none;")
        duzen.addWidget(self.lbl_taksit_ozet)
        
        self.liste_taksit = QListWidget()
        self.liste_taksit.itemDoubleClicked.connect(self.taksit_duzenle)
        
        duzen.addWidget(self.t_grup)
        duzen.addSpacing(10)
        
        lbl_ipt = QLabel(T("(İptal etmek için çift tıklayın)", "(Double click to cancel)"))
        lbl_ipt.setStyleSheet("color: gray; font-style: italic; background-color: transparent; border: none;")
        duzen.addWidget(lbl_ipt)
        duzen.addWidget(self.liste_taksit)

    def taksit_ekle(self):
        if not hasattr(self, 'taksit_kart_combo'): return
        kart_id = self.taksit_kart_combo.currentData()
        kart_ad = self.taksit_kart_combo.currentText()
        if not kart_id: return
        urun = self.taksit_urun.text().strip()
        tutar = guvenli_float(self.taksit_tutar.text())
        dt = self.taksit_tarih.date().toPyDate()
        if tutar > 0 and urun:
            try: ay = int(self.taksit_ay.text())
            except: ay = 1
            if ay < 1: ay = 1
            aylik = tutar / ay
            
            k_obj = next((k for k in self.kartlar if k["id"] == kart_id), None)
            if k_obj:
                if tutar > (k_obj["limit"] - k_obj["kullanilan"]):
                    cevap = QMessageBox.question(self, T("Limit Aşımı", "Limit Exceeded"), T("Kart limitiniz yetersiz! Yine de eklensin mi?", "Card limit insufficient! Add anyway?"), QMessageBox.Yes | QMessageBox.No)
                    if cevap == QMessageBox.No: return
                k_obj["kullanilan"] += tutar
                
            taksit = {
                "id": str(uuid.uuid4()),
                "kart_id": kart_id,
                "kart": kart_ad,
                "urun": urun,
                "vade": ay,
                "aylik": aylik,
                "toplam": tutar,
                "tarih": dt.strftime("%Y-%m")
            }
            self.taksitler.append(taksit)
            self.taksit_urun.clear()
            self.taksit_tutar.clear()
            self.taksit_ay.clear()
            self.veri_degisti()

    def kart_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_kartlar)
        self.kart_scroll = QScrollArea()
        self.kart_scroll.setWidgetResizable(True)
        self.kart_icerik = QWidget()
        self.kart_grid = QGridLayout(self.kart_icerik)
        self.kart_scroll.setWidget(self.kart_icerik)
        duzen.addWidget(self.kart_scroll)
        
    def kart_gridini_ciz(self):
        if not hasattr(self, 'kart_grid'): return
        for i in reversed(range(self.kart_grid.count())): 
            w = self.kart_grid.itemAt(i).widget()
            if w: w.setParent(None)
            
        row, col = 0, 0
        for kart in self.kartlar:
            wrapper = QWidget()
            w_duz = QVBoxLayout(wrapper)
            
            kutu = QFrame()
            is_dark = CURRENT_THEME == "dark"
            bg1 = "#1e293b" if is_dark else "#0f766e"
            bg2 = "#0f172a" if is_dark else "#042f2e"
            kutu.setStyleSheet(f"QFrame {{ border-radius: 12px; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {bg1}, stop:1 {bg2}); padding: 15px; margin: 5px; border: none; }}")
            
            k_duz = QVBoxLayout(kutu)
            
            header = QHBoxLayout()
            lbl_ad = QLabel(kart.get("ad", "Banka"))
            lbl_ad.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 16px; background-color: transparent; border: none;")
            lbl_chip = QLabel(kart.get("tip", "Visa") + " 💳")
            lbl_chip.setStyleSheet("font-size: 16px; color: #cbd5e1; font-weight: bold; font-style: italic; background-color: transparent; border: none;")
            header.addWidget(lbl_ad)
            header.addStretch()
            header.addWidget(lbl_chip)
            
            lbl_no = QLabel("**** **** **** " + kart.get("no_gizli", "0000"))
            lbl_no.setStyleSheet("color: white; font-size: 18px; font-weight: bold; letter-spacing: 2px; background-color: transparent; border: none;")
            
            detay_satir = QHBoxLayout()
            lbl_skt = QLabel("SKT: **/**")
            lbl_cvv = QLabel("CVV: ***")
            lbl_skt.setStyleSheet("color: #cbd5e1; background-color: transparent; border: none;")
            lbl_cvv.setStyleSheet("color: #cbd5e1; background-color: transparent; border: none;")
            detay_satir.addWidget(lbl_skt)
            detay_satir.addWidget(lbl_cvv)
            detay_satir.addStretch()
            
            btn_goz = QPushButton("👁")
            btn_goz.setFixedSize(32, 32)
            btn_goz.setStyleSheet("background-color: transparent; border: 1px solid #cbd5e1; border-radius: 4px; color: white; padding: 0px;")
            btn_goz.clicked.connect(lambda checked, k=kart, ln=lbl_no, ls=lbl_skt, lc=lbl_cvv: self.kart_bilgi_goster(k, ln, ls, lc))
            detay_satir.addWidget(btn_goz)
            
            k_duz.addLayout(header)
            k_duz.addSpacing(15)
            k_duz.addWidget(lbl_no)
            k_duz.addLayout(detay_satir)
            
            w_duz.addWidget(kutu)
            
            lim = kart.get("limit", 0)
            kul = kart.get("kullanilan", 0)
            kalan = lim - kul
            lbl_detay = QLabel(f"{T('Limit:', 'Limit:')} {lim:.2f} | {T('Kalan:', 'Left:')} {kalan:.2f}")
            lbl_detay.setStyleSheet("font-size: 12px; color: gray; background-color: transparent; border: none;")
            lbl_detay.setAlignment(Qt.AlignCenter)
            
            btn_satir = QHBoxLayout()
            btn_ode = QPushButton(T("Borç Öde", "Pay Debt"))
            btn_ode.setStyleSheet("background-color: #28a745; color: white; padding: 5px; border: none;")
            btn_ode.clicked.connect(lambda checked, k=kart: self.tekil_kart_ode(k))
            
            btn_duzenle = QPushButton(T("Düzenle", "Edit"))
            btn_duzenle.setStyleSheet("background-color: #f39c12; color: white; padding: 5px; border: none;")
            btn_duzenle.clicked.connect(lambda checked, k=kart: self.tekil_kart_duzenle(k))
            
            btn_sil = QPushButton(T("Sil", "Delete"))
            btn_sil.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px; border: none;")
            btn_sil.clicked.connect(lambda checked, k=kart: self.tekil_kart_sil(k))
            
            btn_satir.addWidget(btn_ode); btn_satir.addWidget(btn_duzenle); btn_satir.addWidget(btn_sil)
            
            w_duz.addWidget(lbl_detay)
            w_duz.addLayout(btn_satir)
            
            self.kart_grid.addWidget(wrapper, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        btn_ekle = QPushButton("+\n" + T("Yeni Kart Ekle", "Add New Card"))
        btn_ekle.setStyleSheet("font-size: 16px; font-weight: bold; border: 2px dashed #0ea5e9; border-radius: 8px; min-height: 150px; background-color: transparent; color: #0ea5e9;")
        btn_ekle.clicked.connect(self.yeni_kart_ekle)
        self.kart_grid.addWidget(btn_ekle, row, col)

    def kart_bilgi_goster(self, kart, ln, ls, lc):
        if "****" in ln.text():
            try:
                no = sifre_coz(kart.get("no", ""))
                skt = sifre_coz(kart.get("skt", "**/**"))
                cvv = sifre_coz(kart.get("cvv", "***"))
                fmt_no = " ".join([no[i:i+4] for i in range(0, len(no), 4)]) if len(no) == 16 else no
                ln.setText(fmt_no)
                ls.setText(f"SKT: {skt}")
                lc.setText(f"CVV: {cvv}")
            except: pass
        else:
            ln.setText("**** **** **** " + kart.get("no_gizli", "0000"))
            ls.setText("SKT: **/**")
            lc.setText("CVV: ***")

    def yeni_kart_ekle(self):
        diyalog = KartEkleDialog(self)
        if diyalog.exec_() == QDialog.Accepted:
            ad = diyalog.ad.text().strip()
            tip = diyalog.tip.currentText()
            no_temiz = diyalog.no.text().replace(" ", "")
            skt_temiz = diyalog.skt.text().replace("/", "")
            skt_fmt = f"{skt_temiz[:2]}/{skt_temiz[2:]}" if len(skt_temiz)==4 else skt_temiz
            cvv_temiz = diyalog.cvv.text()
            limit = guvenli_float(diyalog.limit.text())
            
            self.kartlar.append({
                "id": str(uuid.uuid4()),
                "ad": ad,
                "tip": tip,
                "no": sifrele(no_temiz),
                "no_gizli": no_temiz[-4:] if len(no_temiz)>=4 else "0000",
                "skt": sifrele(skt_fmt),
                "cvv": sifrele(cvv_temiz),
                "limit": limit,
                "kullanilan": 0.0
            })
            self.veri_degisti()
            self.kart_gridini_ciz()

    def tekil_kart_duzenle(self, kart):
        diyalog = KartEkleDialog(self, kart)
        if diyalog.exec_() == QDialog.Accepted:
            kart["ad"] = diyalog.ad.text().strip()
            kart["tip"] = diyalog.tip.currentText()
            no_temiz = diyalog.no.text().replace(" ", "")
            kart["no"] = sifrele(no_temiz)
            kart["no_gizli"] = no_temiz[-4:] if len(no_temiz)>=4 else "0000"
            
            skt_temiz = diyalog.skt.text().replace("/", "")
            skt_fmt = f"{skt_temiz[:2]}/{skt_temiz[2:]}" if len(skt_temiz)==4 else skt_temiz
            kart["skt"] = sifrele(skt_fmt)
            kart["cvv"] = sifrele(diyalog.cvv.text())
            kart["limit"] = guvenli_float(diyalog.limit.text())
            
            self.veri_degisti()
            self.kart_gridini_ciz()

    def tekil_kart_ode(self, kart):
        max_borc = kart.get("kullanilan", 0)
        if max_borc <= 0:
            QMessageBox.information(self, T("Bilgi", "Info"), T("Bu kartın borcu yok.", "No debt on this card."))
            return
            
        diyalog = ManuelFiyatDiyalog(self, f"{kart['ad']} {T('Borcu Ödemesi (Maks:', 'Debt Payment (Max:')} {max_borc:.2f} TL)")
        if diyalog.exec_() == QDialog.Accepted and diyalog.fiyat > 0:
            odeme = min(diyalog.fiyat, max_borc)
            kart["kullanilan"] -= odeme
            islem = {
                "id": str(uuid.uuid4()),
                "tarih": datetime.now().strftime("%Y-%m-%d"),
                "ay": datetime.now().month,
                "yil": datetime.now().year,
                "tip": "gider",
                "kategori": T("Diğer", "Other"),
                "aciklama": f"{kart['ad']} {T('Ödemesi', 'Payment')}",
                "tutar": odeme,
                "sabit": False
            }
            self.islemler.append(islem)
            self.veri_degisti()
            self.kart_gridini_ciz()

    def tekil_kart_sil(self, kart):
        cevap = QMessageBox.question(self, T("Emin misiniz?", "Are you sure?"), T(f"{kart['ad']} kartını silmek istiyor musunuz?", f"Delete card {kart['ad']}?"), QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            self.kartlar = [k for k in self.kartlar if k["id"] != kart["id"]]
            self.veri_degisti()
            self.kart_gridini_ciz()

    def varlik_listesini_guncelle(self):
        if hasattr(self, 'taksit_kart_combo'):
            self.taksit_kart_combo.clear()
            for kart in self.kartlar:
                self.taksit_kart_combo.addItem(kart.get("ad", ""), kart.get("id", ""))

    def hedef_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_hedefler)
        ust = QHBoxLayout()
        self.btn_hedef_ekle = QPushButton("+ " + T("Yeni Hedef Ekle", "Add New Goal"))
        self.btn_hedef_ekle.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border: none;")
        self.btn_hedef_ekle.clicked.connect(self.hedef_ekle)
        ust.addWidget(self.btn_hedef_ekle)
        ust.addStretch()
        
        self.hedef_scroll = QScrollArea()
        self.hedef_scroll.setWidgetResizable(True)
        self.hedef_icerik = QWidget()
        self.hedef_grid = QGridLayout(self.hedef_icerik)
        self.hedef_scroll.setWidget(self.hedef_icerik)
        
        self.lbl_hedef_ozet = QLabel()
        self.lbl_hedef_ozet.setStyleSheet("font-size: 14px; font-weight: bold; color: #d4af37; background-color: transparent; border: none;")
        duzen.addLayout(ust)
        duzen.addWidget(self.lbl_hedef_ozet)
        duzen.addWidget(self.hedef_scroll)

    def hedef_gridini_ciz(self):
        if not hasattr(self, 'hedef_grid'): return
        for i in reversed(range(self.hedef_grid.count())): 
            w = self.hedef_grid.itemAt(i).widget()
            if w: w.setParent(None)
            
        row, col = 0, 0
        for h in self.hedefler:
            kutu = QGroupBox(h.get("ad", "Hedef"))
            k_duz = QVBoxLayout(kutu)
            
            hedef = h.get("hedef", 1)
            biriken = h.get("biriken", 0)
            oran = int((biriken / hedef) * 100) if hedef > 0 else 0
            
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(min(oran, 100))
            
            bar_bg = "#1e293b" if CURRENT_THEME == "dark" else "#f1f5f9"
            bar_color = "#28a745" if oran >= 100 else "#3b82f6"
            text_color = "white" if CURRENT_THEME == "dark" else "black"
            
            bar.setStyleSheet(f"""
                QProgressBar {{ border: 1px solid gray; border-radius: 5px; text-align: center; color: {text_color}; background-color: {bar_bg}; min-height: 20px; }}
                QProgressBar::chunk {{ background-color: {bar_color}; border-radius: 4px; }}
            """)
            
            lbl = QLabel(f"<b>Biriken:</b> {biriken:.2f} TL / {hedef:.2f} TL")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background-color: transparent; border: none;")
            
            btn_ekle = QPushButton(T("Para Ekle", "Add Funds"))
            btn_ekle.setStyleSheet("background-color: #10b981; color: white; padding: 5px; border: none;")
            btn_ekle.clicked.connect(lambda checked, hedef_obj=h: self.hedefe_para_ekle(hedef_obj))
            
            btn_sil = QPushButton(T("Sil", "Delete"))
            btn_sil.setStyleSheet("background-color: #ef4444; color: white; padding: 5px; border: none;")
            btn_sil.clicked.connect(lambda checked, hedef_obj=h: self.hedef_sil(hedef_obj))
            
            h_alt = QHBoxLayout()
            h_alt.addWidget(btn_ekle); h_alt.addWidget(btn_sil)
            
            k_duz.addWidget(bar)
            k_duz.addWidget(lbl)
            k_duz.addLayout(h_alt)
            
            self.hedef_grid.addWidget(kutu, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        top_hedef = sum(h.get("hedef", 0) for h in self.hedefler)
        top_biriken = sum(h.get("biriken", 0) for h in self.hedefler)
        if hasattr(self, 'lbl_hedef_ozet'):
            self.lbl_hedef_ozet.setText(f"{T('Tüm Hedefler İçin Toplam Biriken:', 'Total Saved for All Goals:')} {top_biriken:.2f} TL / {top_hedef:.2f} TL")
        
        if len(self.hedefler) == 0:
            bos_lbl = QLabel(T("Henüz bir hedefiniz yok. Yeni bir hedef ekleyerek birikime başlayın...", "No goals yet. Start saving by adding a new goal..."))
            bos_lbl.setAlignment(Qt.AlignCenter)
            bos_lbl.setStyleSheet("color: gray; font-style: italic; font-size: 14px; background-color: transparent; border: none;")
            self.hedef_grid.addWidget(bos_lbl, 0, 0)

    def hedef_ekle(self):
        ad, ok1 = QInputDialog.getText(self, T("Yeni Hedef", "New Goal"), T("Hedef Adı (Örn: Araba):", "Goal Name:"))
        if not (ok1 and ad): return
        tutar_str, ok2 = QInputDialog.getText(self, T("Yeni Hedef", "New Goal"), T("Hedeflenen Tutar (TL):", "Target Amount (TL):"))
        if not (ok2 and tutar_str): return
        
        self.hedefler.append({
            "id": str(uuid.uuid4()),
            "ad": ad,
            "hedef": guvenli_float(tutar_str),
            "biriken": 0.0
        })
        self.veri_degisti()
        self.hedef_gridini_ciz()

    def hedefe_para_ekle(self, h):
        kalan = h["hedef"] - h["biriken"]
        diyalog = ManuelFiyatDiyalog(self, f"{h['ad']} {T('hedefine eklenecek tutar (Kalan:', 'amount to add (Left:')} {kalan:.2f} TL)")
        if diyalog.exec_() == QDialog.Accepted and diyalog.fiyat > 0:
            h["biriken"] += diyalog.fiyat
            if h["biriken"] >= h["hedef"]:
                QMessageBox.information(self, "Tebrikler!", f"🎉 {h['ad']} hedefine ulaştınız!")
            self.veri_degisti()
            self.hedef_gridini_ciz()

    def hedef_sil(self, h):
        self.hedefler = [x for x in self.hedefler if x["id"] != h["id"]]
        self.veri_degisti()
        self.hedef_gridini_ciz()

    def borc_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_borclar)
        form = QHBoxLayout()
        self.borc_kisi = QLineEdit()
        self.borc_kisi.setPlaceholderText(T("Kişi Adı", "Person Name"))
        self.borc_tutar = QLineEdit()
        self.borc_tutar.setPlaceholderText(T("Tutar (TL)", "Amount (TL)"))
        self.borc_tip = QComboBox()
        self.borc_tip.addItems(["Borç Aldım (Ödeyeceğim)", "Borç Verdim (Alacağım var)"])
        
        btn_ekle = QPushButton(T("Deftere Yaz", "Add to Book"))
        btn_ekle.setStyleSheet("background-color: #0ea5e9; color: white; border: none;")
        btn_ekle.clicked.connect(self.borc_ekle)
        
        form.addWidget(self.borc_kisi)
        form.addWidget(self.borc_tutar)
        form.addWidget(self.borc_tip)
        form.addWidget(btn_ekle)
        
        self.lbl_borc_ozet = QLabel()
        self.lbl_borc_ozet.setStyleSheet("font-size: 15px; font-weight: bold; background-color: transparent; border: none;")
        
        self.liste_borc = QListWidget()
        self.liste_borc.itemDoubleClicked.connect(self.borc_sil)
        
        duzen.addLayout(form)
        duzen.addWidget(self.lbl_borc_ozet)
        
        lbl_ipt = QLabel(T("(Ödendi işaretlemek / silmek için çift tıklayın)", "(Double click to mark as paid/delete)"))
        lbl_ipt.setStyleSheet("color: gray; font-style: italic; background-color: transparent; border: none;")
        duzen.addWidget(lbl_ipt)
        duzen.addWidget(self.liste_borc)

    def borc_ekle(self):
        kisi = self.borc_kisi.text().strip()
        tutar = guvenli_float(self.borc_tutar.text())
        tip = "alacak" if "Verdim" in self.borc_tip.currentText() else "borc"
        if tutar > 0 and kisi:
            self.borclar.append({
                "id": str(uuid.uuid4()),
                "kisi": kisi,
                "tutar": tutar,
                "tip": tip
            })
            self.borc_kisi.clear(); self.borc_tutar.clear()
            self.veri_degisti()

    def varlik_arayuzu_kur(self):
        duzen = QHBoxLayout(self.tab_varliklar)
        p_duzen = QVBoxLayout()
        self.p_grup = QGroupBox(T("Portföy (Yatırımlar)", "Portfolio (Investments)"))
        p_form = QFormLayout(self.p_grup)
        self.p_tip = QComboBox()
        self.p_tip.addItems([T("Hisse Senedi", "Stock"), T("Altın (Gram)", "Gold (Gram)"), T("Gümüş (Gram)", "Silver (Gram)")])
        self.p_tip.currentTextChanged.connect(self.portfoy_tip_degisti)
        self.p_sembol_lbl = QLabel(T("Sembol/Ad (Örn: THYAO):", "Symbol/Name (Ex: AAPL):"))
        self.p_sembol = QLineEdit()
        self.p_miktar = QLineEdit()
        self.p_miktar.setPlaceholderText(T("Lot veya Gram", "Amount"))
        self.lbl_p_mal = QLabel(T("Alış Maliyeti:", "Cost Price:"))
        self.p_maliyet = QLineEdit()
        self.p_maliyet.setPlaceholderText(T("Birim Başına Maliyet (Opsiyonel)", "Cost Per Unit (Optional)"))
        self.p_miktar.returnPressed.connect(self.portfoy_ekle)
        self.btn_p = QPushButton(T("Canlı Fiyatla Ekle", "Add w/ Live Price"))
        self.btn_p.setStyleSheet("background-color: #8b5cf6; color: white; border: none;")
        self.btn_p.clicked.connect(self.portfoy_ekle)
        
        self.lbl_p_tur = QLabel(T("Varlık Türü:", "Asset Type:"))
        self.lbl_p_mik = QLabel(T("Miktar:", "Amount:"))
        
        p_form.addRow(self.lbl_p_tur, self.p_tip)
        p_form.addRow(self.p_sembol_lbl, self.p_sembol)
        p_form.addRow(self.lbl_p_mik, self.p_miktar)
        p_form.addRow(self.lbl_p_mal, self.p_maliyet)
        p_form.addRow("", self.btn_p)
        
        self.liste_portfoy = QListWidget()
        self.liste_portfoy.itemDoubleClicked.connect(self.portfoy_duzenle)
        
        p_duzen.addWidget(self.p_grup)
        p_duzen.addSpacing(10)
        self.lbl_p_mevcut = QLabel(T("Mevcut Varlıklar:", "Current Assets:"))
        p_duzen.addWidget(self.lbl_p_mevcut)
        
        lbl_ipt = QLabel(T("(Silmek için çift tıklayın)", "(Double click to delete)"))
        lbl_ipt.setStyleSheet("color: gray; font-style: italic; background-color: transparent; border: none;")
        p_duzen.addWidget(lbl_ipt)
        
        p_duzen.addWidget(self.liste_portfoy)
        duzen.addLayout(p_duzen)

    def portfoy_tip_degisti(self, tip):
        if not hasattr(self, 'p_sembol_lbl'): return
        if tip in [T("Hisse Senedi", "Stock"), "Hisse Senedi", "Stock"]:
            self.p_sembol_lbl.show()
            self.p_sembol.show()
        else:
            self.p_sembol_lbl.hide()
            self.p_sembol.hide()

    def sembol_bul(self, arama, tip):
        if tip not in [T("Hisse Senedi", "Stock"), "Hisse Senedi", "Stock"]:
            return tip.split(" ")[0]
            
        arama = arama.strip()
        if not arama: return ""
        try:
            import urllib.request
            import urllib.parse
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(arama)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                quotes = data.get('quotes', [])
                if quotes:
                    for q in quotes:
                        if CURRENT_LANG == "tr" and q.get('exchange') == 'IST': return q['symbol']
                    return quotes[0]['symbol']
        except: pass
        ticker = arama.upper()
        if CURRENT_LANG == "tr" and not ticker.endswith(".IS"): ticker += ".IS"
        return ticker

    def canli_fiyat_cek(self, tip, sembol):
        if not YFINANCE_AVAILABLE: return -1
        try:
            if tip in [T("Hisse Senedi", "Stock"), "Hisse Senedi", "Stock"]:
                return yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1]
            elif "Altın" in tip or "Gold" in tip:
                usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
                gold_oz = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
                return (gold_oz / 31.1035) * usd_try
            elif "Gümüş" in tip or "Silver" in tip:
                usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
                silver_oz = yf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
                return (silver_oz / 31.1035) * usd_try
        except: return -1

    def portfoy_ekle(self):
        tip = self.p_tip.currentText()
        miktar = guvenli_float(self.p_miktar.text())
        if miktar <= 0: return
        
        sembol_ham = self.p_sembol.text()
        sembol = self.sembol_bul(sembol_ham, tip)
        if not sembol: return
        
        fiyat = self.canli_fiyat_cek(tip, sembol)
        if fiyat == -1:
            diyalog = ManuelFiyatDiyalog(self, f"{sembol} {T('güncel fiyatını girin:', 'current price:')}")
            if diyalog.exec_() == QDialog.Accepted and diyalog.fiyat > 0:
                fiyat = diyalog.fiyat
            else: return
            
        maliyet = guvenli_float(self.p_maliyet.text())
        if maliyet <= 0: maliyet = fiyat
            
        bulundu = False
        for p in self.portfoy:
            if isinstance(p, dict) and p.get("sembol") == sembol:
                eski_top_maliyet = p.get("maliyet", p.get("fiyat", 0)) * p.get("miktar", 0)
                yeni_ek_maliyet = maliyet * miktar
                toplam_miktar = p["miktar"] + miktar
                p["maliyet"] = (eski_top_maliyet + yeni_ek_maliyet) / toplam_miktar
                p["miktar"] = toplam_miktar
                p["fiyat"] = fiyat
                bulundu = True
                break
                
        if not bulundu:
            self.portfoy.append({"id": str(uuid.uuid4()), "sembol": sembol, "miktar": miktar, "fiyat": fiyat, "maliyet": maliyet, "tip": tip})
            
        self.p_sembol.clear()
        self.p_miktar.clear()
        self.p_maliyet.clear()
        self.veri_degisti()

    def aylik_analiz_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_aylik_analiz)
        nav_duzen = QHBoxLayout()
        self.btn_onceki_ay = QPushButton("◀")
        self.btn_onceki_ay.setFixedWidth(50)
        self.btn_onceki_ay.clicked.connect(self.onceki_aya_git)
        self.ay_lbl = QLabel()
        self.ay_lbl.setAlignment(Qt.AlignCenter)
        self.ay_lbl.setStyleSheet("font-size: 15px; font-weight: bold; background-color: transparent; border: none;")
        self.btn_sonraki_ay = QPushButton("▶")
        self.btn_sonraki_ay.setFixedWidth(50)
        self.btn_sonraki_ay.clicked.connect(self.sonraki_aya_git)
        nav_duzen.addWidget(self.btn_onceki_ay)
        nav_duzen.addStretch()
        nav_duzen.addWidget(self.ay_lbl)
        nav_duzen.addStretch()
        nav_duzen.addWidget(self.btn_sonraki_ay)
        
        self.grafik_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        
        self.btn_excel = QPushButton(T("📊 Excel Detaylı Rapor Al", "📊 Export Detail to Excel"))
        self.btn_excel.setStyleSheet("background-color: #0284c7; color: white; padding: 12px; border: none;")
        self.btn_excel.clicked.connect(self.excel_disa_aktar)
        
        duzen.addLayout(nav_duzen)
        duzen.addWidget(self.grafik_canvas)
        duzen.addSpacing(10)
        duzen.addWidget(self.btn_excel)

    def onceki_aya_git(self):
        self.suanki_ay = self.suanki_ay - timedelta(days=28)
        self.suanki_ay = self.suanki_ay.replace(day=1)
        self.aylik_analiz_guncelle()

    def sonraki_aya_git(self):
        if self.suanki_ay.month == 12:
            self.suanki_ay = self.suanki_ay.replace(year=self.suanki_ay.year+1, month=1)
        else:
            self.suanki_ay = self.suanki_ay.replace(month=self.suanki_ay.month+1)
        self.aylik_analiz_guncelle()

    def aylik_analiz_guncelle(self):
        if not hasattr(self, 'ay_lbl'): return
        ay = self.suanki_ay.month
        yil = self.suanki_ay.year
        
        ay_adi = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        if CURRENT_LANG == "en":
            ay_adi = ["", "January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
        self.ay_lbl.setText(f"{ay_adi[ay]} {yil}")
        self.grafik_ciz(yil, ay)

    def islem_hesapla(self, tip, yil, ay):
        toplam = 0.0
        hedef_abs = yil * 12 + ay
        for i in self.islemler:
            if not isinstance(i, dict) or i.get("tip") != tip: continue
            tutar = guvenli_float(i.get("tutar", 0))
            is_sabit = i.get("sabit", False)
            i_abs = i.get("yil") * 12 + i.get("ay")
            
            if is_sabit:
                if hedef_abs >= i_abs:
                    bitis = i.get("bitis_tarihi")
                    if bitis:
                        b_yil, b_ay = map(int, bitis.split("-"))
                        b_abs = b_yil * 12 + b_ay
                        if hedef_abs <= b_abs:
                            toplam += tutar
                    else:
                        toplam += tutar
            else:
                if i_abs == hedef_abs:
                    toplam += tutar
        return toplam

    def grafik_ciz(self, yil, ay):
        self.grafik_canvas.figure.clear()
        gs = self.grafik_canvas.figure.add_gridspec(2, 2)
        ax_bar = self.grafik_canvas.figure.add_subplot(gs[0, 0])
        ax_pie = self.grafik_canvas.figure.add_subplot(gs[0, 1])
        ax_line = self.grafik_canvas.figure.add_subplot(gs[1, :])
        
        is_dark = CURRENT_THEME == "dark"
        text_color = "#e2e8f0" if is_dark else "#1e293b"
        bg_color = "#0f172a" if is_dark else "#f1f5f9"
        ax_bg = "#1e293b" if is_dark else "#ffffff"
        grid_color = "#334155" if is_dark else "#cbd5e1"
        spine_color = "#334155" if is_dark else "#cbd5e1"
        
        self.grafik_canvas.figure.patch.set_facecolor(bg_color)
        for ax in [ax_bar, ax_pie, ax_line]:
            ax.set_facecolor(ax_bg)
            for spine in ax.spines.values():
                spine.set_color(spine_color)
            ax.tick_params(colors=text_color)
        
        aylik_gelir = self.islem_hesapla("gelir", yil, ay)
        normal_gider = self.islem_hesapla("gider", yil, ay)
        taksit_tutar = self.aktif_taksit_hesapla(yil, ay)
        
        ax_bar.bar([T("Gelir", "Income")], [aylik_gelir], color="#28a745", edgecolor=spine_color)
        ax_bar.bar([T("Gider", "Expense")], [normal_gider], color="#e74c3c", edgecolor=spine_color, label="Normal")
        ax_bar.bar([T("Gider", "Expense")], [taksit_tutar], bottom=[normal_gider], color="#922b21", edgecolor=spine_color, label="Taksit")
        
        ax_bar.set_title(T("Aylık Bilanço", "Monthly Balance"), color=text_color, fontweight="bold")
        ax_bar.grid(axis="y", alpha=0.3, color=grid_color, linestyle="--")
        if normal_gider > 0 or taksit_tutar > 0:
            ax_bar.legend(loc='upper right', fontsize=8, facecolor=ax_bg, edgecolor=spine_color, labelcolor=text_color)
        
        kategoriler_toplam = {}
        hedef_abs = yil * 12 + ay
        for i in self.islemler:
            if isinstance(i, dict) and i.get("tip") == "gider":
                i_abs = i.get("yil") * 12 + i.get("ay")
                ekle = False
                if i.get("sabit"):
                    if hedef_abs >= i_abs:
                        b = i.get("bitis_tarihi")
                        if b:
                            b_yil, b_ay = map(int, b.split("-"))
                            if hedef_abs <= (b_yil*12+b_ay): ekle = True
                        else: ekle = True
                else:
                    if i_abs == hedef_abs: ekle = True
                if ekle:
                    k = i.get("kategori", "Diğer")
                    kategoriler_toplam[k] = kategoriler_toplam.get(k, 0) + guvenli_float(i.get("tutar", 0))
                    
        if taksit_tutar > 0: kategoriler_toplam[T("Taksitler", "Installments")] = taksit_tutar
        
        if kategoriler_toplam:
            labels = list(kategoriler_toplam.keys())
            sizes = list(kategoriler_toplam.values())
            wedges, texts, autotexts = ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'color': text_color, 'fontsize': 8})
            centre_circle = plt.Circle((0,0),0.65, fc=ax_bg)
            ax_pie.add_artist(centre_circle)
            ax_pie.set_title(T("Gider Dağılımı", "Expense Breakdown"), color=text_color, fontweight="bold")
        else:
            ax_pie.text(0.5, 0.5, T("Veri Yok", "No Data"), ha='center', va='center', color=text_color)
            ax_pie.axis('off')
            
        aylar_str = []
        net_akis = []
        cur_y, cur_m = yil, ay
        for i in range(5, -1, -1):
            temp_m = cur_m - i
            temp_y = cur_y
            while temp_m <= 0:
                temp_m += 12
                temp_y -= 1
            aylar_str.append(f"{temp_m:02d}/{str(temp_y)[2:]}")
            
            t_gelir = self.islem_hesapla("gelir", temp_y, temp_m)
            t_gider = self.islem_hesapla("gider", temp_y, temp_m) + self.aktif_taksit_hesapla(temp_y, temp_m)
            net_akis.append(t_gelir - t_gider)
            
        ax_line.plot(aylar_str, net_akis, marker='o', color="#3498db", linewidth=2)
        ax_line.fill_between(aylar_str, net_akis, 0, where=[n >= 0 for n in net_akis], color="#28a745", alpha=0.3, interpolate=True)
        ax_line.fill_between(aylar_str, net_akis, 0, where=[n < 0 for n in net_akis], color="#e74c3c", alpha=0.3, interpolate=True)
        ax_line.set_title(T("Son 6 Ay Net Akış", "Last 6 Months Net Flow"), color=text_color, fontweight="bold")
        ax_line.grid(axis="both", alpha=0.3, color=grid_color, linestyle="--")
        
        self.grafik_canvas.figure.tight_layout()
        self.grafik_canvas.draw()

    def excel_disa_aktar(self):
        dosya, _ = QFileDialog.getSaveFileName(self, T("Kaydet", "Save"), f"{self.profil_adi}_Detayli_Rapor_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if dosya:
            try:
                with open(dosya, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f, delimiter=';')
                    
                    writer.writerow([T("--- AYLIK BİLANÇO ÖZETİ ---", "--- MONTHLY BALANCE SUMMARY ---")])
                    bu_ay_gelir = self.islem_hesapla("gelir", self.suanki_ay.year, self.suanki_ay.month)
                    bu_ay_gider = self.islem_hesapla("gider", self.suanki_ay.year, self.suanki_ay.month)
                    aktif_taksit = self.aktif_taksit_hesapla(self.suanki_ay.year, self.suanki_ay.month)
                    net_bakiye = bu_ay_gelir - (bu_ay_gider + aktif_taksit)
                    
                    writer.writerow([T("Aylık Gelir", "Monthly Income"), f"{bu_ay_gelir:.2f} TL".replace('.', ',')])
                    writer.writerow([T("Aylık Normal Gider", "Monthly Expense"), f"{bu_ay_gider:.2f} TL".replace('.', ',')])
                    writer.writerow([T("Aylık Taksit Yükü", "Monthly Installment Load"), f"{aktif_taksit:.2f} TL".replace('.', ',')])
                    writer.writerow([T("Kullanılabilir Net Bakiye", "Available Net Balance"), f"{net_bakiye:.2f} TL".replace('.', ',')])
                    writer.writerow([])
                    
                    writer.writerow([T("--- İŞLEMLER ---", "--- TRANSACTIONS ---")])
                    writer.writerow([T("Tarih", "Date"), T("Tür", "Type"), T("Kategori", "Category"), T("Açıklama", "Description"), T("Tutar (TL)", "Amount (TL)")])
                    for islem in sorted(self.islemler, key=lambda x: x.get("tarih", "") if isinstance(x, dict) else ""):
                        if isinstance(islem, dict):
                            tutar_formatted = f"{islem.get('tutar', 0.0):.2f}".replace('.', ',')
                            tip_str = "Sabit " + islem.get("tip", "").capitalize() if islem.get("sabit") else islem.get("tip", "").capitalize()
                            writer.writerow([islem.get("tarih", ""), tip_str, islem.get("kategori", ""), islem.get("aciklama", ""), tutar_formatted])
                            
                    writer.writerow([])
                    writer.writerow([T("--- KARTLAR VE BORÇ DURUMU ---", "--- CARDS AND DEBT STATUS ---")])
                    writer.writerow([T("Kart Adı", "Card Name"), T("Tip", "Network"), T("Limit", "Limit"), T("Kullanılan", "Used")])
                    for kart in self.kartlar:
                        if isinstance(kart, dict):
                            writer.writerow([kart.get("ad", ""), kart.get("tip", ""), f"{kart.get('limit', 0):.2f}".replace('.',','), f"{kart.get('kullanilan', 0):.2f}".replace('.',',')])
                            
                    writer.writerow([])
                    writer.writerow([T("--- KİŞİSEL BORÇ/ALACAK DEFTERİ ---", "--- PERSONAL DEBT/RECEIVABLE BOOK ---")])
                    writer.writerow([T("Kişi", "Person"), T("Tip", "Type"), T("Tutar", "Amount")])
                    for b in self.borclar:
                        if isinstance(b, dict):
                            writer.writerow([b.get("kisi", ""), T("Alacak", "Receivable") if b.get("tip") == "alacak" else T("Borç", "Debt"), f"{b.get('tutar', 0):.2f}".replace('.',',')])
                            
                    writer.writerow([])
                    writer.writerow([T("--- YATIRIM PORTFÖYÜ ---", "--- INVESTMENT PORTFOLIO ---")])
                    writer.writerow([T("Sembol", "Symbol"), T("Tip", "Type"), T("Miktar", "Amount"), T("Maliyet", "Cost"), T("Güncel Değer", "Current Value")])
                    for p in self.portfoy:
                        if isinstance(p, dict):
                            writer.writerow([p.get("sembol", ""), p.get("tip", ""), f"{p.get('miktar', 0):.2f}".replace('.',','), f"{p.get('maliyet', 0):.2f}".replace('.',','), f"{p.get('fiyat', 0):.2f}".replace('.',',')])
                            
                QMessageBox.information(self, T("Başarılı", "Success"), T("Detaylı Excel raporu tablosu başarıyla oluşturuldu!", "Detailed Excel report created successfully!"))
            except Exception as e:
                QMessageBox.warning(self, T("Hata", "Error"), f"{str(e)}")

    def ozet_arayuzu_kur(self):
        duzen = QVBoxLayout(self.tab_ozet)
        grid = QGridLayout()
        
        self.b_grup = QGroupBox()
        b_duzen = QVBoxLayout(self.b_grup)
        self.lbl_gelir = QLabel()
        self.lbl_gider = QLabel()
        self.lbl_taksit = QLabel()
        self.lbl_net = QLabel()
        
        self.lbl_gelir.setStyleSheet("background-color: transparent; border: none;")
        self.lbl_gider.setStyleSheet("background-color: transparent; border: none;")
        self.lbl_taksit.setStyleSheet("background-color: transparent; border: none;")
        self.lbl_net.setStyleSheet("font-size: 16px; font-weight:bold; background-color: transparent; border: none;")
        
        self.saglik_bar = QProgressBar()
        self.saglik_bar.setFixedHeight(22)
        self.lbl_tavsiye = QLabel()
        self.lbl_tavsiye.setStyleSheet("font-style: italic; background-color: transparent; border: none;")
        
        b_duzen.addWidget(self.lbl_gelir)
        b_duzen.addWidget(self.lbl_gider)
        b_duzen.addWidget(self.lbl_taksit)
        b_duzen.addWidget(QLabel("-" * 40))
        b_duzen.addWidget(self.lbl_net)
        b_duzen.addSpacing(10)
        b_duzen.addWidget(self.saglik_bar)
        b_duzen.addWidget(self.lbl_tavsiye)
        b_duzen.addStretch()
        
        self.s_grup = QGroupBox()
        s_duzen = QVBoxLayout(self.s_grup)
        self.lbl_servet_portfoy = QLabel()
        self.lbl_servet_kart = QLabel()
        self.lbl_servet_toplam = QLabel()
        
        self.lbl_servet_portfoy.setStyleSheet("background-color: transparent; border: none;")
        self.lbl_servet_kart.setStyleSheet("background-color: transparent; border: none;")
        self.lbl_servet_toplam.setStyleSheet("font-size: 18px; font-weight:bold; color: #28a745; text-align: center; background-color: transparent; border: none;")
        
        s_duzen.addStretch()
        s_duzen.addWidget(self.lbl_servet_portfoy, alignment=Qt.AlignCenter)
        s_duzen.addWidget(self.lbl_servet_kart, alignment=Qt.AlignCenter)
        s_duzen.addSpacing(15)
        s_duzen.addWidget(self.lbl_servet_toplam, alignment=Qt.AlignCenter)
        s_duzen.addStretch()
        
        grid.addWidget(self.b_grup, 0, 0)
        grid.addWidget(self.s_grup, 0, 1)
        
        alt_duzen = QHBoxLayout()
        self.btn_pdf = QPushButton()
        self.btn_pdf.setStyleSheet("background-color: #f59e0b; color: white; padding: 12px; border: none;")
        self.btn_pdf.clicked.connect(self.pdf_disa_aktar)
        
        self.btn_kaydet = QPushButton()
        self.btn_kaydet.setStyleSheet("background-color: #10b981; color: white; padding: 12px; border: none;")
        self.btn_kaydet.clicked.connect(lambda: self.profili_kaydet(sessiz=False))
        
        self.btn_hesap_sil = QPushButton()
        self.btn_hesap_sil.setStyleSheet("background-color: #ef4444; color: white; padding: 12px; border: none;")
        self.btn_hesap_sil.clicked.connect(self.hesabi_sil)
        
        alt_duzen.addWidget(self.btn_pdf)
        alt_duzen.addWidget(self.btn_kaydet)
        alt_duzen.addWidget(self.btn_hesap_sil)
        
        duzen.addLayout(grid)
        duzen.addSpacing(15)
        duzen.addLayout(alt_duzen)

    def ozeti_guncelle(self):
        if not hasattr(self, 'b_grup'): return
        self.b_grup.setTitle(T("Aylık Bütçe Disiplini", "Monthly Budget Discipline"))
        self.s_grup.setTitle(T("Finansal Karne (Tüm Zamanlar)", "Financial Scorecard (All Time)"))
        
        suan = datetime.now()
        yil, ay = suan.year, suan.month
        
        bu_ay_gelir = self.islem_hesapla("gelir", yil, ay)
        bu_ay_gider = self.islem_hesapla("gider", yil, ay)
        aktif_taksit = self.aktif_taksit_hesapla(yil, ay)
        
        self.lbl_gelir.setText(f"↑ {T('Aylık Gelir:', 'Monthly Income:')} {bu_ay_gelir:.2f} TL")
        self.lbl_gelir.setStyleSheet("color: #28a745; background-color: transparent; border: none;")
        
        self.lbl_gider.setText(f"↓ {T('Aylık Gider:', 'Monthly Expense:')} {bu_ay_gider:.2f} TL")
        self.lbl_gider.setStyleSheet("color: #e74c3c; background-color: transparent; border: none;")
        
        self.lbl_taksit.setText(f"💳 {T('Taksit Yükü:', 'Installment Load:')} {aktif_taksit:.2f} TL")
        self.lbl_taksit.setStyleSheet("background-color: transparent; border: none;")
        
        top_cikis = bu_ay_gider + aktif_taksit
        net = bu_ay_gelir - top_cikis
        self.lbl_net.setText(f"{T('Kullanılabilir Bakiye:', 'Available Balance:')} {net:.2f} TL")
        
        if net < 0:
            self.lbl_net.setStyleSheet("font-size: 16px; font-weight:bold; color: #e74c3c; background-color: transparent; border: none;")
        else:
            self.lbl_net.setStyleSheet("font-size: 16px; font-weight:bold; color: #28a745; background-color: transparent; border: none;")
        
        self.saglik_bar.setFormat(T("Bütçe Kullanımı: %p%", "Budget Usage: %p%"))
        durum_metni = ""
        if bu_ay_gelir > 0:
            oran = int((top_cikis / bu_ay_gelir) * 100)
            self.saglik_bar.setValue(min(oran, 100))
            
            bar_bg = "#1e293b" if CURRENT_THEME == "dark" else "#f1f5f9"
            text_color = "white" if CURRENT_THEME == "dark" else "black"
            bar_css = f"QProgressBar {{ border: 1px solid gray; border-radius: 5px; text-align: center; color: {text_color}; background-color: {bar_bg}; min-height: 20px; }}"
            
            if oran <= 40: 
                durum_metni = T("Harika birikim yapıyorsun, bütçe güvende!", "Great savings, safe budget!")
                self.saglik_bar.setStyleSheet(bar_css + " QProgressBar::chunk {background-color: #28a745; border-radius: 4px;}")
            elif oran <= 70: 
                durum_metni = T("Harcamalarına dikkat etmelisin, sınırda.", "Watch your spending, on the edge.")
                self.saglik_bar.setStyleSheet(bar_css + " QProgressBar::chunk {background-color: #f39c12; border-radius: 4px;}")
            else: 
                durum_metni = T("Kırmızı bölgedesin, acil tasarruf şart!", "Red zone, urgent savings needed!")
                self.saglik_bar.setStyleSheet(bar_css + " QProgressBar::chunk {background-color: #e74c3c; border-radius: 4px;}")
        else: self.saglik_bar.setValue(0)
        self.lbl_tavsiye.setText(durum_metni)
        self.lbl_tavsiye.setStyleSheet("font-style: italic; background-color: transparent; border: none;")
            
        portfoy_tl = 0.0
        for p in self.portfoy:
            if isinstance(p, dict):
                portfoy_tl += p.get('fiyat', 0) * p.get('miktar', 0)
            
        top_kart_borc = sum(k.get("kullanilan", 0) for k in self.kartlar if isinstance(k, dict))
        
        lifetime_gelir = sum(guvenli_float(i.get("tutar", 0)) for i in self.islemler if isinstance(i, dict) and i.get("tip") == "gelir" and not i.get("sabit"))
        lifetime_gider = sum(guvenli_float(i.get("tutar", 0)) for i in self.islemler if isinstance(i, dict) and i.get("tip") == "gider" and not i.get("sabit"))
        
        for i in self.islemler:
            if isinstance(i, dict) and i.get("sabit"):
                s_yil = i.get("yil")
                s_ay = i.get("ay")
                start_abs = s_yil * 12 + s_ay
                suan_abs = yil * 12 + ay
                
                bitis = i.get("bitis_tarihi")
                if bitis:
                    b_yil, b_ay = map(int, bitis.split("-"))
                    end_abs = b_yil * 12 + b_ay
                    gecen_ay = min(suan_abs, end_abs) - start_abs + 1
                else:
                    gecen_ay = suan_abs - start_abs + 1
                    
                if gecen_ay > 0:
                    if i.get("tip") == "gelir": lifetime_gelir += gecen_ay * guvenli_float(i.get("tutar", 0))
                    elif i.get("tip") == "gider": lifetime_gider += gecen_ay * guvenli_float(i.get("tutar", 0))
        
        lifetime_taksit = self.toplam_odenen_taksit()
        gercek_kalan_nakit = lifetime_gelir - (lifetime_gider + lifetime_taksit)
        
        self.lbl_servet_portfoy.setText(f"📈 {T('Yatırımlarım:', 'Investments:')} \n{portfoy_tl:.2f} TL")
        self.lbl_servet_portfoy.setStyleSheet("background-color: transparent; border: none;")
        
        self.lbl_servet_kart.setText(f"💳 {T('Aktif Kredi Borcu:', 'Active Credit Debt:')} \n-{top_kart_borc:.2f} TL")
        self.lbl_servet_kart.setStyleSheet("background-color: transparent; border: none;")
        
        net_servet = portfoy_tl + (gercek_kalan_nakit if gercek_kalan_nakit > 0 else 0) - top_kart_borc
        self.lbl_servet_toplam.setText(f"💰 {T('NET SERVETİM:', 'MY NET WORTH:')} \n{net_servet:.2f} TL")
        self.lbl_servet_toplam.setStyleSheet("font-size: 18px; font-weight:bold; color: #28a745; background-color: transparent; border: none;")

    def hesabi_sil(self):
        cevap = QMessageBox.question(self, T("Hesabı Sil", "Delete Account"), T("Hesabınızı silmek üzeresiniz. Tüm verileriniz kalıcı olarak yok olacak.\nSilmeden önce verilerinizi Excel olarak yedeklemek ister misiniz?", "You are about to delete your account. All data will be lost.\nDo you want to backup your data as Excel before deleting?"), QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if cevap == QMessageBox.Cancel: return
        if cevap == QMessageBox.Yes:
            self.excel_disa_aktar()
            
        kullanicilar = {}
        dosya = os.path.join(DATA_FOLDER, "users.json")
        if os.path.exists(dosya):
            with open(dosya, "r", encoding="utf-8") as f:
                try: kullanicilar = json.load(f)
                except: pass
                
        kayit = kullanicilar.get(self.profil_adi)
        if not kayit: return
        
        if isinstance(kayit, dict):
            soru = kayit.get("soru", "")
            cevap_girdi, ok = QInputDialog.getText(self, T("Güvenlik Onayı", "Security Check"), f"{soru}\n{T('Güvenlik Sorusu Cevabınız:', 'Your Security Answer:')}")
            if not ok: return
            if sifre_hashle(cevap_girdi.strip().lower()) != kayit.get("cevap", ""):
                QMessageBox.warning(self, T("Hata", "Error"), T("Yanlış cevap!", "Wrong answer!"))
                return
        
        sifre, ok2 = QInputDialog.getText(self, T("Güvenlik Onayı 2", "Security Check 2"), T("Lütfen mevcut şifrenizi girin:", "Please enter your current password:"), QLineEdit.Password)
        if not ok2: return
        
        dogru_mu = False
        if isinstance(kayit, str):
            if kayit == sifre_hashle(sifre) or kayit == sifre: dogru_mu = True
        else:
            if kayit.get("sifre") == sifre_hashle(sifre): dogru_mu = True
            
        if dogru_mu:
            del kullanicilar[self.profil_adi]
            with open(dosya, "w", encoding="utf-8") as f:
                json.dump(kullanicilar, f, ensure_ascii=False, indent=4)
            if os.path.exists(self.dosya_adi):
                os.remove(self.dosya_adi)
            QMessageBox.information(self, T("Silindi", "Deleted"), T("Hesabınız ve tüm verileriniz kalıcı olarak silindi.", "Your account and all data have been permanently deleted."))
            self.kaydedildi = True 
            self.cikis_yap()
        else:
            QMessageBox.warning(self, T("Hata", "Error"), T("Hatalı şifre!", "Invalid password!"))
    def pdf_disa_aktar(self):
        if not PRINTER_AVAILABLE: return
        dosya, _ = QFileDialog.getSaveFileName(self, T("Kaydet", "Save"), f"{self.profil_adi}_Rapor_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF (*.pdf)")
        if dosya:
            suan = datetime.now()
            bu_ay_gelir = self.islem_hesapla("gelir", suan.year, suan.month)
            bu_ay_gider = self.islem_hesapla("gider", suan.year, suan.month)
            aktif_taksit = self.aktif_taksit_hesapla(suan.year, suan.month)
            net = bu_ay_gelir - (bu_ay_gider + aktif_taksit)
            n_renk = 'green' if net >= 0 else 'red'
            oran = int(((bu_ay_gider + aktif_taksit) / bu_ay_gelir * 100)) if bu_ay_gelir > 0 else 0

            html = f"""
            <html><head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; font-size: 10px; }}
                h1 {{ text-align: center; color: #0f766e; border-bottom: 2px solid #0f766e; padding-bottom: 5px; font-size: 16px; margin: 5px 0; }}
                h3 {{ font-size: 12px; margin-top: 10px; margin-bottom: 5px; color: #2c3e50; border-bottom: 1px solid #ccc; }}
                p {{ font-size: 11px; margin: 2px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 5px; }}
                th, td {{ padding: 3px; border: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                ul {{ margin: 2px 0; padding-left: 20px; }}
                li {{ margin-bottom: 1px; }}
                .right {{ text-align: right; }}
            </style>
            </head><body>
            <h1>{T('Yönetici Özeti Raporu', 'Executive Summary Report')}</h1>
            <p class="right" style="color: #555;">{T('Tarih:', 'Date:')} {suan.strftime('%d/%m/%Y %H:%M')}</p>
            <p>Sayın {self.profil_adi}, {suan.strftime('%B %Y')} dönemine ait finansal özetiniz aşağıda sunulmuştur. Bu ay gelirlerinizin %{oran} kadarını harcadınız.</p>
            """
            
            html += f"<h3>1. {T('Aylık Bütçe Disiplini', 'Monthly Budget Discipline')}</h3><table>"
            html += f"<tr><th>{T('Kalem', 'Item')}</th><th class='right'>{T('Tutar (TL)', 'Amount (TL)')}</th></tr>"
            html += f"<tr><td>{T('Aylık Gelirler', 'Monthly Incomes')}</td><td class='right' style='color: green;'>+{bu_ay_gelir:.2f}</td></tr>"
            html += f"<tr><td>{T('Aylık Giderler', 'Monthly Expenses')}</td><td class='right' style='color: red;'>-{bu_ay_gider:.2f}</td></tr>"
            html += f"<tr><td>{T('Taksit Yükü', 'Installment Load')}</td><td class='right' style='color: red;'>-{aktif_taksit:.2f}</td></tr>"
            html += f"<tr style='font-weight: bold; background-color: #e9ecef;'><td>{T('KULLANILABİLİR BAKİYE', 'AVAILABLE BALANCE')}</td><td class='right' style='color: {n_renk};'>{net:.2f}</td></tr></table>"

            html += f"<h3>2. {T('Kredi Kartları Durumu', 'Credit Card Status')}</h3><table>"
            html += f"<tr><th>{T('Kart Adı', 'Card Name')}</th><th class='right'>{T('Toplam Limit', 'Total Limit')}</th><th class='right'>{T('Kullanılan', 'Used')}</th></tr>"
            for k in self.kartlar:
                if isinstance(k, dict):
                    html += f"<tr><td>{k.get('ad','')}</td><td class='right'>{k.get('limit',0):.2f} TL</td><td class='right'>{k.get('kullanilan',0):.2f} TL</td></tr>"
            html += "</table>"
            
            html += f"<h3>3. {T('Borç / Alacak Defteri', 'Debt / Receivable Book')}</h3><table>"
            html += f"<tr><th>{T('Kişi', 'Person')}</th><th>{T('Tip', 'Type')}</th><th class='right'>{T('Tutar', 'Amount')}</th></tr>"
            for b in self.borclar:
                if isinstance(b, dict):
                    tip_metni = T("Alacak", "Receivable") if b.get("tip") == "alacak" else T("Borç", "Debt")
                    r_renk = "green" if b.get("tip") == "alacak" else "red"
                    html += f"<tr><td>{b.get('kisi','')}</td><td style='color: {r_renk};'>{tip_metni}</td><td class='right'>{b.get('tutar',0):.2f} TL</td></tr>"
            html += "</table>"
            
            html += f"<h3>4. {T('Mevcut Hedefler', 'Current Goals')}</h3><table>"
            html += f"<tr><th>{T('Hedef Adı', 'Goal Name')}</th><th class='right'>{T('Hedef', 'Target')}</th><th class='right'>{T('Biriken', 'Saved')}</th><th class='right'>%</th></tr>"
            for h in self.hedefler:
                if isinstance(h, dict):
                    h_oran = int((h.get('biriken',0) / h.get('hedef',1)) * 100) if h.get('hedef',1) > 0 else 0
                    html += f"<tr><td>{h.get('ad','')}</td><td class='right'>{h.get('hedef',0):.2f} TL</td><td class='right'>{h.get('biriken',0):.2f} TL</td><td class='right'>%{min(h_oran,100)}</td></tr>"
            html += "</table>"

            html += f"<h3>5. {T('Son 5 Finansal İşlem', 'Last 5 Transactions')}</h3><ul>"
            sorted_islem = sorted(self.islemler, key=lambda x: x.get("tarih", ""), reverse=True)[:5]
            for islem in sorted_islem:
                if isinstance(islem, dict):
                    sembol = "+" if islem.get('tip') == 'gelir' else "-"
                    html += f"<li>{islem.get('tarih', '')} | {islem.get('kategori', '')} | {sembol}{islem.get('tutar', 0):.2f} TL</li>"
            html += "</ul>"
            
            html += f"<hr><h2 class='right' style='color: #28a745; margin-top: 5px;'>{self.lbl_servet_toplam.text()}</h2></body></html>"
            
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(dosya)
            printer.setPageSize(QPrinter.A4) 
            printer.setFullPage(True)
            doc.print_(printer)

    def profili_kaydet(self, sessiz=False):
        veriler = {
            "kategoriler": self.kategoriler,
            "kartlar": self.kartlar,
            "islemler": self.islemler,
            "taksitler": self.taksitler,
            "portfoy": self.portfoy,
            "hedefler": self.hedefler,
            "borclar": self.borclar
        }
        with open(self.dosya_adi, "w", encoding="utf-8") as d:
            json.dump(veriler, d, ensure_ascii=False, indent=4)
        self.kaydedildi = True
        self.setWindowTitle(f"{T('Kişisel Finans Yöneticisi', 'Personal Finance Manager')} - {self.profil_adi}")

    def profili_yukle(self):
        if os.path.exists(self.dosya_adi):
            with open(self.dosya_adi, "r", encoding="utf-8") as d:
                try: v = json.load(d)
                except: v = {}
                
                self.kategoriler = v.get("kategoriler", self.kategoriler)
                
                self.kartlar = v.get("kartlar", [])
                
                self.hedefler = v.get("hedefler", [])
                self.borclar = v.get("borclar", [])
                
                self.islemler = []
                for islem in v.get("islemler", []):
                    if isinstance(islem, dict):
                        if "id" not in islem: islem["id"] = str(uuid.uuid4())
                        if "ay" not in islem or "yil" not in islem:
                            try:
                                d_obj = datetime.strptime(islem.get("tarih", ""), "%Y-%m-%d")
                                islem["ay"] = d_obj.month
                                islem["yil"] = d_obj.year
                            except:
                                islem["ay"] = datetime.now().month
                                islem["yil"] = datetime.now().year
                        self.islemler.append(islem)
                
                self.taksitler = []
                for t in v.get("taksitler", []):
                    if isinstance(t, dict):
                        if "id" not in t: t["id"] = str(uuid.uuid4())
                        
                        k_ad = t.get("kart", "")
                        if not t.get("kart_id"):
                            es_kart = next((k for k in self.kartlar if k.get("ad") == k_ad), None)
                            if es_kart: t["kart_id"] = es_kart["id"]
                            
                        self.taksitler.append(t)
                        
                self.portfoy = []
                for p in v.get("portfoy", []):
                    if isinstance(p, dict):
                        if "id" not in p: p["id"] = str(uuid.uuid4())
                        if "maliyet" not in p: p["maliyet"] = p.get("fiyat", 0)
                        self.portfoy.append(p)
                        
            self.islem_ay_filtre_guncelle()
            self.listeleri_guncelle()
            self.kart_gridini_ciz()
            self.hedef_gridini_ciz()
            self.aylik_analiz_guncelle()
            self.ozeti_guncelle()
            self.kaydedildi = True
            self.setWindowTitle(f"{T('Kişisel Finans Yöneticisi', 'Personal Finance Manager')} - {self.profil_adi}")

    def onayi_sor(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(T("Uyarı", "Warning"))
        msg.setText(T("Kaydedilmemiş değişiklikler var. Çıkmadan önce kaydedilsin mi?", "You have unsaved changes. Save before exiting?"))
        btn_evet = msg.addButton(T("Evet", "Yes"), QMessageBox.YesRole)
        btn_hayir = msg.addButton(T("Hayır", "No"), QMessageBox.NoRole)
        btn_iptal = msg.addButton(T("İptal", "Cancel"), QMessageBox.RejectRole)
        msg.exec_()
        return msg.clickedButton() == btn_evet, msg.clickedButton() == btn_iptal

    def closeEvent(self, event):
        if not getattr(self, 'kaydedildi', True):
            evet_mi, iptal_mi = self.onayi_sor()
            if iptal_mi: event.ignore()
            else:
                if evet_mi: self.profili_kaydet(sessiz=True)
                event.accept()
        else: event.accept()

    def cikis_yap(self):
        if not self.kaydedildi:
            evet_mi, iptal_mi = self.onayi_sor()
            if iptal_mi: return
            if evet_mi: self.profili_kaydet(sessiz=True)
                
        self.kaydedildi = True
        self.ge = GirisEkrani()
        self.ge.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    g = GirisEkrani()
    g.show()
    sys.exit(app.exec_())