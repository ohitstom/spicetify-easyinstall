import os
import sys
import ssl
import http.server
import subprocess
import ctypes
import threading
import time

PORT = 443
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
ENTRY = "127.0.0.1 upgrade.scdn.co"
COMMENT = "# Spicetify-Easyinstall Legacy Fix"

CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDFTCCAf2gAwIBAgIUBL/69RYm2e3KaZdQAMkTDOv+DFcwDQYJKoZIhvcNAQEL
BQAwGjEYMBYGA1UEAwwPdXBncmFkZS5zY2RuLmNvMB4XDTI2MDYxMzAyMjIwMloX
DTM2MDYxMDAyMjIwMlowGjEYMBYGA1UEAwwPdXBncmFkZS5zY2RuLmNvMIIBIjAN
BgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmDykcjEfXU45+nCi6fAGsTns8qID
kIWOMdfcLOo8i5G/MPW7KOYw71cW5Y+qFmyi9woGNVPrTncdU7iinLpmfv41XLiv
AZoSUtcvEcMZWd1+716/H9/pPWhuIJXsk9pO94U18g9sw8QV1vOBRAZZB/dmNr84
kS462OJL/2cQOiaYoPumJhXbO3r9RXbwInxakNbxlNPqPau/DHBGAEpUkcjzhQsc
welqWZsax7g26Q6I+Qkrg5gYEjhHTHL+S+IwH7CaOJ7rAwu1R6DEZO9ioOMVUAvL
EkiZlPQOaaBIkGwsHYM0cj/87AHk+rRL+IZPh8izQQ8Lv5xYGmJTt+ZWkwIDAQAB
o1MwUTAdBgNVHQ4EFgQU3TV7J94y/z7OToAhMRXZMSQgcxcwHwYDVR0jBBgwFoAU
3TV7J94y/z7OToAhMRXZMSQgcxcwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0B
AQsFAAOCAQEAI9PqggMvt825u1LLvK85UakLErsLKFw+x8cCBx4+/PaKw+kPg3LB
E9cW50EWmVDm/js4tTlDkSa83409M5RMK1ZHZbwH2Xtj8GTd9gw8AcRrEUaEeozj
+4Pr4hGa3nYN2VfM8qEJcqneJVVznGZJvtsZE7xj9+MpMSe5I0L5Wd74G8/FPt45
JYcrazqAFFDrwE6SgXJBleM7lGT0wqUQL1KrLiK9JyCpKm25Pp9WpDRpfVTFJNl7
LT0SEcmkbMe4uJxW7akyzuBeX/CDabi3ZCMgS6zCJ47jywpsQpnU4FvjPfNKLam+
HGBQAHkBG9kxLY/BHI5ejO1GNGW41PpvCg==
-----END CERTIFICATE-----"""

KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCYPKRyMR9dTjn6
cKLp8AaxOezyogOQhY4x19ws6jyLkb8w9bso5jDvVxblj6oWbKL3CgY1U+tOdx1T
uKKcumZ+/jVcuK8BmhJS1y8RwxlZ3X7vXr8f3+k9aG4gleyT2k73hTXyD2zDxBXW
84FEBlkH92Y2vziRLjrY4kv/ZxA6Jpig+6YmFds7ev1FdvAifFqQ1vGU0+o9q78M
cEYASlSRyPOFCxzB6WpZmxrHuDbpDoj5CSuDmBgSOEdMcv5L4jAfsJo4nusDC7VH
oMRk72Kg4xVQC8sSSJmU9A5poEiQbCwdgzRyP/zsAeT6tEv4hk+HyLNBDwu/nFga
YlO35laTAgMBAAECggEABVY+55fsQw+efbacJ3pYKbdfpKPkXxkngnzQRazSgYwS
+UrsDEOBnKpfbZ3LNy0Iy4NI826lNaN8XjZ/UOJB/Jq50S3SSMqXcNsFVeiSh3F5
5TdbmOj3GsWB8td+qzJAiXHckcdTp0tE/ruboQBd96cHKM0sVP6bZoYMZwA8c+Vf
oU4gQPolg5Kk4NaVWm/ESysYJBOV4zxKVHWxYxTpRdkM17rIuyPu5n2Q6v4/E6QU
UZlOkAJqH1f/T1BdPyZgaFdfM1Z1lEVj4+jce/Cmb2+yyQvgc6vwEt7apcs0nJsd
JfrpA3A4x1CxgAFmd8+uc72qQj3mUh8YLaOwIO78VQKBgQDPzhN93BER/Gm/ElaY
al/SRgzcIEB1mGcy72GaaOiqGhq3gIYE34oDJ/0jcSRB6pxodm3Qcc99ovpswSzn
ZQbeBY7kFJYnTo7cacJZJuN+rUGdgNZKUCOADynDz8sAPztaOwwjjyDEsySjvljM
Gta/UxzcSqj/2FppDwoW+jwvJwKBgQC7i1fa1kI8/jM7sdJEjUFG8saYXHudVff9
oNC8G3+2FST+JTWKNxfrTBWXczIsYotQSraGi73HwYQXH/Ogu8bsZu2rz4AOAAmd
f8w2cuciSNs3qCLlJbdDN5PbqQ8fcey16AekJx74++rszw9mGmVhXCiUnnddvjTr
V1oLwX8AtQKBgQCYs+eQ4klM/T474V7vC6Q0YbOLgsu7Xm3feRcxH4xxi1M8q15Q
cG/7l8Ql6jtpkNy0yuoxdaCywzPg/SdhNtUQC+eP5Szd35WNlM3zM2eTK//+nLFb
1H3x2bKoKKcVHGIiESf/bWr4AGiZRwP7oHFUEOAxZU/BChyN/TY94k6dmwKBgQCQ
JPpCfXltractE3BcNgFdCY3wXuy3sfKoIqksWypehYPoPisXb17X/6N8wxJmINuY
u8PsR4128dqXd3xmJs0ut7Gm4xY2LHs3bZlEpC3YIQ00ius/Gizv4dCn/Rldfs+D
xLHSziq1DdKzbjYUsOcI3K9oAyAVkfLUi0/vRypZHQKBgGqpxX/gVasYNH7npWLM
ig4y5hOLP0tpilnEmxN0MutZnPusIWASqb8tn3+tSX6HKfRUMxYkupnyOFKyMpkP
mT6AO3/uvz9ukPO3rlfcHTNepMQLCx9VnyRn2GRy/xArDSCnANtEHomYWEZZty8o
o0+szcdthEotYF4vS9AbrUpH
-----END PRIVATE KEY-----"""

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    if is_admin():
        return True
    
    # Relaunch the executable/script with admin privileges
    exe_path = os.path.abspath(sys.argv[0])
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, None, None, 1)
    if int(ret) > 32:
        return False  # Elevated instance launched, this one exits
    else:
        print("Error: This patch helper requires administrator privileges to modify the hosts file.")
        print("Please run it as Administrator.")
        return False

