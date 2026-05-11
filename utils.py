# ============================================================
# utils.py  --  Funciones compartidas entre main.py y service.py
# ============================================================
import os
import json
import random
from datetime import datetime, timedelta

from kivy.utils import platform

if platform == "android":
    from jnius import autoclass
    from android import api_version
    ANDROID = True
else:
    ANDROID = False


# ============================================================
# RUTA SEGURA DE ALMACENAMIENTO
# ============================================================
def get_data_path(filename):
    """
    Android: /data/user/0/<paquete>/files/
    PC:      directorio actual
    """
    if ANDROID:
        try:
            PythonService = autoclass('org.kivy.android.PythonService')
            base = PythonService.mService.getFilesDir().getAbsolutePath()
            return os.path.join(base, filename)
        except Exception:
            try:
                from kivy.app import App
                return os.path.join(App.get_running_app().user_data_dir, filename)
            except Exception:
                pass
    return filename


# ============================================================
# ALARMA EXACTA CON ALARMMANAGER
# ============================================================
def schedule_alarm(trigger_epoch_ms, title, message):
    if not ANDROID:
        return
    try:
        PythonService = autoclass('org.kivy.android.PythonService')
        Context       = autoclass('android.content.Context')
        AlarmManager  = autoclass('android.app.AlarmManager')
        Intent        = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')

        try:
            ctx = PythonService.mService
        except Exception:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity

        alarm_mgr = ctx.getSystemService(Context.ALARM_SERVICE)

        intent = Intent(ctx, PythonService)
        intent.putExtra("notif_title",   str(title))
        intent.putExtra("notif_message", str(message))
        intent.setAction("com.recordatorios.ALARM")

        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if api_version >= 31:
            flags = flags | 0x04000000  # FLAG_MUTABLE

        pending = PendingIntent.getService(
            ctx,
            random.randint(1, 999999),
            intent,
            flags,
        )

        alarm_mgr.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            int(trigger_epoch_ms),
            pending,
        )
        print(f"[ALARM] Programada epoch_ms={trigger_epoch_ms}: {title}")
    except Exception as e:
        print(f"[ALARM ERROR] {e}")


# ============================================================
# ENVIO DE NOTIFICACION NATIVA
# ============================================================
def send_notification(title, message):
    if not ANDROID:
        print(f"[NOTIF PC] {title} | {message}")
        return
    try:
        Context             = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        Builder             = autoclass('androidx.core.app.NotificationCompat$Builder')
        BigTextStyle        = autoclass('androidx.core.app.NotificationCompat$BigTextStyle')

        try:
            ctx = autoclass('org.kivy.android.PythonService').mService
        except Exception:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity

        notif_manager = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
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

        builder = Builder(ctx, channel_id)
        builder.setSmallIcon(ctx.getApplicationInfo().icon)
        builder.setContentTitle(str(title))
        builder.setContentText(str(message))
        builder.setStyle(BigTextStyle().bigText(str(message)))
        builder.setAutoCancel(True)
        builder.setPriority(2)
        builder.setVibrate([0, 300, 200, 300])

        notif_manager.notify(random.randint(1, 999999), builder.build())
        print(f"[NOTIF OK] {title}")
    except Exception as e:
        print(f"[NOTIF ERROR] {e}")


# ============================================================
# REPROGRAMAR ALARMAS (para usar desde main.py tras reinicio)
# ============================================================
def reprogramar_alarmas():
    print("[UTILS] Reprogramando alarmas guardadas...")
    now = datetime.now()

    # Medicamentos
    med_path = get_data_path("medications_data.json")
    try:
        with open(med_path, "r", encoding="utf-8") as f:
            medications = json.load(f)
    except Exception:
        medications = []

    for med in medications:
        try:
            h, m = map(int, med["start_time"].split(":"))
            interval_hours = int(med["interval_hours"])
            meds_per_dose = int(med["meds_per_dose"])
            days = int(med["days"])
            dose_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            while dose_time <= now:
                dose_time += timedelta(hours=interval_hours)
            end_time = now + timedelta(days=days)
            while dose_time < end_time:
                schedule_alarm(
                    int(dose_time.timestamp() * 1000),
                    "Es hora de tomar tu medicamento",
                    f"{med['med_name']} -- {meds_per_dose} unidad(es) ({dose_time.strftime('%H:%M')})"
                )
                dose_time += timedelta(hours=interval_hours)
        except Exception as e:
            print(f"[UTILS MED ERROR] {med.get('med_name', '?')}: {e}")

    # Citas
    apt_path = get_data_path("appointments_data.json")
    try:
        with open(apt_path, "r", encoding="utf-8") as f:
            appointments = json.load(f)
    except Exception:
        appointments = []

    for apt in appointments:
        try:
            h, m = map(int, apt["time"].split(":"))
            apt_dt = datetime(int(apt["year"]), int(apt["month"]), int(apt["day"]), h, m)
            alerts = [
                (apt_dt - timedelta(days=1), f"Tu cita {apt['name']} es manana"),
                (apt_dt - timedelta(hours=1), f"Tu cita {apt['name']} es en 1 hora"),
                (apt_dt, f"Es la hora de tu cita: {apt['name']}")
            ]
            for alert_time, msg in alerts:
                if alert_time > now:
                    schedule_alarm(
                        int(alert_time.timestamp() * 1000),
                        "Recordatorio de Cita Medica",
                        msg
                    )
        except Exception as e:
            print(f"[UTILS APT ERROR] {apt.get('name', '?')}: {e}")

    print("[UTILS] Reprogramacion completada")
