from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QLineEdit, QDialog, QFormLayout, QMessageBox, QCheckBox,
                             QTabWidget, QGroupBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
import hashlib
import json
from services.audit_service import AuditService

class SettingsScreen(QWidget):
    logout_requested = Signal()
    
    def __init__(self, db_manager, current_user, translator=None):
        super().__init__()
        self.db = db_manager
        self.current_user = current_user
        self.trans = translator
        self.audit = AuditService(db_manager)  # Audit logging
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("PARAMÈTRES & GESTION DES UTILISATEURS")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()

        # --- TAB 0: GÉNÉRAL (Shop Info) ---
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(25, 25, 25, 25)
        
        # Shop Info Form
        shop_group = QGroupBox("INFORMATIONS DU MAGASIN")
        shop_layout = QFormLayout(shop_group)
        shop_layout.setSpacing(15)
        
        self.shop_name_input = QLineEdit(self.db.get_setting("shop_name", "CaisseDZ"))
        self.shop_name_input.setFixedHeight(40)
        shop_layout.addRow("Nom du Magasin:", self.shop_name_input)
        
        self.shop_addr_input = QLineEdit(self.db.get_setting("shop_address", ""))
        self.shop_addr_input.setFixedHeight(40)
        shop_layout.addRow("Adresse:", self.shop_addr_input)
        
        self.shop_phone_input = QLineEdit(self.db.get_setting("shop_phone", ""))
        self.shop_phone_input.setFixedHeight(40)
        shop_layout.addRow("Téléphone:", self.shop_phone_input)

        self.table_count_input = QLineEdit(self.db.get_setting("table_count", "10"))
        self.table_count_input.setFixedHeight(40)
        self.table_count_input.setPlaceholderText("ex: 10")
        shop_layout.addRow("Nombre de Tables:", self.table_count_input)
        
        general_layout.addWidget(shop_group)
        
        # Danger Zone
        danger_group = QGroupBox("ZONE DE DANGER")
        danger_group.setObjectName("dangerZone")
        danger_layout = QVBoxLayout(danger_group)
        danger_layout.setContentsMargins(20, 30, 20, 20)
        danger_layout.setSpacing(15)

        danger_warning = QLabel("⚠️ ATTENTION : Ces actions sont irréversibles. Soyez prudent.")
        danger_warning.setStyleSheet("color: #ff6666; font-style: italic; font-weight: bold;")
        danger_warning.setAlignment(Qt.AlignCenter)
        danger_layout.addWidget(danger_warning)
        
        reset_btn = QPushButton("RÉINITIALISER TOUTE LA BASE DE DONNÉES")
        reset_btn.setObjectName("dangerButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_database_action)
        danger_layout.addWidget(reset_btn)
        
        general_layout.addWidget(danger_group)
        
        # Save Button
        save_gen_btn = QPushButton("ENREGISTRER LES MODIFICATIONS")
        save_gen_btn.setObjectName("primaryButton")
        save_gen_btn.setFixedHeight(50)
        save_gen_btn.setCursor(Qt.PointingHandCursor)
        save_gen_btn.clicked.connect(self.save_general_settings)
        general_layout.addWidget(save_gen_btn)
        
        general_layout.addStretch()
        self.tabs.addTab(general_tab, "GÉNÉRAL")
        
        # --- TAB 1: USER MANAGEMENT (Admin only) ---
        if self.current_user['role'] == 'admin':
            users_tab = QWidget()
            users_layout = QVBoxLayout(users_tab)
            users_layout.setContentsMargins(15, 15, 15, 15)
            
            # Toolbar
            toolbar = QHBoxLayout()
            users_label = QLabel("GESTION DES UTILISATEURS")
            users_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #00FFAA; letter-spacing: 2px;")
            toolbar.addWidget(users_label)
            toolbar.addStretch()
            
            add_user_btn = QPushButton("+ NOUVEL UTILISATEUR")
            add_user_btn.setObjectName("primaryButton")
            add_user_btn.setFixedHeight(45)
            add_user_btn.setCursor(Qt.PointingHandCursor)
            add_user_btn.clicked.connect(self.add_user_dialog)
            toolbar.addWidget(add_user_btn)
            
            users_layout.addLayout(toolbar)
            
            # Users Table
            self.users_table = QTableWidget(0, 4)
            self.users_table.setObjectName("ticketTable")
            self.users_table.setAlternatingRowColors(True)
            self.users_table.setHorizontalHeaderLabels(["ID", "Utilisateur", "Rôle", "Actions"])
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.users_table.verticalHeader().setVisible(False)
            self.users_table.verticalHeader().setDefaultSectionSize(70)  # Taller rows for buttons
            users_layout.addWidget(self.users_table)
            
            self.tabs.addTab(users_tab, "UTILISATEURS")
        
        # --- TAB 2: MY ACCOUNT ---
        account_tab = QWidget()
        account_layout = QVBoxLayout(account_tab)
        account_layout.setContentsMargins(15, 15, 15, 15)
        
        account_label = QLabel("MON COMPTE")
        account_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #FFD700; letter-spacing: 2px;")
        account_layout.addWidget(account_label)
        
        # Current user info
        info_frame = QFrame()
        info_frame.setObjectName("glassPanel")
        info_layout = QVBoxLayout(info_frame)
        
        info_layout.addWidget(QLabel(f"👤 Utilisateur: {self.current_user['username']}"))
        info_layout.addWidget(QLabel(f"🔑 Rôle: {self.current_user['role'].upper()}"))
        
        account_layout.addWidget(info_frame)
        
        # Change password button
        change_pwd_btn = QPushButton("CHANGER MON MOT DE PASSE")
        change_pwd_btn.setObjectName("primaryButton")
        change_pwd_btn.setFixedHeight(50)
        change_pwd_btn.setCursor(Qt.PointingHandCursor)
        change_pwd_btn.clicked.connect(self.change_password_dialog)
        account_layout.addWidget(change_pwd_btn)
        account_layout.addStretch()
        
        self.tabs.addTab(account_tab, "MON COMPTE")
        
        # --- TAB 3: OPTIONS / SUPPLÉMENTS ---
        if self.current_user['role'] == 'admin':
            mods_tab = QWidget()
            mods_layout = QVBoxLayout(mods_tab)
            mods_layout.setContentsMargins(15, 15, 15, 15)
            
            mod_toolbar = QHBoxLayout()
            mod_label = QLabel("GESTION DES OPTIONS (SUPPLÉMENTS)")
            mod_label.setStyleSheet("font-weight: 800; font-size: 13px; color: #FFA500; letter-spacing: 2px;")
            mod_toolbar.addWidget(mod_label)
            mod_toolbar.addStretch()
            
            add_mod_btn = QPushButton("+ NOUVELLE OPTION")
            add_mod_btn.setObjectName("primaryButton")
            add_mod_btn.setFixedHeight(45)
            add_mod_btn.clicked.connect(self.add_modifier_dialog)
            mod_toolbar.addWidget(add_mod_btn)
            
            mods_layout.addLayout(mod_toolbar)
            
            self.mods_table = QTableWidget(0, 4)
            self.mods_table.setObjectName("ticketTable")
            self.mods_table.setHorizontalHeaderLabels(["ID", "Nom", "Prix (DA)", "Actions"])
            self.mods_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.mods_table.verticalHeader().setVisible(False)
            mods_layout.addWidget(self.mods_table)
            
            self.tabs.addTab(mods_tab, "OPTIONS")
            self.load_modifiers()

        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def save_general_settings(self):
        """Save shop name, address, phone and table count."""
        try:
            name = self.shop_name_input.text().strip()
            addr = self.shop_addr_input.text().strip()
            phone = self.shop_phone_input.text().strip()
            count = self.table_count_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Erreur", "Le nom du magasin est requis!")
                return
            
            self.db.set_setting("shop_name", name)
            self.db.set_setting("shop_address", addr)
            self.db.set_setting("shop_phone", phone)
            self.db.set_setting("table_count", count)
            
            QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès!")
            
            # Audit log
            self.audit.log(
                user_id=self.current_user['id'],
                action_type="UPDATE_SETTINGS",
                details={'message': f"Updated shop settings: {name}"}
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'enregistrement : {e}")

    def reset_database_action(self):
        """Handle full database reset with multiple confirmations."""
        # 1. Warning Dialog
        reply = QMessageBox.warning(
            self,
            "ATTENTION - ACTION DESTRUCTIVE",
            "Êtes-vous sûr de vouloir réinitialiser TOUTE la base de données ?\n\n"
            "Cette action est IRRÉVERSIBLE. Toutes les ventes, produits, sessions et utilisateurs seront SUPPRIMÉS.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 2. Critical Confirmation
            reply2 = QMessageBox.critical(
                self,
                "CONFIRMATION ULTIME",
                "Confirmez-vous SUPPRIMER DÉFINITIVEMENT toutes les données ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply2 == QMessageBox.Yes:
                # 3. Password Verification
                from PySide6.QtWidgets import QInputDialog
                pwd, ok = QInputDialog.getText(
                    self, 
                    "Sécurité", 
                    "Entrez votre mot de passe pour confirmer :", 
                    QLineEdit.Password
                )
                
                if ok and pwd:
                    # Verify password
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (self.current_user['id'],))
                        user_data = cursor.fetchone()
                    
                    input_hash = hashlib.sha256(pwd.encode()).hexdigest()
                    if input_hash == user_data['password_hash']:
                        # PERFORM RESET
                        try:
                            self.db.reset_database()
                            QMessageBox.information(
                                self, 
                                "Réinitialisation Terminée", 
                                "La base de données a été réinitialisée avec succès.\n"
                                "L'application va maintenant se déconnecter."
                            )
                            # Force logout to reset state
                            self.logout_requested.emit() 
                        except Exception as e:
                            QMessageBox.critical(self, "Erreur", f"Erreur lors de la réinitialisation : {e}")
                    else:
                        QMessageBox.warning(self, "Erreur", "Mot de passe incorrect ! Action annulée.")
                else:
                    pass # User cancelled password input

    def load_users(self):

        """Load all users into the table."""
        if self.current_user['role'] != 'admin':
            return
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users ORDER BY id")
            users = cursor.fetchall()
        
        self.users_table.setRowCount(0)
        for user in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)
            
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            
            role_item = QTableWidgetItem(user['role'].upper())
            if user['role'] == 'admin':
                role_item.setForeground(QColor("#FFD700"))
                role_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.users_table.setItem(row, 2, role_item)
            
            # Actions buttons - use factory function to capture user correctly
            def make_action_buttons(user_data):
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 5, 5, 5)
                actions_layout.setSpacing(5)
                
                edit_btn = QPushButton("✏️ Modifier")
                edit_btn.setFixedHeight(40)
                edit_btn.setCursor(Qt.PointingHandCursor)
                edit_btn.clicked.connect(lambda: self.edit_user_dialog(user_data))
                
                history_btn = QPushButton("📊 Détails")
                history_btn.setFixedHeight(40)
                history_btn.setCursor(Qt.PointingHandCursor)
                history_btn.setStyleSheet("background-color: #1a3a1a; color: #00FFAA;")
                history_btn.clicked.connect(lambda: self.show_user_history(user_data))
                
                delete_btn = QPushButton("🗑️ Supprimer")
                delete_btn.setFixedHeight(40)
                delete_btn.setCursor(Qt.PointingHandCursor)
                delete_btn.setStyleSheet("background-color: #331111; color: #ff5555;")
                delete_btn.clicked.connect(lambda: self.delete_user(user_data))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(history_btn)
                actions_layout.addWidget(delete_btn)
                
                return actions_widget
            
            self.users_table.setCellWidget(row, 3, make_action_buttons(dict(user)))
    
    def add_user_dialog(self):
        """Dialog to add a new user."""
        dialog = UserDialog(self.db, mode="add", parent=self)
        if dialog.exec():
            self.load_users()
    
    def edit_user_dialog(self, user):
        """Dialog to edit user permissions."""
        dialog = UserDialog(self.db, mode="edit", user_data=user, parent=self)
        if dialog.exec():
            self.load_users()
    
    def delete_user(self, user):
        """Delete a user."""
        if user['id'] == self.current_user['id']:
            QMessageBox.warning(self, "Erreur", "Vous ne pouvez pas supprimer votre propre compte!")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Supprimer l'utilisateur '{user['username']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user['id'],))
                conn.commit()
            self.load_users()
    
    def show_user_history(self, user):
        """Show sales history for a specific user."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historique de Ventes - {user['username']}")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Stats
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_sales, SUM(total) as total_amount
                FROM sales
                WHERE user_id = ?
            """, (user['id'],))
            stats = cursor.fetchone()
        
        stats_frame = QFrame()
        stats_frame.setObjectName("glassPanel")
        stats_layout = QHBoxLayout(stats_frame)
        
        total_sales_lbl = QLabel(f"📊 Total Ventes: {stats['total_sales'] or 0}")
        total_sales_lbl.setStyleSheet("font-weight: 800; font-size: 14px; color: #00FFAA;")
        
        total_amount_lbl = QLabel(f"💰 Montant Total: {stats['total_amount'] or 0:.2f} DA")
        total_amount_lbl.setStyleSheet("font-weight: 800; font-size: 14px; color: #FFD700;")
        
        stats_layout.addWidget(total_sales_lbl)
        stats_layout.addWidget(total_amount_lbl)
        layout.addWidget(stats_frame)
        
        # Sales table
        sales_table = QTableWidget(0, 4)
        sales_table.setObjectName("ticketTable")
        sales_table.setAlternatingRowColors(True)
        sales_table.setHorizontalHeaderLabels(["ID", "Date", "Montant", "Paiement"])
        sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sales_table.verticalHeader().setVisible(False)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total, payment_type
                FROM sales
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 100
            """, (user['id'],))
            sales = cursor.fetchall()
        
        for sale in sales:
            row = sales_table.rowCount()
            sales_table.insertRow(row)
            sales_table.setItem(row, 0, QTableWidgetItem(f"#{sale['id']}"))
            sales_table.setItem(row, 1, QTableWidgetItem(str(sale['date'])))
            sales_table.setItem(row, 2, QTableWidgetItem(f"{sale['total']:.2f} DA"))
            sales_table.setItem(row, 3, QTableWidgetItem(sale['payment_type'].upper()))
        
        layout.addWidget(sales_table)
        
        # Details Area
        details_label = QLabel("Détails de la vente sélectionnée:")
        details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(details_label)

        self.details_table = QTableWidget(0, 3)
        self.details_table.setObjectName("ticketTable")
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setHorizontalHeaderLabels(["Produit", "Qté", "Prix"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setFixedHeight(150)
        layout.addWidget(self.details_table)

        def show_details(row, col):
            sale_id_text = sales_table.item(row, 0).text()
            sale_id = int(sale_id_text.replace("#", ""))
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, si.quantity, si.price, si.modifiers_json
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale_id,))
                items = cursor.fetchall()
            
            self.details_table.setRowCount(0)
            for item in items:
                r = self.details_table.rowCount()
                self.details_table.insertRow(r)
                
                name = item['name']
                if item['modifiers_json']:
                    try:
                        mods = json.loads(item['modifiers_json'])
                        if mods:
                            name += " (" + ", ".join([m['name'] for m in mods]) + ")"
                    except: pass
                
                self.details_table.setItem(r, 0, QTableWidgetItem(name))
                self.details_table.setItem(r, 1, QTableWidgetItem(str(item['quantity'])))
                self.details_table.setItem(r, 2, QTableWidgetItem(f"{item['price']:.2f}"))

        sales_table.cellClicked.connect(show_details)

        
        # Close button
        close_btn = QPushButton("FERMER")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedHeight(45)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def change_password_dialog(self):
        """Dialog to change current user's password."""
        dialog = ChangePasswordDialog(self.db, self.current_user, parent=self)
        dialog.exec()

    # --- MODIFIER MANAGEMENT ---

    def load_modifiers(self):
        """Load all modifiers into the table."""
        modifiers = self.db.get_all_modifiers()
        self.mods_table.setRowCount(0)
        
        for mod in modifiers:
            row = self.mods_table.rowCount()
            self.mods_table.insertRow(row)
            
            self.mods_table.setItem(row, 0, QTableWidgetItem(str(mod['id'])))
            
            name_item = QTableWidgetItem(mod['name'])
            if not mod['active']:
                name_item.setForeground(QColor("#888888"))
                name_item.setText(mod['name'] + " (Inactif)")
            self.mods_table.setItem(row, 1, QTableWidgetItem(name_item))
            
            self.mods_table.setItem(row, 2, QTableWidgetItem(f"{mod['price']:.2f}"))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("✏️ Modifier")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked=False, m=mod: self.edit_modifier_dialog(m))
            actions_layout.addWidget(edit_btn)
            
            self.mods_table.setCellWidget(row, 3, actions_widget)

    def add_modifier_dialog(self):
        dialog = ModifierEditDialog(parent=self)
        if dialog.exec():
            name, price, active = dialog.get_data()
            self.db.add_modifier(name, price)
            self.load_modifiers()

    def edit_modifier_dialog(self, mod):
        dialog = ModifierEditDialog(mod, parent=self)
        if dialog.exec():
            name, price, active = dialog.get_data()
            self.db.update_modifier(mod['id'], name, price, active)
            self.load_modifiers()



