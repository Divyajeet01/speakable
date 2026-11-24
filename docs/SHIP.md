# Shipping the web tool

`index.html` is the whole product. One file, no build step, no dependencies, no
server. Open it locally and it works offline.

**Verified on every push:** `tests/test_parity.py` lifts the JavaScript engine
straight out of this page, runs it over all 91 suite cases plus the acronym and
emoji options, and diffs the output against the Python library - **94/94
identical**. CI fails if they drift. The page is not an approximation of
`speakable`; it is the same behaviour, and that is now checked rather than
claimed.

```bash
python tests/test_parity.py     # needs node; skips without it
```

## Deploy free on GitHub Pages

The page lives at `docs/index.html`, which is exactly what GitHub Pages serves -
there is no build step and no second copy to keep in sync.

On github.com/Divyajeet01/speakable &rarr; **Settings &rarr; Pages** &rarr;
Source: *Deploy from a branch*, Branch: `main`, Folder: `/docs` &rarr; Save.

Live in about a minute at:

**https://divyajeet01.github.io/speakable/**

Then add that URL to the repo's About sidebar and to the PyPI project page.

## Alternatives, if you ever want a custom domain

| Host | Cost | Notes |
|---|---|---|
| GitHub Pages | free | Simplest. Use this. |
| Cloudflare Pages | free | Faster globally, free custom domain, drag-and-drop deploy. |
| Netlify / Vercel | free tier | Fine, but more account surface than this needs. |

A static page has no cold start and no running cost, so none of the
"always-warm" concerns from `micro-api.md` apply here.

## Why this exists

`pip install speakable` only reaches people who already know the library exists.
The web page reaches people **searching the symptom** - "tts reads markdown",
"voice agent says asterisk", "tts reading dollar sign wrong". They arrive, paste
their own broken text, and watch it get fixed with their own data. That is a far
stronger pitch than a README.

The funnel: page &rarr; `pip install` &rarr; (later) the paid API in
`micro-api.md`.

## Changelog

**1.2.0** - twelve bugs fixed and the coverage gaps beside them, all mirrored
here. The full list is in the README. The item left open below is one of them:
`"1 kg"` now reads as `"one kilogram"`. Keeping the two engines in step is no
longer a manual diff - `tests/test_parity.py` does it, and CI runs it.

**1.1.0** - two bugs found while building this page, both fixed in the library
and mirrored here:

1. **A sentence-ending abbreviation no longer loses its full stop.**
   `"42 Oak St. Co-pay is..."` now gives `"forty-two Oak Street. Co-pay is..."`.
   Abbreviations that introduce a name (`Dr.`, `Mr.`, `Prof.`) or join clauses
   (`vs.`) still always absorb the stop, so `"Call Dr. Rao"` is unaffected.
2. **A unit after a fraction now expands.** `"3/4 kg"` gives
   `"three quarters kilograms"` instead of leaving `kg` unspoken.

One existing test expectation was itself encoding bug 1 and was corrected:
`"Acme Inc. vs. Beta Ltd."` now ends with a full stop, as it should.

**Still open, deliberately not changed:** units are always plural, so `"1 kg"`
reads as `"one kilograms"`. Fixing it touches the same rule but changes more
behaviour than the two bugs above, so it is left for you to decide on.
*(Decided in 1.2.0: a quantity of exactly one now takes a singular unit. A
fraction still takes a plural one.)*
