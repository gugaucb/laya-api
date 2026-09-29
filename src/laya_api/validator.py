"""Context window and token validator for Laya API."""

from typing import List, Tuple, Literal

class ContextLengthExceededError(ValueError):
    """Raised when request tokens exceed the maximum context window."""
    def __init__(self, token_count: int, max_tokens: int):
        self.token_count = token_count
        self.max_tokens = max_tokens
        super().__init__(
            f"Input token count ({token_count}) exceeds model context window limit ({max_tokens} tokens). "
            "Configure 'on_overflow' parameter to 'truncate_head' or 'truncate_tail' to allow automatic truncation."
        )


class ContextValidator:
    """Validates and enforces token limits against model context windows."""
    
    def __init__(self, max_tokens: int = 1024, tokenizer=None):
        self.max_tokens = max_tokens
        self._tokenizer = tokenizer

    def _tokenize(self, text: str) -> List[str]:
        if self._tokenizer is not None and hasattr(self._tokenizer, "tokenize"):
            return self._tokenizer.tokenize(text)
        # Fast fallback tokenization: whitespace-separated words/tokens
        return text.split()

    def decode(self, tokens: List[str]) -> str:
        if self._tokenizer is not None and hasattr(self._tokenizer, "decode"):
            return self._tokenizer.decode(tokens)
        return " ".join(tokens)

    def validate_and_tokenize(
        self,
        text: str,
        on_overflow: Literal["error", "truncate_head", "truncate_tail"] = "error"
    ) -> Tuple[List[str], int]:
        tokens = self._tokenize(text)
        total_tokens = len(tokens)

        if total_tokens <= self.max_tokens:
            return tokens, total_tokens

        if on_overflow == "error":
            raise ContextLengthExceededError(token_count=total_tokens, max_tokens=self.max_tokens)
        elif on_overflow == "truncate_head":
            truncated_tokens = tokens[-self.max_tokens:]
            return truncated_tokens, len(truncated_tokens)
        elif on_overflow == "truncate_tail":
            truncated_tokens = tokens[:self.max_tokens:]
            return truncated_tokens, len(truncated_tokens)
        else:
            raise ValueError(f"Unknown overflow strategy: '{on_overflow}'")
