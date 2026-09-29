"""
Simple rule-based judge for a RAG evaluation harness.

Given a question, an "expects" string describing acceptable target phrases,
the generated answer, and the retrieved context chunks, decide whether the
answer (or, failing that, the retrieved context) contains one of the
expected phrases.
"""

import re
import string


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace for matching."""
    if not text:
        return ""

    text = text.lower()

    # Drop punctuation so "credit-hours" and "credit hours" compare equal.
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Collapse any run of whitespace down to single spaces.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _split_candidates(expects: str) -> list[str]:
    """Split an `expects` string into individual candidate phrases.

    Candidates may be separated by ';' or '|'. Empty/whitespace-only
    candidates are dropped.
    """
    if not expects:
        return []

    # Split on either delimiter.
    raw_candidates = re.split(r"[;|]", expects)

    candidates = [c.strip() for c in raw_candidates if c.strip()]
    return candidates


def _contains_phrase(phrase: str, target_text: str) -> bool:
    """Check whether `phrase` is present in `target_text`.

    Matching strategy:
      1. Normalize both strings.
      2. Try an exact normalized substring match.
      3. Fall back to a "bag of words" check: every word in `phrase` must
         appear somewhere in `target_text`.
    """
    norm_phrase = _normalize(phrase)
    norm_target = _normalize(target_text)

    if not norm_phrase or not norm_target:
        return False

    # 1. Exact substring match.
    if norm_phrase in norm_target:
        return True

    # 2. Fallback: all words of the phrase appear somewhere in the target.
    phrase_words = norm_phrase.split()
    target_words = set(norm_target.split())

    return all(word in target_words for word in phrase_words)


def _extract_result_text(result) -> str:
    """Best-effort extraction of text content from a single retrieved result.

    Supports plain strings as well as objects/dicts exposing a text-like
    attribute or key (e.g. `text`, `content`, `page_content`, `document`).
    """
    if result is None:
        return ""

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in ("text", "content", "page_content", "document"):
            value = result.get(key)
            if isinstance(value, str):
                return value
        return ""

    for attr in ("text", "content", "page_content", "document"):
        value = getattr(result, attr, None)
        if isinstance(value, str):
            return value

    return ""


def judge(question: str, expects: str, answer: str | None, results) -> bool:
    """Decide whether `answer` (or, failing that, `results`) satisfies `expects`.

    Args:
        question: The original question (not used for matching, but part of
            the standard judge signature for logging/debugging purposes).
        expects: One or more candidate target phrases separated by ';' or '|'.
        answer: The generated answer text, or None if generation failed.
        results: An iterable of retrieved context chunks (strings, dicts, or
            objects exposing a text-like attribute).

    Returns:
        True if any candidate phrase is found in the answer or, failing
        that, in the joined retrieved context. False otherwise (including
        when `expects` is empty).
    """
    candidates = _split_candidates(expects)
    if not candidates:
        return False

    # 1. Check the generated answer first.
    if answer:
        if any(_contains_phrase(candidate, answer) for candidate in candidates):
            return True

    # 2. Fall back to the retrieved context chunks.
    if results:
        joined_results = " ".join(_extract_result_text(r) for r in results)
        if any(_contains_phrase(candidate, joined_results) for candidate in candidates):
            return True

    return False


if __name__ == "__main__":
    # Sample test cases in the form (question, expects, answer).
    test_cases = [
        (
            "How is course difficulty determined?",
            "not random; credit hours",
            "Course difficulty is not random, it is based on credit hours.",
        ),
        (
            "What determines course difficulty?",
            "credit hours",
            "It depends on how many credit hours the course is worth.",
        ),
        (
            "Why is grading structured this way?",
            "fair | consistent",
            "The system aims to be fair and consistent across sections.",
        ),
        (
            "What is the capital of France?",
            "paris",
            "I'm not sure, the documents don't mention that.",
        ),
        (
            "Empty expects case",
            "",
            "Some answer text here.",
        ),
        (
            "None answer case",
            "credit hours",
            None,
        ),
    ]

    class _FakeResult:
        """Minimal stand-in for a retrieved chunk object with a `.text` attr."""

        def __init__(self, text: str):
            self.text = text

    # Results only used for the "None answer" case, to show the context fallback.
    sample_results = [
        _FakeResult("Grades depend on credit hours and attendance."),
        _FakeResult("Some unrelated chunk of text."),
    ]

    print("Running scorer.py self-tests...\n")

    for question, expects, answer in test_cases:
        # Only the "None answer" case gets sample_results; others get no context.
        results = sample_results if answer is None else []
        outcome = judge(question, expects, answer, results)
        print(f"Q: {question!r}")
        print(f"  expects: {expects!r}")
        print(f"  answer:  {answer!r}")
        print(f"  -> judge() = {outcome}\n")
