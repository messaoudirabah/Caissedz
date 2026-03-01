from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QDoubleSpinBox, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt

class OpenSessionDialog(QDialog):
    def __init__(self, default_amount=0.0, parent=None):
        super().__init__(parent)
        self.default_amount = default_amount
        self.setWindowTitle("Ouvrir la Caisse")
        self.setFixedWidth(300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("OUVERTURE DE CAISSE")
        title.setStyleSheet("font-weight: 800; font-size: 16px; color: #FFD700; letter-spacing: 1px;") # Gold
        layout.addWidget(title)
        
        layout.addWidget(QLabel("Montant initial (Fond de caisse):"))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setValue(self.default_amount)
        self.amount_input.setSuffix(" DA")
        self.amount_input.setFixedHeight(50)
        self.amount_input.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FFAA;")
        layout.addWidget(self.amount_input)
        
        btn = QPushButton("OUVRIR LA SESSION")
        btn.setObjectName("primaryButton")
        btn.setFixedHeight(60)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class CloseSessionDialog(QDialog):
    def __init__(self, session_data, db_manager, parent=None):
        super().__init__(parent)
        self.session = session_data
        self.db = db_manager
        self.setWindowTitle("Fermer la Caisse")
        self.setFixedWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("CLÔTURE DE CAISSE")
        title.setStyleSheet("font-weight: 800; font-size: 16px; color: #FFD700; letter-spacing: 1px;")
        layout.addWidget(title)
        
        # Calculate expected total
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total) FROM sales WHERE date >= ?", (self.session['date'],))
            sales_total = cursor.fetchone()[0] or 0
        
        expected = self.session['opening_cash'] + sales_total
        
        info_frame = QFrame()
        info_frame.setObjectName("glassPanel")
        info_layout = QVBoxLayout(info_frame)
        
        info_layout.addWidget(QLabel(f"Ouvert le: {self.session['date']}"))
        info_layout.addWidget(QLabel(f"Fond de caisse: {self.session['opening_cash']:.2f} DA"))
        info_layout.addWidget(QLabel(f"Ventes session: {sales_total:.2f} DA"))
        
        expected_lbl = QLabel(f"TOTAL ATTENDU: {expected:,.2f} DA")
        expected_lbl.setStyleSheet("font-weight: 900; font-size: 18px; color: #00FFAA;")
        info_layout.addWidget(expected_lbl)
        
        layout.addWidget(info_frame)
        
        layout.addWidget(QLabel("\nMontant RÉEL en caisse:"))
        self.actual_input = QDoubleSpinBox()
        self.actual_input.setRange(0, 1000000)
        self.actual_input.setValue(expected)
        self.actual_input.setSuffix(" DA")
        self.actual_input.setFixedHeight(50)
        self.actual_input.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(self.actual_input)
        
        btn = QPushButton("FERMER LA SESSION")
        btn.setStyleSheet("background-color: #331111; color: #ff5555; border: 1px solid #442222; height: 60px; font-weight: 800;")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.handle_close)
        layout.addWidget(btn)

    def handle_close(self):
        amount = self.actual_input.value()
        if self.db.close_session(amount):
            QMessageBox.information(self, "Succès", "Session fermée avec succès.")
            self.accept()
        else:
            self.reject()
