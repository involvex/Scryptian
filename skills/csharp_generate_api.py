# @title: C# API Generator
# @description: Generate C# API endpoints and controllers
# @author: Scryptian
# @category: programming
# @languages: C#

import bridge


def prompt(text):
    return (
        "<Instruction>Generate C# API endpoints based on the following description. "
        "Include controllers, models, and proper async/await patterns. "
        "Output only the code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
