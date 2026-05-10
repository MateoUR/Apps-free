# ============================================================
# service.py  —  Android Foreground Service
# ============================================================
# Coloca este archivo en la raíz del proyecto junto a main.py.
#
# Declarar en buildozer.spec:
#   services = Recordatorio:service.py:foreground
#
# Este proceso:
#  1. Arranca como Foreground Service (no puede ser matado)
#  2. Al recibir ALARM: muestra la notificación inmediatamente
#  3. Al recibir BOOT_COMPLETED: reprograma todas las alarmas
#     guardadas en los JSON
# ============================================================

import json
import os
import random
import time
from datetime import datetime, timedelta

from kivy.utils import platform

if platform == "android":
    from jnius import autoclass
    from android import api_version, AndroidService
    ANDROID = True
else:
    ANDROID = False

# Importar funciones compartidas
from utils import get_data_path, schedule_alarm, send_notification


# ============================================================
# REPROGRAMAR ALARMAS TRAS REINICIO
# Lee los JSON guardados y vuelve a registrar con AlarmManager
# todas las alarmas que aún están en el futuro.
# ============================================================
def reprogramar_alarmas():
    print("[SERVICE] Reprogramando alarmas tras reinicio...")

    # ── Medicamentos ──────────────────────────────────────────
    med_path = get_data_path("medications_data.json")
    try:
        with open(med_path, "r", encoding="utf-8") as f:
            medications = json.load(f)
    except Exception:
        medications = []

    now = datetime.now()
    for med in medications:
        try:
            med_name       = med["med_name"]
            interval_hours = int(med["interval_hours"])
            meds_per_dose  = int(med["meds_per_dose"])
            days           = int(med["days"])
            h, m           = map(int, med["start_time"].split(":"))

            # Primera dosis del día actual
            dose_time = now.replace(hour=h, minute=m, second=0, microsecond=0)

            # Avanzar hasta la siguiente dosis futura
            while dose_time <= now:
                dose_time += timedelta(hours=interval_hours)

            # Programar las dosis que queden dentro del período
            end_time = now + timedelta(days=days)
            while dose_time < end_time:
                title   = "Es hora de tomar tu medicamento"
                message = (
                    f"{med_name}  —  {meds_per_dose} unidad(es)"
                    f"  ({dose_time.strftime('%H:%M')})"
                )
                schedule_alarm(int(dose_time.timestamp() * 1000), title, message)
                dose_time += timedelta(hours=interval_hours)

        except Exception as e:
            print(f"[SERVICE BOOT MED ERROR] {med.get('med_name', '?')}: {e}")

    # ── Citas ─────────────────────────────────────────────────
    apt_path = get_data_path("appointments_data.json")
    try:
        with open(apt_path, "r", encoding="utf-8") as f:
            appointments = json.load(f)
    except Exception:
        appointments = []

    for apt in appointments:
        try:
            name   = apt["name"]
            h, m   = map(int, apt["time"].split(":"))
            apt_dt = datetime(
                int(apt["year"]), int(apt["month"]), int(apt["day"]), h, m
            )

            alerts = [
                (apt_dt - timedelta(days=1),  f"Tu cita {name} es mañana"),
                (apt_dt - timedelta(hours=1), f"Tu cita {name} es en 1 hora"),
                (apt_dt,                       f"Es la hora de tu cita: {name}"),
            ]
            for alert_time, msg in alerts:
                if alert_time > now:
                    schedule_alarm(
                        int(alert_time.timestamp() * 1000),
                        "Recordatorio de Cita Médica",
                        msg,
                    )
        except Exception as e:
            print(f"[SERVICE BOOT APT ERROR] {apt.get('name', '?')}: {e}")

    print("[SERVICE] Reprogramación completada")