def enable_patch():
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()
            
        if "upgrade.scdn.co" in content:
            print("[Hosts] upgrade.scdn.co redirect already exists in hosts file.")
            return True
            
        with open(HOSTS_PATH, "a") as f:
            f.write(f"\n{COMMENT}\n{ENTRY}\n")
        print("[Hosts] Redirect added: upgrade.scdn.co -> 127.0.0.1")
        return True
    except Exception as e:
        print(f"[Hosts] Error modifying hosts file: {e}")
        return False

def disable_patch():
    try:
        if not os.path.exists(HOSTS_PATH):
            return
            
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            trimmed = line.strip()
            if trimmed == COMMENT or trimmed == ENTRY or "upgrade.scdn.co" in trimmed:
                continue
            new_lines.append(line)
            
        with open(HOSTS_PATH, "w") as f:
            f.writelines(new_lines)
        print("[Hosts] Redirect removed successfully.")
    except Exception as e:
        print(f"[Hosts] Error cleaning hosts file: {e}")

class SpotifyInstallerRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default request logging to avoid cluttering output
        pass

    def do_GET(self):
        print(f"[Server] Received GET request for: {self.path}")
        if "upgrade/client/" in self.path or self.path.endswith(".exe"):
            # Check for spotify_installer.exe first
            installer_path = "spotify_installer.exe"
            if not os.path.exists(installer_path):
                # Search for any non-patcher .exe file in the current directory
                exe_files = [f for f in os.listdir('.') if f.endswith('.exe') and "patch" not in f.lower() and "easyinstall" not in f.lower()]
                if exe_files:
                    installer_path = exe_files[0]
            
            if os.path.exists(installer_path):
                print(f"[Server] Serving local installer: {installer_path} ({os.path.getsize(installer_path)} bytes)")
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(os.path.getsize(installer_path)))
                self.end_headers()
                
                with open(installer_path, 'rb') as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                return
            else:
                print(f"[Server] Error: Spotify installer not found! Place a valid SpotifySetup.exe or spotify_installer.exe next to this patcher.")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Spotify installer file not found. Please place the installer next to this tool.")
                return
        
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Local Spotify CDN Mock Server is running.")

