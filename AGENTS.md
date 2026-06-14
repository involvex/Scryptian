# AGENTS.md - Scryptian

> Instructions for AI coding agents working on this codebase.

---

## Project Overview

Scryptian is a **Windows desktop application** for inline AI text editing. It runs as a system tray app, triggered by a global hotkey (`Ctrl+Alt`). Text is copied from the clipboard, processed by a **local LLM** (SmolLM3-3B via llama.cpp), and the result is returned to the clipboard.

Key characteristics:
- **Offline-first**: All AI inference runs locally on the user's machine
- **Privacy-focused**: No data leaves the device (except anonymous telemetry via PostHog)
- **Skill-based architecture**: Each text transformation is a separate `.py` file in `skills/`
- **Single-file EXE distribution**: Built with PyInstaller

---

## Technologies

| Layer | Technology |
|---|---|
| Language | Python 3.10+ (tested with 3.12) |
| UI | tkinter (custom hotkey bar overlay) |
| AI Engine | llama.cpp via `llama-cpp-python` (SmolLM3-Q4_K_M GGUF model) |
| System Tray | `pystray` + `Pillow` |
| Clipboard | `pyperclip` |
| Hotkey | `keyboard` |
| Telemetry | PostHog (anonymous, stdlib `urllib`) |
| Build | PyInstaller (`build.spec`) |
| Installer | Inno Setup 6 (`installer.iss`) |
| Platform | Windows 10/11 x64 only |

---

## Project Structure

```
Scryptian/
├── main.py              # Entry point: skill scanner, UI bar, hotkey, tray
├── bridge.py            # LLM bridge: model download, loading, generate/generate_stream
├── config.py            # Central config: paths, model settings, telemetry keys
├── bootstrap.py         # Clean install: wipes old data, extracts fresh skills
├── telemetry.py         # Anonymous analytics via PostHog (stdlib only)
├── tray.py              # System tray icon and menu
├── autostart.py         # Windows startup registry management
├── build.spec           # PyInstaller build configuration
├── installer.iss        # Inno Setup installer script
├── requirements.txt     # Python dependencies
├── icon.ico             # Application icon
├── skills/              # AI skill plugins (one .py file = one skill)
│   ├── translate.py
│   ├── translate_to_english.py
│   ├── summarize.py
│   ├── improve_writing.py
│   ├── fix_grammar.py
│   ├── friendly_tone.py
│   ├── professional_tone.py
│   ├── explain_simply.py
│   └── humanize.py
├── models/              # GGUF model files (gitignored)
├── vendor/              # Vendored dependencies (llama-cpp-python)
└── docs/                # Web page assets
```

---

## Useful Commands

### Development

```bash
# Run the app in development mode
python main.py

# Install dependencies
pip install pyinstaller pystray keyboard pyperclip certifi posthog

# Install llama-cpp-python (compiles from source, takes 5-10 min)
pip install cmake ninja scikit-build-core
git clone --recursive https://github.com/abetlen/llama-cpp-python.git vendor/llama-cpp-python
pip install vendor/llama-cpp-python --no-cache-dir --no-build-isolation
```

### Building

```bash
# Build the EXE
pyinstaller build.spec --noconfirm
# Output: dist/Scryptian.exe

# Build the installer (requires Inno Setup 6)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
# Output: dist/Scryptian_Setup.exe
```

### Debugging

```bash
# Check if model is present
dir models\SmolLM3-Q4_K_M.gguf

# Verify skills are loadable (no syntax errors)
python -c "import importlib.util; spec = importlib.util.spec_from_file_location('test', 'skills/summarize.py'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); print('OK')"

# Test bridge/generation directly
python -c "import bridge; print(bridge.generate('Say hello in one word'))"
```

---

## Architecture Notes

### Main Loop (`main.py`)
- tkinter `root.mainloop()` runs on the main thread
- `keyboard.add_hotkey()` listens globally and calls `bar.toggle()` from any thread
- `ScryptianBar` manages the overlay UI as a `tk.Toplevel` window
- Skills are hot-reloaded from disk on every bar open
- Results are copied to clipboard on Enter

### LLM Bridge (`bridge.py`)
- Model is lazily loaded on first skill invocation
- Download happens automatically from HuggingFace (~1.9 GB, one-time)
- `generate()` for non-streaming, `generate_stream()` for streaming
- Both strip `<think>...</think>` tags from model output
- Model config: `CONTEXT_SIZE=2048`, `TEMPERATURE=0` (deterministic)

