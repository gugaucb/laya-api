import pytest
from laya_api.validator import ContextValidator, ContextLengthExceededError

def test_context_validator_passes_when_within_limit():
    validator = ContextValidator(max_tokens=100)
    # 5 words -> approx 5 tokens
    text = "This is a short input text."
    tokens, count = validator.validate_and_tokenize(text, on_overflow="error")
    assert count <= 100
    assert len(tokens) == count

def test_context_validator_raises_when_exceeding_limit_with_error_strategy():
    validator = ContextValidator(max_tokens=10)
    long_text = "word " * 20
    with pytest.raises(ContextLengthExceededError) as exc_info:
        validator.validate_and_tokenize(long_text, on_overflow="error")
    
    assert exc_info.value.token_count > 10
    assert exc_info.value.max_tokens == 10
    assert "exceeds model context window" in str(exc_info.value)

def test_context_validator_truncates_head_when_requested():
    validator = ContextValidator(max_tokens=5)
    # Provide 10 distinct words
    text = "one two three four five six seven eight nine ten"
    tokens, count = validator.validate_and_tokenize(text, on_overflow="truncate_head")
    assert count == 5
    assert len(tokens) == 5
    # Head truncated means retaining the tail (six, seven, eight, nine, ten)
    decoded = validator.decode(tokens)
    assert "ten" in decoded

def test_context_validator_truncates_tail_when_requested():
    validator = ContextValidator(max_tokens=5)
    text = "one two three four five six seven eight nine ten"
    tokens, count = validator.validate_and_tokenize(text, on_overflow="truncate_tail")
    assert count == 5
    assert len(tokens) == 5
    # Tail truncated means retaining the head (one, two, three, four, five)
    decoded = validator.decode(tokens)
    assert "one" in decoded
