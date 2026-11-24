"""Turn LLM output into text a TTS engine can speak correctly.

The problem this solves: an LLM happily returns "**Total: $1,234.56** due on
2026-11-11 - call Dr. Rao at (555) 123-4567". Feed that straight to TTS and the
caller hears "asterisk asterisk total dollar one comma two three four".

Rule order is most of the difficulty here. Each block below notes what it has
to run before or after, and why.
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
# The ISO code an LLM writes when it has no symbol to hand: "USD 50", "50 EUR".
CURRENCY_CODES = {
    "USD": ("US dollar", "cent"), "EUR": ("euro", "cent"),
    "GBP": ("pound", "penny"), "INR": ("rupee", "paisa"),
    "JPY": ("yen", "sen"), "CAD": ("Canadian dollar", "cent"),
    "AUD": ("Australian dollar", "cent"), "CHF": ("Swiss franc", "centime"),
}
# "$1.5M" is a sum of money, not one dollar fifty and a stray spoken letter.
MAGNITUDES = {"k": "thousand", "m": "million", "b": "billion", "t": "trillion",
              "bn": "billion", "mn": "million", "tn": "trillion"}

ABBREVIATIONS = {
    "Dr": "Doctor", "Mr": "Mister", "Mrs": "Missus", "Ms": "Miss",
    "Prof": "Professor", "Jr": "Junior", "Sr": "Senior", "St": "Street",
    "Ave": "Avenue", "Rd": "Road", "Blvd": "Boulevard", "Ln": "Lane",
    "Apt": "Apartment", "Ste": "Suite", "Inc": "Incorporated",
    "Corp": "Corporation", "Ltd": "Limited", "Dept": "Department",
    "approx": "approximately", "vs": "versus", "etc": "et cetera",
}
# Abbreviations that sit *before* a name ("Dr. Rao") or join two clauses
# ("Acme vs. Beta") can never be the last word of a sentence, so their full stop
# always belongs to the abbreviation. Every other one sits *after* its noun
# ("42 Oak St.") and so can end a sentence - there the full stop has to survive,
# or TTS runs the two sentences together.
_NEVER_ENDS_SENTENCE = {"Dr", "Mr", "Mrs", "Ms", "Prof", "vs", "approx"}

# Dotted initialisms. Spacing the letters out is what makes a TTS engine say
# "U S" instead of the word "us". Longest key first: "U.S.A." before "U.S.".
INITIALISMS = {
    "U.S.A.": "U S A", "U.S.": "U S", "U.K.": "U K", "E.U.": "E U",
    "Ph.D.": "P H D", "M.D.": "M D", "B.A.": "B A", "M.A.": "M A",
    "a.k.a.": "also known as", "A.M.": "AM", "P.M.": "PM",
}
# Only the period-terminated form is expanded: a bare "Sat" or "Sun" is as
# likely to be an ordinary word as a weekday.
DAYS = {
    "Mon": "Monday", "Tues": "Tuesday", "Tue": "Tuesday", "Weds": "Wednesday",
    "Wed": "Wednesday", "Thurs": "Thursday", "Thur": "Thursday",
    "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday",
}

PHRASES = {
    "e.g.": "for example", "i.e.": "that is",
    "a.m.": "AM", "p.m.": "PM",
    "&": " and ", "%": " percent ", "=": " equals ",
    "<": " less than ", ">": " greater than ",
}
# Characters an LLM emits that a TTS engine either skips or mispronounces.
TYPOGRAPHY = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "–": "-",      # en dash: keep it a hyphen so ranges still parse
    "—": ", ",     # em dash: a spoken comma pause
    "―": ", ", "−": "-", "…": "...",
    " ": " ", " ": " ", " ": " ", "​": "", "­": "",
    "•": " ", "●": " ", "·": " ",
}

# Plural by default; a quantity of exactly one is singularised at the point
# where it is used.
UNITS = {
    "kg": "kilograms", "mg": "milligrams", "mcg": "micrograms",
    "lbs": "pounds", "lb": "pounds", "oz": "ounces",
    "km": "kilometers", "cm": "centimeters", "mm": "millimeters",
    "mi": "miles", "ft": "feet", "yd": "yards",
    "hrs": "hours", "hr": "hours", "mins": "minutes", "min": "minutes",
    "secs": "seconds", "sec": "seconds", "ms": "milliseconds",
    "yrs": "years", "yr": "years", "wks": "weeks", "wk": "weeks",
    "kb": "kilobytes", "mb": "megabytes", "gb": "gigabytes",
    "tb": "terabytes", "px": "pixels",
    "tsp": "teaspoons", "tbsp": "tablespoons", "ml": "milliliters",
    "gal": "gallons", "kcal": "calories", "cal": "calories",
    "mph": "miles per hour", "kph": "kilometers per hour",
    "kmh": "kilometers per hour",
    "hz": "hertz", "khz": "kilohertz", "mhz": "megahertz",
    "ghz": "gigahertz", "kw": "kilowatts", "mw": "megawatts",
}
# Units whose singular is not simply the plural without its "s".
_IRREGULAR_SINGULARS = {"feet": "foot", "inches": "inch",
                        "calories": "calorie"}
# Longest first, or "min" shadows "mins" and leaves an "s" to be spoken.
_UNIT_RE = "|".join(sorted(UNITS, key=len, reverse=True))

# Acronyms a TTS engine already says correctly as a word.
PRONOUNCEABLE = {"NASA", "RADAR", "LASER", "SCUBA", "JSON", "YAML", "SOAP",
                 "REST", "SIP", "RAM", "ROM", "AIDS", "OPEC", "NATO", "SIM"}
# Bare domains an LLM drops into prose: "see acme.io/docs". Lower case only, so
# a missing space after a full stop ("data.Org policy") is not read as one.
TLDS = ("com", "org", "net", "io", "ai", "dev", "app", "co", "edu", "gov")

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U0000FE00-\U0000FE0F\U00002B00-\U00002BFF]+")


def _say_number(raw):
    """'1,234.5' -> 'one thousand two hundred thirty-four point five'"""
    raw = raw.replace(",", "")
    if "." in raw:
        whole, _, frac = raw.partition(".")
        return decimal_to_words(whole, frac)
    # A leading zero means the digits are an identifier rather than a quantity:
    # a PIN, a room, an order number. "0042" is read out, not counted.
    if len(raw) > 1 and raw[0] == "0":
        return digits_to_words(raw)
    return int_to_words(int(raw))


_FRACTIONS = {
    (1, 2): "one half", (1, 3): "one third", (2, 3): "two thirds",
    (1, 4): "one quarter", (3, 4): "three quarters", (1, 5): "one fifth",
    (1, 8): "one eighth", (3, 8): "three eighths", (5, 8): "five eighths",
}
# A denominator a real fraction actually uses. Anything else shaped like "a/b"
# with a plausible month and day is a date - "12/25" is Christmas, not twelve
# twenty-fifths.
_FRACTION_DENOMINATORS = {2, 3, 4, 5, 6, 8, 10, 16, 32, 64}


def _say_fraction(num, den):
    if (num, den) in _FRACTIONS:
        return _FRACTIONS[(num, den)]
    return "%s over %s" % (int_to_words(num), int_to_words(den))


def _is_fraction(num, den):
    return num < den and den in _FRACTION_DENOMINATORS


def _singular(unit):
    """'kilograms' -> 'kilogram', 'miles per hour' -> 'mile per hour'"""
    head, sep, tail = unit.partition(" ")
    head = _IRREGULAR_SINGULARS.get(head,
                                    head[:-1] if head.endswith("s") else head)
    return head + sep + tail


def _say_quantity(raw, unit):
    """Pair a number with its unit, singular when there is exactly one."""
    word = unit if raw.replace(",", "") != "1" else _singular(unit)
    return "%s %s" % (_say_number(raw), word)


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


def _say_minor(minor, cents):
    if minor == "penny":
        word = "penny" if cents == 1 else "pence"
    elif minor == "paisa":
        word = "paisa" if cents == 1 else "paise"
    else:
        word = minor if cents == 1 else minor + "s"
    return "%s %s" % (int_to_words(cents), word)


def _say_amount(major, minor, whole, frac):
    amount = int(whole.replace(",", ""))
    cents = int(frac.ljust(2, "0")[:2]) if frac else 0
    # Under a unit, only the minor part is spoken: "$0.99" is ninety-nine
    # cents, never "zero dollars and ninety-nine cents".
    if amount == 0 and cents:
        return _say_minor(minor, cents)
    out = "%s %s%s" % (int_to_words(amount), major,
                       "" if amount == 1 else "s")
    if cents:
        out += " and " + _say_minor(minor, cents)
    return out


def _say_money(symbol, whole, frac):
    major, minor = CURRENCIES[symbol]
    return _say_amount(major, minor, whole, frac)


def _say_big_money(symbol, amount, suffix):
    """'$1.5M' -> 'one point five million dollars'"""
    major = CURRENCIES[symbol][0]
    return "%s %s %ss" % (_say_number(amount), MAGNITUDES[suffix.lower()],
                          major)


def _say_code_amount(code, raw):
    major, minor = CURRENCY_CODES[code.upper()]
    whole, _, frac = raw.partition(".")
    return _say_amount(major, minor, whole, frac)


def _say_month_day(m, d):
    return "%s %s" % (MONTHS[m - 1], ordinal_to_words(d))


def _say_date(y, m, d):
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return ""
    return "%s, %s" % (_say_month_day(m, d), year_to_words(y))


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


# The text stopping here, or a capitalised word following, means the period was
# doing double duty as a full stop; without keeping it the two sentences run
# together.
_ENDS_SENTENCE = r"(?=\s+[A-Z]|\s*$)"
# An initialism is usually followed by a capitalised noun it belongs to ("U.S.
# Department"), so only the end of a line is evidence that it ended a sentence.
_ENDS_LINE = r"(?=[ \t]*$)"


def _expand(t, pattern, replace, ends=_ENDS_SENTENCE):
    """Expand an abbreviation, keeping a full stop that ends a sentence."""
    if ends:
        t = re.sub(pattern + ends, lambda m: replace(m) + ".", t,
                   flags=re.M)
    return re.sub(pattern, replace, t)


def _slash_pair(m):
    """A slash between two numbers: a date, a fraction, or the 24/7 idiom."""
    a, b = int(m.group(1)), int(m.group(2))
    if (a, b) == (24, 7):
        return "twenty four seven"
    if _is_fraction(a, b):
        return m.group(0)                      # left for the fraction rule
    if 1 <= a <= 12 and 1 <= b <= 31:
        return _say_month_day(a, b)
    return m.group(0)


def normalize(text, spell_acronyms=False, strip_emoji=True):
    """Rewrite `text` so a TTS engine speaks it the way a human would."""
    if not text:
        return ""
    t = _strip_markdown(text)
    if strip_emoji:
        t = _EMOJI.sub(" ", t)
    # Before any rule that looks for a hyphen or a quote.
    for src, dst in TYPOGRAPHY.items():
        t = t.replace(src, dst)

    # Emails and URLs first, before anything else touches the dots.
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
               lambda m: m.group(0).replace("@", " at ").replace(".", " dot "),
               t)
    t = re.sub(r"https?://\S+|\bwww\.\S+",
               lambda m: re.sub(r"/\S*$", "",
                                re.sub(r"https?://|www\.", "", m.group(0)))
               .replace(".", " dot "), t)
    # A bare domain with no scheme. Its path is dropped, as a URL's path is.
    t = re.sub(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*)\.(" + "|".join(TLDS)
               + r")\b(?:/\S*)?",
               lambda m: (m.group(1) + " dot " + m.group(2))
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
    # A score out of a total, before either slash rule claims the pair.
    t = re.sub(r"(?<![\d.])(\d+\.\d+)\s?/\s?(\d+)\b",
               lambda m: _say_number(m.group(1)) + " out of "
               + _say_number(m.group(2)), t)
    # A yearless "11/25", and the 24/7 idiom, before the fraction rule sees it.
    # The lookbehind keeps a decimal out of it: the "5/5" inside "4.5/5" is
    # not a date.
    t = re.sub(r"(?<![\d.])(\d{1,2})/(\d{1,2})(?![\d/])", _slash_pair, t)

    # Note: the meridiem deliberately does not absorb a trailing dot, so that
    # "at 3:30 PM." keeps the sentence-ending period.
    t = re.sub(r"\b(\d{1,2}):(\d{2})(?:\s*([ap]\.?m))?",
               lambda m: _say_time(int(m.group(1)), int(m.group(2)),
                                   m.group(3) or "") or m.group(0),
               t, flags=re.I)
    # Whatever colon-separated pair is left is a ratio or a score, not a time.
    t = re.sub(r"\b(\d{1,3}):(\d{1,3})\b",
               lambda m: "%s to %s" % (int_to_words(int(m.group(1))),
                                       int_to_words(int(m.group(2)))), t)

    def _phone(m):
        raw = m.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if not 7 <= len(digits) <= 15:
            return m.group(0)
        # A digit run alone is not a phone number - "1000-2000" is a range.
        # Require real phone shape: a country code, parens, two or more
        # separators, an unbroken run long enough to be a full number, or the
        # classic seven-digit local form "555-0100".
        seps = len(re.findall(r"[\s\-.]", raw))
        if not (raw.startswith("+") or "(" in raw or seps >= 2
                or (seps == 0 and len(digits) >= 10)
                or re.match(r"^\d{3}[-.\s]\d{4}$", raw)):
            return m.group(0)
        return digits_to_words(raw)

    # The leading paren must be inside the match, or "(555) 123-4567" leaves a
    # stray "(" behind once the digits are rewritten.
    t = re.sub(r"(?<![\w$.])\+?\(?\d[\d\-.\s()]{6,18}\d\)?(?![\w])", _phone, t)
    # An extension trails the number it belongs to, so it is read the same way.
    # A bare "x" has to be joined to its digits ("x204"): a spaced "x" is a
    # multiplication sign, as in "B12 x 3".
    t = re.sub(r"(?<!\w)(?:ext\.?|extension)\s?(\d{1,6})\b",
               lambda m: "extension " + digits_to_words(m.group(1)), t)
    t = re.sub(r"(?<!\w)x(\d{2,6})\b",
               lambda m: "extension " + digits_to_words(m.group(1)), t)

    t = re.sub(r"#(?=\d)", "number ", t)
    t = re.sub(r"\b[Nn]o\.\s*(?=\d)", "number ", t)

    # Ranges, now that whatever is left is not a phone number. A pair of years
    # is spoken as years, not counted: "the 2026-2027 season".
    t = re.sub(r"\b((?:19|20)\d{2})\s?-\s?((?:19|20)\d{2})\b",
               lambda m: year_to_words(int(m.group(1))) + " to "
               + year_to_words(int(m.group(2))), t)
    # A percent on both ends is a range too. Without this the hyphen falls
    # through to the negative-sign rule below and is spoken as "negative".
    t = re.sub(r"(\d[\d,]*(?:\.\d+)?)\s?%\s?-\s?(\d[\d,]*(?:\.\d+)?)\s?%",
               lambda m: _say_number(m.group(1)) + " percent to "
               + _say_number(m.group(2)) + " percent", t)
    t = re.sub(r"\b(\d[\d,]*)\s?-\s?(\d[\d,]*)\b",
               lambda m: _say_number(m.group(1)) + " to "
               + _say_number(m.group(2)), t)
    # A bare leading minus is spoken, not silent. Must follow the range rule,
    # whose hyphen is preceded by a digit and so is unaffected.
    t = re.sub(r"(?<![\w\d%])-\s?(?=\d)", "negative ", t)

    # The unit is absorbed here: once the fraction becomes words, the unit rule
    # below can no longer see a quantity in front of it ("3/4 kg"). A fraction
    # takes a plural unit - "three quarters kilograms".
    t = re.sub(r"\b(\d+)/(\d+)(?:\s?(" + _UNIT_RE + r")\b)?",
               lambda m: _say_fraction(int(m.group(1)), int(m.group(2)))
               + (" " + UNITS[m.group(3).lower()] if m.group(3) else ""),
               t, flags=re.I)

    sym = "|".join(re.escape(s) for s in CURRENCIES)
    # A hyphen between two sums is a range: "$5M-$10M". Both ends still carry
    # their symbol, so this runs before either is turned into words.
    t = re.sub(r"((?:" + sym + r")\s?\d[\d,]*(?:\.\d+)?\s?"
               r"(?:bn|mn|tn|[KMBT])?)\s?-\s?(?=(?:" + sym + r")\s?\d)",
               lambda m: m.group(1) + " to ", t)
    # "$1.5M" before "$1.5", or the suffix is stranded as a spoken letter.
    t = re.sub("(" + sym + r")\s?(\d[\d,]*(?:\.\d+)?)\s?(bn|mn|tn|[KMBT])\b",
               lambda m: _say_big_money(m.group(1), m.group(2), m.group(3)), t)
    # A cents-only amount written without its leading zero: "$.50".
    t = re.sub("(" + sym + r")\.(\d{1,2})\b",
               lambda m: _say_minor(CURRENCIES[m.group(1)][1],
                                    int(m.group(2).ljust(2, "0")[:2])), t)
    t = re.sub("(" + sym + r")\s?(\d[\d,]*)(?:\.(\d{1,2}))?",
               lambda m: _say_money(m.group(1), m.group(2), m.group(3)), t)
    codes = "|".join(CURRENCY_CODES)
    t = re.sub(r"\b(" + codes + r")\s?(\d[\d,]*(?:\.\d{1,2})?)\b",
               lambda m: _say_code_amount(m.group(1), m.group(2)), t)
    t = re.sub(r"\b(\d[\d,]*(?:\.\d{1,2})?)\s?(" + codes + r")\b",
               lambda m: _say_code_amount(m.group(2), m.group(1)), t)

    t = re.sub(r"(\d[\d,]*(?:\.\d+)?)\s?%",
               lambda m: _say_number(m.group(1)) + " percent", t)
    # Temperatures, before the bare-number rule leaves the degree sign behind.
    t = re.sub(r"(\d[\d,]*(?:\.\d+)?)\s?°\s?([CF])\b",
               lambda m: _say_number(m.group(1)) + " degrees "
               + ("Celsius" if m.group(2).upper() == "C" else "Fahrenheit"), t)
    t = re.sub(r"(\d[\d,]*(?:\.\d+)?)\s?°",
               lambda m: _say_number(m.group(1)) + " degrees", t)
    t = re.sub(r"\b(degrees?)\s+([CF])\b",
               lambda m: m.group(1) + " "
               + ("Celsius" if m.group(2) == "C" else "Fahrenheit"), t)

    t = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b",
               lambda m: ordinal_to_words(int(m.group(1))), t)
    # "1920x1080" is a size; "3x" on its own is a multiplier.
    t = re.sub(r"\b(\d[\d,]*)\s?[xX]\s?(\d[\d,]*)\b",
               lambda m: _say_number(m.group(1)) + " by "
               + _say_number(m.group(2)), t)
    t = re.sub(r"\b(\d[\d,]*)x\b",
               lambda m: _say_number(m.group(1)) + " times", t)
    t = re.sub(r"\b(\d[\d,]*(?:\.\d+)?)\s?(" + _UNIT_RE + r")\b",
               lambda m: _say_quantity(m.group(1), UNITS[m.group(2).lower()]),
               t, flags=re.I)

    for abbr, full in ABBREVIATIONS.items():
        # An abbreviation written lower case is still capitalised at the start
        # of a sentence, and its expansion has to follow suit.
        forms = [abbr] if abbr[0].isupper() else [abbr, abbr.capitalize()]
        pattern = r"\b(" + "|".join(re.escape(f) for f in forms) + r")\."

        def replace(m, full=full):
            return full.capitalize() if m.group(1)[0].isupper() else full

        t = _expand(t, pattern, replace,
                    ends="" if abbr in _NEVER_ENDS_SENTENCE
                    else _ENDS_SENTENCE)
    for src, dst in INITIALISMS.items():
        t = _expand(t, re.escape(src), lambda m, dst=dst: dst, ends=_ENDS_LINE)
    t = _expand(t, r"\b(" + "|".join(DAYS) + r")\.",
                lambda m: DAYS[m.group(1)])
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
    t = re.sub(r",\s*,", ",", t)
    return re.sub(r"\n{2,}", "\n", t).strip()
