# @title: Python Class Generator
# @description: Generate Python classes with type hints
# @author: Scryptian
# @category: programming
# @languages: Python

import bridge


def prompt(text):
    return (
        "<Instruction>Generate a Python class based on the following description. "
        "Include type hints, docstrings, and common methods. "
        "Follow PEP 8. Output only the code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
