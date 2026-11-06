"""Recognize explicit local-file append requests and documented effects."""
import re

_FILE = re.compile(r"\b(?:files?|logs?|paths?)\b")
_APPEND = re.compile(r"\bappend(?:ing)?\b|\b(?:add|write)\b.{0,45}\b(?:to|at) the end of\b")
_PRESERVE = re.compile(r"\b(?:keep(?:ing)?|preserv(?:e|ing)) (?:the )?(?:existing|previous|prior|old) (?:contents?|lines|data)\b")
_WRITE = re.compile(r"\b(?:write|writing|add|adding)\b")
_WITHOUT_OVERWRITE = re.compile(r"\bwithout overwriting\b", re.I)
_OTHER_EFFECT = re.compile(r"\b(?:overwrit\w*|truncat\w*|delet\w*|archives?|zip|tar|non[- ]append\w*)\b")


def requested(text):
    operation = _APPEND.search(text) or (_WRITE.search(text) and _PRESERVE.search(text))
    return bool(_FILE.search(text) and operation and not _OTHER_EFFECT.search(text))


def intent_text(text):
    """Treat a no-overwrite qualifier as positive only for explicit append requests."""
    affirmative = _WITHOUT_OVERWRITE.sub(" ", text)
    return affirmative if requested(affirmative.lower()) else text


def note_evidence(note):
    """Only accept affirmative file-append statements in official variant notes."""
    for phrase in ("Append data to the end of the output file,", "Data is appended to the file and "):
        if note.startswith(phrase):
            return "example", phrase.rstrip()
    if re.fullmatch(r"Use \x60-a\x60 to append data to (?:exising|existing) files\.", note):
        return "option", note.replace(chr(96), "")
    return None
