# @title: Optimize C#
# @description: Optimize C# code for performance
# @author: Scryptian
# @category: programming
# @languages: C#

import bridge


def prompt(text):
    return (
        "<Instruction>Optimize the following C# code for better performance, "
        "memory usage, and follows C# best practices. "
        "Output only the optimized code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
