# @title: Add Comments
# @description: Add explanatory comments to code
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Add clear, concise comments to the following code. Focus on explaining WHY, not WHAT. Output only the updated code with comments added.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
