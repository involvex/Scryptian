# @title: React Hooks Generator
# @description: Generate React hooks from component code
# @author: Scryptian
# @category: programming
# @languages: TypeScript

import bridge


def prompt(text):
    return (
        "<Instruction>Extract logic from the following React component and generate "
        "custom hooks. Follow React best practices. "
        "Output only the hook code.</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
