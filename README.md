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

[On PyPI](https://pypi.org/project/speakable/) &middot; Python 3.9+ &middot; zero
dependencies &middot; MIT.

## Try it without installing anything

**https://divyajeet01.github.io/speakable/** - paste your own text and watch it
get fixed. The whole library is compiled into the page, so nothing you paste
leaves your browser.

## What it handles

| Input | Output |
|---|---|
| `**bold**`, `# heading`, `` `code` ``, `[link](url)`, `**unclosed` | stripped to plain text |
| `$1,234.56` &middot; `$1.5M` &middot; `$.50` &middot; `USD 50` &middot; `₹500` | `one thousand two hundred thirty-four dollars and fifty-six cents`, `one point five million dollars`, `fifty cents`, `fifty US dollars` |
| `2026-11-11`, `Nov 11, 2026`, `12/25` | `November eleventh, twenty twenty-six`, `December twenty-fifth` |
| `3:30 PM`, `14:00`, `9:05 a.m.` | `three thirty PM`, `two o'clock PM`, `nine oh five AM` |
| `(555) 123-4567`, `555-0100`, `x204` | digit by digit, the way a human reads a number aloud |
| `15%`, `10%-20%` | `fifteen percent`, `ten percent to twenty percent` |
| `1 kg`, `5kg`, `3hrs`, `10 min` | `one kilogram`, `five kilograms`, `three hours`, `ten minutes` — singular when there is one |
| `1st`, `3/4`, `24/7`, `4.5/5`, `3:1` | `first`, `three quarters`, `twenty four seven`, `four point five out of five`, `three to one` |
| `10-20`, `2026-2027`, `-45` | `ten to twenty`, `twenty twenty-six to twenty twenty-seven`, `negative forty-five` |
| `20°C`, `90°`, `3x`, `2x4` | `twenty degrees Celsius`, `ninety degrees`, `three times`, `two by four` |
| `0042`, `00123` | read out digit by digit — a PIN is not a quantity |
| `Dr.`, `Inc.`, `etc.`, `U.S.`, `Ph.D.`, `Mon.` | `Doctor`, `Incorporated`, `et cetera`, `U S`, `P H D`, `Monday` |
| `john@example.com`, `acme.io/docs` | `john at example dot com`, `acme dot io` |
| `192.168.1.1`, `v1.2.3` | read as an address and a version, not a phone number |
| 🎉 &middot; `—` &middot; `“ ”` &middot; `•` | emoji removed; em dash becomes a comma pause; the rest normalised |
| `API` (opt-in) | `A P I`, skipping acronyms TTS already says right |

## The whole API

```python
normalize(text, spell_acronyms=False, strip_emoji=True) -> str
```

One function, two options, and it is idempotent — running it twice changes
nothing, so it is safe on text that may already have been through it.

```python
normalize("The API is up", spell_acronyms=True)   # 'The A P I is up'
normalize("Ready 🚀 to go", strip_emoji=False)     # 'Ready 🚀 to go'
```

A string in, a string out, with no runtime dependencies — so it drops into any
agent loop, streaming callback or batch job, with no framework assumed:

```
LLM  ->  normalize()  ->  TTS  ->  caller
```

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
fifty thousand rupees"), roman numerals, mathematical expressions, vanity
numbers (`1-800-FLOWERS`), and bare temperature letters (`72F` without a degree
sign, as likely to be a seat as a temperature). PRs welcome.

Two deliberate calls: an ambiguous `a/b` is a fraction when the denominator is
one a real fraction uses (`1/2`, `3/4`, `5/16`) and a date otherwise (`12/25`,
`9/11`); and a fraction takes a plural unit, so `3/4 kg` is "three quarters
kilograms".

## Changelog

See [CHANGELOG.md](CHANGELOG.md). The short version of 1.2.0: twelve bugs
where a voice agent said the wrong thing out loud, and the coverage gaps
beside them.

## License

MIT.
