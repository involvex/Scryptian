# @title: Optimize Python
# @description: Optimize Python code for performance
# @author: Scryptian
# @category: programming
# @languages: Python

import bridge


def prompt(text):
    return (
        "<Instruction>Optimize the following Python code for better performance "
        "and readability. Follow PEP 8 and Python best practices. "
        "Output only the optimized code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
