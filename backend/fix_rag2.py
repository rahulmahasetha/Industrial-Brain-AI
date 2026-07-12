import re

with open('services/rag_service.py', 'r') as f:
    content = f.read()

# We need to replace everything from `    def _build_direct_answer_prompt(self) -> PromptTemplate:`
# down to the line with `        return PromptTemplate.from_template(prompt_text)` that belongs to it.

new_func = r'''    def _build_direct_answer_prompt(self) -> PromptTemplate:
        """Lightweight prompt for concise/direct answers."""
        prompt_text = (
            "You are Industrial Brain AI, an expert assistant for FreshFlow Beverages plant operations.\n\n"
            "Answer the operator's question using ONLY the context provided below.\n"
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
            "Search Log:\n{search_log}\n\n"
            "Context: {context_chunks}\n"
            "Question: {question}"
        )
        return PromptTemplate.from_template(prompt_text)'''

content = re.sub(r'    def _build_direct_answer_prompt\(self\) -> PromptTemplate:\n.*?(?=\n    def _rerank_pages)', new_func, content, flags=re.DOTALL)

with open('services/rag_service.py', 'w') as f:
    f.write(content)


