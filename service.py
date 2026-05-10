# ============================================================
# service.py  —  Android Foreground Service
# ============================================================
# Este archivo corre como un proceso separado de Android.
# Android lo mantiene vivo aunque el usuario cierre la app.
# Requiere declarar en buildozer.spec:
#   services = Recordatorio:service.py
#
# El proceso revisa el archivo JSON de recordatorios cada
# minuto y dispara notificaciones nativas cuando corresponde.
# ============================================================

import json
import os
import time
import random
from datetime import datetime

from kivy.utils import platform

# ── Android imports ──────────────────────────────────────────
if platform == "android":
    from jnius import autoclass
    from android import api_version
    ANDROID = True
else:
    ANDROID = False


# ── Ruta al archivo de datos ─────────────────────────────────
def get_data_path(filename):
    if ANDROID:
        # Mismo directorio que usa main.py
        PythonService = autoclass('org.kivy.android.PythonService')
        base = PythonService.mService.getFilesDir().getAbsolutePath()
        return os.path.join(base, filename)
    return filename


# ── Enviar notificación nativa ────────────────────────────────
def send_notification(title, message):
    if not ANDROID:
        print(f"[NOTIF] {title} | {message}")
        return
    try:
        PythonService       = autoclass('org.kivy.android.PythonService')
        Context             = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Builder             = autoclass('androidx.core.app.NotificationCompat$Builder')

        service = PythonService.mService

        notif_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
        channel_id    = "canal_hospital_01"

        if api_version >= 26:
            channel = NotificationChannel(
                channel_id,
                "Recordatorios de Salud",
                NotificationManager.IMPORTANCE_HIGH,
            )
            channel.enableVibration(True)
            channel.enableLights(True)
            notif_manager.createNotificationChannel(channel)

        builder = Builder(service, channel_id)
        builder.setSmallIcon(service.getApplicationInfo().icon)
        builder.setContentTitle(str(title))
        builder.setContentText(str(message))
        builder.setStyle(
            autoclass('androidx.core.app.NotificationCompat$BigTextStyle')()
            .bigText(str(message))
        )
        builder.setAutoCancel(True)
        builder.setPriority(2)          # PRIORITY_MAX
        builder.setVibrate([0, 300, 200, 300])

        notif_manager.notify(random.randint(1, 999999), builder.build())
        print(f"[SERVICE NOTIF OK] {title}")

    except Exception as e:
        print(f"[SERVICE NOTIF ERROR] {e}")


# ── Revisar recordatorios de medicamentos ────────────────────
def check_medications(data_path):
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            medications = json.load(f)
    except Exception:
        return

    now = datetime.now()

    for med in medications:
        try:
            med_name       = med["med_name"]
            interval_hours = int(med["interval_hours"])
            meds_per_dose  = int(med["meds_per_dose"])
            start_time_str = med["start_time"]        # "HH:MM"
            days           = int(med["days"])

            start_h, start_m = map(int, start_time_str.split(":"))
            start_base = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)

            # Calcular la próxima dosis a partir de ahora
            dose_time = start_base
            end_time  = start_base.replace(hour=0, minute=0) + __import__("datetime").timedelta(days=days)

            while dose_time < now - __import__("datetime").timedelta(minutes=1):
                dose_time += __import__("datetime").timedelta(hours=interval_hours)

            # ¿Toca ahora? (ventana de ±1 minuto)
            diff = abs((dose_time - now).total_seconds())
            if diff <= 60:
                send_notification(
                    "💊 Es hora de tomar tu medicamento",
                    f"{med_name}  —  {meds_per_dose} unidad(es)  ({dose_time.strftime('%H:%M')})",
                )

        except Exception as e:
            print(f"[SERVICE MED ERROR] {med.get('med_name', '?')}: {e}")


# ── Revisar citas médicas ─────────────────────────────────────
def check_appointments(data_path):
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            appointments = json.load(f)
    except Exception:
        return

    now = datetime.now()

    for apt in appointments:
        try:
            name  = apt["name"]
            h, m  = map(int, apt["time"].split(":"))
            apt_dt = datetime(
                int(apt["year"]), int(apt["month"]), int(apt["day"]), h, m
            )

            diff_s = (apt_dt - now).total_seconds()

            # 1 día antes (ventana ±60 s)
            if abs(diff_s - 86400) <= 60:
                send_notification("📅 Recordatorio de Cita Médica", f"Tu cita '{name}' es mañana")

            # 1 hora antes (ventana ±60 s)
            elif abs(diff_s - 3600) <= 60:
                send_notification("📅 Recordatorio de Cita Médica", f"Tu cita '{name}' es en 1 hora")

            # En el momento (ventana ±60 s)
            elif abs(diff_s) <= 60:
                send_notification("📅 ¡Cita Médica Ahora!", f"Es la hora de tu cita: {name}")

        except Exception as e:
            print(f"[SERVICE APT ERROR] {apt.get('name', '?')}: {e}")


# ── Bucle principal del servicio ──────────────────────────────
if __name__ == "__main__":
    print("[SERVICE] Iniciado")

    med_path = get_data_path("medications_data.json")
    apt_path = get_data_path("appointments_data.json")

    while True:
        try:
            check_medications(med_path)
            check_appointments(apt_path)
        except Exception as e:
            print(f"[SERVICE LOOP ERROR] {e}")

        time.sleep(60)   # Revisa cada 60 segundos
