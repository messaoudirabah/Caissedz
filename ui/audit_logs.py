"""
Audit Logs Screen - View and search all system activity logs.

Admin-only screen for reviewing:
- Sales created/voided
- Stock adjustments
- User management changes
- Permission modifications
- Login/logout events
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                              QFrame, QLineEdit, QComboBox, QDateEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from services.audit_service import AuditService
from datetime import datetime, timedelta
import json


class AuditLogsScreen(QWidget):
    """Admin screen to view and search audit logs."""
    
    def __init__(self, db_manager, current_user, translator=None):
        super().__init__()
        self.db = db_manager
        self.current_user = current_user
        self.trans = translator
        self.audit = AuditService(db_manager)
        self.init_ui()
        self.load_logs()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🔐 JOURNAL D'AUDIT - TRAÇABILITÉ COMPLÈTE")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Filters Panel
        filters_frame = QFrame()
        filters_frame.setObjectName("glassPanel")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(15, 15, 15, 15)
        
        # Action Type Filter
        action_label = QLabel("Type d'action:")
        action_label.setStyleSheet("font-weight: 800; color: #00FFAA;")
        filters_layout.addWidget(action_label)
        
        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "Tous",
            "sale_created",
            "sale_voided",
            "stock_adjusted",
            "user_created",
            "user_deleted",
            "permissions_changed",
            "session_opened",
            "session_closed",
            "login_success",
            "logout"
        ])
        self.action_filter.setFixedHeight(40)
        self.action_filter.currentTextChanged.connect(self.load_logs)
        filters_layout.addWidget(self.action_filter)
        
        filters_layout.addSpacing(20)
        
        # Date Range
        date_label = QLabel("Période:")
        date_label.setStyleSheet("font-weight: 800; color: #FFD700;")
        filters_layout.addWidget(date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFixedHeight(40)
        self.start_date.dateChanged.connect(self.load_logs)
        filters_layout.addWidget(self.start_date)
        
        filters_layout.addWidget(QLabel("→"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFixedHeight(40)
        self.end_date.dateChanged.connect(self.load_logs)
        filters_layout.addWidget(self.end_date)
        
        filters_layout.addSpacing(20)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher (utilisateur, détails)...")
        self.search_input.setFixedHeight(40)
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_table)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addStretch()
        
        # Export Button
        export_btn = QPushButton("📊 EXPORTER")
        export_btn.setObjectName("primaryButton")
        export_btn.setFixedHeight(45)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self.export_logs)
        filters_layout.addWidget(export_btn)
        
        layout.addWidget(filters_frame)
        
        # Logs Table
        self.logs_table = QTableWidget(0, 7)
        self.logs_table.setObjectName("ticketTable")
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setHorizontalHeaderLabels([
            "ID", "Date/Heure", "Utilisateur", "Action", "Entité", "Détails", "IP"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.itemDoubleClicked.connect(self.show_log_details)
        layout.addWidget(self.logs_table)
        
        # Stats Footer
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
    
    def load_logs(self):
        """Load logs from database with current filters."""
        # Get filter values
        action_type = self.action_filter.currentText()
        if action_type == "Tous":
            action_type = None
        
        start_date_str = self.start_date.date().toString("yyyy-MM-dd") + "T00:00:00"
        end_date_str = self.end_date.date().toString("yyyy-MM-dd") + "T23:59:59"
        
        # Fetch logs
        logs = self.audit.get_logs(
            limit=1000,
            action_type=action_type,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # Populate table
        self.logs_table.setRowCount(0)
        for log in logs:
            row = self.logs_table.rowCount()
            self.logs_table.insertRow(row)
            
            # ID
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(log['id'])))
            
            # Timestamp (formatted)
            try:
                dt = datetime.fromisoformat(log['timestamp'])
                timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                timestamp_str = log['timestamp']
            self.logs_table.setItem(row, 1, QTableWidgetItem(timestamp_str))
            
            # User (fetch username)
            username = self.get_username(log['user_id'])
            user_item = QTableWidgetItem(username)
            if log['user_id'] == 1:  # Admin
                user_item.setForeground(QColor("#FFD700"))
                user_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.logs_table.setItem(row, 2, user_item)
            
            # Action Type (color-coded)
            action_item = QTableWidgetItem(log['action_type'])
            if 'voided' in log['action_type'] or 'deleted' in log['action_type']:
                action_item.setForeground(QColor("#ff5555"))
            elif 'created' in log['action_type']:
                action_item.setForeground(QColor("#00FFAA"))
            elif 'login' in log['action_type']:
                action_item.setForeground(QColor("#FFD700"))
            self.logs_table.setItem(row, 3, action_item)
            
            # Entity
            entity_str = f"{log['entity_type'] or ''} #{log['entity_id'] or ''}"
            self.logs_table.setItem(row, 4, QTableWidgetItem(entity_str.strip()))
            
            # Details (truncated)
            details_str = log['details'] or ""
            if len(details_str) > 50:
                details_str = details_str[:50] + "..."
            self.logs_table.setItem(row, 5, QTableWidgetItem(details_str))
            
            # IP Address
            self.logs_table.setItem(row, 6, QTableWidgetItem(log['ip_address'] or ""))
        
        # Update stats
        self.stats_label.setText(f"📊 {len(logs)} entrées affichées")
    
    def get_username(self, user_id):
        """Get username from user ID."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result['username'] if result else f"User #{user_id}"
    
    def filter_table(self):
        """Filter table rows based on search input."""
        search_text = self.search_input.text().lower()
        for row in range(self.logs_table.rowCount()):
            should_show = False
            for col in range(self.logs_table.columnCount()):
                item = self.logs_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.logs_table.setRowHidden(row, not should_show)
    
    def show_log_details(self, item):
        """Show full details of a log entry in a dialog."""
        row = item.row()
        log_id = int(self.logs_table.item(row, 0).text())
        
        # Fetch full log
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs WHERE id = ?", (log_id,))
            log = cursor.fetchone()
        
        if not log:
            return
        
        # Format details
        details_text = f"""
<h3 style='color: #00FFAA;'>Détails du Log #{log['id']}</h3>
<table style='width: 100%; color: #fff;'>
    <tr><td><b>Date/Heure:</b></td><td>{log['timestamp']}</td></tr>
    <tr><td><b>Utilisateur:</b></td><td>{self.get_username(log['user_id'])} (ID: {log['user_id']})</td></tr>
    <tr><td><b>Action:</b></td><td>{log['action_type']}</td></tr>
    <tr><td><b>Entité:</b></td><td>{log['entity_type']} #{log['entity_id']}</td></tr>
    <tr><td><b>Adresse IP:</b></td><td>{log['ip_address']}</td></tr>
</table>
<h4 style='color: #FFD700;'>Détails JSON:</h4>
<pre style='background: #1a1a1a; padding: 10px; border-radius: 5px; color: #00FFAA;'>
{json.dumps(json.loads(log['details']) if log['details'] else {}, indent=2, ensure_ascii=False)}
</pre>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Détails du Log")
        msg.setText(details_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def export_logs(self):
        """Export logs to CSV file."""
        try:
            from datetime import datetime
            filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = f"installer/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Header
                f.write("ID,Timestamp,User,Action,Entity,Details,IP\n")
                
                # Data
                for row in range(self.logs_table.rowCount()):
                    if not self.logs_table.isRowHidden(row):
                        values = []
                        for col in range(self.logs_table.columnCount()):
                            item = self.logs_table.item(row, col)
                            values.append(f'"{item.text() if item else ""}"')
                        f.write(",".join(values) + "\n")
            
            QMessageBox.information(self, "Succès", f"Logs exportés vers:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{e}")
