import re

with open('services/rag_service.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_prompt = False
for line in lines:
    if 'def _build_prompt' in line:
        in_prompt = True
        new_lines.append(line)
        continue
    if in_prompt and 'def _build_direct_answer_prompt' in line:
        in_prompt = False
        # Insert the correct body
        new_lines.append(r'''        template_fields = []
        intent = retrieval_plan.get("intent", "") if retrieval_plan else ""
        if retrieval_plan and "response_template" in retrieval_plan:
            template_fields = retrieval_plan["response_template"]
        
        json_fields = [
            '"answer": "Your detailed explanation of 3 to 4 sentences here",',
            '"confidence": 95,',
            '"citations": [{{"document_name": "...", "page_number": 1, "section_title": "..."}}],',
            '"safety_flag": false,',
            '"follow_up_suggestions": ["...", "..."],',
            '"data": {{'
        ]
        
        if template_fields:
            for field in template_fields:
                key = field.lower().replace(" ", "_")
                json_fields.append(f'    "{key}": "...",')  
        else:
            json_fields.append('    "details": "..."')
            
        json_fields.append('  }}')
        json_schema = "\n".join(json_fields)
        
        intent_rules = ""
        if intent == "RCA":
            intent_rules = (
                "\nROOT CAUSE ANALYSIS RULES:\n"
                "- The root cause MUST be a physical or process failure mechanism.\n"
                "- Merge evidence chronologically based on document dates.\n"
                "- Prioritize evidence from: Incident Reports, RCA Reports, Failure Logs.\n"
            )
        
        list_rules = ""
        if any(w in (retrieval_plan or {}).get("intent", "").lower() for w in ["incident", "maintenance", "inspection"]):
            list_rules = (
                "\nLIST QUERY RULES:\n"
                "- If the user asks to 'show', 'list', or 'find all' matching records, return ALL matching items.\n"
            )
        
        prompt_text = (
            "You are Industrial Brain AI, an expert assistant for FreshFlow Beverages plant operations.\n\n"
            "Answer the operator's question using ONLY the context provided below.\n"
            "OPERATOR QUESTION: {question}\n"
            "ASSET CONTEXT: {asset_tag}\n"
            "OPERATOR ROLE: {user_role}\n\n"
            "RULES:\n"
            "1. KEEP RESPONSES UNDER 250 WORDS unless the user asks for 'full details' or 'detailed analysis'.\n"
            "2. NEVER expose raw JSON, internal schema, backend keys (answer, data, confidence, citations, follow_up_suggestions) to the user.\n"
            "3. Format your response strictly using the markdown template below.\n"
            "4. Show detailed timelines, evidence, RCA, and JSON ONLY when explicitly asked for full details.\n"
            "5. Always cite your sources using [Document Name (Page X)] format.\n\n"
            "FORMAT TEMPLATE (Use exactly these headings):\n"
            "📌 Summary\n"
            "- Direct answer in 2–3 sentences.\n\n"
            "📋 Key Findings\n"
            "- 3–5 important points only.\n\n"
            "⚠ Recommendations (if applicable)\n"
            "- Short actionable recommendations.\n\n"
            "📄 Sources\n"
            "- Document Name (Page Number)\n\n"
            "💡 Related Questions\n"
            "- 3 suggested follow-up questions.\n\n"
            + intent_rules
            + list_rules +
            "\nRespond in this exact JSON format. Put your formatted markdown inside the 'answer' field:\n"
            + json_schema +
            "\n\nSearch Log:\n{search_log}\n\n"
            "Context: {context_chunks}\n"
            "Question: {question}"
        )
        return PromptTemplate.from_template(prompt_text)

''')
        new_lines.append(line)
        continue
        
    if not in_prompt:
        new_lines.append(line)

with open('services/rag_service.py', 'w') as f:
    f.writelines(new_lines)


