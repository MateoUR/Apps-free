# ============================================================
# IMPORTS
# ============================================================
import json
import os
import time
import threading
from datetime import datetime, timedelta

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.image import AsyncImage
from kivy.metrics import dp, sp

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# Solicitud de permisos en Android en tiempo de ejecución
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android import api_version
    ANDROID = True
except ImportError:
    ANDROID = False


def request_android_permissions():
    """
    Pide POST_NOTIFICATIONS (Android 13+) y VIBRATE en tiempo de ejecución.
    En versiones anteriores a Android 13 las notificaciones no necesitan
    permiso explícito, pero VIBRATE sí se declara en el manifest.
    """
    if not ANDROID:
        return
    perms = [Permission.VIBRATE]
    if api_version >= 33:          # Android 13+
        perms.append(Permission.POST_NOTIFICATIONS)
    request_permissions(perms)


# ============================================================
# CONSTANTES
# ============================================================
SUPPORT_EMAIL    = "mateo.underblade@gmail.com"
BG_MENU          = "bg_menu.png"
BG_MEDICATIONS   = "bg_medications.png"
BG_APPOINTMENTS  = "bg_appointments.png"
SND_BUTTON       = "sound_button.mp3"
SND_NOTIFICATION = "sound_notification.mp3"


# ============================================================
# SONIDO  (pygame primero; SoundLoader de Kivy como respaldo)
# ============================================================
try:
    import pygame
    pygame.mixer.init()
    _PYGAME_OK = True
except Exception:
    _PYGAME_OK = False

if not _PYGAME_OK:
    from kivy.core.audio import SoundLoader


def play_sound(path):
    """Reproduce un sonido en un hilo separado para no bloquear la UI."""
    def _play():
        try:
            if _PYGAME_OK:
                snd = pygame.mixer.Sound(path)
                snd.play()
            else:
                from kivy.core.audio import SoundLoader
                snd = SoundLoader.load(path)
                if snd:
                    snd.play()
        except Exception:
            pass  # Si el audio falla, la app sigue funcionando
    threading.Thread(target=_play, daemon=True).start()


# ============================================================
# HELPERS DE UI  (responsive: todo en dp/sp, sin px fijos)
# ============================================================
BTN_H      = dp(48)   # altura estándar de botón
INPUT_H    = dp(44)   # altura de TextInput
SPINNER_H  = dp(44)
PAD        = dp(12)   # padding general
SPC        = dp(10)   # spacing general
FONT_L     = sp(16)   # fuente labels
FONT_BTN   = sp(15)   # fuente botones


def make_button(text, **kwargs):
    """Botón estilo uniforme con tamaño relativo."""
    defaults = dict(
        text=text,
        size_hint_x=1,
        size_hint_y=None,
        height=BTN_H,
        font_size=FONT_BTN,
        background_color=(0.1, 0.45, 0.85, 0.88),
        color=(1, 1, 1, 1),
    )
    defaults.update(kwargs)
    btn = Button(**defaults)
    btn.bind(on_press=lambda *_: play_sound(SND_BUTTON))
    return btn


def make_label(text, **kwargs):
    defaults = dict(
        text=text,
        size_hint_y=None,
        height=dp(30),
        font_size=FONT_L,
        color=(0.05, 0.2, 0.5, 1),
        halign="left",
        valign="middle",
    )
    defaults.update(kwargs)
    lbl = Label(**defaults)
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def make_input(hint, **kwargs):
    defaults = dict(
        hint_text=hint,
        multiline=False,
        size_hint_y=None,
        height=INPUT_H,
        font_size=FONT_L,
    )
    defaults.update(kwargs)
    return TextInput(**defaults)


def make_spinner(text, values, **kwargs):
    defaults = dict(
        text=text,
        values=values,
        size_hint_x=1,
        size_hint_y=None,
        height=SPINNER_H,
        font_size=FONT_L,
    )
    defaults.update(kwargs)
    sp_widget = Spinner(**defaults)
    sp_widget.bind(text=lambda *_: play_sound(SND_BUTTON))
    return sp_widget


