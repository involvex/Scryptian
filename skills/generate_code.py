# @title: Generate Code
# @description: Generate code from a description
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Generate code based on the following description. "
        "Output only the code, no explanation. Use modern best practices. "
        "Include type hints where applicable.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
