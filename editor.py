# editor.py - Scryptian Editor
# Full-featured code editor with AI skills integration

import tkinter as tk
from tkinter import filedialog, font
import os
import sys
import json
import threading
import bridge

# -- Catppuccin Mocha Color Palette --
C = {
    "crust": "#11111b",
    "mantle": "#181825",
    "base": "#1e1e2e",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "overlay1": "#7f849c",
    "overlay2": "#9399b2",
    "subtext0": "#a6adc8",
    "subtext1": "#bac2de",
    "text": "#cdd6f4",
    "lavender": "#b4befe",
    "blue": "#89b4fa",
    "sapphire": "#74c7ec",
    "sky": "#89dceb",
    "teal": "#94e2d5",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "maroon": "#eba0ac",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
    "pink": "#f5c2e7",
    "flamingo": "#f2cdcd",
    "rosewater": "#f5e0dc",
}

# -- Syntax highlighting colors --
SYNTAX_COLORS = {
    "Keyword": C["mauve"],
    "Keyword.Namespace": C["mauve"],
    "Keyword.Type": C["yellow"],
    "Keyword.Constant": C["peach"],
    "Name.Function": C["blue"],
    "Name.Class": C["yellow"],
    "Name.Decorator": C["pink"],
    "Name.Builtin": C["red"],
    "Name.Builtin.Pseudo": C["red"],
    "String": C["green"],
    "String.Affix": C["green"],
    "String.Escape": C["peach"],
    "Number": C["peach"],
    "Number.Float": C["peach"],
    "Comment": C["overlay0"],
    "Comment.Multiline": C["overlay0"],
    "Comment.Single": C["overlay0"],
    "Operator": C["sky"],
    "Operator.Word": C["mauve"],
    "Punctuation": C["subtext1"],
    "Name.Variable": C["text"],
    "Name.Tag": C["red"],
    "Name.Attribute": C["yellow"],
    "Literal": C["teal"],
    "Literal.Date": C["teal"],
    "Generic.Heading": C["blue"],
    "Generic.Subheading": C["blue"],
    "Generic.Deleted": C["red"],
    "Generic.Inserted": C["green"],
    "Generic.Error": C["red"],
}

# -- File extension to language mapping --
EXTENSION_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JSX",
    ".ts": "TypeScript",
    ".tsx": "TSX",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".md": "Markdown",
    ".txt": "Text",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".sql": "SQL",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".r": "R",
    ".lua": "Lua",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".env": "Environment",
    ".gitignore": "Git Ignore",
    ".dockerfile": "Dockerfile",
}

MAX_HIGHLIGHT_SIZE = 500 * 1024


class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(
            parent, bg=C["mantle"], highlightthickness=0, width=50, **kwargs
        )
        self.text_widget = text_widget
        self._font = font.Font(family="Consolas", size=12)
        self._line_height = self._font.metrics("linespace")
        self._current_line = 1

    def refresh(self, _event=None):
        self.delete("all")
        if not self.text_widget:
            return
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            line_num = str(i).split(".", maxsplit=1)[0]
            y = dline[1]
            is_current = line_num == str(self._current_line)
            fill = C["text"] if is_current else C["overlay0"]
            self.create_text(
                45, y, anchor="ne", text=line_num, font=self._font, fill=fill
            )
            i = self.text_widget.index(f"{i}+1line")
            if str(self.text_widget.index(i)) == str(self.text_widget.index("end")):
                break
        self._update_width()

    def update_current_line(self, _event=None):
        if not self.text_widget:
            return
        pos = self.text_widget.index("insert")
        line = pos.split(".")[0]
        if line != str(self._current_line):
            self._current_line = line
            self.refresh()

    def _update_width(self):
        if not self.text_widget:
            return
        line_count = int(self.text_widget.index("end-1c").split(".")[0])
        digits = max(3, len(str(line_count)))
        new_width = self._font.measure("9" * digits) + 20
        self.config(width=new_width)

    def sync_scroll(self, *_args):
        if self.text_widget:
            self.yview_moveto(self.text_widget.yview()[0])


