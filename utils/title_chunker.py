import re
import tiktoken


class TitleChunker:
    def __init__(self, max_title_tokens=50, max_title_words=15):
        self.max_title_tokens = max_title_tokens
        self.max_title_words = max_title_words
        self.encoder = tiktoken.get_encoding("gpt2")

    def trim_title(self, title):
        # Limit by word count first
        words = title.strip().split()
        if len(words) > self.max_title_words:
            title = " ".join(words[: self.max_title_words])
        # Then ensure token count is safe
        tokens = self.encoder.encode(title)
        if len(tokens) > self.max_title_tokens:
            trimmed_tokens = tokens[: self.max_title_tokens]
            title = self.encoder.decode(trimmed_tokens)
        return title.strip()

    def chunk(self, text):
        sections = re.split(r"\n(?=\d+\.\s)", text)
        chunks = []
        for i, section in enumerate(sections):
            lines = section.strip().split("\n")
            if not lines:
                continue
            raw_title = lines[0].strip()
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
            trimmed_title = (
                self.trim_title(raw_title) if raw_title else f"Section {i+1}"
            )
            chunks.append({"title": trimmed_title, "text": body, "page": i + 1})
        return chunks
