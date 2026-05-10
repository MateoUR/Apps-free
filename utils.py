# ============================================================
# utils.py  —  Funciones compartidas entre main.py y service.py
# ============================================================
# Coloca este archivo en la raíz del proyecto, junto a main.py
# y service.py.
# ============================================================
import os
import random

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
            # Funciona tanto desde main como desde service
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
# Corrección principal de Corrección.txt:
#   - Usa PendingIntent.getService en lugar de getBroadcast
#   - El intent apunta a PythonService, no a PythonActivity
#   - FLAG_IMMUTABLE requerido en Android 12+
# ============================================================
def schedule_alarm(trigger_epoch_ms, title, message):
    """
    Programa una alarma exacta que despierta al servicio aunque
    la app esté cerrada o el teléfono en modo Doze.

    trigger_epoch_ms : int — datetime.timestamp() * 1000
    title            : str — título de la notificación
    message          : str — cuerpo de la notificación
    """
    if not ANDROID:
        return
    try:
        PythonService = autoclass('org.kivy.android.PythonService')
        Context       = autoclass('android.content.Context')
        AlarmManager  = autoclass('android.app.AlarmManager')
        Intent        = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')

        # Obtener el contexto desde el servicio o desde la activity
        try:
            ctx = PythonService.mService
        except Exception:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity

        alarm_mgr = ctx.getSystemService(Context.ALARM_SERVICE)

        # ── CORRECCIÓN: getService, apuntando a PythonService ──
        intent = Intent(ctx, PythonService)
        intent.putExtra("notif_title",   str(title))
        intent.putExtra("notif_message", str(message))
        intent.setAction("com.recordatorios.ALARM")

        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if api_version >= 31:
            flags = flags | 0x04000000  # FLAG_MUTABLE (necesario para extras)

        pending = PendingIntent.getService(
            ctx,
            random.randint(1, 999999),
            intent,
            flags,
        )

        # setExactAndAllowWhileIdle despierta incluso en modo Doze
        alarm_mgr.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            int(trigger_epoch_ms),
            pending,
        )
        print(f"[ALARM] Programada epoch_ms={trigger_epoch_ms}: {title}")
    except Exception as e:
        print(f"[ALARM ERROR] {e}")


# ============================================================
# ENVÍO DE NOTIFICACIÓN NATIVA
# Funciona tanto desde main.py (PythonActivity) como desde
# service.py (PythonService).
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

        # Intentar obtener contexto desde servicio primero, luego activity
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
        builder.setPriority(2)          # PRIORITY_MAX
        builder.setVibrate([0, 300, 200, 300])

        notif_manager.notify(random.randint(1, 999999), builder.build())
        print(f"[NOTIF OK] {title}")
    except Exception as e:
        print(f"[NOTIF ERROR] {e}")
