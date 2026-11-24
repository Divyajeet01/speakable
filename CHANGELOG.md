# Changelog

All notable changes to [speakable](https://pypi.org/project/speakable/).
Versions follow [semantic versioning](https://semver.org/).

## 1.2.0

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

## 1.1.0

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

## 1.0.0

Initial release.
