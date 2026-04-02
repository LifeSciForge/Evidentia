#!/usr/bin/env python3
import os
import shutil
import zipfile
import datetime
from pathlib import Path

# Get current directory
project_root = Path.cwd()
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_name = f"evidentia_backup_{timestamp}"
backup_zip = project_root / "backups" / f"{backup_name}.zip"

# Create backups folder
os.makedirs(project_root / "backups", exist_ok=True)

print(f"\n📦 Backing up to: {backup_zip.name}")

# Create zip file
with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Backup src folder
    for file_path in (project_root / "src").rglob('*'):
        if file_path.is_file() and '__pycache__' not in str(file_path):
            arcname = f"{backup_name}/{file_path.relative_to(project_root)}"
            zipf.write(file_path, arcname)
    
    # Backup main files
    for file in ["streamlit_app.py", "requirements.txt"]:
        if (project_root / file).exists():
            zipf.write(project_root / file, f"{backup_name}/{file}")

print(f"✅ Backup complete: {backup_zip}")
print(f"📊 Size: {backup_zip.stat().st_size / (1024*1024):.2f} MB\n")
