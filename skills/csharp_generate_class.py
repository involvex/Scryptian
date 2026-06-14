# @title: C# Class Generator
# @description: Generate C# classes with properties and methods
# @author: Scryptian
# @category: programming
# @languages: C#

import bridge


def prompt(text):
    return (
        "<Instruction>Generate a C# class based on the following description. "
        "Include properties, constructor, and common methods. "
        "Follow C# naming conventions. Output only the code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
