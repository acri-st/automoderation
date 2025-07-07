import re


def split_into_sentences(text: str) -> list:
    """Splits a given text into sentences using common punctuation marks.

    Args:
        text (str): The input text to split.

    Returns:
        list: A list of sentences.
    """
    # Regular expression to split sentences on '.', '!', or '?' followed by a space or end of string
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    # Remove empty strings from the result
    return [s for s in sentences if s]
