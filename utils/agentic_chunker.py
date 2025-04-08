
import re
import tiktoken

class AgenticChunker:
    def __init__(self, max_tokens=250, overlap=30):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.encoder = tiktoken.get_encoding("gpt2")

    def split_by_symptom_blocks(self, text):
        # Chunk on common troubleshooting section dividers or symptom keywords
        sections = re.split(r'(?i)(?=symptom:|issue:|problem:|error code\s*\w+)', text)
        blocks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            tokens = self.encoder.encode(section)
            if len(tokens) > self.max_tokens:
                # Split long sections by tokens
                start = 0
                while start < len(tokens):
                    end = min(start + self.max_tokens, len(tokens))
                    chunk_tokens = tokens[start:end]
                    chunk = self.encoder.decode(chunk_tokens)
                    blocks.append(chunk.strip())
                    start += self.max_tokens - self.overlap
            else:
                blocks.append(section)
        return blocks

    def chunk(self, text, metadata=None):
        blocks = self.split_by_symptom_blocks(text)
        return [{
            "title": f"Symptom Block {i+1}",
            "text": block,
            "page": metadata.get("page", 0) if metadata else 0
        } for i, block in enumerate(blocks)]
