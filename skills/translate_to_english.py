# @title: Translate to English
# @description: Translate any text to English keeping meaning and tone
# @author: Scryptian

import bridge


def prompt(text):
    return (
        "Translate the following text into natural, idiomatic English. "
        "Do NOT translate word-by-word. Rephrase so it sounds like a native English speaker wrote it. "
        "Keep the original meaning and tone. Output ONLY the translation:\n\n"
        f"{text}"
    )


def run(text):
    """
    text: text from clipboard to translate to English
    """
    return bridge.generate(prompt(text))
