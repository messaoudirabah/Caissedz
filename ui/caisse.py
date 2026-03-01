import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QDialog, QCheckBox, QDialogButtonBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPixmap
from services.audit_service import AuditService
from ui.tables import TableSelectionDialog
from PySide6.QtWidgets import QMessageBox

class ProductButton(QPushButton):
    product_clicked = Signal(dict)
    
    def __init__(self, product):
        super().__init__()
        self.product = product
        self.setFixedSize(160, 140) # Larger for touch
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("productBtn")
        
        # Internal layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Product Name
        name_label = QLabel(product['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff; background: transparent; border: none;")
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Price Tag
        price_label = QLabel(f"{product['price_sale']} DA")
        price_label.setAlignment(Qt.AlignCenter)
        price_label.setStyleSheet("""
            background-color: #2e7d32; 
            color: white; 
            font-size: 12px; 
            font-weight: bold; 
            border-radius: 6px; 
            padding: 4px;
            border: none;
        """)
        price_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(price_label)
        
        self.clicked.connect(lambda: self.product_clicked.emit(self.product))
        
        # Micro-animation setup
        self._set_hover_style(False)

    def enterEvent(self, event):
        self._set_hover_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_hover_style(False)
        super().leaveEvent(event)

    def _set_hover_style(self, hovered):
        if hovered:
            self.setStyleSheet("QPushButton#productBtn { background-color: #121813; border: 2px solid #4caf50; margin: -2px; }")
        else:
            self.setStyleSheet("QPushButton#productBtn { background-color: #0d120e; border: 1px solid #1e261f; margin: 0px; }")

class ModifierDialog(QDialog):
    def __init__(self, product_name, modifiers_list, translator, parent=None):
        super().__init__(parent)
        self.trans = translator
        self.setWindowTitle(f"{self.trans.get('choose_options')} {product_name}")
        self.setFixedWidth(350)
        self.selected_modifiers = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel(f"{self.trans.get('choose_options')} {product_name}:")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        self.checkboxes = []
        for mod in modifiers_list:
            cb = QCheckBox(f"{mod['name']} (+{mod['price']} DA)")
            cb.setProperty("mod_data", mod)
            cb.setStyleSheet("padding: 5px; font-size: 13px;")
            layout.addWidget(cb)
            self.checkboxes.append(cb)
            
        layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.handle_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def handle_accept(self):
        self.selected_modifiers = [cb.property("mod_data") for cb in self.checkboxes if cb.isChecked()]
        self.accept()

class CaisseScreen(QWidget):
    def __init__(self, user_info, db_manager, printer_service, translator):
        super().__init__()
        self.user_info = user_info
        self.db = db_manager
        self.printer = printer_service
        self.trans = translator
        self.audit = AuditService(db_manager)  # Audit logging
        self.cart = []
        self.all_products = []
        self.order_type = "sur_place" # Default
        self.current_table = None # Selected table number
        self.current_sale_id = None # If editing an existing pending order
        self.permissions = self.load_permissions()
        self.init_ui()
        self.load_products()
        
    def load_permissions(self):
        """Load user permissions from JSON."""
        if self.user_info['role'] == 'admin':
            return {k: True for k in ['can_use_pos', 'can_edit_fond', 'can_close_session', 'can_add_product', 
                                    'can_edit_product', 'can_delete_product', 'can_view_products', 
                                    'can_view_reports', 'can_view_settings', 'can_view_audit', 
                                    'can_manage_tables', 'can_delete_sale']}
        
        perms_str = self.user_info.get('permissions', '{}')
        try:
            return json.loads(perms_str) if perms_str else {}
        except:
            return {}

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # --- LEFT: Categories (Glass Panel) ---
        categories_panel = QFrame()
        categories_panel.setObjectName("glassPanel")
        categories_panel.setFixedWidth(200)
        cat_layout = QVBoxLayout(categories_panel)
        cat_layout.setContentsMargins(0, 20, 0, 20)
        
        cat_title = QLabel(self.trans.get('categories'))
        cat_title.setAlignment(Qt.AlignCenter)
        cat_title.setStyleSheet("font-weight: 800; color: #444; letter-spacing: 2px;")
        cat_layout.addWidget(cat_title)
        cat_layout.addSpacing(10)
        
        # Categories from DB
        categories = [self.trans.get('all')]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND active = 1")
            categories.extend([row['category'] for row in cursor.fetchall()])

        for cat in categories:
            btn = QPushButton(cat)
            btn.setObjectName("categoryBtn")
            btn.setFixedHeight(60) # Ensure 60px min for touch
            btn.setCheckable(True)
            if cat == self.trans.get('all'): btn.setChecked(True)
            btn.clicked.connect(lambda checked=False, c=cat: self.filter_products(c))
            cat_layout.addWidget(btn)
        
        cat_layout.addStretch()
        main_layout.addWidget(categories_panel)
        
        # --- CENTER: Product Grid & Search ---
        center_panel = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        # Small Logo
        logo_path = os.path.join(os.path.dirname(__file__), "../assets/logo.png")
        if os.path.exists(logo_path):
            header_logo = QLabel()
            header_logo.setPixmap(QPixmap(logo_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            header_layout.addWidget(header_logo)
            
        header_label = QLabel(self.trans.get('caissedz_pro'))
        header_label.setObjectName("titleLabel")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # SEARCH BAR
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText(f"{self.trans.get('search_product')} (F2)")
        self.search_bar.setFixedWidth(350)
        self.search_bar.textChanged.connect(self.search_products)
        header_layout.addWidget(self.search_bar)
        
        center_panel.addLayout(header_layout)
        center_panel.addSpacing(10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll.setWidget(self.grid_widget)
        center_panel.addWidget(scroll)
        
        # --- FOOTER: Order Type & Actions ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        
        self.mode_btn = QPushButton(f"☕ {self.trans.get('on_site').upper()}")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.setFixedSize(160, 50)
        self.mode_btn.setStyleSheet("""
            QPushButton { background-color: #1a221b; color: #4caf50; border: 2px solid #2e7d32; font-weight: 800; border-radius: 12px; }
            QPushButton:checked { background-color: #2e7d32; color: white; }
        """)
        self.mode_btn.clicked.connect(self.toggle_order_mode)
        footer_layout.addWidget(self.mode_btn)
        
        # Table Indicator Label
        self.table_label = QLabel("")
        self.table_label.setStyleSheet("font-weight: bold; color: #FFD700; font-size: 14px; margin-left: 15px;")
        footer_layout.addWidget(self.table_label)
        
        # Change Table Button
        self.table_btn = QPushButton("CHOISIR TABLE")
        self.table_btn.setCursor(Qt.PointingHandCursor)
        self.table_btn.setFixedHeight(50)
        self.table_btn.setStyleSheet("background-color: #333; color: white; border: 1px solid #555; border-radius: 8px; font-weight: bold; padding: 0 15px;")
        self.table_btn.clicked.connect(self.open_table_selection)
        self.table_btn.setVisible(True) # Always visible for Sur Place
        footer_layout.addWidget(self.table_btn)

        
        # Edit Fond Button
        if self.permissions.get('can_edit_fond'):
            self.edit_fond_btn = QPushButton("✏️ MODIFIER FOND")
            self.edit_fond_btn.setCursor(Qt.PointingHandCursor)
            self.edit_fond_btn.setFixedHeight(50)
            self.edit_fond_btn.setStyleSheet("""
                QPushButton { 
                    background-color: rgba(255, 215, 0, 15); 
                    color: #FFD700; 
                    border: 1px solid rgba(255, 215, 0, 40); 
                    border-radius: 8px; 
                    font-weight: bold; 
                    padding: 0 15px; 
                }
                QPushButton:hover { background-color: rgba(255, 215, 0, 30); border: 1.5px solid #FFD700; }
            """)
            self.edit_fond_btn.clicked.connect(self.edit_opening_balance)
            footer_layout.addWidget(self.edit_fond_btn)

        footer_layout.addStretch()
        
        center_panel.addLayout(footer_layout)
        
        main_layout.addLayout(center_panel, 3)
        
        # --- RIGHT: Ticket (Glass Panel) ---
        right_panel = QVBoxLayout()
        
        ticket_frame = QFrame()
        ticket_frame.setObjectName("glassPanel")
        ticket_layout = QVBoxLayout(ticket_frame)
        ticket_layout.setContentsMargins(15, 20, 15, 15)
        
        ticket_header = QHBoxLayout()
        ticket_title = QLabel(self.trans.get('sales_ticket'))
        ticket_title.setStyleSheet("font-weight: 800; font-size: 16px; color: #d4af37;")
        ticket_header.addWidget(ticket_title)
        ticket_header.addStretch()
        ticket_layout.addLayout(ticket_header)
        
        self.cart_table = QTableWidget(0, 4) # Add column for actions
        self.cart_table.setObjectName("ticketTable")
        self.cart_table.setHorizontalHeaderLabels([self.trans.get('product').upper(), self.trans.get('qty').upper(), self.trans.get('total').upper(), ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.cart_table.setColumnWidth(3, 40)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.verticalHeader().setDefaultSectionSize(60) # Increased height
        ticket_layout.addWidget(self.cart_table)
        
        # Summary
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: rgba(0,0,0,50); border-radius: 12px; margin-top: 10px;")
        summary_layout = QVBoxLayout(summary_frame)
        
        self.total_label = QLabel("0.00 DA")
        self.total_label.setStyleSheet("font-size: 38px; font-weight: 900; color: #00FFAA;")
        
        # Neon Glow Effect
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(20)
        self.glow.setColor(QColor(0, 255, 170, 150)) # Neon Green
        self.glow.setOffset(0, 0)
        self.total_label.setGraphicsEffect(self.glow)

        total_title = QLabel(self.trans.get('total_to_pay'))
        total_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(total_title)
        summary_layout.addWidget(self.total_label)
        
        ticket_layout.addWidget(summary_frame)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        pay_btn = QPushButton(f"{self.trans.get('checkout').upper()} (F1)")
        pay_btn.setObjectName("primaryButton")
        pay_btn.setFixedHeight(70)
        pay_btn.setStyleSheet("font-size: 18px;")
        pay_btn.clicked.connect(self.process_payment)
        
        cancel_btn = QPushButton(self.trans.get('clear').upper())
        cancel_btn.setStyleSheet("background-color: #331111; color: #ff5555; border: 1px solid #441111;")
        cancel_btn.setFixedHeight(70)
        cancel_btn.clicked.connect(self.clear_cart)
        
        actions_layout.addWidget(cancel_btn, 1)
        
        # Save Button (For Tables)
        self.save_btn = QPushButton(f"💾 SAUVEGARDER")
        self.save_btn.setObjectName("secondaryButton") # Need to style this if not exists, or use manual style
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #113355; color: #88ccff; border: 1px solid #2266aa; border-radius: 5px; font-weight: bold; font-size: 16px; }
            QPushButton:hover { background-color: #1a4a7a; }
        """)
        self.save_btn.setFixedHeight(70)
        self.save_btn.clicked.connect(self.save_order)
        actions_layout.addWidget(self.save_btn, 1)
        
        actions_layout.addWidget(pay_btn, 2)
        
        ticket_layout.addLayout(actions_layout)
        
        right_panel.addWidget(ticket_frame)
        main_layout.addLayout(right_panel, 2)
        
        self.setLayout(main_layout)

    def toggle_order_mode(self):
        if self.mode_btn.isChecked():
            self.mode_btn.setText(f"☕ {self.trans.get('on_site').upper()}")
            self.order_type = "sur_place"
            self.table_btn.setVisible(True)
            self.save_btn.setVisible(True)
            self.open_table_selection()
        else:
            self.mode_btn.setText(f"🛍️ {self.trans.get('takeaway').upper()}")
            self.order_type = "emporter"
            self.current_table = None
            self.current_sale_id = None
            self.update_table_display()
            self.table_btn.setVisible(False)
            self.save_btn.setVisible(False)
            
    def update_table_display(self):
        if self.current_table:
            self.table_label.setText(f"TABLE {self.current_table}")
            if self.current_sale_id:
                self.table_label.setText(f"TABLE {self.current_table} (MODIFICATION)")
        else:
            self.table_label.setText("")

    def open_table_selection(self):
        dlg = TableSelectionDialog(self.db, self)
        if dlg.exec():
            self.current_table = dlg.selected_table
            self.update_table_display()
            
            # If we selected a busy table, load its order
            if dlg.selected_sale:
                self.load_sale(dlg.selected_sale)
            else:
                # If switching from busy table to new table, maybe clear cart? 
                # Or carry over? Let's assume carry over if no sale loaded.
                # But if we had a sale_id loaded, and picked a free table, we are moving the order (advanced).
                # For simplicity: If picked free table, just keep current cart (new order or moving).
                # If we were editing an order (current_sale_id set) and picked a new table, we treat it as moving the table.
                pass
    
    def load_sale(self, sale):
        """Load an existing pending sale into the cart."""
        self.current_sale_id = sale['id']
        self.cart = []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale['id'],))
            items = cursor.fetchall()
            
            for item in items:
                # Reconstruct cart item
                # Need product info
                cursor.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],))
                prod = cursor.fetchone()
                if not prod: continue
                
                modifiers = []
                if item['modifiers_json']:
                    try:
                        modifiers = json.loads(item['modifiers_json'])
                    except: pass
                
                # Rebuild name
                item_name = prod['name']
                extra_price = sum(m['price'] for m in modifiers)
                if modifiers:
                    mod_str = " + ".join([m['name'] for m in modifiers])
                    item_name = f"{prod['name']} ({mod_str})"
                
                cart_key = f"{prod['id']}_{json.dumps(modifiers, sort_keys=True)}"
                
                self.cart.append({
                    "id": prod['id'], 
                    "key": cart_key,
                    "name": item_name, 
                    "price": item['price'], # This includes modifiers from DB record
                    "qty": item['quantity'],
                    "modifiers": modifiers
                })
        
        self.update_cart_display()
        self.update_table_display()

    def save_order(self):
        if not self.cart: return
        if not self.current_table:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une table pour sauvegarder.")
            self.open_table_selection()
            if not self.current_table: return
            
        total = sum(item['price'] * item['qty'] for item in self.cart)
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.current_sale_id:
                    # Update existing
                    cursor.execute("""
                        UPDATE sales 
                        SET total = ?, table_number = ?, date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (total, self.current_table, self.current_sale_id))
                    
                    # Delete old items (easier than diffing)
                    # Note: This is tricky with stock. 
                    # Simpler approach: 
                    # 1. Restore stock from old items
                    # 2. Delete old items
                    # 3. Add new items and deduct stock
                    
                    cursor.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (self.current_sale_id,))
                    old_items = cursor.fetchall()
                    for old in old_items:
                         cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (old['quantity'], old['product_id']))
                         
                    cursor.execute("DELETE FROM sale_items WHERE sale_id = ?", (self.current_sale_id,))
                    sale_id = self.current_sale_id
                    
                else:
                    # Create new
                    cursor.execute("""
                        INSERT INTO sales (total, user_id, payment_type, order_type, table_number, status) 
                        VALUES (?, ?, ?, ?, ?, 'pending')
                    """, (total, self.user_info['id'], 'cash', 'sur_place', self.current_table))
                    sale_id = cursor.lastrowid
                
                # Insert items
                for item in self.cart:
                    mods_json = json.dumps(item.get('modifiers', []))
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, price, modifiers_json) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (sale_id, item['id'], item['qty'], item['price'], mods_json))
                    
                    # Deduct stock
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
                
                conn.commit()
                QMessageBox.information(self, "Sauvegardé", f"Commande pour Table {self.current_table} sauvegardée.")
                self.clear_cart() # Reset UI
                
        except Exception as e:
             QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {e}")


    def edit_opening_balance(self):
        """Allow user to update the opening cash of the current session."""
        session = self.db.get_open_session()
        if not session:
            QMessageBox.warning(self, "Erreur", "Aucune session ouverte.")
            return
            
        from ui.sessions import OpenSessionDialog
        dlg = OpenSessionDialog(default_amount=session['opening_cash'], parent=self)
        dlg.setWindowTitle("Modifier le Fond de Caisse")
        
        if dlg.exec():
            new_amount = dlg.amount_input.value()
            if self.db.update_session_opening(session['id'], new_amount):
                QMessageBox.information(self, "Succès", f"Fond de caisse mis à jour : {new_amount:.2f} DA")
                # Audit log
                self.audit.log(
                    user_id=self.user_info['id'],
                    action_type="UPDATE_CASH_OPENING",
                    entity_type="session",
                    entity_id=session['id'],
                    details={'old': session['opening_cash'], 'new': new_amount}
                )

    def load_products(self, category=None):
        if category is None:
            category = self.trans.get('all')
        self.all_products = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM products WHERE active = 1"
            if category != self.trans.get('all'):
                query += " AND category = ?"
                cursor.execute(query, (category,))
            else:
                cursor.execute(query)
            
            self.all_products = [dict(p) for p in cursor.fetchall()]
            
        if not self.all_products and category == self.trans.get('all'):
            self.create_default_products()
            self.load_products()
            return
            
        self.display_products(self.all_products)

    def display_products(self, products):
        # Clear grid
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        row, col = 0, 0
        for prod in products:
            btn = ProductButton(prod)
            btn.product_clicked.connect(self.add_to_cart)
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 3: # 4 columns
                col = 0
                row += 1

    def search_products(self, text):
        filtered = [p for p in self.all_products if text.lower() in p['name'].lower()]
        self.display_products(filtered)

    def filter_products(self, category):
        # Update sidebar selection
        for i in range(self.layout().itemAt(0).widget().layout().count()):
            w = self.layout().itemAt(0).widget().layout().itemAt(i).widget()
            if isinstance(w, QPushButton):
                w.setChecked(w.text() == category)
        self.load_products(category)

    def add_to_cart(self, product):
        # Fetch active modifiers for this product from the database
        mods_list = self.db.get_product_modifiers(product['id'], only_active=True)
        modifiers = []
        
        if mods_list:
            try:
                dlg = ModifierDialog(product['name'], mods_list, self.trans, self)
                if dlg.exec():
                    modifiers = dlg.selected_modifiers
                else:
                    return # Cancelled
            except Exception as e:
                print(f"Error handling modifiers: {e}")

        # Construct item name with modifiers
        item_name = product['name']
        extra_price = sum(m['price'] for m in modifiers)
        if modifiers:
            mod_str = " + ".join([m['name'] for m in modifiers])
            item_name = f"{product['name']} ({mod_str})"

        # For modifiers, we treat items as unique if they have different modifiers
        cart_key = f"{product['id']}_{json.dumps(modifiers, sort_keys=True)}"
        
        for item in self.cart:
            if item.get('key') == cart_key:
                item['qty'] += 1
                self.update_cart_display()
                return
        
        self.cart.append({
            "id": product['id'], 
            "key": cart_key,
            "name": item_name, 
            "price": product['price_sale'] + extra_price, 
            "qty": 1,
            "modifiers": modifiers
        })
        self.update_cart_display()

    def update_cart_display(self):
        self.cart_table.setRowCount(0)
        total = 0
        for i, item in enumerate(self.cart):
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            # Name
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            
            # Quantity Widget (Buttons +/-)
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(0, 0, 0, 0)
            qty_layout.setSpacing(5)
            
            btn_minus = QPushButton("-")
            btn_minus.setFixedSize(25, 25)
            btn_minus.setStyleSheet("padding: 0; background: #222; border-radius: 4px;")
            btn_minus.clicked.connect(lambda checked=False, idx=i: self.adjust_qty(idx, -1))
            
            qty_lbl = QLabel(str(item['qty']))
            qty_lbl.setStyleSheet("font-weight: bold; min-width: 20px; color: #fff;")
            qty_lbl.setAlignment(Qt.AlignCenter)
            
            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(25, 25)
            btn_plus.setStyleSheet("padding: 0; background: #222; border-radius: 4px;")
            btn_plus.clicked.connect(lambda checked=False, idx=i: self.adjust_qty(idx, 1))
            
            qty_layout.addWidget(btn_minus)
            qty_layout.addWidget(qty_lbl)
            qty_layout.addWidget(btn_plus)
            
            self.cart_table.setCellWidget(row, 1, qty_widget)
            
            # Total per item
            item_total = item['price'] * item['qty']
            item_total_widget = QTableWidgetItem(f"{item_total:,.2f}")
            item_total_widget.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.cart_table.setItem(row, 2, item_total_widget)
            
            # Delete Button
            btn_del = QPushButton("×")
            btn_del.setFixedSize(25, 25)
            btn_del.setStyleSheet("background-color: transparent; color: #ff5555; font-size: 18px; border: none; font-weight: bold;")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.clicked.connect(lambda checked=False, idx=i: self.remove_item(idx))
            
            self.cart_table.setCellWidget(row, 3, btn_del)
            
            total += item_total
            
        self.total_label.setText(f"{total:,.2f} DA")

    def remove_item(self, index):
        self.cart.pop(index)
        self.update_cart_display()

    def adjust_qty(self, index, delta):
        self.cart[index]['qty'] += delta
        if self.cart[index]['qty'] <= 0:
            self.cart.pop(index)
        self.update_cart_display()

    def create_default_products(self):
        cafe_mods = json.dumps([
            {"name": "Sucre ++", "price": 0},
            {"name": "Supplément Lait", "price": 20},
            {"name": "Miel", "price": 30}
        ])
        defaults = [
            ("Espresso", "Café", 100, 50, 100, cafe_mods),
            ("Direct", "Café", 120, 60, 100, cafe_mods),
            ("Coca Cola", "Boissons", 90, 70, 50, None),
            ("Eau 0.5L", "Boissons", 40, 20, 200, None),
            ("Sandwich", "Snacks", 250, 150, 30, None),
        ]
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("INSERT INTO products (name, category, price_sale, price_cost, stock, modifiers_json) VALUES (?, ?, ?, ?, ?, ?)", defaults)
            conn.commit()

    def clear_cart(self):
        self.cart = []
        self.current_sale_id = None
        # Keep table selected? Maybe.
        # If we cleared manually, we probably are starting over on same table or cancelling.
        # But for 'clear', usually we just empty the cart.
        self.update_cart_display()
        self.update_table_display()

    def process_payment(self):
        if not self.cart: return
        total = sum(item['price'] * item['qty'] for item in self.cart)
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                sale_id = None
                
                if self.current_sale_id:
                     # Updating pending order to completed
                     sale_id = self.current_sale_id
                     cursor.execute("""
                        UPDATE sales 
                        SET total = ?, status = 'completed', payment_type = 'cash', date = CURRENT_TIMESTAMP
                        WHERE id = ?
                     """, (total, sale_id))
                     
                     # Update items (Stock logic same as save: Restore -> Delete -> Insert)
                     # Or assuming cart matches DB if recalled... 
                     # But user might have added items since recall.
                     # Safest: Restore old stock, Wipe items, Re-insert all, Deduct new stock. (Same logic as save)
                     
                     cursor.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,))
                     old_items = cursor.fetchall()
                     for old in old_items:
                         cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (old['quantity'], old['product_id']))
                     
                     cursor.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
                     
                else:
                    # New Sale
                    # Logic for Table Number if Sur Place
                    table_num = self.current_table if self.order_type == 'sur_place' else None
                    
                    cursor.execute("""
                        INSERT INTO sales (total, user_id, payment_type, order_type, table_number, status) 
                        VALUES (?, ?, ?, ?, ?, 'completed')
                    """, (total, self.user_info['id'], 'cash', self.order_type, table_num))
                    sale_id = cursor.lastrowid

                # Insert Items (Shared logic)
                for item in self.cart:
                    mods_json = json.dumps(item.get('modifiers', []))
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, price, modifiers_json) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (sale_id, item['id'], item['qty'], item['price'], mods_json))
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
                    
                conn.commit()
                
                # Audit log
                self.audit.log_sale_created(
                    user_id=self.user_info['id'],
                    sale_id=sale_id,
                    total=total,
                    payment_type='cash'
                )
                
                # Print Info
                print_data = {
                    'id': sale_id, 
                    'total': total, 
                    'order_type': self.order_type,
                    'table_number': self.current_table
                }
                
                self.printer.print_ticket(print_data, self.cart)
                self.clear_cart()
                
                if self.current_table:
                   QMessageBox.information(self, "Succès", "Paiement validé et Table libérée.")
                   self.current_table = None # Free the table in UI
                   self.current_sale_id = None
                   self.update_table_display()
                   
        except Exception as e:
            print(f"Error processing sale: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur encaissement: {e}")
