# @title: Optimize TypeScript
# @description: Optimize TypeScript code for performance
# @author: Scryptian
# @category: programming
# @languages: TypeScript

import bridge


def prompt(text):
    return (
        "<Instruction>Optimize the following TypeScript code for better performance "
        "and type safety. Output only the optimized code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
