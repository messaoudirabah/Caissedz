"""
Audit Service - Enterprise-level logging for fraud prevention & accountability.

Tracks all critical operations:
- Sales (create, void, modify)
- Stock changes (add, remove, adjust)
- User management (create, edit, delete, permission changes)
- Cash sessions (open, close)
"""

from datetime import datetime
import json
import socket


class AuditService:
    """Centralized audit logging service."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.ip_address = self._get_local_ip()
    
    def _get_local_ip(self):
        """Get local machine IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def log(self, user_id, action_type, entity_type=None, entity_id=None, details=None):
        """
        Log an action to the audit trail.
        
        Args:
            user_id: ID of user performing action
            action_type: Type of action (e.g., 'sale_created', 'sale_voided', 'stock_adjusted')
            entity_type: Type of entity affected (e.g., 'product', 'sale', 'user')
            entity_id: ID of affected entity
            details: Dict with additional context (before/after values, reason, etc.)
        """
        timestamp = datetime.now().isoformat()
        details_json = json.dumps(details) if details else None
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (timestamp, user_id, action_type, entity_type, entity_id, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, user_id, action_type, entity_type, entity_id, details_json, self.ip_address))
            conn.commit()
    
    # --- Convenience Methods for Common Actions ---
    
    def log_sale_created(self, user_id, sale_id, total, payment_type):
        """Log a new sale."""
        self.log(
            user_id=user_id,
            action_type='sale_created',
            entity_type='sale',
            entity_id=sale_id,
            details={'total': total, 'payment_type': payment_type}
        )
    
    def log_sale_voided(self, user_id, sale_id, reason):
        """Log a voided sale."""
        self.log(
            user_id=user_id,
            action_type='sale_voided',
            entity_type='sale',
            entity_id=sale_id,
            details={'reason': reason}
        )
    
    def log_stock_adjusted(self, user_id, product_id, old_stock, new_stock, reason):
        """Log a stock adjustment."""
        self.log(
            user_id=user_id,
            action_type='stock_adjusted',
            entity_type='product',
            entity_id=product_id,
            details={'old_stock': old_stock, 'new_stock': new_stock, 'reason': reason}
        )
    
    def log_user_created(self, admin_id, new_user_id, username):
        """Log user creation."""
        self.log(
            user_id=admin_id,
            action_type='user_created',
            entity_type='user',
            entity_id=new_user_id,
            details={'username': username}
        )
    
    def log_user_deleted(self, admin_id, deleted_user_id, username):
        """Log user deletion."""
        self.log(
            user_id=admin_id,
            action_type='user_deleted',
            entity_type='user',
            entity_id=deleted_user_id,
            details={'username': username}
        )
    
    def log_permissions_changed(self, admin_id, target_user_id, old_perms, new_perms):
        """Log permission changes."""
        self.log(
            user_id=admin_id,
            action_type='permissions_changed',
            entity_type='user',
            entity_id=target_user_id,
            details={'old_permissions': old_perms, 'new_permissions': new_perms}
        )
    
    def log_session_opened(self, user_id, session_id, initial_cash):
        """Log cash session opening."""
        self.log(
            user_id=user_id,
            action_type='session_opened',
            entity_type='session',
            entity_id=session_id,
            details={'initial_cash': initial_cash}
        )
    
    def log_session_closed(self, user_id, session_id, final_cash, expected_cash):
        """Log cash session closing."""
        self.log(
            user_id=user_id,
            action_type='session_closed',
            entity_type='session',
            entity_id=session_id,
            details={'final_cash': final_cash, 'expected_cash': expected_cash, 'variance': final_cash - expected_cash}
        )
    
    def log_product_created(self, user_id, product_id, product_name):
        """Log product creation."""
        self.log(
            user_id=user_id,
            action_type='product_created',
            entity_type='product',
            entity_id=product_id,
            details={'name': product_name}
        )
    
    def log_product_deleted(self, user_id, product_id, product_name):
        """Log product deletion."""
        self.log(
            user_id=user_id,
            action_type='product_deleted',
            entity_type='product',
            entity_id=product_id,
            details={'name': product_name}
        )
    
    def log_login(self, user_id, username, success=True):
        """Log login attempt."""
        self.log(
            user_id=user_id,
            action_type='login_success' if success else 'login_failed',
            entity_type='user',
            entity_id=user_id,
            details={'username': username}
        )
    
    def log_logout(self, user_id, username):
        """Log logout."""
        self.log(
            user_id=user_id,
            action_type='logout',
            entity_type='user',
            entity_id=user_id,
            details={'username': username}
        )
    
    # --- Query Methods ---
    
    def get_logs(self, limit=100, user_id=None, action_type=None, start_date=None, end_date=None):
        """
        Retrieve audit logs with optional filters.
        
        Args:
            limit: Max number of logs to return
            user_id: Filter by specific user
            action_type: Filter by action type
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
        
        Returns:
            List of log entries
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_user_activity(self, user_id, days=7):
        """Get recent activity for a specific user."""
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.get_logs(user_id=user_id, start_date=start_date, limit=1000)
    
    def get_suspicious_activity(self, limit=50):
        """Get potentially suspicious activities (voids, large stock adjustments, etc.)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM audit_logs 
                WHERE action_type IN ('sale_voided', 'stock_adjusted', 'permissions_changed', 'user_deleted')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()