class UserDialog(QDialog):
    """Dialog for adding/editing users with permissions."""
    
    def __init__(self, db_manager, mode="add", user_data=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.mode = mode
        self.user_data = user_data
        self.setWindowTitle("Nouvel Utilisateur" if mode == "add" else "Modifier Utilisateur")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form
        form = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setFixedHeight(40)
        if self.mode == "edit" and self.user_data:
            self.username_input.setText(self.user_data['username'])
        form.addRow("Nom d'utilisateur:", self.username_input)
        
        if self.mode == "add":
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.setFixedHeight(40)
            form.addRow("Mot de passe:", self.password_input)
        
        layout.addLayout(form)
        
        # Permissions Group
        perms_group = QGroupBox("PERMISSIONS")
        perms_layout = QVBoxLayout(perms_group)
        
        self.perm_checkboxes = {}
        permissions = [
            ("can_use_pos", "Utiliser la Caisse (POS)"),
            ("can_edit_fond", "Modifier le Fond de Caisse"),
            ("can_close_session", "Clôturer la Session"),
            ("can_add_product", "Ajouter des Produits"),
            ("can_edit_product", "Modifier des Produits"),
            ("can_delete_product", "Supprimer des Produits"),
            ("can_view_products", "Voir l'Inventaire"),
            ("can_view_reports", "Voir les Rapports"),
            ("can_view_settings", "Accéder aux Paramètres"),
            ("can_view_audit", "Voir les Logs d'Audit"),
            ("can_manage_tables", "Gérer les Tables"),
            ("can_delete_sale", "Supprimer/Annuler une Vente"),
        ]
        
        for perm_key, perm_label in permissions:
            checkbox = QCheckBox(perm_label)
            checkbox.setFixedHeight(30)
            self.perm_checkboxes[perm_key] = checkbox
            perms_layout.addWidget(checkbox)
        
        # Load existing permissions if editing
        if self.mode == "edit" and self.user_data:
            self.load_permissions()
        
        layout.addWidget(perms_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("ENREGISTRER")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(45)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_user)
        
        cancel_btn = QPushButton("ANNULER")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def load_permissions(self):
        """Load permissions from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT permissions FROM users WHERE id = ?", (self.user_data['id'],))
            result = cursor.fetchone()
            
            if result and result['permissions']:
                perms = json.loads(result['permissions'])
                for key, checkbox in self.perm_checkboxes.items():
                    checkbox.setChecked(perms.get(key, False))
    
    def save_user(self):
        """Save user to database."""
        username = self.username_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur est requis!")
            return
        
        # Collect permissions
        permissions = {key: cb.isChecked() for key, cb in self.perm_checkboxes.items()}
        permissions_json = json.dumps(permissions)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.mode == "add":
                password = self.password_input.text()
                if not password:
                    QMessageBox.warning(self, "Erreur", "Le mot de passe est requis!")
                    return
                
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role, permissions) VALUES (?, ?, 'cashier', ?)",
                        (username, password_hash, permissions_json)
                    )
                    conn.commit()
                    QMessageBox.information(self, "Succès", "Utilisateur créé avec succès!")
                    self.accept()
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {e}")
            
            else:  # edit
                cursor.execute(
                    "UPDATE users SET username = ?, permissions = ? WHERE id = ?",
                    (username, permissions_json, self.user_data['id'])
                )
                conn.commit()
                QMessageBox.information(self, "Succès", "Utilisateur mis à jour!")
                self.accept()


class ChangePasswordDialog(QDialog):
    """Dialog to change password for current user."""
    
    def __init__(self, db_manager, current_user, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_user = current_user
        self.setWindowTitle("Changer le Mot de Passe")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        form = QFormLayout()
        
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.old_password.setFixedHeight(40)
        form.addRow("Ancien mot de passe:", self.old_password)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setFixedHeight(40)
        form.addRow("Nouveau mot de passe:", self.new_password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setFixedHeight(40)
        form.addRow("Confirmer:", self.confirm_password)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("CHANGER")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(45)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.change_password)
        
        cancel_btn = QPushButton("ANNULER")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def change_password(self):
        """Change the password."""
        old_pwd = self.old_password.text()
        new_pwd = self.new_password.text()
        confirm_pwd = self.confirm_password.text()
        
        if not all([old_pwd, new_pwd, confirm_pwd]):
            QMessageBox.warning(self, "Erreur", "Tous les champs sont requis!")
            return
        
        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas!")
            return
        
        # Verify old password - load from database
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (self.current_user['id'],))
            user_data = cursor.fetchone()
        
        if not user_data:
            QMessageBox.critical(self, "Erreur", "Utilisateur introuvable!")
            return
        
        old_hash = hashlib.sha256(old_pwd.encode()).hexdigest()
        if old_hash != user_data['password_hash']:
            QMessageBox.warning(self, "Erreur", "Ancien mot de passe incorrect!")
            return
        
        # Update password
        new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                         (new_hash, self.current_user['id']))
            conn.commit()
        
        QMessageBox.information(self, "Succès", "Mot de passe changé avec succès!")
        self.accept()


class ModifierEditDialog(QDialog):
    def __init__(self, mod_data=None, parent=None):
        super().__init__(parent)
        self.mod_data = mod_data
        self.setWindowTitle("Nouvelle Option" if not mod_data else "Modifier l'Option")
        self.setFixedWidth(350)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        if self.mod_data: self.name_input.setText(self.mod_data['name'])
        form.addRow("Nom:", self.name_input)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(100000)
        if self.mod_data: self.price_input.setValue(self.mod_data['price'])
        form.addRow("Prix Supplément:", self.price_input)
        
        self.active_cb = QCheckBox("Activer cet option")
        self.active_cb.setChecked(True)
        if self.mod_data: self.active_cb.setChecked(bool(self.mod_data['active']))
        form.addRow("Statut:", self.active_cb)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("ENREGISTRER")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        btns.addWidget(save_btn)
        
        cancel_btn = QPushButton("ANNULER")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        
        layout.addLayout(btns)
        
    def get_data(self):
        return self.name_input.text().strip(), self.price_input.value(), self.active_cb.isChecked()

