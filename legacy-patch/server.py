import os
import sys
import ssl
import http.server
import subprocess

PORT = 443
CERT_FILE = "cert.pem"
KEY_FILE = "key.pem"
INSTALLER_FILENAME = "spotify_installer.exe"

def generate_cert():
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        print("SSL certificate and key already exist.")
        return

    print("Generating self-signed certificate...")
    openssl_path = None
    # 1. Check if openssl is in PATH
    try:
        subprocess.run(["openssl", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        openssl_path = "openssl"
    except Exception:
        # 2. Check Git common paths
        paths = [
            r"C:\Program Files\Git\usr\bin\openssl.exe",
            r"C:\Program Files (x86)\Git\usr\bin\openssl.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                openssl_path = p
                break
    
    if not openssl_path:
        print("Error: openssl.exe not found in PATH or Git directories.")
        print("Please install Git or OpenSSL, or generate cert.pem and key.pem manually.")
        sys.exit(1)
        
    cmd = [
        openssl_path, "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", KEY_FILE, "-out", CERT_FILE,
        "-sha256", "-days", "3650", "-nodes",
        "-subj", "/CN=upgrade.scdn.co"
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Self-signed certificate generated successfully.")
    except Exception as e:
        print(f"Failed to generate certificate: {e}")
        sys.exit(1)

class SpotifyInstallerRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received GET request for: {self.path}")
        
        # Check if request is for the spotify installer upgrade/client/win32-x86_64/...
        if "upgrade/client/" in self.path or self.path.endswith(".exe"):
            # Search for the installer file
            installer_path = None
            
            # Check for spotify_installer.exe first
            if os.path.exists(INSTALLER_FILENAME):
                installer_path = INSTALLER_FILENAME
            else:
                # Find any .exe file in the current directory
                exe_files = [f for f in os.listdir('.') if f.endswith('.exe') and f != "Spicetify-Easyinstall.exe"]
                if exe_files:
                    installer_path = exe_files[0]
            
            if installer_path and os.path.exists(installer_path):
                print(f"Serving local installer: {installer_path}")
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(os.path.getsize(installer_path)))
                self.end_headers()
                
                with open(installer_path, 'rb') as f:
                    # Serve file in chunks
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                return
            else:
                print(f"Error: Spotify installer not found! Place '{INSTALLER_FILENAME}' in this directory.")
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Spotify installer file not found on server. Please place spotify_installer.exe in the server directory.")
                return
        
        # Default response for other paths
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Local Spotify CDN Mock Server is running.")

def run_server():
    generate_cert()
    
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.HTTPServer(server_address, SpotifyInstallerRequestHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"\nServer running at https://localhost:{PORT}")
    print(f"Mocking upgrade.scdn.co. Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    # Ensure working directory is the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_server()
