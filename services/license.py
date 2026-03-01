import os
import subprocess
import hashlib
import platform

class LicenseService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Persistent path for license (User Home)
        app_dir = os.path.join(os.path.expanduser("~"), ".caissedz")
        if not os.path.exists(app_dir):
            os.makedirs(app_dir, exist_ok=True)
        self.license_file = os.path.join(app_dir, "license.dat")
        self.salt = "CAISSEDZ_SECRET_SALT_2026"

    def get_hardware_id(self):
        """Generates a unique hardware ID based on CPU and Disk Serial."""
        try:
            hw_id = ""
            if platform.system() == "Windows":
                # Get CPU Serial
                cpu_cmd = "wmic cpu get processorid"
                cpu_id = subprocess.check_output(cpu_cmd, shell=True).decode().split('\n')[1].strip()
                
                # Get Disk Serial
                disk_cmd = "wmic diskdrive get serialnumber"
                disk_id = subprocess.check_output(disk_cmd, shell=True).decode().split('\n')[1].strip()
                
                hw_id = f"{cpu_id}-{disk_id}"
            else:
                # Fallback for non-windows (though user specified PC/Windows context)
                hw_id = platform.node()
            
            # Hash it to make it look like a clean ID
            hash_id = hashlib.sha256(hw_id.encode()).hexdigest().upper()[:16]
            # Format: XXXX-XXXX-XXXX-XXXX
            formatted_id = "-".join(hash_id[i:i+4] for i in range(0, 16, 4))
            return formatted_id
        except Exception as e:
            print(f"Error generating Hardware ID: {e}")
            return "UNKNOWN-HWID"

    def verify_activation_code(self, code):
        """Verifies if the provided code matches the hardware ID."""
        hw_id = self.get_hardware_id()
        expected_code = self._generate_code(hw_id)
        if code.strip() == expected_code:
            self._save_activation(code.strip())
            return True
        return False

    def is_activated(self):
        """Checks if the app is already activated."""
        if not os.path.exists(self.license_file):
            return False
        
        try:
            with open(self.license_file, "r") as f:
                saved_code = f.read().strip()
                hw_id = self.get_hardware_id()
                return saved_code == self._generate_code(hw_id)
        except:
            return False

    def _generate_code(self, hw_id):
        """Internal logic to generate the activation code from HWID."""
        # Simple but effective logic: hash(HWID + SALT)
        combined = f"{hw_id}{self.salt}"
        activation_hash = hashlib.sha256(combined.encode()).hexdigest().upper()[:20]
        # Format: XXXXX-XXXXX-XXXXX-XXXXX
        return "-".join(activation_hash[i:i+5] for i in range(0, 20, 5))

    def _save_activation(self, code):
        """Saves the activation code locally."""
        try:
            with open(self.license_file, "w") as f:
                f.write(code)
        except Exception as e:
            print(f"Error saving activation: {e}")
