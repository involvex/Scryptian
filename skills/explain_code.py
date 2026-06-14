# @title: Explain Code
# @description: Explain what selected code does line by line
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Explain the following code line by line. "
        "Be concise and clear. Focus on what the code does, "
        "not how to improve it. Output only the explanation.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