def run_server(httpd):
    try:
        httpd.serve_forever()
    except Exception as e:
        print(f"[Server] Server exception: {e}")

def main():
    if not is_admin():
        print("Requesting administrator privileges...")
        if not run_as_admin():
            time.sleep(3)
            return
        return

    # Ensure working directory is the script/exe folder
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    print("==========================================================")
    print("   Spicetify EasyInstall Legacy Patch Helper")
    print("==========================================================")
    
    # 1. Write certificate and key if they don't exist
    cert_file = "cert.pem"
    key_file = "key.pem"
    created_cert = False
    created_key = False
    
    if not os.path.exists(cert_file):
        with open(cert_file, "w") as f:
            f.write(CERT_PEM)
        created_cert = True
    if not os.path.exists(key_file):
        with open(key_file, "w") as f:
            f.write(KEY_PEM)
        created_key = True

    # 2. Modify hosts file
    if not enable_patch():
        print("Failed to edit hosts file. Exiting.")
        time.sleep(5)
        return

    # 3. Start HTTPS Server on background thread
    server_address = ('127.0.0.1', PORT)
    try:
        httpd = http.server.HTTPServer(server_address, SpotifyInstallerRequestHandler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        server_thread = threading.Thread(target=run_server, args=(httpd,), daemon=True)
        server_thread.start()
        print(f"[Server] Background HTTPS server started on port {PORT}.")
    except Exception as e:
        print(f"[Server] Failed to start HTTPS server: {e}")
        print("Please check if another application is running on port 443 (e.g. Skype, IIS, VMware).")
        disable_patch()
        time.sleep(5)
        return

    # 4. Search and launch Spicetify-Easyinstall.exe
    installer_exe = "Spicetify-Easyinstall.exe"
    launched = False
    
    # Check if Spicetify-Easyinstall.exe exists
    # Look in current folder or parent folder (if running inside a subdirectory like legacy-patch)
    target_exe = None
    if os.path.exists(installer_exe):
        target_exe = installer_exe
    elif os.path.exists(os.path.join("..", installer_exe)):
        target_exe = os.path.join("..", installer_exe)
    else:
        # Search for any .exe with easyinstall in current or parent folder
        easy_exes = [f for f in os.listdir('.') if f.endswith('.exe') and 'easyinstall' in f.lower() and f != os.path.basename(sys.argv[0])]
        if easy_exes:
            target_exe = easy_exes[0]
        else:
            parent_exes = [os.path.join("..", f) for f in os.listdir('..') if f.endswith('.exe') and 'easyinstall' in f.lower()] if os.path.exists("..") else []
            if parent_exes:
                target_exe = parent_exes[0]

    if target_exe:
        print(f"[Patcher] Found {target_exe}. Launching...")
        try:
            p = subprocess.Popen([target_exe])
            launched = True
            print(f"[Patcher] Running... Waiting for {os.path.basename(target_exe)} to exit.")
            p.wait()
            print(f"[Patcher] {os.path.basename(target_exe)} has exited.")
        except Exception as e:
            print(f"[Patcher] Error launching {target_exe}: {e}")
    else:
        print(f"\n[Patcher] ERROR: Spicetify-Easyinstall.exe not found!")
        print("Please place this patch helper in the SAME folder as Spicetify-Easyinstall.exe")
        print("and make sure your offline Spotify installer is named 'spotify_installer.exe'.\n")
        input("Press Enter to clean up and exit...")

    # 5. Clean up
    print("[Patcher] Shutting down HTTPS server...")
    try:
        httpd.shutdown()
        httpd.server_close()
    except Exception:
        pass
        
    disable_patch()
    
    # Clean up cert/key files if we generated them
    if created_cert and os.path.exists(cert_file):
        try:
            os.remove(cert_file)
        except Exception:
            pass
    if created_key and os.path.exists(key_file):
        try:
            os.remove(key_file)
        except Exception:
            pass

    print("[Patcher] Clean up finished. Exiting in 3 seconds...")
    time.sleep(3)

if __name__ == "__main__":
    main()
