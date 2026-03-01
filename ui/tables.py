
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGridLayout, QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

class TableButton(QPushButton):
    def __init__(self, table_num, status="free", amount=0.0):
        super().__init__()
        self.table_num = table_num
        self.status = status # 'free', 'busy'
        self.setFixedSize(120, 120)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Table Number
        self.num_lbl = QLabel(f"TABLE {table_num}")
        self.num_lbl.setAlignment(Qt.AlignCenter)
        self.num_lbl.setStyleSheet("font-weight: 900; font-size: 16px; color: white; background: transparent;")
        layout.addWidget(self.num_lbl)
        
        # Icon/Status
        self.icon_lbl = QLabel("🍽️")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 30px; background: transparent;")
        layout.addWidget(self.icon_lbl)
        
        # Amount (if busy)
        self.amount_lbl = QLabel(f"{amount:.2f} DA" if amount > 0 else "LIBRE")
        self.amount_lbl.setAlignment(Qt.AlignCenter)
        self.amount_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #eee; background: transparent;")
        layout.addWidget(self.amount_lbl)
        
        self.update_style()
        
    def update_style(self):
        if self.status == "busy":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #551111;
                    border: 2px solid #ff5555;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #662222;
                    border: 2px solid #ff7777;
                }
            """)
            self.amount_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffaaaa; background: transparent;")
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #113311;
                    border: 2px solid #00ffaa;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #224422;
                    border: 2px solid #44ffcc;
                }
            """)
            self.amount_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ccffdd; background: transparent;")

class TableSelectionDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.selected_table = None
        self.selected_sale = None # If resuming an order
        
        self.setWindowTitle("Choix de la Table - CaisseDZ")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        
        self.init_ui()
        self.load_tables()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("PLAN DES TABLES")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: 900; color: #FFD700; letter-spacing: 2px; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setAlignment(Qt.AlignCenter)
        
        free_lbl = QLabel("🟩 LIBRE")
        free_lbl.setStyleSheet("color: #00ffaa; font-weight: bold; margin-right: 20px;")
        legend_layout.addWidget(free_lbl)
        
        busy_lbl = QLabel("🟥 OCCUPÉE")
        busy_lbl.setStyleSheet("color: #ff5555; font-weight: bold;")
        legend_layout.addWidget(busy_lbl)
        
        layout.addLayout(legend_layout)
        
        # Grid Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(15)
        
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)
        
        # Footer Actions
        footer = QHBoxLayout()
        cancel_btn = QPushButton("ANNULER")
        cancel_btn.setFixedSize(150, 50)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #333; 
                border: 1px solid #555; 
                color: white; 
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #444; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        footer.addStretch()
        footer.addWidget(cancel_btn)
        footer.addStretch()
        
        layout.addLayout(footer)

    def load_tables(self):
        # Clear grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
            
        # Get config
        table_count = int(self.db.get_setting("table_count", 10))
        
        # Get active orders
        open_orders = self.db.get_open_orders_by_table()
        
        row, col = 0, 0
        max_cols = 5
        
        for i in range(1, table_count + 1):
            status = "free"
            amount = 0.0
            
            if i in open_orders:
                status = "busy"
                amount = open_orders[i]['total']
            
            btn = TableButton(i, status, amount)
            btn.clicked.connect(lambda checked=False, t=i, s=status: self.on_table_click(t, s))
            
            self.grid.addWidget(btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def on_table_click(self, table_num, status):
        self.selected_table = table_num
        # If busy, we might want to load the order
        if status == "busy":
            open_orders = self.db.get_open_orders_by_table()
            if table_num in open_orders:
                self.selected_sale = open_orders[table_num]
        
        self.accept()
