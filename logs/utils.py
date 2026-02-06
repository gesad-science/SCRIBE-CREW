import sys

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

import re

ANSI_ESCAPE = re.compile(
    r"""
    \x1B
    (?:[@-Z\\-_]|
    \[[0-?]*[ -/]*[@-~])
    """,
    re.VERBOSE,
)

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)

def remove_characters(text: str) -> str:
    chars = ["─", "│", "╭", "╮", "╰", "╯", "├", "•", "└"]
    for c in chars:
        text = text.replace(c, "")
    return text.split()


def normalize_multiline_patterns(lines: list[str], patterns: list[str]) -> list[str]:
    tokenized_patterns = [
        pattern.split()
        for pattern in patterns
    ]

    i = 0
    out = []

    while i < len(lines):
        matched = False

        for tokens in tokenized_patterns:
            n = len(tokens)

            if i + n > len(lines):
                continue

            window = [lines[i + j].strip() for j in range(n)]

            if all(
                window[j].lower() == tokens[j].lower()
                for j in range(n)
            ):
                out.append(" ".join(tokens))
                i += n
                matched = True
                break

        if not matched:
            out.append(lines[i])
            i += 1

    return out


def parse_by_patterns(lines: list[str], patterns: list[str]) -> list[dict]:

    pattern_set = set(patterns)

    results = []
    current_pattern = None
    buffer = []

    def flush():
        nonlocal buffer
        if current_pattern is not None:
            content = " ".join(buffer).strip()
            results.append({current_pattern: content})
        buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line in pattern_set:
            flush()
            current_pattern = line
            continue

        if current_pattern is not None:
            buffer.append(line)

    # flush final
    flush()

    return results

def remove_from_list(result:list[dict], keywords:list[str]):
    for act in list(result):
        key = list(act.keys())[0]
        if key in keywords:
            result.remove(act)

    return result

def build_high_level_story(parsed_events):
    story = []

    current_agent = None
    current_step = None

    for event in parsed_events:
        key, value = list(event.items())[0]

        # ---------- Agent Started ----------
        if key == "Agent Started":
            if current_agent:
                story.append(current_agent)

            agent_name = value.replace("Agent:", "").strip()

            current_agent = {
                "agent": agent_name,
                "steps": [],
                "final_answer": None
            }

        # ---------- Tool ----------
        elif key.startswith("Using Tool"):
            tool_name = value.strip()

            current_step = {
                "tool": tool_name,
                "input": None,
                "output": None
            }

            current_agent["steps"].append(current_step)

        elif key == "Tool Input":
            if current_step:
                current_step["input"] = value

        elif key == "Tool Output":
            if current_step:
                current_step["output"] = value

        # ---------- Final Answer ----------
        elif key == "Agent Final Answer":
            if current_agent:
                current_agent["final_answer"] = value

    if current_agent:
        story.append(current_agent)

    return story




import json


def try_parse_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return value
    return value


def json_to_tree(data, indent=0):
    space = "  " * indent
    output = ""

    if isinstance(data, dict):
        for key, value in data.items():
            value = try_parse_json(value)

            if isinstance(value, (dict, list)):
                output += f"{space}{key}:\n"
                output += json_to_tree(value, indent + 1)
            else:
                output += f"{space}{key}: {value}\n"

    elif isinstance(data, list):
        for item in data:
            item = try_parse_json(item)

            output += f"{space}- "
            if isinstance(item, (dict, list)):
                output += "\n"
                output += json_to_tree(item, indent + 1)
            else:
                output += f"{item}\n"

    else:
        output += f"{space}{data}\n"

    return output


def event_stream_to_tree(events):
    result = ""

    for i, event in enumerate(events):
        result += f"Event {i}\n"
        result += json_to_tree(event, indent=1)
        result += "\n"

    return result


def save_tree_to_file(events, filename="agent_execution_tree.txt"):
    tree_text = event_stream_to_tree(events)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(tree_text)

    return filename
