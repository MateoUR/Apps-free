[app]

# Título de la aplicación
title = App Recordatorios

# Nombre del paquete
package.name = apprecordatorios

# Dominio
package.domain = org.MateoUR

source.dir = .
source.main = main.py

source.include_exts = py,png,json,mp3,java

# Incluye utils.py y service.py
source.include_patterns = bg_menu.png,bg_medications.png,bg_appointments.png,sound_button.mp3,sound_notification.mp3,service.py,utils.py

version = 1.0

# -------------------------------------------------------
# Dependencias
# -------------------------------------------------------
requirements = python3,kivy==2.3.0,plyer,pillow,pyjnius

android.gradle_dependencies = androidx.core:core:1.12.0

orientation = portrait

icon.filename = %(source.dir)s/bg_menu.png

# -------------------------------------------------------
# Android
# -------------------------------------------------------

# Permisos
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,SCHEDULE_EXACT_ALARM

# Servicio en segundo plano (foreground)
services = Recordatorio:service.py:foreground

# Incluir código Java del BootReceiver
android.add_src = src

# ─── AÑADIR ESTAS LÍNEAS (reemplazan a pre_build.py) ───
# Declarar el foreground service type (Android 14+)
android.foreground_service_type = dataSync

# Registrar el BootReceiver en el manifiesto (BOOT_COMPLETED + QUICKBOOT)
android.extra_manifest_xml = \
    <receiver android:name="com.recordatorios.BootReceiver" \
              android:enabled="true" \
              android:exported="true"> \
        <intent-filter> \
            <action android:name="android.intent.action.BOOT_COMPLETED" /> \
            <action android:name="android.intent.action.QUICKBOOT_POWERON" /> \
        </intent-filter> \
    </receiver>
# ─────────────────────────────────────────────────────

# API objetivo
android.api = 34
android.minapi = 26
android.sdk = 34
android.ndk = 25b

android.build_tools_version = 34.0.0
android.enable_androidx = True
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# -------------------------------------------------------
# Sistema
# -------------------------------------------------------
[buildozer]

log_level = 2
warn_on_root = 1
