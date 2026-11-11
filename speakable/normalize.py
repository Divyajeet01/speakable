"""Turn LLM output into text a TTS engine can speak correctly.

The problem this solves: an LLM happily returns "**Total: $1,234.56** due on
2026-11-11 - call Dr. Rao at (555) 123-4567". Feed that straight to TTS and the
caller hears "asterisk asterisk total dollar one comma two three four".
"""
import re

from .numbers import (MONTHS, decimal_to_words, digits_to_words, int_to_words,
                      ordinal_to_words, year_to_words)

CURRENCIES = {
    "$": ("dollar", "cent"),
    "₹": ("rupee", "paisa"),
    "£": ("pound", "penny"),
    "€": ("euro", "cent"),
    "¥": ("yen", "sen"),
}

ABBREVIATIONS = {
    "Dr": "Doctor", "Mr": "Mister", "Mrs": "Missus", "Ms": "Miss",
    "Prof": "Professor", "Jr": "Junior", "Sr": "Senior", "St": "Street",
    "Ave": "Avenue", "Rd": "Road", "Blvd": "Boulevard", "Ln": "Lane",
    "Apt": "Apartment", "Ste": "Suite", "Inc": "Incorporated",
    "Corp": "Corporation", "Ltd": "Limited", "Dept": "Department",
    "approx": "approximately", "vs": "versus", "etc": "et cetera",
}
PHRASES = {
    "e.g.": "for example", "i.e.": "that is",
    "a.m.": "AM", "p.m.": "PM",
    "&": " and ", "%": " percent ", "=": " equals ",
    "<": " less than ", ">": " greater than ",
}
UNITS = {
    "kg": "kilograms", "mg": "milligrams", "lbs": "pounds", "lb": "pounds",
    "oz": "ounces", "km": "kilometers", "cm": "centimeters",
    "mm": "millimeters", "mi": "miles", "ft": "feet", "hrs": "hours",
    "hr": "hours", "sec": "seconds", "ms": "milliseconds",
    "kb": "kilobytes", "mb": "megabytes", "gb": "gigabytes",
    "tb": "terabytes",
}
# Acronyms a TTS engine already says correctly as a word.
PRONOUNCEABLE = {"NASA", "RADAR", "LASER", "SCUBA", "JSON", "YAML", "SOAP",
                 "REST", "SIP", "RAM", "ROM", "AIDS", "OPEC", "NATO", "SIM"}

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U0000FE00-\U0000FE0F\U00002B00-\U00002BFF]+")


def _say_number(raw):
    """'1,234.5' -> 'one thousand two hundred thirty-four point five'"""
    raw = raw.replace(",", "")
    if "." in raw:
        whole, _, frac = raw.partition(".")
        return decimal_to_words(whole, frac)
    return int_to_words(int(raw))


_FRACTIONS = {
    (1, 2): "one half", (1, 3): "one third", (2, 3): "two thirds",
    (1, 4): "one quarter", (3, 4): "three quarters", (1, 5): "one fifth",
    (1, 8): "one eighth", (3, 8): "three eighths", (5, 8): "five eighths",
}


def _say_fraction(num, den):
    if (num, den) in _FRACTIONS:
        return _FRACTIONS[(num, den)]
    return "%s over %s" % (int_to_words(num), int_to_words(den))


def _strip_markdown(text):
    text = re.sub(r"```[\s\S]*?```", " ", text)           # fenced code
    text = re.sub(r"`([^`]*)`", r"\1", text)              # inline code
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)     # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links -> label
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)  # bullets
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.M)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", " ", text, flags=re.M)
    text = re.sub(r"(\*\*\*|___)(.+?)\1", r"\2", text, flags=re.S)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text, flags=re.S)
    text = re.sub(r"(?<!\w)([*_])(?!\s)(.+?)(?<!\s)\1(?!\w)", r"\2", text)
    text = re.sub(r"~~(.+?)~~", r"\1", text)
    # Streaming or truncated LLM output leaves unpaired markers behind. Any
    # asterisk that survives the rules above would be spoken aloud, so drop it.
    text = re.sub(r"\*+", "", text)
    return text


def _say_money(symbol, whole, frac):
    major, minor = CURRENCIES[symbol]
    amount = int(whole.replace(",", ""))
    out = "%s %s%s" % (int_to_words(amount), major,
                       "" if amount == 1 else "s")
    if frac and int(frac):
        cents = int(frac.ljust(2, "0")[:2])
        if minor == "penny":
            word = "penny" if cents == 1 else "pence"
        elif minor == "paisa":
            word = "paisa" if cents == 1 else "paise"
        else:
            word = minor if cents == 1 else minor + "s"
        out += " and %s %s" % (int_to_words(cents), word)
    return out


def _say_date(y, m, d):
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return ""
    return "%s %s, %s" % (MONTHS[m - 1], ordinal_to_words(d), year_to_words(y))


def _say_time(h, mi, meridiem):
    if h > 23 or mi > 59:
        return ""
    if not meridiem and h >= 13:
        # 24-hour input: nobody says "fourteen o'clock" out loud.
        h, meridiem = h - 12, "PM"
    elif not meridiem and h == 0:
        h, meridiem = 12, "AM"
    hour = int_to_words(h if h else 12)
    if mi == 0:
        body = hour + " o'clock"
    elif mi < 10:
        body = "%s oh %s" % (hour, int_to_words(mi))
    else:
        body = "%s %s" % (hour, int_to_words(mi))
    tail = meridiem.upper().replace(".", "")
    return (body + " " + tail).strip()


