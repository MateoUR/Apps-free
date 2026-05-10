// ============================================================
// BootReceiver.java
//
// UBICACIÓN CORRECTA (corrección de Corrección.txt §1):
//   <tu_proyecto>/src/com/recordatorios/BootReceiver.java
//
// En buildozer.spec agregar:
//   android.add_src = src
//   android.manifest.intent_filters = <receiver android:name="com.recordatorios.BootReceiver" android:exported="true"><intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/><action android:name="android.intent.action.QUICKBOOT_POWERON"/></intent-filter></receiver>
// ============================================================
package com.recordatorios;   // <-- paquete que coincide con la ruta src/com/recordatorios/

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();

        if (Intent.ACTION_BOOT_COMPLETED.equals(action)
                || "android.intent.action.QUICKBOOT_POWERON".equals(action)) {

            // Lanzar el Foreground Service de Python para reprogramar alarmas
            // Corrección: se pasa la action del intent para que service.py sepa
            // que fue disparado por BOOT_COMPLETED y ejecute reprogramar_alarmas()
            Intent serviceIntent = new Intent(context, org.kivy.android.PythonService.class);
            serviceIntent.setAction(action);   // <-- pasa BOOT_COMPLETED al service.py

            serviceIntent.putExtra("androidPrivate",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("androidArgument",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("serviceEntrypoint", "service.py");
            serviceIntent.putExtra("pythonName",        "Recordatorio");
            serviceIntent.putExtra("pythonHome",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("pythonPath",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("serviceStartAsForeground", "true");

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(serviceIntent);
            } else {
                context.startService(serviceIntent);
            }
        }
    }
}
