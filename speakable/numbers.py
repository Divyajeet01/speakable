"""English number-to-words. No dependencies, so the API has no cold-start cost."""

_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
         "eighty", "ninety"]
_SCALES = [(10**12, "trillion"), (10**9, "billion"), (10**6, "million"),
           (10**3, "thousand")]

_ORDINALS = {
    "one": "first", "two": "second", "three": "third", "four": "fourth",
    "five": "fifth", "six": "sixth", "seven": "seventh", "eight": "eighth",
    "nine": "ninth", "ten": "tenth", "eleven": "eleventh", "twelve": "twelfth",
    "thirteen": "thirteenth", "fourteen": "fourteenth", "fifteen": "fifteenth",
    "sixteen": "sixteenth", "seventeen": "seventeenth",
    "eighteen": "eighteenth", "nineteen": "nineteenth", "twenty": "twentieth",
    "thirty": "thirtieth", "forty": "fortieth", "fifty": "fiftieth",
    "sixty": "sixtieth", "seventy": "seventieth", "eighty": "eightieth",
    "ninety": "ninetieth", "hundred": "hundredth", "thousand": "thousandth",
    "million": "millionth", "billion": "billionth", "zero": "zeroth",
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _under_hundred(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")


def _under_thousand(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    parts = []
    if hundreds:
        parts += [_ONES[hundreds], "hundred"]
    if rest:
        parts.append(_under_hundred(rest))
    return " ".join(parts)


def int_to_words(n: int) -> str:
    """1234 -> 'one thousand two hundred thirty-four'"""
    if n < 0:
        return "negative " + int_to_words(-n)
    if n == 0:
        return "zero"
    parts = []
    for value, name in _SCALES:
        if n >= value:
            chunk, n = divmod(n, value)
            parts += [int_to_words(chunk), name]
    if n:
        parts.append(_under_thousand(n))
    return " ".join(parts)


def digits_to_words(s: str) -> str:
    """'555' -> 'five five five'. For phone numbers and codes."""
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(_ONES[int(ch)])
        elif ch == "+":
            out.append("plus")
        elif ch in "-.()":
            continue
        else:
            out.append(ch)
    return " ".join(out)


def decimal_to_words(whole: str, frac: str) -> str:
    """'3', '14' -> 'three point one four'"""
    head = int_to_words(int(whole)) if whole else "zero"
    return f"{head} point {digits_to_words(frac)}"


def ordinal_to_words(n: int) -> str:
    """3 -> 'third', 21 -> 'twenty-first'"""
    words = int_to_words(n)
    head, sep, last = words.rpartition("-")
    if not sep:
        head, sep, last = words.rpartition(" ")
    if last in _ORDINALS:
        return head + sep + _ORDINALS[last]
    return words + "th"


def year_to_words(y: int) -> str:
    """2026 -> 'twenty twenty-six', 1905 -> 'nineteen oh five'"""
    if 1100 <= y < 2000 or 2010 <= y < 2100:
        hi, lo = divmod(y, 100)
        if lo == 0:
            return f"{int_to_words(hi)} hundred"
        if lo < 10:
            return f"{int_to_words(hi)} oh {_ONES[lo]}"
        return f"{int_to_words(hi)} {_under_hundred(lo)}"
    return int_to_words(y)
