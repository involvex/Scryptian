# @title: Add Docstrings
# @description: Add docstrings to Python functions and classes
# @author: Scryptian
# @category: programming
# @languages: Python

import bridge


def prompt(text):
    return (
        "<Instruction>Add comprehensive docstrings to all functions and classes in the following Python code. Follow Google docstring format. Output only the updated code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
