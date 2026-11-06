"""Lossless literal offsets: gaps/lengths as unsigned base-128 varints.

Zero marks a punctuation gap; other records contain (start - previous_end + 1,
length). Base64 keeps the stream inside JSON. This is our own offset container,
not a Protobuf message. References: U1 p.43–48; protobuf.dev encoding/#varints.
"""
import base64
from functools import lru_cache

ENCODING = "gap-length-varint-v1"


def _append_integer(output, value):
    if not 0 <= value < 2 ** 64:
        raise ValueError("Offset integer is outside unsigned 64-bit range")
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)


def encode(values):
    output, previous_end = bytearray(), 0
    for value in values:
        if value is None:
            _append_integer(output, 0)
            continue
        start, end = value
        if start < previous_end or end <= start:
            raise ValueError("Literal offsets must be ordered nonempty spans")
        _append_integer(output, start - previous_end + 1)
        _append_integer(output, end - start)
        previous_end = end
    return base64.b64encode(output).decode("ascii")


def _integers(raw):
    value = shift = 0
    for byte in raw:
        value |= (byte & 127) << shift
        if value >= 2 ** 64:
            raise ValueError("Offset integer exceeds unsigned 64-bit range")
        if byte < 128:
            yield value
            value = shift = 0
        else:
            shift += 7
            if shift >= 70:
                raise ValueError("Invalid offset varint")
    if shift:
        raise ValueError("Truncated offset varint")


@lru_cache(maxsize=128)
def decode(encoded):
    """Decode only requested fields, retaining at most 128 immutable results."""
    integers = iter(_integers(base64.b64decode(encoded, validate=True)))
    output, previous_end = [], 0
    for gap in integers:
        if gap == 0:
            output.append(None)
            continue
        length = next(integers, None)
        if length is None or length == 0:
            raise ValueError("Invalid or truncated offset span")
        start = previous_end + gap - 1
        previous_end = start + length
        output.append((start, previous_end))
    return tuple(output)
