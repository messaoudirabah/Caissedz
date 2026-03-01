import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from database.db_manager import DatabaseManager
from services.auth import AuthService
from services.printer import PrinterService
from services.translator import Translator
from ui.login import LoginScreen
from ui.caisse import CaisseScreen
from ui.products import ProductsScreen
from ui.reports import ReportsScreen
from ui.settings import SettingsScreen
from ui.audit_logs import AuditLogsScreen
from ui.activation import ActivationScreen
from ui.sessions import OpenSessionDialog, CloseSessionDialog
from services.license import LicenseService

class CaisseDZApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize services first
        self.db_manager = DatabaseManager(os.path.join(os.path.dirname(__file__), "database/db_v2.sqlite"))
        self.auth_service = AuthService(self.db_manager)
        self.printer_service = PrinterService(self.db_manager) # Pass DB manager for settings
        self.license_service = LicenseService(self.db_manager)
        self.translator = Translator("fr")
        
        self.setWindowTitle(self.translator.get("app_title"))
        self.resize(1100, 800)
        
        # Set Window Icon
        logo_path = os.path.join(os.path.dirname(__file__), "assets/logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        # Set Background Banner with Dark Overlay
        banner_path = os.path.join(os.path.dirname(__file__), "assets/banner.jpg")
        if os.path.exists(banner_path):
            # Convert to forward slashes for Qt stylesheet
            banner_path_qt = banner_path.replace("\\", "/")
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url('{banner_path_qt}');
                    background-position: center center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
            """)
        
        # Load Additional Stylesheet
        style_path = os.path.join(os.path.dirname(__file__), "assets/style.css")
        if os.path.exists(style_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    style_content = f.read()
                    # Apply to global application for consistent rendering
                    QApplication.instance().setStyleSheet(style_content)
            except Exception as e:
                print(f"Error loading style: {e}")
        
        # Main Stacked Widget with dark overlay
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: rgba(0, 0, 0, 0.65);
            }
        """)
        self.setCentralWidget(self.stacked_widget)
        
        self.check_activation()

    def check_activation(self):
        """Checks if the app is activated before showing login."""
        if self.license_service.is_activated():
            self.show_login()
        else:
            self.show_activation()

    def show_activation(self):
        self.activation_screen = ActivationScreen(self.license_service, self.translator)
        self.activation_screen.activation_success.connect(self.show_login)
        self.stacked_widget.addWidget(self.activation_screen)
        self.stacked_widget.setCurrentWidget(self.activation_screen)

    def show_login(self):
        self.login_screen = LoginScreen(self.auth_service, self.translator)
        self.login_screen.login_success.connect(self.on_login_success)
        self.login_screen.lang_changed.connect(self.change_language)
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.setCurrentWidget(self.login_screen)

    def change_language(self, lang_code):
        self.translator.set_lang(lang_code)
        self.setWindowTitle(self.translator.get("app_title"))
        if self.translator.is_rtl():
            QApplication.setLayoutDirection(Qt.RightToLeft)
        else:
            QApplication.setLayoutDirection(Qt.LeftToRight)
        # Refresh login screen text if needed (or just recreate)
        self.show_login()

    def on_login_success(self, user_info):
        self.user_info = user_info
        print(f"Login successful: {user_info}")
        
        # Check for open session
        session = self.db_manager.get_open_session()
        if not session:
            # Get last closing balance for carry-over
            last_session = self.db_manager.get_last_closed_session()
            default_amount = last_session['closing_cash'] if last_session else 0.0
            
            # Prompt user to open session
            dlg = OpenSessionDialog(default_amount, self)
            if dlg.exec():
                amount = dlg.amount_input.value()
                self.db_manager.open_session(amount)
                self.show_caisse()
            else:
                # User cancelled opening session. Return to login.
                self.show_login()
        else:
            self.show_caisse()

    def show_caisse(self):
        self.caisse_screen = CaisseScreen(self.user_info, self.db_manager, self.printer_service, self.translator)
        
        # Load user permissions
        import json
        permissions = {}
        if self.user_info['role'] != 'admin':
            try:
                permissions = json.loads(self.user_info.get('permissions', '{}'))
            except:
                permissions = {}
        
        # Navigation buttons based on role and permissions
        nav_index = 0
        
        # Admin gets full navigation with premium styling
        if self.user_info['role'] == 'admin':
            # Create modern menu bar with glassmorphism
            from PySide6.QtWidgets import QHBoxLayout, QFrame
            from PySide6.QtCore import Qt
            
            menu_bar = QFrame()
            menu_bar.setObjectName("adminMenuBar")
            menu_bar.setStyleSheet("""
                QFrame#adminMenuBar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(12, 18, 13, 245),
                        stop:1 rgba(8, 12, 9, 235));
                    border: 1px solid rgba(0, 255, 170, 50);
                    border-radius: 18px;
                    padding: 12px 20px;
                    margin: 8px 0 15px 0;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(20, 28, 22, 200),
                        stop:1 rgba(12, 18, 14, 220));
                    border: 1.5px solid rgba(0, 255, 170, 35);
                    border-radius: 12px;
                    color: #e8e8e8;
                    font-weight: 800;
                    font-size: 12px;
                    letter-spacing: 0.5px;
                    padding: 14px 24px;
                    min-width: 120px;
                    text-transform: uppercase;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 255, 170, 20),
                        stop:1 rgba(0, 200, 140, 30));
                    border: 1.5px solid #00FFAA;
                    color: #00FFAA;
                    font-weight: 900;
                }
                QPushButton:pressed {
                    background: rgba(0, 255, 170, 60);
                    border: 1.5px solid #FFD700;
                    transform: scale(0.98);
                }
            """)
            
            menu_layout = QHBoxLayout(menu_bar)
            menu_layout.setSpacing(10)
            menu_layout.setContentsMargins(10, 5, 10, 5)
            
            # Navigation buttons with icons
            nav_btn = QPushButton(f"📦 {self.translator.get('products').upper()}")
            nav_btn.setCursor(Qt.PointingHandCursor)
            nav_btn.clicked.connect(self.show_products)
            menu_layout.addWidget(nav_btn)
            
            reports_btn = QPushButton(f"📊 {self.translator.get('reports').upper()}")
            reports_btn.setCursor(Qt.PointingHandCursor)
            reports_btn.clicked.connect(self.show_reports)
            menu_layout.addWidget(reports_btn)
            
            settings_btn = QPushButton(f"⚙️ {self.translator.get('settings').upper()}")
            settings_btn.setCursor(Qt.PointingHandCursor)
            settings_btn.clicked.connect(self.show_settings)
            menu_layout.addWidget(settings_btn)
            
            audit_btn = QPushButton(f"🔐 {self.translator.get('audit').upper()}")
            audit_btn.setCursor(Qt.PointingHandCursor)
            audit_btn.clicked.connect(self.show_audit_logs)
            menu_layout.addWidget(audit_btn)
            
            menu_layout.addStretch()
            
            # Logout button (premium danger style)
            logout_btn = QPushButton(f"🚪 {self.translator.get('logout').upper()}")
            logout_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(80, 40, 40, 200),
                        stop:1 rgba(60, 25, 25, 220));
                    border: 1.5px solid rgba(255, 100, 100, 50);
                    border-radius: 12px;
                    color: #FFD700;
                    font-weight: 800;
                    font-size: 12px;
                    letter-spacing: 0.5px;
                    padding: 14px 24px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 100, 100, 45),
                        stop:1 rgba(200, 60, 60, 55));
                    border: 1.5px solid #ff6666;
                    color: #ffffff;
                    font-weight: 900;
                }
                QPushButton:pressed {
                    background: rgba(255, 85, 85, 70);
                    border: 1.5px solid #ff4444;
                }
            """)
            logout_btn.setCursor(Qt.PointingHandCursor)
            logout_btn.clicked.connect(self.logout)
            menu_layout.addWidget(logout_btn)
            
            # Close session button (premium warning style)
            close_btn = QPushButton(f"❌ {self.translator.get('close_session').upper()}")
            close_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(80, 50, 30, 200),
                        stop:1 rgba(60, 35, 20, 220));
                    border: 1.5px solid rgba(255, 150, 50, 50);
                    border-radius: 12px;
                    color: #FFA500;
                    font-weight: 800;
                    font-size: 12px;
                    letter-spacing: 0.5px;
                    padding: 14px 24px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 150, 50, 45),
                        stop:1 rgba(200, 100, 30, 55));
                    border: 1.5px solid #ff9933;
                    color: #ffffff;
                    font-weight: 900;
                }
                QPushButton:pressed {
                    background: rgba(255, 140, 50, 70);
                    border: 1.5px solid #ff8800;
                }
            """)
            close_btn.setCursor(Qt.PointingHandCursor)
            close_btn.clicked.connect(self.close_current_session)
            menu_layout.addWidget(close_btn)
            
            # Insert menu bar at top of caisse screen
            self.caisse_screen.layout().itemAt(1).layout().insertWidget(0, menu_bar)
            
        
        else:
            # Non-admin: Compact menu bar with permissions-based buttons
            from PySide6.QtWidgets import QHBoxLayout, QFrame
            from PySide6.QtCore import Qt
            
            menu_bar = QFrame()
            menu_bar.setObjectName("userMenuBar")
            menu_bar.setStyleSheet("""
                QFrame#userMenuBar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(15, 20, 16, 230),
                        stop:1 rgba(10, 14, 11, 220));
                    border: 1px solid rgba(0, 255, 170, 40);
                    border-radius: 16px;
                    padding: 10px 18px;
                    margin: 8px 0 12px 0;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(25, 35, 27, 180),
                        stop:1 rgba(18, 25, 20, 200));
                    border: 1.5px solid rgba(0, 255, 170, 30);
                    border-radius: 10px;
                    color: #d8d8d8;
                    font-weight: 700;
                    font-size: 11px;
                    letter-spacing: 0.3px;
                    padding: 12px 20px;
                    min-width: 110px;
                    text-transform: uppercase;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(0, 255, 170, 18),
                        stop:1 rgba(0, 200, 140, 28));
                    border: 1.5px solid #00FFAA;
                    color: #00FFAA;
                    font-weight: 800;
                }
                QPushButton:pressed {
                    background: rgba(0, 255, 170, 50);
                    border: 1.5px solid #FFD700;
                }
            """)
            
            menu_layout = QHBoxLayout(menu_bar)
            menu_layout.setSpacing(8)
            menu_layout.setContentsMargins(8, 4, 8, 4)
            
            # Show buttons based on permissions
            if permissions.get('can_view_products', False):
                products_btn = QPushButton(f"📦 {self.translator.get('products').upper()}")
                products_btn.setCursor(Qt.PointingHandCursor)
                products_btn.clicked.connect(self.show_products)
                menu_layout.addWidget(products_btn)
            
            if permissions.get('can_view_reports', False):
                reports_btn = QPushButton(f"📊 {self.translator.get('reports').upper()}")
                reports_btn.setCursor(Qt.PointingHandCursor)
                reports_btn.clicked.connect(self.show_reports)
                menu_layout.addWidget(reports_btn)
            
            if permissions.get('can_view_settings', False):
                settings_btn = QPushButton(f"⚙️ {self.translator.get('settings').upper()}")
                settings_btn.setCursor(Qt.PointingHandCursor)
                settings_btn.clicked.connect(self.show_settings)
                menu_layout.addWidget(settings_btn)
            
            if permissions.get('can_view_audit', False):
                audit_btn = QPushButton(f"🔐 {self.translator.get('audit').upper()}")
                audit_btn.setCursor(Qt.PointingHandCursor)
                audit_btn.clicked.connect(self.show_audit_logs)
                menu_layout.addWidget(audit_btn)
            
            menu_layout.addStretch()
            
            # Close session for users with permission
            if permissions.get('can_close_session', False):
                close_btn = QPushButton(f"❌ {self.translator.get('close_session').upper()}")
                close_btn.setObjectName("dangerButton") # Style will need checking for non-admin
                # For consistency with user style:
                close_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(80, 50, 30, 180),
                            stop:1 rgba(60, 35, 20, 200));
                        border: 1.5px solid rgba(255, 150, 50, 45);
                        border-radius: 10px;
                        color: #FFA500;
                        font-weight: 700;
                        font-size: 11px;
                        letter-spacing: 0.3px;
                        padding: 12px 20px;
                        min-width: 110px;
                    }
                    QPushButton:hover {
                         background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(255, 150, 50, 40),
                            stop:1 rgba(200, 100, 30, 50));
                        border: 1.5px solid #ff9933;
                        color: #ffffff;
                    }
                """)
                close_btn.setCursor(Qt.PointingHandCursor)
                close_btn.clicked.connect(self.close_current_session)
                menu_layout.addWidget(close_btn)

            # Logout for all users (premium danger style)
            logout_btn_all = QPushButton(f"🚪 {self.translator.get('logout').upper()}")
            logout_btn_all.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(80, 40, 40, 180),
                        stop:1 rgba(60, 25, 25, 200));
                    border: 1.5px solid rgba(255, 100, 100, 45);
                    border-radius: 10px;
                    color: #FFD700;
                    font-weight: 700;
                    font-size: 11px;
                    letter-spacing: 0.3px;
                    padding: 12px 20px;
                    min-width: 110px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 100, 100, 40),
                        stop:1 rgba(200, 60, 60, 50));
                    border: 1.5px solid #ff6666;
                    color: #ffffff;
                    font-weight: 800;
                }
                QPushButton:pressed {
                    background: rgba(255, 85, 85, 60);
                    border: 1.5px solid #ff4444;
                }
            """)
            logout_btn_all.setCursor(Qt.PointingHandCursor)
            logout_btn_all.clicked.connect(self.logout)
            menu_layout.addWidget(logout_btn_all)
            
            # Insert menu bar at top
            self.caisse_screen.layout().itemAt(1).layout().insertWidget(0, menu_bar)
        
        self.stacked_widget.addWidget(self.caisse_screen)
        self.stacked_widget.setCurrentWidget(self.caisse_screen)

    def show_products(self):
        self.products_screen = ProductsScreen(self.db_manager, self.user_info, self.translator)
        back_btn = QPushButton(self.translator.get('back_to_caisse').upper())
        back_btn.clicked.connect(self.show_caisse)
        self.products_screen.layout().insertWidget(0, back_btn)
        
        self.stacked_widget.addWidget(self.products_screen)
        self.stacked_widget.setCurrentWidget(self.products_screen)

    def close_current_session(self):
        session = self.db_manager.get_open_session()
        if session:
            dlg = CloseSessionDialog(session, self.db_manager, self)
            if dlg.exec():
                self.show_login()

    def show_reports(self):
        self.reports_screen = ReportsScreen(self.db_manager, self.user_info, self.translator)
        back_btn = QPushButton(self.translator.get('back_to_caisse').upper())
        back_btn.clicked.connect(self.show_caisse)
        self.reports_screen.layout().insertWidget(0, back_btn)
        
        self.stacked_widget.addWidget(self.reports_screen)
        self.stacked_widget.setCurrentWidget(self.reports_screen)
    
    def show_settings(self):
        self.settings_screen = SettingsScreen(self.db_manager, self.user_info, self.translator)
        
        # Connect logout signal from settings (e.g. after DB reset)
        self.settings_screen.logout_requested.connect(self.force_logout)
        
        back_btn = QPushButton(self.translator.get('back_to_caisse').upper())
        back_btn.clicked.connect(self.show_caisse)
        self.settings_screen.layout().insertWidget(0, back_btn)
        
        self.stacked_widget.addWidget(self.settings_screen)
        self.stacked_widget.setCurrentWidget(self.settings_screen)
    
    def show_audit_logs(self):
        """Show audit logs screen (admin only)."""
        self.audit_screen = AuditLogsScreen(self.db_manager, self.user_info, self.translator)
        back_btn = QPushButton(self.translator.get('back_to_caisse').upper())
        back_btn.clicked.connect(self.show_caisse)
        self.audit_screen.layout().insertWidget(0, back_btn)
        
        self.stacked_widget.addWidget(self.audit_screen)
        self.stacked_widget.setCurrentWidget(self.audit_screen)
    
    def logout(self):
        """Logout current user and return to login screen."""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            self.translator.get('logout'),
            self.translator.get('confirm_logout'),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.force_logout()

    def force_logout(self):
        """Logout without confirmation (used after resets)."""
        self.user_info = None
        # Clear all screens
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        # Return to login
        self.show_login()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set app style/theme eventually
    
    window = CaisseDZApp()
    window.show()
    
    sys.exit(app.exec())
