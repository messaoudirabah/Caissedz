import uuid
import hashlib
import platform
import os

class LicenseService:
    def __init__(self):
        self.machine_id = self._generate_machine_id()
        self.license_path = os.path.join(os.path.expanduser("~"), ".caissedz_license")

    def _generate_machine_id(self):
        """Generates a stable machine fingerprint."""
        # Mix UUID node, system architecture, and processor info
        raw = f"{uuid.getnode()}-{platform.machine()}-{platform.processor()}"
        return hashlib.sha256(raw.encode()).hexdigest().upper()

    def get_machine_id(self):
        return self.machine_id

    def is_activated(self):
        """Checks if the application is activated on this machine."""
        if not os.path.exists(self.license_path):
            return False
        
        try:
            with open(self.license_path, "r") as f:
                license_key = f.read().strip()
                # Simplified check for now: a valid license would be a signature
                # In 2.0, we would use ed25519 to verify license_key matches machine_id
                return self._verify_license(license_key)
        except:
            return False

    def _verify_license(self, key):
        """Placeholder for cryptographic verification."""
        # For now, let's say a 'demo' key that matches a specific pattern is valid
        # or just check if it's a hash of our machine_id for testing
        expected = hashlib.md5(f"SECRET-{self.machine_id}".encode()).hexdigest().upper()
        return key == expected

    def activate(self, key):
        """Attempts to activate the software with a key."""
        if self._verify_license(key):
            with open(self.license_path, "w") as f:
                f.write(key)
            return True
        return False
