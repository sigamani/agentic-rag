import re

def safe_trim(text, max_tokens, encoding_name="gpt2"):
    enc = tiktoken.get_encoding(encoding_name)
    token_ids = enc.encode(text)
    if len(token_ids) <= max_tokens:
        return text
    trimmed_text = enc.decode(token_ids[:max_tokens])
    # Try trimming to last sentence end
    sentences = re.split(r'(?<=[.!?]) +', trimmed_text)
    result = ""
    for sentence in sentences:
        if count_tokens(result + sentence, encoding_name) <= max_tokens:
            result += sentence + " "
        else:
            break
    return result.strip()
