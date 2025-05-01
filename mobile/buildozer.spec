[app]
title = AI Script Kill
package.name = aiscriptkill
package.domain = org.aiscriptkill
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,requests,pillow

# Android specific
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

# 构建设置
fullscreen = 0
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1 