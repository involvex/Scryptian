# @title: TS to Interface
# @description: Generate TypeScript interfaces from JSON or data
# @author: Scryptian
# @category: programming
# @languages: TypeScript

import bridge


def prompt(text):
    return (
        "<Instruction>Convert the following data or JSON into TypeScript interfaces. "
        "Include proper types, optional markers, and JSDoc comments. "
        "Output only the interface definitions.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
