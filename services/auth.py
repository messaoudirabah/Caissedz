import hashlib

class AuthService:
    def __init__(self, db_manager):
        self.db = db_manager

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        password_hash = self.hash_password(password)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role, permissions FROM users WHERE username = ? AND password_hash = ?", 
                         (username, password_hash))
            user = cursor.fetchone()
            
            if user:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
        return None

    def create_user(self, username, password, role="cashier"):
        password_hash = self.hash_password(password)
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                             (username, password_hash, role))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
