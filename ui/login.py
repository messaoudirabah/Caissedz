import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QSpacerItem, 
                             QSizePolicy, QApplication, QGraphicsOpacityEffect, QFrame)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon

class LoginScreen(QWidget):
    login_success = Signal(dict)
    lang_changed = Signal(str)

    def __init__(self, auth_service, translator):
        super().__init__()
        self.auth = auth_service
        self.trans = translator
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- LOGIN CARD ---
        self.login_card = QFrame()
        self.login_card.setObjectName("loginCard")
        self.login_card.setFixedWidth(400)
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "../assets/logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("CAISSEDZ")
            logo_label.setStyleSheet("font-size: 24px; font-weight: 900; color: #00FFAA;")
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)
        
        # Welcome Text
        self.welcome_lbl = QLabel()
        self.welcome_lbl.setStyleSheet("font-weight: 800; font-size: 14px; color: #666; letter-spacing: 3px;")
        self.welcome_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.welcome_lbl)
        card_layout.addSpacing(10)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setObjectName("loginInput")
        self.username_input.setFixedWidth(320)
        self.username_input.setFixedHeight(50)
        card_layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(320)
        self.password_input.setFixedHeight(50)
        card_layout.addWidget(self.password_input)

        # Language
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Français 🇫🇷", "fr")
        self.lang_combo.addItem("العربية 🇩🇿", "ar")
        self.lang_combo.setFixedWidth(320)
        self.lang_combo.setFixedHeight(40)
        if QApplication.layoutDirection() == Qt.RightToLeft:
            self.lang_combo.setCurrentIndex(1)
        self.lang_combo.currentIndexChanged.connect(self.handle_lang_change)
        card_layout.addWidget(self.lang_combo)

        # Login button
        self.login_btn = QPushButton()
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setFixedHeight(55)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        # Error
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.error_label)

        main_layout.addWidget(self.login_card)
        
        # Update text based on current language
        self.update_texts()
    
    def update_texts(self):
        """Update all UI texts based on current language."""
        # Welcome text
        if self.trans.lang == "ar":
            self.welcome_lbl.setText("دخول آمن")
            self.username_input.setPlaceholderText("اسم المستخدم")
            self.password_input.setPlaceholderText("كلمة المرور")
            self.login_btn.setText("تسجيل الدخول")
        else:
            self.welcome_lbl.setText("CONNEXION SÉCURISÉE")
            self.username_input.setPlaceholderText("UTILISATEUR")
            self.password_input.setPlaceholderText("MOT DE PASSE")
            self.login_btn.setText("SE CONNECTER")
        
    def handle_lang_change(self, index):
        lang_code = self.lang_combo.itemData(index)
        self.lang_changed.emit(lang_code)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            if self.trans.lang == "ar":
                self.error_label.setText("الحقول مطلوبة")
            else:
                self.error_label.setText("Champs requis")
            return
            
        user = self.auth.login(username, password)
        if user:
            self.login_success.emit(user)
        else:
            if self.trans.lang == "ar":
                self.error_label.setText("تم رفض الوصول")
            else:
                self.error_label.setText("Accès refusé")
