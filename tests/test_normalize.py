import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from speakable import normalize  # noqa: E402

CASES = [
    ("**Total: $1,234.56** due on 2026-11-11.",
     "Total: one thousand two hundred thirty-four dollars and fifty-six cents "
     "due on November eleventh, twenty twenty-six."),
    ("Call Dr. Rao at 3:30 PM.", "Call Doctor Rao at three thirty PM."),
    ("Your balance is ₹500.", "Your balance is five hundred rupees."),
    ("The fee is 2.5%.", "The fee is two point five percent."),
    ("Email john.doe@example.com",
     "Email john dot doe at example dot com"),
    ("See https://example.com/pricing now", "See example dot com now"),
    ("## Summary\n- 1st item\n- 5kg total",
     "Summary\nfirst item\nfive kilograms total"),
    ("Meeting on Nov 11, 2026.",
     "Meeting on November eleventh, twenty twenty-six."),
    # "Ltd." ends the sentence, so its full stop has to survive the expansion.
    ("Acme Inc. vs. Beta Ltd.", "Acme Incorporated versus Beta Limited."),
    ("Call +1 555-123-4567 today",
     "Call plus one five five five one two three four five six seven today"),
    ("It costs $1 exactly.", "It costs one dollar exactly."),
    ("Ready \U0001F680 to go", "Ready to go"),
    ("Use `curl` and [the docs](https://x.io).", "Use curl and the docs."),
    ("Call (555) 123-4567 now",
     "Call five five five one two three four five six seven now"),
    ("Invoice #42 is ready.", "Invoice number forty-two is ready."),
    ("Departs at 14:00 sharp", "Departs at two o'clock PM sharp"),
    ("Arrives 00:15", "Arrives twelve fifteen AM"),
    ("**unclosed bold here", "unclosed bold here"),
    ("Server at 192.168.1.1 is down",
     "Server at one hundred ninety-two dot one hundred sixty-eight dot one "
     "dot one is down"),
    ("Upgrade to v1.2.3 today", "Upgrade to one point two point three today"),
    ("Expect 10-20 calls", "Expect ten to twenty calls"),
    ("Lines 1000-2000 failed", "Lines one thousand to two thousand failed"),
    ("Balance -45 dollars", "Balance negative forty-five dollars"),
    ("Call 5551234567 now",
     "Call five five five one two three four five six seven now"),
    ("Add 3/4 cup", "Add three quarters cup"),
    ("Mix 5/16 parts", "Mix five over sixteen parts"),
    ("Issue # filed", "Issue filed"),
    # A sentence-ending abbreviation keeps its full stop, or TTS runs the two
    # sentences together.
    ("We are at 42 Oak St. Co-pay is due.",
     "We are at forty-two Oak Street. Co-pay is due."),
    ("Mail it to the Sales Dept. Thanks.",
     "Mail it to the Sales Department. Thanks."),
    ("Visit 9 Elm Rd.", "Visit nine Elm Road."),
    # ...but one that introduces a name never does, even before a capital.
    ("Call Dr. Rao now.", "Call Doctor Rao now."),
    # A lowercase word after it means mid-sentence, so no full stop is kept.
    ("Acme Corp. vs. Beta Inc. won",
     "Acme Corporation versus Beta Incorporated won"),
    # A unit still expands when the quantity is a fraction.
    ("Add 3/4 kg of flour", "Add three quarters kilograms of flour"),
    ("Use 1/2 mb of cache", "Use one half megabytes of cache"),
    # A non-unit word after a fraction is left alone.
    ("Add 3/4 cup", "Add three quarters cup"),
    ("", ""),
]


def test_cases():
    failures = []
    for src, expected in CASES:
        got = normalize(src)
        if got != expected:
            failures.append((src, expected, got))
    for src, expected, got in failures:
        print("INPUT:    %r" % src)
        print("EXPECTED: %r" % expected)
        print("GOT:      %r" % got)
        print()
    assert not failures, "%d/%d cases failed" % (len(failures), len(CASES))


def test_acronyms():
    assert normalize("The API is up", spell_acronyms=True) == "The A P I is up"
    assert normalize("JSON only", spell_acronyms=True) == "JSON only"


def test_idempotent():
    once = normalize("Pay $20 by 2026-01-05.")
    assert normalize(once) == once


if __name__ == "__main__":
    test_cases()
    test_acronyms()
    test_idempotent()
    print("all %d cases pass" % len(CASES))