class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self._lexer = None
        self._lang = None
        self._job = None
        self._setup_tags()

    def _setup_tags(self):
        for token_name, color in SYNTAX_COLORS.items():
            tag = f"syn_{token_name}"
            self.text_widget.tag_configure(tag, foreground=color)

    def set_language(self, lang):
        if lang == self._lang:
            return
        self._lang = lang
        self._lexer = self._get_lexer(lang)
        self.highlight_all()

    def _get_lexer(self, lang):
        try:
            from pygments.lexers import get_lexer_by_name, ClassNotFound

            try:
                return get_lexer_by_name(
                    lang.lower().replace(" ", "").replace("#", "sharp")
                )
            except ClassNotFound:
                return None
        except ImportError:
            return None

    def highlight_all(self):
        if self._job:
            self.text_widget.after_cancel(self._job)
        self._job = self.text_widget.after(100, self._do_highlight)

    def _do_highlight(self):
        if not self._lexer:
            return
        content = self.text_widget.get("1.0", "end-1c")
        if len(content) > MAX_HIGHLIGHT_SIZE:
            return
        try:
            from pygments import lex

            for tag in self.text_widget.tag_names():
                if tag.startswith("syn_"):
                    self.text_widget.tag_remove(tag, "1.0", "end")
            offset = 0
            for token, value in lex(content, self._lexer):
                token_name = str(token).rsplit(".", maxsplit=1)[-1]
                tag = f"syn_{token_name}"
                if tag in self.text_widget.tag_names():
                    start_idx = f"1.0 + {offset} chars"
                    end_idx = f"1.0 + {offset + len(value)} chars"
                    self.text_widget.tag_add(tag, start_idx, end_idx)
                offset += len(value)
        except Exception:
            pass


