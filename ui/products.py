from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QLineEdit, QDoubleSpinBox, QSpinBox, QFormLayout, QMessageBox,
                             QDialog, QComboBox, QScrollArea, QCheckBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from services.ai_service import AIService, StockPredictionThread

class ProductsScreen(QWidget):
    def __init__(self, db_manager, user_info=None, translator=None):
        super().__init__()
        self.db = db_manager
        self.user_info = user_info or {'role': 'admin', 'permissions': '{}'}
        self.permissions = self.load_permissions()
        self.trans = translator
        self.ai_service = AIService(db_manager)
        self.ai_alerts = {}
        self.init_ui()
        self.load_products()
        self.run_ai_predictions()
    
    def load_permissions(self):
        """Load user permissions from JSON."""
        import json
        try:
            if self.user_info['role'] == 'admin':
                # Admin has all permissions
                return {
                    'can_view_products': True,
                    'can_add_product': True,
                    'can_edit_product': True,
                    'can_delete_product': True
                }
            perms_str = self.user_info.get('permissions', '{}')
            return json.loads(perms_str) if perms_str else {}
        except:
            return {}

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # --- LEFT: Product Table ---
        left_panel = QFrame()
        left_panel.setObjectName("glassPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # Search & Title Header
        table_header = QHBoxLayout()
        title = QLabel(self.trans.get('inventory_management'))
        title.setObjectName("titleLabel")
        table_header.addWidget(title)
        
        table_header.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText(self.trans.get('search_product'))
        self.search_bar.setFixedWidth(250)
        self.search_bar.textChanged.connect(self.filter_products)
        table_header.addWidget(self.search_bar)
        
        left_layout.addLayout(table_header)
        left_layout.addSpacing(10)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([self.trans.get('id'), self.trans.get('name'), self.trans.get('category'), 
                                               self.trans.get('sale_price'), self.trans.get('cost_price'), self.trans.get('stock')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.table)
        
        layout.addWidget(left_panel, 2) # Add left_panel to main layout
        
        # --- RIGHT: Edit Form ---
        right_panel = QFrame()
        right_panel.setObjectName("glassPanel")
        right_panel.setFixedWidth(380)
        form_layout = QVBoxLayout(right_panel)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        form_title = QLabel(self.trans.get('product_details'))
        form_title.setStyleSheet("font-weight: 800; font-size: 14px; color: #00FFAA; letter-spacing: 1px;")
        form_layout.addWidget(form_title)
        form_layout.addSpacing(10)
        
        self.form = QFormLayout()
        self.form.setSpacing(15)
        
        self.id_input = QLineEdit()
        self.id_input.setReadOnly(True)
        self.id_input.setPlaceholderText(self.trans.get('auto_generated'))
        self.form.addRow(self.trans.get('id') + ":", self.id_input)
        
        self.name_input = QLineEdit()
        self.form.addRow(self.trans.get('name') + ":", self.name_input)
        
        self.cat_input = QLineEdit()
        self.form.addRow(self.trans.get('category') + ":", self.cat_input)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999)
        self.price_input.setSuffix(" DA")
        self.form.addRow(self.trans.get('sale_price') + ":", self.price_input)
        
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(999999)
        self.cost_input.setSuffix(" DA")
        self.form.addRow(self.trans.get('cost_price') + ":", self.cost_input)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(999999)
        self.form.addRow(self.trans.get('stock') + ":", self.stock_input)
        
        form_layout.addLayout(self.form)
        form_layout.addSpacing(20)
        
        # Action Buttons
        actions_label = QLabel(self.trans.get('actions'))
        actions_label.setStyleSheet("font-weight: 800; font-size: 12px; color: #888; letter-spacing: 1px;")
        form_layout.addWidget(actions_label)
        form_layout.addSpacing(10)
        
        # Show buttons based on permissions
        if self.permissions.get('can_add_product', False):
            add_btn = QPushButton(self.trans.get('new_product'))
            add_btn.setObjectName("primaryButton")
            add_btn.setFixedHeight(50)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.clicked.connect(self.add_product)
            form_layout.addWidget(add_btn)
        
        if self.permissions.get('can_edit_product', False):
            # Modifier Options Button
            self.mod_btn = QPushButton("⚙️ GÉRER LES OPTIONS")
            self.mod_btn.setFixedHeight(50)
            self.mod_btn.setStyleSheet("background-color: #1a2a3a; color: #00CCFF; border: 1px solid #005577; border-radius: 10px;")
            self.mod_btn.setCursor(Qt.PointingHandCursor)
            self.mod_btn.clicked.connect(self.manage_product_modifiers)
            form_layout.addWidget(self.mod_btn)

            save_btn = QPushButton(self.trans.get('save'))
            save_btn.setObjectName("primaryButton")
            save_btn.setFixedHeight(50)
            save_btn.setCursor(Qt.PointingHandCursor)
            save_btn.clicked.connect(self.save_product)
            form_layout.addWidget(save_btn)
        
        if self.permissions.get('can_delete_product', False):
            delete_btn = QPushButton(self.trans.get('delete'))
            delete_btn.setStyleSheet("background-color: #331111; color: #ff5555; border: 1px solid #441111; border-radius: 10px;")
            delete_btn.setFixedHeight(50)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.clicked.connect(self.delete_product)
            form_layout.addWidget(delete_btn)
        
        # Show read-only message if user has no edit permissions
        if not any([self.permissions.get('can_add_product'), 
                   self.permissions.get('can_edit_product'),
                   self.permissions.get('can_delete_product')]):
            readonly_label = QLabel(self.trans.get('readonly_mode'))
            readonly_label.setStyleSheet("""
                background-color: rgba(255, 215, 0, 20);
                color: #FFD700;
                padding: 15px;
                border-radius: 10px;
                font-weight: 800;
                font-size: 12px;
                text-align: center;
            """)
            readonly_label.setAlignment(Qt.AlignCenter)
            form_layout.addWidget(readonly_label)
        
        form_layout.addStretch()
        layout.addWidget(right_panel)
        self.setLayout(layout)
    
    def add_product(self):
        """Clear form for new product entry."""
        self.clear_form()
        self.name_input.setFocus()
    
    def edit_product(self):
        """Edit selected product (selection already loads data)."""
        if not self.id_input.text():
            QMessageBox.warning(self, self.trans.get('error'), self.trans.get('select_product'))
            return
        self.name_input.setFocus()


    def run_ai_predictions(self):
        """Run AI stock predictions in background thread."""
        self.prediction_thread = StockPredictionThread(self.ai_service, threshold_days=3)
        self.prediction_thread.predictions_ready.connect(self.on_ai_predictions_ready)
        self.prediction_thread.start()
    
    def on_ai_predictions_ready(self, alerts):
        """Handle AI prediction results."""
        self.ai_alerts = {alert['id']: alert for alert in alerts}
        self.load_products()  # Refresh to show AI indicators

    def load_products(self):
        self.all_data = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category, price_sale, stock FROM products WHERE active = 1")
            self.all_data = [dict(p) for p in cursor.fetchall()]
        
        self.display_data(self.all_data)

    def display_data(self, data):
        self.table.setRowCount(0)
        for row_data in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # We map dict values to columns manually to ensure correct order
            cols = ['id', 'name', 'category', 'price_sale', 'stock']
            for i, key in enumerate(cols):
                item = QTableWidgetItem(str(row_data[key]))
                # AI Stock Alert (Priority 1: Cyan glow for predicted depletion)
                if key == 'stock':
                    if row_data['id'] in self.ai_alerts:
                        alert = self.ai_alerts[row_data['id']]
                        item.setForeground(QColor("#00FFFF"))  # Cyan
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        item.setToolTip(f"🤖 AI ALERT: Stock épuisé dans {alert['days_remaining']:.1f} jours\nPrévision: {alert['daily_forecast']:.1f} unités/jour")
                    # Low stock visual alert (existing - Priority 2)
                    elif (row_data[key] or 0) < 5:
                        item.setForeground(QColor("#FF4D4D")) # Neon Red
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                self.table.setItem(row, i, item)

    def filter_products(self, text):
        filtered = [p for p in self.all_data if text.lower() in p['name'].lower()]
        self.display_data(filtered)

    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            return
            
        prod_id = selected[0].text()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
            p = cursor.fetchone()
            if p:
                self.id_input.setText(str(p['id']))
                self.name_input.setText(p['name'])
                self.cat_input.setText(p['category'] or "")
                self.price_input.setValue(p['price_sale'])
                self.cost_input.setValue(p['price_cost'] or 0)
                self.stock_input.setValue(p['stock'] or 0)

    def clear_form(self):
        self.id_input.clear()
        self.name_input.clear()
        self.cat_input.clear()
        self.price_input.setValue(0)
        self.cost_input.setValue(0)
        self.stock_input.setValue(0)
        self.table.clearSelection()

    def save_product(self):
        name = self.name_input.text()
        if not name:
            QMessageBox.warning(self, self.trans.get('error'), self.trans.get('name_required'))
            return
            
        data = (
            name,
            self.cat_input.text(),
            self.price_input.value(),
            self.cost_input.value(),
            self.stock_input.value()
        )
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if self.id_input.text(): # Update
                cursor.execute("""
                    UPDATE products SET name=?, category=?, price_sale=?, price_cost=?, stock=?
                    WHERE id=?
                """, data + (self.id_input.text(),))
            else: # Insert
                cursor.execute("""
                    INSERT INTO products (name, category, price_sale, price_cost, stock)
                    VALUES (?, ?, ?, ?, ?)
                """, data)
            conn.commit()
            
        self.load_products()
        self.clear_form()

    def delete_product(self):
        if not self.id_input.text(): return
        
        reply = QMessageBox.question(self, "Supprimer", "Voulez-vous vraiment supprimer ce produit ?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET active = 0 WHERE id = ?", (self.id_input.text(),))
                conn.commit()
            self.load_products()
            self.clear_form()


    def manage_product_modifiers(self):
        """Show dialog to link modifiers to the current product."""
        if not self.id_input.text():
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord sélectionner un produit.")
            return
            
        product_id = int(self.id_input.text())
        dialog = ProductModifierLinkDialog(self.db, product_id, self)
        dialog.exec()


class ProductModifierLinkDialog(QDialog):
    def __init__(self, db, product_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.product_id = product_id
        self.setWindowTitle("Lier des Options au Produit")
        self.setFixedWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Sélectionnez les options applicables à ce produit :"))
        
        # All modifiers from DB
        all_mods = self.db.get_all_modifiers(only_active=True)
        # Currently linked modifiers
        linked_mods = self.db.get_product_modifiers(self.product_id)
        linked_ids = [m['id'] for m in linked_mods]
        
        self.checkboxes = []
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        for mod in all_mods:
            cb = QCheckBox(f"{mod['name']} (+{mod['price']:.2f} DA)")
            cb.setProperty("mod_id", mod['id'])
            if mod['id'] in linked_ids:
                cb.setChecked(True)
            scroll_layout.addWidget(cb)
            self.checkboxes.append(cb)
            
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("ENREGISTRER LES LIENS")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_links)
        btns.addWidget(save_btn)
        
        cancel_btn = QPushButton("ANNULER")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        
        layout.addLayout(btns)
        
    def save_links(self):
        selected_ids = [cb.property("mod_id") for cb in self.checkboxes if cb.isChecked()]
        self.db.set_product_modifiers(self.product_id, selected_ids)
        self.accept()

