[app]

# Título que aparece en el launcher del celular
title = App Recordatorios Medicamentos y Citas

# Nombre del paquete (solo letras minúsculas y puntos, sin espacios)
package.name = apprecordatorios

# Dominio del paquete (puede ser ficticio, pero debe tener formato válido)
package.domain = org.MateoUR

# Archivo principal (debe llamarse main.py)
source.dir = .
source.main = main.py

# Extensiones de archivos a incluir en el APK
source.include_exts = py,png,json,mp3

# Archivos de datos a incluir explícitamente
source.include_patterns = bg_menu.png,bg_medications.png,bg_appointments.png

# Versión de la app
version = 1.0

# -------------------------------------------------------
# Dependencias
# -------------------------------------------------------
# plyer: para notificaciones del sistema
# pillow: requerido internamente por kivy para imágenes
requirements = python3,kivy==2.3.0,plyer,pillow

# Orientación de la pantalla: portrait (vertical) o landscape
orientation = portrait

# Icono de la app (puedes reemplazar con tu propio .png de 512x512)
# icon.filename = %(source.dir)s/bg_menu.png

# Pantalla de carga (splash screen), opcional
# presplash.filename = %(source.dir)s/presplash.png

# -------------------------------------------------------
# Android
# -------------------------------------------------------

# Permisos necesarios
android.permissions = VIBRATE, RECEIVE_BOOT_COMPLETED, POST_NOTIFICATIONS

# API mínima soportada (Android 8.0+)
android.minapi = 26

# API objetivo (Android 14)
android.api = 34

# NDK version
android.ndk = 25b

# SDK de Android (Buildozer lo descarga automáticamente)
android.sdk = 34

# Arquitecturas a compilar (arm64-v8a cubre la mayoría de celulares modernos)
# Para máxima compatibilidad puedes agregar armeabi-v7a separado por coma
android.archs = arm64-v8a, armeabi-v7a

# Modo de compilación: debug (para pruebas) o release (para publicar)
# Para release necesitas firmar el APK con una keystore
android.debug = 1

# -------------------------------------------------------
# iOS (no configurado, solo Android)
# -------------------------------------------------------
# [buildozer]
# No tocar esta sección a menos que sepas lo que haces

[buildozer]

# Nivel de log: 0 = silencioso, 1 = normal, 2 = verbose (útil para depurar errores)
log_level = 2

# Advertencia: si es 1, el build se detiene ante cualquier advertencia
warn_on_root = 1
