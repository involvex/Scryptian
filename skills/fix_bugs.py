# @title: Fix Bugs
# @description: Analyze and fix bugs in selected code
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Analyze the following code for bugs and fix them. "
        "Output only the corrected code. If there are no bugs, output the "
        "original code unchanged.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