class EditorTab:
    def __init__(self, parent, filename=None, content=""):
        self.filename = filename
        self.modified = False
        self.language = "Text"

        self.frame = tk.Frame(parent, bg=C["base"])

        if filename:
            ext = os.path.splitext(filename)[1].lower()
            self.language = EXTENSION_MAP.get(ext, "Text")

        self._build_ui(content)

    def _build_ui(self, content):
        container = tk.Frame(self.frame, bg=C["base"])
        container.pack(fill="both", expand=True)

        self.line_numbers = LineNumbers(container, None)
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(
            container,
            font=("Consolas", 12),
            bg=C["base"],
            fg=C["text"],
            insertbackground=C["rosewater"],
            selectbackground=C["surface1"],
            selectforeground=C["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            wrap="none",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            tabs=("4c",),
        )
        self.text.pack(side="left", fill="both", expand=True)

        self.line_numbers.text_widget = self.text

        h_scroll = tk.Scrollbar(
            self.frame, orient="horizontal", command=self.text.xview
        )
        h_scroll.pack(side="bottom", fill="x")
        self.text.config(xscrollcommand=h_scroll.set)

        self._v_scroll = tk.Scrollbar(
            self.frame, orient="vertical", command=self._on_scroll_y
        )
        self._v_scroll.pack(side="right", fill="y")
        self.text.config(yscrollcommand=self._on_scroll_y_setup)

        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self.line_numbers.update_current_line)
        self.text.bind("<ButtonRelease-1>", self.line_numbers.update_current_line)
        self.text.bind("<KeyRelease>", self._on_key, add="+")

        self.highlighter = SyntaxHighlighter(self.text)
        if self.language != "Text":
            self.highlighter.set_language(self.language)

    def _on_scroll_y_setup(self, *args):
        self._v_scroll.set(*args)
        self.line_numbers.sync_scroll()

    def _on_scroll_y(self, *args):
        self.text.yview(*args)
        self.line_numbers.sync_scroll()

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.modified = True

    def _on_key(self, _event=None):
        self.highlighter.highlight_all()

    def get_content(self):
        return self.text.get("1.0", "end-1c")

    def set_content(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.modified = False

    def get_selection(self):
        try:
            return self.text.get("sel.first", "sel.last")
        except tk.TclError:
            return ""

    def replace_selection(self, text):
        try:
            self.text.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        self.text.insert("insert", text)

    def insert_text(self, text):
        self.text.insert("insert", text)

    def undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def show(self):
        self.frame.pack(fill="both", expand=True)
        self.line_numbers.refresh()
        self.text.focus_set()

    def hide(self):
        self.frame.pack_forget()

    def mark_saved(self):
        self.modified = False
        self.text.edit_modified(False)

    def update_line_numbers(self, _event=None):
        self.line_numbers.refresh()


class FindReplaceDialog:
    def __init__(self, parent, editor_tab_getter):
        self.parent = parent
        self.get_tab = editor_tab_getter
        self.window = None
        self.matches = []
        self.current_match = 0

    def open_find(self):
        self._open(replace=False)

    def open_replace(self):
        self._open(replace=True)

    def _open(self, replace=False):
        if self.window:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Find" if not replace else "Find and Replace")
        self.window.configure(bg=C["surface0"])
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)

        frame = tk.Frame(self.window, bg=C["surface0"], padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame, text="Find:", bg=C["surface0"], fg=C["text"], font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="w", pady=2)
        self.find_entry = tk.Entry(
            frame,
            font=("Consolas", 11),
            bg=C["base"],
            fg=C["text"],
            insertbackground=C["text"],
            relief="flat",
            width=40,
        )
        self.find_entry.grid(row=0, column=1, columnspan=2, padx=(5, 0), pady=2)
        self.find_entry.bind("<KeyRelease>", self._on_search_change)
        self.find_entry.focus_set()

        self.match_label = tk.Label(
            frame,
            text="0 matches",
            bg=C["surface0"],
            fg=C["subtext0"],
            font=("Segoe UI", 9),
        )
        self.match_label.grid(row=0, column=3, padx=(10, 0))

        self.replace_entry = None
        if replace:
            tk.Label(
                frame,
                text="Replace:",
                bg=C["surface0"],
                fg=C["text"],
                font=("Segoe UI", 10),
            ).grid(row=1, column=0, sticky="w", pady=2)
            self.replace_entry = tk.Entry(
                frame,
                font=("Consolas", 11),
                bg=C["base"],
                fg=C["text"],
                insertbackground=C["text"],
                relief="flat",
                width=40,
            )
            self.replace_entry.grid(row=1, column=1, columnspan=2, padx=(5, 0), pady=2)

        btn_frame = tk.Frame(frame, bg=C["surface0"])
        btn_frame.grid(
            row=2 if replace else 1, column=0, columnspan=4, pady=(10, 0), sticky="e"
        )

        tk.Button(
            btn_frame,
            text="< Prev",
            command=self._prev_match,
            bg=C["surface1"],
            fg=C["text"],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
        ).pack(side="left", padx=2)
        tk.Button(
            btn_frame,
            text="Next >",
            command=self._next_match,
            bg=C["surface1"],
            fg=C["text"],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
        ).pack(side="left", padx=2)

        if replace:
            tk.Button(
                btn_frame,
                text="Replace",
                command=self._replace_current,
                bg=C["surface1"],
                fg=C["text"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
            ).pack(side="left", padx=2)
            tk.Button(
                btn_frame,
                text="Replace All",
                command=self._replace_all,
                bg=C["surface1"],
                fg=C["text"],
                font=("Segoe UI", 9),
                relief="flat",
                padx=10,
            ).pack(side="left", padx=2)

        tk.Button(
            btn_frame,
            text="Close",
            command=self.close,
            bg=C["surface1"],
            fg=C["text"],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
        ).pack(side="left", padx=2)

        self.window.bind("<Escape>", lambda e: self.close())

    def _on_search_change(self, _event=None):
        query = self.find_entry.get()
        tab = self.get_tab()
        if not tab or not query:
            self.matches = []
            self.current_match = 0
            self.match_label.config(text="0 matches")
            return

        content = tab.get_content()
        self.matches = []
        start = 0
        query_lower = query.lower()
        while True:
            idx = content.lower().find(query_lower, start)
            if idx == -1:
                break
            self.matches.append(idx)
            start = idx + 1

        self.current_match = 0
        self.match_label.config(text=f"{len(self.matches)} matches")
        if self.matches:
            self._highlight_match(tab)

    def _highlight_match(self, tab):
        if not self.matches or not tab:
            return
        pos = self.matches[self.current_match]
        end = pos + len(self.find_entry.get())
        tab.text.tag_remove("find_highlight", "1.0", "end")
        start_idx = f"1.0 + {pos} chars"
        end_idx = f"1.0 + {end} chars"
        tab.text.tag_add("sel", start_idx, end_idx)
        tab.text.see(start_idx)
        tab.text.tag_configure(
            "find_highlight", background=C["yellow"], foreground=C["base"]
        )
        tab.text.tag_add("find_highlight", start_idx, end_idx)
        self.match_label.config(text=f"{self.current_match + 1} of {len(self.matches)}")

    def _next_match(self):
        if not self.matches:
            return
        self.current_match = (self.current_match + 1) % len(self.matches)
        self._highlight_match(self.get_tab())

    def _prev_match(self):
        if not self.matches:
            return
        self.current_match = (self.current_match - 1) % len(self.matches)
        self._highlight_match(self.get_tab())

    def _replace_current(self):
        tab = self.get_tab()
        if not tab or not self.matches:
            return
        pos = self.matches[self.current_match]
        end = pos + len(self.find_entry.get())
        tab.text.delete(f"1.0 + {pos} chars", f"1.0 + {end} chars")
        tab.text.insert(f"1.0 + {pos} chars", self.replace_entry.get())
        self._on_search_change()

    def _replace_all(self):
        tab = self.get_tab()
        if not tab:
            return
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return
        content = tab.get_content()
        new_content = content.replace(query, replacement)
        tab.set_content(new_content)
        count = content.count(query)
        self.match_label.config(text=f"Replaced {count} occurrences")
        self.matches = []
        self.current_match = 0

    def close(self):
        if self.window:
            tab = self.get_tab()
            if tab:
                tab.text.tag_remove("find_highlight", "1.0", "end")
            self.window.destroy()
            self.window = None


class SkillPalette:
    def __init__(self, parent, skills, apply_callback):
        self.parent = parent
        self.skills = skills
        self.apply_callback = apply_callback
        self.window = None
        self.filtered = list(skills)
        self.selected_index = 0
        self.skill_buttons = []

    def show(self):
        if self.window:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Run Skill")
        self.window.configure(bg=C["surface0"])
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)

        sw = self.parent.winfo_screenwidth()
        pw = 500
        px = (sw - pw) // 2
        py = int(self.parent.winfo_screenheight() * 0.3)
        self.window.geometry(f"{pw}x400+{px}+{py}")

        container = tk.Frame(self.window, bg=C["surface0"], padx=12, pady=12)
        container.pack(fill="both", expand=True)

        self.search = tk.Entry(
            container,
            font=("Segoe UI", 14),
            bg=C["base"],
            fg=C["text"],
            insertbackground=C["text"],
            relief="flat",
            borderwidth=0,
        )
        self.search.pack(fill="x", pady=(0, 8))
        self.search.focus_set()
        self.search.bind("<KeyRelease>", self._on_search)
        self.search.bind("<Down>", self._select_next)
        self.search.bind("<Up>", self._select_prev)
        self.search.bind("<Return>", self._on_enter)
        self.search.bind("<Escape>", lambda e: self.close())

        self.list_frame = tk.Frame(container, bg=C["surface0"])
        self.list_frame.pack(fill="both", expand=True)

        self._render_list()

    def _on_search(self, _event=None):
        query = self.search.get().lower().strip()
        if query:
            self.filtered = [
                s
                for s in self.skills
                if query in s["title"].lower()
                or query in s.get("description", "").lower()
            ]
        else:
            self.filtered = list(self.skills)
        self.selected_index = 0
        self._render_list()

    def _render_list(self):
        for btn in self.skill_buttons:
            btn.destroy()
        self.skill_buttons = []

        for i, skill in enumerate(self.filtered):
            btn = tk.Button(
                self.list_frame,
                text=f"  {skill['title']}",
                anchor="w",
                font=("Segoe UI", 12),
                bg=C["surface1"] if i == self.selected_index else C["surface0"],
                fg=C["text"],
                activebackground=C["surface1"],
                activeforeground=C["text"],
                relief="flat",
                borderwidth=0,
                padx=8,
                pady=6,
                command=lambda idx=i: self._click(idx),
            )
            btn.pack(fill="x", pady=1)

            if skill.get("description"):
                desc = tk.Label(
                    self.list_frame,
                    text=f"    {skill['description'][:60]}",
                    anchor="w",
                    font=("Segoe UI", 9),
                    bg=C["surface0"],
                    fg=C["subtext0"],
                )
                desc.pack(fill="x", padx=8)
                self.skill_buttons.append(desc)

            self.skill_buttons.append(btn)

    def _click(self, idx):
        self.selected_index = idx
        self._render_list()
        self._apply()

    def _select_next(self, _event=None):
        if self.filtered:
            self.selected_index = min(self.selected_index + 1, len(self.filtered) - 1)
            self._render_list()

    def _select_prev(self, _event=None):
        if self.filtered:
            self.selected_index = max(self.selected_index - 1, 0)
            self._render_list()

    def _on_enter(self, _event=None):
        self._apply()

    def _apply(self):
        if not self.filtered:
            return
        skill = self.filtered[self.selected_index]
        self.close()
        self.apply_callback(skill)

    def close(self):
        if self.window:
            self.window.destroy()
            self.window = None


