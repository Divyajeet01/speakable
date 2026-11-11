# Why your voice agent says "asterisk asterisk"

You build a voice agent. The LLM is sharp, the TTS voice is warm, the latency is
good. You put it on a real phone number and call it.

And it says:

> "asterisk asterisk invoice hash forty two asterisk asterisk colon dollar one
> comma two three four point five six due two zero two six dash one one dash
> one one"

What the LLM actually returned was perfectly reasonable:

```
**Invoice #42**: $1,234.56 due 2026-11-11.
```

The LLM did nothing wrong. The TTS engine did nothing wrong. The bug is in the
gap between them, and almost nobody budgets for it.

## Why this happens

LLMs are trained overwhelmingly on written English — documentation, Markdown,
code, articles. So they emit written English: `**bold**`, `$1,234.56`, `Dr.`,
`2026-11-11`, bullet lists, emoji.

TTS engines expect prose. Good ones handle a few of these. None handle all of
them, and which ones they handle is undocumented and changes between providers
and between versions of the same provider. Switch your TTS vendor and a
different subset of your text starts being mispronounced.

So the normalization has to happen in your code, before synthesis.

## The fix everyone writes first

```python
text = text.replace("*", "").replace("#", "")
```

This gets you through the demo. Then:

- `$1,234.56` is still read as digits
- `(555) 123-4567` is read as "five hundred fifty-five, one hundred twenty-three..."
  instead of digit-by-digit, which is how humans read phone numbers aloud
- `Dr. Rao` becomes "dee are rao"
- `2026-11-11` becomes "two zero two six dash one one dash one one"
- `3:30 PM` is fine, but `14:00` becomes "fourteen o'clock"

So you add regexes. One per symptom, in the order you discovered them. And that
is where it gets genuinely tricky.

## The part that's actually hard: ordering

These rules are not independent. They fight each other, and the order you apply
them in determines whether the output is right.

**Dates must run before phone numbers.** A phone-number matcher looks for runs
of digits, hyphens and spaces. So does `2026-11-11`. If phones run first, your
date is read out as a phone number.

**Emails and URLs must run before anything that touches a dot.** Once an
abbreviation rule has rewritten the `.` in `john.doe@example.com`, you can't
recover the address.

**Currency must run before plain integers.** If a generic number rule reaches
`$1,234.56` first, you get "one thousand two hundred thirty-four point five six"
with the dollars silently dropped — the worst kind of bug, because it sounds
fluent and is wrong.

**Markdown stripping must run first of all**, or `**$5**` never matches your
currency pattern because of the asterisks glued to it.

Here's a concrete one that cost me an afternoon. This looks fine:

```python
re.sub(r"\b(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)?", say_time, text)
```

Given `"Call at 3:30 PM."` it produces `"Call at three thirty PM"` — note the
missing full stop. The optional meridiem group happily absorbed the
sentence-ending period as part of `PM.`. The fix is to not let it:

```python
re.sub(r"\b(\d{1,2}):(\d{2})(?:\s*([ap]\.?m))?", say_time, text)
```

And the same pattern has a second bug: with `\s*` outside the optional group,
`"Departs at 14:00 sharp"` becomes `"...two o'clock PMsharp"`, because the
whitespace was consumed even when no meridiem was found. Both of these produce
output that *looks* right in a unit test you wrote carelessly, and sounds
obviously broken on a phone call.

Phone numbers have a similar trap. This pattern:

```python
r"(?<![\w$.])\+?\d[\d\-.\s()]{6,18}\d(?![\w])"
```

starts matching at the first *digit*, so `(555) 123-4567` leaves a dangling `(`
in your output. The opening paren has to be inside the match.

And one more that only shows up in production. If you stream tokens, or the
model hits its output limit mid-sentence, you get *unpaired* markers:

```
**Your total is
```

Every emphasis regex is written to match pairs, so an unclosed `**` matches
nothing and sails straight through to the synthesizer. Your carefully tested
markdown stripper produces "asterisk asterisk your total is" on exactly the
responses that were already degraded. Strip any marker that survives the
pairing rules.

## Reading numbers the way people do

Not every number is read the same way, and the difference is not cosmetic:

| Context | `4567` is read as |
|---|---|
| Quantity | "four thousand five hundred sixty-seven" |
| Phone number | "four five six seven" |
| Year | "forty-five sixty-seven" |
| PIN or code | "four five six seven" |

Years have their own rules that no general number function gets right: `2026` is
"twenty twenty-six", `2005` is "two thousand five", and `1905` is "nineteen oh
five". Three different forms, no clean rule — you special-case them or you sound
like a robot.

## So I packaged it

I kept rewriting this layer, so I wrote it once properly:

```bash
pip install speakable
```

```python
from speakable import normalize

normalize("**Invoice #42**: $1,234.56 due 2026-11-11.")
# 'Invoice number forty-two: one thousand two hundred thirty-four dollars
#  and fifty-six cents due November eleventh, twenty twenty-six.'
```

In a LiveKit agent it's one line, right before synthesis:

```python
await tts.say(normalize(llm_response))
```

It handles markdown and emoji stripping, currency in five denominations, dates
in ISO/US/written forms, 12- and 24-hour times, phone numbers, percentages,
ordinals, units, abbreviations, emails and URLs, and optional acronym spelling.
Zero dependencies in the core, around 1.5 ms per utterance, and idempotent —
running it twice changes nothing.

It does **not** yet handle non-English locales, Indian lakh/crore grouping,
roman numerals, or fractions. If you need those, the issues are open.

MIT licensed. Source: `github.com/Divyajeet01/speakable`

## The takeaway, even if you don't use it

Treat text normalization as a real stage in your pipeline, not a `.replace()`
you bolt on the day before launch. Give it its own module, its own tests, and —
most importantly — a deliberate, documented order. The ordering is the design.

And test it by *listening*, not by reading. Every bug above passes a code review
and fails a phone call.
