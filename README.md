# Speakable

**Text normalization for voice agents.** Turn LLM output into text a TTS engine
speaks correctly.

Your LLM returns this:

```
**Invoice #42**: $1,234.56 due 2026-11-11. Call Dr. Rao at (555) 123-4567
before 3:30 PM. Save 15%! 🎉
```

Your TTS engine says *"asterisk asterisk invoice hash forty two asterisk
asterisk colon dollar one comma two three four point five six..."*

Speakable returns this:

```
Invoice number forty-two: one thousand two hundred thirty-four dollars and
fifty-six cents due November eleventh, twenty twenty-six. Call Doctor Rao at
five five five one two three four five six seven before three thirty PM.
Save fifteen percent!
```

Pure Python, zero dependencies in the core, ~1.5 ms for a typical utterance.

## Install

```bash
pip install speakable
```

```python
from speakable import normalize

normalize("Pay $20 by 2026-01-05.")
# 'Pay twenty dollars by January fifth, twenty twenty-six.'
```

It is a plain string-to-string function with no runtime dependencies, so there
is nothing to wire up and nothing to configure. Call it on the text you are
about to speak, whatever TTS engine or framework you are speaking it with:

```python
text = normalize(llm_output)   # then hand `text` to your TTS engine
```

[On PyPI](https://pypi.org/project/speakable/) &middot; Python 3.9+ &middot; MIT.

## Try it without installing anything

**https://divyajeet01.github.io/speakable/** - paste your own text and watch it
get fixed. The whole library is compiled into the page, so nothing you paste
leaves your browser.

## What it handles

| Input | Output |
|---|---|
| `**bold**`, `# headings`, `` `code` ``, `[link](url)` | stripped to plain text |
| `$1,234.56` / `₹500` / `£20` / `€99` | `one thousand two hundred thirty-four dollars and fifty-six cents` |
| `2026-11-11`, `11/11/2026`, `Nov 11, 2026` | `November eleventh, twenty twenty-six` |
| `3:30 PM`, `9:05 a.m.`, `14:00` | `three thirty PM`, `nine oh five AM`, `two o'clock PM` |
| `(555) 123-4567`, `+1 555-123-4567` | digit-by-digit, the way a human reads a number aloud |
| `15%`, `2.5%` | `fifteen percent`, `two point five percent` |
| `1st`, `21st`, `3rd` | `first`, `twenty-first`, `third` |
| `5kg`, `10mi`, `3hrs` | `five kilograms`, `ten miles`, `three hours` |
| `Dr.`, `Inc.`, `vs.`, `etc.` | `Doctor`, `Incorporated`, `versus`, `et cetera` |
| `john@example.com`, `https://acme.io/help` | `john at example dot com`, `acme dot io` |
| 🎉 and friends | removed |
| `API` (opt-in) | `A P I`, skipping acronyms TTS already says right |
| `10-20`, `1000-2000` | `ten to twenty` (ranges, not phone numbers) |
| `-45` | `negative forty-five` |
| `192.168.1.1`, `v1.2.3` | `one hundred ninety-two dot ...`, `one point two point three` |
| `**unclosed bold` | unpaired markers dropped, not spoken |
| `3/4`, `5/16` | `three quarters`, `five over sixteen` |
| `1 kg`, `2 kg` | `one kilogram`, `two kilograms` (singular when there is one) |
| `$1.5M`, `$2B`, `$5M-$10M` | `one point five million dollars`, `… to …` |
| `$.50`, `$0.99` | `fifty cents`, `ninety-nine cents` |
| `USD 50`, `40 EUR` | `fifty US dollars`, `forty euros` |
| `10%-20%` | `ten percent to twenty percent` |
| `24/7`, `12/25`, `4.5/5` | `twenty four seven`, `December twenty-fifth`, `four point five out of five` |
| `3:1`, `2:0` | `three to one`, `two to zero` (ratios and scores) |
| `555-0100`, `x204` | `five five five zero one zero zero`, `extension two zero four` |
| `0042`, `00123` | read out digit by digit — a PIN is not a quantity |
| `20°C`, `72°F`, `90°` | `twenty degrees Celsius`, `… Fahrenheit`, `ninety degrees` |
| `2026-2027` | `twenty twenty-six to twenty twenty-seven` (years, not a count) |
| `3x`, `2x4` | `three times`, `two by four` |
| `U.S.`, `Ph.D.`, `Mon.` | `U S`, `P H D`, `Monday` |
| `—`, `–`, `…`, `“ ”`, `•` | em dash to a comma pause; the rest normalised or dropped |
| `acme.io/docs` | `acme dot io` |

## The whole API

```python
normalize(text, spell_acronyms=False, strip_emoji=True) -> str
```

That is all of it — one function, two options.

```python
normalize("The API is up", spell_acronyms=True)
# 'The A P I is up'   (acronyms TTS already says right are left alone)

normalize("Ready 🚀 to go", strip_emoji=False)
# 'Ready 🚀 to go'     (keep them if your engine handles them)
```

It is idempotent — running it twice changes nothing, so it is safe to call on
text that may already have been through it.

## Where it goes in a voice pipeline

One line, between the model and the microphone:

```
LLM  ->  normalize()  ->  TTS  ->  caller
```

```python
from speakable import normalize

async def on_llm_response(text: str):
    await speak(normalize(text))
```

Nothing above is framework-specific. `normalize()` takes a string and returns a
string, so it drops into any agent loop, any streaming callback, or any batch
job that writes text a machine will read aloud.

## HTTP API

```bash
pip install -r requirements.txt
uvicorn app:app --reload          # docs at http://127.0.0.1:8000/docs
```

```bash
curl -X POST http://127.0.0.1:8000/normalize \
  -H 'Content-Type: application/json' \
  -d '{"text": "Pay $20 by 2026-01-05."}'
```

```json
{
  "text": "Pay twenty dollars by January fifth, twenty twenty-six.",
  "original": "Pay $20 by 2026-01-05.",
  "chars_in": 22,
  "chars_out": 54,
  "took_ms": 0.9
}
```

`POST /normalize/batch` takes `{"texts": [...]}` for up to 100 strings at once.
`GET /health` for liveness.

Set `RAPIDAPI_PROXY_SECRET` to reject any traffic that didn't come through the
marketplace proxy. `MAX_CHARS` and `MAX_BATCH` bound request size.

## Docker

```bash
docker build -t speakable .
docker run -p 8000:8000 speakable
```

## Tests

```bash
python tests/test_normalize.py     # 91 cases, no pytest required
python tests/test_parity.py        # the web page vs the library (needs node)
```

`test_parity.py` lifts the engine out of `docs/index.html` and runs it over
every case in the suite, so the browser tool and `pip install speakable` cannot
drift apart unnoticed. It reports as skipped when node is not installed.

## Why this exists

Every voice agent hits this. The LLM is trained on written English and emits
markdown, digits and abbreviations; TTS engines are built for prose. The gap
between them is where callers hear "asterisk" out loud. Most teams end up with
a pile of ad-hoc regexes that handle their own demo and break on the next one.

This is that pile, written once, tested, and ordered correctly — the ordering
is most of the difficulty. Dates have to run before phone numbers, because
`2026-11-11` is also digits-and-hyphens. Emails have to run before anything
touches a dot. Currency has to run before plain integers.

## Not handled (yet)

Non-English locales, lakh/crore wording (`₹1,50,000` reads as "one hundred
fifty thousand rupees", not "one lakh fifty thousand"), roman numerals,
mathematical expressions, vanity numbers (`1-800-FLOWERS`), and bare
temperature letters (`72F` without a degree sign, which is as likely to be a
seat as a temperature). PRs welcome.

Two deliberate choices worth knowing about:

- **An ambiguous `a/b` is read as a fraction when the denominator is one a real
  fraction uses** (`1/2`, `3/4`, `5/16`), and as a date otherwise (`12/25`,
  `11/11`, `9/11`). `3/10` stays a fraction; there is no way to tell it from
  March 10th without context.
- **A fraction takes a plural unit** — `3/4 kg` is "three quarters kilograms",
  not "three quarters of a kilogram".

## Changelog

### 1.2.0

Twelve bugs where a voice agent said the wrong thing, plus the coverage gaps
that turned up alongside them. Every fix is mirrored in the browser engine and
checked by `tests/test_parity.py`.

**Fixed**

- **A quantity of one takes a singular unit.** `1 kg` was "one kilograms";
  it is now "one kilogram". (The item left open in 1.1.0.)
- **A magnitude suffix belongs to the amount.** `$1.5M` was "one dollar and
  fifty cents**M**"; it is now "one point five million dollars".
- **A percent range is a range.** `10%-20%` was "ten percent**negative**
  twenty percent" — the hyphen fell through to the negative-number rule.
- **A seven-digit local number is a phone number.** `555-0100` was read as the
  range "five hundred fifty-five to one hundred".
- **A leading zero marks an identifier.** `0042` was "forty-two"; a PIN, room
  or order number is now read out digit by digit.
- **`$.50` and `$0.99`** were "dollar sign point fifty" and "zero dollars and
  ninety-nine cents"; both now read as cents.
- **An abbreviation capitalised at the start of a sentence expands.**
  `Approx. 40` kept its "Approx." - the lookup was case-sensitive.
- **A leftover colon pair is a ratio.** `3:1` kept the colon, which TTS read
  aloud; it is now "three to one".
- **`24/7`** was "twenty-four over seven".
- **A yearless `11/25`** was "eleven over twenty-five" instead of a date.
- **A pair of years** reads as years: `2026-2027` was "two thousand twenty-six
  to two thousand twenty-seven".
- **`4.5/5`** was "four.May fifth" - the slash rule matched inside a decimal.

**Added**

- Temperatures (`20°C`, `72°F`, `90°`, `350 degrees F`)
- Currency codes (`USD 50`, `40 EUR`) and currency ranges (`$5M-$10M`)
- Scores out of a total (`4.5/5`), multipliers (`3x`) and sizes (`2x4`)
- Phone extensions (`x204`, `ext. 204`) and `No. 7`
- Dotted initialisms (`U.S.`, `Ph.D.`), weekday abbreviations (`Mon.`)
- Typography an LLM emits: em and en dashes, curly quotes, ellipsis, bullets
- Bare domains without a scheme (`acme.io/docs`)
- 25 more units (`min`, `tsp`, `tbsp`, `ml`, `gal`, `mph`, `ghz`, `px`, …),
  matched case-insensitively and longest-first

**Also**

- `tests/test_parity.py` diffs the browser engine against the library on every
  case, so the page and the package cannot drift apart silently
- The idempotency test now covers every case, not one
- `app.py` no longer uses `list[str]`, which broke the API on Python 3.9 —
  the floor the package claims to support
- CI runs the suite on Python 3.9 through 3.13

### 1.1.0

- **Sentence-ending abbreviations keep their full stop.** `"42 Oak St. Co-pay
  is due."` now reads as `"forty-two Oak Street. Co-pay is due."` instead of
  running the two sentences together. Abbreviations that introduce a name
  (`Dr.`, `Mr.`, `Prof.`) or join clauses (`vs.`) still always absorb the stop,
  so `"Call Dr. Rao"` is unchanged.
- **Units after a fraction expand.** `"3/4 kg"` now reads as `"three quarters
  kilograms"`. A following word that is not a unit is left alone, so
  `"3/4 cup"` is still `"three quarters cup"`.
- Added a browser build of the engine under `docs/`, diffed against the Python
  library on every test case.

### 1.0.0

Initial release.

## License

MIT.
