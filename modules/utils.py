import os
import stat
import subprocess
import time
import warnings

import psutil
import requests, requests.exceptions
from clint.textui import progress

from modules import globals

def requests_progress(url, path):
    if os.path.isdir(path) == True:
        os.mkdir(path)
    
    r = requests.get(url, headers={'User-Agent': 'Developer'}, stream=True)
    try:
        with open(path, 'wb') as f:
            total_length = int((r.headers.get('content-length')))
            for chunk in progress.bar(r.iter_content(chunk_size=1024000), expected_size=round(total_length/1024000)):
                if chunk:
                    f.write(chunk)
                    f.flush()
    
    except (TypeError, #Fill in for proper error checking, simply checks if int((r.headers.get('content-length'))) isnt nonetype, or doesnt throw any errors.
            ZeroDivisionError, AttributeError) as e:
        print("[!]ERROR Loading ProgressBar. Attempting To Downloading Without It.[!]")
        r = requests.get(url, stream=True)
        with open(path, 'wb') as f:
            f.write(r.content)
    
    except Exception as e:
        raise TypeError(e)

    print("\033[A                                                     \033[A")


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
            time.sleep(0.25)


def process_running(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                return True
        except Exception:
            time.sleep(0.25)
    return False


def process_pid_running(pid):
    for proc in psutil.process_iter():
        try:
            if proc.pid == pid:
                return True
        except Exception:
            time.sleep(0.25)
    return False
