with open('services/rag_service.py', 'r') as f:
    content = f.read()

old_rules = """            "4. Show detailed timelines, evidence, RCA, and JSON ONLY when explicitly asked for full details.\\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\\n\\n" """

new_rules = """            "4. Show detailed timelines, evidence, RCA, and JSON ONLY when explicitly asked for full details.\\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\\n"
            "6. CRITICAL: You MUST escape all newlines in your markdown as \\\\n inside the JSON string (e.g. 'Summary\\\\n- Text'). Do not use literal newlines.\\n\\n" """

content = content.replace(old_rules, new_rules)

# Also let's add a small cleanup in case JSON decode fails due to newlines
old_json_parse = """                try:
                    match = re.search(r'\\{.*\\}', raw_answer, re.DOTALL)
                    if match:
                        parsed_json = json.loads(match.group())
                    else:
                        parsed_json = json.loads(raw_answer)"""

new_json_parse = """                try:
                    match = re.search(r'\\{.*\\}', raw_answer, re.DOTALL)
                    json_str = match.group() if match else raw_answer
                    
                    # Fix common unescaped newlines in JSON strings by replacing literal newlines with \\n
                    # Only do this if standard parsing fails
                    try:
                        parsed_json = json.loads(json_str)
                    except json.JSONDecodeError:
                        # naive attempt to escape newlines inside the JSON string
                        # just escape all newlines since the JSON schema doesn't strictly need them
                        json_str_fixed = json_str.replace('\\n', '\\\\n')
                        parsed_json = json.loads(json_str_fixed)"""

content = content.replace(old_json_parse, new_json_parse)

with open('services/rag_service.py', 'w') as f:
    f.write(content)
