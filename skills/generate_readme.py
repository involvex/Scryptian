# @title: Generate README
# @description: Generate a README.md for the selected code
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Generate a comprehensive README.md for the following code. Include: description, installation, usage, and examples. Output only the markdown content.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
