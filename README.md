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

## Library use

```python
from speakable import normalize

normalize("Pay $20 by 2026-01-05.")
# 'Pay twenty dollars by January fifth, twenty twenty-six.'

normalize("The API is up", spell_acronyms=True)
# 'The A P I is up'
```

`normalize(text, spell_acronyms=False, strip_emoji=True)` is the whole API.
It is idempotent — running it twice changes nothing.

## Use it in a LiveKit agent

The one line that matters, right before synthesis:

```python
from speakable import normalize

async def on_llm_response(text: str):
    await tts.say(normalize(text))
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
python tests/test_normalize.py     # 28 cases, no pytest required
```

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

Non-English locales, Indian digit grouping (lakh/crore), roman numerals, and
mathematical expressions. PRs welcome.

## Changelog

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
