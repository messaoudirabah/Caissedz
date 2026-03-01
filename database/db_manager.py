import sys
import os
import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = "database/db_v2.sqlite"
            
        # If running as a frozen executable (EXE), use AppData for writable database
        if getattr(sys, 'frozen', False):
            app_data = os.environ.get('APPDATA') or os.path.expanduser('~')
            base_dir = os.path.join(app_data, 'CaisseDZ')
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, 'database', 'db_v2.sqlite')
        else:
            self.db_path = db_path
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    price_sale REAL NOT NULL,
                    price_cost REAL,
                    stock INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    image_path TEXT
                )
            ''')
            
            # Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'cashier', -- 'admin' or 'cashier'
                    permissions TEXT DEFAULT '{}' -- JSON: permissions flags
                )
            ''')
            
            # Sales Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    payment_type TEXT DEFAULT 'cash',
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Sale_Items Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Cash_Sessions Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    opening_cash REAL DEFAULT 0,
                    closing_cash REAL DEFAULT 0,
                    difference REAL DEFAULT 0,
                    status TEXT DEFAULT 'open'
                )
            ''')
            
            # --- Version 2.0 Schema Updates ---
            try:
                # Add modifiers_json to products
                cursor.execute("ALTER TABLE products ADD COLUMN modifiers_json TEXT")
            except sqlite3.OperationalError:
                pass # Already exists
            
            try:
                # Add modifiers_json to sale_items to record selection
                cursor.execute("ALTER TABLE sale_items ADD COLUMN modifiers_json TEXT")
            except sqlite3.OperationalError:
                pass # Already exists
            
            try:
                # Add order_type to sales (sur_place, emporter)
                cursor.execute("ALTER TABLE sales ADD COLUMN order_type TEXT DEFAULT 'sur_place'")
                cursor.execute("ALTER TABLE sales ADD COLUMN notes TEXT")
            except sqlite3.OperationalError:
                pass # Already exists
            
            try:
                # Add permissions column to users (Phase 3.6 - RBAC)
                cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '{}'")
            except sqlite3.OperationalError:
                pass # Already exists
            
            try:
                # Add table_number and status to sales (Table Management)
                cursor.execute("ALTER TABLE sales ADD COLUMN table_number INTEGER")
                cursor.execute("ALTER TABLE sales ADD COLUMN status TEXT DEFAULT 'completed'") # 'pending', 'completed', 'cancelled'
            except sqlite3.OperationalError:
                pass # Already exists
            
            # --- Phase 6: Audit Logs Table ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Index for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action_type)')

            # Create a default admin if none exists
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                import hashlib
                default_password = "admin"
                pwd_hash = hashlib.sha256(default_password.encode()).hexdigest()
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                             ("admin", pwd_hash, "admin"))

            # Settings Table (Added for Shop Customization)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Default Settings
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_name', 'CaisseDZ')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_address', '')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_phone', '')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('table_count', '10')")
            
            # --- Phase 7: Product Modifiers (Options) ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS modifiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL DEFAULT 0,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_modifiers (
                    product_id INTEGER,
                    modifier_id INTEGER,
                    PRIMARY KEY (product_id, modifier_id),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (modifier_id) REFERENCES modifiers(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result['value'] if result else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_open_session(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cash_sessions WHERE status = 'open' ORDER BY id DESC LIMIT 1")
            return cursor.fetchone()

    def get_last_closed_session(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cash_sessions WHERE status = 'closed' ORDER BY id DESC LIMIT 1")
            return cursor.fetchone()

    def open_session(self, amount):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cash_sessions (opening_cash, status) VALUES (?, 'open')", (amount,))
            conn.commit()
            return cursor.lastrowid

    def update_session_opening(self, session_id, new_amount):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cash_sessions SET opening_cash = ? WHERE id = ? AND status = 'open'", (new_amount, session_id))
            conn.commit()
            return True

    def close_session(self, closing_amount):
        session = self.get_open_session()
        if not session: return False
        
        # Calculate expected (opening + sum of sales since opening)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total) FROM sales WHERE date >= ?", (session['date'],))
            total_sales = cursor.fetchone()[0] or 0
            
            expected = session['opening_cash'] + total_sales
            diff = closing_amount - expected
            
            cursor.execute("""
                UPDATE cash_sessions 
                SET closing_cash = ?, difference = ?, status = 'closed'
                WHERE id = ?
            """, (closing_amount, diff, session['id']))
            conn.commit()
            return True

    def get_open_orders_by_table(self):
        """Get all pending orders grouped by table number."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales WHERE status = 'pending' AND table_number IS NOT NULL")
            rows = cursor.fetchall()
            return {row['table_number']: dict(row) for row in rows}

    def reset_database(self):
        """Drops all known tables and re-initializes the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Disable foreign keys to avoid constraints issues while dropping
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            tables = ["products", "users", "sales", "sale_items", "cash_sessions", "audit_logs", "settings", "modifiers", "product_modifiers"]
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()
        
        # Re-initialize to create fresh tables and admin user
        self.init_db()

    # --- MODIFIERS (OPTIONS) METHODS ---
    
    def get_all_modifiers(self, only_active=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM modifiers"
            if only_active:
                query += " WHERE active = 1"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def add_modifier(self, name, price):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO modifiers (name, price) VALUES (?, ?)", (name, price))
            conn.commit()
            return cursor.lastrowid

    def update_modifier(self, mod_id, name, price, active):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE modifiers SET name=?, price=?, active=? WHERE id=?", (name, price, active, mod_id))
            conn.commit()

    def get_product_modifiers(self, product_id, only_active=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT m.* FROM modifiers m
                JOIN product_modifiers pm ON m.id = pm.modifier_id
                WHERE pm.product_id = ?
            """
            if only_active:
                query += " AND m.active = 1"
            cursor.execute(query, (product_id,))
            return [dict(row) for row in cursor.fetchall()]

    def set_product_modifiers(self, product_id, modifier_ids):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM product_modifiers WHERE product_id = ?", (product_id,))
            for mod_id in modifier_ids:
                cursor.execute("INSERT INTO product_modifiers (product_id, modifier_id) VALUES (?, ?)", (product_id, mod_id))
            conn.commit()

    def delete_sale(self, sale_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Restore stock
            cursor.execute("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,))
            items = cursor.fetchall()
            for item in items:
                cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item['quantity'], item['product_id']))
            
            # 2. Delete items
            cursor.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
            # 3. Delete sale
            cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
            conn.commit()
            return True


