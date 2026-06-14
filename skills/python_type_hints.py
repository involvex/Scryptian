# @title: Add Type Hints
# @description: Add type hints to Python code
# @author: Scryptian
# @category: programming
# @languages: Python

import bridge


def prompt(text):
    return (
        "<Instruction>Add type hints to the following Python code. Use modern typing syntax (list, dict, union with |). Output only the updated code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
