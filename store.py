# store.py — Online skill store: fetches registry.json from GitHub and installs skills locally.

import os
import json
import ssl
import threading
import tkinter as tk
from urllib import request

REGISTRY_URL = "https://raw.githubusercontent.com/newJenius/Scryptian/main/store/registry.json"
SKILL_BASE_URL = "https://raw.githubusercontent.com/newJenius/Scryptian/main/store/skills/"


def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch_registry(timeout=10):
    """Fetch registry.json from GitHub. Returns list of skill dicts."""
    resp = request.urlopen(REGISTRY_URL, timeout=timeout, context=_ssl_ctx())
    data = json.loads(resp.read())
    return data.get("skills", [])


def is_installed(filename, skills_dir):
    return os.path.exists(os.path.join(skills_dir, filename))


def install_skill(filename, skills_dir):
    url = SKILL_BASE_URL + filename
    resp = request.urlopen(url, timeout=15, context=_ssl_ctx())
    content = resp.read()
    os.makedirs(skills_dir, exist_ok=True)
    path = os.path.join(skills_dir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


class StoreWindow:
    """Simple store browser window listing skills from the online registry."""

    def __init__(self, parent, skills_dir, on_installed=None):
        self.parent = parent
        self.skills_dir = skills_dir
        self.on_installed = on_installed
        self.window = None

    def open(self):
        if self.window:
            try:
                self.window.lift()
                self.window.focus_force()
                return
            except Exception:
                self.window = None

        win = tk.Toplevel(self.parent)
        win.title("Scryptian — Skill Store")
        win.configure(bg="#1e1e2e")
        win.geometry("480x440")
        win.attributes("-topmost", True)
        win.after(300, lambda: win.attributes("-topmost", False))
        self.window = win

        tk.Label(
            win, text="Skill Store", font=("Segoe UI", 14, "bold"),
            bg="#1e1e2e", fg="#cdd6f4",
        ).pack(pady=(14, 4))

        self.status_lbl = tk.Label(
            win, text="Loading...", font=("Segoe UI", 10),
            bg="#1e1e2e", fg="#a6adc8",
        )
        self.status_lbl.pack(pady=(0, 8))

        canvas = tk.Canvas(win, bg="#1e1e2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg="#1e1e2e")

        self.list_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw", width=440)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        scrollbar.pack(side="right", fill="y", pady=(0, 12), padx=(0, 12))

        win.protocol("WM_DELETE_WINDOW", self._close)

        threading.Thread(target=self._load, daemon=True).start()

    def _close(self):
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None

    def _load(self):
        try:
            skills = fetch_registry()
            self.parent.after(0, lambda: self._render(skills))
        except Exception as e:
            err = str(e)
            self.parent.after(0, lambda: self._show_error(err))

    def _show_error(self, err):
        if not self.window:
            return
        self.status_lbl.config(text=f"Failed to load store: {err}")

    def _render(self, skills):
        if not self.window:
            return
        self.status_lbl.config(text=f"{len(skills)} skill(s) available")
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not skills:
            tk.Label(
                self.list_frame, text="No skills available right now.",
                font=("Segoe UI", 10), bg="#1e1e2e", fg="#585b70",
            ).pack(pady=20)
            return

        for skill in skills:
            self._make_row(skill)

    def _make_row(self, skill):
        row = tk.Frame(self.list_frame, bg="#1e1e2e")
        row.pack(fill="x", pady=4)

        text_frame = tk.Frame(row, bg="#1e1e2e")
        text_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            text_frame, text=skill.get("title", ""), font=("Segoe UI", 11, "bold"),
            bg="#1e1e2e", fg="#cdd6f4", anchor="w",
        ).pack(fill="x")
        tk.Label(
            text_frame, text=skill.get("description", ""), font=("Segoe UI", 9),
            bg="#1e1e2e", fg="#a6adc8", anchor="w", wraplength=300, justify="left",
        ).pack(fill="x")

        filename = skill.get("filename", "")
        installed = is_installed(filename, self.skills_dir)

        btn = tk.Label(
            row,
            text="Installed" if installed else "Install",
            font=("Segoe UI", 9, "bold"),
            bg="#45475a" if installed else "#89b4fa",
            fg="#a6adc8" if installed else "#1e1e2e",
            padx=10, pady=4,
            cursor="arrow" if installed else "hand2",
        )
        btn.pack(side="right", padx=(8, 0))

        if not installed:
            btn.bind("<Button-1>", lambda e, s=skill, b=btn: self._install(s, b))

    def _install(self, skill, btn):
        btn.config(text="Installing...", bg="#f9e2af", cursor="arrow")
        filename = skill.get("filename", "")

        def do_install():
            try:
                install_skill(filename, self.skills_dir)
                self.parent.after(0, lambda: self._on_install_done(btn, True))
            except Exception as e:
                err = str(e)
                self.parent.after(0, lambda: self._on_install_done(btn, False, err))

        threading.Thread(target=do_install, daemon=True).start()

    def _on_install_done(self, btn, success, error=None):
        try:
            if success:
                btn.config(text="Installed", bg="#45475a", fg="#a6adc8", cursor="arrow")
                btn.unbind("<Button-1>")
                if self.on_installed:
                    self.on_installed()
            else:
                btn.config(text="Failed", bg="#f38ba8", fg="#1e1e2e")
        except Exception:
            pass
