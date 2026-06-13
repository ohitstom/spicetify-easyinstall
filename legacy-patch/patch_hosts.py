import sys
import os
import ctypes

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
ENTRY = "127.0.0.1 upgrade.scdn.co"
COMMENT = "# Spicetify-Easyinstall Legacy Fix"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    if is_admin():
        return True
    
    # Relaunch the script with admin privileges
    script_path = os.path.abspath(sys.argv[0])
    params = f'"{script_path}"'
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    if int(ret) > 32:
        return False  # Main process exits, elevated one starts
    else:
        print("Failed to elevate privileges. Please run as Administrator manually.")
        return False

def enable_patch():
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()
            
        if "upgrade.scdn.co" in content:
            print("Patch is already applied or upgrade.scdn.co exists in the hosts file.")
            return
            
        # Append the redirect
        with open(HOSTS_PATH, "a") as f:
            f.write(f"\n{COMMENT}\n{ENTRY}\n")
        print("Patch successfully applied! upgrade.scdn.co now points to 127.0.0.1.")
    except Exception as e:
        print(f"Error applying patch: {e}")

def disable_patch():
    try:
        if not os.path.exists(HOSTS_PATH):
            print("Hosts file not found!")
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
            
        print("Patch successfully removed! upgrade.scdn.co restored to default.")
    except Exception as e:
        print(f"Error removing patch: {e}")

def main():
    if not is_admin():
        print("Requesting administrator privileges...")
        if not run_as_admin():
            input("Press Enter to exit...")
            return
        return

    print("=============================================")
    print("   Spicetify Legacy Hosts Patcher (Python)")
    print("=============================================")
    print("1) Enable Patch (Redirect upgrade.scdn.co to localhost)")
    print("2) Disable Patch (Restore default behavior)")
    print("3) Exit")
    print("=============================================")
    
    choice = input("Select an option [1-3]: ").strip()
    if choice == "1":
        enable_patch()
    elif choice == "2":
        disable_patch()
    else:
        print("Exiting.")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
