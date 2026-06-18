import os
import time
import sqlite3
import base64

# PyCryptodome Modules (سپر اسٹیبل اینڈرائیڈ کرپٹو)
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

# Kivy UX Modules
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserIconView

# --- اینڈرائیڈ کے لیے مخصوص مستحکم سیٹنگز اور پاتھ ---
if platform == 'android':
    from android.storage import app_storage_path
    from android.permissions import request_permissions, Permission
    DB_FILE = os.path.join(app_storage_path(), ".vault.db")
    DEFAULT_PATH = "/storage/emulated/0" 
else:
    DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".vault.db")
    DEFAULT_PATH = "."

# --- کرپٹوگرافی اور کور انجن (v5.6 - PyCryptodome الائنڈ) ---
def derive_keys(pin, salt):
    # PBKDF2 کے ذریعے 64 بائٹس کی کیز بنانا (100k Iterations)
    stretched = PBKDF2(pin.encode(), salt, dkLen=64, count=100000, hmac_hash_module=SHA256)
    return stretched[:32], stretched[32:]

def hash_pin(pin, salt):
    return PBKDF2(pin.encode(), salt, dkLen=32, count=100000, hmac_hash_module=SHA256).hex()

def capture_intruder():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if platform == 'android':
        try:
            import subprocess
            photo_name = os.path.join(app_storage_path(), f"intruder_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
            subprocess.run(["termux-camera-photo", "-c", "1", photo_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    try:
        log_path = os.path.join(app_storage_path() if platform == 'android' else '.', "security_brute_logs.txt")
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] CRITICAL: 3 Unauthorized PIN attempts detected.\n")
    except Exception:
        pass

def encrypt_aes256(data_bytes, pin):
    salt = get_random_bytes(16)
    aes_key, hmac_key = derive_keys(pin, salt)
    iv = get_random_bytes(16)
    
    # PKCS7 Padding
    pad_len = 16 - (len(data_bytes) % 16)
    padded_data = data_bytes + bytes([pad_len] * pad_len)
    
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded_data)
    
    # HMAC-SHA256 برائے انٹیگریٹی چیلنج
    hmac_obj = HMAC.new(hmac_key, iv + ciphertext, digestmod=SHA256)
    mac = hmac_obj.digest()
    
    combined = salt + iv + mac + ciphertext
    return base64.urlsafe_b64encode(combined).decode()

def decrypt_aes256(enc_data_b64, pin):
    try:
        combined = base64.urlsafe_b64decode(enc_data_b64.encode())
        if len(combined) < 64: return None
        salt, iv, mac_stored, ciphertext = combined[:16], combined[16:32], combined[32:64], combined[64:]
        
        aes_key, hmac_key = derive_keys(pin, salt)
        
        # HMAC ویریفیکیشن
        hmac_obj = HMAC.new(hmac_key, iv + ciphertext, digestmod=SHA256)
        try:
            hmac_obj.verify(mac_stored)
        except Exception:
            return b"[X] INTEGRITY ERROR"
            
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        padded_msg = cipher.decrypt(ciphertext)
        
        # Unpadding
        pad_len = padded_msg[-1]
        if pad_len < 1 or pad_len > 16: return None
        return padded_msg[:-pad_len]
    except Exception:
        return None

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, pin_hash TEXT, pin_salt TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS secrets (id INTEGER PRIMARY KEY, title TEXT, encrypted_data TEXT)')
    cursor.execute("PRAGMA table_info(secrets)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_file' not in columns:
        cursor.execute("ALTER TABLE secrets ADD COLUMN is_file INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

# --- Kivy UI ڈیزائن (KV Stream) ---
KV_UI = """
ScreenManager:
    LoginScreen:
    MenuScreen:
    TextSaveScreen:
    FileSaveScreen:
    ViewSecretsScreen:
    SecurityLogScreen:

<LoginScreen>
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 15
        Label:
            text: 'KEEP SECRET VIP WALLET v5.6'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: '80dp'
        TextInput:
            id: pin_input
            hint_text: 'Enter Master PIN'
            password: True
            multiline: False
            size_hint_y: None
            height: '50dp'
        Button:
            text: 'Unlock Vault'
            size_hint_y: None
            height: '50dp'
            background_color: 0, 0.7, 0.3, 1
            on_press: root.process_login()
        Label:
            id: status_lbl
            text: 'Status: Safe-Locked'
            color: 1, 0.3, 0.3, 1

<MenuScreen>
    name: 'menu'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        Label:
            text: 'SYSTEM MAIN MENU'
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: '50dp'
        Button:
            text: '1. Hide Secret Message (Text)'
            on_press: root.navigate_to('text_save')
        Button:
            text: '2. Hide Secret File (Media/PDF)'
            on_press: root.navigate_to('file_save')
        Button:
            text: '3. View Stored Secrets'
            on_press: root.navigate_to_secrets()
        Button:
            text: '4. Cryptographic Audit Logs'
            on_press: root.navigate_to('crypto_logs')
        Button:
            text: '5. Exit & Lock Session'
            background_color: 0.8, 0.2, 0.2, 1
            on_press: root.lock_vault()

<TextSaveScreen>
    name: 'text_save'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        Label:
            text: 'HIDE SECRET TEXT'
            bold: True
        TextInput:
            id: text_title
            hint_text: 'Enter Title/Label'
            size_hint_y: None
            height: '45dp'
        TextInput:
            id: text_content
            hint_text: 'Enter Secret Message Here...'
            multiline: True
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 10
            Button:
                text: 'Save Secret'
                background_color: 0, 0.6, 0.8, 1
                on_press: root.save_text()
            Button:
                text: 'Back'
                on_press: root.back_to_menu()

<FileSaveScreen>
    name: 'file_save'
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        Label:
            text: 'SELECT FILE TO ENCRYPT'
            size_hint_y: None
            height: '40dp'
            bold: True
        FileChooserIconView:
            id: file_chooser
            path: app.get_default_path()
        BoxLayout:
            size_hint_y: None
            height: '50dp'
            spacing: 10
            Button:
                text: 'Encrypt Selected File'
                background_color: 0, 0.6, 0.8, 1
                on_press: root.encrypt_file()
            Button:
                text: 'Back'
                on_press: root.back_to_menu()

<ViewSecretsScreen>
    name: 'view_secrets'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        Label:
            text: 'STORED VAULT ASSETS'
            bold: True
            size_hint_y: None
            height: '40dp'
        TextInput:
            id: secret_id_input
            hint_text: 'Enter Secret ID to View'
            size_hint_y: None
            height: '45dp'
        TextInput:
            id: double_pin_verify
            hint_text: 'Re-enter PIN for Double-Verification'
            password: True
            multiline: False
            size_hint_y: None
            height: '45dp'
        Button:
            text: 'Decrypt & Display (Double PIN Lock)'
            background_color: 0.9, 0.6, 0, 1
            size_hint_y: None
            height: '45dp'
            on_press: root.verify_and_decrypt()
        TextInput:
            id: output_box
            hint_text: 'Decrypted Content Output Field...'
            readonly: True
        Button:
            text: 'Back to Menu'
            size_hint_y: None
            height: '45dp'
            on_press: root.back_to_menu()

<SecurityLogScreen>
    name: 'crypto_logs'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        Label:
            text: 'CRYPTOGRAPHIC SECURITY AUDIT'
            bold: True
            size_hint_y: None
            height: '40dp'
        Label:
            text: 'Engine: Pure PyCryptodome AES-256 (CBC)\\nIntegrity: HMAC-SHA256 Signatures Active\\nHardening: PBKDF2 Key Stretching (100k Iterations)\\nAnti-Tamper: Local Logs & Camera Armed\\nSession Lock: 60s Rolling Timer Active'
            halign: 'center'
        Button:
            text: 'Back'
            size_hint_y: None
            height: '45dp'
            on_press: root.back_to_menu()
"""

# --- اسکرین کلاسز کی لاجک ---
class LoginScreen(Screen):
    attempts = 0
    def process_login(self):
        pin = self.ids.pin_input.text
        if len(pin) < 4:
            self.ids.status_lbl.text = "Weak PIN Structure!"
            return
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT pin_hash, pin_salt FROM config WHERE id = 1")
        row = cursor.fetchone()
        
        if not row:
            salt = os.urandom(16).hex()
            db_hash = hash_pin(pin, salt.encode())
            cursor.execute("INSERT INTO config (id, pin_hash, pin_salt) VALUES (1, ?, ?)", (db_hash, salt))
            conn.commit()
            App.get_running_app().session_pin = pin
            self.manager.current = 'menu'
            App.get_running_app().start_timeout_timer()
        else:
            db_hash, db_salt = row[0], row[1]
            if hash_pin(pin, db_salt.encode()) == db_hash:
                App.get_running_app().session_pin = pin
                self.manager.current = 'menu'
                App.get_running_app().start_timeout_timer()
            else:
                self.attempts += 1
                self.ids.status_lbl.text = f"Invalid PIN! Attempt {self.attempts}/3"
                if self.attempts >= 3:
                    capture_intruder()
                    App.get_running_app().stop()
        conn.close()

class MenuScreen(Screen):
    def navigate_to(self, screen_name):
        App.get_running_app().start_timeout_timer()
        self.manager.current = screen_name

    def navigate_to_secrets(self):
        App.get_running_app().start_timeout_timer()
        self.manager.get_screen('view_secrets').load_secrets()
        self.manager.current = 'view_secrets'

    def lock_vault(self):
        App.get_running_app().session_pin = ""
        App.get_running_app().stop_timeout_timer()
        self.manager.get_screen('login').ids.pin_input.text = ""
        self.manager.get_screen('login').ids.status_lbl.text = "Session Safely Cleared & Locked."
        self.manager.current = 'login'

class TextSaveScreen(Screen):
    def back_to_menu(self):
        App.get_running_app().start_timeout_timer()
        self.manager.current = 'menu'

    def save_text(self):
        App.get_running_app().start_timeout_timer()
        title = self.ids.text_title.text
        content = self.ids.text_content.text
        pin = App.get_running_app().session_pin
        if title and content and pin:
            enc_data = encrypt_aes256(content.encode('utf-8'), pin)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO secrets (title, encrypted_data, is_file) VALUES (?, ?, 0)", (title, enc_data))
            conn.commit()
            conn.close()
            self.ids.text_title.text = ""
            self.ids.text_content.text = ""
            self.manager.current = 'menu'

class FileSaveScreen(Screen):
    def back_to_menu(self):
        App.get_running_app().start_timeout_timer()
        self.manager.current = 'menu'

    def encrypt_file(self):
        App.get_running_app().start_timeout_timer()
        selection = self.ids.file_chooser.selection
        pin = App.get_running_app().session_pin
        if selection and pin:
            file_path = selection[0]
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                enc_data = encrypt_aes256(file_bytes, pin)
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO secrets (title, encrypted_data, is_file) VALUES (?, ?, 1)", (file_name, enc_data))
                conn.commit()
                conn.close()
                self.manager.current = 'menu'

class ViewSecretsScreen(Screen):
    def back_to_menu(self):
        App.get_running_app().start_timeout_timer()
        self.manager.current = 'menu'

    def load_secrets(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, is_file FROM secrets")
        records = cursor.fetchall()
        conn.close()
        
        output = "ID | Label | Type\n" + "-"*30 + "\n"
        for r in records:
            sec_type = "FILE" if r[2] == 1 else "TEXT"
            output += f"[{r[0]}] {r[1]} ({sec_type})\n"
        self.ids.output_box.text = output

    def verify_and_decrypt(self):
        App.get_running_app().start_timeout_timer()
        secret_id = self.ids.secret_id_input.text
        verify_pin = self.ids.double_pin_verify.text
        
        if not secret_id or not verify_pin:
            self.ids.output_box.text = "Error: Fields cannot be empty."
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT pin_hash, pin_salt FROM config WHERE id = 1")
        conf = cursor.fetchone()
        
        if hash_pin(verify_pin, conf[1].encode()) != conf[0]:
            self.ids.output_box.text = "[✘] SECURITY REJECTION: Re-verification PIN Failed!"
            conn.close()
            return
            
        cursor.execute("SELECT encrypted_data, is_file, title FROM secrets WHERE id = ?", (secret_id,))
        res = cursor.fetchone()
        conn.close()
        
        if res:
            decrypted_bytes = decrypt_aes256(res[0], verify_pin)
            if decrypted_bytes == b"[X] INTEGRITY ERROR" or decrypted_bytes is None:
                self.ids.output_box.text = "CRITICAL: Integrity Check Failed! Data Tampered."
            else:
                if res[1] == 0:
                    self.ids.output_box.text = f"Decrypted Text:\n\n{decrypted_bytes.decode('utf-8')}"
                else:
                    out_name = f"decrypted_{res[2]}"
                    out_path = os.path.join(app_storage_path() if platform == 'android' else '.', out_name)
                    with open(out_path, 'wb') as out_f:
                        out_f.write(decrypted_bytes)
                    self.ids.output_box.text = f"Success: File restored safely to:\n{out_path}"
        self.ids.double_pin_verify.text = ""

class SecurityLogScreen(Screen):
    def back_to_menu(self):
        App.get_running_app().start_timeout_timer()
        self.manager.current = 'menu'

# --- مین ایپ مینیجر ---
class KeepSecretVIPApp(App):
    session_pin = ""
    timeout_event = None

    def build(self):
        init_database()
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        return Builder.load_string(KV_UI)

    def get_default_path(self):
        return DEFAULT_PATH

    def start_timeout_timer(self):
        self.stop_timeout_timer()
        self.timeout_event = Clock.schedule_once(self.auto_lock_vault, 60)

    def stop_timeout_timer(self):
        if self.timeout_event:
            Clock.unschedule(self.timeout_event)

    def auto_lock_vault(self, dt):
        if self.root.current != 'login':
            self.session_pin = ""
            self.root.get_screen('login').ids.pin_input.text = ""
            self.root.get_screen('login').ids.status_lbl.text = "Session auto-locked due to inactivity."
            self.root.current = 'login'

if __name__ == '__main__':
    KeepSecretVIPApp().run()
            
