[app]
title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0

# PyCryptodome और Kivy के लिए बिल्कुल सटीक रिक्वायरमेंट्स
requirements = python3,kivy,pycryptodome,sqlite3

orientation = portrait
fullscreen = 1

# एंड्रॉइड आर्किटेक्चर और API सेटिंग्स
android.api = 33
android.minapi = 24
android.ndk_api = 21
android.archs = arm64-v8a

# ऐप के लिए जरूरी परमिशन सेटिंग्स
android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