def _month_name(token):
    for name in MONTHS:
        if name.lower().startswith(token[:3].lower()):
            return name
    return token


def normalize(text, spell_acronyms=False, strip_emoji=True):
    """Rewrite `text` so a TTS engine speaks it the way a human would."""
    if not text:
        return ""
    t = _strip_markdown(text)
    if strip_emoji:
        t = _EMOJI.sub(" ", t)

    # Emails and URLs first, before anything else touches the dots.
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
               lambda m: m.group(0).replace("@", " at ").replace(".", " dot "),
               t)
    t = re.sub(r"https?://\S+|\bwww\.\S+",
               lambda m: re.sub(r"/\S*$", "",
                                re.sub(r"https?://|www\.", "", m.group(0)))
               .replace(".", " dot "), t)

    # Dotted numerics before everything numeric, or the phone matcher claims
    # them: "192.168.1.1" is seven digits and three separators.
    t = re.sub(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b",
               lambda m: " dot ".join(int_to_words(int(g))
                                      for g in m.groups()), t)
    t = re.sub(r"\bv?(\d+)\.(\d+)\.(\d+)\b",
               lambda m: " point ".join(int_to_words(int(g))
                                        for g in m.groups()), t)

    # Dates before phone numbers: 2026-11-11 is digits-and-hyphens too.
    t = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b",
               lambda m: _say_date(int(m.group(1)), int(m.group(2)),
                                   int(m.group(3))) or m.group(0), t)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
               lambda m: _say_date(int(m.group(3)), int(m.group(1)),
                                   int(m.group(2))) or m.group(0), t)
    month_re = "|".join(MONTHS + [m[:3] for m in MONTHS])
    t = re.sub(r"\b(" + month_re + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?"
               r"(?:,?\s*(\d{4}))?\b",
               lambda m: _month_name(m.group(1)) + " "
               + ordinal_to_words(int(m.group(2)))
               + (", " + year_to_words(int(m.group(3))) if m.group(3) else ""),
               t, flags=re.I)

    # Note: the meridiem deliberately does not absorb a trailing dot, so that
    # "at 3:30 PM." keeps the sentence-ending period.
    t = re.sub(r"\b(\d{1,2}):(\d{2})(?:\s*([ap]\.?m))?",
               lambda m: _say_time(int(m.group(1)), int(m.group(2)),
                                   m.group(3) or "") or m.group(0),
               t, flags=re.I)

    def _phone(m):
        raw = m.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if not 7 <= len(digits) <= 15:
            return m.group(0)
        # A digit run alone is not a phone number - "1000-2000" is a range.
        # Require real phone shape: a country code, parens, two or more
        # separators, or an unbroken run long enough to be a full number.
        seps = len(re.findall(r"[\s\-.]", raw))
        if not (raw.startswith("+") or "(" in raw or seps >= 2
                or (seps == 0 and len(digits) >= 10)):
            return m.group(0)
        return digits_to_words(raw)

    # The leading paren must be inside the match, or "(555) 123-4567" leaves a
    # stray "(" behind once the digits are rewritten.
    t = re.sub(r"(?<![\w$.])\+?\(?\d[\d\-.\s()]{6,18}\d\)?(?![\w])", _phone, t)

    t = re.sub(r"#(?=\d)", "number ", t)

    # Ranges, now that whatever is left is not a phone number.
    t = re.sub(r"\b(\d[\d,]*)\s?-\s?(\d[\d,]*)\b",
               lambda m: _say_number(m.group(1)) + " to "
               + _say_number(m.group(2)), t)
    # A bare leading minus is spoken, not silent. Must follow the range rule,
    # whose hyphen is preceded by a digit and so is unaffected.
    t = re.sub(r"(?<![\w\d])-\s?(?=\d)", "negative ", t)

    t = re.sub(r"\b(\d+)/(\d+)\b",
               lambda m: _say_fraction(int(m.group(1)), int(m.group(2))), t)

    sym = "|".join(re.escape(s) for s in CURRENCIES)
    t = re.sub("(" + sym + r")\s?(\d[\d,]*)(?:\.(\d{1,2}))?",
               lambda m: _say_money(m.group(1), m.group(2), m.group(3)), t)
    t = re.sub(r"(\d[\d,]*(?:\.\d+)?)\s?%",
               lambda m: _say_number(m.group(1)) + " percent", t)
    t = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b",
               lambda m: ordinal_to_words(int(m.group(1))), t)
    t = re.sub(r"\b(\d[\d,]*(?:\.\d+)?)\s?(" + "|".join(UNITS) + r")\b",
               lambda m: _say_number(m.group(1)) + " " + UNITS[m.group(2)], t)

    for abbr, full in ABBREVIATIONS.items():
        t = re.sub(r"\b" + re.escape(abbr) + r"\.", full, t)
    for src, dst in PHRASES.items():
        t = t.replace(src, dst)

    t = re.sub(r"\b\d[\d,]*(?:\.\d+)?\b", lambda m: _say_number(m.group(0)), t)

    if spell_acronyms:
        t = re.sub(r"\b([A-Z]{2,5})\b",
                   lambda m: m.group(1) if m.group(1) in PRONOUNCEABLE
                   else " ".join(m.group(1)), t)

    # A bare "#" with no number after it would be read out as "hash".
    t = re.sub(r"#", " ", t)

    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+([,.!?;:])", r"\1", t)
    return re.sub(r"\n{2,}", "\n", t).strip()
