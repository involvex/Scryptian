import json
import re
import ssl
from urllib import error, parse, request

import bridge

_API_BASE = "https://api.dictionaryapi.dev/api/v2/entries"
_LANGS = {"en", "es", "fr", "de", "it", "pt-BR", "ru", "tr"}
_MAX_WORD_LENGTH = 100
_MAX_DEFINITIONS = 3
_MAX_MEANINGS = 6
_USER_AGENT = "Scryptian/0.5.2 (https://github.com/adrianium/Scryptian)"


def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _language():
    try:
        value = (bridge.get_state("dictionary").get("settings", {}) or {}).get("lang", "en")
    except Exception:
        value = "en"
    return value if value in _LANGS else "en"


def _get_json(url):
    req = request.Request(url, headers={"User-Agent": _USER_AGENT})
    with request.urlopen(req, timeout=10, context=_ssl_ctx()) as response:
        return json.loads(response.read().decode("utf-8"))


def _translate_many(values, lang):
    cleaned = [_clean(value) for value in values]
    if lang == "en" or not any(cleaned):
        return cleaned

    target = "pt" if lang == "pt-BR" else ("zh-CN" if lang == "zh" else lang)
    marker = " SCRYPTIAN_TRANSLATION_ITEM_9F3A "
    translated = []
    batch = []
    batch_length = 0

    def flush(items):
        if not items:
            return []
        source = marker.join(items)
        url = "https://translate.googleapis.com/translate_a/single"
        params = parse.urlencode({"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": source})
        try:
            data = _get_json(f"{url}?{params}")
            result = _clean("".join(part[0] for part in data[0] if part[0]))
            parts = [part.strip() for part in result.split("SCRYPTIAN_TRANSLATION_ITEM_9F3A")]
            return parts if len(parts) == len(items) else items
        except Exception:
            return items

    for value in cleaned:
        if batch and batch_length + len(value) + len(marker) > 3000:
            translated.extend(flush(batch))
            batch = []
            batch_length = 0
        batch.append(value)
        batch_length += len(value) + len(marker)
    translated.extend(flush(batch))
    return translated


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _lookup(word, lang):
    url = f"{_API_BASE}/{parse.quote(lang)}/{parse.quote(word)}"
    try:
        return _get_json(url)
    except error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _format_entry(entries, output_lang):
    if isinstance(entries, dict):
        entries = [entries]

    entries = entries or []
    if not entries:
        return ""

    first = entries[0]
    word = _clean(first.get("word"))
    phonetic = _clean(first.get("phonetic"))
    header = word or "Dictionary result"
    if phonetic:
        header += f"\n/{phonetic.strip('/')} /".replace(" /", "/")

    example_label = "Example"
    translation_label = "Translation"
    synonyms_label = "Synonyms"
    records = []
    translation_values = []
    for entry in entries:
        for meaning in (entry.get("meanings") or [])[:_MAX_MEANINGS]:
            part = _clean(meaning.get("partOfSpeech"))
            translation_values.append(part)
            definitions = meaning.get("definitions") or []
            definition_records = []
            for item in definitions[:_MAX_DEFINITIONS]:
                definition = _clean(item.get("definition"))
                example = _clean(item.get("example"))
                translation_values.extend([definition, example])
                definition_records.append((definition, example))
            records.append((part, definition_records))

    synonyms = []
    for entry in entries:
        for meaning in entry.get("meanings") or []:
            synonyms.extend(meaning.get("synonyms") or [])
            for item in meaning.get("definitions") or []:
                synonyms.extend(item.get("synonyms") or [])
    unique_synonyms = list(dict.fromkeys(_clean(item) for item in synonyms if _clean(item)))
    translated_values = _translate_many(translation_values, output_lang)
    translated_iter = iter(translated_values)
    sections = [header]
    for part, definition_records in records:
        translated_part = next(translated_iter, part)
        block = []
        if translated_part:
            block.append(translated_part.capitalize())
        for index, (definition, example) in enumerate(definition_records, 1):
            translated_definition = next(translated_iter, definition)
            translated_example = next(translated_iter, example)
            if not translated_definition:
                continue
            block.append(f"{index}. {translated_definition}")
            if example:
                block.append(f"{example_label}: {example}")
                if output_lang != "en" and translated_example and translated_example != example:
                    block.append(f"{translation_label}: {translated_example}")
        if block:
            sections.append("\n".join(block))

    if unique_synonyms:
        sections.append(synonyms_label + "\n" + ", ".join(unique_synonyms[:12]))

    return "\n\n".join(sections).strip()


def run(text):
    query = _clean(text)
    if not query:
        return "[Scryptian Error] Select a word first."
    if len(query) > _MAX_WORD_LENGTH:
        return "[Scryptian Error] The selected word is too long."
    if len(query.split()) != 1:
        return "[Scryptian Error] Select one word, not a phrase."

    output_lang = _language()
    try:
        entry = _lookup(query, "en")
        if not entry and output_lang != "en":
            entry = _lookup(query, output_lang)
    except Exception as exc:
        return f"[Scryptian Error] Could not reach Dictionary API: {exc}"

    if not entry:
        return f"No definition found for: {query}"
    result = _format_entry(entry, output_lang)
    return result or f"No definition found for: {query}"
