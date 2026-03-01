import os
from datetime import datetime

import sys

class PrinterService:
    def __init__(self, db_manager=None, settings=None):
        self.db = db_manager
        self.settings = settings or {}
        
        # Use a writable directory in AppData for frozen build
        if getattr(sys, 'frozen', False):
            app_data = os.environ.get('APPDATA') or os.path.expanduser('~')
            self.receipts_dir = os.path.join(app_data, 'CaisseDZ', 'receipts')
        else:
            self.receipts_dir = "installer"
            
        os.makedirs(self.receipts_dir, exist_ok=True)

    def _get_best_printer_name(self):
        import win32print
        
        # 1. Check known thermal printer keywords
        keywords = ["epson", "bixolon", "star", "pos", "thermal", "receipt", "xprinter", "gainscha"]
        
        try:
            printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except:
            return None
        
        # Try to find a thermal printer
        for p in printers:
            for k in keywords:
                if k.lower() in p.lower():
                    return p
                    
        # Fallback to default
        try:
            return win32print.GetDefaultPrinter()
        except:
            return None

    def _print_windows_gdi(self, printer_name, ticket_lines):
        import win32ui
        import win32con
        import win32print

        try:
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
        except Exception as e:
            print(f"Failed to create printer DC: {e}")
            return
        
        hDC.StartDoc("CaisseDZ Receipt")
        hDC.StartPage()
        
        # --- CONFIGURATION (80mm / 58mm Scaled) ---
        # Scale factor for High DPI printers. 
        # Usually 203 DPI (8 dots/mm). 80mm = ~640 dots.
        # We'll stick to the fonts that worked (height 40/28/22) but add weights.
        
        FONTS = {
            "title": win32ui.CreateFont({"name": "Courier New", "height": 50, "weight": 700}), # Big Header
            "header": win32ui.CreateFont({"name": "Courier New", "height": 30, "weight": 700}), # Subheaders
            "bold": win32ui.CreateFont({"name": "Courier New", "height": 28, "weight": 700}),   # Strong text
            "normal": win32ui.CreateFont({"name": "Courier New", "height": 28, "weight": 400}), # Standard
            "small": win32ui.CreateFont({"name": "Courier New", "height": 22, "weight": 400}),  # Footer
        }
        
        page_width = hDC.GetDeviceCaps(win32con.HORZRES)
        y = 20
        
        for line in ticket_lines:
            cmd = line[0] if line else "T"
            content = line[1:] if line else ""
            
            # Reset
            hDC.SetTextAlign(win32con.TA_LEFT)
            
            if cmd == "!": # !TITLE: Text
                parts = content.split(":", 1)
                ctype = parts[0]
                text = parts[1] if len(parts) > 1 else ""
                
                if ctype == "TITLE":
                    hDC.SelectObject(FONTS["title"])
                    # Center
                    hDC.SetTextAlign(win32con.TA_CENTER)
                    hDC.TextOut(page_width // 2, y, text)
                    y += 55
                    
                elif ctype == "HEADER":
                    hDC.SelectObject(FONTS["header"])
                    hDC.SetTextAlign(win32con.TA_CENTER)
                    hDC.TextOut(page_width // 2, y, text)
                    y += 35
                    
                elif ctype == "TOTAL":
                    hDC.SelectObject(FONTS["title"]) # Reuse big font
                    hDC.SetTextAlign(win32con.TA_CENTER)
                    # Draw a box? Or just text. Let's do text for now.
                    hDC.TextOut(page_width // 2, y, text)
                    y += 60

                elif ctype == "LINE":
                    # Draw actual line
                    hDC.MoveTo(10, y + 10)
                    hDC.LineTo(page_width - 10, y + 10)
                    y += 20
                    
                elif ctype == "SPACE":
                    y += 20
                    
            elif cmd == "|": # | Qty | Name | Price (Table Row)
                # Flexible Column Layout
                # We expect 3 parts
                cols = content.split("|")
                if len(cols) == 3:
                     qty, name, price = cols
                     hDC.SelectObject(FONTS["normal"])
                     
                     # Col 1: Left  (0 - 15%)
                     # Col 2: Left  (15% - 75%)
                     # Col 3: Right (100%)
                     
                     # Qty
                     hDC.TextOut(0, y, qty.strip())
                     
                     # Name
                     hDC.TextOut(int(page_width * 0.15), y, name.strip())
                     
                     # Price
                     hDC.SetTextAlign(win32con.TA_RIGHT)
                     hDC.TextOut(page_width, y, price.strip())
                     
                     y += 30
                
                elif len(cols) == 2: # Name ...... Price
                     name, price = cols
                     hDC.SelectObject(FONTS["bold"])
                     hDC.TextOut(0, y, name.strip())
                     hDC.SetTextAlign(win32con.TA_RIGHT)
                     hDC.TextOut(page_width, y, price.strip())
                     y += 30

            else: # Standard text line (centered or left based on context?)
                # Default to Left for "Text"
                hDC.SelectObject(FONTS["normal"])
                hDC.TextOut(0, y, line)
                y += 30
                
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        print(f"✓ Printed using GDI Markup Engine: {printer_name}")

    def print_ticket(self, sale_data, items):
        """
        Generates printer commands list.
        """
        # Fetch Shop Info
        shop_name = "CaisseDZ"
        shop_addr = ""
        shop_phone = ""
        
        if self.db:
            shop_name = self.db.get_setting("shop_name", "CaisseDZ")
            shop_addr = self.db.get_setting("shop_address", "")
            shop_phone = self.db.get_setting("shop_phone", "")

        # BUILD COMMAND LIST
        # Format:
        # !TITLE: Text
        # !HEADER: Text
        # !LINE
        # | Col1 | Col2 | Col3
        # Plain Text
        
        lines = []
        
        # --- HEADER ---
        lines.append(f"!TITLE:{shop_name}")
        if shop_addr: lines.append(f"!HEADER:{shop_addr}")
        if shop_phone: lines.append(f"!HEADER:{shop_phone}")
        lines.append("!SPACE")
        lines.append("!LINE")
        
        # --- META ---
        lines.append(f"Ticket: #{sale_data['id']}")
        lines.append(f"Date:   {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Order Type / Table
        order_type_str = "SUR PLACE" if sale_data.get('order_type') == 'sur_place' else "EMPORTER"
        if sale_data.get('order_type') == 'emporter':
            lines.append(f"!HEADER:{order_type_str}")
        else:
             # Sur place case
             if sale_data.get('table_number'):
                 lines.append(f"!HEADER:{order_type_str} - TABLE {sale_data['table_number']}")
             else:
                 lines.append(f"!HEADER:{order_type_str}")
        
        lines.append("!LINE")
        
        # --- COLUMNS ---
        # Header
        lines.append("| Qt | DESIGNATION | TOTAL ")
        lines.append("!LINE")
        
        # Items
        for item in items:
            name = item['name']
            qty = str(item['qty'])
            price = f"{item['price'] * item['qty']:.2f}"
            
            # Truncate Name if CRAZY long, but GDI handles width better
            if len(name) > 20: name = name[:18] + ".."
            
            lines.append(f"| {qty} | {name} | {price}")
            
            # Modifiers
            if item.get('modifiers'):
                 for m in item['modifiers']:
                     lines.append(f"| | + {m['name']} | ")

        lines.append("!LINE")
        
        # --- TOTAL ---
        lines.append("!SPACE")
        lines.append(f"!TOTAL:TOTAL: {sale_data['total']:.2f} DA")
        lines.append("!SPACE")
        lines.append("!HEADER:Merci de votre visite!")
        
        # 1. Save to file (debug text representation)
        debug_str = "\n".join(lines)
        receipt_path = os.path.join(self.receipts_dir, "last_receipt_markup.txt")
        with open(receipt_path, "w", encoding="utf-8") as f:
            f.write(debug_str)
            
        # 2. Print
        try:
            printer_name = self._get_best_printer_name()
            if printer_name:
                self._print_windows_gdi(printer_name, lines)
            else:
                 print("⚠ No Windows printer found.")
        except Exception as e:
            print(f"⚠ Windows printer error: {e}")
             
        return debug_str

