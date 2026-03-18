[app]

# ── Información de la aplicación ──────────────────────────────────────────────
title           = PhoneBooster Pro
package.name    = phoneboosterpro
package.domain  = com.devtools

source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,json

version         = 1.0.0

# ── Dependencias Python ────────────────────────────────────────────────────────
requirements = python3,kivy==2.3.0,pillow,android,pyjnius,requests

# ── Orientación y pantalla ────────────────────────────────────────────────────
orientation     = portrait
fullscreen      = 0
android.wakelock = False

# ── Íconos y splash ───────────────────────────────────────────────────────────
# icon.filename     = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# ── Permisos Android necesarios ───────────────────────────────────────────────
android.permissions = \
    READ_EXTERNAL_STORAGE,\
    WRITE_EXTERNAL_STORAGE,\
    MANAGE_EXTERNAL_STORAGE,\
    KILL_BACKGROUND_PROCESSES,\
    GET_TASKS,\
    RECEIVE_BOOT_COMPLETED,\
    ACCESS_NETWORK_STATE,\
    INTERNET,\
    PACKAGE_USAGE_STATS,\
    QUERY_ALL_PACKAGES,\
    REQUEST_INSTALL_PACKAGES,\
    CLEAR_APP_CACHE

# ── SDK Android ───────────────────────────────────────────────────────────────
android.minapi   = 26
android.ndk      = 25b
android.sdk      = 33
android.ndk_api  = 21
android.archs    = arm64-v8a, armeabi-v7a

# Gradle & build tools
android.gradle_dependencies =
android.enable_androidx       = True
android.accept_sdk_license    = True

# ── Bootstrap ─────────────────────────────────────────────────────────────────
p4a.bootstrap = sdl2

# ── Buildozer ─────────────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
