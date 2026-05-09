# @title: Change tone to friendly
# @description: Rewrite text in a warm, friendly tone
# @author: Scryptian

import bridge


def prompt(text):
    return (
        "Rewrite the following text in a warm, friendly, and approachable tone. "
        "Keep the original meaning and length. Output ONLY the rewritten text:\n\n"
        f"{text}"
    )


def run(text):
    """
    text: text from clipboard to rewrite in a friendly tone
    """
    return bridge.generate(prompt(text))
