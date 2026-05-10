"""
pre_build.py
============
Se ejecuta entre la primera y segunda pasada de Buildozer.
Modifica el AndroidManifest.xml generado para añadir:

1. El <receiver> del BootReceiver (BOOT_COMPLETED + QUICKBOOT_POWERON)
2. android:foregroundServiceType="dataSync" al <service> del PythonService
   (requerido en Android 14+ para Foreground Services)

Ejecutar con:
    python3 pre_build.py
"""

import glob
import os
import re
import sys

# ── Buscar el AndroidManifest.xml generado por Buildozer ────
MANIFEST_GLOB = ".buildozer/android/platform/build-*/dists/*/AndroidManifest.xml"
matches = glob.glob(MANIFEST_GLOB)

if not matches:
    print("[pre_build] No se encontró AndroidManifest.xml")
    print(f"[pre_build]    Buscado en: {MANIFEST_GLOB}")
    sys.exit(1)

manifest_path = matches[0]
print(f"[pre_build] Manifest encontrado: {manifest_path}")

with open(manifest_path, "r", encoding="utf-8") as f:
    content = f.read()

original = content  # guardar para comparar al final

# ── 1. Inyectar BootReceiver ─────────────────────────────────
RECEIVER_TAG = """
    <!-- BootReceiver: reprograma alarmas tras reinicio del dispositivo -->
    <receiver
        android:name="com.recordatorios.BootReceiver"
        android:exported="true">
        <intent-filter>
            <action android:name="android.intent.action.BOOT_COMPLETED"/>
            <action android:name="android.intent.action.QUICKBOOT_POWERON"/>
        </intent-filter>
    </receiver>"""

if "com.recordatorios.BootReceiver" in content:
    print("[pre_build] BootReceiver ya estaba en el manifest — no se duplica")
else:
    # Insertar justo antes del cierre de </application>
    content = content.replace("</application>", RECEIVER_TAG + "\n</application>", 1)
    print("[pre_build] BootReceiver inyectado")

# ── 2. Añadir foregroundServiceType al PythonService ─────────
# Android 14+ exige declarar el tipo de servicio en foreground.
# "dataSync" es el tipo más genérico y compatible con python-for-android.
SERVICE_PATTERN = r'(<service[^>]*android:name="org\.kivy\.android\.PythonService"[^>]*)(/>|>)'

def add_foreground_type(match):
    tag_open = match.group(1)
    tag_close = match.group(2)
    if "foregroundServiceType" in tag_open:
        return match.group(0)  # ya tiene el atributo
    return tag_open + '\n            android:foregroundServiceType="dataSync"' + tag_close

new_content, count = re.subn(SERVICE_PATTERN, add_foreground_type, content)
if count:
    content = new_content
    print(f"[pre_build] foregroundServiceType añadido al PythonService ({count} coincidencia/s)")
else:
    print("[pre_build] PythonService no encontrado en el manifest — puede que el nombre difiera")

# ── 3. Guardar si hubo cambios ───────────────────────────────
if content != original:
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[pre_build] Manifest guardado con los cambios")
else:
    print("[pre_build]  El manifest no cambió")

print("[pre_build] Completado")
