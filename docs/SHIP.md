# Shipping the web tool

`index.html` is the whole product. One file, no build step, no dependencies, no
server. Open it locally and it works offline.

**Verified before shipping:** the JavaScript engine was diffed against the
Python library on all 28 test cases plus the 2 acronym cases - **30/30 identical
output**. The page is not an approximation of `speakable`; it is the same
behaviour.

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
