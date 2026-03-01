from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLineEdit, QScrollArea, QTabWidget,
                             QPushButton, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont
import json

class ReportsScreen(QWidget):
    def __init__(self, db_manager, user_info=None, translator=None):
        super().__init__()
        self.db = db_manager
        self.user_info = user_info or {'role': 'admin'}
        self.trans = translator
        self.permissions = self.load_permissions()
        self.init_ui()
        self.load_stats()

    def load_permissions(self):
        """Load user permissions from JSON."""
        if self.user_info['role'] == 'admin':
            return {k: True for k in ['can_delete_sale']} # Add others as needed
        
        perms_str = self.user_info.get('permissions', '{}')
        try:
            return json.loads(perms_str) if perms_str else {}
        except:
            return {}

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(25)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("TABLEAU DE BORD (2026 EDITION)")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # --- TOP: Key Stats (NEW REDESIGN) ---
        stats_container = QHBoxLayout()
        stats_container.setSpacing(20)
        
        self.sales_card = self.create_stat_card("📊", "VENTES (AUJOURD'HUI)", "0.00 DA")
        self.profit_card = self.create_stat_card("💰", "PROFIT ESTIMÉ", "0.00 DA")
        self.count_card = self.create_stat_card("🛒", "NOMBRE DE VENTES", "0")
        
        stats_container.addWidget(self.sales_card)
        stats_container.addWidget(self.profit_card)
        stats_container.addWidget(self.count_card)
        layout.addLayout(stats_container)
        
        # --- MIDDLE: TABS (Expanded) ---
        self.tabs = QTabWidget()
        
        # --- TAB 1: SALES ---
        sales_tab = QWidget()
        sales_tab_layout = QVBoxLayout(sales_tab)
        sales_tab_layout.setContentsMargins(15, 15, 15, 15)
        
        table_header = QHBoxLayout()
        table_label = QLabel("HISTORIQUE DES VENTES")
        table_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #00FFAA; letter-spacing: 2px;")
        table_header.addWidget(table_label)
        table_header.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("Chercher par ID ou Date...")
        self.search_bar.setFixedWidth(280)
        self.search_bar.textChanged.connect(self.filter_reports)
        table_header.addWidget(self.search_bar)
        
        sales_tab_layout.addLayout(table_header)
        
        self.table = QTableWidget(0, 5) # Increased cols
        self.table.setObjectName("ticketTable")
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels(["ID", "Date / Heure", "Montant Total", "Paiement", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(65) # Taller rows
        sales_tab_layout.addWidget(self.table)
        
        # --- TAB 2: SESSIONS ---
        sessions_tab = QWidget()
        sessions_layout = QVBoxLayout(sessions_tab)
        sessions_layout.setContentsMargins(15, 15, 15, 15)
        
        sessions_label = QLabel("BILAN DES SESSIONS (2026 EDITION)")
        sessions_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #FFD700; letter-spacing: 2px;")
        sessions_layout.addWidget(sessions_label)
        
        self.session_table = QTableWidget(0, 6)
        self.session_table.setObjectName("ticketTable")
        self.session_table.setAlternatingRowColors(True)
        self.session_table.setHorizontalHeaderLabels(["Date", "Fond Caisse", "Ventes", "Profit", "Clôture", "Diff."])
        self.session_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.verticalHeader().setDefaultSectionSize(50) # Taller rows
        sessions_layout.addWidget(self.session_table)
        
        self.tabs.addTab(sales_tab, "VENTES")
        self.tabs.addTab(sessions_tab, "SESSIONS / FOND DE CAISSE")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_stat_card(self, icon, title, value):
        card = QFrame()
        card.setObjectName("statCard")
        # Inline padding sometimes helps if QSS is finicky
        card.setMinimumHeight(120)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon Section
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("statIcon")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
        
        # Text Section
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("statTitle")
        
        val_lbl = QLabel(value)
        val_lbl.setObjectName("statValue")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(val_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        card.value_label = val_lbl
        return card

    def load_stats(self):
        self.all_sales_data = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Today's Sales
            cursor.execute("""
                SELECT SUM(total), COUNT(id) 
                FROM sales 
                WHERE date(date) = date('now')
            """)
            res = cursor.fetchone()
            total = res[0] or 0
            count = res[1] or 0
            self.sales_card.value_label.setText(f"{total:,.2f} DA")
            self.count_card.value_label.setText(str(count))
            
            # Estimated Profit
            cursor.execute("""
                SELECT SUM(si.quantity * (si.price - p.price_cost))
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE date(s.date) = date('now')
            """)
            profit = cursor.fetchone()[0] or 0
            self.profit_card.value_label.setText(f"{profit:,.2f} DA")
            
            # Recent Sales table
            cursor.execute("SELECT id, date, total, payment_type FROM sales ORDER BY id DESC LIMIT 100")
            self.all_sales_data = [dict(s) for s in cursor.fetchall()]
        
        self.display_sales(self.all_sales_data)
        
        # Session History (NEW)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch closed sessions
            cursor.execute("""
                SELECT cs.*,
                (SELECT SUM(total) FROM sales WHERE date >= cs.date AND (date < (SELECT date FROM cash_sessions WHERE id = cs.id + 1) OR (SELECT id FROM cash_sessions WHERE id = cs.id + 1) IS NULL)) as total_sales,
                (SELECT SUM(si.quantity * (si.price - p.price_cost))
                 FROM sale_items si
                 JOIN products p ON si.product_id = p.id
                 JOIN sales s ON si.sale_id = s.id
                 WHERE s.date >= cs.date AND (s.date < (SELECT date FROM cash_sessions WHERE id = cs.id + 1) OR (SELECT id FROM cash_sessions WHERE id = cs.id + 1) IS NULL)) as session_profit
                FROM cash_sessions cs
                ORDER BY cs.id DESC
            """)
            sessions = cursor.fetchall()
            
            self.session_table.setRowCount(0)
            for s in sessions:
                row = self.session_table.rowCount()
                self.session_table.insertRow(row)
                
                sales_val = s['total_sales'] or 0
                profit_val = s['session_profit'] or 0
                
                self.session_table.setItem(row, 0, QTableWidgetItem(str(s['date'])))
                self.session_table.setItem(row, 1, QTableWidgetItem(f"{s['opening_cash']:,.2f} DA"))
                self.session_table.setItem(row, 2, QTableWidgetItem(f"{sales_val:,.2f} DA"))
                
                profit_item = QTableWidgetItem(f"{profit_val:,.2f} DA")
                profit_item.setForeground(QColor("#00FFAA")) # Green for profit
                self.session_table.setItem(row, 3, profit_item)
                
                self.session_table.setItem(row, 4, QTableWidgetItem(f"{s['closing_cash']:,.2f} DA"))
                
                diff_item = QTableWidgetItem(f"{s['difference']:,.2f} DA")
                if s['difference'] < 0:
                    diff_item.setForeground(QColor("#FF4D4D")) # Red
                self.session_table.setItem(row, 5, diff_item)

    def display_sales(self, data):
        self.table.setRowCount(0)
        for s in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"#{s['id']}"))
            self.table.setItem(row, 1, QTableWidgetItem(str(s['date'])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{s['total']:,.2f} DA"))
            self.table.setItem(row, 3, QTableWidgetItem(s['payment_type'].upper()))
            
            # Details Button
            # Details Button
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 5, 2, 5) # Top/Bottom margins to prevent clipping
            btn_layout.setAlignment(Qt.AlignCenter)

            btn = QPushButton("🔍 DÉTAILS")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(110, 36) # Fixed size specifically for better appearance
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #113355; 
                    color: #88ccff; 
                    border: 1px solid #2266aa; 
                    border-radius: 6px; 
                    font-weight: bold; 
                    font-size: 11px; 
                }
                QPushButton:hover { background-color: #1a4a7a; }
            """)
            btn.clicked.connect(lambda checked=False, sid=s['id']: self.show_sale_details(sid))
            btn_layout.addWidget(btn)

            # Delete Button (Conditional)
            if self.permissions.get('can_delete_sale'):
                del_btn = QPushButton("🗑️")
                del_btn.setToolTip("Supprimer la vente")
                del_btn.setCursor(Qt.PointingHandCursor)
                del_btn.setFixedSize(40, 36)
                del_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #331111; 
                        color: #ff5555; 
                        border: 1px solid #552222; 
                        border-radius: 6px; 
                        font-weight: bold; 
                    }
                    QPushButton:hover { background-color: #551111; }
                """)
                del_btn.clicked.connect(lambda checked=False, sid=s['id']: self.delete_sale(sid))
                btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 4, btn_container)

    def delete_sale(self, sale_id):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirmer", f"Voulez-vous vraiment supprimer la vente #{sale_id} ?\n(Le stock sera restauré)",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.db.delete_sale(sale_id):
                QMessageBox.information(self, "Succès", "Vente supprimée avec succès.")
                self.load_stats() # Refresh everything

    def show_sale_details(self, sale_id):
        """Show details dialog for a sale."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Détails Ticket #{sale_id}")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Table Items
        details_table = QTableWidget(0, 3)
        details_table.setObjectName("ticketTable")
        details_table.setAlternatingRowColors(True)
        details_table.setHorizontalHeaderLabels(["Produit", "Qté", "Prix"])
        details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        details_table.verticalHeader().setVisible(False)
        layout.addWidget(details_table)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.name, si.quantity, si.price, si.modifiers_json
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            """, (sale_id,))
            items = cursor.fetchall()
            
        for item in items:
            r = details_table.rowCount()
            details_table.insertRow(r)
            
            name = item['name']
            if item['modifiers_json']:
                try:
                    mods = json.loads(item['modifiers_json'])
                    if mods:
                        name += " (" + ", ".join([m['name'] for m in mods]) + ")"
                except: pass
            
            details_table.setItem(r, 0, QTableWidgetItem(name))
            details_table.setItem(r, 1, QTableWidgetItem(str(item['quantity'])))
            details_table.setItem(r, 2, QTableWidgetItem(f"{item['price']:.2f} DA"))
            
        # Close
        close_btn = QPushButton("FERMER")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def filter_reports(self, text):
        filtered = [s for s in self.all_sales_data if text.lower() in str(s['id']) or text.lower() in str(s['date']).lower()]
        self.display_sales(filtered)