def add_background(screen, image_path):
    """Envuelve el contenido del Screen con una imagen de fondo estirada."""
    children = list(screen.children)
    for child in children:
        screen.remove_widget(child)
    root = FloatLayout()
    bg = AsyncImage(
        source=image_path,
        allow_stretch=True,
        keep_ratio=False,
        size_hint=(1, 1),
        pos_hint={"x": 0, "y": 0},
    )
    root.add_widget(bg)
    for child in reversed(children):
        root.add_widget(child)
    screen.add_widget(root)


# ============================================================
# MIXIN DE PERSISTENCIA
# ============================================================
class DataMixin:
    def load_data(self):
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)


# ============================================================
# MENÚ PRINCIPAL
# ============================================================
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        outer = FloatLayout()
        inner = BoxLayout(
            orientation="vertical",
            padding=PAD,
            spacing=SPC,
            size_hint=(0.85, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        inner.bind(minimum_height=inner.setter("height"))

        title = Label(
            text="App Recordatorios",
            size_hint_y=None,
            height=dp(50),
            font_size=sp(22),
            bold=True,
            color=(0.05, 0.2, 0.55, 1),
            halign="center",
        )
        title.bind(size=title.setter("text_size"))

        btn_med  = make_button("💊  Recordatorios de Medicamentos")
        btn_apt  = make_button("📅  Citas Médicas")
        btn_help = make_button("❓  Ayuda")

        btn_med.bind(on_press=lambda *_: setattr(self.manager, "current", "medications"))
        btn_apt.bind(on_press=lambda *_: setattr(self.manager, "current", "appointments"))
        btn_help.bind(on_press=lambda *_: setattr(self.manager, "current", "help"))

        inner.add_widget(title)
        inner.add_widget(btn_med)
        inner.add_widget(btn_apt)
        inner.add_widget(btn_help)
        outer.add_widget(inner)
        self.add_widget(outer)
        add_background(self, BG_MENU)


# ============================================================
# RECORDATORIOS DE MEDICAMENTOS
# ============================================================
class MedicationReminderScreen(DataMixin, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = "medications_data.json"
        self.medications = self.load_data()
        self._stop_flags = {}

        # ScrollView para que quepa en pantallas pequeñas
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(
            orientation="vertical",
            padding=PAD,
            spacing=SPC,
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))

        # --- Barra superior ---
        top_bar = BoxLayout(size_hint_y=None, height=BTN_H, spacing=SPC)
        btn_back = make_button("← Menú", size_hint_x=0.45)
        btn_back.bind(on_press=lambda *_: setattr(self.manager, "current", "menu"))
        btn_del = make_button("🗑 Borrar", size_hint_x=0.45)
        btn_del.bind(on_press=lambda *_: setattr(self.manager, "current", "delete_reminders"))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(btn_del)

        self.med_name_input  = make_input("Nombre del medicamento")
        self.quantity_input  = make_input("Cantidad total de pastillas")
        self.interval_input  = make_input("Cada cuántas horas (Ej: 8)")
        self.start_time_input= make_input("Hora inicial 24H  (Ej: 14:30)")
        self.days_input      = make_input("Días de tratamiento")

        chronic_row = BoxLayout(size_hint_y=None, height=BTN_H, spacing=SPC)
        chronic_row.add_widget(make_label("Paciente crónico (365 días):"))
        self.chronic_checkbox = CheckBox(size_hint_x=0.2)
        chronic_row.add_widget(self.chronic_checkbox)

        btn_set = make_button("✅  Establecer Recordatorio")
        btn_set.bind(on_press=self.set_reminder)

        self.status_label = make_label("Esperando datos...", color=(0.1, 0.4, 0.1, 1))

        for w in [top_bar,
                  make_label("Nombre del medicamento:"),
                  self.med_name_input,
                  make_label("Cantidad total de pastillas:"),
                  self.quantity_input,
                  make_label("Intervalo entre dosis (horas):"),
                  self.interval_input,
                  make_label("Hora de la primera dosis:"),
                  self.start_time_input,
                  make_label("Días de tratamiento:"),
                  self.days_input,
                  chronic_row,
                  btn_set,
                  self.status_label]:
            layout.add_widget(w)

        scroll.add_widget(layout)
        self.add_widget(scroll)
        add_background(self, BG_MEDICATIONS)

    def set_reminder(self, instance):
        med_name = self.med_name_input.text.strip()
        try:
            quantity       = int(self.quantity_input.text)
            interval_hours = int(self.interval_input.text)
            start_time     = datetime.strptime(self.start_time_input.text.strip(), "%H:%M")
            days           = 365 if self.chronic_checkbox.active else int(self.days_input.text)
        except ValueError:
            self.status_label.text = "⚠ Por favor, ingrese valores válidos."
            return

        if not med_name or quantity <= 0 or interval_hours <= 0 or days <= 0:
            self.status_label.text = "⚠ Complete todos los campos correctamente."
            return

        doses_per_day = max(1, 24 // interval_hours)
        total_doses   = days * doses_per_day
        meds_per_dose = max(1, quantity // total_doses)

        now = datetime.now()
        start_datetime = now.replace(
            hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0
        )
        if start_datetime < now:
            start_datetime += timedelta(hours=interval_hours)

        reminder_data = {
            "med_name":      med_name,
            "quantity":      quantity,
            "interval_hours":interval_hours,
            "start_time":    start_time.strftime("%H:%M"),
            "days":          days,
            "doses_per_day": doses_per_day,
            "meds_per_dose": meds_per_dose,
        }
        self.medications.append(reminder_data)
        self.save_data(self.medications)
        self.clear_inputs()

        stop_event = threading.Event()
        self._stop_flags[med_name] = stop_event
        threading.Thread(
            target=self.schedule_reminders,
            args=(reminder_data, start_datetime, stop_event),
            daemon=True,
        ).start()

        self.status_label.text = f"✔ Recordatorios establecidos para {med_name}."

    def schedule_reminders(self, reminder_data, start_datetime, stop_event):
        med_name      = reminder_data["med_name"]
        interval_hours= reminder_data["interval_hours"]
        meds_per_dose = reminder_data["meds_per_dose"]
        days          = reminder_data["days"]
        doses_per_day = reminder_data["doses_per_day"]
        current_time  = start_datetime

        for _ in range(days):
            for _ in range(doses_per_day):
                if stop_event.is_set():
                    return
                wait_seconds = (current_time - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    deadline = time.monotonic() + wait_seconds
                    while time.monotonic() < deadline:
                        if stop_event.is_set():
                            return
                        time.sleep(min(5, deadline - time.monotonic()))
                if not stop_event.is_set():
                    self._push_medication(med_name, meds_per_dose, current_time)
                current_time += timedelta(hours=interval_hours)

    def _push_medication(self, med_name, meds_per_dose, reminder_time):
        """Push notification: 'Es hora de tomar tu medicamento: <nombre>'"""
        title   = "💊 Es hora de tomar tu medicamento"
        message = f"{med_name}  —  {meds_per_dose} unidad(es)  ({reminder_time.strftime('%H:%M')})"
        send_notification(title, message)
        play_sound(SND_NOTIFICATION)

    def stop_reminder(self, med_name):
        if med_name in self._stop_flags:
            self._stop_flags[med_name].set()
            del self._stop_flags[med_name]

    def clear_inputs(self):
        self.med_name_input.text   = ""
        self.quantity_input.text   = ""
        self.interval_input.text   = ""
        self.start_time_input.text = ""
        self.days_input.text       = ""


# ============================================================
# CITAS MÉDICAS
# ============================================================
class MedicalAppointmentsScreen(DataMixin, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file   = "appointments_data.json"
        self.appointments = self.load_data()

        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(
            orientation="vertical",
            padding=PAD,
            spacing=SPC,
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))

        # --- Barra superior ---
        top_bar = BoxLayout(size_hint_y=None, height=BTN_H, spacing=SPC)
        btn_back = make_button("← Menú", size_hint_x=0.45)
        btn_back.bind(on_press=lambda *_: setattr(self.manager, "current", "menu"))
        btn_del = make_button("🗑 Borrar", size_hint_x=0.45)
        btn_del.bind(on_press=lambda *_: setattr(self.manager, "current", "delete_appointments"))
        top_bar.add_widget(btn_back)
        top_bar.add_widget(btn_del)

        self.name_input = make_input("Nombre de la cita")

        # Hora: HH y MM en fila
        time_row = BoxLayout(size_hint_y=None, height=SPINNER_H, spacing=SPC)
        self.hour_spinner   = make_spinner("HH", [f"{i:02}" for i in range(24)], size_hint_x=0.45)
        self.minute_spinner = make_spinner("MM", [f"{i:02}" for i in range(0, 60, 5)], size_hint_x=0.45)
        time_row.add_widget(self.hour_spinner)
        time_row.add_widget(make_label(":", size_hint_x=0.1, halign="center"))
        time_row.add_widget(self.minute_spinner)

        # Fecha en una sola fila compacta
        date_row = BoxLayout(size_hint_y=None, height=SPINNER_H, spacing=SPC)
        current_year = datetime.now().year
        self.day_spinner   = make_spinner("Día",  [str(i) for i in range(1, 32)])
        self.month_spinner = make_spinner("Mes",  [str(i) for i in range(1, 13)])
        self.year_spinner  = make_spinner("Año",  [str(i) for i in range(current_year, current_year + 7)])
        date_row.add_widget(self.day_spinner)
        date_row.add_widget(self.month_spinner)
        date_row.add_widget(self.year_spinner)

        btn_set = make_button("📅  Establecer Cita Médica")
        btn_set.bind(on_press=self.set_appointment)

        self.status_label = make_label("Esperando datos...", color=(0.1, 0.4, 0.1, 1))

        for w in [top_bar,
                  make_label("Nombre de la cita:"),
                  self.name_input,
                  make_label("Hora de la cita (HH : MM):"),
                  time_row,
                  make_label("Fecha  (Día / Mes / Año):"),
                  date_row,
                  btn_set,
                  self.status_label]:
            layout.add_widget(w)

        scroll.add_widget(layout)
        self.add_widget(scroll)
        add_background(self, BG_APPOINTMENTS)

    def set_appointment(self, instance):
        name   = self.name_input.text.strip()
        hour   = self.hour_spinner.text
        minute = self.minute_spinner.text
        day    = self.day_spinner.text
        month  = self.month_spinner.text
        year   = self.year_spinner.text

        if not name:
            self.status_label.text = "⚠ Ingrese un nombre para la cita."
            return
        if hour == "HH" or minute == "MM" or day == "Día" or month == "Mes" or year == "Año":
            self.status_label.text = "⚠ Seleccione fecha y hora completas."
            return
        try:
            apt_time = datetime.strptime(f"{day} {month} {year} {hour}:{minute}", "%d %m %Y %H:%M")
        except ValueError:
            self.status_label.text = "⚠ Fecha inválida (ese mes no tiene ese día)."
            return

        data = {"name": name, "time": apt_time.strftime("%H:%M"),
                "day": day, "month": month, "year": year}
        self.appointments.append(data)
        self.save_data(self.appointments)

        self.status_label.text = f"✔ Cita '{name}' — {apt_time.strftime('%d/%m/%Y %H:%M')}."

        # Reset
        self.name_input.text    = ""
        self.hour_spinner.text  = "HH"
        self.minute_spinner.text= "MM"
        self.day_spinner.text   = "Día"
        self.month_spinner.text = "Mes"
        self.year_spinner.text  = "Año"

        threading.Thread(
            target=self._schedule_alerts,
            args=(name, apt_time),
            daemon=True,
        ).start()

        self.manager.get_screen("delete_appointments").update_spinner_values()

    def _schedule_alerts(self, name, apt_time):
        """
        Push notifications anticipadas para citas:
          - 1 día antes  → 'Tu cita <nombre> es mañana'
          - 1 hora antes → 'Tu cita <nombre> es en 1 hora'
          - En el momento → 'Es la hora de tu cita: <nombre>'
        """
        alerts = [
            (apt_time - timedelta(days=1),  f"Tu cita {name} es mañana"),
            (apt_time - timedelta(hours=1), f"Tu cita {name} es en 1 hora"),
        ]
        for alert_time, msg in alerts:
            wait = (alert_time - datetime.now()).total_seconds()
            if wait <= 0:
                continue
            time.sleep(wait)
            send_notification("📅 Recordatorio de Cita Médica", msg)
            play_sound(SND_NOTIFICATION)

        wait = (apt_time - datetime.now()).total_seconds()
        if wait > 0:
            time.sleep(wait)
            send_notification("📅 ¡Cita Médica Ahora!", f"Es la hora de tu cita: {name}")
            play_sound(SND_NOTIFICATION)

    def _send_notification(self, title, message):
        send_notification(title, message)


# ============================================================
# PANTALLA DE AYUDA
# ============================================================
class HelpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()

        info = Label(
            text=f"Para soporte contactar:\n{SUPPORT_EMAIL}",
            size_hint=(0.8, None),
            height=dp(80),
            font_size=FONT_L,
            color=(0.05, 0.2, 0.5, 1),
            halign="center",
            valign="middle",
            pos_hint={"center_x": 0.5, "center_y": 0.55},
        )
        info.bind(size=info.setter("text_size"))

        btn_back = make_button("← Volver al Menú", size_hint=(0.6, None))
        btn_back.size_hint_y = None
        btn_back.height = BTN_H
        btn_back.pos_hint = {"center_x": 0.5, "y": 0.08}
        btn_back.bind(on_press=lambda *_: setattr(self.manager, "current", "menu"))

        layout.add_widget(info)
        layout.add_widget(btn_back)
        self.add_widget(layout)
        add_background(self, BG_MENU)


# ============================================================
# BORRAR RECORDATORIOS
# ============================================================
class DeleteRemindersScreen(DataMixin, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file   = "medications_data.json"
        self.medications = self.load_data()

        layout = BoxLayout(
            orientation="vertical",
            padding=PAD,
            spacing=SPC,
            size_hint=(0.85, None),
        )
        layout.bind(minimum_height=layout.setter("height"))

        outer = FloatLayout()
        layout.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        layout.add_widget(make_label("Selecciona el recordatorio a eliminar:"))

        self.reminder_spinner = make_spinner(
            "Seleccionar...",
            ["Seleccionar..."] + [r["med_name"] for r in self.medications],
        )
        layout.add_widget(self.reminder_spinner)

        btn_del = make_button("🗑  Eliminar Recordatorio")
        btn_del.bind(on_press=self.delete_reminder)
        layout.add_widget(btn_del)

        btn_back = make_button("← Regresar")
        btn_back.bind(on_press=lambda *_: setattr(self.manager, "current", "medications"))
        layout.add_widget(btn_back)

        outer.add_widget(layout)
        self.add_widget(outer)
        add_background(self, BG_MEDICATIONS)

    def delete_reminder(self, instance):
        sel = self.reminder_spinner.text
        if sel not in ("Seleccionar...", ""):
            self.manager.get_screen("medications").stop_reminder(sel)
            self.medications = [r for r in self.medications if r["med_name"] != sel]
            self.save_data(self.medications)
            self.update_spinner_values()

    def update_spinner_values(self):
        self.medications = self.load_data()
        self.reminder_spinner.values = (
            ["Seleccionar..."] + [r["med_name"] for r in self.medications]
        )
        self.reminder_spinner.text = "Seleccionar..."


# ============================================================
# BORRAR CITAS
# ============================================================
class DeleteAppointmentsScreen(DataMixin, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file    = "appointments_data.json"
        self.appointments = self.load_data()

        layout = BoxLayout(
            orientation="vertical",
            padding=PAD,
            spacing=SPC,
            size_hint=(0.85, None),
        )
        layout.bind(minimum_height=layout.setter("height"))

        outer = FloatLayout()
        layout.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        layout.add_widget(make_label("Selecciona la cita a eliminar:"))

        self.appointment_spinner = make_spinner(
            "Seleccionar...",
            ["Seleccionar..."] + [
                f"{a['name']} — {a['day']}/{a['month']} {a['year']} {a['time']}"
                for a in self.appointments
            ],
        )
        layout.add_widget(self.appointment_spinner)

        btn_del = make_button("🗑  Eliminar Cita")
        btn_del.bind(on_press=self.delete_appointment)
        layout.add_widget(btn_del)

        btn_back = make_button("← Regresar")
        btn_back.bind(on_press=lambda *_: setattr(self.manager, "current", "appointments"))
        layout.add_widget(btn_back)

        outer.add_widget(layout)
        self.add_widget(outer)
        add_background(self, BG_APPOINTMENTS)

    def delete_appointment(self, instance):
        sel = self.appointment_spinner.text
        if sel not in ("Seleccionar...", ""):
            sel_name = sel.split(" — ")[0]
            self.appointments = [a for a in self.appointments if a["name"] != sel_name]
            self.save_data(self.appointments)
            self.update_spinner_values()

    def update_spinner_values(self):
        self.appointments = self.load_data()
        self.appointment_spinner.values = ["Seleccionar..."] + [
            f"{a['name']} — {a['day']}/{a['month']} {a['year']} {a['time']}"
            for a in self.appointments
        ]
        self.appointment_spinner.text = "Seleccionar..."


# ============================================================
# NOTIFICACIÓN CENTRAL  (nativa Android > plyer > print)
# ============================================================
def send_notification(title, message):
    """
    Intenta enviar la notificación por el método más confiable disponible:
    1. API nativa de Android (android.app.Notification) vía pyjnius
    2. plyer como respaldo
    3. print como último recurso
    """
    if ANDROID:
        try:
            from jnius import autoclass, cast
            PythonActivity   = autoclass("org.kivy.android.PythonActivity")
            NotifManager     = autoclass("android.app.NotificationManager")
            NotifCompat      = autoclass("androidx.core.app.NotificationCompat")
            ChannelClass     = autoclass("android.app.NotificationChannel")
            context          = PythonActivity.mActivity

            CHANNEL_ID = "app_recordatorios_channel"
            manager = cast(
                "android.app.NotificationManager",
                context.getSystemService("notification")
            )

            # Crear canal (requerido Android 8+)
            if api_version >= 26:
                channel = ChannelClass(
                    CHANNEL_ID,
                    "Recordatorios",
                    NotifManager.IMPORTANCE_HIGH,
                )
                channel.enableVibration(True)
                manager.createNotificationChannel(channel)

            builder = NotifCompat.Builder(context, CHANNEL_ID)
            builder.setSmallIcon(autoclass("android.R$drawable").ic_dialog_info)
            builder.setContentTitle(title)
            builder.setContentText(message)
            builder.setAutoCancel(True)
            builder.setPriority(NotifCompat.PRIORITY_HIGH)

            import random
            manager.notify(random.randint(1, 99999), builder.build())
            return
        except Exception as e:
            print(f"[NOTIF nativa falló] {e}")

    # Respaldo: plyer
    if PLYER_AVAILABLE:
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name="App Recordatorios",
                timeout=10,
            )
            return
        except Exception:
            pass

    print(f"[NOTIF] {title} | {message}")


# ============================================================
# APP PRINCIPAL
# ============================================================
class ReminderApp(App):
    def build(self):
        # Pedir permisos al arrancar la app en Android
        request_android_permissions()

        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name="menu"))
        self.sm.add_widget(MedicationReminderScreen(name="medications"))
        self.sm.add_widget(MedicalAppointmentsScreen(name="appointments"))
        self.sm.add_widget(DeleteRemindersScreen(name="delete_reminders"))
        self.sm.add_widget(DeleteAppointmentsScreen(name="delete_appointments"))
        self.sm.add_widget(HelpScreen(name="help"))
        return self.sm


if __name__ == "__main__":
    ReminderApp().run()
