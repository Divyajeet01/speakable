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

    # --- 1.2.0 ---
    # A quantity of exactly one takes a singular unit.
    ("The box weighs 1 kg.", "The box weighs one kilogram."),
    ("It took 1 hr and 2 hrs.", "It took one hour and two hours."),
    ("1 ft and 2 ft long.", "one foot and two feet long."),
    ("1 mph wind.", "one mile per hour wind."),
    # ...but a fraction of one does not.
    ("Add 1/2 tsp salt.", "Add one half teaspoons salt."),
    # A magnitude suffix belongs to the amount, not to the next word.
    ("Revenue hit $1.5M last year.",
     "Revenue hit one point five million dollars last year."),
    ("A $2B round closed.", "A two billion dollars round closed."),
    ("Budget is $5M-$10M range.",
     "Budget is five million dollars to ten million dollars range."),
    # Under a unit, only the minor part is spoken.
    ("Just $.50 more.", "Just fifty cents more."),
    ("Cost: $0.99 only.", "Cost: ninety-nine cents only."),
    ("He owes $1.", "He owes one dollar."),
    # An ISO code reads as the currency it names.
    ("Pay USD 50 or EUR 40.", "Pay fifty US dollars or forty euros."),
    ("USD 1 only.", "one US dollar only."),
    # A percent on both ends of a hyphen is a range, not a negative number.
    ("Save 10%-20% today.", "Save ten percent to twenty percent today."),
    ("Discount is -5% this week.",
     "Discount is negative five percent this week."),
    # A slash: an idiom, a date, a fraction, or a score out of a total.
    ("We are open 24/7 for support.",
     "We are open twenty four seven for support."),
    ("Delivery on 12/25 confirmed.",
     "Delivery on December twenty-fifth confirmed."),
    ("On 11/11 we launch.", "On November eleventh we launch."),
    ("Rated 4.5/5 overall.", "Rated four point five out of five overall."),
    ("Use a 5/8 inch bolt.", "Use a five eighths inch bolt."),
    # A colon pair the clock rule rejected is a ratio or a score.
    ("The ratio is 3:1 overall.", "The ratio is three to one overall."),
    ("Score was 2:0 at halftime.", "Score was two to zero at halftime."),
    ("Meet at 10:30 tomorrow.", "Meet at ten thirty tomorrow."),
    # The classic seven-digit local number, and an extension.
    ("Call 555-0100 now.", "Call five five five zero one zero zero now."),
    ("Call 555-0100 x204 now.",
     "Call five five five zero one zero zero extension two zero four now."),
    ("Call ext. 204 please.", "Call extension two zero four please."),
    # A spaced "x" is a multiplication sign, not an extension.
    ("Vitamin B12 x 3 daily.", "Vitamin B12 x three daily."),
    # A leading zero marks an identifier, which is read out digit by digit.
    ("Your PIN is 0042.", "Your PIN is zero zero four two."),
    ("Order 00123 shipped.", "Order zero zero one two three shipped."),
    ("Room 101 is ready.", "Room one hundred one is ready."),
    # An abbreviation capitalised at the start of a sentence still expands.
    ("Approx. 40 people came.", "Approximately forty people came."),
    ("No. 7 is missing.", "number seven is missing."),
    # Temperatures.
    ("It is 20°C today.", "It is twenty degrees Celsius today."),
    ("It is 72°F today.", "It is seventy-two degrees Fahrenheit today."),
    ("Turn 90° left.", "Turn ninety degrees left."),
    ("Set the oven to 350 degrees F.",
     "Set the oven to three hundred fifty degrees Fahrenheit."),
    # A pair of years is spoken as years, not counted.
    ("The 2026-2027 season starts.",
     "The twenty twenty-six to twenty twenty-seven season starts."),
    ("The 1990-1995 period was odd.",
     "The nineteen ninety to nineteen ninety-five period was odd."),
    # ...but a pair of plain numbers is still a range.
    ("Lines 1,000-2,000 failed.",
     "Lines one thousand to two thousand failed."),
    ("ETA is 10 min.", "ETA is ten minutes."),
    ("Latency was 250 ms flat.", "Latency was two hundred fifty "
     "milliseconds flat."),
    # A multiplier and a size.
    ("A 3x increase happened.", "A three times increase happened."),
    ("A 2x4 board.", "A two by four board."),
    # A dotted initialism is spelled out, so TTS does not say the word "us".
    # The full stop survives only at the end of a line - "U.S. Department" is
    # one phrase, not two sentences.
    ("The U.S. Department opened.", "The U S Department opened."),
    ("We ship to the U.K.", "We ship to the U K."),
    ("Ph.D. candidates only.", "P H D candidates only."),
    # A weekday abbreviation, which can end a sentence.
    ("Mon. is a holiday.", "Monday is a holiday."),
    ("Sat. delivery is extra.", "Saturday delivery is extra."),
    # Typography an LLM emits that TTS skips or mispronounces.
    ("Wait — I think so.", "Wait, I think so."),
    ("Takes 20–30 minutes.", "Takes twenty to thirty minutes."),
    ("She said ‘ok’ then left.", "She said 'ok' then left."),
    ("Bullet • point here.", "Bullet point here."),
    # A bare domain, with its path dropped as a URL's is.
    ("Visit example.com/docs today.", "Visit example dot com today."),
    # ...but an ordinary full stop before a capital is not a domain, and a
    # suffix that is not a TLD is left alone.
    ("I will check the data. Org policy says no.",
     "I will check the data. Org policy says no."),
    ("The file app.js is broken.", "The file app.js is broken."),
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
    """Normalized text is already spoken form, so a second pass is a no-op.

    Agents re-run this on text that has been through it before; a rule that
    keeps firing would garble the output a little more on every pass.
    """
    unstable = []
    for src, _ in CASES:
        once = normalize(src)
        if normalize(once) != once:
            unstable.append((src, once, normalize(once)))
    for src, once, twice in unstable:
        print("INPUT: %r" % src)
        print("ONCE:  %r" % once)
        print("TWICE: %r" % twice)
        print()
    assert not unstable, "%d/%d outputs changed on a second pass" % (
        len(unstable), len(CASES))


if __name__ == "__main__":
    test_cases()
    test_acronyms()
    test_idempotent()
    print("all %d cases pass" % len(CASES))
