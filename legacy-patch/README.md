# Guide: Running Legacy Spicetify-Easyinstall Releases

Older compiled releases of `Spicetify-Easyinstall.exe` are hardcoded to download the Spotify installer from Spotify's CDN (`https://upgrade.scdn.co/upgrade/client/win32-x86_64/spotify_installer-<version>.exe`). Because these links now return a **403 Forbidden** error, the installer fails.

However, since `Spicetify-Easyinstall` was compiled using Python's `aiohttp` with `verify_ssl=False`, it is possible to intercept the download requests using a local HTTPS mock server and a Windows hosts patch.

---

## Prerequisites

1. **Python 3.x** must be installed on your system.
2. **Git** (or OpenSSL) must be installed so the server can automatically generate a self-signed certificate.

---

## Step-by-Step Instructions

### Step 1: Place the Spotify Installer
1. Download a compatible offline Spotify installer (e.g., `SpotifyFullSetup.exe` or the specific version `spotify_installer-1.2.51.345.gcc39d911-63.exe`).
2. Rename the installer to **`spotify_installer.exe`**.
3. Place this file in the same folder as the patch scripts (`legacy-patch/`).

### Step 2: Apply the Hosts Patch
To redirect requests for `upgrade.scdn.co` to your local machine, you must patch the Windows `hosts` file.

You can use either the Python script or the PowerShell script provided:

#### Option A: Using Python (Recommended)
1. Open an Administrator command prompt or terminal.
2. Run:
   ```cmd
   python patch_hosts.py
   ```
3. Type **`1`** and press **Enter** to enable the patch.

#### Option B: Using PowerShell
1. Open an elevated PowerShell session (Run as Administrator).
2. Run:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\patch_hosts.ps1
   ```
3. Choose **`1`** to enable the patch.

---

## Step 3: Run the Mock HTTPS Server
The mock server must listen on port **443** (the standard HTTPS port) to handle the secure download request.

1. Open a command prompt or PowerShell window **as Administrator** (required to bind to port 443).
2. Run:
   ```cmd
   python server.py
   ```
3. On first startup, the script will locate `openssl.exe` (via PATH or Git) and automatically generate `cert.pem` and `key.pem`.
4. You will see:
   ```text
   Server running at https://localhost:443
   Mocking upgrade.scdn.co. Press Ctrl+C to stop.
   ```

---

## Step 4: Run your Legacy executable
1. With the mock server running, launch your legacy **`Spicetify-Easyinstall.exe`** file.
2. The executable will attempt to connect to `upgrade.scdn.co` on port 443.
3. The host redirect will send it to `127.0.0.1` (your mock server).
4. The server will intercept the request and output:
   ```text
   Received GET request for: /upgrade/client/win32-x86_64/spotify_installer-<version>.exe
   Serving local installer: spotify_installer.exe
   ```
5. `Spicetify-Easyinstall` will accept the self-signed certificate, download the file successfully, and continue the installation process.

---

## Step 5: Clean Up (Restore Hosts File)
Once installation is complete, it is highly recommended to restore your hosts file to avoid issues with standard Spotify updates.

1. Run the hosts patcher script again.
2. Select **`2`** (Disable Patch).
3. The redirection for `upgrade.scdn.co` will be removed.
4. You can stop the mock server by pressing **`Ctrl+C`** in its terminal window.
