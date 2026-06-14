# @title: Refactor Code
# @description: Refactor code for better readability and performance
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Refactor the following code for better readability, "
        "performance, and maintainability. Output only the refactored code. "
        "Do not explain changes.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
