import os

manifest_path = os.path.join(
    os.getcwd(),
    ".buildozer", "android", "platform", "build-arm64-v8a_armeabi-v7a",
    "dists", "apprecordatorios", "AndroidManifest.xml"
)

receiver_xml = """
    <receiver
        android:name="com.recordatorios.BootReceiver"
        android:enabled="true"
        android:exported="true">
        <intent-filter>
            <action android:name="android.intent.action.BOOT_COMPLETED" />
            <action android:name="android.intent.action.QUICKBOOT_POWERON" />
            <category android:name="android.intent.category.DEFAULT" />
        </intent-filter>
    </receiver>
"""

if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        content = f.read()
    if "BootReceiver" not in content:
        content = content.replace("</application>", receiver_xml + "</application>")
        with open(manifest_path, "w") as f:
            f.write(content)
        print("[HOOK] BootReceiver inyectado en AndroidManifest.xml")
    else:
        print("[HOOK] BootReceiver ya estaba en el manifest")
else:
    print(f"[HOOK] Manifest no encontrado en: {manifest_path}")
    print("[HOOK] Rutas disponibles:")
    base = os.path.join(os.getcwd(), ".buildozer", "android", "platform")
    if os.path.exists(base):
        for root, dirs, files in os.walk(base):
            for f in files:
                if f == "AndroidManifest.xml":
                    print(" ", os.path.join(root, f))
