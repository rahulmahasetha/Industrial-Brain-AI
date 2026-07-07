with open('services/rag_service.py', 'r') as f:
    content = f.read()

# Replace rules in _build_prompt
old_rules_1 = """            "RULES:\\n"
            "1. KEEP RESPONSES UNDER 250 WORDS unless the user asks for 'full details' or 'detailed analysis'.\\n"
            "2. NEVER expose raw JSON, internal schema, backend keys (answer, data, confidence, citations, follow_up_suggestions) to the user.\\n"
            "3. Format your response strictly using the markdown template below.\\n"
            "4. Show detailed timelines, evidence, RCA, and JSON ONLY when explicitly asked for full details.\\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\\n"
            "6. CRITICAL: You MUST escape all newlines in your markdown as \\\\n inside the JSON string (e.g. 'Summary\\\\n- Text'). Do not use literal newlines.\\n\\n" """

new_rules_1 = """            "RULES:\\n"
            "1. Answer the user's question directly in the first 2-3 sentences.\\n"
            "2. Never return raw JSON or long paragraphs. KEEP RESPONSES UNDER 250 WORDS unless the user asks for 'full details'.\\n"
            "3. Display results in tables whenever multiple records exist, and group similar records instead of repeating information.\\n"
            "4. Highlight the most important findings only. Show recommendations only when relevant.\\n"
            "5. Always include source document names and page numbers in [Document Name (Page X)] format.\\n"
            "6. If no exact record exists, explain what was searched and show the closest matching records.\\n"
            "7. If the user asks for 'full details', display the complete report; otherwise keep responses concise.\\n"
            "8. Format your response strictly using the markdown template below.\\n"
            "9. CRITICAL: You MUST escape all newlines in your markdown as \\\\n inside the JSON string (e.g. 'Summary\\\\n- Text'). Do not use literal newlines.\\n\\n" """

content = content.replace(old_rules_1, new_rules_1)


# Replace rules in _build_direct_answer_prompt
old_rules_2 = """            "RULES:\\n"
            "1. KEEP RESPONSES UNDER 250 WORDS unless the user asks for 'full details' or 'detailed analysis'.\\n"
            "2. NEVER expose raw JSON, internal schema, backend keys (answer, data, confidence, citations, follow_up_suggestions) to the user.\\n"
            "3. Format your response strictly using the markdown template below.\\n"
            "4. Show detailed timelines, evidence, RCA, and JSON ONLY when explicitly asked for full details.\\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\\n\\n" """

new_rules_2 = """            "RULES:\\n"
            "1. Answer the user's question directly in the first 2-3 sentences.\\n"
            "2. Never return raw JSON or long paragraphs. KEEP RESPONSES UNDER 250 WORDS unless the user asks for 'full details'.\\n"
            "3. Display results in tables whenever multiple records exist, and group similar records instead of repeating information.\\n"
            "4. Highlight the most important findings only. Show recommendations only when relevant.\\n"
            "5. Always include source document names and page numbers in [Document Name (Page X)] format.\\n"
            "6. If no exact record exists, explain what was searched and show the closest matching records.\\n"
            "7. If the user asks for 'full details', display the complete report; otherwise keep responses concise.\\n"
            "8. Format your response strictly using the markdown template below.\\n\\n" """

content = content.replace(old_rules_2, new_rules_2)

with open('services/rag_service.py', 'w') as f:
    f.write(content)
