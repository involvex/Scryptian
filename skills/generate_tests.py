# @title: Generate Tests
# @description: Generate unit tests for selected code
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Generate comprehensive unit tests for the following code. "
        "Use the appropriate test framework for the language. Cover edge cases "
        "and error conditions. Output only the test code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
