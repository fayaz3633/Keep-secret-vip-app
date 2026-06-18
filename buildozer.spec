[app]
title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0

# پائپ لائن کو تیز کرنے کے لیے لائٹ ویٹ ریکوائرمنٹس
requirements = python3,kivy,pycryptodome,sqlite3

orientation = portrait
fullscreen = 1

# اینڈرائیڈ ٹارگٹ سیٹنگز
android.api = 33
android.minapi = 24
android.ndk_api = 21
android.archs = arm64-v8a

# والٹ کی سیکیورٹی پرمیشنز
android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
