from clint.textui import progress
import subprocess
import requests
import psutil
import os

from modules import globals


def requests_progress(url, path):
    if os.path.isdir(path) == True:
        os.mkdir(path)
    warnings.filterwarnings('ignore', message='Unverified HTTPS request') #Extremely janky way to bypass shitty pyinstaller sslerrors that i just cant seem to fix for the moment.
    r = requests.get(url, stream=True, verify=False)
    with open(path, 'wb') as f:
        total_length = int((r.headers.get('content-length')))
        for chunk in progress.bar(r.iter_content(chunk_size=1024000), expected_size=round(total_length/1024000)):
            if chunk:
                f.write(chunk)
                f.flush()
            except:
                    print("ERROR Loading ProgressBar.")
        print ("\033[A                                                     \033[A")
        
        #Reminder - Add except loop when headers cant be found [division error (0)]


def start_process(path):
    SW_HIDE = 0
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_HIDE
    return subprocess.Popen(path, startupinfo=info)


def kill_processes(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                proc.kill()
        except Exception:
            pass


def process_running(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                return True
        except Exception:
            pass
    return False


def process_pid_running(pid):
    for proc in psutil.process_iter():
        try:
            if proc.pid == pid:
                return True
        except Exception:
            pass
    return False
