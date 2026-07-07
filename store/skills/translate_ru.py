# @title: Translate to Russian
# @description: Translate text to Russian (Google Translate)
# @author: Scryptian

from urllib import request, parse
import json
import ssl
import bridge

TARGET_LANG = "ru"


def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def run(text):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = parse.urlencode({"client": "gtx", "sl": "auto", "tl": TARGET_LANG, "dt": "t", "q": text})
        resp = request.urlopen(f"{url}?{params}", timeout=10, context=_ssl_ctx())
        data = json.loads(resp.read())
        return "".join(part[0] for part in data[0] if part[0])
    except Exception:
        if not bridge.is_model_ready():
            return "[Scryptian Error] Translation failed: no internet connection and AI model is not downloaded yet."
        return bridge.generate(f"Translate the following text to {TARGET_LANG}. Output ONLY the translated text:\n\n{text}")
