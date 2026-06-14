# main.py - Scryptian Core
# Skill scanner | Hotkey | Editor UI

import os
import sys
import re
import signal
import importlib.util
import tkinter as tk
import keyboard
import telemetry
import tray
import autostart
from config import HOTKEY, BASE_DIR, MODEL_PATH, MODEL_FILE
import bootstrap

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes


# -- DPI (crisp rendering on Windows) --
if IS_WINDOWS:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

SKILLS_DIR = os.path.join(BASE_DIR, "skills")


# ── Skill scanner ──
def scan_skills():
    """
    Scans the skills/ folder, reads metadata (@title, @description)
    and loads modules. Returns a list of dicts.
    """
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills

    for filename in sorted(os.listdir(SKILLS_DIR)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        filepath = os.path.join(SKILLS_DIR, filename)
        meta = _parse_metadata(filepath)
        module = _load_module(filename, filepath)

        if module and hasattr(module, "run"):
            skills.append(
                {
                    "title": meta.get("title", filename.replace(".py", "")),
                    "description": meta.get("description", ""),
                    "author": meta.get("author", ""),
                    "module": module,
                    "filename": filename,
                }
            )
    return skills


def _parse_metadata(filepath):
    """Reads @title, @description, @author from file header comments."""
    meta = {}
    pattern = re.compile(r"^#\s*@(\w+):\s*(.+)$")
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("#"):
                break
            match = pattern.match(line)
            if match:
                meta[match.group(1).lower()] = match.group(2).strip()
    return meta


def _load_module(name, filepath):
    """Dynamically loads a .py file as a module."""
    try:
        spec = importlib.util.spec_from_file_location(name.replace(".py", ""), filepath)
        module = importlib.util.module_from_spec(spec)

        parent_dir = os.path.dirname(os.path.abspath(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"[Scryptian] Failed to load {name}: {e}")
        return None


class ScryptianBar:
    """Wrapper that delegates to ScryptianEditor."""

    def __init__(self, root, skills):
        from editor import ScryptianEditor

        self.root = root
        self.skills = skills
        self.editor = ScryptianEditor(root, skills)

    def toggle(self):
        self.editor.toggle()


def _kill_other_instances():
    """Kill other Scryptian.exe processes, keeping only current instance."""
    import ctypes
    import ctypes.wintypes

    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_TERMINATE = 0x0001

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    my_pid = os.getpid()
    my_ppid = None

    # Find my parent PID
    snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

    keep_pids = {my_pid}

    if ctypes.windll.kernel32.Process32First(snap, ctypes.byref(pe)):
        while True:
            if pe.th32ProcessID == my_pid:
                my_ppid = pe.th32ParentProcessID
                keep_pids.add(my_ppid)
                break
            if not ctypes.windll.kernel32.Process32Next(snap, ctypes.byref(pe)):
                break

    # Kill all other Scryptian.exe
    pe2 = PROCESSENTRY32()
    pe2.dwSize = ctypes.sizeof(PROCESSENTRY32)
    snap2 = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if ctypes.windll.kernel32.Process32First(snap2, ctypes.byref(pe2)):
        while True:
            name = pe2.szExeFile.decode("utf-8", errors="ignore").lower()
            if "scryptian" in name and pe2.th32ProcessID not in keep_pids:
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_TERMINATE, False, pe2.th32ProcessID
                )
                if handle:
                    ctypes.windll.kernel32.TerminateProcess(handle, 0)
                    ctypes.windll.kernel32.CloseHandle(handle)
            if not ctypes.windll.kernel32.Process32Next(snap2, ctypes.byref(pe2)):
                break

    ctypes.windll.kernel32.CloseHandle(snap)
    ctypes.windll.kernel32.CloseHandle(snap2)


def _ensure_installed():
    """Kill duplicate instances. Installer handles placement."""
    _kill_other_instances()
    return True


# ── Entry point ──
def main():
    if not _ensure_installed():
        return
    bootstrap.setup()

    print("[Scryptian] Scanning skills...")
    skills = scan_skills()

    if not skills:
        print("[Scryptian] No skills found in skills/ folder")
        return

    for s in skills:
        print(f"  → {s['title']}: {s['description']}")

    print(f"\n[Scryptian] Skills loaded: {len(skills)}")

    # Check model file
    if os.path.exists(MODEL_PATH):
        print(f"[Scryptian] Model: {MODEL_FILE}")
    else:
        print(
            "[Scryptian] WARNING: Model not found. It will download on first skill use."
        )

    print(f"[Scryptian] Hotkey: {HOTKEY}")
    print("[Scryptian] Waiting...")

    telemetry.send("app_started", {"skills": len(skills)})

    # Hidden root tkinter window — keeps mainloop on the main thread
    root = tk.Tk()
    root.withdraw()

    bar = ScryptianBar(root, skills)

    keyboard.add_hotkey(HOTKEY, bar.toggle)

    def _rehook():
        """Re-register hotkey periodically to survive sleep/hibernate."""
        try:
            keyboard.remove_hotkey(HOTKEY)
        except Exception:
            pass
        keyboard.add_hotkey(HOTKEY, bar.toggle)
        root.after(300000, _rehook)  # every 5 minutes

    root.after(300000, _rehook)

    autostart.enable()
    print("[Scryptian] Autostart updated.")

    tray.start(on_quit=root.quit, on_open=bar.toggle)

    # Show editor on first launch so user knows it's working
    root.after(500, bar.toggle)

    def _sigint_handler(_sig, _frame):
        root.after(0, root.quit)

    signal.signal(signal.SIGINT, _sigint_handler)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[Scryptian] Stopped.")


if __name__ == "__main__":
    main()
