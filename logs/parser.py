from logs.utils import  strip_ansi, remove_characters, normalize_multiline_patterns, parse_by_patterns, remove_from_list, build_high_level_story, save_tree_to_file

patterns = ["Agent Started", "Executing Task" "Task Completed", "Task:", "Agent Final Answer", "User Input", "Using Tool:", "Tool Input", "Tool Output", "Tool Description:"]
remove = ["Task:", "Tool Description:"]
raw_log = open("system.log", encoding="utf-8").read()
clean_lines = remove_characters(strip_ansi(raw_log))
#parsed = parse_crewai_log(clean_lines)

clean_lines = normalize_multiline_patterns(lines=clean_lines, patterns=patterns)

result = parse_by_patterns(clean_lines, patterns)
result = remove_from_list(result, remove)
result = build_high_level_story(result)

graph = save_tree_to_file(result)

#for p in result:
#    print(p)