# ============================================================
# PUNTO DE ENTRADA DEL SERVICIO
# ============================================================
if __name__ == "__main__":
    print("[SERVICE] Iniciado")

    if not ANDROID:
        print("[SERVICE] No es Android, saliendo.")
        exit(0)

    # ── Iniciar como Foreground Service (OBLIGATORIO) ─────────
    # Sin esto Android mata el proceso en segundos.
    service = AndroidService(
        "Recordatorios activos",
        "Vigilando tus recordatorios de salud...",
    )
    service.start("service_started")
    print("[SERVICE] Foreground Service activo")

    # ── Leer el intent que despertó este servicio ─────────────
    try:
        PythonService = autoclass('org.kivy.android.PythonService')
        intent = PythonService.mService.getIntent()
        action = intent.getAction() if intent else None
        print(f"[SERVICE] Action recibida: {action}")
    except Exception as e:
        print(f"[SERVICE] Error al leer intent: {e}")
        action = None

    if action == "com.recordatorios.ALARM":
        # ── Alarma exacta disparada: mostrar notificación ─────
        try:
            title   = intent.getStringExtra("notif_title") or "Recordatorio"
            message = intent.getStringExtra("notif_message") or ""
            send_notification(title, message)
        except Exception as e:
            print(f"[SERVICE ALARM ERROR] {e}")
        # Detener el servicio tras mostrar la notificación
        service.stop()

    elif action in (
        "android.intent.action.BOOT_COMPLETED",
        "android.intent.action.QUICKBOOT_POWERON",
    ):
        # ── Boot completado: reprogramar todas las alarmas ────
        reprogramar_alarmas()
        service.stop()

    else:
        # ── Inicio manual desde main.py (permisos concedidos) ─
        # Mantener el servicio vivo en segundo plano revisando
        # periódicamente (respaldo por si AlarmManager falla).
        print("[SERVICE] Modo vigilancia en segundo plano activo")
        med_path = get_data_path("medications_data.json")
        apt_path = get_data_path("appointments_data.json")

        while True:
            try:
                now = datetime.now()

                # Revisar medicamentos (ventana ±60 s)
                try:
                    with open(med_path, "r", encoding="utf-8") as f:
                        meds = json.load(f)
                    for med in meds:
                        h, m = map(int, med["start_time"].split(":"))
                        interval_hours = int(med["interval_hours"])
                        dose_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                        while dose_time < now - timedelta(minutes=1):
                            dose_time += timedelta(hours=interval_hours)
                        if abs((dose_time - now).total_seconds()) <= 60:
                            send_notification(
                                "Es hora de tomar tu medicamento",
                                f"{med['med_name']}  —  {med['meds_per_dose']} unidad(es)"
                                f"  ({dose_time.strftime('%H:%M')})",
                            )
                except Exception as e:
                    print(f"[SERVICE LOOP MED] {e}")

                # Revisar citas (ventana ±60 s)
                try:
                    with open(apt_path, "r", encoding="utf-8") as f:
                        apts = json.load(f)
                    for apt in apts:
                        h, m   = map(int, apt["time"].split(":"))
                        apt_dt = datetime(
                            int(apt["year"]), int(apt["month"]),
                            int(apt["day"]), h, m
                        )
                        diff = (apt_dt - now).total_seconds()
                        name = apt["name"]
                        if abs(diff - 86400) <= 60:
                            send_notification(
                                "Recordatorio de Cita Médica",
                                f"Tu cita '{name}' es mañana",
                            )
                        elif abs(diff - 3600) <= 60:
                            send_notification(
                                "Recordatorio de Cita Médica",
                                f"Tu cita '{name}' es en 1 hora",
                            )
                        elif abs(diff) <= 60:
                            send_notification(
                                "¡Cita Médica Ahora!",
                                f"Es la hora de tu cita: {name}",
                            )
                except Exception as e:
                    print(f"[SERVICE LOOP APT] {e}")

            except Exception as e:
                print(f"[SERVICE LOOP ERROR] {e}")

            time.sleep(60)
