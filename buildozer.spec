[app]
title = Keep Secret VIP
package.name = keepsecretvip
package.domain = org.fayaz
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0

# پلے اسٹور ریڈی لائبریریز
requirements = python3,kivy,cryptography,openssl,sqlite3

orientation = portrait
fullscreen = 1

# کلاؤڈ بلڈ آپٹیمائزیشن
android.api = 35
android.minapi = 24
android.ndk_api = 21
android.archs = arm64-v8a

# پلے اسٹور فرینڈلی پرمیشنز (کوئی ریجکشن چانس نہیں)
android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
