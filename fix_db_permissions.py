import os
import stat
import time

db_path = "database/db.sqlite"

def set_writable(path):
    try:
        os.chmod(path, stat.S_IWRITE)
        print(f"Made {path} writable.")
    except Exception as e:
        print(f"Failed to make writable: {e}")

def delete_db():
    if os.path.exists(db_path):
        print(f"Found database at {db_path}")
        set_writable(db_path)
        try:
            os.remove(db_path)
            print("Database file deleted successfully. It will be recreated on next app start.")
        except PermissionError:
            print("Error: Permission denied. The file might be in use.")
            print("Please close any instances of CaisseDZ or SQLite browsers.")
        except Exception as e:
            print(f"Error deleting file: {e}")
    else:
        print("Database file not found.")

if __name__ == "__main__":
    delete_db()
