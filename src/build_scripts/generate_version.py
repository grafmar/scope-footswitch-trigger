# generate_version.py
# Liest APP_VERSION aus OsciFootswitch.py und erzeugt version.txt für PyInstaller

import re
import os

APP_SCRIPT = "../pc_app/OsciFootswitch.py"
VERSION_FILE = "../assets/version.txt"

# Lies APP_VERSION aus dem Python-Code
with open(APP_SCRIPT, "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'APP_VERSION\s*=\s*["\']([\d\.]+)["\']', content)
if not match:
    raise ValueError("APP_VERSION nicht gefunden in OsciFootswitch.py")

app_version = match.group(1)
major, minor = (app_version.split("."))

# Version-Datei für PyInstaller erstellen
version_txt = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major},{minor},0,0),
    prodvers=({major},{minor},0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0,0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'github_grafmar'),
         StringStruct('FileDescription', 'OsciFootswitch'),
         StringStruct('InternalName', 'OsciFootswitch'),
         StringStruct('OriginalFilename', 'OsciFootswitch.exe'),
         StringStruct('ProductName', 'OsciFootswitch'),
         StringStruct('ProductVersion', '{app_version}')]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
  ]
)
"""

os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
with open(VERSION_FILE, "w", encoding="utf-8") as f:
    f.write(version_txt)

print(f"version.txt erzeugt mit APP_VERSION={app_version}")
