import os
import shutil
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = os.path.join(BASE_DIR, "backups", f"chatbot_backup_{TIMESTAMP}")
LATEST_BACKUP_LINK = os.path.join(BASE_DIR, "backups", "chatbot_backup_latest")

FILES_TO_BACKUP = [
    os.path.join(BASE_DIR, "apps", "ai_assistant", "views.py"),
    os.path.join(BASE_DIR, "apps", "ai_assistant", "llm_engine.py"),
    os.path.join(BASE_DIR, "apps", "ai_assistant", "knowledge_base.py"),
    os.path.join(BASE_DIR, "apps", "ai_assistant", "models.py"),
    os.path.join(BASE_DIR, "apps", "ai_assistant", "urls.py"),
    os.path.join(BASE_DIR, "config", "settings.py"),
    os.path.join(BASE_DIR, ".env"),
]

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"Creating chatbot backup in: {BACKUP_DIR}")

    for file_path in FILES_TO_BACKUP:
        if os.path.exists(file_path):
            rel_path = os.path.relpath(file_path, BASE_DIR)
            dest_path = os.path.join(BACKUP_DIR, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
            print(f"  Backed up: {rel_path}")

    # Copy latest pointer directory
    if os.path.exists(LATEST_BACKUP_LINK):
        if os.path.isdir(LATEST_BACKUP_LINK):
            shutil.rmtree(LATEST_BACKUP_LINK)
        else:
            os.remove(LATEST_BACKUP_LINK)
    shutil.copytree(BACKUP_DIR, LATEST_BACKUP_LINK)
    print("Backup completed successfully!")

if __name__ == "__main__":
    create_backup()
