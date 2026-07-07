# Based on https://gist.github.com/Willy-JL/3eaa171144b3bb0a4602c7b537f90036
import sys
import os
from contextlib import contextmanager
from modules import globals

# Backup original functionality
_stdout = sys.stdout
_stderr = sys.stderr
_stdin = sys.stdin

# Used to temporarily stop output to log file
_pause_file_output = False

def _file_write(message):
    if _pause_file_output: return
    try:
        with open(os.path.join(globals.installer_config, "log.txt"), "a", encoding="utf-8") as log:
            if message.startswith("\r") or message == "\n":
                log.write(message)
            else:
                log.write(message + "\n")
    except FileNotFoundError:
        pass

class __stdout_override:
    def write(self, message):
        if _stdout is not None:
            try:
                _stdout.write(message)
            except Exception:
                pass
        _file_write(message)

    def flush(self):
        if _stdout is not None:
            try:
                _stdout.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        if _stdout is not None:
            return getattr(_stdout, name)
        raise AttributeError(name)

class __stderr_override:
    def write(self, message):
        if _stderr is not None:
            try:
                _stderr.write(message)
            except Exception:
                pass
        _file_write(message)

    def flush(self):
        if _stderr is not None:
            try:
                _stderr.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        if _stderr is not None:
            return getattr(_stderr, name)
        raise AttributeError(name)

class __stdin_override:
    def readline(self):
        if _stdin is not None:
            try:
                message = _stdin.readline()
                _file_write(message)
                return message
            except Exception:
                pass
        return ""

    def __getattr__(self, name):
        if name == "fileno":
            raise AttributeError
        if _stdin is not None:
            return getattr(_stdin, name)
        raise AttributeError(name)

@contextmanager
def pause_file_output():
    global _pause_file_output
    _pause_file_output = True
    yield
    _pause_file_output = False

pause = pause_file_output

# Create / clear log file
if not os.path.exists(globals.installer_config):
    os.makedirs(globals.installer_config)
open(os.path.join(globals.installer_config, "log.txt"), "w").close()

# Apply overrides
sys.stdout = __stdout_override()
sys.stderr = __stderr_override()
sys.stdin = __stdin_override()
