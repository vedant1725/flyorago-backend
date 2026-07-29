import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEST_BACKUP_LINK = os.path.join(BASE_DIR, "backups", "chatbot_backup_latest")

def rollback():
    if not os.path.exists(LATEST_BACKUP_LINK):
        print("ERROR: No latest backup found in backups/chatbot_backup_latest.")
        sys.exit(1)

    print(f"Rolling back chatbot configuration from: {LATEST_BACKUP_LINK}")
    for root, _, files in os.walk(LATEST_BACKUP_LINK):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, LATEST_BACKUP_LINK)
            dest_path = os.path.join(BASE_DIR, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
            print(f"  Restored: {rel_path}")

    print("Rollback executed successfully!")

if __name__ == "__main__":
    rollback()
