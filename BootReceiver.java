// ============================================================
// BootReceiver.java
// Coloca este archivo en:
//   <tu_proyecto>/src/BootReceiver.java
// Y agrega en buildozer.spec:
//   android.add_src = src
// ============================================================
package com.recordatorios;

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

            // Arrancar el Foreground Service de Python
            Intent serviceIntent = new Intent(context, org.kivy.android.PythonService.class);
            serviceIntent.putExtra("androidPrivate",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("androidArgument",
                    context.getFilesDir().getAbsolutePath());
            serviceIntent.putExtra("serviceEntrypoint", "service.py");
            serviceIntent.putExtra("pythonName", "Recordatorio");
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
