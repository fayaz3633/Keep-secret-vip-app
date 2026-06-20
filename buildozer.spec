[app]
title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 2.0

requirements = python3,kivy==2.3.0,pycryptodome

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk_api = 21
android.archs = arm64-v8a

android.permissions = CAMERA

log_level = 2
warn_on_root = 1
