# store.py - Online skill store backed by Supabase and public Storage.

import os
import io
import json
import ssl
import zipfile
from urllib import request


def _load_env():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


_load_env()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_TABLE = os.environ.get("SUPABASE_SKILLS_TABLE", "skills")
SUPABASE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "skills")


def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _require_config():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError(
            "Supabase Store is not configured. Copy .env.example to .env and fill SUPABASE_URL and SUPABASE_ANON_KEY."
        )


def _headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "User-Agent": "Scryptian Store",
    }


def _storage_url(path):
    path = str(path or "").lstrip("/")
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"


def _skill_download_url(skill):
    return skill.get("download_url") or _storage_url(
        skill.get("storage_path") or skill.get("archive") or skill.get("filename", "")
    )


def fetch_registry(timeout=10):
    """Fetch skill metadata from the public Supabase REST table."""
    _require_config()
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=*"
    req = request.Request(url, headers=_headers())
    with request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data if isinstance(data, list) else data.get("skills", [])


def _bundle_dir_name(skill):
    """Folder name a bundle installs into."""
    name = skill.get("filename", "")
    return name[:-4] if name.endswith(".zip") else name


def is_installed(skill, skills_dir):
    """skill is a registry dict. Handles both single-file and bundle skills."""
    if skill.get("type") == "bundle":
        return os.path.isdir(os.path.join(skills_dir, _bundle_dir_name(skill)))
    return os.path.exists(os.path.join(skills_dir, skill.get("filename", "")))


def _version_tuple(v):
    """Parse a dotted version string into a comparable tuple. Bad input -> (0,)."""
    try:
        return tuple(int(x) for x in str(v).strip().split("."))
    except Exception:
        return (0,)


def installed_version(skill, skills_dir):
    """Return the locally installed version of a bundle skill, or None.

    Single-file skills carry no version metadata, so this only applies to
    bundles (which have a manifest.json).
    """
    if skill.get("type") != "bundle":
        return None
    manifest_path = os.path.join(skills_dir, _bundle_dir_name(skill), "manifest.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None


def has_update(skill, skills_dir):
    """True if the skill is installed but the registry offers a newer version."""
    if not is_installed(skill, skills_dir):
        return False
    registry_ver = skill.get("version")
    local_ver = installed_version(skill, skills_dir)
    if not registry_ver or not local_ver:
        return False
    return _version_tuple(registry_ver) > _version_tuple(local_ver)


def install_skill(skill, skills_dir):
    """Download and install a skill. Returns the installed path."""
    os.makedirs(skills_dir, exist_ok=True)

    _require_config()

    if skill.get("type") == "bundle":
        url = _skill_download_url(skill)
        req = request.Request(url, headers=_headers())
        with request.urlopen(req, timeout=30, context=_ssl_ctx()) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(skills_dir)
        return os.path.join(skills_dir, _bundle_dir_name(skill))

    filename = skill.get("filename", "")
    url = _skill_download_url(skill)
    req = request.Request(url, headers=_headers())
    resp = request.urlopen(req, timeout=15, context=_ssl_ctx())
    content = resp.read()
    path = os.path.join(skills_dir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path