### Skills System
- Each skill is a standalone `.py` file in `skills/`
- Metadata via header comments: `@title`, `@description`, `@author`
- Must expose a `run(text) -> str` function
- Optionally expose a `prompt(text) -> str` function for streaming mode
- Skills are dynamically loaded via `importlib.util`

---

## Best Practices and Guidelines

### When Modifying Skills

1. **Keep skills self-contained** - each skill should be a single `.py` file with no external dependencies beyond `bridge`
2. **Use `bridge.generate()` or `bridge.generate_stream()`** - do not call the LLM directly
3. **Include metadata headers** - always add `@title`, `@description`, `@author` in comments at the top
4. **Return clean output** - return only the transformed text, no preamble or explanation
5. **Handle errors gracefully** - return `[Scryptian Error] <message>` on failure
6. **The model strips thinking tags** - you do not need to handle `<think>` tags in skill code

### When Modifying Core Modules

1. **Threading safety** - UI updates must go through `root.after(0, callback)`. Never update tkinter widgets from background threads
2. **Windows-specific code** - guard with `if IS_WINDOWS:` or `if sys.platform == "win32":`
3. **Model changes affect all skills** - any change to `bridge.py` impacts every skill
4. **Config is centralized** - all paths, model settings, and constants live in `config.py`
5. **Telemetry is anonymous** - use `telemetry.send(event, properties)` for tracking; do not send PII

### When Adding Dependencies

1. **Minimize dependencies** - prefer stdlib where possible (the project uses `urllib` for downloads and telemetry)
2. **Update `requirements.txt`** - add any new pip packages
3. **Update `build.spec`** - add to `hiddenimports` if PyInstaller can't find it
4. **Test the EXE build** - verify the dependency bundles correctly with PyInstaller

### When Modifying the UI

1. **Catppuccin Mocha palette** - colors are hardcoded: `#1e1e2e` (base), `#313244` (surface), `#45475a` (overlay), `#cdd6f4` (text), `#585b70` (subtext), `#6c7086` (overlay1)
2. **Font: Segoe UI** - system font on Windows, used for UI elements
3. **Font: Consolas** - used for the result text box
4. **Dynamic resizing** - the bar height adjusts to content; use `_resize()` and `update_idletasks()`
5. **Focus management** - Windows requires `AttachThreadInput` hack for reliable focus stealing; see `_force_focus()`

### Code Style

1. **Python 3.10+** - use modern syntax (match/case, type hints where helpful)
2. **No type annotations required** - the codebase does not use them consistently
3. **Comments are minimal** - the code is self-documenting; add comments only for non-obvious logic
4. **Error handling** - wrap external calls (network, file I/O) in try/except; return error strings, do not crash
5. **ASCII only** - avoid unicode characters like em-dash, arrows; use `-`, `->`, `...`

### Testing

- There is no formal test suite
- Manual testing: run `python main.py`, press `Ctrl+Alt`, select a skill, verify output
- Test with empty clipboard, long text, and special characters
- Verify the EXE builds and runs on a clean Windows machine

### Git and Commits

- Commit messages should be concise and descriptive
- Use present tense: "Add skill for X" not "Added skill for X"
- Reference issue numbers when applicable
- Do not commit `models/`, `dist/`, `build/`, or `*.gguf` files

---

## Common Pitfalls

1. **tkinter thread safety** - never call tkinter methods from non-main threads; always use `root.after()`
2. **PyInstaller path resolution** - use `sys._MEIPASS` for bundled resources, `os.path.dirname(__file__)` for dev mode
3. **Model download on first use** - the app blocks until the ~1.9 GB model downloads; handle this gracefully in the UI
4. **Clipboard access** - `pyperclip` may fail if clipboard is locked by another app; always wrap in try/except
5. **Hotkey conflicts** - `Ctrl+Alt` may conflict with other apps; users can change it in `config.py`
6. **Registry writes** - `autostart.py` modifies `HKEY_CURRENT_USER`; failures are silently ignored (non-admin environments)

---

## File Editing Rules

- **Never modify** `vendor/` directory - these are vendored upstream dependencies
- **Never commit** `.env`, `.id`, `models/`, or `dist/` contents
- **Config changes** in `config.py` affect the entire application; test thoroughly
- **Skill files** are extracted from the bundle on app update; local modifications in `skills/` may be overwritten when running the EXE