class ScryptianEditor:
    def __init__(self, root, skills):
        self.root = root
        self.skills = skills
        self.tabs = []
        self.active_tab = None
        self.window = None
        self.visible = False
        self.find_dialog = None
        self.skill_palette = None
        self._config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".editor_state.json"
        )
        self._load_state()

    def _load_state(self):
        self._state = {"geometry": "1000x700", "recent_files": []}
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
        except Exception:
            pass

    def _save_state(self):
        try:
            if self.window:
                self._state["geometry"] = self.window.geometry()
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception:
            pass

    def toggle(self):
        import telemetry

        telemetry.send("hotkey_pressed")
        self.root.after(0, self._do_toggle)

    def _do_toggle(self):
        if self.visible:
            self._hide()
        else:
            self._show()

    def _show(self):
        if self.window and self.visible:
            self.window.lift()
            return

        self.skills = self._scan_skills()

        self.window = tk.Toplevel(self.root)
        self.window.title("Scryptian")
        self.window.configure(bg=C["base"])
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.window.geometry(self._state.get("geometry", "1000x700"))
        except Exception:
            self.window.geometry("1000x700")

        self._create_menu()
        self._create_tab_bar()
        self._create_content_area()
        self._create_status_bar()

        self.find_dialog = FindReplaceDialog(self.window, self._get_active_tab)
        self.skill_palette = SkillPalette(self.window, self.skills, self._apply_skill)

        self.window.bind("<Control-n>", lambda e: self._new_file())
        self.window.bind("<Control-o>", lambda e: self._open_file())
        self.window.bind("<Control-s>", lambda e: self._save_file())
        self.window.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        self.window.bind("<Control-w>", lambda e: self._close_tab())
        self.window.bind("<Control-z>", lambda e: self._undo())
        self.window.bind("<Control-y>", lambda e: self._redo())
        self.window.bind("<Control-Shift-Z>", lambda e: self._redo())
        self.window.bind("<Control-f>", lambda e: self.find_dialog.open_find())
        self.window.bind("<Control-h>", lambda e: self.find_dialog.open_replace())
        self.window.bind("<Control-k>", lambda e: self.skill_palette.show())
        self.window.bind("<Control-t>", lambda e: self._new_file())
        self.window.bind(
            "<F3>",
            lambda e: self.find_dialog._next_match() if self.find_dialog else None,
        )
        self.window.bind("<Control-Tab>", lambda e: self._next_tab())
        self.window.bind("<Control-Shift-Tab>", lambda e: self._prev_tab())

        self.visible = True

        if not self.tabs:
            self._new_file()

        self.window.after(50, self._force_focus)

    def _hide(self):
        if self.window:
            self._save_state()
            self.visible = False
            self.window.destroy()
            self.window = None
            self.tabs = []
            self.active_tab = None

    def _on_close(self):
        unsaved = [t for t in self.tabs if t.modified]
        if unsaved:
            self._prompt_save_all(unsaved)
        self._hide()

    def _prompt_save_all(self, unsaved):
        for tab in unsaved:
            result = tk.messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes to {tab.filename or 'untitled'}?",
                parent=self.window,
            )
            if result is True:
                self.active_tab = tab
                self._save_file()
            elif result is None:
                return False
        return True

    def _force_focus(self, attempt=0):
        if not self.window:
            return
        if sys.platform == "win32":
            try:
                import ctypes

                hwnd = int(self.window.wm_frame(), 16)
                fg = ctypes.windll.user32.GetForegroundWindow()
                tid_fg = ctypes.windll.user32.GetWindowThreadProcessId(fg, None)
                tid_self = ctypes.windll.kernel32.GetCurrentThreadId()
                ctypes.windll.user32.AttachThreadInput(tid_fg, tid_self, True)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.AttachThreadInput(tid_fg, tid_self, False)
            except Exception:
                pass
        self.window.focus_force()
        if self.active_tab:
            self.active_tab.text.focus_set()
        if attempt < 3:
            self.window.after(80, lambda: self._force_focus(attempt + 1))

    # -- Menu --

    def _create_menu(self):
        menubar = tk.Menu(
            self.window,
            bg=C["surface0"],
            fg=C["text"],
            activebackground=C["surface1"],
            activeforeground=C["text"],
        )

        file_menu = tk.Menu(menubar, tearoff=0, bg=C["surface0"], fg=C["text"])
        file_menu.add_command(label="New            Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open           Ctrl+O", command=self._open_file)
        file_menu.add_command(label="Save           Ctrl+S", command=self._save_file)
        file_menu.add_command(
            label="Save As        Ctrl+Shift+S", command=self._save_file_as
        )
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab      Ctrl+W", command=self._close_tab)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0, bg=C["surface0"], fg=C["text"])
        edit_menu.add_command(label="Undo           Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo           Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Find           Ctrl+F", command=lambda: self.find_dialog.open_find()
        )
        edit_menu.add_command(
            label="Replace        Ctrl+H",
            command=lambda: self.find_dialog.open_replace(),
        )
        menubar.add_cascade(label="Edit", menu=edit_menu)

        skills_menu = tk.Menu(menubar, tearoff=0, bg=C["surface0"], fg=C["text"])
        skills_menu.add_command(
            label="Run Skill      Ctrl+K", command=lambda: self.skill_palette.show()
        )
        menubar.add_cascade(label="Skills", menu=skills_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=C["surface0"], fg=C["text"])
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.window.config(menu=menubar)

    def _show_about(self):
        import tkinter.messagebox as messagebox

        messagebox.showinfo(
            "About Scryptian",
            "Scryptian - AI Text Editor\nLocal LLM powered text transformation.\n\nCtrl+Alt to toggle editor.\nCtrl+K to run skills.",
            parent=self.window,
        )

    # -- Tab bar --

    def _create_tab_bar(self):
        self.tab_bar = tk.Frame(self.window, bg=C["crust"], height=36)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)

        self.tab_container = tk.Frame(self.tab_bar, bg=C["crust"])
        self.tab_container.pack(side="left", fill="both", expand=True)

        add_btn = tk.Label(
            self.tab_bar,
            text=" + ",
            font=("Segoe UI", 14),
            bg=C["crust"],
            fg=C["overlay0"],
            cursor="hand2",
            padx=4,
        )
        add_btn.pack(side="left")
        add_btn.bind("<Button-1>", lambda e: self._new_file())

    def _refresh_tab_bar(self):
        for widget in self.tab_container.winfo_children():
            widget.destroy()

        for i, tab in enumerate(self.tabs):
            name = os.path.basename(tab.filename) if tab.filename else "untitled"
            if tab.modified:
                name = "*" + name

            is_active = tab == self.active_tab
            bg = C["surface0"] if is_active else C["crust"]
            fg = C["text"] if is_active else C["subtext0"]

            tab_frame = tk.Frame(self.tab_container, bg=bg)
            tab_frame.pack(side="left", fill="y", padx=1)

            label = tk.Label(
                tab_frame, text=f" {name} ", font=("Segoe UI", 10), bg=bg, fg=fg
            )
            label.pack(side="left", padx=4, pady=4)
            label.bind("<Button-1>", lambda e, idx=i: self._switch_tab(idx))

            close = tk.Label(
                tab_frame,
                text="x",
                font=("Segoe UI", 9),
                bg=bg,
                fg=C["overlay0"],
                cursor="hand2",
            )
            close.pack(side="right", padx=(0, 4))
            close.bind("<Button-1>", lambda e, idx=i: self._close_tab_at(idx))
            close.bind("<Enter>", lambda e, w=close: w.config(fg=C["red"]))
            close.bind("<Leave>", lambda e, w=close: w.config(fg=C["overlay0"]))

    def _switch_tab(self, idx):
        if idx < 0 or idx >= len(self.tabs):
            return
        if self.active_tab:
            self.active_tab.hide()
        self.active_tab = self.tabs[idx]
        self.active_tab.show()
        self._refresh_tab_bar()
        self._update_status()

    def _next_tab(self):
        if not self.tabs:
            return
        idx = self.tabs.index(self.active_tab) if self.active_tab else 0
        self._switch_tab((idx + 1) % len(self.tabs))

    def _prev_tab(self):
        if not self.tabs:
            return
        idx = self.tabs.index(self.active_tab) if self.active_tab else 0
        self._switch_tab((idx - 1) % len(self.tabs))

    def _close_tab_at(self, idx):
        if idx < 0 or idx >= len(self.tabs):
            return
        tab = self.tabs[idx]
        if tab.modified:
            result = tk.messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes to {tab.filename or 'untitled'}?",
                parent=self.window,
            )
            if result is True:
                self.active_tab = tab
                self._save_file()
            elif result is None:
                return

        was_active = tab == self.active_tab
        self.tabs.pop(idx)

        if was_active:
            if self.tabs:
                new_idx = min(idx, len(self.tabs) - 1)
                self._switch_tab(new_idx)
            else:
                self.active_tab = None
                self._new_file()
        else:
            if self.active_tab:
                self.active_tab.show()

        self._refresh_tab_bar()

    # -- Content area --

    def _create_content_area(self):
        self.content_frame = tk.Frame(self.window, bg=C["base"])
        self.content_frame.pack(fill="both", expand=True)

    def _get_active_tab(self):
        return self.active_tab

    # -- Status bar --

    def _create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg=C["crust"], height=24)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_lang = tk.Label(
            self.status_bar,
            text="Text",
            font=("Segoe UI", 9),
            bg=C["crust"],
            fg=C["subtext0"],
            padx=10,
        )
        self.status_lang.pack(side="left")

        self.status_pos = tk.Label(
            self.status_bar,
            text="Ln 1, Col 1",
            font=("Segoe UI", 9),
            bg=C["crust"],
            fg=C["subtext0"],
            padx=10,
        )
        self.status_pos.pack(side="left")

        self.status_encoding = tk.Label(
            self.status_bar,
            text="UTF-8",
            font=("Segoe UI", 9),
            bg=C["crust"],
            fg=C["subtext0"],
            padx=10,
        )
        self.status_encoding.pack(side="left")

        self.status_skill_hint = tk.Label(
            self.status_bar,
            text="Ctrl+K - Skills",
            font=("Segoe UI", 9),
            bg=C["crust"],
            fg=C["overlay0"],
            padx=10,
        )
        self.status_skill_hint.pack(side="right")

    def _update_status(self, _event=None):
        if not self.active_tab:
            return
        tab = self.active_tab
        self.status_lang.config(text=tab.language)
        try:
            pos = tab.text.index("insert")
            line, col = pos.split(".")
            self.status_pos.config(text=f"Ln {line}, Col {int(col) + 1}")
        except Exception:
            pass
        self._refresh_tab_bar()

    # -- File operations --

    def _new_file(self, content="", filename=None):
        tab = EditorTab(self.content_frame, filename=filename, content=content)
        self.tabs.append(tab)
        if self.active_tab:
            self.active_tab.hide()
        self.active_tab = tab
        tab.show()
        tab.text.bind("<KeyRelease>", self._update_status, add="+")
        tab.text.bind("<ButtonRelease-1>", self._update_status, add="+")
        tab.text.bind("<<Modified>>", self._refresh_tab_bar_event, add="+")
        self._refresh_tab_bar()
        self._update_status()

    def _refresh_tab_bar_event(self, _event=None):
        self.root.after(0, self._refresh_tab_bar)

    def _open_file(self):
        filetypes = [
            ("All Files", "*.*"),
            ("Python", "*.py"),
            ("JavaScript", "*.js"),
            ("TypeScript", "*.ts"),
            ("C Sharp", "*.cs"),
            ("Go", "*.go"),
            ("Rust", "*.rs"),
            ("Java", "*.java"),
            ("C/C++", "*.c *.cpp *.h *.hpp"),
            ("HTML", "*.html *.htm"),
            ("CSS", "*.css *.scss"),
            ("JSON", "*.json"),
            ("YAML", "*.yaml *.yml"),
            ("Markdown", "*.md"),
            ("Text", "*.txt"),
        ]
        paths = filedialog.askopenfilenames(
            title="Open File", filetypes=filetypes, parent=self.window
        )
        for path in paths:
            if not path:
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception:
                    content = ""
            self._new_file(content=content, filename=path)
            if path not in self._state.get("recent_files", []):
                self._state.setdefault("recent_files", [])
                self._state["recent_files"].insert(0, path)
                self._state["recent_files"] = self._state["recent_files"][:10]
            self._update_status()

    def _save_file(self):
        if not self.active_tab:
            return
        if not self.active_tab.filename:
            self._save_file_as()
            return
        try:
            content = self.active_tab.get_content()
            with open(self.active_tab.filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.active_tab.mark_saved()
            self._refresh_tab_bar()
            self._update_status()
        except Exception as e:
            import tkinter.messagebox as messagebox

            messagebox.showerror(
                "Save Error", f"Could not save file:\n{e}", parent=self.window
            )

    def _save_file_as(self):
        if not self.active_tab:
            return
        path = filedialog.asksaveasfilename(
            title="Save As",
            initialfile=(
                os.path.basename(self.active_tab.filename)
                if self.active_tab.filename
                else "untitled.txt"
            ),
            parent=self.window,
        )
        if path:
            self.active_tab.filename = path
            ext = os.path.splitext(path)[1].lower()
            self.active_tab.language = EXTENSION_MAP.get(ext, "Text")
            if self.active_tab.highlighter:
                self.active_tab.highlighter.set_language(self.active_tab.language)
            self._save_file()
            self._refresh_tab_bar()
            self._update_status()

    def _close_tab(self):
        if self.active_tab:
            idx = self.tabs.index(self.active_tab)
            self._close_tab_at(idx)

    # -- Edit operations --

    def _undo(self):
        if self.active_tab:
            self.active_tab.undo()

    def _redo(self):
        if self.active_tab:
            self.active_tab.redo()

    # -- Skill application --

    def _apply_skill(self, skill):
        tab = self.active_tab
        if not tab:
            return

        text = tab.get_selection()
        if not text.strip():
            text = tab.get_content()

        if not text.strip():
            tab.insert_text("[Scryptian] No text to process.")
            return

        status_label = tk.Label(
            self.status_bar,
            text=f"  Running: {skill['title']}...",
            font=("Segoe UI", 9),
            bg=C["crust"],
            fg=C["yellow"],
            padx=10,
        )
        status_label.pack(side="right")

        def execute():
            try:
                if not bridge.is_model_ready():
                    bridge._get_llm()

                mod = skill["module"]
                if hasattr(mod, "prompt"):
                    prompt_str = mod.prompt(text)
                    full_text = ""
                    for chunk in bridge.generate_stream(prompt_str):
                        full_text += chunk
                        snapshot = full_text
                        self.root.after(
                            0, lambda t=snapshot: self._stream_to_tab(t, tab)
                        )

                    import re

                    stripped = re.sub(r"<think>[\s\S]*?</think>", "", full_text).strip()
                    self.root.after(0, lambda: self._finish_skill(stripped, tab, skill))
                else:
                    result = mod.run(text)
                    self.root.after(0, lambda: self._finish_skill(result, tab, skill))
            except Exception as e:
                self.root.after(
                    0, lambda: self._finish_skill(f"[Scryptian Error] {e}", tab, skill)
                )
            finally:
                self.root.after(0, lambda: status_label.destroy())

        threading.Thread(target=execute, daemon=True).start()

    def _stream_to_tab(self, text, tab):
        if tab != self.active_tab:
            return
        try:
            sel_start = tab.text.index("sel.first")
            sel_end = tab.text.index("sel.last")
            tab.text.delete(sel_start, sel_end)
            tab.text.insert(sel_start, text)
        except tk.TclError:
            pass

    def _finish_skill(self, result, tab, skill):
        if not result:
            return
        if result.startswith("[Scryptian Error]"):
            import tkinter.messagebox as messagebox

            messagebox.showerror("Skill Error", result, parent=self.window)
            return

        try:
            sel_start = tab.text.index("sel.first")
            sel_end = tab.text.index("sel.last")
            tab.text.delete(sel_start, sel_end)
            tab.text.insert(sel_start, result)
        except tk.TclError:
            tab.text.insert("insert", result)

        tab.modified = True
        self._refresh_tab_bar()

        import telemetry

        telemetry.send("skill_run", {"name": skill["title"]})

    # -- Skill scanning --

    def _scan_skills(self):
        import importlib.util

        skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
        skills = []
        if not os.path.isdir(skills_dir):
            return skills

        for filename in sorted(os.listdir(skills_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            filepath = os.path.join(skills_dir, filename)
            meta = self._parse_metadata(filepath)
            try:
                spec = importlib.util.spec_from_file_location(
                    filename.replace(".py", ""), filepath
                )
                module = importlib.util.module_from_spec(spec)
                parent_dir = os.path.dirname(os.path.abspath(__file__))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"[Scryptian] Failed to load {filename}: {e}")
                continue

            if hasattr(module, "run"):
                skills.append(
                    {
                        "title": meta.get("title", filename.replace(".py", "")),
                        "description": meta.get("description", ""),
                        "author": meta.get("author", ""),
                        "module": module,
                        "filename": filename,
                        "category": meta.get("category", "general"),
                        "languages": meta.get("languages", "any"),
                    }
                )

        self.skills = skills
        if self.skill_palette:
            self.skill_palette.skills = skills
            self.skill_palette.filtered = list(skills)
        return skills

    def _parse_metadata(self, filepath):
        import re

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
