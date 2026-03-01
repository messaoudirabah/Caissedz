from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import os

class ActivationScreen(QWidget):
    activation_success = Signal()

    def __init__(self, license_service, translator):
        super().__init__()
        self.license_service = license_service
        self.translator = translator
        self.init_ui()
        self.apply_anydesk_protection()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Container Frame (Glassmorphism style)
        container = QFrame()
        container.setFixedWidth(500)
        container.setObjectName("activationContainer")
        container.setStyleSheet("""
            QFrame#activationContainer {
                background: rgba(15, 23, 18, 240);
                border: 2px solid #00FFAA;
                border-radius: 20px;
                padding: 40px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(25)

        # Title
        title = QLabel("ACTIVATION DZ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00FFAA; font-size: 24px; font-weight: bold; letter-spacing: 2px;")
        container_layout.addWidget(title)

        # Subtitle/Instruction
        info = QLabel(self.translator.get("activation_needed_msg", "Veuillez activer votre application pour continuer."))
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        container_layout.addWidget(info)

        # Hardware ID Section
        hw_layout = QVBoxLayout()
        hw_label = QLabel(self.translator.get("hardware_id", "ID Matériel :"))
        hw_label.setStyleSheet("color: #aaa; font-size: 11px; text-transform: uppercase;")
        hw_layout.addWidget(hw_label)

        self.hw_id_display = QLineEdit(self.license_service.get_hardware_id())
        self.hw_id_display.setReadOnly(True)
        self.hw_id_display.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 255, 170, 0.2);
                border-radius: 8px;
                color: #FFD700;
                padding: 12px;
                font-family: 'Consolas', 'Monospace';
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Copy Button for HWID
        copy_btn = QPushButton(self.translator.get("copy_id", "Copier ID"))
        copy_btn.setFixedWidth(100)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 255, 170, 0.1);
                color: #00FFAA;
                border: 1px solid #00FFAA;
                border-radius: 5px;
                font-size: 10px;
                padding: 5px;
            }
            QPushButton:hover { background: rgba(0, 255, 170, 0.2); }
        """)
        copy_btn.clicked.connect(lambda: self.hw_id_display.selectAll() or self.hw_id_display.copy())
        
        hw_id_row = QHBoxLayout()
        hw_id_row.addWidget(self.hw_id_display)
        hw_id_row.addWidget(copy_btn)
        hw_layout.addLayout(hw_id_row)
        container_layout.addLayout(hw_layout)

        # Activation Code Input
        code_layout = QVBoxLayout()
        code_label = QLabel(self.translator.get("activation_code", "Code d'Activation :"))
        code_label.setStyleSheet("color: #aaa; font-size: 11px; text-transform: uppercase;")
        code_layout.addWidget(code_label)

        self.code_input = QLineEdit()
        self.code_input.setEchoMode(QLineEdit.Password) # Mask the code
        self.code_input.setPlaceholderText("•••••-•••••-•••••-•••••")
        self.code_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1.5px solid rgba(0, 255, 170, 0.3);
                border-radius: 10px;
                color: #ffffff;
                padding: 15px;
                font-size: 18px;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border: 1.5px solid #00FFAA;
                background: rgba(0, 255, 170, 0.05);
            }
        """)
        
        # Eye button to toggle masking (optional but helpful)
        show_code_btn = QPushButton("👁️")
        show_code_btn.setFixedWidth(40)
        show_code_btn.setStyleSheet("background: transparent; color: #aaa; border: none; font-size: 16px;")
        show_code_btn.clicked.connect(lambda: self.code_input.setEchoMode(
            QLineEdit.Normal if self.code_input.echoMode() == QLineEdit.Password else QLineEdit.Password
        ))
        
        code_input_row = QHBoxLayout()
        code_input_row.addWidget(self.code_input)
        code_input_row.addWidget(show_code_btn)
        code_layout.addLayout(code_input_row)
        container_layout.addLayout(code_layout)

        # AnyDesk Privacy Toggle
        self.privacy_toggle = QPushButton("🔒 " + self.translator.get("anydesk_privacy", "Mode Confidentialité AnyDesk: ON"))
        self.privacy_toggle.setCheckable(True)
        self.privacy_toggle.setChecked(True)
        self.privacy_toggle.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #aaa;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
            QPushButton:checked {
                background: rgba(0, 255, 170, 0.1);
                color: #00FFAA;
                border: 1px solid #00FFAA;
            }
        """)
        self.privacy_toggle.clicked.connect(self.apply_anydesk_protection)
        container_layout.addWidget(self.privacy_toggle)

        # Activate Button
        self.activate_btn = QPushButton(self.translator.get("activate_now", "ACTIVER MAINTENANT"))
        self.activate_btn.setCursor(Qt.PointingHandCursor)
        self.activate_btn.setFixedHeight(55)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00E699, stop:1 #00B377);
                border: none;
                border-radius: 12px;
                color: #0c120d;
                font-weight: 800;
                font-size: 15px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #00FFAA;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: #00CC88;
                transform: translateY(0px);
            }
        """)
        self.activate_btn.clicked.connect(self.handle_activation)
        container_layout.addWidget(self.activate_btn)

        layout.addWidget(container)

    def apply_anydesk_protection(self):
        """
        Prevents the window from being captured by remote access tools (AnyDesk, TeamViewer, etc.)
        on Windows. This makes the window appear black to the remote user.
        """
        try:
            import platform
            if platform.system() == "Windows":
                import ctypes
                # WDA_NONE = 0
                # WDA_MONITOR = 1
                affinity = 1 if self.privacy_toggle.isChecked() else 0
                
                # Update label text
                state_text = "ON" if affinity == 1 else "OFF"
                self.privacy_toggle.setText(f"🔒 {self.translator.get('anydesk_privacy', 'Mode Confidentialité AnyDesk')}: {state_text}")
                
                hwnd = self.winId()
                if isinstance(hwnd, int):
                    ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
                else:
                    ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd), affinity)
        except Exception as e:
            print(f"AnyDesk protection failed: {e}")

    def handle_activation(self):
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Activation", "Veuillez entrer un code.")
            return

        if self.license_service.verify_activation_code(code):
            QMessageBox.information(self, "Activation", "Application activée avec succès !")
            self.activation_success.emit()
        else:
            QMessageBox.critical(self, "Activation", "Code d'activation invalide pour ce PC.")
