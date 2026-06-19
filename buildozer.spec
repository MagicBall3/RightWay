[app]
# (string) Title of your application
title = RightWay

# (string) Version of the application
version = 1.0

# (string) Package name
package.name = rightway

# (string) Package domain (needed for android app id)
package.domain = org.zrqcorp

# (string) Source code where the main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,ttf,wav,mp3,json,spec

# (list) Application requirements
# Добавляем sqlite3 на случай работы с базой данных
requirements = python3,pygame,sqlite3

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (string) Supported orientations
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# Жестко прописываем стабильную версию инструментов, чтобы сборщик не путался в логах
android.skip_update = False
android.accept_sdk_license = True

# (list) Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) The format used to package the app for release mode
android.release_artifact = apk
