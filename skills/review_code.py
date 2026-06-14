# @title: Code Review
# @description: Review code for issues and improvements
# @author: Scryptian
# @category: programming
# @languages: any

import bridge


def prompt(text):
    return (
        "<Instruction>Review the following code for issues, improvements, "
        "and best practices. Format your review as:\n"
        "- Issues found: (list)\n"
        "- Suggestions: (list)\n"
        "- Rating: (1-5 stars)</Instruction>\n\n"
        f"{text}"
    )


def run(text):
    return bridge.generate(prompt(text))
