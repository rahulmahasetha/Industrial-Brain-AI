import re

def clean_llm_json_output(text):
    # Remove <think>...</think> blocks entirely (including spanning multiple lines)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Extract JSON between the first { and last }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx+1]
    return ""
